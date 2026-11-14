"""Reuse the original machining form against the active step/operation."""

from dxf2gcode.presentation.qt.numeric_display import format_number, set_number
from html import escape
from math import ceil, isfinite

import dxf2gcode.bootstrap.runtime_state as g
from dxf2gcode.domain.project.machining_project import MachiningOperation
from dxf2gcode.presentation.qt.qt_compat import QtCore
from dxf2gcode.presentation.qt.qt_compat.QtGui import QIcon, QPainter, QPainterPath, QPen, QPixmap, QPalette
from dxf2gcode.presentation.qt.qt_compat.QtWidgets import (
    QLineEdit, QComboBox, QToolButton, QLabel, QMenu, QSizePolicy, QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame, QGridLayout, QGroupBox)

Qt = QtCore.Qt


def provenance_icon(kind, color):
    """Draw monochrome vector paths at several sizes for normal/HiDPI use."""
    icon = QIcon()
    for size in (16, 20, 24, 32, 48):
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.scale(size / 24, size / 24)
        painter.setPen(QPen(color, 1.8, Qt.PenStyle.SolidLine,
                            Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        if kind == 'inherited':
            painter.translate(12, 12)
            painter.rotate(-35)
            painter.drawRoundedRect(QtCore.QRectF(-10, -4, 12, 8), 4, 4)
            painter.drawRoundedRect(QtCore.QRectF(-2, -4, 12, 8), 4, 4)
        elif kind == 'own':
            path = QPainterPath()
            path.moveTo(5, 19)
            path.lineTo(6, 15)
            path.lineTo(16, 5)
            path.lineTo(20, 9)
            path.lineTo(10, 19)
            path.closeSubpath()
            painter.drawPath(path)
            painter.drawLine(14, 7, 18, 11)
        elif kind == 'mixed':
            painter.drawEllipse(QtCore.QRectF(4, 4, 16, 16))
            painter.drawLine(7, 12, 17, 12)
        else:
            path = QPainterPath()
            path.moveTo(6, 7)
            path.cubicTo(23, -1, 25, 23, 10, 20)
            painter.drawPath(path)
            painter.drawLine(6, 3, 6, 9)
            painter.drawLine(6, 9, 12, 9)
        painter.end()
        icon.addPixmap(pixmap)
    return icon


class ParameterRow(QWidget):
    """Two labelled inputs; keep every provenance button next to its input."""
    def __init__(self, cells, parent):
        super().__init__(parent)
        self.cells = cells
        self.grid = QGridLayout(self)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setHorizontalSpacing(6)
        self.grid.setVerticalSpacing(0)
        self.pairs = []
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        for index, (label, field, status) in enumerate(cells):
            visible = not (field.isHidden() and field.testAttribute(Qt.WidgetAttribute.WA_WState_ExplicitShowHide))
            pair = QWidget(self)
            layout = QHBoxLayout(pair)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(2)
            layout.addWidget(field)
            if status is not None:
                layout.addWidget(status)
            layout.addStretch(1)
            pair.setMinimumWidth(24+(status.width()+2 if status is not None else 0))
            pair.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            label.setWordWrap(True)
            label.setMinimumWidth(0)
            label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
            field.setMinimumWidth(24)
            field.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
            field.setVisible(visible)
            field.installEventFilter(self)
            self.grid.addWidget(label, 0, index*2)
            self.grid.addWidget(pair, 0, index*2+1)
            self.grid.setColumnStretch(index*2, 1)
            self.grid.setColumnStretch(index*2+1, 1)
            self.pairs.append(pair)
        if len(cells) == 1:
            self.grid.setColumnStretch(2, 1)
            self.grid.setColumnStretch(3, 1)
        self.reflow()

    def reflow(self):
        for (label, field, status), pair in zip(self.cells, self.pairs):
            visible = not field.isHidden()
            label.setVisible(visible)
            pair.setVisible(visible)
            if status is not None:
                status.setVisible(visible)
        self.setVisible(any(not field.isHidden() for _, field, _ in self.cells))

    def eventFilter(self, watched, event):
        if event.type() in (QtCore.QEvent.Type.ShowToParent, QtCore.QEvent.Type.HideToParent):
            self.reflow()
        return False


class MachiningParameters:
    """One copy of the familiar form; no legacy shape mutation signal paths."""
    step_only = {'axis3_retract', 'axis3_safe_margin'}

    def tr(self, text):
        return QtCore.QCoreApplication.translate('MachiningParameters', text)

    def __init__(self, panel):
        self.panel = panel
        self.ui = panel.window.ui
        self.frame = self.ui.millSettingsFrame
        self.ui.verticalLayout_5.removeWidget(self.frame)
        self.frame.layout().setAlignment(Qt.AlignmentFlag(0))
        self.updating = False
        self.fields = {}
        self.origins = {}
        self.resets = {}
        self.origin_boxes = {}
        color = self.frame.palette().color(QPalette.ColorGroup.Active, QPalette.ColorRole.Text)
        self.own_icon = provenance_icon('own', color)
        self.inherited_icon = provenance_icon('inherited', color)
        self.reset_icon = provenance_icon('reset', color)
        self.mixed_icon = provenance_icon('mixed', color)
        names = {
            'axis3_retract': 'zRetractionArealLineEdit', 'axis3_safe_margin': 'zSafetyMarginLineEdit',
            'axis3_start_mill_depth': 'zInitialMillDepthLineEdit', 'axis3_slice_depth': 'zInfeedDepthLineEdit',
            'axis3_mill_depth': 'zFinalMillDepthLineEdit', 'milling_offset': 'millingOffsetLineEdit',
            'f_g1_plane': 'g1FeedXYLineEdit', 'f_g1_depth': 'g1FeedZLineEdit',
            'drag_swivel_depth': 'knifeSwivelLineEdit', 'lead_in_mode': 'leadInComboBox',
            'lead_out_mode': 'leadOutComboBox', 'overcut_enabled': 'overcutComboBox',
            'break_pass': 'breaksPassComboBox'}
        # Reuse the original controls. Machining defaults become contour inputs;
        # changing them does not change the project's tool definition.
        for key, name in (('speed', 'toolSpeedLabel'), ('lead_radius', 'leadRadiusLabel'),
                          ('lead_length', 'leadLengthLabel'), ('overcut_length', 'overcutLengthLabel')):
            old = getattr(self.ui, name)
            index = self.ui.toolValuesGrid.indexOf(old)
            row, col, rs, cs = self.ui.toolValuesGrid.getItemPosition(index)
            field = QLineEdit(self.ui.toolGroupBox)
            field.setObjectName(name)
            field.setMaximumWidth(110)
            self.ui.toolValuesGrid.removeWidget(old)
            old.hide()
            old.deleteLater()
            self.ui.toolValuesGrid.addWidget(field, row, col, rs, cs)
            setattr(self.ui, name, field)
            names[key] = name
        for key, name in names.items():
            field = getattr(self.ui, name)
            self.fields[key] = field
            self._disconnect(field)
            self._connect(key, field)
            self._add_origin(key, field, self.ui.toolValuesGrid if key in
                             ('speed', 'lead_radius', 'lead_length', 'overcut_length') else self.ui.gridLayout)
        # Additional values already supported by the machining model stay in
        # the same form rather than requiring a second parameter editor.
        for key, choices in (('cut_cor', True), ('drag_angle', False), ('start_radius', False)):
            grid = self.ui.toolValuesGrid if key == 'start_radius' else self.ui.gridLayout
            row = grid.rowCount()
            label = QLabel(panel.parameter_label(key), self.frame)
            field = QComboBox(self.frame) if choices else QLineEdit(self.frame)
            field.setObjectName('machining_' + key)
            grid.addWidget(label, row, 0)
            grid.addWidget(field, row, 3 if grid is self.ui.toolValuesGrid else 1)
            self.fields[key] = field
            setattr(self, key + '_label', label)
            self._connect(key, field)
            self._add_origin(key, field, grid)
        self.tool_combo = self.ui.toolDiameterComboBox
        self.tool_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.tool_combo.setMinimumContentsLength(8)
        self.tool_combo.setMaximumWidth(180)
        self._disconnect(self.tool_combo)
        self.tool_combo.activated.connect(self.change_tool)
        for coordinate, name in enumerate(('startAtXLineEdit', 'startAtYLineEdit')):
            field = getattr(self.ui, name)
            self._disconnect(field)
            field.setReadOnly(False)
            field.editingFinished.connect(lambda coordinate=coordinate, field=field:
                                          self.change_start(coordinate, field))
        self._align_forms()
        layout = self.frame.layout()
        layout.removeWidget(self.ui.toolGroupBox)
        layout.removeWidget(self.ui.shapeGroupBox)
        content = QWidget(self.frame)
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(4, 4, 4, 4)
        content_layout.setSpacing(6)
        content_layout.addWidget(self.ui.toolGroupBox)
        content_layout.addWidget(self.ui.shapeGroupBox)
        content_layout.addStretch(1)
        self.scroll = QScrollArea(self.frame)
        self.scroll.setObjectName('machiningParametersScrollArea')
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setWidget(content)
        layout.setAlignment(Qt.AlignmentFlag(0))
        layout.addWidget(self.scroll)
        self.frame.setMinimumWidth(0)
        self.frame.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Expanding)
        self.frame.setEnabled(True)

    @staticmethod
    def _disconnect(field):
        for name in ('editingFinished', 'activated', 'textActivated'):
            signal = getattr(field, name, None)
            if signal is not None:
                try:
                    signal.disconnect()
                except TypeError:
                    pass

    def _connect(self, key, field):
        if isinstance(field, QLineEdit):
            field.editingFinished.connect(lambda key=key: self.commit_number(key))
        else:
            field.activated.connect(lambda index, key=key, field=field:
                                    self.commit(key, field.currentData()))

    def _add_origin(self, key, field, grid):
        index = grid.indexOf(field)
        row, col, rs, cs = grid.getItemPosition(index)
        origin = QToolButton(self.frame)
        origin.setAutoRaise(True)
        origin.setIconSize(QtCore.QSize(16, 16))
        origin.setFixedSize(32, max(20, field.sizeHint().height()))
        origin.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        menu = QMenu(origin)
        edit = menu.addAction(self.tr('Edit value…'))
        edit.triggered.connect(lambda checked=False, field=field: field.setFocus())
        reset = menu.addAction(self.reset_icon, self.tr('Use step default'))
        reset.triggered.connect(lambda checked=False, key=key: self.reset(key))
        origin.setMenu(menu)
        grid.addWidget(origin, row, 4 if grid is self.ui.toolValuesGrid else 3)
        self.origins[key], self.resets[key], self.origin_boxes[key] = origin, reset, origin
        if key == 'break_pass':
            self.ui.breaksPassOrigin = origin
            origin.setVisible(not field.isHidden())

    def _align_forms(self):
        """One scrolling form with four groups and two values per row."""
        ui = self.ui
        controls = dict(self.fields, tool=self.tool_combo, start_x=ui.startAtXLineEdit, start_y=ui.startAtYLineEdit)
        visibility = {key: not (field.isHidden() and field.testAttribute(
            Qt.WidgetAttribute.WA_WState_ExplicitShowHide)) for key, field in controls.items()}
        def clear(layout):
            while layout.count():
                item = layout.takeAt(0)
                if item.layout() is not None:
                    clear(item.layout())
                elif item.widget() is not None:
                    item.widget().hide()
        for grid in (ui.toolValuesGrid, ui.gridLayout):
            clear(grid)
            for column in range(grid.columnCount()):
                grid.setColumnMinimumWidth(column, 0)
                grid.setColumnStretch(column, 0)
            grid.setContentsMargins(0, 0, 0, 0)
            grid.setAlignment(Qt.AlignmentFlag.AlignTop)
        for group in (ui.toolGroupBox, ui.shapeGroupBox):
            group.setTitle('')
            group.setFlat(True)
            group.layout().setContentsMargins(0, 0, 0, 0)
            group.setMinimumWidth(0)
            group.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Maximum)
        self.groups = {}
        self.value_rows = []
        self.labels = {}
        self.label_texts = {}
        descriptions = {
            'tool': self.tr('Tool'), 'speed': self.tr('Speed'),
            'axis3_start_mill_depth': self.tr('Top'), 'axis3_safe_margin': self.tr('Safety'),
            'axis3_retract': self.tr('Retract'), 'axis3_slice_depth': self.tr('Infeed'),
            'axis3_mill_depth': self.tr('Final'), 'break_pass': self.tr('Pass'),
            'f_g1_plane': 'XY', 'f_g1_depth': 'Z',
            'lead_in_mode': self.tr('Entry'), 'lead_out_mode': self.tr('Exit'),
            'lead_radius': self.tr('Radius'), 'lead_length': self.tr('Straight'),
            'overcut_enabled': self.tr('Overcut'), 'overcut_length': self.tr('Length'),
            'start_radius': self.tr('Legacy radius'), 'cut_cor': self.tr('Compensation'),
            'milling_offset': self.tr('Allowance'), 'drag_swivel_depth': self.tr('Swivel'),
            'drag_angle': self.tr('Knife angle'), 'start_x': self.tr('Start X'), 'start_y': self.tr('Start Y')}
        for key, field in controls.items():
            if key != 'tool':
                field.setMaximumWidth(field.fontMetrics().horizontalAdvance(
                    '0000000000' if isinstance(field, QComboBox) else '00000000')+12)
        def row(keys, parent, layout):
            cells = []
            for key in keys:
                label = QLabel(descriptions[key], parent)
                label.setToolTip(self.panel.parameter_label(key) if key in self.fields else descriptions[key])
                self.labels[key] = label
                self.label_texts[key] = descriptions[key]
                controls[key].setVisible(visibility[key])
                cells.append((label, controls[key], self.origins.get(key)))
            widget = ParameterRow(cells, parent)
            self.value_rows.append(widget)
            layout.addWidget(widget)
        # The tool selector and speed share the top row without a separator.
        top = QVBoxLayout()
        top.setContentsMargins(4, 4, 4, 4)
        row(('tool', 'speed'), ui.toolGroupBox, top)
        ui.toolValuesGrid.addLayout(top, 0, 0)
        definitions = (
            ('z', self.tr('Z values'), (('axis3_start_mill_depth', 'axis3_safe_margin'),
             ('axis3_retract', 'axis3_slice_depth'), ('axis3_mill_depth', 'drag_swivel_depth'), ('break_pass',))),
            ('feeds', self.tr('Feeds'), (('f_g1_plane', 'f_g1_depth'),)),
            ('leads', self.tr('Lead in/out'), (('lead_in_mode', 'lead_out_mode'),
             ('lead_radius', 'lead_length'), ('overcut_enabled', 'overcut_length'), ('start_radius',))),
            ('offset', self.tr('Offset'), (('cut_cor', 'milling_offset'), ('start_x', 'start_y'), ('drag_angle',))))
        for index, (key, title, rows) in enumerate(definitions):
            group = QGroupBox(title, ui.shapeGroupBox)
            group.setObjectName('machining_'+key+'Group')
            group.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Maximum)
            layout = QVBoxLayout(group)
            layout.setContentsMargins(8, 6, 8, 8)
            layout.setSpacing(2)
            for keys in rows:
                row(keys, group, layout)
            self.groups[key] = group
            ui.gridLayout.addWidget(group, index, 0)
        ui.gridLayout.setVerticalSpacing(6)
        # Existing visibility controllers keep addressing these labels.
        ui.breaksPassLabel = self.labels['break_pass']
        ui.knifeSwivelLabel = self.labels['drag_swivel_depth']
        self.drag_angle_label = self.labels['drag_angle']
        self.cut_cor_label = self.labels['cut_cor']
        self.start_radius_label = self.labels['start_radius']
        self.update_preferred_columns()

    def update_preferred_columns(self):
        self.preferred_width = max(sum(label.fontMetrics().horizontalAdvance(label.text())+
            min(field.maximumWidth(), 140)+(34 if status is not None else 0)+12
            for label, field, status in row.cells) for row in self.value_rows)+48

    def update_labels(self, units):
        for key, label in self.labels.items():
            suffix = ('rpm' if key == 'speed' else units+'/min' if key in ('f_g1_plane', 'f_g1_depth')
                      else '°' if key == 'drag_angle' else units if key in (
                          'axis3_retract', 'axis3_safe_margin', 'axis3_start_mill_depth', 'axis3_slice_depth',
                          'axis3_mill_depth', 'milling_offset', 'drag_swivel_depth', 'lead_radius',
                          'lead_length', 'overcut_length', 'start_radius', 'start_x', 'start_y') else '')
            label.setText(self.label_texts[key]+(' ['+suffix+']' if suffix else ''))

    def tool_selection(self):
        panel = self.panel
        if panel.binding is None:
            return ()
        selected = panel.tree.selectedItems()
        if len(selected) == 1 and selected[0].data(0, Qt.ItemDataRole.UserRole)[0] == 'step':
            return ()  # An explicit step selection keeps the step-default editor.
        ids = panel.selected_entries()
        return tuple(ids) if len(ids) > 1 else ()

    def target(self):
        panel = self.panel
        if panel.binding is None:
            return None, None
        project = panel.binding.project
        if panel.context:
            return next(((s, e) for s in project.steps for e in s.entries
                         if isinstance(e, MachiningOperation) and e.id == panel.context), (None, None))
        item = panel.tree.currentItem()
        identity = item.data(0, Qt.ItemDataRole.UserRole)[1] if item is not None and item.data(
            0, Qt.ItemDataRole.UserRole)[0] == 'step' else None
        if identity is None and len(panel.commands.selection) == 1:
            identity = panel.commands.selection[0]
        return next(((s, None) for s in project.steps if s.id == identity), (None, None))

    def selection_targets(self):
        panel = self.panel
        if panel.binding is None:
            return []
        selected = panel.tree.selectedItems()
        if len(selected) == 1 and selected[0].data(0, Qt.ItemDataRole.UserRole)[0] == 'step':
            return []
        return [(step, entry) for step, entry in panel.commands.entries(
            panel.binding.project, panel.selected_entries()) if isinstance(entry, MachiningOperation)]

    def ambiguous_geometry_selection(self, targets):
        if not getattr(self.panel, 'selection_from_geometry', False):
            return False
        linked = self.panel.binding.operations_by_geometry()
        return any(len(linked[entry.geometry_id]) > 1 for _, entry in targets)

    def set_value_palette(self, field, subdued):
        palette = QPalette(self.frame.palette())
        if subdued:
            for role in (QPalette.ColorRole.Text, QPalette.ColorRole.WindowText):
                palette.setColor(role, Qt.GlobalColor.gray)
            palette.setColor(QPalette.ColorRole.PlaceholderText, Qt.GlobalColor.gray)
        field.setPalette(palette)

    def number_kind(self, key):
        return ('angle' if key == 'drag_angle' else 'integer' if key == 'speed' else
                'feed' if key in ('f_g1_plane', 'f_g1_depth') else 'length')

    def render_selection(self, targets, units):
        panel, project = self.panel, self.panel.binding.project
        blocked = self.ambiguous_geometry_selection(targets)
        self.ui.toolGroupBox.setEnabled(not blocked)
        self.ui.shapeGroupBox.setEnabled(not blocked)
        text = (self.tr('Select machining operations explicitly: selected geometry has multiple linked operations.')
                if blocked else self.tr('{0} machining contours selected. Changes apply to the entire selection.').format(len(targets)))
        self.frame.setToolTip(text)
        resolved = [(step, entry, *project.resolve(step, entry)[:2]) for step, entry in targets]
        tools = {project.tools[step.tool_id] for step, _ in targets}
        panel.populate_tool_combo(self.tool_combo, targets[0][0].tool_id if len(tools) == 1 else None)
        self.tool_combo.setPlaceholderText(self.tr('Different tools'))
        if len(tools) > 1:
            self.tool_combo.insertItem(0, self.tr('Different tools'), None)
            self.tool_combo.setCurrentIndex(0)
        self.tool_combo.setToolTip(text)
        for key, field in self.fields.items():
            samples = resolved
            if key in self.step_only:
                samples = list({item[0].id: item for item in resolved}.values())
            values = [values.get(key) for _, _, values, _ in samples]
            applicable = all(value is not None for value in values)
            if key in ('cut_cor', 'lead_in_mode', 'lead_out_mode', 'lead_radius', 'lead_length', 'overcut_enabled', 'overcut_length'):
                applicable &= all(step.kind in ('contour', 'pocket') for step, _ in targets)
            if key in ('overcut_enabled', 'overcut_length'):
                applicable &= all(panel.binding.sources.get(entry.geometry_id) is not None and
                                  panel.binding.sources[entry.geometry_id].closed for _, entry in targets)
            same = applicable and all(value == values[0] for value in values)
            own = sum(key in (step.defaults if key in self.step_only else entry.overrides)
                      for step, entry, _, _ in samples)
            state = 'same' if same else 'mixed' if applicable else 'unavailable'
            placeholder = self.tr('Different') if applicable else self.tr('Not jointly available')
            field.setProperty('selection_state', state)
            field.setEnabled(applicable and not blocked)
            if isinstance(field, QLineEdit):
                set_number(field, values[0] if same else None, units, self.number_kind(key))
                field.setPlaceholderText('' if same else placeholder)
                field.setModified(False)
            else:
                field.clear()
                if not same:
                    field.addItem(placeholder, None)
                if key == 'break_pass':
                    choices = [(-1, QtCore.QCoreApplication.translate('TreeHandler', 'Last pass (default)')),
                               (0, QtCore.QCoreApplication.translate('TreeHandler', '0 - never'))]
                    count = max((ceil(abs(v.get('axis3_mill_depth', 0)-v.get('axis3_start_mill_depth', 0))/abs(v['axis3_slice_depth']))
                                 if v.get('axis3_slice_depth') else 0 for _, _, v, _ in resolved), default=0)
                    choices += [(i, QtCore.QCoreApplication.translate('TreeHandler', 'Pass %d') % i) for i in range(1, count+1)]
                    for value, label in choices:
                        field.addItem(label, value)
                else:
                    for label, value in panel.value_choices(key):
                        field.addItem(label, value)
                if same:
                    if field.findData(values[0]) < 0:
                        field.addItem(str(values[0]), values[0])
                    field.setCurrentIndex(field.findData(values[0]))
            self.set_value_palette(field, not same or own == 0)
            field.setToolTip(self.field_help(key)+('' if same else '\n'+placeholder))
            field.setAccessibleName(panel.parameter_label(key))
            button = self.origins[key]
            provenance = 'inherited' if own == 0 else 'own' if own == len(samples) else 'mixed'
            button.setIcon({'own': self.own_icon, 'inherited': self.inherited_icon, 'mixed': self.mixed_icon}[provenance])
            button.setProperty('provenance', provenance)
            button.setEnabled(applicable and not blocked)
            help_text = self.tr('{0}: {1} own values, {2} inherited values.').format(panel.parameter_label(key), own, len(samples)-own)
            # Retain actual values/origins in the symbol help, never infer
            # inheritance merely because a value happens to equal a default.
            origin_names = {'operation': self.tr('Own value'), 'step': self.tr('Step {0}'),
                            'tool': self.tr('Tool T{0}'), 'project': self.tr('Project default')}
            def origin_name(step, origins):
                name = origin_names[origins.get(key, 'step')]
                return name.format(step.name if origins.get(key, 'step') == 'step' else project.tools[step.tool_id].tool_nr)
            help_text += '\n' + '\n'.join('%s / %s: %s (%s)' % (step.name,
                panel.tr('Contour {0}').format(panel.binding.sources[entry.geometry_id].nr) if entry.geometry_id in panel.binding.sources else entry.id[:8],
                values.get(key), origin_name(step, origins)) for step, entry, values, origins in samples)
            if key in self.step_only:
                help_text += '\n' + self.tr('Changes affect all contours in {0} selected steps.').format(len(samples))
            button.setToolTip(help_text)
            button.setAccessibleName(help_text.split('\n')[0])
            self.resets[key].setEnabled(bool(own and key not in self.step_only and applicable and not blocked))
        legacy = any('start_radius' in entry.overrides or 'start_radius' in step.defaults for step, entry in targets)
        self.fields['start_radius'].setVisible(legacy)
        self.apply_machine_visibility()
        for coordinate, name in enumerate(('startAtXLineEdit', 'startAtYLineEdit')):
            field = getattr(self.ui, name)
            values = [entry.start[coordinate] for _, entry in targets]
            same = all(value == values[0] for value in values)
            set_number(field, values[0] if same else None, units)
            field.setPlaceholderText('' if same else self.tr('Different'))
            field.setEnabled(not blocked)
            field.setModified(False)
            self.set_value_palette(field, not same)

    def refresh(self):
        self.updating = True
        try:
            self._refresh()
        finally:
            for row in self.value_rows:
                row.reflow()
            for group in self.groups.values():
                group.setVisible(any(row.isVisibleTo(group) for row in group.findChildren(ParameterRow)))
            self.updating = False

    def _refresh(self):
        panel, ui = self.panel, self.ui
        step, entry = self.target()
        selection = self.tool_selection()
        units = panel.binding.project.units if panel.binding else ('mm' if g.config.metric else 'in')
        unit = '[' + units + ']'
        self.apply_machine_visibility()
        self.update_labels(units)
        targets = self.selection_targets()
        if len(targets) > 1 or self.ambiguous_geometry_selection(targets):
            self.render_selection(targets, units)
            return
        for field in self.fields.values():
            if isinstance(field, QLineEdit):
                field.setPlaceholderText('')
            self.set_value_palette(field, False)
            field.setProperty('selection_state', None)
        for name in ('startAtXLineEdit', 'startAtYLineEdit'):
            getattr(ui, name).setPlaceholderText('')
            self.set_value_palette(getattr(ui, name), False)
        for name in ('toolDiameterUnitLabel', 'leadRadiusUnitLabel', 'leadLengthUnitLabel', 'overcutLengthUnitLabel'):
            getattr(ui, name).setText(unit)
        for number in range(1, 11):
            getattr(ui, 'unitLabel_' + str(number)).setText('[' + units + '/min]' if number in (8, 9) else unit)
        self.frame.setEnabled(True)
        ui.toolGroupBox.setEnabled(step is not None)
        ui.shapeGroupBox.setEnabled(step is not None)
        if step is None:
            for field in self.fields.values():
                field.setEnabled(False)
                if isinstance(field, QLineEdit):
                    field.clear()
                else:
                    field.setCurrentIndex(-1)
            for button in self.origins.values():
                button.setEnabled(False)
                button.setIcon(QIcon())
                button.setToolTip('')
            for button in self.resets.values():
                button.setEnabled(False)
            self.tool_combo.setCurrentIndex(-1)
            for name in ('toolDiameterLabel', 'startAtXLineEdit', 'startAtYLineEdit'):
                getattr(ui, name).setText('')
            self.frame.setToolTip(panel.tr('Select a machining operation to edit its values.'))
            if selection:
                project = panel.binding.project
                steps = [source for source, _ in panel.commands.entries(project, selection)]
                definitions = {project.tools[source.tool_id] for source in steps}
                common = steps[0].tool_id if len(definitions) == 1 else None
                ui.toolGroupBox.setEnabled(True)
                panel.populate_tool_combo(self.tool_combo, common)
                self.tool_combo.setPlaceholderText(self.tr('Different tools'))
                if common is not None:
                    ui.toolDiameterLabel.setText(format_number(project.tools[common].tool_diameter, units))
                text = self.tr('{0} contours selected. Tool changes apply only to this selection.').format(len(selection))
                self.frame.setToolTip(text)
                self.tool_combo.setToolTip(text)
            return
        project = panel.binding.project
        operation = entry or MachiningOperation('', '')
        values, origins, tool = project.resolve(step, operation)
        self.frame.setToolTip(panel.tr('Active: {0} · T{1}').format(step.name, tool.tool_nr)
                                    if entry else self.tr('Step defaults: {0}').format(step.name))
        panel.populate_tool_combo(self.tool_combo, step.tool_id, shared_replacement=entry is None)
        self.tool_combo.setPlaceholderText('')
        self.tool_combo.setToolTip(self.tr('Tool from step {0}').format(step.name))
        if selection:
            steps = [source for source, _ in panel.commands.entries(project, selection)]
            definitions = {project.tools[source.tool_id] for source in steps}
            panel.populate_tool_combo(self.tool_combo, steps[0].tool_id if len(definitions) == 1 else None)
            self.tool_combo.setPlaceholderText(self.tr('Different tools'))
            text = self.tr('{0} contours selected. Tool changes apply only to this selection.').format(len(selection))
            self.frame.setToolTip(self.frame.toolTip()+'\n'+text)
            self.tool_combo.setToolTip(text)
        ui.toolDiameterLabel.setText(format_number(tool.tool_diameter, units))
        for key, field in self.fields.items():
            value = values.get(key)
            if isinstance(field, QLineEdit):
                set_number(field, value, units, 'angle' if key == 'drag_angle' else 'integer' if key == 'speed' else 'feed' if key in ('f_g1_plane', 'f_g1_depth') else 'length')
                field.setModified(False)
            else:
                field.clear()
                if key == 'break_pass':
                    field.addItem(QtCore.QCoreApplication.translate('TreeHandler', 'Last pass (default)'), -1)
                    field.addItem(QtCore.QCoreApplication.translate('TreeHandler', '0 - never'), 0)
                    depth = abs(values.get('axis3_mill_depth', 0) - values.get('axis3_start_mill_depth', 0))
                    slice_depth = abs(values.get('axis3_slice_depth', 0))
                    count = ceil(depth / slice_depth) if slice_depth else 0
                    for number in range(1, count+1):
                        field.addItem(QtCore.QCoreApplication.translate('TreeHandler', 'Pass %d') % number, number)
                    if value is not None and field.findData(value) < 0:
                        field.addItem(str(value), value)
                else:
                    for label, data in panel.value_choices(key):
                        field.addItem(label, data)
                field.setCurrentIndex(field.findData(value))
            enabled = value is not None
            field.setEnabled(enabled)
            # Clearance always edits step defaults, even with an active contour.
            own = (key in entry.overrides if entry and key not in self.step_only else key in step.defaults)
            self.set_value_palette(field, not own)
            owner = origins.get(key, 'step')
            source = (self.tr('Step {0}').format(step.name) if owner == 'step' or key in self.step_only else
                      self.tr('Tool T{0}').format(tool.tool_nr) if owner == 'tool' else self.tr('Project default'))
            name = panel.parameter_label(key)
            if isinstance(field, QComboBox):
                rendered = field.currentText()
            else:
                suffix = 'rpm' if key == 'speed' else units+'/min' if key in ('f_g1_plane', 'f_g1_depth') else '°' if key == 'drag_angle' else units
                rendered = '%s %s' % (value, suffix)
            if own and entry is not None and key not in self.step_only:
                contour = panel.binding.sources.get(entry.geometry_id)
                text = self.tr('{0} — own value for contour {1} in step "{2}": {3}').format(
                    name, contour.nr if contour is not None else entry.id[:8], step.name, rendered)
            elif own:
                text = self.tr('{0} — own value in step "{1}": {2}').format(name, step.name, rendered)
            else:
                text = self.tr('{0} — inherited from {1}: {2}').format(name, source, rendered)
            button = self.origins[key]
            button.setEnabled(enabled)
            button.setIcon(self.own_icon if own else self.inherited_icon)
            button.setProperty('provenance', 'own' if own else 'inherited')
            button.setAccessibleName(panel.parameter_label(key) + ': ' +
                                     (self.tr('Own value') if own else self.tr('Inherited value')))
            button.setToolTip('<qt>' + escape(text) + '</qt>')
            field.setAccessibleName(panel.parameter_label(key))
            field.setToolTip(self.field_help(key))
            self.resets[key].setEnabled(bool(entry and own and key not in self.step_only))
        legacy_radius = values.get('start_radius')
        explicit_legacy = 'start_radius' in step.defaults or (entry is not None and 'start_radius' in entry.overrides)
        visible = explicit_legacy and legacy_radius is not None and legacy_radius != values.get('lead_radius')
        self.fields['start_radius'].setVisible(visible)
        self.origin_boxes['start_radius'].setVisible(visible)
        self.apply_machine_visibility()
        for coordinate, name in enumerate(('startAtXLineEdit', 'startAtYLineEdit')):
            field = getattr(ui, name)
            field.setEnabled(entry is not None)
            set_number(field, entry.start[coordinate] if entry else None, units)
            field.setToolTip(panel.tr('Local X, Y') + ' ' + unit)
            field.setModified(False)

    def apply_machine_visibility(self):
        project = self.panel.binding.project if self.panel.binding else None
        machine = (project.configuration if project else g.config.vars)['General']['machine_type']
        knife = machine == 'drag_knife'
        for key, visible in (('drag_swivel_depth', knife), ('drag_angle', knife), ('cut_cor', not knife)):
            self.fields[key].setVisible(visible)
            self.origin_boxes[key].setVisible(visible)
        # These controls belong to the milling lead generator. Lathe kinematics
        # and the native knife planner do not consume them.
        for key in ('lead_in_mode', 'lead_out_mode', 'lead_radius', 'lead_length',
                    'overcut_enabled', 'overcut_length'):
            self.fields[key].setVisible(machine == 'milling')
            self.origin_boxes[key].setVisible(machine == 'milling')
        if machine != 'milling':
            self.fields['start_radius'].hide()
            self.origin_boxes['start_radius'].hide()
        for row in self.value_rows:
            row.reflow()

    def field_help(self, key):
        return {
            'axis3_retract': self.tr('Z height used for retracting and rapid travel.'),
            'axis3_safe_margin': self.tr('Clearance above the workpiece before approaching a cut.'),
            'axis3_start_mill_depth': self.tr('Z coordinate of the workpiece surface.'),
            'axis3_slice_depth': self.tr('Maximum cutting depth per pass.'),
            'axis3_mill_depth': self.tr('Z coordinate reached by the final cutting pass.'),
            'f_g1_plane': self.tr('XY feed: movement speed in the machining plane.'),
            'f_g1_depth': self.tr('Z feed: movement speed along the depth axis.'),
            'milling_offset': self.tr('Additional contour allowance applied to the toolpath.'),
            'lead_in_mode': self.tr('Movement used to approach the contour.'),
            'lead_out_mode': self.tr('Movement used to leave the contour.'),
            'overcut_enabled': self.tr('Whether the toolpath continues beyond the contour end.'),
            'break_pass': self.tr('Pass from which holding-tab regions affect the contour.'),
            'speed': self.tr('Spindle speed for this machining operation.'),
            'lead_radius': self.tr('Radius of the approach or departure arc at the workpiece.'),
            'lead_length': self.tr('Length of the straight approach or departure segment.'),
            'overcut_length': self.tr('Distance travelled beyond the contour end.'),
            'drag_swivel_depth': self.tr('Z contact height for swivelling a drag knife.'),
            'drag_angle': self.tr('Angle threshold for swivelling the drag knife.'),
            'cut_cor': self.tr('Tool radius compensation: G40 off, G41 left, G42 right.'),
            'start_radius': self.tr('Legacy entry radius; prefer the lead radius for new settings.')}[key]

    def commit_number(self, key):
        field = self.fields[key]
        if self.updating or self.panel.busy or not field.isModified():
            return
        try:
            value = float(field.text().replace(',', '.'))
            if not isfinite(value):
                raise ValueError()
        except ValueError:
            self.panel.report_warning(self.tr('Enter a finite number.'))
            self.refresh()
            return
        self.commit(key, value)

    def commit(self, key, value):
        if self.updating or self.panel.busy:
            return
        targets = self.selection_targets()
        if len(targets) > 1:
            if self.ambiguous_geometry_selection(targets) or value is None or not self.fields[key].isEnabled():
                return
            identities = tuple(entry.id for _, entry in targets)
            if key in self.step_only:
                self.panel.execute(lambda: self.panel.commands.update_selected_step_defaults(identities, {key: value}))
            else:
                self.panel.execute(lambda: self.panel.commands.update_entries(identities, {key: value}))
            return
        step, entry = self.target()
        if step is None or value is None:
            return
        if entry is not None and key not in self.step_only:
            self.panel.execute(lambda: self.panel.commands.update_entries([entry.id], {key: value}))
        else:
            defaults = dict(step.defaults, **{key: value})
            self.panel.execute(lambda: self.panel.commands.edit_step(step.id, step.name, step.kind, step.tool_id, defaults))

    def reset(self, key):
        targets = self.selection_targets()
        if len(targets) > 1:
            if not self.ambiguous_geometry_selection(targets) and self.resets[key].isEnabled():
                self.panel.execute(lambda: self.panel.commands.update_entries(
                    tuple(entry.id for _, entry in targets), {key: None}))
            return
        step, entry = self.target()
        if entry is not None and key not in self.step_only and key in entry.overrides:
            self.panel.execute(lambda: self.panel.commands.update_entries([entry.id], {key: None}))

    def change_tool(self, index):
        if self.updating or self.panel.busy:
            return
        if self.tool_combo.itemData(index) is None:
            return
        if self.ambiguous_geometry_selection(self.selection_targets()):
            return
        selection = self.tool_selection()
        if selection:
            identity = self.tool_combo.itemData(index)
            self.panel.execute(lambda: self.panel.commands.set_operation_tool(selection, identity))
            return
        step, entry = self.target()
        if entry is not None:
            identity = self.tool_combo.itemData(index)
            self.panel.execute(lambda: self.panel.commands.set_operation_tool((entry.id,), identity))
            return
        if step is not None:
            identity = self.tool_combo.itemData(index)
            shared = self.panel.replaces_shared_tool(self.tool_combo, step)
            self.panel.execute(lambda: self.panel.commands.edit_step(step.id, step.name, step.kind, identity,
                               replace_shared_tool=shared))

    def change_start(self, coordinate, field):
        if self.updating or self.panel.busy or not field.isModified():
            return
        targets = self.selection_targets()
        step, entry = self.target()
        if self.ambiguous_geometry_selection(targets) or (entry is None and not targets):
            return
        try:
            value = float(field.text().replace(',', '.'))
            if not isfinite(value):
                raise ValueError()
        except ValueError:
            self.panel.report_warning(self.tr('Enter a finite number.'))
            self.refresh()
            return
        if len(targets) > 1:
            self.panel.execute(lambda: self.panel.commands.update_start_coordinate(
                tuple(entry.id for _, entry in targets), coordinate, value))
            return
        point = list(entry.start)
        point[coordinate] = value
        self.panel.execute(lambda: self.panel.commands.update_entries([entry.id], start=tuple(point)))
