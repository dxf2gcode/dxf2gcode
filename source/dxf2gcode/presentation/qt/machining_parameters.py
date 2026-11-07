"""Reuse the original machining form against the active step/operation."""

from dxf2gcode.presentation.qt.numeric_display import format_number, set_number
from html import escape
from math import ceil, isfinite

import dxf2gcode.bootstrap.runtime_state as g
from dxf2gcode.domain.project.machining_project import MachiningOperation
from dxf2gcode.presentation.qt.qt_compat import QtCore
from dxf2gcode.presentation.qt.qt_compat.QtGui import QIcon, QPainter, QPainterPath, QPen, QPixmap, QPalette
from dxf2gcode.presentation.qt.qt_compat.QtWidgets import (
    QLineEdit, QComboBox, QToolButton, QLabel, QMenu, QSizePolicy, QLayout)

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
        self.frame.layout().setAlignment(Qt.AlignmentFlag.AlignTop)
        self.updating = False
        self.fields = {}
        self.origins = {}
        self.resets = {}
        self.origin_boxes = {}
        color = self.frame.palette().color(QPalette.ColorGroup.Active, QPalette.ColorRole.Text)
        self.own_icon = provenance_icon('own', color)
        self.inherited_icon = provenance_icon('inherited', color)
        self.reset_icon = provenance_icon('reset', color)
        names = {
            'axis3_retract': 'zRetractionArealLineEdit', 'axis3_safe_margin': 'zSafetyMarginLineEdit',
            'axis3_start_mill_depth': 'zInitialMillDepthLineEdit', 'axis3_slice_depth': 'zInfeedDepthLineEdit',
            'axis3_mill_depth': 'zFinalMillDepthLineEdit', 'milling_offset': 'millingOffsetLineEdit',
            'f_g1_plane': 'g1FeedXYLineEdit', 'f_g1_depth': 'g1FeedZLineEdit',
            'drag_swivel_depth': 'knifeSwivelLineEdit', 'lead_in_mode': 'leadInComboBox',
            'lead_out_mode': 'leadOutComboBox', 'overcut_enabled': 'overcutComboBox',
            'break_pass': 'breaksPassComboBox'}
        # Keep the original form and positions. The previously read-only tool
        # values become inputs so that existing operation overrides stay editable.
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
        self.ui.toolGroupBox.setTitle(self.tr('Machining tool'))
        self._align_forms()
        self.frame.setEnabled(False)

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
        origin.setFixedSize(32, 24)
        origin.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        menu = QMenu(origin)
        edit = menu.addAction(self.tr('Edit value…'))
        edit.triggered.connect(lambda checked=False, field=field: field.setFocus())
        reset = menu.addAction(self.reset_icon, self.tr('Use step default'))
        reset.triggered.connect(lambda checked=False, key=key: self.reset(key))
        origin.setMenu(menu)
        grid.addWidget(origin, row, 4 if grid is self.ui.toolValuesGrid else 3)
        self.origins[key], self.resets[key], self.origin_boxes[key] = origin, reset, origin

    def _align_forms(self):
        """Rearrange existing labels/inputs into the same four columns."""
        ui = self.ui
        ui.toolGroupBox.layout().setContentsMargins(0, 0, 0, 0)
        def labels(item):
            if item.widget() is not None:
                return [item.widget()]
            result = []
            if item.layout() is not None:
                child = item.layout()
                while child.count():
                    result.extend(labels(child.takeAt(0)))
            return result
        rows = []
        for grid in (ui.toolValuesGrid, ui.gridLayout):
            collected = {}
            while grid.count():
                row, col, _, _ = grid.getItemPosition(0)
                item = grid.takeAt(0)
                collected.setdefault(row, {})[col] = labels(item)
            if grid is ui.toolValuesGrid:
                # Give tool selection its own row; diameter uses the common grid.
                data = [(QLabel(self.tr('Tool'), self.frame), None, self.tool_combo, None),
                        (ui.label_11, ui.toolDiameterUnitLabel, ui.toolDiameterLabel, None)]
                for row in sorted(collected):
                    if row == 0:
                        continue
                    values = collected[row]
                    label = values[0][0]
                    key = next(key for key, field in self.fields.items()
                               if any(field in widgets for widgets in values.values()))
                    data.append((label, values.get(2, [None])[0], self.fields[key], self.origins[key]))
            else:
                data = []
                for row in sorted(collected):
                    values = collected[row]
                    label_and_unit = values.get(0, [])
                    if not label_and_unit:
                        continue
                    field = next((field for field in list(self.fields.values()) + [ui.startAtXLineEdit, ui.startAtYLineEdit]
                                  if any(field in widgets for widgets in values.values())), None)
                    if field is not None:
                        key = next((key for key, value in self.fields.items() if value is field), None)
                        data.append((label_and_unit[0], label_and_unit[1] if len(label_and_unit) > 1 else None,
                                     field, self.origins.get(key)))
            grid.setContentsMargins(8, 8, 8, 8)
            grid.setHorizontalSpacing(8)
            grid.setVerticalSpacing(4)
            for column in range(grid.columnCount()):
                grid.setColumnStretch(column, 0)
                grid.setColumnMinimumWidth(column, 0)
            grid.setColumnStretch(2, 1)
            for row, (label, unit, field, status) in enumerate(data):
                label.setMinimumWidth(0)
                label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
                label.setWordWrap(True)
                label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                grid.addWidget(label, row, 0)
                if unit is not None:
                    unit.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    unit.setMinimumWidth(0)
                    unit.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
                    unit.setWordWrap(True)
                    grid.addWidget(unit, row, 1)
                field.setMinimumWidth(0)
                field.setMaximumWidth(16777215)
                field.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
                grid.addWidget(field, row, 2)
                if status is not None:
                    grid.addWidget(status, row, 3)
                rows.append((grid, label, unit))
        self.form_rows = rows
        self.update_preferred_columns()
        for group in (ui.toolGroupBox, ui.shapeGroupBox):
            group.setMinimumWidth(0)
            group.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
            group.layout().setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint)
        self.frame.setMinimumWidth(0)
        self.frame.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.frame.layout().setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint)

    def update_preferred_columns(self):
        ui, rows = self.ui, self.form_rows
        label_width = max(label.fontMetrics().horizontalAdvance(label.text()) for _, label, _ in rows)
        unit_width = max(unit.fontMetrics().horizontalAdvance(unit.text()) for _, _, unit in rows if unit is not None)
        value_fields = list(self.fields.values()) + [self.tool_combo, ui.startAtXLineEdit, ui.startAtYLineEdit]
        value_width = max(max(field.sizeHint().width(), field.fontMetrics().horizontalAdvance(
            field.currentText() if isinstance(field, QComboBox) else field.text()) + 30) for field in value_fields)
        self.preferred_width = label_width + unit_width + value_width + 32 + 3*8 + 2*8 + 24
        for grid in (ui.toolValuesGrid, ui.gridLayout):
            for column, width in enumerate((label_width, unit_width, value_width)):
                grid.setColumnMinimumWidth(column, 0)
                grid.setColumnStretch(column, max(1, width))
            grid.setColumnMinimumWidth(3, 32)
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

    def refresh(self):
        self.updating = True
        try:
            self._refresh()
        finally:
            self.updating = False

    def _refresh(self):
        panel, ui = self.panel, self.ui
        step, entry = self.target()
        units = panel.binding.project.units if panel.binding else ('mm' if g.config.metric else 'in')
        unit = '[' + units + ']'
        for name in ('toolDiameterUnitLabel', 'leadRadiusUnitLabel', 'leadLengthUnitLabel', 'overcutLengthUnitLabel'):
            getattr(ui, name).setText(unit)
        for number in range(1, 11):
            getattr(ui, 'unitLabel_' + str(number)).setText('[' + units + '/min]' if number in (8, 9) else unit)
        self.frame.setEnabled(step is not None)
        if step is None:
            for field in self.fields.values():
                if isinstance(field, QLineEdit):
                    field.clear()
                else:
                    field.setCurrentIndex(-1)
            for button in self.origins.values():
                button.setIcon(QIcon())
                button.setToolTip('')
            for button in self.resets.values():
                button.setEnabled(False)
            self.tool_combo.setCurrentIndex(-1)
            for name in ('toolDiameterLabel', 'startAtXLineEdit', 'startAtYLineEdit'):
                getattr(ui, name).setText('')
            panel.context_label.setText(panel.tr('Select a machining operation to edit its values.'))
            return
        project = panel.binding.project
        operation = entry or MachiningOperation('', '')
        values, origins, tool = project.resolve(step, operation)
        panel.context_label.setText(panel.tr('Active: {0} · T{1}').format(step.name, tool.tool_nr)
                                    if entry else self.tr('Step defaults: {0}').format(step.name))
        ui.toolGroupBox.setTitle(self.tr('Machining tool'))
        ui.shapeGroupBox.setTitle(QtCore.QCoreApplication.translate('MainWindow', 'Shape parameters')
                                 if entry else self.tr('Step defaults'))
        self.tool_combo.clear()
        for index, (identity, definition) in enumerate(project.tools.items()):
            self.tool_combo.addItem('T%d · Ø%s · #%d' % (definition.tool_nr, format_number(definition.tool_diameter, units), index+1), identity)
        self.tool_combo.setCurrentIndex(self.tool_combo.findData(step.tool_id))
        for number in g.config.vars.Tool_Parameters:
            self.tool_combo.addItem(panel.tr('Import profile tool T{0}').format(number),
                                    panel.profile_tool(number, g.config.vars.Tool_Parameters[number]))
        self.tool_combo.setToolTip(self.tr('Tool from step {0}').format(step.name))
        ui.toolDiameterLabel.setText(format_number(tool.tool_diameter, units))
        knife = project.configuration['General']['machine_type'] == 'drag_knife'
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
            owner = origins.get(key, 'step')
            source = (self.tr('Step {0}').format(step.name) if owner == 'step' or key in self.step_only else
                      self.tr('Tool T{0}').format(tool.tool_nr) if owner == 'tool' else self.tr('Project default'))
            text = self.tr('Own value: {0}').format(value) if own else self.tr('Inherited from {0}: {1}').format(source, value)
            if key in self.step_only or entry is None:
                text = self.tr('Step {0}').format(step.name) + ': ' + text
            button = self.origins[key]
            button.setIcon(self.own_icon if own else self.inherited_icon)
            button.setProperty('provenance', 'own' if own else 'inherited')
            button.setAccessibleName(panel.parameter_label(key) + ': ' +
                                     (self.tr('Own value') if own else self.tr('Inherited value')))
            button.setToolTip('<qt>' + escape(text) + '</qt>')
            field.setAccessibleName(panel.parameter_label(key))
            field.setToolTip(button.toolTip())
            self.resets[key].setEnabled(bool(entry and own and key not in self.step_only))
        for key in ('drag_swivel_depth', 'drag_angle'):
            label = ui.knifeSwivelLabel if key == 'drag_swivel_depth' else self.drag_angle_label
            label.setVisible(knife)
            self.fields[key].setVisible(knife)
            self.origin_boxes[key].setVisible(knife)
        self.cut_cor_label.setVisible(not knife)
        self.fields['cut_cor'].setVisible(not knife)
        self.origin_boxes['cut_cor'].setVisible(not knife)
        self.start_radius_label.setVisible(values.get('start_radius') is not None)
        self.fields['start_radius'].setVisible(values.get('start_radius') is not None)
        self.origin_boxes['start_radius'].setVisible(values.get('start_radius') is not None)
        for coordinate, name in enumerate(('startAtXLineEdit', 'startAtYLineEdit')):
            field = getattr(ui, name)
            field.setEnabled(entry is not None)
            set_number(field, entry.start[coordinate] if entry else None, units)
            field.setToolTip(panel.tr('Local X, Y') + ' ' + unit)
            field.setModified(False)

    def commit_number(self, key):
        field = self.fields[key]
        if self.updating or self.panel.busy or not field.isModified():
            return
        try:
            value = float(field.text().replace(',', '.'))
            if not isfinite(value):
                raise ValueError()
        except ValueError:
            self.panel.notice.setText(self.tr('Enter a finite number.'))
            self.refresh()
            return
        self.commit(key, value)

    def commit(self, key, value):
        if self.updating or self.panel.busy:
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
        step, entry = self.target()
        if entry is not None and key not in self.step_only and key in entry.overrides:
            self.panel.execute(lambda: self.panel.commands.update_entries([entry.id], {key: None}))

    def change_tool(self, index):
        if self.updating or self.panel.busy:
            return
        step, entry = self.target()
        if step is not None:
            identity = self.tool_combo.itemData(index)
            self.panel.execute(lambda: self.panel.commands.edit_step(step.id, step.name, step.kind, identity))

    def change_start(self, coordinate, field):
        if self.updating or self.panel.busy or not field.isModified():
            return
        step, entry = self.target()
        if entry is None:
            return
        try:
            value = float(field.text().replace(',', '.'))
            if not isfinite(value):
                raise ValueError()
        except ValueError:
            self.panel.notice.setText(self.tr('Enter a finite number.'))
            self.refresh()
            return
        point = list(entry.start)
        point[coordinate] = value
        self.panel.execute(lambda: self.panel.commands.update_entries([entry.id], start=tuple(point)))
