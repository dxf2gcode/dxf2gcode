"""Imported global BREAKS regions presented as machining modifiers.

The existing project entries remain the storage/export contract. References in
the tree are views of those entries, never additional machining operations.
"""
from collections import defaultdict
from dxf2gcode.presentation.qt.qt_compat import QtCore
from dxf2gcode.presentation.qt.qt_compat.QtGui import QPainterPath, QPainterPathStroker, QPen, QIcon, QPixmap, QPainter, QPalette
from dxf2gcode.presentation.qt.qt_compat.QtWidgets import (
    QGroupBox, QVBoxLayout, QFormLayout, QLabel, QLineEdit, QCheckBox, QPushButton, QTreeWidgetItem, QStyle)
from dxf2gcode.presentation.qt.numeric_display import set_number
from dxf2gcode.domain.project.machining_project import MachiningOperation
from dxf2gcode.adapters.toolpath.preparation import prepare_shape
from dxf2gcode.adapters.toolpath.preview import preview_result

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


class TabModifiers:
    def tr(self, text):
        return QtCore.QCoreApplication.translate('TabModifiers', text)

    def __init__(self, panel):
        self.panel = panel
        self.mode = False
        self.context = None
        self.project = None
        self.usage = {}
        self.groups = []
        self.nodes = {}
        self.updating = False
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
        self.fields = {}
        for key, label in (('axis3_mill_depth', self.tr('Tab top')),
                           ('f_g1_plane', self.tr('XY feed')), ('f_g1_depth', self.tr('Z feed'))):
            field = QLineEdit(self.editor)
            field.setObjectName('tabModifier_'+key)
            field.setMaximumWidth(140)
            form.addRow(label, field)
            field.editingFinished.connect(lambda key=key: self.commit(key))
            self.fields[key] = field
        self.form = form
        self.enabled = QCheckBox(self.tr('Region enabled'), self.editor)
        self.enabled.toggled.connect(self.change_enabled)
        layout.addWidget(self.enabled)
        self.info = QLabel(self.editor)
        self.info.setWordWrap(True)
        layout.addWidget(self.info)
        self.remove_button = QPushButton(self.tr('Remove region'), self.editor)
        self.remove_button.clicked.connect(self.remove)
        layout.addWidget(self.remove_button)
        layout.addStretch(1)
        self.editor.hide()

    def records(self):
        binding = self.panel.binding
        return {entry.id: (step, entry, binding.sources.get(entry.geometry_id))
                for step in binding.project.steps if step.kind == 'break'
                for entry in step.entries if isinstance(entry, MachiningOperation)} if binding else {}

    def reset(self):
        self.project = None
        self.usage = {}
        self.context = None
        self.mode = False
        self.editor.hide()
        if self.panel.buttons.get('tabs') is not None:
            self.panel.buttons['tabs'].setChecked(False)

    def update_usage(self, layers):
        binding = self.panel.binding
        if binding.project is self.project:
            return
        records = self.records()
        usage = defaultdict(lambda: defaultdict(set))
        if records:
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
                    plan = view.toolpath_plan
                    for action in plan.actions if plan is not None else ():
                        if action.modifier_id in records and action.kind in ('linear_xy', 'arc'):
                            endpoints = action.args[1:3] if action.kind == 'arc' else action.args[:2]
                            ends = tuple(sorted(tuple(round(v, 10) for v in point) for point in endpoints))
                            curve = (('arc', tuple(round(v, 10) for v in action.args[6]), round(abs(action.args[8]), 10))
                                     if action.kind == 'arc' else ('line',))
                            usage[layer.machining_step_id][action.modifier_id].add((view.operation_id, ends, curve))
        self.project = binding.project
        self.usage = {step: dict(regions) for step, regions in usage.items()}
        self.populate_tree()

    def populate_tree(self):
        panel, tree = self.panel, self.panel.tree
        was_busy = panel.busy
        panel.busy = True
        try:
            expanded = {group.data(0, ROLE): group.isExpanded() for group in self.groups
                        if group.treeWidget() is tree}
            for group in self.groups:
                if group.treeWidget() is not tree:
                    continue
                parent = group.parent()
                if parent is not None:
                    parent.removeChild(group)
                else:
                    tree.takeTopLevelItem(tree.indexOfTopLevelItem(group))
            self.groups, self.nodes = [], {}
            records = self.records()
            button = panel.buttons.get('tabs')
            if button is not None:
                button.setVisible(bool(records))
            if not records:
                self.mode, self.context = False, None
            used = set()
            roots = {tree.topLevelItem(i).data(0, ROLE)[1]: tree.topLevelItem(i)
                     for i in range(tree.topLevelItemCount()) if tree.topLevelItem(i).data(0, ROLE)[0] == 'step'}
            def group(parent, key, region_ids, count):
                caption = (self.tr('Holding tabs — {0} regions, {1} segments').format(len(region_ids), count)
                           if parent else self.tr('Imported tab regions — currently ineffective'))
                item = QTreeWidgetItem(parent if parent is not None else tree, [caption])
                item.setFirstColumnSpanned(True)
                item.setData(0, ROLE, ('modifier_group', key))
                item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                item.setExpanded(expanded.get(item.data(0, ROLE), False))
                self.groups.append(item)
                for identity in region_ids:
                    step, entry, shape = records[identity]
                    label = self.tr('Tab region {0} · global').format(shape.nr if shape else identity[:8])
                    if not entry.enabled:
                        label += ' · ' + self.tr('Disabled')
                    child = QTreeWidgetItem(item, [label])
                    child.setFirstColumnSpanned(True)
                    child.setData(0, ROLE, ('modifier', identity))
                    child.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                    child.setToolTip(0, self.scope.text()+'\n'+step.name)
                    self.nodes.setdefault(identity, child)
                    if not parent:
                        child.setIcon(0, panel.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxInformation))
                return item
            if self.project is panel.binding.project:
                for step_id, regions in self.usage.items():
                    if step_id in roots:
                        ids = [identity for identity in records if identity in regions]
                        group(roots[step_id], step_id, ids, sum(len(parts) for parts in regions.values()))
                        used.update(ids)
            unused = [identity for identity in records if identity not in used]
            if unused:
                group(None, 'unused', unused, 0)
            if self.context in self.nodes:
                node = self.nodes[self.context]
                node.parent().setExpanded(True)
                tree.setCurrentItem(node)
        finally:
            panel.busy = was_busy

    def select(self, identity):
        if identity not in self.records():
            return
        self.context = identity
        self.panel.context = None
        self.panel.commands.selection = ()
        self.set_mode(True)
        affected = {part[0] for regions in self.usage.values()
                    for part in regions.get(identity, ())}
        geometries = {entry.geometry_id for step in self.panel.binding.project.steps
                      for entry in step.entries if entry.id in affected}
        was_busy = self.panel.busy
        self.panel.busy = True
        try:
            for geometry, source in self.panel.binding.sources.items():
                source.setSelected(geometry in geometries)
        finally:
            self.panel.busy = was_busy
        self.panel.refresh_preview()
        self.panel.show_parameters()
        self.panel.canvas_preview.overlay.update()

    def set_mode(self, enabled):
        self.mode = bool(enabled)
        button = self.panel.buttons.get('tabs')
        if button is not None:
            button.setChecked(self.mode)
        if not self.mode:
            self.context = None
            if hasattr(self.panel, 'parameter_editor'):
                self.panel.show_parameters()
        if hasattr(self.panel, 'canvas_preview'):
            self.panel.canvas_preview.overlay.update()

    def open_from_geometry(self, shapes):
        geometries = {getattr(shape, 'geometry_id', None) for shape in shapes}
        identity = next((identity for identity, (_, entry, _) in self.records().items()
                         if entry.geometry_id in geometries), None)
        if identity is not None:
            self.panel.window.ui.mytabWidget.setCurrentWidget(self.panel)
            self.select(identity)
            node = self.nodes.get(identity)
            if node is not None:
                self.panel.tree.setCurrentItem(node)
                self.panel.tree.scrollToItem(node)

    def show(self):
        record = self.records().get(self.context)
        if record is None:
            self.context = None
            self.editor.hide()
            return False
        step, entry, shape = record
        values = self.panel.binding.project.resolve(step, entry)[0]
        units = self.panel.binding.project.units
        self.updating = True
        try:
            self.origin.setText(self.tr('Source: {0}').format(step.name))
            self.enabled.setChecked(entry.enabled)
            for key, field in self.fields.items():
                set_number(field, values.get(key), units, 'feed' if key.startswith('f_') else 'length')
                field.setModified(False)
                label = {'axis3_mill_depth': self.tr('Tab top'), 'f_g1_plane': self.tr('XY feed'), 'f_g1_depth': self.tr('Z feed')}[key]
                self.form.labelForField(field).setText(label+' ['+units+('/min' if key.startswith('f_') else '')+']')
            count = sum(len(regions[self.context]) for regions in self.usage.values() if self.context in regions)
            self.info.setText(self.tr('Effective tab segments: {0}. Pass selection belongs to the machining contour.').format(count))
            self.editor.show()
        finally:
            self.updating = False
        return True

    def commit(self, key):
        field = self.fields[key]
        if self.updating or not field.isModified() or self.context not in self.records():
            return
        from math import isfinite
        try:
            value = float(field.text().replace(',', '.'))
            if not isfinite(value):
                raise ValueError()
        except ValueError:
            self.panel.report_warning(self.tr('Enter a finite number.'))
            self.show()
            return
        self.panel.execute(lambda: self.panel.commands.update_entries([self.context], {key: value}))

    def change_enabled(self, value):
        if not self.updating and self.context in self.records():
            self.panel.execute(lambda: self.panel.commands.update_entries([self.context], enabled=value))

    def remove(self):
        if self.context in self.records():
            self.panel.execute(lambda: self.panel.commands.remove([self.context]))

    def paths(self):
        if not self.mode:
            return {}
        project = self.panel.canvas_preview.project
        result = {}
        for identity, (_, _, shape) in self.records().items():
            if shape is None:
                continue
            z = shape.axis3_start_mill_depth
            start = shape.get_start_end_points(True)
            path = QPainterPath(project((start.x, start.y, z)))
            shape.make_path(lambda caller, start, end: path.lineTo(project((end.x, end.y, z))), lambda caller, start: None)
            result[identity] = path
        return result

    def hit(self, point):
        if not self.mode:
            return False
        point = QtCore.QPointF(point)
        stroke = QPainterPathStroker()
        stroke.setWidth(12)
        hits = [identity for identity, path in self.paths().items() if stroke.createStroke(path).contains(point)]
        if hits:
            self.select(hits[0])
            node = self.nodes.get(hits[0])
            if node is not None:
                self.panel.tree.setCurrentItem(node)
                self.panel.tree.scrollToItem(node)
        return True

    def paint(self, painter):
        from dxf2gcode.presentation.qt.canvas2d import ShapeGUI
        for identity, path in self.paths().items():
            pen = QPen(ShapeGUI.PEN_BREAK)
            pen.setWidthF(2 if identity == self.context else 1)
            pen.setStyle(Qt.PenStyle.DashDotLine)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(path)
