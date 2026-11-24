"""Imported global BREAKS regions presented as machining modifiers.

The existing project entries remain the storage/export contract. References in
the tree are views of those entries, never additional machining operations.
"""
from collections import defaultdict
from dataclasses import replace
from dxf2gcode.presentation.qt.qt_compat import QtCore
from dxf2gcode.presentation.qt.qt_compat.QtGui import QPainterPath, QPainterPathStroker, QPen, QIcon, QPixmap, QPainter, QPalette, QFontMetricsF, QCursor
from dxf2gcode.presentation.qt.qt_compat.QtWidgets import (
    QGroupBox, QVBoxLayout, QFormLayout, QLabel, QLineEdit, QCheckBox, QPushButton, QTreeWidgetItem, QStyle, QWidget, QHBoxLayout, QToolButton, QTreeWidget, QMenu, QMessageBox, QDialog, QDialogButtonBox, QComboBox, QHeaderView, QInputDialog, QAbstractItemView)
from dxf2gcode.presentation.qt.numeric_display import set_number, format_number
from dxf2gcode.domain.project.machining_project import MachiningOperation
from dxf2gcode.adapters.toolpath.preparation import prepare_shape
from dxf2gcode.adapters.toolpath.preview import preview_result
from dxf2gcode.presentation.qt.selection_marks import REFERENCE_ROLE, ReferenceDelegate

Qt = QtCore.Qt
ROLE = Qt.ItemDataRole.UserRole


def is_tab_region(shape):
    return bool(getattr(shape, 'parentLayer', None) and shape.parentLayer.isBreakLayer())


