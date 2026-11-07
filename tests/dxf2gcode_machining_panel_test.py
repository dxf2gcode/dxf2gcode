"""Real Qt selection/drop/history/export integration for the machining tab."""
import json
import ast
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


class TestMachiningPanel(unittest.TestCase):
    def test_all_panel_text_has_finished_translations(self):
        for module, name in (('machining_panel', 'MachiningPanel'), ('machining_parameters', 'MachiningParameters'), ('geometry_panel', 'GeometryPanel')):
            source = ROOT / ('source/dxf2gcode/presentation/qt/' + module + '.py')
            messages = {node.args[0].value for node in ast.walk(ast.parse(source.read_text(encoding='utf-8')))
                        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                        and isinstance(node.func.value, ast.Name) and node.func.value.id == 'self'
                        and node.func.attr == 'tr' and node.args and isinstance(node.args[0], ast.Constant)}
            for language in ('de', 'fr', 'ru'):
                context = next(c for c in ET.parse(ROOT / ('source/i18n/dxf2gcode_' + language + '.ts')).findall('context')
                               if c.findtext('name') == name)
                translated = {m.findtext('source'): m.find('translation') for m in context.findall('message')}
                self.assertTrue(messages <= set(translated))
                for text, value in translated.items():
                    self.assertTrue(value.text)
                    self.assertNotEqual(value.get('type'), 'unfinished')
                    for placeholder in ('{0}', '{1}'):
                        self.assertEqual(text.count(placeholder), value.text.count(placeholder))

    def test_real_events_selection_history_and_program_order(self):
        with tempfile.TemporaryDirectory() as folder:
            env = dict(os.environ, D2G_MACHINING_TEMP=folder, D2G_TEST_MACHINING_PANEL='1',
                       QT_QPA_PLATFORM='offscreen')
            result = subprocess.run([sys.executable, str(ROOT / 'tests/dxf2gcode_machining_gui_test.py'), '--worker'],
                                    env=env, cwd=folder, capture_output=True, timeout=45)
            self.assertEqual(result.returncode, 0, result.stdout.decode(errors='replace') +
                             result.stderr.decode(errors='replace'))


