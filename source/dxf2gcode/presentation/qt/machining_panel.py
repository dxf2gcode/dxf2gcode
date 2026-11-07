"""The machining tab: one document, explicit editing context and command history."""

import json
from dxf2gcode.presentation.qt.numeric_display import format_number
from dataclasses import replace
from uuid import uuid4

import dxf2gcode.bootstrap.runtime_state as g
from dxf2gcode.application.machining import MachiningDrawing, ProjectConfiguration
from dxf2gcode.application.machining_actions import MachiningCommands
from dxf2gcode.domain.project.layercontent import Layers
from dxf2gcode.domain.project.machining_project import MachiningOperation, LiteralAction, PARAMETERS
from dxf2gcode.domain.project.tool_settings import ToolSettings
from dxf2gcode.presentation.qt.qt_compat import QtCore
from dxf2gcode.presentation.qt.qt_compat.QtGui import QDrag, QAction, QKeySequence, QGuiApplication, QIcon
from dxf2gcode.presentation.qt.qt_compat.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QTreeWidget, QTreeWidgetItem,
    QAbstractItemView, QLabel, QToolBar, QStyle, QHeaderView, QSizePolicy,
    QDialog, QDialogButtonBox, QLineEdit, QComboBox, QMenu, QInputDialog, QScrollArea, QFrame)

Qt = QtCore.Qt
ROLE = Qt.ItemDataRole.UserRole
SOURCE_ROLE = int(ROLE) + 1
MIME = 'application/x-dxf2gcode-machining'


class MachiningTree(QTreeWidget):
    def __init__(self, panel):
        super().__init__(panel)
        self.panel = panel
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.drop_marker = QFrame(self.viewport())
        self.drop_marker.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.drop_marker.hide()

    def payload(self):
        items = self.selectedItems()
        kinds = {item.data(0, ROLE)[0] for item in items}
        if len(kinds) != 1 or not kinds <= {'step', 'entry'}:
            return None
        return dict(token=self.panel.token, generation=self.panel.generation,
                    kind=next(iter(kinds)), ids=[i.data(0, ROLE)[1] for i in items])

    def startDrag(self, actions):
        payload = self.payload()
        if payload is None:
            return
        mime = QtCore.QMimeData()
        mime.setData(MIME, json.dumps(payload).encode())
        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.exec(Qt.DropAction.MoveAction | Qt.DropAction.CopyAction)

    def read_payload(self, event):
        try:
            if not event.mimeData().hasFormat(MIME):
                return None
            value = json.loads(bytes(event.mimeData().data(MIME)).decode())
            if (value['token'] != self.panel.token or value['generation'] != self.panel.generation
                    or value['kind'] not in ('step', 'entry') or not isinstance(value['ids'], list)
                    or not value['ids'] or any(not isinstance(i, str) for i in value['ids'])):
                return None
            return value
        except (ValueError, KeyError, TypeError):
            return None

    def dragEnterEvent(self, event):
        if self.read_payload(event):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        payload = self.read_payload(event)
        point = event.position().toPoint() if hasattr(event, 'position') else event.pos()
        item = self.itemAt(point)
        if payload is None or item is None or item.data(0, ROLE)[0] not in ('step', 'entry'):
            self.drop_marker.hide()
            event.ignore()
            return
        rect = self.visualItemRect(item)
        after = point.y() >= rect.center().y()
        if item.data(0, ROLE)[0] == 'step' and (payload['kind'] == 'entry' or after):
            if item.isExpanded() and item.childCount():
                rect = self.visualItemRect(item.child(item.childCount()-1))
            after = True
        y = rect.bottom() if after else rect.top()
        self.drop_marker.setStyleSheet('background-color: %s;' % self.palette().highlight().color().name())
        self.drop_marker.setGeometry(0, y, self.viewport().width(), 3)
        self.drop_marker.show()
        self.drop_marker.raise_()
        event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        self.drop_marker.hide()
        event.accept()

    def dropEvent(self, event):
        self.drop_marker.hide()
        payload = self.read_payload(event)
        if payload is None:
            event.ignore()
            return
        point = event.position().toPoint() if hasattr(event, 'position') else event.pos()
        item = self.itemAt(point)
        if item is None or item.data(0, ROLE)[0] not in ('step', 'entry'):
            event.ignore()
            return
        kind, identity = item.data(0, ROLE)
        after = point.y() >= self.visualItemRect(item).center().y()
        modifiers = event.modifiers() if hasattr(event, 'modifiers') else event.keyboardModifiers()
        copy = bool(modifiers & Qt.KeyboardModifier.ControlModifier)
        if self.panel.drop(payload, kind, identity, after, copy):
            event.setDropAction(Qt.DropAction.CopyAction if copy else Qt.DropAction.MoveAction)
            event.accept()
        else:
            event.ignore()