def tab_mode_icon(palette):
    """Contour crossing a dashed region, with the selected editing pencil."""
    icon = QIcon()
    for mode, group in ((QIcon.Mode.Normal, QPalette.ColorGroup.Active),
                        (QIcon.Mode.Disabled, QPalette.ColorGroup.Disabled)):
        for size in (16, 18, 24, 32, 48):
            pixmap = QPixmap(size, size)
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.scale(size/24, size/24)
            pen = QPen(palette.color(group, QPalette.ColorRole.ButtonText), 1.7,
                       Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            painter.drawLine(QtCore.QPointF(2, 12), QtCore.QPointF(22, 12))
            pen.setDashPattern([2.2/1.7, 2.2/1.7])
            painter.setPen(pen)
            painter.drawRect(QtCore.QRectF(7, 5, 10, 14))
            pen.setStyle(Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            painter.setBrush(palette.color(group, QPalette.ColorRole.Button))
            pencil = QPainterPath(QtCore.QPointF(14, 20))
            for x, y in ((19, 15), (21, 17), (16, 22), (14, 22)):
                pencil.lineTo(x, y)
            pencil.closeSubpath()
            painter.drawPath(pencil)
            painter.end()
            icon.addPixmap(pixmap, mode)
    return icon


class TabModifiers(QtCore.QObject):
    def tr(self, text):
        return QtCore.QCoreApplication.translate('TabModifiers', text)

    def __init__(self, panel):
        super().__init__(panel)
        self.panel = panel
        self.mode = False
        self.context = None
        self.link_operation = None
        self.selected_regions = set()
        self.related_operations = set()
        self.source_layer = None
        self.project = None
        self.transform = None
        self.usage = {}
        self.groups, self.nodes = [], {}
        self.catalog = None
        self.updating = False
        self.drawing = False
        self.gesture = None
        self.pending = None
        self.draw_operations = ()
        self.creation_mode = None
        self.ignore_release = False
        self.last_height = None
        self.last_units = None
        self.preview_segments = ()
        self.dimension_hover = None
        self.dimension_editor = None
        self.preview_timer = QtCore.QTimer(self)
        self.preview_timer.setSingleShot(True)
        self.preview_timer.timeout.connect(self.compute_preview)
        self.editor = QGroupBox(self.tr('Holding tabs'), panel)
        layout = QVBoxLayout(self.editor)
        self.scope = QLabel(self.tr('Imported region — global. Changes affect every linked machining operation.'), self.editor)
        self.scope.setWordWrap(True)
        layout.addWidget(self.scope)
        self.origin = QLabel(self.editor)
        self.origin.setWordWrap(True)
        layout.addWidget(self.origin)
        form = QFormLayout()
        layout.addLayout(form)
        self.name_field = QLineEdit(self.editor)
        self.name_field.setObjectName('tabModifier_name')
        self.name_field.editingFinished.connect(lambda: self.commit('name'))
        form.addRow(self.tr('Name'), self.name_field)
        self.placement = QComboBox(self.editor)
        self.placement.setObjectName('tabModifier_placement')
        self.placement.addItem(self.tr('Snap to contour'), 'snap')
        self.placement.addItem(self.tr('Draw manually'), 'manual')
        self.placement.activated.connect(self.change_placement)
        form.addRow(self.tr('Tab placement'), self.placement)
        self.fields = {}
        for key, label in (('height', self.tr('Tab top')), ('xy_feed', self.tr('XY feed')), ('z_feed', self.tr('Z feed'))):
            field = QLineEdit(self.editor)
            field.setObjectName('tabModifier_'+key)
            field.setMaximumWidth(140)
            form.addRow(label, field)
            field.editingFinished.connect(lambda key=key: self.commit(key))
            self.fields[key] = field
        self.form = form
        self.enabled = QCheckBox(self.tr('Region enabled'), self.editor)
        self.enabled.stateChanged.connect(self.change_enabled)
        layout.addWidget(self.enabled)
        self.info = QLabel(self.editor)
        self.info.setWordWrap(True)
        layout.addWidget(self.info)
        self.assignment_scope = QComboBox(self.editor)
        self.assignment_scope.setObjectName('tabModifier_scope')
        for text, value in ((self.tr('Global'), 'global'), (self.tr('Step'), 'steps'),
                            (self.tr('Selected operations'), 'operations')):
            self.assignment_scope.addItem(text, value)
        form.addRow(self.tr('Assignment'), self.assignment_scope)
        self.assignment_targets = QTreeWidget(self.editor)
        self.assignment_targets.setObjectName('tabModifier_targets')
        self.assignment_targets.setHeaderHidden(True)
        self.assignment_targets.setMaximumHeight(110)
        layout.addWidget(self.assignment_targets)
        self.no_targets = QLabel(self.tr('No common intersecting targets.'), self.editor)
        self.no_targets.setWordWrap(True)
        layout.addWidget(self.no_targets)
        self.clear_exclusions = QCheckBox(self.editor)
        layout.addWidget(self.clear_exclusions)
        self.assignment_button = QPushButton(self.tr('Apply assignment'), self.editor)
        self.assignment_button.clicked.connect(self.apply_assignment)
        layout.addWidget(self.assignment_button)
        self.assignment_scope.currentIndexChanged.connect(self.populate_assignment_targets)
        self.assignment_targets.itemChanged.connect(self.update_assignment_button)
        self.clear_exclusions.toggled.connect(self.update_assignment_button)
        self.unlink_button = QPushButton(self.tr('Remove assignment'), self.editor)
        self.unlink_button.setObjectName('removeTabAssignment')
        self.unlink_button.clicked.connect(self.remove_assignment)
        layout.addWidget(self.unlink_button)
        self.remove_button = QPushButton(self.tr('Delete region…'), self.editor)
        self.remove_button.clicked.connect(self.remove)
        layout.addWidget(self.remove_button)
        layout.addStretch(1)
        self.editor.hide()
        self.install_filters()

    def install_filters(self):
        for tree in (self.panel.window.ui.layersShapesTreeView, self.panel.window.ui.entitiesTreeView):
            tree.setItemDelegate(ReferenceDelegate(tree))
        for view in (self.panel.window.ui.layersShapesTreeView, self.panel.window.ui.entitiesTreeView,
                     self.panel.window.canvas):
            if hasattr(view, 'viewport'):
                view.viewport().setMouseTracking(True)
                view.viewport().installEventFilter(self)
                view.installEventFilter(self)

    def records(self):
        return self.panel.binding.project.regions if self.panel.binding else {}

    def reset(self):
        self.project, self.transform = None, None
        self.usage = {}
        self.draw_operations = ()
        self.context, self.link_operation = None, None
        self.clear_reference()
        self.mode = False
        self.last_height = None
        self.last_units = None
        self.cancel()
        self.editor.hide()
        if self.panel.buttons.get('tabs') is not None:
            self.panel.buttons['tabs'].setChecked(False)

    def label(self, region):
        source = self.panel.binding.sources.get(region.geometry_id)
        name = region.name or self.tr('Tab region {0}').format(source.nr if source else region.id[:8])
        scope = self.tr('Global') if region.scope == 'global' else self.tr('Step') if region.scope == 'steps' else self.tr('Selected operations')
        return name+' · '+scope

    def affected(self, identity):
        return {part[0] for regions in self.usage.values() for part in regions.get(identity, ())}

    def regions_for_operations(self, operations):
        return {identity for regions in self.usage.values() for identity, parts in regions.items()
                if any(part[0] in operations for part in parts)}

    def selected_only(self):
        view = getattr(self.panel.window, 'view_comparison', None)
        return view is not None and view.selected_paths_action.isChecked()

    def update_usage(self, layers):
        from dxf2gcode.application.tab_regions import to_world
        binding = self.panel.binding
        transform = to_world(binding, ((0, 0), (1, 0), (0, 1)))
        if binding.project is self.project and transform == self.transform:
            return
        usage = defaultdict(lambda: defaultdict(set))
        for layer in layers:
            if layer.isBreakLayer() or layer.should_ignore():
                continue
            for view in layer.shapes:
                if not isinstance(getattr(view, 'operation_id', None), str) or view.disabled or not hasattr(view, 'geos'):
                    continue
                if view.stmove is None:
                    prepare_shape(view, build_preview=False)
                if view.toolpath_plan is None and not getattr(view, 'toolpath_diagnostics', ()):
                    preview_result(view, self.panel.window.MyPostProcessor, layers)
                for action in view.toolpath_plan.actions if view.toolpath_plan else ():
                    if action.modifier_id in self.records() and action.kind in ('linear_xy', 'arc'):
                        endpoints = action.args[1:3] if action.kind == 'arc' else action.args[:2]
                        ends = tuple(sorted(tuple(round(v, 10) for v in point) for point in endpoints))
                        curve = (('arc', tuple(round(v, 10) for v in action.args[6]), round(abs(action.args[8]), 10)) if action.kind == 'arc' else ('line',))
                        usage[layer.machining_step_id][action.modifier_id].add((view.operation_id, ends, curve))
        self.project, self.transform = binding.project, transform
        self.usage = {step: dict(regions) for step, regions in usage.items()}
        had_reference = bool(self.selected_regions)
        self.populate_tree()
        if had_reference:
            anchor = next((group.child(i) for group in self.groups
                           if group.data(0, ROLE)[1] == self.link_operation
                           for i in range(group.childCount())
                           if group.child(i).data(0, ROLE)[1] == self.context), None)
            self.select_regions(self.selected_regions, primary=self.context,
                                anchor=anchor, source_layer=self.source_layer)

    def install_catalog(self, geometry_panel):
        section = QWidget(geometry_panel.splitter)
        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        header = QHBoxLayout()
        toggle = QToolButton(section)
        toggle.setText(self.tr('Tab regions'))
        toggle.setCheckable(True)
        toggle.setChecked(True)
        toggle.setArrowType(Qt.ArrowType.DownArrow)
        toggle.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        header.addWidget(toggle)
        header.addStretch()
        create = QToolButton(section)
        create.setText('+')
        create.setToolTip(self.tr('Draw new tab region…'))
        create.clicked.connect(self.start_draw)
        header.addWidget(create)
        layout.addLayout(header)
        self.catalog = QTreeWidget(section)
        self.catalog.setItemDelegate(ReferenceDelegate(self.catalog))
        self.catalog.setHeaderLabels([self.tr('Tab regions'), self.tr('Source / effect')])
        self.catalog.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.catalog.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.catalog.setContextMenuPolicy(Qt.ContextMenuPolicy.PreventContextMenu)
        self.catalog.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.catalog.itemSelectionChanged.connect(self.catalog_selection_changed)
        self.catalog.itemDoubleClicked.connect(lambda item, col: self.edit_assignment())
        layout.addWidget(self.catalog)
        def collapse(checked):
            self.catalog.setVisible(checked)
            toggle.setArrowType(Qt.ArrowType.DownArrow if checked else Qt.ArrowType.RightArrow)
            section.setMaximumHeight(16777215 if checked else toggle.sizeHint().height()+8)
            geometry_panel.layout().setAlignment(Qt.AlignmentFlag.AlignTop
                if all(not button.isChecked() for button, _ in geometry_panel.sections) else Qt.AlignmentFlag(0))
            geometry_panel.splitter.refresh()
        toggle.toggled.connect(collapse)
        geometry_panel.sections.append((toggle, self.catalog))

    def catalog_selection_changed(self):
        if self.updating:
            return
        identities = [item.data(0, ROLE) for item in self.catalog.selectedItems()]
        self.link_operation = None
        self.select_regions(identities, primary=identities[0] if len(identities) == 1 else None)

    def populate_tree(self):
        panel, tree = self.panel, self.panel.tree
        was_busy = panel.busy
        panel.busy = True
        self.updating = True
        try:
            for group in self.groups:
                if group.treeWidget() is tree and group.parent():
                    group.parent().removeChild(group)
            self.groups, self.nodes = [], {}
            panel.buttons['tabs'].setVisible(True)
            icon = tab_mode_icon(panel.palette())
            for identity, entry_item in panel.entry_items.items():
                base_role = int(ROLE)+17
                base = entry_item.data(0, base_role) or entry_item.text(0)
                entry_item.setData(0, base_role, base)
                entry_item.setText(0, base)
                regions = [r for r in self.records().values() if identity in self.affected(r.id)]
                if not regions:
                    continue
                # A single region can split into several raised path pieces.
                # The tree lists regions, so its badge must count those objects.
                count = len(regions)
                entry_item.setText(0, entry_item.text(0)+' · '+self.tr('{0} tabs').format(count))
                group = QTreeWidgetItem(entry_item, [self.tr('Tab regions')])
                group.setData(0, ROLE, ('modifier_group', identity))
                group.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                group.setFirstColumnSpanned(True)
                self.groups.append(group)
                for region in regions:
                    child = QTreeWidgetItem(group, [self.label(region)])
                    child.setFirstColumnSpanned(True)
                    child.setIcon(0, icon)
                    child.setData(0, ROLE, ('modifier', region.id))
                    child.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                    self.nodes.setdefault(region.id, child)
                    if region.id in self.selected_regions:
                        entry_item.setExpanded(True)
                        group.setExpanded(True)
            if self.catalog is not None:
                self.catalog.clear()
                for region in self.records().values():
                    origin = self.tr('DXF') if region.geometry_id else self.tr('Manual')
                    effect = self.tr('Disabled') if not region.enabled else self.tr('No effective tabs') if not self.affected(region.id) else self.tr('{0} operations').format(len(self.affected(region.id)))
                    item = QTreeWidgetItem(self.catalog, [self.label(region), origin+' · '+effect])
                    item.setIcon(0, icon)
                    item.setData(0, ROLE, region.id)
                    item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                    if self.context == region.id:
                        self.catalog.setCurrentItem(item, 0, QtCore.QItemSelectionModel.SelectionFlag.NoUpdate)
                    item.setSelected(region.id in self.selected_regions)
        finally:
            self.updating = False
            panel.busy = was_busy
        panel.freeze_original_trees()
        # Current usage may have changed after a region/assignment command.
        self.selected_regions.intersection_update(self.records())
        self.related_operations = set().union(*(self.affected(i) for i in self.selected_regions)) if self.selected_regions else set()
        panel.update_reference_marks()

    def select(self, identity, edit=False, operation=None, anchor=None, *, toggle=False):
        if identity not in self.records():
            return
        self.link_operation = operation
        identities = self.selected_regions ^ {identity} if toggle else {identity}
        primary = next(iter(identities)) if len(identities) == 1 else None
        target = identity if identity in identities else primary
        self.select_regions(identities, primary=primary, anchor=anchor or self.nodes.get(target))
        if edit:
            self.set_mode(True)

    def clear_reference(self):
        self.context, self.link_operation, self.source_layer = None, None, None
        self.selected_regions.clear()
        self.related_operations.clear()

    def select_regions(self, identities, primary=None, anchor=None, source_layer=None, *, preserve_tree=False):
        self.selected_regions = set(identities) & set(self.records())
        self.context = primary if primary in self.selected_regions else None
        self.source_layer = source_layer
        self.related_operations = set().union(*(self.affected(i) for i in self.selected_regions)) if self.selected_regions else set()
        self.panel.context = None
        self.panel.selection_from_geometry = False
        self.panel.commands.selection = ()
        geometries = {e.geometry_id for s in self.panel.binding.project.steps for e in s.entries if e.id in self.related_operations}
        was_busy = self.panel.busy
        self.panel.busy = True
        try:
            if not preserve_tree:
                self.panel.tree.clearSelection()
                if len(self.selected_regions) > 1:
                    for identity in self.selected_regions:
                        if identity in self.nodes:
                            self.nodes[identity].setSelected(True)
            for tree in (self.panel.window.ui.layersShapesTreeView, self.panel.window.ui.entitiesTreeView):
                tree.clearSelection()
            for geometry, source in self.panel.binding.sources.items():
                source.setSelected(geometry in geometries)
            if anchor is not None:
                if anchor.parent():
                    anchor.parent().setExpanded(True)
                    if anchor.parent().parent():
                        anchor.parent().parent().setExpanded(True)
                self.panel.tree.setCurrentItem(anchor, 0, QtCore.QItemSelectionModel.SelectionFlag.NoUpdate)
                anchor.setSelected(True)
        finally:
            self.panel.busy = was_busy
        self.panel.refresh_preview()
        self.panel.show_parameters()
        self.panel.update_reference_marks()
        self.repaint()

    def mark_original_references(self):
        from dxf2gcode.presentation.qt.treehandling import SHAPE_OBJECT, LAYER_OBJECT
        geometry_regions = {r.geometry_id: r.id for r in self.records().values() if r.geometry_id}
        referenced = {e.geometry_id for s in self.panel.binding.project.steps for e in s.entries
                      if isinstance(e, MachiningOperation) and e.id in self.related_operations}
        for tree in (self.panel.window.ui.layersShapesTreeView, self.panel.window.ui.entitiesTreeView):
            model = tree.model()
            if model is None:
                continue
            blocked = model.blockSignals(True)
            def walk(parent):
                for row in range(model.rowCount(parent)):
                    index = model.index(row, 0, parent)
                    source = getattr(index.data(SHAPE_OBJECT), 'shapeobj', None)
                    layer = index.data(LAYER_OBJECT)
                    flag = 0
                    if source is not None:
                        geometry = getattr(source, 'geometry_id', None)
                        identity = geometry_regions.get(geometry)
                        flag = 2 if identity == self.context and identity is not None else 1 if identity in self.selected_regions or geometry in referenced else 0
                    elif layer is not None and layer.isBreakLayer():
                        flag = 2 if layer is self.source_layer else 1 if any(
                            r.id in self.selected_regions and self.panel.binding.sources.get(r.geometry_id) is not None
                            and self.panel.binding.sources[r.geometry_id].parentLayer is layer for r in self.records().values()) else 0
                    for column in range(model.columnCount(parent)):
                        cell = model.index(row, column, parent)
                        if cell.data(REFERENCE_ROLE) != flag:
                            model.setData(cell, flag, REFERENCE_ROLE)
                    walk(index)
            walk(QtCore.QModelIndex())
            model.blockSignals(blocked)
            tree.viewport().update()
        if self.catalog is not None:
            for row in range(self.catalog.topLevelItemCount()):
                item = self.catalog.topLevelItem(row)
                flag = 1 if item.data(0, ROLE) in self.selected_regions and not item.isSelected() else 0
                for col in range(self.catalog.columnCount()):
                    item.setData(col, REFERENCE_ROLE, flag)
            self.catalog.viewport().update()

    def set_mode(self, enabled):
        comparison = getattr(self.panel.window, 'view_comparison', None)
        if enabled and comparison is not None and comparison.renderer is not None:
            comparison.activate('plane')
        self.mode = bool(enabled)
        self.panel.buttons['tabs'].setChecked(self.mode)
        combo = self.panel.tab_placement
        blocked = combo.blockSignals(True)
        combo.setCurrentIndex(combo.findData(self.drawing_mode()))
        combo.blockSignals(blocked)
        combo.setToolTip(combo.currentText())
        if not self.mode:
            self.cancel()
            self.dimension_hover = None
            if hasattr(self.panel.window.canvas, 'viewport'):
                self.panel.window.canvas.viewport().unsetCursor()
        self.panel.show_parameters()
        self.repaint()
        if comparison is not None and comparison.renderer is not None:
            comparison.renderer.redraw()

    def open_from_geometry(self, shapes):
        geometries = {getattr(s, 'geometry_id', None) for s in shapes}
        identity = next((r.id for r in self.records().values() if r.geometry_id in geometries), None)
        if identity:
            self.select(identity, edit=True)

    def show(self):
        regions = self.editable_regions()
        if not regions:
            self.editor.hide()
            return False
        units = self.panel.binding.project.units
        mixed = self.tr('Different values')
        self.updating = True
        try:
            region = regions[0]
            self.remove_button.setEnabled(len(regions) == 1 and self.context is not None)
            self.unlink_button.setEnabled(len(regions) == 1 and self.link_operation in self.affected(region.id))
            self.scope.setText(self.label(region) if len(regions) == 1 else self.tr('{0} tabs').format(len(regions)))
            self.origin.setText(self.tr('Changes affect every linked operation. Remove assignment to exclude only one operation.'))
            names = {r.name for r in regions}
            self.name_field.setPlaceholderText(mixed if len(names) > 1 else '')
            self.name_field.setText(region.name if len(names) == 1 else '')
            self.name_field.setModified(False)
            placement = {r.placement_mode for r in regions}
            self.placement.setPlaceholderText(mixed)
            self.placement.setCurrentIndex(self.placement.findData(region.placement_mode) if len(placement) == 1 else -1)
            enabled = {r.enabled for r in regions}
            self.enabled.setTristate(len(enabled) > 1)
            self.enabled.setCheckState(Qt.CheckState.PartiallyChecked if len(enabled) > 1
                                       else Qt.CheckState.Checked if region.enabled else Qt.CheckState.Unchecked)
            for key, field in self.fields.items():
                values = {getattr(r, key) for r in regions}
                field.setPlaceholderText(mixed if len(values) > 1 else '')
                set_number(field, getattr(region, key) if len(values) == 1 else None,
                           units, 'length' if key == 'height' else 'feed')
                field.setModified(False)
                label = {'height': self.tr('Tab top'), 'xy_feed': self.tr('XY feed'), 'z_feed': self.tr('Z feed')}[key]
                self.form.labelForField(field).setText(label+' ['+units+('/min' if key != 'height' else '')+']')
            scopes = {r.scope for r in regions}
            self.assignment_scope.setPlaceholderText(mixed)
            self.assignment_scope.setCurrentIndex(self.assignment_scope.findData(region.scope) if len(scopes) == 1 else -1)
            excluded = set().union(*(r.excluded for r in regions))
            self.clear_exclusions.setText(self.tr('Clear local exclusions ({0})').format(len(excluded)))
            self.clear_exclusions.setVisible(bool(excluded))
            self.clear_exclusions.setChecked(False)
            self.info.setText(self.tr('{0} operations').format(len(self.related_operations)))
            self.editor.show()
        finally:
            self.updating = False
        self.populate_assignment_targets()
        return True

    def editable_regions(self):
        return [r for r in self.records().values() if r.id in self.selected_regions or r.id == self.context]

    def apply_properties(self, **values):
        updates = {}
        for region in self.editable_regions():
            change = dict(values)
            if values.get('placement_mode') == 'snap' and region.placement_mode != 'snap':
                from dxf2gcode.application.tab_regions import to_drawing
                vertices = self.standard_vertices(replace(region, placement_mode='snap'))
                if vertices is None:
                    self.show()
                    return
                change['vertices'] = to_drawing(self.panel.binding, vertices)
            updates[region.id] = change
        if updates:
            self.panel.execute(lambda: self.panel.commands.update_regions(updates))
        self.show()

    def commit(self, key):
        field = self.name_field if key == 'name' else self.fields[key]
        if self.updating or not field.isModified():
            return
        field.setModified(False)
        if key == 'name':
            self.apply_properties(name=field.text())
            return
        from math import isfinite
        try:
            value = float(field.text().replace(',', '.'))
            if not isfinite(value) or key != 'height' and value <= 0:
                raise ValueError()
        except ValueError:
            self.panel.report_warning(self.tr('Enter valid tab height and positive feeds.'))
            self.show()
            return
        self.apply_properties(**{key: value})

    def change_placement(self):
        if not self.updating and self.placement.currentData():
            self.apply_properties(placement_mode=self.placement.currentData())

    def change_enabled(self):
        state = self.enabled.checkState()
        if not self.updating and state != Qt.CheckState.PartiallyChecked:
            self.apply_properties(enabled=state == Qt.CheckState.Checked)

    def populate_assignment_targets(self):
        if self.updating:
            return
        from dxf2gcode.application.tab_regions import overlapping_operations
        kind = self.assignment_scope.currentData()
        regions = self.editable_regions()
        with QtCore.QSignalBlocker(self.assignment_targets):
            self.assignment_targets.clear()
            self.assignment_targets.setVisible(kind in ('steps', 'operations'))
            if regions and kind in ('steps', 'operations'):
                index = 0 if kind == 'steps' else 1
                common = set.intersection(*({target[index] for target in overlapping_operations(self.panel.binding, r)}
                                            for r in regions))
                for step in self.panel.binding.project.steps:
                    rows = [(step.id, step.name)] if kind == 'steps' else [
                        (e.id, step.name+' / '+self.panel.entry_items[e.id].text(0))
                        for e in step.entries if e.id in self.panel.entry_items]
                    for identity, text in rows:
                        if identity not in common:
                            continue
                        selected = sum(r.scope == kind and identity in r.targets for r in regions)
                        item = QTreeWidgetItem(self.assignment_targets, [text])
                        item.setData(0, ROLE, identity)
                        item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable)
                        item.setCheckState(0, Qt.CheckState.Checked if selected == len(regions)
                                           else Qt.CheckState.PartiallyChecked if selected else Qt.CheckState.Unchecked)
        self.no_targets.setVisible(kind in ('steps', 'operations') and not self.assignment_targets.topLevelItemCount())
        self.update_assignment_button()

    def assignment_values(self):
        scope = self.assignment_scope.currentData()
        rows = [self.assignment_targets.topLevelItem(i) for i in range(self.assignment_targets.topLevelItemCount())]
        targets = [item.data(0, ROLE) for item in rows if item.checkState(0) == Qt.CheckState.Checked]
        if not scope or scope != 'global' and not targets or any(
                item.checkState(0) == Qt.CheckState.PartiallyChecked for item in rows):
            return {}
        return dict(scope=scope, targets=targets, **({'excluded': []} if self.clear_exclusions.isChecked() else {}))

    def update_assignment_button(self):
        if self.updating:
            return
        values = self.assignment_values()
        self.assignment_button.setEnabled(bool(values) and any(
            any(getattr(r, key) != value for key, value in values.items()) for r in self.editable_regions()))

    def apply_assignment(self):
        values = self.assignment_values()
        if values:
            self.apply_properties(**values)

    def remove(self):
        if self.context not in self.records():
            return
        message = self.tr('Delete this region globally? {0} effective operations are affected. This can be undone.').format(len(self.affected(self.context)))
        if QMessageBox.question(self.panel, self.tr('Delete region…'), message,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
            return
        self.panel.execute(lambda: self.panel.commands.remove_region(self.context))
        self.context = None
        self.panel.show_parameters()
        self.repaint()

    def remove_assignment(self):
        region = self.records().get(self.context)
        if region and self.link_operation:
            excluded = list(dict.fromkeys(region.excluded+[self.link_operation]))
            self.panel.execute(lambda: self.panel.commands.update_region(region.id, excluded=excluded))

    def assignment_defaults(self):
        from dxf2gcode.domain.project.machining_project import StegRegion, new_id
        project = self.panel.binding.project
        ids = self.panel.commands.selection
        steps = [s.id for s in project.steps if s.id in ids]
        operations = [e.id for s in project.steps for e in s.entries if e.id in ids]
        scope = 'steps' if steps else 'operations' if operations else ''
        if not scope and not self.panel.selection_from_geometry:
            operations = list(self.panel.selected_entries())
            scope = 'operations' if operations else ''
        values = project.configuration['Depth_Coordinates']
        feeds = project.configuration['Feed_Rates']
        entry = next(((s, e) for s in project.steps for e in s.entries if e.id in operations or s.id in steps), None)
        if entry:
            values = dict(values, **project.resolve(*entry)[0])
            feeds = values
        height = self.last_height
        if height is None:
            manual = [r for r in project.regions.values() if not r.geometry_id]
            height = manual[-1].height if manual else values['axis3_start_mill_depth']
        elif self.last_units != project.units:
            height *= 25.4 if project.units == 'mm' else 1/25.4
            self.last_height, self.last_units = height, project.units
        used_names = {r.name for r in self.records().values()}
        number = 1
        while self.tr('Tab {0}').format(number) in used_names:
            number += 1
        return StegRegion(new_id(), name=self.tr('Tab {0}').format(number), height=height,
                          xy_feed=feeds['f_g1_plane'], z_feed=feeds['f_g1_depth'],
                          scope=scope, targets=steps or operations, placement_mode=self.drawing_mode())

    def region_dialog(self, region):
        from copy import deepcopy
        from dxf2gcode.application.tab_regions import overlapping_operations
        result = deepcopy(region)
        candidates = overlapping_operations(self.panel.binding, region)
        candidate_steps = {step for step, _ in candidates}
        candidate_operations = {entry for _, entry in candidates}
        creating = region.id not in self.records()
        initial_scope, initial_targets = region.scope, set(region.targets)
        if creating and len(candidates) == 1:
            initial_scope, initial_targets = 'operations', candidate_operations
        elif creating and initial_scope != 'global':
            valid = candidate_steps if initial_scope == 'steps' else candidate_operations
            initial_targets &= valid
            if not initial_targets:
                initial_scope = ''
        dialog = QDialog(self.panel)
        dialog.setWindowTitle(self.tr('Tab region'))
        dialog.setObjectName('tabRegionDialog')
        layout = QVBoxLayout(dialog)
        form = QFormLayout()
        layout.addLayout(form)
        name = QLineEdit(region.name, dialog)
        name.setObjectName('regionName')
        form.addRow(self.tr('Name'), name)
        placement = QComboBox(dialog)
        placement.setObjectName('regionPlacement')
        placement.addItem(self.tr('Snap to contour'), 'snap')
        placement.addItem(self.tr('Draw manually'), 'manual')
        placement.setCurrentIndex(placement.findData(region.placement_mode))
        form.addRow(self.tr('Tab placement'), placement)
        fields = {}
        units = self.panel.binding.project.units
        for key, text in (('height', self.tr('Tab top')), ('xy_feed', self.tr('XY feed')), ('z_feed', self.tr('Z feed'))):
            field = QLineEdit(dialog)
            field.setObjectName('region_'+key)
            set_number(field, getattr(region, key), self.panel.binding.project.units, 'length' if key == 'height' else 'feed')
            fields[key] = field
            form.addRow(text+' ['+units+('/min' if key != 'height' else '')+']', field)
        scope = QComboBox(dialog)
        scope.setObjectName('regionScope')
        for text, key in ((self.tr('Choose assignment…'), ''), (self.tr('Global'), 'global'), (self.tr('Step'), 'steps'), (self.tr('Selected operations'), 'operations')):
            scope.addItem(text, key)
        scope.setCurrentIndex(scope.findData(initial_scope))
        form.addRow(self.tr('Assignment'), scope)
        targets = QTreeWidget(dialog)
        targets.setObjectName('regionTargets')
        targets.setHeaderLabels([self.tr('Assignment')])
        targets.setMinimumHeight(180)
        layout.addWidget(targets)
        no_intersection = QLabel(self.tr('No intersecting contour. Change the region.'), dialog)
        no_intersection.setObjectName('regionNoIntersection')
        no_intersection.setWordWrap(True)
        no_intersection.setVisible(not candidates)
        layout.addWidget(no_intersection)
        clear_exclusions = QCheckBox(self.tr('Clear local exclusions ({0})').format(len(region.excluded)), dialog)
        clear_exclusions.setVisible(bool(region.excluded))
        layout.addWidget(clear_exclusions)
        choices = {key: set(initial_targets) if key == initial_scope else set() for key in ('steps', 'operations')}
        previous_kind = [None]
        def populate():
            if previous_kind[0] in choices:
                choices[previous_kind[0]] = {targets.topLevelItem(i).data(0, ROLE) for i in range(targets.topLevelItemCount())
                                           if targets.topLevelItem(i).checkState(0) == Qt.CheckState.Checked}
            targets.clear()
            kind = scope.currentData()
            previous_kind[0] = kind
            for step in self.panel.binding.project.steps:
                if step.id not in candidate_steps:
                    continue
                rows = [(step.id, step.name)] if kind == 'steps' else [(e.id, step.name+' / '+self.panel.entry_items[e.id].text(0))
                        for e in step.entries if e.id in candidate_operations and e.id in self.panel.entry_items]
                for identity, text in rows:
                    item = QTreeWidgetItem(targets, [text])
                    item.setData(0, ROLE, identity)
                    item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable)
                    checked = (kind == 'global' and (identity not in region.excluded or clear_exclusions.isChecked())
                               or kind != 'global' and identity in choices.get(kind, ()))
                    item.setCheckState(0, Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)
            targets.setEnabled(kind in ('steps', 'operations'))
        scope.currentIndexChanged.connect(populate)
        clear_exclusions.toggled.connect(populate)
        populate()
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, dialog)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(bool(candidates) or not creating)
        layout.addWidget(buttons)
        def accept():
            from math import isfinite
            if creating and not candidates:
                return
            chosen = [targets.topLevelItem(i).data(0, ROLE) for i in range(targets.topLevelItemCount())
                      if targets.topLevelItem(i).checkState(0) == Qt.CheckState.Checked]
            if not scope.currentData() or scope.currentData() != 'global' and not chosen:
                self.panel.report_warning(self.tr('Choose assignment…'))
                return
            try:
                values = {key: float(field.text().replace(',', '.')) if field.isModified() else getattr(region, key)
                          for key, field in fields.items()}
                if any(not isfinite(v) for v in values.values()) or min(values['xy_feed'], values['z_feed']) <= 0:
                    raise ValueError()
            except ValueError:
                self.panel.report_warning(self.tr('Enter valid tab height and positive feeds.'))
                return
            result.name = name.text()
            result.placement_mode = placement.currentData()
            result.scope = scope.currentData()
            result.excluded = [] if clear_exclusions.isChecked() else list(region.excluded)
            result.targets = chosen if result.scope != 'global' else []
            for key, value in values.items():
                setattr(result, key, value)
            dialog.accept()
        buttons.accepted.connect(accept)
        buttons.rejected.connect(dialog.reject)
        return result if dialog.exec() == QDialog.DialogCode.Accepted else None

    def edit_assignment(self):
        region = self.records().get(self.context)
        if region:
            result = self.region_dialog(region)
            if result:
                if result.placement_mode == 'snap' and region.placement_mode != 'snap':
                    vertices = self.standard_vertices(result)
                    if vertices is None:
                        return
                    from dxf2gcode.application.tab_regions import to_drawing
                    result.vertices = to_drawing(self.panel.binding, vertices)
                self.panel.execute(lambda: self.panel.commands.update_region(region.id, name=result.name, scope=result.scope,
                    targets=result.targets, excluded=result.excluded, height=result.height, xy_feed=result.xy_feed, z_feed=result.z_feed,
                    placement_mode=result.placement_mode, vertices=result.vertices))

    def start_draw(self):
        if self.context is None and not self.selected_regions:
            self.update_draw_selection()
        self.pending = self.prepare_pending()
        self.drawing = True
        self.context = None
        self.set_mode(True)
        self.panel.report_warning(self.tr('Draw a rectangle. Escape cancels.') if self.draw_operations else
                                  self.tr('Select a contour or machining operation before drawing a tab.'))

    def update_draw_selection(self):
        """Capture explicit machining/original selection, not region references."""
        if self.panel.binding is None or self.panel.commands is None:
            self.draw_operations = ()
            return
        selected = set(self.panel.commands.selection)
        self.draw_operations = tuple(e.id for s in self.panel.binding.project.steps for e in s.entries
            if isinstance(e, MachiningOperation) and s.kind in ('contour', 'pocket')
            and (s.id in selected or e.id in selected))
        if self.pending is not None:
            self.pending.scope = 'operations' if self.draw_operations else ''
            self.pending.targets = list(self.draw_operations)

    def prepare_pending(self):
        region = self.assignment_defaults()
        region.scope = 'operations' if self.draw_operations else ''
        region.targets = list(self.draw_operations)
        return region

    def drawing_mode(self):
        import dxf2gcode.bootstrap.runtime_state as g
        return self.creation_mode or g.config.var_dict.get('Tab_Regions', {}).get('creation_mode', 'snap')

    def set_creation_mode(self, mode):
        """The toolbar choice controls new regions, never the selected region."""
        self.creation_mode = mode
        if self.pending is not None:
            self.pending.placement_mode = mode
        if self.mode and not self.drawing:
            self.start_draw()

    def change_drawing_mode(self, mode):
        if self.context in self.records():
            region = self.records()[self.context]
            if region.placement_mode == mode:
                return
            values = dict(placement_mode=mode)
            if mode == 'snap':
                vertices = self.standard_vertices(region)
                if vertices is None:
                    return
                from dxf2gcode.application.tab_regions import to_drawing
                values['vertices'] = to_drawing(self.panel.binding, vertices)
            self.panel.execute(lambda: self.panel.commands.update_region(region.id, **values))
            self.select(region.id)
            return
        self.cancel()
        self.creation_mode = mode
        self.start_draw()

    def choose_region_operation(self, region, creating=False):
        from dxf2gcode.application.tab_regions import overlapping_operations
        eligible = {e for _, e in overlapping_operations(self.panel.binding, region)}
        options = [(s, e) for s in self.panel.binding.project.steps for e in s.entries
                   if isinstance(e, MachiningOperation) and e.id in eligible and
                   (creating or (e.id not in region.excluded and (region.scope == 'global' or
                    region.scope == 'steps' and s.id in region.targets or
                    region.scope == 'operations' and e.id in region.targets)))]
        if not options:
            self.panel.report_warning(self.tr('No intersecting contour. Change the region.'))
            return None
        active = next((pair for pair in options if pair[1].id == self.panel.context), None)
        if len(options) > 1 and active is None:
            menu = QMenu(self.panel)
            for step, entry in options:
                tool = self.panel.binding.project.tools[step.tool_id]
                source = self.panel.binding.sources[entry.geometry_id]
                label = self.tr('{0} · Contour {1} · T{2} · Ø{3} {4}').format(
                    step.name, source.nr, tool.tool_nr,
                    format_number(tool.tool_diameter, self.panel.binding.project.units), self.panel.binding.project.units)
                action = menu.addAction(label)
                action.setData(entry.id)
            action = menu.exec(QCursor.pos())
            if action is None:
                return
            active = next(pair for pair in options if pair[1].id == action.data())
        return active or options[0]

    def standard_vertices(self, region, operation=None):
        from dxf2gcode.application.tab_regions import world_vertices, nominal_contour, square_on_contour
        import dxf2gcode.bootstrap.runtime_state as g
        operation = operation or self.choose_region_operation(region)
        if operation is None:
            return None
        step, entry = operation
        tool = self.panel.binding.project.tools[step.tool_id]
        from dxf2gcode.application.tab_regions import configured_tab_length
        length = configured_tab_length(g.config.var_dict, self.panel.binding.project.units)
        vertices = world_vertices(self.panel.binding, region)
        centre = tuple(sum(p[j] for p in vertices)/len(vertices) for j in (0, 1))
        return square_on_contour(nominal_contour(self.panel.binding.sources[entry.geometry_id]),
                                 centre, tool.tool_diameter+length)

    def confirm_new_region(self, vertices):
        from copy import deepcopy
        from dxf2gcode.application.tab_regions import to_drawing, overlapping_operations
        from dxf2gcode.domain.project.machining_project import new_id
        region = self.pending
        region.vertices = to_drawing(self.panel.binding, vertices)
        eligible = {e for _, e in overlapping_operations(self.panel.binding, region)}
        targets = set(region.targets) & eligible
        options = [(s, e) for s in self.panel.binding.project.steps for e in s.entries
                   if isinstance(e, MachiningOperation) and e.id in targets]
        groups = {}
        for step, entry in options:
            shape = (self.standard_vertices(region, (step, entry)) if region.placement_mode == 'snap' else vertices)
            if shape not in groups:
                target = deepcopy(region)
                target.id = region.id if not groups else new_id()
                target.vertices = to_drawing(self.panel.binding, shape)
                target.scope, target.targets = 'operations', []
                groups[shape] = target
            groups[shape].targets.append(entry.id)
        regions = list(groups.values())
        if regions:
            selection = self.draw_operations
            self.panel.execute(lambda: self.panel.commands.create_regions(regions))
            self.draw_operations = selection
            self.last_height = region.height
            self.last_units = self.panel.binding.project.units
            self.select(regions[0].id)
        else:
            self.panel.report_warning(self.tr('No selected machining contour intersects this region.'))
        self.gesture = None
        self.preview_segments = ()
        self.drawing = True
        self.pending = self.prepare_pending()
        self.repaint()

    def cancel(self):
        self.close_dimension_editor()
        self.drawing = False
        self.gesture, self.pending = None, None
        self.preview_segments = ()
        self.preview_timer.stop()
        self.repaint()

    def dimension_labels(self, view=None):
        from dxf2gcode.application.tab_regions import world_vertices, rectangle_size
        if not self.mode or not self.panel.binding or self.gesture is not None:
            return ()
        vertices = (world_vertices(self.panel.binding, self.records()[self.context])
                    if self.context in self.records() else ())
        if len(vertices) != 4:
            return ()
        view = view or self.panel.window.canvas
        metrics = QFontMetricsF(view.font())
        units = self.panel.binding.project.units
        labels = []
        sizes = rectangle_size(vertices)
        projected = [self.projection(v, view) for v in vertices]
        centres = [(projected[i]+projected[(i+1) % 4])/2 for i in range(4)]
        top = min(range(4), key=lambda i: (centres[i].y(), centres[i].x()))
        right = max((i for i in range(4) if i % 2 != top % 2), key=lambda i: centres[i].x())
        for edge in (top, right):
            axis = edge % 2
            value = sizes[axis]
            p = centres[edge]
            text = format_number(value, units)+' '+units
            width, height = metrics.horizontalAdvance(text)+12, metrics.height()+6
            rect = QtCore.QRectF(p.x()-width/2, p.y()-height/2, width, height)
            labels.append((axis, rect, text, value))
        labels.sort(key=lambda label: label[0])
        return labels

    def close_dimension_editor(self):
        editor, self.dimension_editor = self.dimension_editor, None
        if editor is not None:
            editor.hide()
            editor.deleteLater()

    def edit_dimension(self, axis, rect, value, view):
        self.close_dimension_editor()
        identity = self.context
        editor = QLineEdit(view.viewport())
        editor.setObjectName('tabDimensionEditor')
        editor.setProperty('dimensionAxis', axis)
        editor.setGeometry(rect.toAlignedRect().adjusted(-3, -3, 3, 3))
        initial_text = format_number(value, self.panel.binding.project.units)
        editor.setText(initial_text)
        editor.setToolTip(self.tr('Enter a positive size. Enter confirms; Escape cancels.'))
        editor.installEventFilter(self)
        self.dimension_editor = editor

        def confirm():
            from dxf2gcode.application.tab_regions import world_vertices, resize_rectangle, to_drawing
            entered = editor.isModified() or editor.text() != initial_text
            try:
                # Formatting the initial text must never round stored geometry.
                number = float(editor.text().replace(',', '.')) if entered else value
                vertices = world_vertices(self.panel.binding, self.records()[identity])
                changed = resize_rectangle(vertices, axis, number)
            except (ValueError, KeyError):
                editor.setFocus()
                editor.selectAll()
                return
            self.close_dimension_editor()
            if number != value or entered and self.records()[identity].placement_mode != 'manual':
                values = dict(placement_mode='manual')
                if number != value:
                    values['vertices'] = to_drawing(self.panel.binding, changed)
                self.panel.execute(lambda: self.panel.commands.update_region(identity, **values))
                self.select(identity)
            self.repaint()

        editor.returnPressed.connect(confirm)
        # Clicking elsewhere cancels, rather than accepting an accidental value.
        editor.show()
        editor.raise_()
        editor.setFocus()
        editor.selectAll()
        self.repaint()

    def snap_gesture(self, gesture, choose=False):
        from dxf2gcode.application.tab_regions import alignment_candidates, alignment_contours, align_rectangle
        if 'snap_contours' not in gesture:
            gesture['snap_contours'] = alignment_contours(self.panel.binding)
        candidates = alignment_candidates(self.panel.binding, gesture['vertices'], gesture['snap_contours'])
        if len(candidates) == 1:
            gesture['vertices'] = align_rectangle(gesture['vertices'], next(iter(candidates.values())))
        elif len(candidates) > 1 and choose:
            identities = list(candidates)
            labels = [self.tr('Contour {0} · {1}').format(self.panel.binding.sources[g].nr, g) for g in identities]
            label, accepted = QInputDialog.getItem(self.panel, self.tr('Align tab region'),
                                                   self.tr('Choose original contour'), labels, 0, False)
            if accepted:
                gesture['vertices'] = align_rectangle(gesture['vertices'], candidates[identities[labels.index(label)]])
        elif not candidates and choose:
            self.panel.report_warning(self.tr('Alignment needs exactly two crossings with an original contour.'))

    def projection(self, xy, view=None):
        view = view or self.panel.window.canvas
        if hasattr(view, 'tab_project'):
            return view.tab_project(xy)
        if hasattr(view, 'viewportTransform'):
            return view.viewportTransform().map(QtCore.QPointF(xy[0], -xy[1]))
        z = xy[2] if len(xy) > 2 else self.panel.binding.project.configuration['Depth_Coordinates']['axis3_start_mill_depth']
        return self.panel.canvas_preview.project((xy[0], xy[1], z))

    def displayed(self):
        selected_only = self.selected_only()
        if self.mode and not selected_only:
            return set(self.records())
        operations = set(self.panel.selected_entries())
        if selected_only:
            operations.update(self.related_operations)
        elif self.panel.selection_from_geometry:
            geometries = {g for g, s in self.panel.binding.sources.items() if s.isSelected()}
            operations.update(e.id for s in self.panel.binding.project.steps for e in s.entries
                              if isinstance(e, MachiningOperation) and e.geometry_id in geometries)
        result = self.regions_for_operations(operations)
        result.update(self.selected_regions)
        if self.context in self.records():
            result.add(self.context)
        return result

    def paths(self, view=None):
        from dxf2gcode.application.tab_regions import world_vertices
        result = {}
        for identity in self.displayed() if self.panel.binding else ():
            vertices = world_vertices(self.panel.binding, self.records()[identity])
            if self.gesture and identity == self.gesture['id']:
                vertices = self.gesture['vertices']
            if not vertices:
                continue
            path = QPainterPath(self.projection(vertices[0], view))
            for vertex in vertices[1:]:
                path.lineTo(self.projection(vertex, view))
            path.closeSubpath()
            result[identity] = path
        return result

    def hit(self, point, view=None, *, toggle=False):
        stroke = QPainterPathStroker()
        stroke.setWidth(12)
        point = QtCore.QPointF(point)
        for identity, path in self.paths(view).items():
            if stroke.createStroke(path).contains(point) or path.contains(point):
                self.select(identity, toggle=toggle)
                return True
        if self.mode and not toggle:
            self.select_geometry(point, view)
        return self.mode

    def geometry_hits(self, point, view=None):
        """Original contours under a viewport point, independent of compensation."""
        from dxf2gcode.application.tab_regions import nominal_contour
        from dxf2gcode.domain.toolpath.tabs import point as on_curve
        view = view or self.panel.window.canvas
        point = QtCore.QPointF(point)
        stroke = QPainterPathStroker()
        stroke.setWidth(12)
        hits = []
        for identity, source in self.panel.binding.sources.items():
            if is_tab_region(source):
                continue
            path = QPainterPath()
            for geo in nominal_contour(source):
                path.moveTo(self.projection(geo.start, view))
                if geo.kind == 'arc':
                    # Project an analytic scene-space arc, preserving zoom accuracy.
                    scene = QPainterPath(QtCore.QPointF(geo.start[0], -geo.start[1]))
                    from math import degrees
                    scene.arcTo(QtCore.QRectF(geo.center[0]-geo.radius, -geo.center[1]-geo.radius,
                                              2*geo.radius, 2*geo.radius),
                                degrees(geo.start_angle), degrees(geo.sweep))
                    if hasattr(view, 'viewportTransform'):
                        path.addPath(view.viewportTransform().map(scene))
                    else:
                        for i in range(1, 65):
                            path.lineTo(self.projection(on_curve(geo, i/64), view))
                else:
                    path.lineTo(self.projection(geo.end, view))
            if stroke.createStroke(path).contains(point):
                hits.append(identity)
        return hits

    def select_geometry(self, point, view=None):
        """Keep tab editing open while choosing another original or empty space."""
        view = view or self.panel.window.canvas
        point = QtCore.QPointF(point)
        hits = self.geometry_hits(point, view)
        if len(hits) > 1:
            menu = QMenu(view)
            for identity in hits:
                source = self.panel.binding.sources[identity]
                action = menu.addAction(self.tr('Contour {0} · {1}').format(source.nr, source.parentLayer.name))
                action.setData(identity)
            target = view.viewport() if hasattr(view, 'viewport') else view
            action = menu.exec(target.mapToGlobal(QtCore.QPoint(point)))
            if action is None:
                return
            hits = [action.data()]
        self.clear_reference()
        self.panel.busy = True
        try:
            self.panel.tree.clearSelection()
            if self.catalog is not None:
                self.catalog.clearSelection()
            for identity, source in self.panel.binding.sources.items():
                self.panel.window.TreeHandler.setShapeSelected(source, identity in hits)
        finally:
            self.panel.busy = False
        self.panel.geometry_selected()
        self.panel.update_reference_marks()
        self.repaint()

    def paint(self, painter, view=None):
        from dxf2gcode.presentation.qt.canvas2d import ShapeGUI
        for identity, path in self.paths(view).items():
            pen = QPen(ShapeGUI.PEN_BREAK)
            pen.setWidthF(2 if identity == self.context else 1)
            pen.setStyle(Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(path)
            if self.mode and identity == self.context:
                from dxf2gcode.application.tab_regions import world_vertices
                vertices = self.gesture['vertices'] if self.gesture and self.gesture['id'] == identity else world_vertices(self.panel.binding, self.records()[identity])
                if len(vertices) == 4:
                    for v in vertices:
                        p = self.projection(v, view)
                        painter.drawRect(QtCore.QRectF(p.x()-3, p.y()-3, 6, 6))
        if self.gesture and self.gesture['kind'] == 'draw':
            vertices = self.gesture['vertices']
            painter.setPen(QPen(ShapeGUI.PEN_BREAK))
            path = QPainterPath(self.projection(vertices[0], view))
            for v in vertices[1:]:
                path.lineTo(self.projection(v, view))
            path.closeSubpath()
            painter.drawPath(path)
        pen = QPen(ShapeGUI.PEN_BREAK)
        pen.setWidthF(2)
        painter.setPen(pen)
        for segment in self.preview_segments:
            painter.drawLine(self.projection(segment.start, view), self.projection(segment.end, view))
        view = view or self.panel.window.canvas
        palette = view.palette()
        for axis, rect, text, value in self.dimension_labels(view):
            if (self.dimension_editor is not None and hasattr(view, 'viewport') and self.dimension_editor.parent() is view.viewport()
                    and self.dimension_editor.property('dimensionAxis') == axis):
                continue
            painter.setPen(palette.color(QPalette.ColorRole.Highlight) if self.dimension_hover == axis
                           else palette.color(QPalette.ColorRole.Text))
            painter.setBrush(palette.color(QPalette.ColorRole.Base))
            painter.drawRoundedRect(rect, 3, 3)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)

    def repaint(self):
        if hasattr(self.panel, 'canvas_preview'):
            self.panel.canvas_preview.overlay.update()
        comparison = getattr(self.panel.window, 'view_comparison', None)
        if comparison is not None:
            comparison.repaint_overlay()
        if self.dimension_editor is not None:
            self.dimension_editor.raise_()

    def eventFilter(self, watched, event):
        kind = event.type()
        if watched is self.dimension_editor and kind == QtCore.QEvent.Type.FocusOut:
            self.close_dimension_editor()
            return False
        if watched is self.dimension_editor and kind == QtCore.QEvent.Type.KeyPress and event.key() == Qt.Key.Key_Escape:
            self.close_dimension_editor()
            self.repaint()
            return True
        if kind not in (QtCore.QEvent.Type.MouseButtonRelease, QtCore.QEvent.Type.MouseButtonPress,
                        QtCore.QEvent.Type.MouseButtonDblClick, QtCore.QEvent.Type.MouseMove,
                        QtCore.QEvent.Type.KeyPress, QtCore.QEvent.Type.ContextMenu):
            return False
        window = self.panel.window
        for tree in (window.ui.layersShapesTreeView, window.ui.entitiesTreeView):
            if (watched is tree.viewport() and kind in (QtCore.QEvent.Type.MouseButtonPress,
                    QtCore.QEvent.Type.MouseButtonRelease, QtCore.QEvent.Type.MouseButtonDblClick)
                    and event.button() == Qt.MouseButton.LeftButton):
                from dxf2gcode.presentation.qt.treehandling import SHAPE_OBJECT, LAYER_OBJECT
                index = tree.indexAt(event.pos())
                first = index.sibling(index.row(), 0)
                source = getattr(first.data(SHAPE_OBJECT), 'shapeobj', None)
                layer = first.data(LAYER_OBJECT)
                if layer is not None and layer.isBreakLayer():
                    ids = [r.id for r in self.records().values() if self.panel.binding.sources.get(r.geometry_id) is not None
                           and self.panel.binding.sources[r.geometry_id].parentLayer is layer]
                    if kind == QtCore.QEvent.Type.MouseButtonDblClick:
                        tree.setExpanded(first, not tree.isExpanded(first))
                    elif kind == QtCore.QEvent.Type.MouseButtonPress and event.pos().x() < tree.visualRect(first).left():
                        tree.setExpanded(first, not tree.isExpanded(first))
                    self.link_operation = None
                    self.select_regions(ids, source_layer=layer)
                    return True
                region = next((r for r in self.records().values() if source and r.geometry_id == getattr(source, 'geometry_id', None)), None)
                if region:
                    self.select(region.id)
                    if kind == QtCore.QEvent.Type.MouseButtonDblClick:
                        self.edit_assignment()
                    return True
        views = [window.canvas]
        comparison = getattr(window, 'view_comparison', None)
        if comparison is not None:
            renderer = comparison.renderer
            if renderer is not None and renderer.isVisible() and not renderer.spatial:
                views.append(renderer)
        view = next((v for v in views if watched is v.viewport() or watched is v), None)
        if view is not None and kind == QtCore.QEvent.Type.MouseButtonRelease and self.ignore_release:
            self.ignore_release = False
            return True
        if view is not None and kind == QtCore.QEvent.Type.MouseButtonDblClick and event.button() == Qt.MouseButton.LeftButton:
            point = QtCore.QPointF(event.pos())
            stroke = QPainterPathStroker()
            stroke.setWidth(12)
            for identity, path in sorted(reversed(list(self.paths(view).items())), key=lambda pair: pair[0] != self.context):
                if path.contains(point) or stroke.createStroke(path).contains(point):
                    self.gesture = None
                    self.ignore_release = True
                    self.select(identity)
                    self.edit_assignment()
                    return True
        if view is None or not self.mode:
            return False
        if kind == QtCore.QEvent.Type.ContextMenu:
            return False
        if kind == QtCore.QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Escape:
                self.cancel() if self.gesture or self.drawing else self.set_mode(False)
                return True
            if event.key() == Qt.Key.Key_Delete:
                self.remove()
                return True
        if kind not in (QtCore.QEvent.Type.MouseButtonPress, QtCore.QEvent.Type.MouseMove, QtCore.QEvent.Type.MouseButtonRelease):
            return False
        if kind != QtCore.QEvent.Type.MouseMove and event.button() != Qt.MouseButton.LeftButton:
            return False
        if hasattr(view, 'tab_scene_point'):
            xy = view.tab_scene_point(event.pos())
        else:
            p = view.mapToScene(event.pos())
            xy = (p.x(), -p.y())
        from dxf2gcode.application.tab_regions import world_vertices, to_drawing
        label = next((label for label in self.dimension_labels(view)
                      if label[1].contains(QtCore.QPointF(event.pos()))), None)
        if not self.gesture and kind == QtCore.QEvent.Type.MouseMove:
            hover = label[0] if label else None
            if hover != self.dimension_hover:
                self.dimension_hover = hover
                view.viewport().setCursor(Qt.CursorShape.PointingHandCursor if label else Qt.CursorShape.ArrowCursor)
                self.repaint()
            return label is not None
        if kind == QtCore.QEvent.Type.MouseButtonPress:
            control = bool(event.modifiers() & Qt.KeyboardModifier.ControlModifier)
            handles = world_vertices(self.panel.binding, self.records()[self.context]) if self.context in self.records() else ()
            handle_distance = min(((self.projection(v, view)-QtCore.QPointF(event.pos())).manhattanLength()
                                   for v in handles), default=float('inf')) if len(handles) == 4 else float('inf')
            on_handle = handle_distance <= 4 and (label is None or handle_distance <
                        (label[1].center()-QtCore.QPointF(event.pos())).manhattanLength())
            if label and not on_handle and not control:
                self.edit_dimension(label[0], label[1], label[3], view)
                return True
            point = QtCore.QPointF(event.pos())
            for identity, path in sorted(reversed(list(self.paths(view).items())), key=lambda pair: pair[0] != self.context):
                already_selected = self.context == identity
                vertices = world_vertices(self.panel.binding, self.records()[identity])
                corner = next((i for i, v in enumerate(vertices) if already_selected and len(vertices) == 4 and
                               (self.projection(v, view)-point).manhattanLength() <= 9), None)
                stroke = QPainterPathStroker()
                stroke.setWidth(12 if already_selected else 4)
                if corner is not None or path.contains(point) or stroke.createStroke(path).contains(point):
                    if not control:
                        self.select(identity)
                    action = ('resize' if corner is not None else 'move') if already_selected else 'select'
                    self.gesture = dict(kind=action, id=identity,
                                        start=xy, vertices=vertices, original=vertices, corner=corner,
                                        press=event.pos(), control_press=control)
                    break
            if self.gesture is None and self.drawing:
                if self.draw_operations:
                    self.pending.scope, self.pending.targets = 'operations', list(self.draw_operations)
                    self.gesture = dict(kind='draw', id=None, start=xy, vertices=(xy, xy, xy, xy))
                else:
                    self.gesture = dict(kind='select', id=None, vertices=(), pick_geometry=True, press=event.pos())
            if self.gesture is not None:
                self.dimension_hover = None
                view.viewport().unsetCursor()
                self.repaint()
            return True
        if self.gesture and kind == QtCore.QEvent.Type.MouseMove:
            gesture = self.gesture
            if 'press' in gesture and not gesture.get('dragged'):
                gesture['dragged'] = (event.pos() - gesture['press']).manhattanLength() > 4
                if gesture.get('control_press') and not gesture['dragged']:
                    return True
            if gesture['kind'] == 'select':
                return True
            x, y = gesture['start']
            if gesture['kind'] == 'draw':
                gesture['vertices'] = ((x, y), (xy[0], y), xy, (x, xy[1]))
            elif gesture['kind'] == 'move':
                gesture['vertices'] = tuple((a+xy[0]-x, b+xy[1]-y) for a, b in gesture['original'])
            else:
                vertices = list(gesture['original'])
                i = gesture['corner']
                opposite = vertices[(i+2) % 4]
                u = tuple(vertices[(i+1) % 4][j]-opposite[j] for j in (0, 1))
                v = tuple(vertices[(i-1) % 4][j]-opposite[j] for j in (0, 1))
                delta = (xy[0]-opposite[0], xy[1]-opposite[1])
                det = u[0]*v[1]-u[1]*v[0]
                if abs(det) > 1e-15:
                    a = (delta[0]*v[1]-delta[1]*v[0])/det
                    b = (u[0]*delta[1]-u[1]*delta[0])/det
                    if abs(a*b) > 1e-6:
                        vertices[i] = xy
                        vertices[(i+1) % 4] = tuple(opposite[j]+a*u[j] for j in (0, 1))
                        vertices[(i-1) % 4] = tuple(opposite[j]+b*v[j] for j in (0, 1))
                        gesture['vertices'] = tuple(vertices)
            gesture['snap'] = bool(event.modifiers() & Qt.KeyboardModifier.ControlModifier)
            gesture['unsnapped'] = gesture['vertices']
            if gesture['snap']:
                self.snap_gesture(gesture)
            self.preview_segments = ()
            self.preview_timer.start(120)
            self.repaint()
            return True
        if kind == QtCore.QEvent.Type.MouseButtonRelease:
            gesture = self.gesture
            control = bool(event.modifiers() & Qt.KeyboardModifier.ControlModifier)
            if gesture:
                identity = gesture['id']
                if (identity is not None and not gesture.get('dragged')
                        and (event.pos() - gesture['press']).manhattanLength() <= 4
                        and (control or gesture.get('control_press'))):
                    self.gesture = None
                    self.preview_timer.stop()
                    self.preview_segments = ()
                    self.select(identity, toggle=control)
                    return True
                if gesture['kind'] == 'select':
                    self.gesture = None
                    if gesture.get('pick_geometry'):
                        self.select_geometry(event.pos(), view)
                        self.pending = self.prepare_pending()
                        if (event.pos()-gesture['press']).manhattanLength() > 4:
                            self.panel.report_warning(self.tr('Select a contour or machining operation before drawing a tab.'))
                    elif gesture.get('control_press'):
                        self.select(identity)
                    self.repaint()
                    return True
                self.preview_timer.stop()
                gesture['vertices'] = gesture.get('unsnapped', gesture['vertices'])
                if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                    self.snap_gesture(gesture, choose=True)
                self.preview_segments = ()
                self.gesture = None
                vertices = gesture['vertices']
                area = abs(sum(a[0]*b[1]-b[0]*a[1] for a, b in zip(vertices, vertices[1:]+vertices[:1])))
                if area > 1e-12:
                    local = to_drawing(self.panel.binding, vertices)
                    if gesture['kind'] == 'draw':
                        self.confirm_new_region(vertices)
                    elif vertices != gesture['original']:
                        region = self.records()[gesture['id']]
                        if gesture['kind'] == 'resize' and region.placement_mode == 'snap':
                            from dataclasses import replace
                            changed = self.standard_vertices(replace(region, vertices=local))
                            if changed is None:
                                self.repaint()
                                return True
                            local = to_drawing(self.panel.binding, changed)
                        self.panel.execute(lambda: self.panel.commands.update_region(gesture['id'], vertices=local))
                        self.select(gesture['id'])
                elif gesture['kind'] == 'draw':
                    self.select_geometry(event.pos(), view)
                    self.pending = self.prepare_pending()
                self.repaint()
            elif self.dimension_editor is None and not control:
                self.select_geometry(event.pos(), view)
            return True
        return self.gesture is not None

    def compute_preview(self):
        if not self.gesture or self.gesture['kind'] == 'select':
            return
        from copy import copy
        from dataclasses import replace
        from dxf2gcode.application.tab_regions import overlapping_operations, to_drawing
        from dxf2gcode.application.toolpath.projections import plan_preview_segments
        live = self.panel.binding
        source = self.pending if self.gesture['kind'] == 'draw' else self.records()[self.gesture['id']]
        region = replace(source, scope=source.scope or 'global', vertices=to_drawing(live, self.gesture['vertices']))
        targets = {entry for _, entry in overlapping_operations(live, region, assigned_only=True)}
        if self.selected_only():
            targets.intersection_update(set(self.panel.selected_entries()) | self.related_operations)
        if not targets:
            return
        binding = copy(live)
        binding.project = replace(live.project, regions={**live.project.regions, region.id: region})
        # Machine modes using predecessor state still need the complete export order.
        subset = targets if binding.project.configuration['General']['machine_type'] == 'milling' else None
        layers = binding.materialize(allow_unresolved=True, operation_ids=subset)
        segments = []
        for layer in layers.non_break_layer_iter():
            if layer.should_ignore():
                continue
            for shape in layer.shapes.not_disabled_iter():
                if shape.operation_id not in targets or not hasattr(shape, 'geos'):
                    continue
                prepare_shape(shape, build_preview=False)
                result = preview_result(shape, self.panel.window.MyPostProcessor, layers)
                if result.plan is not None:
                    actions = tuple(a if a.modifier_id == region.id else replace(a, role='cut') for a in result.plan.actions)
                    segments.extend(s for s in plan_preview_segments(replace(result.plan, actions=actions)) if s.role == 'tab')
        self.preview_segments = tuple(segments)
        self.repaint()
