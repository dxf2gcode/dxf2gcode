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
        for module, name in (('machining_panel', 'MachiningPanel'), ('machining_parameters', 'MachiningParameters'), ('geometry_panel', 'GeometryPanel'), ('machining_preview', 'MachiningPreview'), ('tab_modifiers', 'TabModifiers')):
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
                    for placeholder in ('{0}', '{1}', '{2}', '{3}'):
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
    from dxf2gcode.presentation.qt.qt_compat.QtWidgets import QLineEdit
    from dxf2gcode.presentation.qt.machining_panel import ROLE, MIME
    Qt = QtCore.Qt
    panel = window.machining_panel
    assert not hasattr(panel, 'parameters')
    assert panel.isAncestorOf(window.ui.millSettingsFrame)
    assert not window.ui.tab_2.isAncestorOf(window.ui.millSettingsFrame)
    assert window.ui.mytabWidget.count() == 2
    assert panel.tree.columnCount() == 3
    assert panel.binding is window.d2g.machining_drawing
    exercise_tool_choices(window, app)
    exercise_multi_tool_selection(window, app)
    exercise_multi_parameter_editing(window, app)
    exercise_automatic_target_reuse(window, app)
    before_layout = panel.binding.project.to_dict()
    for toggle, page in window.geometry_panel.sections:
        assert not page.isHidden()
        toggle.click()
        assert page.isHidden()
        toggle.click()
        assert not page.isHidden()
    for toggle, page in window.geometry_panel.sections:
        toggle.click()
    app.processEvents()
    assert window.geometry_panel.splitter.y() <= 2
    assert window.geometry_panel.sections[0][0].mapTo(window.geometry_panel, QtCore.QPoint()).y() <= 10
    for toggle, page in window.geometry_panel.sections:
        toggle.click()
    app.processEvents()
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
    import dxf2gcode.bootstrap.runtime_state as g
    tool_two = panel.profile_tool(2, g.config.vars.Tool_Parameters['2'])
    assert panel.execute(lambda: panel.commands.create_step('Finish', 'contour', tool_two))
    target = panel.binding.project.steps[-1]
    assert panel.execute(lambda: panel.commands.transfer([entry.id], target.id, copy=True))
    copied = panel.binding.project.steps[-1].entries[0]
    copied_id = copied.id
    assert copied.geometry_id == entry.geometry_id
    exercise_operation_canvas(window, app, entry.id, copied_id)
    # Arrow reordering preserves exactly the selected step and keyboard focus.
    before_nudge = panel.binding.project.to_dict()
    panel.tree.clearSelection()
    root = next(panel.tree.topLevelItem(i) for i in range(panel.tree.topLevelItemCount())
                if panel.tree.topLevelItem(i).data(0, ROLE) == ('step', target.id))
    panel.tree.setCurrentItem(root)
    root.setSelected(True)
    def check_selected_step():
        assert [i.data(0, ROLE) for i in panel.tree.selectedItems()] == [('step', target.id)]
        assert panel.tree.currentItem().data(0, ROLE) == ('step', target.id)
        assert panel.commands.selection == (target.id,)
    panel.buttons['up'].trigger()
    assert panel.binding.project.steps[0].id == target.id
    check_selected_step()
    panel.undo()
    assert panel.binding.project.to_dict() == before_nudge
    check_selected_step()
    panel.redo()
    assert panel.binding.project.steps[0].id == target.id
    check_selected_step()
    panel.buttons['down'].trigger()
    assert panel.binding.project.to_dict() == before_nudge
    check_selected_step()
    panel.undo()
    panel.undo()
    assert panel.binding.project.to_dict() == before_nudge
    exercise_context_menu(window, app, shape, target.id)
    exercise_assignment_dialog(window, app, shape)
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
    exercise_section_content_height(window, app)
    assert not window.ui.toolGroupBox.isEnabled()
    assert not window.ui.shapeGroupBox.isEnabled()
    assert not panel.parameter_editor.tool_combo.isEnabled()
    assert all(not field.isEnabled() for field in panel.parameter_editor.fields.values())
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
    # The optional holding-tab row must not leave its provenance button behind.
    from unittest.mock import patch
    editor = panel.parameter_editor
    before_break_visibility = panel.binding.project.to_dict()
    for visible in (True, False):
        with patch('dxf2gcode.presentation.qt.treehandling.break_geometries_present', return_value=visible):
            window.TreeHandler.updateBreaksPassWidget()
            editor.refresh()
            app.processEvents()
            for widget in (window.ui.breaksPassLabel, editor.fields['break_pass'], editor.origins['break_pass']):
                assert widget.isVisibleTo(window.ui.shapeGroupBox) == visible
    grid = window.ui.gridLayout
    depth = editor.fields['axis3_mill_depth']
    feed = editor.fields['f_g1_plane']
    assert feed.mapTo(window.ui.shapeGroupBox, QtCore.QPoint()).y() >= depth.mapTo(window.ui.shapeGroupBox, QtCore.QPoint()).y()
    assert panel.binding.project.to_dict() == before_break_visibility
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
    for key in ('lead_radius', 'lead_length', 'overcut_length', 'start_radius'):
        assert window.ui.shapeGroupBox.isAncestorOf(editor.fields[key]), key
        assert not window.ui.toolGroupBox.isAncestorOf(editor.fields[key]), key
    machine = panel.binding.project.configuration['General']['machine_type']
    for mode in ('milling', 'lathe', 'drag_knife'):
        panel.binding.project.configuration['General']['machine_type'] = mode
        editor.refresh()
        app.processEvents()
        for key in ('drag_angle', 'drag_swivel_depth'):
            row = next(row for row in editor.value_rows if any(field is editor.fields[key] for _, field, _ in row.cells))
            expected = mode == 'drag_knife'
            assert editor.fields[key].isVisibleTo(editor.frame) == expected
            assert editor.labels[key].isVisibleTo(editor.frame) == expected
            assert editor.origins[key].isVisibleTo(editor.frame) == expected
        for key in ('lead_radius', 'lead_length', 'overcut_length', 'lead_in_mode', 'lead_out_mode'):
            assert editor.fields[key].isVisibleTo(editor.frame) == (mode == 'milling'), (mode, key)
    panel.binding.project.configuration['General']['machine_type'] = machine
    editor.refresh()
    # Two values per row at both ordinary and generous widths. Layout-only
    # changes retain exact project values and history.
    before_resize = panel.binding.project.to_dict()
    sizes = window.ui.splitter.sizes()
    previous_window_size = window.size()
    window.resize(2300, 1200)
    app.processEvents()
    for sidebar in (1700, 530, 340):
        window.ui.splitter.setSizes([sidebar, max(1, sum(window.ui.splitter.sizes())-sidebar)])
        app.processEvents()
        app.processEvents()
        assert list(editor.groups) == ['z', 'feeds', 'leads', 'offset']
        assert not hasattr(editor, 'splitter')
        for row in editor.value_rows:
            visible = [(label, field, status) for label, field, status in row.cells if field.isVisibleTo(editor.frame)]
            if len(visible) == 2:
                first, second = (field.mapTo(row, QtCore.QPoint()) for _, field, _ in visible)
                assert abs(first.y()-second.y()) <= 2
                assert first.x() < second.x()
            for label, field, status in visible:
                if status is not None:
                    gap = status.mapTo(row, QtCore.QPoint()).x()-field.mapTo(row, QtCore.QPoint(field.width(), 0)).x()
                    assert 0 <= gap <= 3, (sidebar, label.text(), gap, field.geometry(), status.geometry(), row.width())
                    assert status.mapTo(row, QtCore.QPoint(status.width(), 0)).x() <= row.width()
        for key, field in editor.fields.items():
            assert field.toolTip() == editor.field_help(key)
            assert field.toolTip() != editor.origins[key].toolTip()
            if isinstance(field, QLineEdit):
                assert field.maximumWidth() <= field.fontMetrics().horizontalAdvance('00000000')+12
        for key in ('axis3_start_mill_depth', 'f_g1_plane', 'lead_radius'):
            assert '[' in editor.labels[key].text() and ']' in editor.labels[key].text()
        assert editor.scroll.horizontalScrollBar().maximum() == 0
    window.resize(previous_window_size)
    window.ui.splitter.setSizes(sizes)
    app.processEvents()
    assert panel.binding.project.to_dict() == before_resize
    # Real handle drags and collapse headers affect presentation only.
    from importlib import import_module
    QTest = import_module('PyQt%d.QtTest' % PYQT_VERSION).QTest
    before_layout = panel.binding.project.to_dict()
    history_count = len(panel.commands.undo_stack)
    assert window.ui.messageSplitter.widget(0) is window.ui.splitter
    assert window.ui.messageSplitter.widget(1) is window.ui.messageBox
    messages_before_resize = window.ui.messageBox.toPlainText()
    for splitter in (panel.splitter, window.ui.messageSplitter):
        sizes = splitter.sizes()
        handle = splitter.handle(1)
        point = handle.rect().center()
        QTest.mousePress(handle, Qt.MouseButton.LeftButton, pos=point)
        from dxf2gcode.presentation.qt.qt_compat.QtGui import QMouseEvent
        minimum, maximum = splitter.getRange(1)
        position = handle.pos().y()
        # Drag into available space, including when the message pane has
        # already reached its minimum height in this platform's layout.
        distance = (min(30, maximum-position) if maximum-position >= position-minimum
                    else -min(30, position-minimum))
        assert distance != 0, (splitter.objectName(), minimum, maximum, position)
        moved = point + QtCore.QPoint(0, distance)
        event = QMouseEvent(QtCore.QEvent.Type.MouseMove, QtCore.QPointF(moved),
                            QtCore.QPointF(handle.mapToGlobal(moved)), Qt.MouseButton.NoButton,
                            Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
        app.sendEvent(handle, event)
        QTest.mouseRelease(handle, Qt.MouseButton.LeftButton, pos=point + QtCore.QPoint(0, distance))
        app.processEvents()
        assert splitter.sizes() != sizes, (splitter.objectName(), sizes, splitter.sizes())
        splitter.setSizes(sizes)
    assert window.ui.messageBox.toPlainText() == messages_before_resize
    # Overflow depends on font metrics and available window height. Exercise
    # scrolling in an explicitly constrained pane instead of assuming that
    # the preceding splitter drags happened to leave a small enough viewport.
    parameter_sizes = panel.splitter.sizes()
    panel.splitter.setSizes([sum(parameter_sizes)-100, 100])
    app.processEvents()
    assert editor.scroll.verticalScrollBar().maximum() > 0
    panel.splitter.setSizes(parameter_sizes)
    app.processEvents()
    assert panel.binding.project.to_dict() == before_layout
    assert len(panel.commands.undo_stack) == history_count
    exercise_section_content_height(window, app)
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
    import logging
    from dxf2gcode.presentation.qt.machining_panel import logger
    handler = logging.StreamHandler(window.ui.messageBox)
    old_level = logger.level
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    try:
        before_tool_change = panel.binding.project.to_dict()
        step = panel.commands.entries(panel.binding.project, [copied_id])[0][0]
        tool = panel.binding.project.tools[step.tool_id]
        panel.execute(lambda: panel.commands.refresh_tool(step.tool_id, replace(tool, speed=12345)))
        assert '12345' in window.ui.messageBox.toPlainText()
        panel.undo()
        assert panel.binding.project.to_dict() == before_tool_change
        assert panel.tr('Machining updated. Undo is available.') not in window.ui.messageBox.toPlainText()
        assert not hasattr(panel, 'notice')
        before_rejection = panel.binding.project.to_dict()
        assert not panel.execute(lambda: panel.commands.transfer(['missing-operation'], target.id))
        assert panel.tr('Action rejected: {0}').split('{0}')[0] in window.ui.messageBox.toPlainText()
        assert panel.binding.project.to_dict() == before_rejection
    finally:
        logger.removeHandler(handler)
        logger.setLevel(old_level)
        handler.close()
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
    # A table choice imports a snapshot into the selected step, with undo.
    from dxf2gcode.domain.project.tool_settings import ToolSettings
    table_index = next(i for i in range(editor.tool_combo.count())
                       if isinstance(editor.tool_combo.itemData(i), ToolSettings)
                       and editor.tool_combo.itemData(i).tool_nr == 10)
    table_tool = editor.tool_combo.itemData(table_index)
    before_import = panel.binding.project.to_dict()
    editor.tool_combo.setCurrentIndex(table_index)
    editor.tool_combo.activated.emit(table_index)
    imported_id = panel.binding.project.steps[-1].tool_id
    assert panel.binding.project.tools[imported_id] == table_tool
    assert source_layer.tool_nr == 1
    panel.undo()
    assert panel.binding.project.to_dict() == before_import
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
    check_selected_step()
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
    import re
    switches = re.findall(r'^T(\d+)\s+M6\s*$', code, re.MULTILINE)
    assert switches == ['2', '1'], code
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
        for owner, name in ((panel, 'MachiningPanel'), (panel.parameter_editor, 'MachiningParameters'), (window.geometry_panel, 'GeometryPanel'), (panel.canvas_preview, 'MachiningPreview'), (panel.modifiers, 'TabModifiers')):
            context = next(c for c in ET.parse(ROOT / ('source/i18n/dxf2gcode_' + language + '.ts')).findall('context')
                           if c.findtext('name') == name)
            for message in context.findall('message'):
                assert owner.tr(message.findtext('source')) == message.findtext('translation')
        app.removeTranslator(translator)
    exercise_saved_window_layout(window, app)
    # The reported drawing must pass through the real MainWindow load/preview
    # path and still export its holding tabs after the subdivision fix.
    window.filename = str(ROOT / 'dxf/BreakExample.dxf')
    assert window.load()
    assert len(window.shapes) == 5
    window.machining_panel.refresh_preview()
    output = folder / 'break-example.ngc'
    assert window.exportShapes(saveas=str(output))
    import re
    assert re.search(r'G1 Z\s+-1\.000', output.read_text())
    exercise_tab_modifiers(window, app, folder)


def exercise_tab_modifiers(window, app, folder):
    from importlib import import_module
    from dxf2gcode.presentation.qt.qt_compat import QtCore, PYQT_VERSION
    from dxf2gcode.presentation.qt.machining_panel import ROLE
    QTest = import_module('PyQt%d.QtTest' % PYQT_VERSION).QTest
    Qt = QtCore.Qt
    panel = window.machining_panel
    tabs = panel.modifiers
    records = tabs.records()
    assert len(records) == 4
    assert tabs.usage and len(tabs.groups) == 1
    assert not tabs.paths()
    for i in range(panel.tree.topLevelItemCount()):
        root = panel.tree.topLevelItem(i)
        assert root.data(0, ROLE)[0] == 'step'
        assert panel.current_step() is None or panel.current_step().kind != 'break'
    for identity, (_, entry, source) in records.items():
        assert identity not in panel.entry_items
        window.TreeHandler.setShapeSelected(source, True)
        assert not source.isSelected()
        node = tabs.nodes[identity]
        assert not node.flags() & Qt.ItemFlag.ItemIsUserCheckable
        assert not node.flags() & Qt.ItemFlag.ItemIsDragEnabled
    identity = next(iter(records))
    panel.tree.setCurrentItem(tabs.nodes[identity])
    app.processEvents()
    assert tabs.mode and tabs.context == identity
    assert tabs.editor.isVisible() and panel.parameter_editor.frame.isHidden()
    assert len(tabs.paths()) == 4
    assert tabs.hit(tabs.paths()[identity].pointAtPercent(0))
    # Real mouse events supply QPoint, whereas path APIs require QPointF.
    # The previous direct helper call only covered QPointF and missed Qt6's
    # strict overload handling.
    window.canvas.autoscale()
    app.processEvents()
    for selected in (next(key for key in records if key != identity), identity):
        point = tabs.paths()[selected].pointAtPercent(0).toPoint()
        assert window.canvas.viewport().rect().contains(point)
        QTest.mouseClick(window.canvas.viewport(), Qt.MouseButton.LeftButton, pos=point)
        app.processEvents()
        assert tabs.context == selected
        assert panel.tree.currentItem().data(0, ROLE) == ('modifier', selected)
    original = panel.binding.project.to_dict()
    field = tabs.fields['axis3_mill_depth']
    field.setFocus()
    field.selectAll()
    QTest.keyClicks(field, '-0.5')
    QTest.keyClick(field, Qt.Key.Key_Return)
    app.processEvents()
    step, entry, _ = tabs.records()[identity]
    assert panel.binding.project.resolve(step, entry)[0]['axis3_mill_depth'] == -0.5
    from dxf2gcode.domain.project.machining_project import MachiningProject
    data = panel.binding.project.to_dict()
    assert MachiningProject.from_dict(json.loads(json.dumps(data))).to_dict() == data
    assert tabs.context == identity and tabs.editor.isVisible()
    assert panel.execute(panel.commands.undo)
    assert panel.binding.project.to_dict() == original
    count = sum(len(regions) for regions in tabs.usage.values())
    tabs.select(identity)
    tabs.enabled.click()
    assert sum(len(regions) for regions in tabs.usage.values()) < count
    assert tabs.nodes[identity].parent().data(0, ROLE) == ('modifier_group', 'unused')
    assert panel.execute(panel.commands.undo)
    assert panel.binding.project.to_dict() == original
    tabs.select(identity)
    tabs.remove_button.click()
    assert identity not in tabs.records() and len(window.shapes) == 5
    assert panel.execute(panel.commands.undo)
    assert panel.binding.project.to_dict() == original
    # One imported region remains a shared global modifier when the contour
    # is copied to a second machining step; editing it never duplicates it.
    ordinary = next(step for step in panel.binding.project.steps if step.kind == 'contour')
    assert panel.execute(lambda: panel.commands.create_step('Second pass', ordinary.kind, ordinary.tool_id))
    target = panel.binding.project.steps[-1]
    assert panel.execute(lambda: panel.commands.transfer([ordinary.entries[0].id], target.id, copy=True))
    assert len(tabs.records()) == 4
    assert identity in tabs.usage[ordinary.id] and identity in tabs.usage[target.id]
    assert panel.execute(panel.commands.undo)
    assert panel.execute(panel.commands.undo)
    assert panel.binding.project.to_dict() == original
    tabs.set_mode(False)
    assert not tabs.paths() and tabs.editor.isHidden()
    output = folder / 'break-modifiers-unchanged.ngc'
    assert window.exportShapes(saveas=str(output))
    # Cosmetic representation and undo leave the emitted program unchanged.
    def program(path):
        return '\n'.join(line for line in path.read_text().splitlines()
                         if not line.startswith('('))
    assert program(output) == program(folder / 'break-example.ngc')


def exercise_operation_canvas(window, app, first_id, second_id):
    from importlib import import_module
    from unittest.mock import patch
    from dxf2gcode.presentation.qt.qt_compat import QtCore, PYQT_VERSION
    from dxf2gcode.presentation.qt.qt_compat.QtGui import QPainter, QPixmap
    from dxf2gcode.presentation.qt.qt_compat.QtWidgets import QMenu
    QTest = import_module('PyQt%d.QtTest' % PYQT_VERSION).QTest
    Qt = QtCore.Qt
    panel, canvas = window.machining_panel, window.canvas
    before = panel.binding.project.to_dict()
    panel.commands.update_entries([second_id], {'axis3_mill_depth': -7}, start=(20, 10))
    panel.refresh()
    window.resize(1700, 1100)
    window.ui.mytabWidget.setCurrentWidget(window.geometry_panel)
    source = panel.binding.sources[panel.commands.entries(panel.binding.project, [first_id])[0][1].geometry_id]
    view = window.ui.layersShapesTreeView
    view.clearSelection()
    view.setCurrentIndex(window.TreeHandler.findLayerItemIndexFromShape(source))
    app.processEvents()
    canvas.autoscale()
    app.processEvents()
    preview = panel.canvas_preview
    # A viewport child must remain anchored during real scene scrolling.
    canvas.scale(3, 3)
    canvas.horizontalScrollBar().setValue(canvas.horizontalScrollBar().value()+35)
    app.processEvents()
    assert preview.overlay.pos() == QtCore.QPoint(), preview.overlay.pos()
    canvas.autoscale()
    app.processEvents()
    records = {r.identity: r for r in preview.records if r.geometry == source.geometry_id}
    assert set(records) == {first_id, second_id}
    for identity, record in records.items():
        step = panel.commands.entries(panel.binding.project, [identity])[0][0]
        expected = '%s · %s · T%d' % (step.name, panel.entry_items[identity].text(0), panel.binding.project.tools[step.tool_id].tool_nr)
        assert record.title == expected, (record.title, expected)
    assert records[first_id].plan is not None and records[second_id].plan is not None
    assert records[first_id].plan.passes[-1].depth != records[second_id].plan.passes[-1].depth
    assert preview.counts[source.geometry_id] == (2, 2)
    assert panel.context is None
    from dxf2gcode.presentation.qt.canvas2d import StMoveGUI
    for role, pen in (('cut', StMoveGUI.PEN_COMP_LINE), ('lead_in', StMoveGUI.PEN_LEAD_IN_LINE),
                      ('lead_out', StMoveGUI.PEN_EXIT_LINE), ('rapid', StMoveGUI.PEN_RAPID_MOVE),
                      ('pocket', StMoveGUI.PEN_POCKET_LINE)):
        assert preview.path_pen(role).color() == pen.color()
        assert preview.path_pen(role, active=True).color() == pen.color()
        assert preview.path_pen(role).style() == pen.style()
    assert records[first_id].color == records[second_id].color
    # G40 without allowance must remain on the original contour. Test the
    # calculated coordinates separately from the overlay's screen projection.
    from copy import copy, deepcopy
    isolated = copy(panel.binding)
    isolated.project = deepcopy(panel.binding.project)
    isolated_entry = panel.commands.entries(isolated.project, [first_id])[0][1]
    isolated_entry.overrides.update(cut_cor=40, milling_offset=0)
    layers = isolated.materialize(allow_unresolved=True)
    shape_view = next(shape for layer in layers for shape in layer.shapes if getattr(shape, 'operation_id', None) == first_id)
    from dxf2gcode.adapters.toolpath.preparation import prepare_shape
    from dxf2gcode.adapters.toolpath.preview import preview_result
    from dxf2gcode.application.toolpath.projections import plan_preview_segments
    prepare_shape(shape_view, build_preview=False)
    plan = preview_result(shape_view, window.MyPostProcessor, layers).plan
    assert plan is not None
    from dxf2gcode.presentation.qt.qt_compat.QtGui import QPainterPathStroker
    stroke = QPainterPathStroker()
    stroke.setWidth(.001)
    original_path = stroke.createStroke(window.canvas_scene.graphics_items[id(source)].path)
    for segment in plan_preview_segments(plan):
        if segment.role == 'cut':
            for point in (segment.start, segment.end):
                assert original_path.contains(QtCore.QPointF(point[0], -point[1])), point
                screen = canvas.viewportTransform().map(QtCore.QPointF(point[0], -point[1]))
                assert preview.project(point) == screen
    selected_snapshot = panel.binding.project.to_dict()
    history = len(panel.commands.undo_stack)
    route_count = len(window.canvas_scene.routearrows)
    label = preview.label_rects()[first_id][0].center().toPoint()
    from dxf2gcode.presentation.qt.qt_compat.QtGui import QMouseEvent
    hover = QMouseEvent(QtCore.QEvent.Type.MouseMove, QtCore.QPointF(label),
                       QtCore.QPointF(canvas.viewport().mapToGlobal(label)), Qt.MouseButton.NoButton,
                       Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier)
    app.sendEvent(canvas.viewport(), hover)
    app.processEvents()
    assert preview.hovered == first_id
    assert canvas.viewport().toolTip() == records[first_id].tooltip
    # Click an overlapping cutting path: a popup explicitly chooses the operation.
    hit = next(preview.project(tuple((a+b)/2 for a, b in zip(segment.start, segment.end)))
               for segment in records[first_id].segments if segment.role == 'cut'
               and len(preview.hit_records(preview.project(tuple((a+b)/2 for a, b in zip(segment.start, segment.end))))) > 1)
    def choose(menu, *args):
        return next(action for action in menu.actions() if action.data() == second_id)
    with patch.object(QMenu, 'exec', return_value=None):
        QTest.mouseClick(canvas.viewport(), Qt.MouseButton.LeftButton, pos=hit.toPoint())
    assert set(panel.selected_entries()) == {first_id, second_id}
    with patch.object(QMenu, 'exec', new=choose) as popup:
        QTest.mouseClick(canvas.viewport(), Qt.MouseButton.LeftButton, pos=hit.toPoint())
    app.processEvents()
    assert panel.context == second_id and panel.selected_entries() == [second_id]
    assert preview.counts[source.geometry_id] == (1, 2)
    assert window.ui.mytabWidget.currentWidget() is window.geometry_panel
    pixmap = QPixmap(100, 100)
    painter = QPainter(pixmap)
    window.canvas_scene.graphics_items[id(source)].paint(painter, None, None)
    assert painter.pen().style() == Qt.PenStyle.DotLine
    painter.end()
    labels = preview.label_rects()
    QTest.mouseClick(canvas.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.ControlModifier,
                     pos=labels[first_id][0].center().toPoint())
    app.processEvents()
    assert set(panel.selected_entries()) == {first_id, second_id}
    assert panel.context == first_id and preview.counts[source.geometry_id] == (2, 2)
    assert panel.parameter_editor.target()[1].id == first_id
    assert panel.parameter_editor.fields['axis3_mill_depth'].isEnabled()
    editor = panel.parameter_editor
    if len({panel.binding.project.tools[step.tool_id] for step, _ in panel.commands.entries(panel.binding.project, [first_id, second_id])}) > 1:
        assert editor.tool_combo.currentText() == editor.tr('Different tools')
        snapshot = panel.binding.project.to_dict()
        editor.tool_combo.activated.emit(0)  # Mixed-state marker is never a tool assignment.
        assert panel.binding.project.to_dict() == snapshot
    painter = QPainter(pixmap)
    window.canvas_scene.graphics_items[id(source)].paint(painter, None, None)
    assert painter.pen().style() == Qt.PenStyle.SolidLine
    painter.end()
    assert panel.binding.project.to_dict() == selected_snapshot
    assert len(panel.commands.undo_stack) == history
    assert len(window.canvas_scene.routearrows) == route_count
    old_disabled = window.ui.actionShowDisabledPaths.isChecked()
    panel.execute(lambda: panel.commands.update_entries([second_id], enabled=False))
    window.ui.actionShowDisabledPaths.setChecked(False)
    panel.refresh_preview()
    assert second_id not in {r.identity for r in preview.records}
    window.ui.actionShowDisabledPaths.setChecked(True)
    assert any(r.identity == second_id and not r.enabled for r in preview.records)
    panel.undo()
    panel.undo()
    assert panel.binding.project.to_dict() == before
    window.ui.actionShowDisabledPaths.setChecked(old_disabled)


def exercise_saved_window_layout(window, app):
    ui = window.ui
    window.showNormal()
    window.resize(1700, 1100)
    app.processEvents()
    ui.splitter.setSizes([600, 1050])
    ui.messageSplitter.setSizes([850, 130])
    window.layout_state.update_minimum()
    app.processEvents()
    sidebar, messages = ui.splitter.sizes()[0], ui.messageSplitter.sizes()[1]
    canvas_size = ui.canvas.size()
    parameters = window.machining_panel.splitter.sizes()[1]
    window.resize(window.width()+240, window.height()+180)
    app.processEvents()
    assert abs(ui.splitter.sizes()[0]-sidebar) <= 1
    assert abs(ui.messageSplitter.sizes()[1]-messages) <= 1
    assert ui.canvas.width() > canvas_size.width()+200
    assert ui.canvas.height() > canvas_size.height()+140
    assert abs(window.machining_panel.splitter.sizes()[1]-parameters) <= 2
    window.geometry_panel.sections[0][0].setChecked(False)
    app.processEvents()
    saved = {key: splitter.sizes() for key, splitter in window.layout_state.splitters.items()}
    window.saveWindowState()
    assert window.settings.contains('MainWindow/sidebarWidth'), (window.settings.group(), window.settings.allKeys(),
        window.settings.status(), window.saveWindowState, window.layout_state.save)
    window.settings.sync()
    ui.splitter.setSizes([400, 1300])
    ui.messageSplitter.setSizes([900, 60])
    window.geometry_panel.sections[0][0].setChecked(True)
    window.restoreWindowState()
    app.processEvents()
    app.processEvents()
    assert abs(ui.splitter.sizes()[0]-sidebar) <= 2, (ui.splitter.sizes(), sidebar, window.size(),
        window.layout_state.sidebar, window.layout_state.timer.isActive(), window.settings.value('MainWindow/sidebarWidth'))
    assert abs(ui.messageSplitter.sizes()[1]-messages) <= 2, (ui.messageSplitter.sizes(), messages)
    assert not window.geometry_panel.sections[0][0].isChecked()
    for key, splitter in window.layout_state.splitters.items():
        ui.mytabWidget.setCurrentWidget(window.geometry_panel if key == 'geometry' else window.machining_panel)
        app.processEvents()
        app.processEvents()
        # restoreGeometry may clamp the window to the test screen. Extra tree
        # space follows the available height; fixed parameter/header heights do not.
        indices = (0,) if key == 'geometry' else (1,) if key == 'machining' else (0, 1)
        assert all(abs(splitter.sizes()[i]-saved[key][i]) <= 3 for i in indices), (key, splitter.sizes(), saved[key])


def exercise_section_content_height(window, app):
    from dxf2gcode.presentation.qt.qt_compat import QtCore
    from dxf2gcode.presentation.qt.qt_compat.QtWidgets import QSplitter
    editor = window.machining_panel.parameter_editor
    assert not editor.frame.findChildren(QSplitter)
    assert editor.scroll.widget().layout().alignment() == QtCore.Qt.AlignmentFlag(0)
    # The trailing stretch is below all groups, never inside the forms.
    for group in editor.groups.values():
        rows = group.layout()
        assert rows.count() >= 1
    assert editor.scroll.widget().layout().itemAt(2).spacerItem() is not None


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
    clicked = max(shape.start_point_candidates(), key=lambda point: point.distance(shape.get_start_end_points(True)))
    with patch.object(QMenu, 'exec', new=capture):
        canvas = MyDropDownMenu(window.canvas_scene, QtCore.QPoint(), clicked)
    layout = [None if a.isSeparator() else a.text() for a in canvas.actions()]
    expected = [canvas.tr('Move workpiece zero here ...'), None,
                canvas.tr('Invert Selection'), canvas.tr('Disable Selection'), canvas.tr('Enable Selection'), None,
                canvas.tr('Switch Direction'), canvas.tr('Set Nearest StartPoint'), canvas.tr('Set Sharpest StartPoint'), None,
                canvas.tr('Cutter Compensation'), None, panel.tr('Assign machining…')]
    assert layout == expected, (layout, expected)
    with patch.object(panel, 'assign_machining') as assign:
        next(action for action in canvas.actions() if action.text() == panel.tr('Assign machining…')).trigger()
        assert assign.call_args.kwargs['shapes'] == canvas.selectedItems
        assert assign.call_args.kwargs['global_position'] == QtCore.QPoint()
    def trigger(source):
        next(a for a in canvas.actions() if a.text() == canvas.tr(source)).trigger()
    trigger('Disable Selection')
    assert not panel.commands.entries(panel.binding.project, [identity])[0][1].enabled
    assert panel.commands.entries(panel.binding.project, [other_identity])[0][1].enabled
    trigger('Enable Selection')
    assert panel.commands.entries(panel.binding.project, [identity])[0][1].enabled
    panel.undo()
    panel.undo()
    assert panel.binding.project.to_dict() == before
    clockwise = panel.commands.entries(panel.binding.project, [identity])[0][1].clockwise
    trigger('Switch Direction')
    assert panel.commands.entries(panel.binding.project, [identity])[0][1].clockwise != clockwise
    assert panel.commands.entries(panel.binding.project, [other_identity])[0][1].clockwise == clockwise
    panel.undo()
    assert panel.binding.project.to_dict() == before
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


def exercise_automatic_target_reuse(window, app):
    from copy import deepcopy
    from dataclasses import replace
    from unittest.mock import patch
    from dxf2gcode.presentation.qt.qt_compat.QtWidgets import QInputDialog
    panel = window.machining_panel
    before, history = panel.binding.project.to_dict(), len(panel.commands.undo_stack)
    source = panel.binding.project.steps[0]
    identity = source.entries[0].id
    tool = replace(panel.binding.project.tools[source.tool_id], tool_nr=2)
    targets = []
    for _ in range(2):
        panel.commands.create_step('Same target name', 'contour', tool)
        step = panel.binding.project.steps[-1]
        panel.commands.edit_step(step.id, step.name, step.kind, step.tool_id, deepcopy(source.defaults))
        targets.append(step.id)
    panel.refresh()
    panel.tree.clearSelection()
    panel.tree.setCurrentItem(panel.entry_items[identity])
    panel.entry_items[identity].setSelected(True)
    snapshot, count = panel.binding.project.to_dict(), len(panel.commands.undo_stack)
    with patch.object(QInputDialog, 'getItem', return_value=('', False)) as choice:
        assert not panel.execute(lambda: panel.commands.set_operation_tool([identity], tool))
        assert choice.call_count == 1
    assert panel.binding.project.to_dict() == snapshot and len(panel.commands.undo_stack) == count
    assert not panel.commands.target_choices
    def choose(parent, title, label, items, **kwargs):
        assert len(items) == 2 and items[0] != items[1]
        return items[1], True
    with patch.object(QInputDialog, 'getItem', side_effect=choose) as choice:
        assert panel.execute(lambda: panel.commands.set_operation_tool([identity], tool))
        assert choice.call_count == 1
    assert len(panel.binding.project.steps) == 3
    assert panel.commands.entries(panel.binding.project, [identity])[0][0].id == targets[1]
    assert len(panel.commands.undo_stack) == count+1 and not panel.commands.target_choices
    panel.undo()
    assert panel.binding.project.to_dict() == snapshot
    # A previous choice is not silently reused for a subsequent action.
    with patch.object(QInputDialog, 'getItem', return_value=('', False)) as choice:
        assert not panel.execute(lambda: panel.commands.set_operation_tool([identity], tool))
        assert choice.call_count == 1
    assert panel.binding.project.to_dict() == snapshot
    while len(panel.commands.undo_stack) > history:
        panel.undo()
    assert panel.binding.project.to_dict() == before
    panel.tree.clearSelection(); panel.tree.setCurrentItem(None); panel.context = None
    panel.show_parameters()


def exercise_multi_parameter_editing(window, app):
    from importlib import import_module
    from dxf2gcode.presentation.qt.qt_compat import QtCore, PYQT_VERSION
    from dxf2gcode.presentation.qt.qt_compat.QtGui import QPalette
    QTest = import_module('PyQt%d.QtTest' % PYQT_VERSION).QTest
    panel, editor = window.machining_panel, window.machining_panel.parameter_editor
    before, history = panel.binding.project.to_dict(), len(panel.commands.undo_stack)
    first = panel.binding.project.steps[0]
    # Distinct original contours with one assignment each can be edited
    # directly from Geometry. An unsupported parameter alone stays disabled.
    for source in window.shapes:
        window.TreeHandler.setShapeSelected(source, True)
    panel.geometry_selected()
    assert editor.fields['f_g1_plane'].isEnabled()
    assert not editor.fields['overcut_enabled'].isEnabled()  # fixture also has an open line
    assert editor.fields['overcut_enabled'].currentText() == editor.tr('Not jointly available')
    editor.commit('f_g1_plane', 77.123456789)
    assert len(panel.commands.undo_stack) == history+1
    assert all(entry.overrides['f_g1_plane'] == 77.123456789 for step in panel.binding.project.steps for entry in step.entries)
    panel.undo()
    assert panel.binding.project.to_dict() == before
    first = panel.binding.project.steps[0]
    a = first.entries[0].id
    panel.commands.transfer([a], first.id, copy=True)
    b = panel.binding.project.steps[0].entries[-1].id
    panel.commands.create_step('Batch finish', 'contour', first.tool_id)
    second = panel.binding.project.steps[-1]
    panel.commands.transfer([b], second.id)
    for step_id, feed in ((first.id, 100), (second.id, 200)):
        step = panel.commands.step(panel.binding.project, step_id)
        panel.commands.edit_step(step.id, step.name, step.kind, step.tool_id,
            dict(step.defaults, f_g1_plane=feed, axis3_mill_depth=-3, axis3_start_mill_depth=0))
    panel.commands.update_entries([a, b], {'f_g1_plane': None, 'axis3_mill_depth': None, 'axis3_start_mill_depth': None})
    panel.commands.update_entries([b], {'axis3_mill_depth': -3}, start=(30, 27))
    panel.refresh()
    def select():
        panel.busy = True
        panel.tree.clearSelection()
        panel.tree.setCurrentItem(panel.entry_items[a])
        for identity in (a, b):
            panel.entry_items[identity].setSelected(True)
        panel.busy = False
        panel.selection_changed()
        app.processEvents()
    select()
    field = editor.fields['f_g1_plane']
    assert field.isEnabled() and field.text() == ''
    assert field.placeholderText() == editor.tr('Different')
    assert field._numeric_display.value is None
    assert editor.fields['axis3_mill_depth'].text() == '-3.000'
    assert editor.origins['axis3_mill_depth'].property('provenance') == 'mixed'
    assert editor.fields['axis3_mill_depth'].palette().color(QPalette.ColorRole.Text) == editor.frame.palette().color(QPalette.ColorRole.Text)
    assert editor.fields['axis3_start_mill_depth'].palette().color(QPalette.ColorRole.Text) == QtCore.Qt.GlobalColor.gray
    saved, stack = panel.binding.project.to_dict(), len(panel.commands.undo_stack)
    field.setFocus(); app.processEvents()
    QTest.keyClick(field, QtCore.Qt.Key.Key_Return)
    assert panel.binding.project.to_dict() == saved and len(panel.commands.undo_stack) == stack
    exact = 12.123456789
    field.selectAll(); QTest.keyClicks(field, str(exact)); QTest.keyClick(field, QtCore.Qt.Key.Key_Return)
    assert len(panel.commands.undo_stack) == stack+1
    assert set(panel.selected_entries()) == {a, b}
    for step, entry in panel.commands.entries(panel.binding.project, [a, b]):
        assert entry.overrides['f_g1_plane'] == exact
    assert panel.binding.project.to_dict()['tools'] == saved['tools']
    assert panel.binding.project.steps[0].entries[1].overrides == saved['steps'][0]['entries'][1]['overrides']
    panel.undo(); assert panel.binding.project.to_dict() == saved
    panel.redo()
    editor.resets['f_g1_plane'].trigger()
    for _, entry in panel.commands.entries(panel.binding.project, [a, b]):
        assert 'f_g1_plane' not in entry.overrides
    assert field.placeholderText() == editor.tr('Different')
    # Combo selection applies to both assignments in one undo step.
    editor.commit('lead_in_mode', 'off')
    for _, entry in panel.commands.entries(panel.binding.project, [a, b]):
        assert entry.overrides['lead_in_mode'] == 'off'
    stack = len(panel.commands.undo_stack)
    editor.commit('axis3_retract', 21.123456789)
    assert len(panel.commands.undo_stack) == stack+1
    assert all(step.defaults['axis3_retract'] == 21.123456789 for step in panel.binding.project.steps)
    assert '2' in editor.origins['axis3_retract'].toolTip()
    x = window.ui.startAtXLineEdit
    x.setFocus(); x.selectAll(); QTest.keyClicks(x, '11.123456789'); QTest.keyClick(x, QtCore.Qt.Key.Key_Return)
    entries = [entry for _, entry in panel.commands.entries(panel.binding.project, [a, b])]
    assert entries[0].start[0] == entries[1].start[0] == 11.123456789
    assert entries[1].start[1] == 27
    # Geometry overview is read-only when either contour is multiply linked.
    panel.geometry_selected()
    assert not field.isEnabled() and not editor.tool_combo.isEnabled()
    snapshot, stack = panel.binding.project.to_dict(), len(panel.commands.undo_stack)
    editor.commit('f_g1_plane', 999)
    assert panel.binding.project.to_dict() == snapshot and len(panel.commands.undo_stack) == stack
    select()
    assert field.isEnabled()
    while len(panel.commands.undo_stack) > history:
        panel.undo()
    assert panel.binding.project.to_dict() == before
    panel.tree.clearSelection(); panel.tree.setCurrentItem(None); panel.context = None
    panel.show_parameters()


def exercise_multi_tool_selection(window, app):
    from dxf2gcode.domain.project.tool_settings import ToolSettings
    panel = window.machining_panel
    before = panel.binding.project.to_dict()
    first = panel.binding.project.steps[0]
    entry = first.entries[0]
    for _ in range(2):
        panel.commands.transfer([entry.id], first.id, copy=True)
    before_tool = panel.binding.project.to_dict()
    ids = [e.id for e in panel.binding.project.steps[0].entries]
    panel.refresh()
    def select_and_change(selection):
        panel.tree.clearSelection()
        panel.tree.setCurrentItem(panel.entry_items[selection[0]])
        for identity in selection:
            panel.entry_items[identity].setSelected(True)
        app.processEvents()
        editor = panel.parameter_editor
        assert editor.tool_combo.isEnabled()
        if len(selection) > 1:
            assert editor.fields['axis3_mill_depth'].isEnabled()
        else:
            assert editor.target()[1].id == selection[0]
        index = next(i for i in range(editor.tool_combo.count())
                     if isinstance(editor.tool_combo.itemData(i), ToolSettings)
                     and editor.tool_combo.itemData(i).tool_nr == 2)
        editor.tool_combo.setCurrentIndex(index)
        editor.tool_combo.activated.emit(index)
    for count in (1, 2):
        select_and_change(ids[:count])
        source, target = panel.binding.project.steps
        assert source.id == first.id and [e.id for e in source.entries] == ids[count:]
        assert [e.id for e in target.entries] == ids[:count]
        assert target.defaults == first.defaults and target.kind == first.kind
        assert panel.binding.project.to_dict()['steps'][1]['entries'] == before_tool['steps'][0]['entries'][:count]
        assert panel.binding.project.tools[target.tool_id].tool_nr == 2
        assert panel.binding.project.tools[source.tool_id].tool_nr == 1
        after_tool = panel.binding.project.to_dict()
        panel.undo()
        assert panel.binding.project.to_dict() == before_tool
        panel.redo()
        assert panel.binding.project.to_dict() == after_tool
        panel.undo()
    select_and_change(ids)
    assert len(panel.binding.project.steps) == 1
    assert panel.binding.project.steps[0].id == first.id
    assert panel.binding.project.tools[panel.binding.project.steps[0].tool_id].tool_nr == 2
    panel.undo()
    panel.undo()
    panel.undo()
    assert panel.binding.project.to_dict() == before
    panel.tree.clearSelection()
    panel.tree.setCurrentItem(None)
    panel.context = None
    panel.show_parameters()


def exercise_tool_choices(window, app):
    from copy import deepcopy
    from dataclasses import replace
    from dxf2gcode.presentation.qt.qt_compat import QtCore
    from dxf2gcode.presentation.qt.qt_compat.QtWidgets import QComboBox
    from dxf2gcode.domain.project.tool_settings import ToolSettings
    import dxf2gcode.bootstrap.runtime_state as g
    panel = window.machining_panel
    project = panel.binding.project
    before = deepcopy(project.to_dict())
    identity, tool = next(iter(project.tools.items()))
    combo = QComboBox(panel)
    for units in ('mm', 'in'):
        project.units = units
        project.tools['test-distinct-tool'] = replace(tool, lead_length=tool.lead_length + .00000001)
        panel.populate_tool_combo(combo, identity)
        assert combo.currentData() == identity
        assert all(combo.model().item(i).isEnabled() for i in range(combo.count()))
        values = [combo.itemData(i) if isinstance(combo.itemData(i), ToolSettings)
                  else project.tools[combo.itemData(i)] for i in range(combo.count())]
        assert len(values) == len(set(values))
        a, b = combo.findData(identity), combo.findData('test-distinct-tool')
        assert combo.itemText(a) != combo.itemText(b)
        assert '#' not in combo.itemText(a) and 'Ø' in combo.itemText(a) and units in combo.itemText(a)
        assert panel.parameter_label('lead_length') in combo.itemText(b)
        assert panel.tr('Project deviation') in combo.itemText(b)
        table_index = next(i for i in range(combo.count()) if isinstance(combo.itemData(i), ToolSettings))
        table_tool = combo.itemData(table_index)
        assert table_tool.tool_diameter == panel.profile_tool(table_tool.tool_nr,
                g.config.vars.Tool_Parameters[str(table_tool.tool_nr)]).tool_diameter
        assert combo.itemData(table_index, QtCore.Qt.ItemDataRole.ToolTipRole)
        del project.tools['test-distinct-tool']
    project.units = before['units']
    assert project.to_dict() == before
    # Both the dialog and the persistent form use the same choices.
    def inspect_dialog():
        dialog = app.activeModalWidget()
        choices = next(c for c in dialog.findChildren(QComboBox) if c.findData(identity) >= 0)
        assert all(choices.model().item(i).isEnabled() for i in range(choices.count()))
        assert choices.currentData() == identity
        dialog.reject()
    QtCore.QTimer.singleShot(0, inspect_dialog)
    assert panel.step_dialog(project.steps[0]) is None
    combo.deleteLater()
    # Choosing the table equivalent of a deviation replaces every shared user.
    before_shared = project.to_dict()
    first = project.steps[0]
    table = panel.profile_tool(tool.tool_nr, g.config.vars.Tool_Parameters[str(tool.tool_nr)])
    panel.commands.create_step('Shared tool test', first.kind, first.tool_id)
    panel.commands.refresh_tool(first.tool_id, replace(table, speed=table.speed + 111))
    old_id = panel.binding.project.steps[0].tool_id
    affected = [s.id for s in panel.binding.project.steps if s.tool_id == old_id]
    panel.refresh()
    panel.tree.setCurrentItem(panel.tree.topLevelItem(0))
    editor = panel.parameter_editor
    def accept_table_replacement():
        dialog = app.activeModalWidget()
        tools = next(c for c in dialog.findChildren(QComboBox)
                     if any(c.itemData(i) == table for i in range(c.count())))
        tools.setCurrentIndex(next(i for i in range(tools.count()) if tools.itemData(i) == table))
        dialog.accept()
    QtCore.QTimer.singleShot(0, accept_table_replacement)
    data = panel.step_dialog(panel.binding.project.steps[0])
    assert data[2] == table and data[5] is True
    target_index = next(i for i in range(editor.tool_combo.count())
                        if editor.tool_combo.itemData(i) == table)
    editor.tool_combo.setCurrentIndex(target_index)
    assert panel.replaces_shared_tool(editor.tool_combo, editor.target()[0])
    before_replace = panel.binding.project.to_dict()
    editor.tool_combo.activated.emit(target_index)
    assert all(panel.binding.project.tools[s.tool_id] == table for s in panel.binding.project.steps
               if s.id in affected)
    assert old_id not in panel.binding.project.tools
    after_replace = panel.binding.project.to_dict()
    panel.undo()
    assert panel.binding.project.to_dict() == before_replace
    panel.redo()
    assert panel.binding.project.to_dict() == after_replace
    panel.undo()
    panel.undo()
    panel.undo()
    assert panel.binding.project.to_dict() == before_shared
    panel.tree.clearSelection()
    panel.tree.setCurrentItem(None)
    panel.context = None
    panel.show_parameters()


def exercise_assignment_dialog(window, app, shape):
    from unittest.mock import patch
    from dxf2gcode.presentation.qt.qt_compat import QtCore
    from dxf2gcode.presentation.qt.qt_compat.QtWidgets import QComboBox, QLineEdit, QMenu, QDialogButtonBox
    panel = window.machining_panel
    pairs = panel.binding.operations_by_geometry()[shape.geometry_id]
    identities = [entry.id for _, entry in pairs]
    a = identities[0]
    source = panel.commands.entries(panel.binding.project, [a])[0][0]
    target = next(step for step in panel.binding.project.steps if step.id != source.id and step.kind == source.kind)
    before = panel.binding.project.to_dict()
    def select(ids):
        panel.busy = True
        panel.tree.clearSelection()
        panel.tree.setCurrentItem(panel.entry_items[ids[0]])
        for identity in ids:
            panel.entry_items[identity].setSelected(True)
        panel.busy = False
        panel.selection_changed()
    def run(configure):
        errors = []
        def modal():
            dialog = app.activeModalWidget()
            try:
                assert dialog.objectName() == 'machiningAssignmentDialog'
                configure(dialog)
            except BaseException as error:
                errors.append(error)
                dialog.reject()
        QtCore.QTimer.singleShot(0, modal)
        panel.assign_machining(identities=[a], global_position=panel.mapToGlobal(QtCore.QPoint(20, 20)))
        if errors:
            raise errors[0]
    select([a])
    count = len(panel.commands.undo_stack)
    def cancel(dialog):
        assert dialog.findChild(QComboBox, 'assignmentTargetType').currentData() == 'existing'
        assert dialog.findChild(QComboBox, 'assignmentAction').currentData() == 'copy'
        for name, cls in (('assignmentStepName', QLineEdit), ('assignmentStepKind', QComboBox), ('assignmentStepTool', QComboBox)):
            assert dialog.findChild(cls, name).isVisible()
            assert not dialog.findChild(cls, name).isEnabled()
        dialog.reject()
    run(cancel)
    assert panel.binding.project.to_dict() == before and len(panel.commands.undo_stack) == count
    for mode in ('copy', 'move'):
        select([a])
        def existing(dialog):
            combo = dialog.findChild(QComboBox, 'assignmentTargetStep')
            combo.setCurrentIndex(combo.findData(target.id))
            action = dialog.findChild(QComboBox, 'assignmentAction')
            action.setCurrentIndex(action.findData(mode))
            dialog.accept()
        run(existing)
        assert len(panel.commands.undo_stack) == count+1
        entries = panel.commands.step(panel.binding.project, target.id).entries
        assert len(entries) == len(next(step for step in before['steps'] if step['id'] == target.id)['entries'])+1
        assert (entries[-1].id == a) == (mode == 'move')
        assert entries[-1].geometry_id == shape.geometry_id
        after = panel.binding.project.to_dict()
        panel.undo(); assert panel.binding.project.to_dict() == before
        panel.redo(); assert panel.binding.project.to_dict() == after
        panel.undo()
    for mode in ('copy', 'move'):
        select([a])
        def new(dialog):
            target_type = dialog.findChild(QComboBox, 'assignmentTargetType')
            fields = [dialog.findChild(cls, name) for name, cls in (
                ('assignmentTargetStep', QComboBox), ('assignmentStepName', QLineEdit),
                ('assignmentStepKind', QComboBox), ('assignmentStepTool', QComboBox))]
            initial_size = dialog.size()
            initial_positions = [field.pos() for field in fields]
            button_position = dialog.findChild(QDialogButtonBox).pos()
            target_type.setCurrentIndex(target_type.findData('new'))
            assert dialog.findChild(QComboBox, 'assignmentTargetStep').isVisible()
            assert not dialog.findChild(QComboBox, 'assignmentTargetStep').isEnabled()
            assert dialog.findChild(QLineEdit, 'assignmentStepName').isVisible()
            assert dialog.findChild(QComboBox, 'assignmentStepKind').isVisible()
            assert dialog.findChild(QComboBox, 'assignmentStepTool').isVisible()
            action = dialog.findChild(QComboBox, 'assignmentAction')
            assert action.currentData() == 'copy'  # Untouched initial choice also survives.
            action.setCurrentIndex(action.findData(mode))
            dialog.findChild(QLineEdit, 'assignmentStepName').setText('Assignment '+mode)
            kinds = dialog.findChild(QComboBox, 'assignmentStepKind')
            tools = dialog.findChild(QComboBox, 'assignmentStepTool')
            original_kind, original_tool = kinds.currentIndex(), tools.currentIndex()
            kinds.setCurrentIndex((original_kind+1) % kinds.count())
            tools.setCurrentIndex((original_tool+1) % tools.count())
            destination = dialog.findChild(QComboBox, 'assignmentTargetStep')
            destination.setCurrentIndex(destination.findData(target.id))
            state = [field.currentData() if isinstance(field, QComboBox) else field.text() for field in fields]
            target_type.setCurrentIndex(target_type.findData('existing'))
            target_type.setCurrentIndex(target_type.findData('new'))
            app.processEvents()
            assert action.currentData() == mode
            assert [field.currentData() if isinstance(field, QComboBox) else field.text() for field in fields] == state
            assert dialog.size() == initial_size
            assert [field.pos() for field in fields] == initial_positions
            assert dialog.findChild(QDialogButtonBox).pos() == button_position
            kinds.setCurrentIndex(original_kind)
            tools.setCurrentIndex(original_tool)
            dialog.accept()
        run(new)
        created = panel.binding.project.steps[-1]
        assert created.name == 'Assignment '+mode and len(created.entries) == 1
        assert (created.entries[0].id == a) == (mode == 'move')
        panel.undo(); assert panel.binding.project.to_dict() == before
    # Both entry points preserve explicitly selected duplicate assignments.
    select(identities)
    with patch.object(panel, 'assignment_dialog', return_value=None) as dialog:
        panel.assign_machining(shapes=[shape])
        assert set(dialog.call_args.args[0]) == set(identities)
    panel.geometry_selected()
    with patch.object(panel, 'assignment_dialog', return_value=None) as dialog:
        panel.assign_machining(shapes=[shape])
        dialog.assert_not_called()
    assert panel.binding.project.to_dict() == before
    select([a])
    menus = []
    with patch.object(QMenu, 'exec', new=lambda menu, point: menus.append(menu)):
        panel.menu(panel.tree.visualItemRect(panel.entry_items[a]).center())
    labels = [action.text() for action in menus[0].actions()]
    assert labels.count(panel.tr('Assign machining…')) == 1
    for removed in ('Edit step', 'Edit step defaults', 'Copy to step', 'Move to step', 'Create machining step…'):
        assert panel.tr(removed) not in labels
    advanced = next(action.menu() for action in menus[0].actions() if action.text() == panel.tr('Advanced'))
    assert len(advanced.actions()) == 3
    with patch.object(panel, 'step_dialog', return_value=None) as edit:
        panel.tree.itemDoubleClicked.emit(panel.entry_items[a].parent(), 0)
        edit.assert_called_once()


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