class MachiningPanel(QWidget):
    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.setMinimumWidth(0)
        self.binding = None
        self.commands = None
        self.token = str(uuid4())
        self.generation = 0
        self.busy = False
        self.context = None
        layout = QVBoxLayout(self)
        bar = QToolBar(self)
        bar.setIconSize(QtCore.QSize(18, 18))
        layout.addWidget(bar)
        self.buttons = {}
        for key, text, icon, callback in (
                ('new', self.tr('Create…'), QStyle.StandardPixmap.SP_FileIcon, self.new_step),
                ('up', self.tr('Move up'), QStyle.StandardPixmap.SP_ArrowUp, lambda: self.nudge(-1)),
                ('down', self.tr('Move down'), QStyle.StandardPixmap.SP_ArrowDown, lambda: self.nudge(1)),
                ('undo', self.tr('Undo'), QStyle.StandardPixmap.SP_ArrowBack, self.undo),
                ('redo', self.tr('Redo'), QStyle.StandardPixmap.SP_ArrowForward, self.redo),
                ('collapse', self.tr('Collapse all'), QStyle.StandardPixmap.SP_TitleBarShadeButton, lambda: self.tree.collapseAll()),
                ('expand', self.tr('Expand all'), QStyle.StandardPixmap.SP_TitleBarUnshadeButton, lambda: self.tree.expandAll())):
            if key == 'collapse':
                spacer = QWidget(bar)
                spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
                bar.addWidget(spacer)
            if key in ('up', 'undo', 'collapse'):
                bar.addSeparator()
            action = bar.addAction(self.style().standardIcon(icon), text)
            action.triggered.connect(callback)
            action.setObjectName('machining_' + key)
            self.buttons[key] = action
        self.buttons['collapse'].setIcon(window.ui.layersCollapsePushButton.icon())
        self.buttons['expand'].setIcon(window.ui.layersExpandPushButton.icon())
        self.buttons['new'].setToolTip(self.tr('Create machining step…'))
        bar.widgetForAction(self.buttons['new']).setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.tree = MachiningTree(self)
        self.tree.setColumnCount(3)
        self.tree.setHeaderLabels([self.tr('Machining'), self.tr('Export'), self.tr('Optimize')])
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for column in (1, 2):
            self.tree.header().setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)
        self.tree.itemExpanded.connect(self.update_tree_actions)
        self.tree.itemCollapsed.connect(self.update_tree_actions)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.menu)
        self.tree.itemSelectionChanged.connect(self.selection_changed)
        self.tree.itemChanged.connect(self.checked)
        self.tree.itemDoubleClicked.connect(self.edit_item)
        layout.addWidget(self.tree, 2)
        self.context_label = QLabel(self.tr('Select a machining operation to edit its values.'), self)
        self.context_label.setWordWrap(True)
        self.context_label.setTextFormat(Qt.TextFormat.PlainText)
        layout.addWidget(self.context_label)
        from dxf2gcode.presentation.qt.machining_parameters import MachiningParameters
        self.parameter_editor = MachiningParameters(self)
        self.parameter_scroll = QScrollArea(self)
        self.parameter_scroll.setWidgetResizable(True)
        self.parameter_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.parameter_scroll.setWidget(self.parameter_editor.frame)
        layout.addWidget(self.parameter_scroll, 3)
        self.notice = QLabel('', self)
        self.notice.setWordWrap(True)
        self.notice.setTextFormat(Qt.TextFormat.PlainText)
        layout.addWidget(self.notice)
        for text, shortcut, callback in ((self.tr('Undo machining action'), 'Ctrl+Z', self.undo),
                                          (self.tr('Redo machining action'), 'Ctrl+Shift+Z', self.redo),
                                          (self.tr('Move up'), 'Alt+Up', lambda: self.nudge(-1)),
                                          (self.tr('Move down'), 'Alt+Down', lambda: self.nudge(1))):
            action = QAction(text, self)
            action.setShortcut(QKeySequence(shortcut))
            action.setShortcutContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
            action.triggered.connect(callback)
            self.addAction(action)
        for text, shortcut, callback in ((self.tr('Edit step'), 'F2', self.edit_step),
                                          (self.tr('Remove'), 'Delete', self.remove)):
            action = QAction(text, self.tree)
            action.setShortcut(QKeySequence(shortcut))
            action.setShortcutContext(Qt.ShortcutContext.WidgetShortcut)
            action.triggered.connect(callback)
            self.tree.addAction(action)
        window.ui.mytabWidget.addTab(self, self.tr('Machining'))
        self.setEnabled(False)
        QtCore.QTimer.singleShot(0, self.initial_sidebar_width)

    def initial_sidebar_width(self):
        self.parameter_editor.update_preferred_columns()
        splitter = self.window.ui.splitter
        sizes = splitter.sizes()
        total = sum(sizes)
        preferred = self.parameter_editor.preferred_width + 40
        if total and len(sizes) == 2:
            splitter.setSizes([preferred, max(1, total-preferred)])

    def attach(self):
        """Migrate after the original model is built, before machining input."""
        binding = self.window.d2g.machining_drawing
        if binding is None:
            self.window.TreeHandler.updateExportOrder(True)
            binding = MachiningDrawing.capture(self.window.layerContents, g.config)
            self.window.d2g.machining_drawing = binding
            if not isinstance(self.window.layerContents, Layers):
                self.window.layerContents = Layers(self.window.layerContents)
            binding.source_layers = self.window.layerContents
            self.window.layerContents.machining_binding = binding
            binding.bind_legacy_editor()
        if binding is not self.binding:
            self.binding = binding
            self.commands = MachiningCommands(binding)
            self.context = None
            self.token = str(uuid4())
        self.setEnabled(True)
        self.freeze_original_trees()
        self.refresh()

    def freeze_original_trees(self):
        for view in (self.window.ui.layersShapesTreeView, self.window.ui.entitiesTreeView):
            view.setDragEnabled(False)
            view.setAcceptDrops(False)
            model = view.model()
            if model is None:
                continue
            blocked = model.blockSignals(True)
            model.setHeaderData(0, Qt.Orientation.Horizontal, '')
            view.setColumnHidden(3, True)
            def walk(parent):
                for row in range(parent.rowCount()):
                    for col in range(parent.columnCount()):
                        item = parent.child(row, col)
                        if item is not None:
                            item.setCheckable(False)
                            item.setData(None, Qt.ItemDataRole.CheckStateRole)
                            item.setEditable(False)
                            item.setDragEnabled(False)
                            item.setDropEnabled(False)
                    walk(parent.child(row, 0))
            walk(model.invisibleRootItem())
            model.blockSignals(blocked)
        self.window.ui.layersGoUpPushButton.setEnabled(False)
        self.window.ui.layersGoDownPushButton.setEnabled(False)

    def kind_text(self, kind):
        return {'contour': self.tr('Contour'), 'pocket': self.tr('Pocket'), 'drill': self.tr('Drilling'),
                'break': self.tr('Holding tabs'), 'ignored': self.tr('Ignored')}[kind]

    def refresh(self, selection=None):
        if self.binding is None:
            return
        selected = set(selection if selection is not None else self.commands.selection)
        self.busy = True
        self.generation += 1
        expanded = {self.tree.topLevelItem(i).data(0, ROLE): self.tree.topLevelItem(i).isExpanded()
                    for i in range(self.tree.topLevelItemCount())}
        self.tree.clear()
        self.entry_items = {}
        project = self.binding.project
        for step in project.steps:
            tool = project.tools[step.tool_id]
            root = QTreeWidgetItem(self.tree, ['%s · %s · T%d' % (step.name, self.kind_text(step.kind), tool.tool_nr)])
            root.setToolTip(0, '%s · Ø%s' % (root.text(0), format_number(tool.tool_diameter, project.units)))
            root.setData(0, ROLE, ('step', step.id))
            for entry in step.entries:
                if isinstance(entry, LiteralAction):
                    text, source = entry.name, self.tr('Custom G-code')
                else:
                    geometry = project.geometries[entry.geometry_id]
                    shape = self.binding.sources.get(entry.geometry_id)
                    text = self.tr('Contour {0}').format(shape.nr if shape else entry.id[:8])
                    source = geometry.source_layer
                    if entry.geometry_id in project.unresolved:
                        source += ' · ' + self.tr('Missing or ambiguous geometry')
                    if entry.legacy_conflict:
                        source += ' · ' + self.tr('Conflicting machining settings')
                item = QTreeWidgetItem(root, [text])
                item.setData(0, ROLE, ('entry', entry.id))
                item.setData(0, SOURCE_ROLE, source)
                item.setToolTip(0, source)
                self.entry_items[entry.id] = item
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(1, Qt.CheckState.Checked if entry.enabled else Qt.CheckState.Unchecked)
                if isinstance(entry, MachiningOperation):
                    item.setCheckState(2, Qt.CheckState.Checked if entry.optimize else Qt.CheckState.Unchecked)
                item.setSelected(entry.id in selected)
                if self.context == entry.id:
                    font = item.font(0)
                    font.setBold(True)
                    item.setFont(0, font)
            root.setExpanded(expanded.get(root.data(0, ROLE), True))
            root.setSelected(step.id in selected)
        unassigned = list(self.binding.unassigned)
        by_geometry = self.binding.operations_by_geometry()
        unassigned += [shape for identity, shape in self.binding.sources.items() if not by_geometry.get(identity)]
        self.unassigned = list(dict.fromkeys(unassigned))
        if self.unassigned:
            root = QTreeWidgetItem(self.tree, [self.tr('Unassigned')])
            root.setData(0, ROLE, ('unassigned', ''))
            for index, shape in enumerate(self.unassigned):
                item = QTreeWidgetItem(root, [self.tr('Contour {0}').format(shape.nr)])
                item.setToolTip(0, shape.parentLayer.name)
                item.setData(0, ROLE, ('geometry', str(index)))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsDragEnabled)
            root.setExpanded(expanded.get(root.data(0, ROLE), True))
        self.buttons['undo'].setEnabled(bool(self.commands.undo_stack))
        self.buttons['redo'].setEnabled(bool(self.commands.redo_stack))
        self.busy = False
        self.update_tree_actions()
        self.show_parameters()

    def update_tree_actions(self, *unused):
        if self.busy:
            return
        roots = [self.tree.topLevelItem(i) for i in range(self.tree.topLevelItemCount())]
        self.buttons['collapse'].setEnabled(any(i.childCount() and i.isExpanded() for i in roots))
        self.buttons['expand'].setEnabled(any(i.childCount() and not i.isExpanded() for i in roots))
        items = self.tree.selectedItems()
        for key, direction in (('up', -1), ('down', 1)):
            movable = False
            if items and all(i.parent() is items[0].parent() for i in items):
                parent = items[0].parent()
                siblings = [parent.child(i) for i in range(parent.childCount())] if parent else roots
                movable = any(0 <= index+direction < len(siblings) and siblings[index+direction] not in items
                              for index, item in enumerate(siblings) if item in items and item.data(0, ROLE)[0] in ('step', 'entry'))
            self.buttons[key].setEnabled(movable)

    def selected_entries(self):
        ids = set()
        for item in self.tree.selectedItems():
            kind, identity = item.data(0, ROLE)
            if kind == 'entry':
                ids.add(identity)
            elif kind == 'step':
                ids.update(e.id for e in self.commands.step(self.binding.project, identity).entries)
        return [e.id for s in self.binding.project.steps for e in s.entries if e.id in ids]

    def current_step(self):
        item = self.tree.currentItem()
        if item is None:
            return None
        kind, identity = item.data(0, ROLE)
        if kind == 'entry':
            return next(s for s in self.binding.project.steps if any(e.id == identity for e in s.entries))
        if kind == 'step':
            return self.commands.step(self.binding.project, identity)
        return None

    def execute(self, callback):
        try:
            result = callback()
        except (ValueError, KeyError, StopIteration) as error:
            self.notice.setText(self.tr('Action rejected: {0}').format(self.error_text(error)))
            return False
        selected = self.commands.selection
        g.config.machine_type = self.binding.project.configuration['General']['machine_type']
        if bool(g.config.metric) != (self.binding.project.units == 'mm'):
            self.window.setMeasurementUnits(int(self.binding.project.units == 'mm'))
        if len(selected) == 1:
            entry = next((e for s in self.binding.project.steps for e in s.entries
                          if e.id == selected[0] and isinstance(e, MachiningOperation)), None)
            if entry is not None and entry.geometry_id in self.binding.sources:
                self.binding.activate_operation(entry.id)
                self.context = entry.id
            elif entry is None:
                self.context = None
        if self.context and not any(e.id == self.context for s in self.binding.project.steps for e in s.entries):
            self.context = None
        self.refresh()
        if result is not None:
            labels = dict(tool=self.tr('Tool'), diameter=self.tr('Tool diameter'), kind=self.tr('Kind'),
                          tool_diameter=self.tr('Tool diameter'), tool_nr=self.tr('Tool'))
            def field_name(key):
                return labels[key] if key in labels else self.parameter_label(key)
            def description(identity):
                step = next((s for s in self.binding.project.steps if s.id == identity or
                             any(e.id == identity for e in s.entries)), None)
                item = self.entry_items.get(identity)
                return (step.name if step else '') + (' / ' + item.text(0) if item else '')
            details = '\n'.join(description(identity) + ': ' + ', '.join('%s: %s → %s' % (field_name(k), *v) for k, v in delta.items())
                                for identity, delta in result.changes)
            self.notice.setText(self.tr('Machining updated. Undo is available.') + ('\n' + details if details else ''))
        self.refresh_preview()
        return True

    def refresh_preview(self):
        scene = getattr(self.window, 'canvas_scene', None)
        if scene is None or self.binding is None:
            return
        with self.binding.preview_batch():
            for shape in self.window.shapes:
                if hasattr(shape, 'machining_binding'):
                    if hasattr(scene, 'graphics_items') and id(shape) not in scene.graphics_items:
                        continue
                    scene.repaint_shape(shape)
                    active = getattr(shape, '_machining_view', None)
                    item = self.entry_items.get(getattr(active, 'operation_id', None))
                    if item is not None:
                        from dxf2gcode.presentation.qt.toolpath_labels import translate_message
                        messages = []
                        for diagnostic in getattr(shape, 'toolpath_diagnostics', ()):
                            message = QtCore.QCoreApplication.translate('Shape', diagnostic.source_message) if diagnostic.source_message else diagnostic.message
                            if diagnostic.message_args:
                                message %= tuple(translate_message(arg) if hasattr(arg, 'context') else arg
                                                 for arg in diagnostic.message_args)
                            messages.append(message)
                        text = item.data(0, SOURCE_ROLE) + (' · ' + '; '.join(messages) if messages else '')
                        item.setToolTip(0, text)
                        item.setIcon(0, self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxWarning) if messages else QIcon())
                    if hasattr(scene, 'set_shape_disabled'):
                        scene.set_shape_disabled(shape, shape.disabled)
        scene.update()
        if self.window.TreeHandler.auto_update_export_order:
            self.draw_route()

    def selection_changed(self):
        self.update_tree_actions()
        if self.busy or self.binding is None:
            return
        ids = self.selected_entries()
        self.commands.selection = tuple(item.data(0, ROLE)[1] for item in self.tree.selectedItems()
                                        if item.data(0, ROLE)[0] in ('step', 'entry'))
        item = self.tree.currentItem()
        self.context = None
        if item is not None and item.data(0, ROLE)[0] == 'entry':
            identity = item.data(0, ROLE)[1]
            entry = next(e for s in self.binding.project.steps for e in s.entries if e.id == identity)
            if isinstance(entry, MachiningOperation) and entry.geometry_id in self.binding.sources:
                self.binding.activate_operation(identity)
                self.context = identity
        elif item is not None and item.data(0, ROLE)[0] == 'step':
            selected = {}
            for step, entry in self.commands.entries(self.binding.project, ids):
                if isinstance(entry, MachiningOperation):
                    selected.setdefault(entry.geometry_id, []).append(entry.id)
            for geometry, operations in selected.items():
                if len(operations) == 1:
                    self.binding.active_operations[geometry] = operations[0]
                else:
                    self.binding.active_operations.pop(geometry, None)
            self.binding.bind_legacy_editor()
        for identity, entry_item in self.entry_items.items():
            font = entry_item.font(0)
            font.setBold(identity == self.context)
            entry_item.setFont(0, font)
        geometries = {e.geometry_id for s, e in self.commands.entries(self.binding.project, ids)
                      if isinstance(e, MachiningOperation)}
        geometries.update(getattr(self.unassigned[int(i.data(0, ROLE)[1])], 'geometry_id', None)
                          for i in self.tree.selectedItems() if i.data(0, ROLE)[0] == 'geometry')
        self.busy = True
        for shape in self.window.shapes:
            selected = getattr(shape, 'geometry_id', None) is not None and shape.geometry_id in geometries
            if any(i.data(0, ROLE)[0] == 'geometry' and self.unassigned[int(i.data(0, ROLE)[1])] is shape
                   for i in self.tree.selectedItems()):
                selected = True
            self.window.TreeHandler.setShapeSelected(shape, selected)
        self.window.TreeHandler.updateSelection(self.window.ui.layersShapesTreeView)
        self.window.TreeHandler.updateSelection(self.window.ui.entitiesTreeView)
        self.busy = False
        self.update_tree_actions()
        self.show_parameters()
        self.refresh_preview()

    def geometry_selected(self):
        if self.busy or self.binding is None:
            return
        geometries = {getattr(s, 'geometry_id', None) for s in self.window.shapes if s.isSelected()}
        by_geometry = self.binding.operations_by_geometry()
        previous = dict(self.binding.active_operations)
        self.binding.active_operations.update({key: options[0][1].id for key, options in by_geometry.items()
                                               if len(options) == 1})
        for key in geometries:
            if len(by_geometry.get(key, ())) > 1:
                self.binding.active_operations.pop(key, None)
        self.binding.bind_legacy_editor()
        ids = [e.id for step in self.binding.project.steps for e in step.entries
               if isinstance(e, MachiningOperation) and e.geometry_id in geometries]
        self.context = ids[0] if len(ids) == 1 else None
        self.commands.selection = tuple(ids)
        self.refresh(ids)
        if previous != self.binding.active_operations:
            self.refresh_preview()

    def show_parameters(self):
        self.parameter_editor.refresh()

    def reverse(self):
        if self.context:
            entry = self.commands.entries(self.binding.project, [self.context])[0][1]
            self.execute(lambda: self.commands.update_entries([self.context], clockwise=not entry.clockwise))

    def start_point(self):
        if not self.context:
            return
        entry = self.commands.entries(self.binding.project, [self.context])[0][1]
        from dxf2gcode.presentation.qt.popupdialog import PopUpDialog
        units = self.binding.project.units
        dialog = PopUpDialog(self.tr('Start point'), ['X ['+units+']', 'Y ['+units+']'],
                             list(entry.start), ['lineEdit', 'lineEdit'])
        if dialog.result is not None:
            self.execute(lambda: self.commands.update_entries(
                [entry.id], start=tuple(float(value) for value in dialog.result)))

    def checked(self, item, column):
        if self.busy or column not in (1, 2):
            return
        kind, identity = item.data(0, ROLE)
        if kind == 'entry':
            key = 'enabled' if column == 1 else 'optimize'
            value = item.checkState(column) == Qt.CheckState.Checked
            commands = self.commands
            # Qt5 still accesses the changed item after emitting itemChanged.
            # Rebuilding the tree inside that signal can free its native item.
            def apply_checked():
                if self.commands is commands:
                    self.execute(lambda: commands.update_entries([identity], **{key: value}))
            QtCore.QTimer.singleShot(0, apply_checked)

    def step_dialog(self, step=None, from_selection=False, global_position=None, selection_count=0):
        dialog = QDialog(self)
        dialog.setObjectName('machiningStepDialog')
        dialog.setWindowTitle(self.tr('Machining step'))
        form = QFormLayout(dialog)
        name = QLineEdit(step.name if step else self.tr('New step'), dialog)
        name.setObjectName('stepName')
        form.addRow(self.tr('Name'), name)
        kinds = QComboBox(dialog)
        for key in ('contour', 'pocket', 'drill', 'break', 'ignored'):
            kinds.addItem(self.kind_text(key), key)
        kinds.setCurrentIndex(kinds.findData(step.kind) if step else 0)
        kinds.setProperty('explicit_kind', False)
        kinds.activated.connect(lambda index: kinds.setProperty('explicit_kind', True))
        form.addRow(self.tr('Kind'), kinds)
        tools = QComboBox(dialog)
        for index, (identity, tool) in enumerate(self.binding.project.tools.items()):
            tools.addItem('T%d · Ø%s · %s rpm · #%d' % (tool.tool_nr, format_number(tool.tool_diameter, self.binding.project.units), format_number(tool.speed, kind='integer'), index+1), identity)
        for number in g.config.vars.Tool_Parameters:
            profile = g.config.vars.Tool_Parameters[number]
            tools.addItem(self.tr('Import profile tool T{0}').format(number),
                          self.profile_tool(number, profile))
        if step:
            tools.setCurrentIndex(tools.findData(step.tool_id))
        form.addRow(self.tr('Tool definition'), tools)
        mode = QComboBox(dialog)
        mode.setObjectName('assignmentMode')
        mode.addItem(self.tr('Move existing assignments'), 'move')
        mode.addItem(self.tr('Additional machining'), 'copy')
        mode.addItem(self.tr('Do not use selection — create empty step'), 'empty')
        if from_selection:
            form.addRow(QLabel(self.tr('{0} contours selected').format(selection_count), dialog))
            form.addRow(self.tr('Assignment'), mode)
        mode.setVisible(from_selection)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, dialog)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        form.addRow(buttons)
        if global_position is not None:
            dialog.adjustSize()
            screen = QGuiApplication.screenAt(global_position) or self.window.screen()
            if screen is not None:
                area = screen.availableGeometry()
                dialog.move(max(area.left(), min(global_position.x(), area.right()-dialog.width()-12)),
                            max(area.top(), min(global_position.y(), area.bottom()-dialog.height()-36)))
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return None
        return (name.text(), kinds.currentData(), tools.currentData(),
                mode.currentData() if from_selection else 'empty', bool(kinds.property('explicit_kind')))

    def new_step(self):
        self.from_selection()

    def from_selection(self, shapes=None, global_position=None):
        if not self.binding:
            return
        if isinstance(shapes, bool):
            shapes = None  # QAction/QPushButton checked state is not a geometry selection.
        shapes = list(shapes) if shapes is not None else [s for s in self.window.shapes if s.isSelected()]
        data = self.step_dialog(from_selection=bool(shapes), global_position=global_position, selection_count=len(shapes))
        if data is None:
            return
        def change():
            copy = data[3] == 'copy'
            ids, unassigned = self.assignment_selection(shapes, copy) if data[3] != 'empty' else ([], [])
            return self.commands.create_step(*data[:3], identities=ids, copy=copy, geometries=unassigned)
        self.execute(change)

    def build_geometry_menu(self, shapes, global_position):
        menu = QMenu(self)
        create = menu.addAction(self.tr('Create machining step…'))
        create.triggered.connect(lambda: self.from_selection(shapes, global_position))
        related = menu.addMenu(self.tr('Related machining steps'))
        geometries = {getattr(shape, 'geometry_id', None) for shape in shapes}
        for step in self.binding.project.steps:
            matches = [e.id for e in step.entries if isinstance(e, MachiningOperation) and e.geometry_id in geometries]
            if matches:
                tool = self.binding.project.tools[step.tool_id]
                action = related.addAction('%s · %s · T%d (%d)' % (step.name, self.kind_text(step.kind), tool.tool_nr, len(matches)))
                action.setData(step.id)
                action.triggered.connect(lambda checked=False, identity=step.id, ids=tuple(matches):
                                         self.navigate_to_step(identity, ids))
        if not related.actions():
            related.addAction(self.tr('No linked machining steps')).setEnabled(False)
        return menu

    def geometry_menu(self, shapes, global_position):
        self.build_geometry_menu(shapes, global_position).exec(global_position)

    def navigate_to_step(self, identity, entries):
        self.window.ui.mytabWidget.setCurrentWidget(self)
        self.context = None
        self.commands.selection = tuple(entries)
        self.refresh(entries)
        root = next((self.tree.topLevelItem(i) for i in range(self.tree.topLevelItemCount())
                     if self.tree.topLevelItem(i).data(0, ROLE) == ('step', identity)), None)
        if root is None:
            return
        root.setExpanded(True)
        self.busy = True
        item = self.entry_items[entries[0]] if len(entries) == 1 else root
        self.tree.selectionModel().setCurrentIndex(self.tree.indexFromItem(item),
                                                   QtCore.QItemSelectionModel.SelectionFlag.NoUpdate)
        self.tree.scrollToItem(item)
        self.busy = False
        self.selection_changed()

    def assignment_selection(self, shapes, copy):
        ids, unassigned = [], []
        by_geometry = self.binding.operations_by_geometry()
        for shape in shapes:
            options = by_geometry.get(getattr(shape, 'geometry_id', None), ())
            if not options:
                unassigned.append(shape)
                continue
            active = self.binding.active_operations.get(shape.geometry_id)
            selected = next((entry.id for step, entry in options if entry.id == active), None)
            if selected is None:
                raise ValueError(self.tr('Select an active operation for contour {0}.').format(shape.nr))
            ids.append(selected)
        return ids, unassigned

    def edit_step(self):
        step = self.current_step()
        if step is None:
            return
        data = self.step_dialog(step)
        if data:
            self.execute(lambda: self.commands.edit_step(step.id, *data[:3], resolve_conflict=data[4]))

    def edit_item(self, item, column):
        kind, identity = item.data(0, ROLE)
        if kind == 'step':
            self.edit_step()
        elif kind == 'entry':
            entry = self.commands.entries(self.binding.project, [identity])[0][1]
            if isinstance(entry, LiteralAction):
                code, accepted = QInputDialog.getMultiLineText(self, self.tr('Custom G-code'), self.tr('G-code'), entry.gcode)
                if accepted:
                    self.execute(lambda: self.commands.update_literal(identity, entry.name, code))

    def remove(self):
        items = self.tree.selectedItems()
        steps = [i.data(0, ROLE)[1] for i in items if i.data(0, ROLE)[0] == 'step']
        if steps:
            if len(steps) != 1 or len(items) != 1:
                self.notice.setText(self.tr('Select one step to remove.'))
                return
            step = self.commands.step(self.binding.project, steps[0])
            if step.entries:
                choices = [self.tr('Cancel'), self.tr('Remove assignments')]
                targets = [s for s in self.binding.project.steps if s.id != step.id]
                choices += [self.tr('Move assignments to {0}').format(s.name) for s in targets]
                choice, accepted = QInputDialog.getItem(self, self.tr('Remove step'),
                    self.tr('Original contours are retained. Choose what happens to the assignments.'), choices, editable=False)
                if not accepted or choice == choices[0]:
                    return
                index = choices.index(choice)
                self.execute(lambda: self.commands.delete_step(step.id, targets[index-2].id if index >= 2 else None))
            else:
                self.execute(lambda: self.commands.delete_step(step.id))
        else:
            ids = self.selected_entries()
            if ids:
                self.execute(lambda: self.commands.remove(ids))

    def choose_target(self, copy=False):
        steps = self.binding.project.steps
        labels = ['%d · %s' % (i+1, s.name) for i, s in enumerate(steps)]
        choice, accepted = QInputDialog.getItem(self, self.tr('Copy to step') if copy else self.tr('Move to step'),
                                               self.tr('Target step'), labels, editable=False)
        if accepted:
            target = steps[labels.index(choice)]
            ids = self.selected_entries()
            if ids:
                self.execute(lambda: self.commands.transfer(ids, target.id, copy=copy))
            else:
                shapes = [self.unassigned[int(i.data(0, ROLE)[1])] for i in self.tree.selectedItems()
                          if i.data(0, ROLE)[0] == 'geometry']
                self.execute(lambda: self.commands.assign(shapes, target.id))

    def nudge(self, direction):
        if self.binding is None:
            return
        items = self.tree.selectedItems()
        if not items:
            return
        if all(i.data(0, ROLE)[0] == 'step' for i in items):
            ids = [s.id for s in self.binding.project.steps]
            selected = {i.data(0, ROLE)[1] for i in items}
            indices = range(len(ids)) if direction < 0 else range(len(ids)-1, -1, -1)
            for index in indices:
                target = index + direction
                if ids[index] in selected and 0 <= target < len(ids) and ids[target] not in selected:
                    ids[index], ids[target] = ids[target], ids[index]
            self.execute(lambda: self.commands.reorder_steps(ids))
            return
        ids = self.selected_entries()
        steps = [s for s in self.binding.project.steps if any(e.id in ids for e in s.entries)]
        if len(steps) != 1:
            self.notice.setText(self.tr('Select entries from one step to reorder.'))
            return
        step = steps[0]
        rows = [i for i, e in enumerate(step.entries) if e.id in ids]
        position = max(0, min(rows)-1) if direction < 0 else min(len(step.entries), max(rows)+2)
        self.execute(lambda: self.commands.transfer(ids, step.id, position))

    def drop(self, payload, kind, identity, after, copy):
        if payload['kind'] == 'step':
            if kind != 'step' or copy:
                return False
            ids = [s.id for s in self.binding.project.steps]
            if identity in payload['ids']:
                return False
            selected = [i for i in ids if i in payload['ids']]
            if len(selected) != len(payload['ids']):
                return False
            remaining = [i for i in ids if i not in selected]
            pos = remaining.index(identity) + int(after)
            remaining[pos:pos] = selected
            return self.execute(lambda: self.commands.reorder_steps(remaining))
        if kind == 'step':
            target, position = identity, None
        else:
            step = next(s for s in self.binding.project.steps if any(e.id == identity for e in s.entries))
            target = step.id
            position = next(i for i, e in enumerate(step.entries) if e.id == identity) + int(after)
        return self.execute(lambda: self.commands.transfer(payload['ids'], target, position, copy))

    def canvas_operation_ids(self, shapes):
        """Resolve original selection only when each machining context is clear."""
        by_geometry = self.binding.operations_by_geometry()
        identities = []
        for shape in shapes:
            geometry = getattr(shape, 'geometry_id', None)
            options = by_geometry.get(geometry, ())
            active = self.binding.active_operations.get(geometry)
            selected = next((entry.id for step, entry in options if entry.id == active), None)
            if selected is None and len(options) == 1:
                selected = options[0][1].id
            if selected is None:
                return []
            identities.append(selected)
        return identities

    def add_machining_actions(self, menu, identities):
        """Shared actions for the machining tree and the drawing context menu."""
        pairs = self.commands.entries(self.binding.project, identities)
        eligible = bool(pairs) and all(isinstance(entry, MachiningOperation) and
                                      step.kind in ('contour', 'pocket', 'drill') for step, entry in pairs)
        for kind, source in (('contour', None), ('pocket', 'Pocket Mill'), ('drill', 'Drill Bore')):
            text = self.kind_text(kind) if source is None else QtCore.QCoreApplication.translate('MyDropDownMenu', source)
            action = menu.addAction(text)
            action.setData(('kind', kind))
            action.setCheckable(True)
            active = eligible and all(step.kind == kind for step, entry in pairs)
            action.setChecked(active)
            action.setEnabled(eligible)
            # Clicking a checked pocket/drilling action returns to contour mode.
            action.triggered.connect(lambda checked=False, kind=kind, active=active:
                                     self.change_operation_mode(identities, 'contour' if active and kind != 'contour' else kind))
        compensation = menu.addMenu(self.tr('Cutter compensation'))
        compensation.setEnabled(eligible and self.binding.project.configuration['General']['machine_type'] != 'drag_knife')
        values = [self.binding.project.resolve(step, entry)[0]['cut_cor'] for step, entry in pairs
                  if isinstance(entry, MachiningOperation)]
        for number, source in ((40, 'G40 No Compensation'), (41, 'G41 Left Compensation'), (42, 'G42 Right Compensation')):
            text = QtCore.QCoreApplication.translate('MyDropDownMenu', source)
            action = compensation.addAction(text)
            action.setData(('compensation', number))
            action.setCheckable(True)
            action.setChecked(bool(values) and all(value == number for value in values))
            action.triggered.connect(lambda checked=False, number=number:
                                     self.change_operation_mode(identities, compensation=number))
        return compensation

    def change_operation_mode(self, identities, kind=None, compensation=None):
        names = {key: self.kind_text(key) for key in ('contour', 'pocket', 'drill')}
        return self.execute(lambda: self.commands.set_operation_mode(identities, kind, compensation, names))

    def menu(self, position):
        if not self.binding:
            return
        clicked = self.tree.itemAt(position)
        if clicked is not None and not clicked.isSelected():
            self.tree.clearSelection()
            self.tree.setCurrentItem(clicked)
            clicked.setSelected(True)
        menu = QMenu(self)
        identities = [item.data(0, ROLE)[1] for item in self.tree.selectedItems()
                      if item.data(0, ROLE)[0] == 'entry']
        self.add_machining_actions(menu, identities)
        menu.addSeparator()
        for text, callback in ((self.tr('Create machining step…'), self.new_step),
                               (self.tr('Edit step'), self.edit_step),
                               (self.tr('Remove'), self.remove),
                               (self.tr('Reverse'), self.reverse),
                               (self.tr('Move to step'), lambda: self.choose_target(False)),
                               (self.tr('Copy to step'), lambda: self.choose_target(True)),
                               (self.tr('Edit step defaults'), self.edit_defaults),
                               (self.tr('Update step defaults from profile'), self.refresh_defaults),
                               (self.tr('Update tool from profile'), self.refresh_tool),
                               (self.tr('Add custom G-code'), self.add_literal)):
            action = menu.addAction(text, callback)
            if callback == self.reverse:
                action.setEnabled(self.context is not None)
        menu.exec(self.tree.viewport().mapToGlobal(position))

    def edit_defaults(self):
        step = self.current_step() or self.parameter_editor.target()[0]
        if step is not None:
            root = next((self.tree.topLevelItem(i) for i in range(self.tree.topLevelItemCount())
                         if self.tree.topLevelItem(i).data(0, ROLE) == ('step', step.id)), None)
            if root is not None:
                self.tree.clearSelection()
                self.tree.setCurrentItem(root)
                root.setSelected(True)

    def refresh_tool(self):
        step = self.current_step()
        if step is None:
            return
        tool = self.binding.project.tools[step.tool_id]
        profile = g.config.vars.Tool_Parameters[str(tool.tool_nr)]
        if profile is None:
            self.notice.setText(self.tr('The tool is absent from the current profile. Saved values are retained.'))
            return
        self.execute(lambda: self.commands.refresh_tool(step.tool_id, self.profile_tool(tool.tool_nr, profile)))

    def refresh_defaults(self):
        step = self.current_step()
        if step is None:
            return
        defaults = dict(step.defaults)
        for section in ('Depth_Coordinates', 'Feed_Rates', 'Lead_In_Out'):
            values = getattr(g.config.vars, section)
            for key in PARAMETERS & set(vars(values)):
                defaults[key] = values[key]
        defaults['drag_swivel_depth'] = g.config.vars.Drag_Knife_Options['swivel_depth']
        defaults['drag_angle'] = g.config.vars.Drag_Knife_Options['drag_angle']
        self.execute(lambda: self.commands.edit_step(step.id, step.name, step.kind, step.tool_id, defaults))

    def profile_tool(self, number, profile):
        tool = ToolSettings.from_profile(number, profile)
        metric = self.binding.project.units == 'mm'
        if metric != bool(g.config.metric):
            factor = 25.4 if metric else 1/25.4
            tool = replace(tool, **{key: getattr(tool, key) * factor for key in (
                'tool_diameter', 'start_radius', 'lead_radius', 'lead_length', 'overcut_length')
                if getattr(tool, key) is not None})
        return tool

    def parameter_label(self, key):
        return {
            'axis3_start_mill_depth': self.tr('Workpiece surface'),
            'axis3_slice_depth': self.tr('Depth per pass'),
            'axis3_mill_depth': self.tr('Final depth'),
            'axis3_retract': self.tr('Retract height'),
            'axis3_safe_margin': self.tr('Safety margin'),
            'f_g1_plane': self.tr('XY feed'), 'f_g1_depth': self.tr('Z feed'),
            'milling_offset': self.tr('Milling allowance'),
            'lead_in_mode': self.tr('Lead in'), 'lead_out_mode': self.tr('Lead out'),
            'overcut_enabled': self.tr('Overcut'), 'lead_radius': self.tr('Lead radius'),
            'lead_length': self.tr('Lead length'), 'overcut_length': self.tr('Overcut length'),
            'drag_swivel_depth': self.tr('Knife swivel height'), 'drag_angle': self.tr('Knife swivel angle'),
            'cut_cor': self.tr('Cutter compensation'), 'break_pass': self.tr('Holding-tab first pass'),
            'speed': self.tr('Spindle speed'), 'start_radius': self.tr('Start radius')}[key]

    def value_choices(self, key):
        if key == 'overcut_enabled':
            return [(self.tr('Off'), False), (self.tr('On'), True)]
        if key in ('lead_in_mode', 'lead_out_mode'):
            return [(self.tr('Off'), 'off'), (self.tr('Straight'), 'straight'),
                    (self.tr('Radius'), 'radius'), (self.tr('Start move'), 'startmove')]
        if key == 'cut_cor':
            return [('G40', 40), ('G41', 41), ('G42', 42)]
        return []

    def error_text(self, error):
        reasons = {
            'literal actions require a machining step': self.tr('Literal actions require a machining step.'),
            'unresolved source contour': self.tr('The original contour is missing or ambiguous.'),
            'special-layer assignments cannot change kind': self.tr('Holding-tab and ignored assignments must retain their kind.'),
            'drilling requires a point/circle and G40': self.tr('Drilling requires a point or circle and G40.'),
            'a drilling point is not a milling contour': self.tr('A drilling point cannot be used as a milling contour.'),
            'pocketing requires a closed contour and internal milling compensation': self.tr('Pocketing requires a closed contour, milling mode and internal compensation.'),
            'Invalid or foreign geometry selection': self.tr('The geometry selection is invalid or belongs to another project.'),
            'Unknown machining selection': self.tr('The machining selection is no longer valid.'),
            'Select an explicit machining operation before editing shared geometry': self.tr('Select an active operation before editing shared geometry.')}
        lines = []
        for line in str(error).splitlines():
            prefix, separator, reason = line.rpartition(': ')
            lines.append(prefix + separator + reasons.get(reason, reason) if separator else reasons.get(line, line))
        return '\n'.join(lines)

    def add_literal(self):
        step = self.current_step()
        if step is None:
            return
        code, accepted = QInputDialog.getMultiLineText(self, self.tr('Custom G-code'), self.tr('G-code'))
        if accepted:
            from dxf2gcode.domain.project.machining_project import new_id
            from dxf2gcode.application.machining_actions import MachiningChange
            def change(project):
                entry = LiteralAction(new_id(), self.tr('Custom G-code'), code)
                self.commands.step(project, step.id).entries.append(entry)
                return MachiningChange('literal', selection=(entry.id,))
            self.execute(lambda: self.commands.perform('literal', change))

    def undo(self):
        if self.commands and self.commands.undo_stack:
            self.context = None
            self.execute(self.commands.undo)

    def redo(self):
        if self.commands and self.commands.redo_stack:
            self.context = None
            self.execute(self.commands.redo)

    def draw_route(self):
        scene = self.window.canvas_scene
        try:
            layers = self.binding.materialize()
            from dxf2gcode.adapters.toolpath.preparation import prepare_shape
            from dxf2gcode.adapters.toolpath.preview import preview_result
            from dxf2gcode.application.toolpath.projections import plan_route_endpoints
            for layer in layers.non_break_layer_iter():
                for shape in layer.shapes:
                    if isinstance(shape, LiteralAction) or not hasattr(shape, 'geos') or shape.disabled:
                        continue
                    prepare_shape(shape, build_preview=False)
                    result = preview_result(shape, self.window.MyPostProcessor, layers)
                    if result.has_errors or result.plan is None:
                        raise ValueError('; '.join(d.message for d in result.diagnostics))
                    shape.route_endpoints = plan_route_endpoints(result.plan)
        except ValueError as error:
            self.notice.setText(str(error))
            scene.delete_opt_paths()
            return
        shapes = [s for layer in layers for s in layer.shapes]
        previous = scene.shapes
        scene.delete_opt_paths()
        scene.shapes = shapes
        config = ProjectConfiguration(self.binding.project)
        try:
            scene.addexproutest(config)
            for layer in layers.non_break_layer_iter():
                if layer.exp_order:
                    scene.addexproute(layer.exp_order, layer.nr)
            if scene.routearrows:
                scene.addexprouteen(config)
                self.window.ui.actionDeleteG0Paths.setEnabled(True)
        finally:
            scene.shapes = previous
        scene.update()