def exercise_panel(window, app, folder):
    from copy import deepcopy
    from dataclasses import replace
    import dxf2gcode.bootstrap.runtime_state as g
    from dxf2gcode.presentation.qt.qt_compat import QtCore, PYQT_VERSION
    from dxf2gcode.presentation.qt.qt_compat.QtGui import QDropEvent
    from dxf2gcode.presentation.qt.machining_panel import ROLE, MIME
    Qt = QtCore.Qt
    panel = window.machining_panel
    assert not hasattr(panel, 'parameters')
    assert panel.isAncestorOf(window.ui.millSettingsFrame)
    assert not window.ui.tab_2.isAncestorOf(window.ui.millSettingsFrame)
    assert window.ui.mytabWidget.count() == 2
    assert panel.tree.columnCount() == 3
    assert panel.binding is window.d2g.machining_drawing
    before_layout = panel.binding.project.to_dict()
    for toggle, page in window.geometry_panel.sections:
        assert not page.isHidden()
        toggle.click()
        assert page.isHidden()
        toggle.click()
        assert not page.isHidden()
    for collapse, expand in ((window.ui.layersCollapsePushButton, window.ui.layersExpandPushButton),
                             (window.ui.blocksCollapsePushButton, window.ui.blocksExpandPushButton)):
        assert window.geometry_panel.isAncestorOf(collapse)
        assert window.geometry_panel.isAncestorOf(expand)
    panel.buttons['collapse'].trigger()
    assert not panel.tree.topLevelItem(0).isExpanded()
    assert not panel.buttons['collapse'].isEnabled() and panel.buttons['expand'].isEnabled()
    panel.buttons['expand'].trigger()
    assert panel.tree.topLevelItem(0).isExpanded()
    assert panel.binding.project.to_dict() == before_layout
    # The user's entire-layer workflow traverses actual selection and dialog
    # signals rather than invoking only the underlying command directly.
    source_layer = window.layerContents[0]
    members = tuple(source_layer.shapes)
    before_assignment = panel.binding.project.to_dict()
    view = window.ui.layersShapesTreeView
    view.setCurrentIndex(view.model().index(0, 0))
    assert all(shape.isSelected() for shape in members)
    def accept_step():
        from dxf2gcode.presentation.qt.qt_compat.QtWidgets import QLineEdit
        dialog = app.activeModalWidget()
        assert dialog is not None
        dialog.findChildren(QLineEdit)[0].setText('From layer')
        dialog.accept()
    QtCore.QTimer.singleShot(0, accept_step)
    panel.from_selection()
    assert panel.binding.project.steps[-1].name == 'From layer'
    assert len(panel.binding.project.steps[-1].entries) == len(members)
    assert tuple(source_layer.shapes) == members
    panel.undo()
    assert panel.binding.project.to_dict() == before_assignment
    item = panel.tree.topLevelItem(0).child(0)
    saved = panel.binding.project.to_dict()
    item.setCheckState(1, Qt.CheckState.Unchecked)
    app.processEvents()
    assert not panel.binding.project.steps[0].entries[0].enabled
    panel.undo()
    assert panel.binding.project.to_dict() == saved
    item = panel.tree.topLevelItem(0).child(0)
    current = panel.binding.project.steps[0].entries[0].optimize
    item.setCheckState(2, Qt.CheckState.Unchecked if current else Qt.CheckState.Checked)
    app.processEvents()
    assert panel.binding.project.steps[0].entries[0].optimize != current
    panel.undo()
    assert panel.binding.project.to_dict() == saved
    assert panel.buttons['undo'].isEnabled() == bool(panel.commands.undo_stack)
    assert panel.buttons['redo'].isEnabled() == bool(panel.commands.redo_stack)
    original = panel.binding.project.steps[0]
    entry = original.entries[0]
    shape = panel.binding.sources[entry.geometry_id]
    original_geometry = deepcopy([(geo.save_v1()) for geo in shape.geos])
    tool = panel.binding.project.tools[original.tool_id]
    assert panel.execute(lambda: panel.commands.create_step('Finish', 'contour', replace(tool, tool_nr=2)))
    target = panel.binding.project.steps[-1]
    assert panel.execute(lambda: panel.commands.transfer([entry.id], target.id, copy=True))
    copied = panel.binding.project.steps[-1].entries[0]
    copied_id = copied.id
    assert copied.geometry_id == entry.geometry_id
    exercise_context_menu(window, app, shape, target.id)
    exercise_machining_modes(window, app, shape, copied_id, entry.id)
    window.canvas_scene.setShowDisabledPaths(False)
    assert panel.execute(lambda: panel.commands.update_entries([entry.id, copied_id], enabled=False))
    assert not window.canvas_scene.graphics_items[id(shape)].isVisible()
    assert panel.execute(lambda: panel.commands.update_entries([copied_id], enabled=True))
    assert window.canvas_scene.graphics_items[id(shape)].isVisible()
    assert panel.execute(lambda: panel.commands.update_entries([entry.id], enabled=True))
    panel.binding.active_operations.clear()
    for candidate in window.shapes:
        window.TreeHandler.setShapeSelected(candidate, candidate is shape)
    panel.geometry_selected()
    assert len([i for i in panel.tree.selectedItems() if i.data(0, ROLE)[0] == 'entry']) == 2
    assert panel.context is None
    assert not panel.binding.active_operations.get(entry.geometry_id)
    for view in (window.ui.layersShapesTreeView, window.ui.entitiesTreeView):
        assert not view.dragEnabled()
        assert view.model().item(0, 0).data(Qt.ItemDataRole.CheckStateRole) is None
    window.ui.mytabWidget.setCurrentWidget(panel)
    window.showNormal()
    window.resize(1200, 900)
    app.processEvents()
    panel.tree.clearSelection()
    item = panel.tree.topLevelItem(panel.tree.topLevelItemCount()-1).child(0)
    panel.tree.setCurrentItem(item)
    item.setSelected(True)
    app.processEvents()
    assert panel.context == copied_id, (panel.context, copied_id)
    assert item.font(0).bold()
    panel.reverse()
    assert [geo.save_v1() for geo in shape.geos] == original_geometry
    assert panel.binding.project.steps[0].entries[0].clockwise != panel.binding.project.steps[-1].entries[0].clockwise
    active = shape._machining_view
    point, angle = active.get_start_end_points_physical(True, True, PPocket=True)
    arrow = window.canvas_scene.graphics_items[id(shape)].starrow
    assert abs(arrow.angle - angle) < 1e-10
    assert shape.stmove.shape.toolpath_plan is shape.toolpath_plan
    editor = panel.parameter_editor
    assert window.ui.millSettingsFrame.isEnabled()
    # Both groups shrink their three content columns; status stays visible/fixed.
    before_resize = panel.binding.project.to_dict()
    sizes = window.ui.splitter.sizes()
    widths = []
    label_widths = []
    unit_widths = []
    for sidebar in (620, 340):
        window.ui.splitter.setSizes([sidebar, max(1, sum(sizes)-sidebar)])
        app.processEvents()
        field_tool = editor.fields['speed']
        field_shape = editor.fields['axis3_mill_depth']
        assert abs(field_tool.width()-field_shape.width()) <= 2
        assert abs(field_tool.mapTo(editor.frame, QtCore.QPoint()).x() -
                   field_shape.mapTo(editor.frame, QtCore.QPoint()).x()) <= 2
        widths.append(field_tool.width())
        label_widths.append(window.ui.label_12.width())
        unit_widths.append(window.ui.toolSpeedUnitLabel.width())
        assert window.ui.toolSpeedUnitLabel.alignment() == window.ui.unitLabel_7.alignment()
        for key in ('speed', 'axis3_mill_depth'):
            status = editor.origins[key]
            assert status.width() == 32
            assert status.mapTo(editor.frame, QtCore.QPoint(status.width(), 0)).x() <= panel.parameter_scroll.viewport().width()
        assert editor.frame.width() <= panel.parameter_scroll.viewport().width()
    assert widths[0] > widths[1], widths
    assert label_widths[0] > label_widths[1], label_widths
    assert unit_widths[0] > unit_widths[1], unit_widths
    window.ui.splitter.setSizes(sizes)
    app.processEvents()
    assert panel.binding.project.to_dict() == before_resize
    field = window.ui.zFinalMillDepthLineEdit
    from importlib import import_module
    QTest = import_module('PyQt%d.QtTest' % PYQT_VERSION).QTest
    field.setFocus()
    field.selectAll()
    QTest.keyClicks(field, '-7')
    QTest.keyClick(field, Qt.Key.Key_Return)
    assert panel.binding.project.steps[-1].entries[0].overrides['axis3_mill_depth'] == -7
    assert editor.origins['axis3_mill_depth'].property('provenance') == 'own'
    assert '-7' in editor.origins['axis3_mill_depth'].toolTip()
    assert len(editor.origins['axis3_mill_depth'].icon().availableSizes()) > 1
    status = editor.origins['axis3_mill_depth']
    assert len(status.menu().actions()) == 2
    assert status.menu().actions()[1] is editor.resets['axis3_mill_depth']
    editor.resets['axis3_mill_depth'].trigger()
    assert 'axis3_mill_depth' not in panel.binding.project.steps[-1].entries[0].overrides
    assert editor.origins['axis3_mill_depth'].property('provenance') == 'inherited'
    assert 'Finish' in editor.origins['axis3_mill_depth'].toolTip()
    # Rounded display must not overwrite the exact stored project value.
    exact = -0.12345678912345678
    panel.execute(lambda: panel.commands.update_entries([copied_id], {'axis3_mill_depth': exact}))
    assert float(field.text()) != exact
    # The start-point dialog also retains exact coordinates when confirmed.
    exact_start = panel.binding.project.steps[-1].entries[0].start
    QtCore.QTimer.singleShot(0, lambda: app.activeModalWidget().cbOK())
    panel.start_point()
    assert panel.binding.project.steps[-1].entries[0].start == exact_start
    count = len(panel.commands.undo_stack)
    unchanged = panel.binding.project.to_dict()
    from dxf2gcode.presentation.qt.configwindow import ConfigWindow
    old_places = g.config.var_dict['Display']['decimals_mm']
    g.config.var_dict['Display']['decimals_mm'] = 2
    window.updateConfiguration(ConfigWindow.Applied)
    assert panel.binding.project.to_dict() == unchanged
    assert field.text() == '-0.12'
    g.config.var_dict['Display']['decimals_mm'] = old_places
    window.updateConfiguration(ConfigWindow.Applied)
    assert panel.binding.project.to_dict() == unchanged
    field.editingFinished.emit()
    assert panel.binding.project.to_dict() == unchanged
    panel.undo()
    count = len(panel.commands.undo_stack)
    field.editingFinished.emit()
    editor.refresh()
    assert len(panel.commands.undo_stack) == count
    panel.undo()
    assert panel.binding.project.steps[-1].entries[0].overrides['axis3_mill_depth'] == -7
    panel.redo()
    assert 'axis3_mill_depth' not in panel.binding.project.steps[-1].entries[0].overrides
    # The same familiar controls edit step defaults when the step is selected.
    before_step_edit = panel.binding.project.to_dict()
    root = next(panel.tree.topLevelItem(i) for i in range(panel.tree.topLevelItemCount())
                if panel.tree.topLevelItem(i).data(0, ROLE) == ('step', target.id))
    panel.tree.clearSelection()
    panel.tree.setCurrentItem(root)
    root.setSelected(True)
    assert editor.target()[1] is None and window.ui.millSettingsFrame.isEnabled()
    feed = window.ui.g1FeedXYLineEdit
    feed.setText('777')
    feed.setModified(True)
    feed.editingFinished.emit()
    assert panel.binding.project.steps[-1].defaults['f_g1_plane'] == 777
    assert panel.binding.project.steps[-1].entries[0].overrides['f_g1_plane'] != 777
    panel.undo()
    assert panel.binding.project.to_dict() == before_step_edit
    assert editor.target()[0].id == target.id and editor.target()[1] is None
    # Tool selection belongs to the step and must not change source-layer tools.
    index = editor.tool_combo.findData(original.tool_id)
    editor.tool_combo.setCurrentIndex(index)
    editor.tool_combo.activated.emit(index)
    assert panel.binding.project.steps[-1].tool_id == original.tool_id
    assert source_layer.tool_nr == 1
    panel.undo()
    assert panel.binding.project.steps[-1].tool_id == target.tool_id
    before_invalid = panel.binding.project.to_dict()
    count = len(panel.commands.undo_stack)
    feed.setText('nan')
    feed.setModified(True)
    feed.editingFinished.emit()
    assert panel.binding.project.to_dict() == before_invalid
    assert len(panel.commands.undo_stack) == count
    # Reorder through an actual Qt5/Qt6 drop event; base Qt never mutates the model.
    root = panel.tree.topLevelItem(0)
    point = panel.tree.visualItemRect(root).topLeft() + QtCore.QPoint(12, 2)
    payload = dict(token=panel.token, generation=panel.generation, kind='step', ids=[target.id])
    mime = QtCore.QMimeData()
    mime.setData(MIME, json.dumps(payload).encode())
    event = QDropEvent(QtCore.QPointF(point), Qt.DropAction.MoveAction, mime,
                       Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
    panel.tree.dropEvent(event)
    assert event.isAccepted()
    assert panel.binding.project.steps[0].id == target.id
    before = panel.binding.project.to_dict()
    event = QDropEvent(QtCore.QPointF(point), Qt.DropAction.MoveAction, mime,
                       Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
    panel.tree.dropEvent(event)  # stale generation
    assert not event.isAccepted()
    assert panel.binding.project.to_dict() == before
    panel.undo()
    assert panel.binding.project.steps[0].id == original.id
    panel.redo()
    assert panel.binding.project.steps[0].id == target.id
    # Explicit routing has detached, per-operation endpoints and no geometry copies in the scene.
    count = len(window.canvas_scene.shapes)
    panel.draw_route()
    assert len(window.canvas_scene.shapes) == count
    assert window.canvas_scene.routearrows
    # The visible order is the emitted order, and persists through GUI/CLI roundtrip.
    path = folder / 'panel.d2g'
    path.write_text(window.d2g.export_current(), encoding='utf-8')
    output = folder / 'panel.ngc'
    assert window.exportShapes(saveas=str(output))
    code = output.read_text()
    assert code.index('T2') < code.index('T1'), code
    cli_output = folder / 'panel-cli.ngc'
    cli = subprocess.run([sys.executable, str(ROOT / 'source/dxf2gcode.py'), '--cfg', 'r3', '--quiet',
                          '--export', str(cli_output), str(path)],
                         env=dict(os.environ, HOME=str(folder), USERPROFILE=str(folder)),
                         cwd=folder, capture_output=True, timeout=30)
    assert cli.returncode == 0, cli.stderr.decode(errors='replace')
    def program(path):
        return [line for line in path.read_text().splitlines() if line and not line.startswith('(')]
    assert program(output) == program(cli_output)
    if os.environ.get('D2G_PANEL_SCREENSHOT'):
        from dxf2gcode.presentation.qt.qt_compat.QtGui import QFont
        panel.setFont(QFont('Segoe UI', 9))
        panel.tree.setCurrentItem(panel.tree.topLevelItem(0).child(0))
        panel.tree.topLevelItem(0).child(0).setSelected(True)
        app.processEvents()
        QTest.qWait(50)
        panel.grab().save(os.environ['D2G_PANEL_SCREENSHOT'])
        editor.frame.grab().save(os.environ['D2G_PANEL_SCREENSHOT'] + '.form.png')
    for language in ('de', 'fr', 'ru'):
        translator = QtCore.QTranslator()
        qm = Path(os.environ.get('D2G_TRANSLATION_DIR', str(ROOT / 'source/i18n'))) / ('dxf2gcode_' + language + '.qm')
        assert translator.load(str(qm))
        app.installTranslator(translator)
        for owner, name in ((panel, 'MachiningPanel'), (panel.parameter_editor, 'MachiningParameters'), (window.geometry_panel, 'GeometryPanel')):
            context = next(c for c in ET.parse(ROOT / ('source/i18n/dxf2gcode_' + language + '.ts')).findall('context')
                           if c.findtext('name') == name)
            for message in context.findall('message'):
                assert owner.tr(message.findtext('source')) == message.findtext('translation')
        app.removeTranslator(translator)


def exercise_machining_modes(window, app, shape, identity, other_identity):
    from unittest.mock import patch
    from dxf2gcode.presentation.qt.qt_compat import QtCore
    from dxf2gcode.presentation.qt.qt_compat.QtGui import QContextMenuEvent
    from dxf2gcode.presentation.qt.qt_compat.QtWidgets import QMenu
    from dxf2gcode.presentation.qt.canvas import MyDropDownMenu
    panel = window.machining_panel
    panel.tree.clearSelection()
    item = panel.entry_items[identity]
    panel.tree.setCurrentItem(item)
    item.setSelected(True)
    before = panel.binding.project.to_dict()
    other = dict(panel.commands.entries(panel.binding.project, [other_identity])[0][1].overrides)
    menus = []
    def capture(menu, position):
        menus.append(menu)
        return None
    window.ui.mytabWidget.setCurrentWidget(panel)
    app.processEvents()
    point = panel.tree.visualItemRect(item).center()
    with patch.object(QMenu, 'exec', new=capture):
        app.sendEvent(panel.tree.viewport(), QContextMenuEvent(QContextMenuEvent.Reason.Mouse,
                      point, panel.tree.viewport().mapToGlobal(point)))
    assert menus
    menu = menus[-1]
    assert not any(action.text() == panel.tr('Start point') for action in menu.actions())
    pocket = next(a for a in menu.actions() if a.data() == ('kind', 'pocket'))
    comp = next(a.menu() for a in menu.actions() if a.menu() is not None)
    next(a for a in comp.actions() if a.data() == ('compensation', 41)).trigger()
    assert panel.commands.entries(panel.binding.project, [identity])[0][1].overrides['cut_cor'] == 41
    assert panel.commands.entries(panel.binding.project, [other_identity])[0][1].overrides == other
    panel.undo()
    assert panel.binding.project.to_dict() == before
    with patch.object(QMenu, 'exec', new=capture):
        canvas = MyDropDownMenu(window.canvas_scene, QtCore.QPoint(), shape.get_start_end_points(True))
    comp = next(a.menu() for a in canvas.actions() if a.menu() is not None)
    assert comp.isEnabled()
    next(a for a in comp.actions() if a.data() == ('compensation', 42)).trigger()
    assert panel.commands.entries(panel.binding.project, [identity])[0][1].overrides['cut_cor'] == 42
    panel.undo()
    assert panel.binding.project.to_dict() == before
    assert panel.execute(lambda: panel.commands.update_settings({'Cutter_Compensation': {'done_by_machine': False}}))
    # QAction uses the captured selected operation, not another shared contour reference.
    pocket.trigger()
    source, operation = panel.commands.entries(panel.binding.project, [identity])[0]
    assert source.kind == 'pocket'
    assert shape._machining_view.Pocket
    assert shape._machining_view.operation_id == identity
    assert panel.commands.entries(panel.binding.project, [other_identity])[0][0].kind == 'contour'
    panel.undo()
    panel.undo()
    assert panel.binding.project.to_dict() == before
    panel.binding.active_operations.pop(shape.geometry_id, None)
    assert panel.canvas_operation_ids([shape]) == []
    menu = QMenu(panel)
    assert not panel.add_machining_actions(menu, []).isEnabled()


def exercise_context_menu(window, app, shape, target_id):
    from unittest.mock import patch
    from dxf2gcode.presentation.qt.qt_compat import QtCore
    from dxf2gcode.presentation.qt.qt_compat.QtGui import QContextMenuEvent
    from dxf2gcode.presentation.qt.qt_compat.QtWidgets import QApplication, QMenu, QComboBox, QLineEdit
    panel = window.machining_panel
    view = window.ui.layersShapesTreeView
    index = window.TreeHandler.findLayerItemIndexFromShape(shape)
    view.scrollTo(index)
    app.processEvents()
    point = view.visualRect(index).center()
    screen_point = view.viewport().mapToGlobal(point)
    before = panel.binding.project.to_dict()
    count = len(panel.commands.undo_stack)
    with patch.object(QMenu, 'exec', return_value=None) as popup, patch.object(panel, 'step_dialog') as dialog:
        event = QContextMenuEvent(QContextMenuEvent.Reason.Mouse, point, screen_point)
        QApplication.sendEvent(view.viewport(), event)
        assert popup.call_count == 1
        assert popup.call_args.args[0] == screen_point
        dialog.assert_not_called()
    assert panel.binding.project.to_dict() == before
    assert len(panel.commands.undo_stack) == count
    entities = window.ui.entitiesTreeView
    index = entities.model().index(0, 0)
    point_entities = entities.visualRect(index).center()
    event_entities = QContextMenuEvent(QContextMenuEvent.Reason.Mouse, point_entities,
                                       entities.viewport().mapToGlobal(point_entities))
    with patch.object(QMenu, 'exec', return_value=None) as popup:
        app.sendEvent(entities.viewport(), event_entities)
        assert popup.call_count == 1
    menu = panel.build_geometry_menu([shape], screen_point)
    related = menu.actions()[1].menu()
    action = next(action for action in related.actions() if action.data() == target_id)
    action.trigger()
    assert window.ui.mytabWidget.currentWidget() is panel
    assert panel.context == panel.binding.project.steps[-1].entries[0].id
    assert panel.binding.project.to_dict() == before
    for mode in ('move', 'copy', 'empty'):
        before = panel.binding.project.to_dict()
        old_ids = {e.id for s in panel.binding.project.steps for e in s.entries}
        def accept():
            dialog = app.activeModalWidget()
            combo = dialog.findChild(QComboBox, 'assignmentMode')
            assert combo.currentData() == 'move'
            combo.setCurrentIndex(combo.findData(mode))
            dialog.findChild(QLineEdit, 'stepName').setText('Context ' + mode)
            assert dialog.screen().availableGeometry().contains(dialog.pos())
            dialog.accept()
        QtCore.QTimer.singleShot(0, accept)
        panel.from_selection([shape], screen_point)
        created = panel.binding.project.steps[-1]
        assert created.name == 'Context ' + mode
        assert len(created.entries) == (0 if mode == 'empty' else 1)
        if created.entries:
            assert (created.entries[0].id in old_ids) == (mode == 'move')
        panel.undo()
        assert panel.binding.project.to_dict() == before
    before = panel.binding.project.to_dict()
    count = len(panel.commands.undo_stack)
    QtCore.QTimer.singleShot(0, lambda: app.activeModalWidget().reject())
    panel.from_selection([shape], screen_point)
    assert panel.binding.project.to_dict() == before
    assert len(panel.commands.undo_stack) == count
    def empty():
        dialog = app.activeModalWidget()
        assert not dialog.findChild(QComboBox, 'assignmentMode').isVisible()
        dialog.accept()
    QtCore.QTimer.singleShot(0, empty)
    panel.from_selection([])
    assert not panel.binding.project.steps[-1].entries
    panel.undo()
    assert panel.binding.project.to_dict() == before


if __name__ == '__main__':
    unittest.main()
