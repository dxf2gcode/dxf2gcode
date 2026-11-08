# -*- coding: utf-8 -*-
"""Run the real MainWindow workflow in an isolated Qt process."""
from __future__ import absolute_import

import os
import subprocess
import sys
import tempfile
import unittest

_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_DIR = os.path.dirname(_TEST_DIR)


class TestMainWindowWorkflow(unittest.TestCase):
    """Exercise load, canvas plot, tree edit, preview, and export together."""

    def test_pocket_machine_and_compensation_changes_refresh_warning_and_plan(self):
        with tempfile.TemporaryDirectory(prefix='d2g_pocket_changes_') as folder:
            env = os.environ.copy()
            env.update(QT_QPA_PLATFORM='offscreen', D2G_WORKFLOW_TEMP=folder)
            result = subprocess.run([sys.executable, __file__, '--worker', '--pocket-worker'],
                cwd=folder, env=env, capture_output=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout.decode(errors='replace') +
                             result.stderr.decode(errors='replace'))

    def test_context_zero_prefills_existing_dialog_and_preserves_cancel(self):
        with tempfile.TemporaryDirectory(prefix='d2g_context_zero_') as folder:
            env = os.environ.copy()
            env.update(QT_QPA_PLATFORM='offscreen', D2G_WORKFLOW_TEMP=folder)
            result = subprocess.run([sys.executable, __file__, '--worker', '--zero-worker'],
                cwd=folder, env=env, capture_output=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout.decode('utf-8', errors='replace') +
                             result.stderr.decode('utf-8', errors='replace'))

    def test_machine_and_tolerance_config_changes_reload_without_restart(self):
        with tempfile.TemporaryDirectory(prefix='d2g_live_config_') as folder:
            env = os.environ.copy()
            env.update(QT_QPA_PLATFORM='offscreen', D2G_WORKFLOW_TEMP=folder)
            result = subprocess.run([sys.executable, __file__, '--worker', '--live-config-worker'],
                cwd=folder, env=env, capture_output=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout.decode('utf-8', errors='replace') +
                             result.stderr.decode('utf-8', errors='replace'))

    def test_restart_changes_wait_for_config_close_and_handle_launch_failure(self):
        with tempfile.TemporaryDirectory(prefix='d2g_restart_') as folder:
            env = os.environ.copy()
            env.update(QT_QPA_PLATFORM='offscreen', D2G_WORKFLOW_TEMP=folder)
            result = subprocess.run([sys.executable, __file__, '--worker', '--restart-worker'],
                cwd=folder, env=env, capture_output=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout.decode('utf-8', errors='replace') +
                             result.stderr.decode('utf-8', errors='replace'))

    def test_profile_defaults_reach_startup_actions_and_new_profiles(self):
        with tempfile.TemporaryDirectory(prefix='d2g_profile_defaults_') as folder:
            env=os.environ.copy()
            env.update(QT_QPA_PLATFORM='offscreen',D2G_WORKFLOW_TEMP=folder)
            result=subprocess.run([sys.executable,__file__,'--worker','--profile-default-worker'],
                                  cwd=folder,env=env,capture_output=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stdout.decode('utf-8',errors='replace')+
                             result.stderr.decode('utf-8',errors='replace'))

    def test_translated_machine_menu_keeps_the_correct_actions(self):
        with tempfile.TemporaryDirectory(prefix="d2g_translated_menu_") as temp_dir:
            env = os.environ.copy()
            env.update(QT_QPA_PLATFORM="offscreen", D2G_WORKFLOW_TEMP=temp_dir)
            result = subprocess.run(
                [sys.executable, __file__, "--worker", "--translation-worker"],
                cwd=temp_dir, env=env, capture_output=True, timeout=30)
            self.assertEqual(result.returncode, 0,
                             result.stdout.decode("utf-8", errors="replace") +
                             result.stderr.decode("utf-8", errors="replace"))

    def test_startpoint_actions_respect_manual_route_display(self):
        with tempfile.TemporaryDirectory(prefix="d2g_startpoint_route_") as temp_dir:
            env = os.environ.copy()
            env.update(QT_QPA_PLATFORM="offscreen", D2G_WORKFLOW_TEMP=temp_dir)
            result = subprocess.run(
                [sys.executable, __file__, "--worker", "--startpoint-worker"],
                cwd=temp_dir, env=env, capture_output=True, timeout=30)
            self.assertEqual(result.returncode, 0,
                             result.stdout.decode("utf-8", errors="replace") +
                             result.stderr.decode("utf-8", errors="replace"))

    def test_shown_frontplate_tree_buttons_after_manual_collapse(self):
        with tempfile.TemporaryDirectory(prefix="d2g_tree_fold_") as temp_dir:
            env = os.environ.copy()
            env.update(QT_QPA_PLATFORM="offscreen", D2G_WORKFLOW_TEMP=temp_dir)
            result = subprocess.run(
                [sys.executable, __file__, "--worker", "--fold-worker"],
                cwd=temp_dir, env=env, capture_output=True, timeout=15)
            self.assertEqual(result.returncode, 0,
                             result.stdout.decode("utf-8", errors="replace") +
                             result.stderr.decode("utf-8", errors="replace"))

    def test_mainwindow_load_edit_preview_and_export(self):
        with tempfile.TemporaryDirectory(prefix="d2g_mainwindow_") as temp_dir:
            env = os.environ.copy()
            env["QT_QPA_PLATFORM"] = "offscreen"
            env["D2G_WORKFLOW_TEMP"] = temp_dir
            result = subprocess.run(
                [sys.executable, __file__, "--worker"],
                cwd=temp_dir,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=120)

            self.assertEqual(
                result.returncode, 0,
                result.stdout.decode("utf-8", errors="replace") +
                result.stderr.decode("utf-8", errors="replace"))


def _check_startpoint_route_display(window, app):
    from unittest.mock import patch
    from dxf2gcode.presentation.qt.canvas import MyDropDownMenu
    from dxf2gcode.presentation.qt.qt_compat.QtCore import QPoint
    from dxf2gcode.presentation.qt.qt_compat.QtWidgets import QMenu

    shape = next(shape for shape in window.shapes if shape.closed and len(shape.geos) > 2)
    view = window.ui.layersShapesTreeView
    view.setCurrentIndex(window.TreeHandler.findLayerItemIndexFromShape(shape))
    assert shape.isSelected()
    scene = window.canvas_scene
    window.TreeHandler.updateExportOrder()
    order = [(layer.nr, list(layer.exp_order_complete)) for layer in window.layerContents]

    panel = getattr(window, 'machining_panel', None)
    if panel is not None and panel.binding is not None:
        from dxf2gcode.presentation.qt import machining_panel as panel_module
        entry = panel.binding.operations_by_geometry()[shape.geometry_id][0][1]
        panel.context = entry.id
        panel.binding.activate_operation(entry.id)
        original_start = shape.get_start_end_points(True)
        for live in (False, True):
            window.ui.actionLiveUpdateExportRoute.setChecked(live)
            for source in ('Set Nearest StartPoint', 'Set Sharpest StartPoint'):
                for visible in ((False, True) if not live else (True,)):
                    window.deleteG0Paths()
                    if visible:
                        window.updateExportRoute()
                    routes = tuple(scene.routearrows)
                    point = shape.start_point_candidates()[len(shape.geos)//2]
                    with patch.object(QMenu, 'exec', return_value=None):
                        menu = MyDropDownMenu(scene, QPoint(), point)
                    action = next(a for a in menu.actions() if a.text() == menu.tr(source))
                    assert action.isEnabled()
                    action.trigger()
                    app.processEvents()
                    assert shape.get_start_end_points(True) == original_start
                    if live:
                        assert scene.routearrows and tuple(scene.routearrows) != routes
                    else:
                        assert tuple(scene.routearrows) == routes
                    assert [(layer.nr, list(layer.exp_order_complete)) for layer in window.layerContents] == order
                    window.updateExportRoute()
                    assert scene.routearrows and scene.routetext
        return

    for live in (False, True):
        window.ui.actionLiveUpdateExportRoute.setChecked(live)
        assert window.TreeHandler.auto_update_export_order == live
        for source in ("Set Nearest StartPoint", "Set Sharpest StartPoint"):
            for visible in ((False, True) if not live else (True,)):
                window.deleteG0Paths()
                if visible:
                    window.updateExportRoute()
                previous_routes = tuple(scene.routearrows)
                previous_preview = shape.stmove
                old_start = shape.get_start_end_points(True)
                clicked = shape.geos[len(shape.geos) // 2].Ps
                with patch.object(QMenu, "exec", return_value=None):
                    menu = MyDropDownMenu(scene, QPoint(), clicked)
                assert menu.selectedItems == [shape]
                action = next(action for action in menu.actions()
                              if action.text() == menu.tr(source))
                action.trigger()
                app.processEvents()
                assert shape.stmove is not previous_preview
                if source == "Set Nearest StartPoint":
                    assert shape.get_start_end_points(True) != old_start
                if live:
                    assert scene.routearrows and tuple(scene.routearrows) != previous_routes
                else:
                    assert tuple(scene.routearrows) == previous_routes, (source, visible)
                    assert bool(scene.routetext) == visible
                    assert window.ui.actionDeleteG0Paths.isEnabled() == visible
                assert [(layer.nr, list(layer.exp_order_complete))
                        for layer in window.layerContents] == order
                # Explicitly requesting the route must still work afterwards.
                window.updateExportRoute()
                assert scene.routearrows and scene.routetext
                assert window.ui.actionDeleteG0Paths.isEnabled()


def _run_mainwindow_workflow():
    import traceback
    def exception_hook(kind, value, trace):
        traceback.print_exception(kind, value, trace)
        sys.stderr.flush()
        os._exit(1)
    sys.excepthook = exception_hook
    """Worker entry point; run separately so a Qt crash cannot kill unittest."""
    from types import SimpleNamespace
    fold_worker = "--fold-worker" in sys.argv
    startpoint_worker = "--startpoint-worker" in sys.argv
    translation_worker = "--translation-worker" in sys.argv
    profile_worker = '--profile-default-worker' in sys.argv
    restart_worker = '--restart-worker' in sys.argv
    live_config_worker = '--live-config-worker' in sys.argv
    zero_worker = '--zero-worker' in sys.argv
    if fold_worker:
        import faulthandler
        faulthandler.dump_traceback_later(4, repeat=True)

    sys.path.insert(0, os.path.join(_REPO_DIR, "source"))
    import dxf2gcode.bootstrap.runtime_state as g
    from dxf2gcode.adapters.config.runtime_config import MyConfig

    temp_dir = os.environ["D2G_WORKFLOW_TEMP"]
    g.folder = os.path.join(temp_dir, "config")
    os.makedirs(g.folder, exist_ok=True)
    g.config = MyConfig()
    g.config.mode3d = False
    g.quiet = True

    from dxf2gcode.presentation.qt.qt_compat.QtWidgets import QApplication
    from dxf2gcode.presentation.qt.qt_compat import QtCore
    from dxf2gcode.presentation.qt.qt_compat import PYQT_VERSION
    if PYQT_VERSION == 5:
        from dxf2gcode.presentation.qt.generated.dxf2gcode_ui5 import Ui_MainWindow
    else:
        from dxf2gcode.presentation.qt.generated.dxf2gcode_ui6 import Ui_MainWindow
    from dxf2gcode.presentation.qt.canvas2d import MyGraphicsScene, ShapeGUI

    from dxf2gcode.presentation.qt import application as app_module
    g.folder = os.path.join(temp_dir, "config")
    app_module.Ui_MainWindow = Ui_MainWindow
    app_module.MyGraphicsScene = MyGraphicsScene
    app_module.Shape = ShapeGUI

    QtCore.QSettings.setDefaultFormat(QtCore.QSettings.Format.IniFormat)
    QtCore.QSettings.setPath(QtCore.QSettings.Format.IniFormat,
                             QtCore.QSettings.Scope.UserScope, temp_dir)
    app = QApplication([])
    window = app_module.MainWindow(app)
    g.window = window
    if '--pocket-worker' in sys.argv:
        from unittest.mock import patch
        fields = window.config_window.cfg_window_def
        fields['Cutter_Compensation']['done_by_machine'].setValue(False)
        window.config_window.applyChanges()
        window.filename = os.path.join(_REPO_DIR,
            'docs/assets/examples/first-dxf/rectangle-20x10-mm.dxf')
        assert window.load()
        window.shapes[0].parentLayer.tool_diameter = 1
        window.shapes[0].Pocket = True
        window.d2g.small_reload()
        assert window.shapes[0].toolpath_plan is not None
        with patch.object(app_module.QMessageBox, 'warning') as warning, \
                patch.object(app_module.QMessageBox, 'critical') as critical:
            window.ui.actionLathe.trigger()
            assert window.shapes[0].Pocket
            assert window.shapes[0].toolpath_plan is None
            assert warning.call_count == 1
            window.ui.actionMilling.trigger()
            assert window.shapes[0].Pocket
            assert window.shapes[0].toolpath_plan is not None
            assert warning.call_count == 1
            fields['Cutter_Compensation']['done_by_machine'].setValue(True)
            window.config_window.applyChanges()
            assert window.shapes[0].Pocket
            assert window.shapes[0].toolpath_plan is None
            assert warning.call_count == 2
            fields['Cutter_Compensation']['done_by_machine'].setValue(False)
            window.config_window.applyChanges()
            assert window.shapes[0].toolpath_plan is not None
            assert warning.call_count == 2
            app.processEvents()
            critical.assert_not_called()
        window.close()
        return
    if zero_worker:
        from unittest.mock import patch
        from math import hypot
        from dxf2gcode.presentation.qt.canvas import MyDropDownMenu
        from dxf2gcode.presentation.qt.project_session import Project
        from dxf2gcode.adapters.project.legacy_d2g import decode_d2g
        from dxf2gcode_stmove_gcode_test import make_plan_service, make_postpro
        window.filename = os.path.join(_REPO_DIR, 'dxf', 'drag_knive_test.dxf')
        assert window.load()
        window.cont_dx, window.cont_dy = 7, -11
        window.cont_scale, window.cont_rotate = 1.3, .4
        window.cont_mirrorx = True
        window.d2g.small_reload()
        def vertices():
            return [geo.get_start_end_points(True) for shape in window.shapes
                    for geo in shape.geos.abs_iter()]
        for metric in (1, 0):
            window.setMeasurementUnits(metric)
            assert window.ui.toolDiameterUnitLabel.text() == ('[mm]' if metric else '[in]')
            assert window.ui.unitLabel_1.text() == ('[mm]' if metric else '[in]')
            clicked = vertices()[0]
            expected = [window.cont_dx-clicked.x, window.cont_dy-clicked.y]
            with patch.object(MyDropDownMenu, 'exec'):
                menu = MyDropDownMenu(window.canvas_scene, QtCore.QPoint(), clicked)
            assert not menu.selectedItems
            action = menu.actions()[0]
            assert action.isEnabled()
            before = Project(window).export(compleet=False)
            with patch.object(app_module, 'PopUpDialog', return_value=SimpleNamespace(result=None)) as dialog:
                action.trigger()
                assert dialog.call_args.args[2] == expected
                assert dialog.call_args.kwargs['decimals'] == (3 if metric else 5)
                assert ('[mm]' if metric else '[in]') in dialog.call_args.args[1][0]
                assert Project(window).export(compleet=False) == before
            with patch.object(app_module, 'PopUpDialog', return_value=SimpleNamespace(result=[str(v) for v in expected])):
                action.trigger()
            assert (window.cont_dx, window.cont_dy) == tuple(expected)
            assert any(hypot(p.x, p.y) < 1e-7 for p in vertices())
            assert not window.canvas_scene.routearrows
            shape = window.shapes[0]
            exported = make_plan_service().execute_result(shape, make_postpro())
            assert not exported.has_errors
            assert exported.plan == window.canvas_scene.graphics_items[id(shape)].stmove_item.plan
            # At the origin, repeating the same action must not accumulate drift.
            zero = min(vertices(), key=lambda p: hypot(p.x, p.y))
            with patch.object(MyDropDownMenu, 'exec'):
                menu = MyDropDownMenu(window.canvas_scene, QtCore.QPoint(), zero)
            with patch.object(app_module, 'PopUpDialog', return_value=SimpleNamespace(result=None)) as dialog:
                menu.actions()[0].trigger()
                assert all(abs(a-b) < 1e-7 for a,b in zip(dialog.call_args.args[2], expected))
            # Edited offsets are honored, and the normal menu still uses them.
            edited = [expected[0]+1, expected[1]+2]
            with patch.object(app_module, 'PopUpDialog', return_value=SimpleNamespace(result=[str(v) for v in edited])):
                menu.actions()[0].trigger()
            assert (window.cont_dx, window.cont_dy) == tuple(edited)
            with patch.object(app_module, 'PopUpDialog', return_value=SimpleNamespace(result=None)) as dialog:
                window.ui.actionMoveWorkpieceZero.trigger()
                assert dialog.call_args.args[2] == edited
            content = Project(window).export(compleet=False)
            values = decode_d2g(content).values
            assert [values['wpzero_x'], values['wpzero_y']] == edited
            Project(window).load(content)
            assert (window.cont_dx, window.cont_dy) == tuple(edited)
        shape = window.shapes[0]
        shape.setSelected(True)
        with patch.object(MyDropDownMenu, 'exec'):
            menu = MyDropDownMenu(window.canvas_scene, QtCore.QPoint(), shape.get_start_end_points(True))
        assert menu.selectedItems
        assert menu.actions()[0].text() == menu.tr('Move workpiece zero here ...')
        assert menu.actions()[0].isEnabled()
        for closed in (True, False):
            shape.closed = closed
            if not closed:
                from dxf2gcode.domain.geometry.collections import Geos
                shape.geos = Geos(shape.geos[:-1])
            candidates = shape.start_point_candidates()
            assert len(candidates) == (len(shape.geos) if closed else 2)
            before_order = tuple(shape.geos)
            before_offset = (window.cont_dx, window.cont_dy)
            near = candidates[0] + app_module.Point(.0001, .0001)
            def inspect_snap(*args, **kwargs):
                snap = kwargs['snap']
                assert callable(snap)
                assert snap(args[2]) == [window.cont_dx-candidates[0].x, window.cont_dy-candidates[0].y]
                # Snapping uses the current dialog offsets, not only the
                # original click, and never changes the contour start.
                other = [window.cont_dx-candidates[-1].x, window.cont_dy-candidates[-1].y]
                assert snap(other) == other
                assert tuple(shape.geos) == before_order
                return SimpleNamespace(result=None)
            with patch.object(app_module, 'PopUpDialog', side_effect=inspect_snap):
                window.moveWorkpieceZero(point=near)
            assert before_offset == (window.cont_dx, window.cont_dy)
            assert tuple(shape.geos) == before_order
        window.shapes[1].setSelected(True)
        with patch.object(app_module, 'PopUpDialog', return_value=SimpleNamespace(result=None)) as dialog:
            window.moveWorkpieceZero()
            assert dialog.call_args.kwargs['snap'] is None
        window.close()
        return
    if live_config_worker:
        from unittest.mock import patch
        window.filename = os.path.join(_REPO_DIR, 'dxf', 'drag_knive_test.dxf')
        assert window.load()
        window.shapes[0].axis3_mill_depth = -.37
        form = window.config_window
        fields = form.cfg_window_def
        with patch.object(app_module.QMessageBox, 'information') as info, \
                patch.object(QtCore.QProcess, 'startDetached') as launch, \
                patch.object(window.d2g, 'small_reload', wraps=window.d2g.small_reload) as small, \
                patch.object(window.d2g, 'reload', wraps=window.d2g.reload) as full:
            form.show()
            fields['General']['machine_type'].setValue('drag_knife')
            form.applyChanges()
            assert g.config.machine_type == 'drag_knife'
            assert window.ui.actionDragKnife.isChecked()
            assert not window.ui.knifeSwivelLineEdit.isHidden()
            assert abs(window.shapes[0].axis3_mill_depth + .37) < 1e-9
            assert small.call_count == 1
            assert full.call_args.args == (False,)
            assert info.call_count == launch.call_count == 0
            assert not window._restart_pending
            form.applyChanges()
            assert small.call_count == full.call_count == 1
            # A combined mode/tolerance change only requires one full reload.
            fields['General']['machine_type'].setValue('milling')
            fields['Import_Parameters']['point_tolerance'].setValue(.002)
            fields['Import_Parameters']['fitting_tolerance'].setValue(.003)
            form.applyChanges()
            assert g.config.machine_type == 'milling'
            assert window.ui.actionMilling.isChecked()
            assert window.ui.knifeSwivelLineEdit.isHidden()
            assert g.config.point_tolerance == .002
            assert g.config.fitting_tolerance == .003
            assert abs(window.shapes[0].axis3_mill_depth + .37) < 1e-9
            assert small.call_count == 1
            assert full.call_count == 2
            assert full.call_args.args == ()
            # An unrelated saved setting must not reset a mode or tolerance
            # selected for the current drawing through the Options menu.
            window.ui.actionDragKnife.trigger()
            g.config.point_tolerance = .004
            previous = full.call_count
            fields['General']['show_scale_bar'].setValue(not fields['General']['show_scale_bar'].getValue())
            form.applyChanges()
            assert g.config.machine_type == 'drag_knife'
            assert g.config.point_tolerance == .004
            assert full.call_count == previous
            form.close()
            app.processEvents()
            assert info.call_count == launch.call_count == 0
        window.close()
        return
    if restart_worker:
        from unittest.mock import patch
        from pathlib import Path
        form = window.config_window
        fields = form.cfg_window_def
        window.show()
        window.filename = 'drawing-that-must-not-reopen.dxf'
        with patch.object(app_module.QMessageBox, 'information') as info, \
                patch.object(app_module.QMessageBox, 'critical') as error, \
                patch.object(QtCore.QProcess, 'startDetached', return_value=(False, 0)) as launch:
            form.show()
            fields['General']['mode3d'].setValue(True)
            form.applyChanges()
            assert window._restart_pending
            assert g.config.mode3d is False
            assert info.call_count == 1
            assert 'empty window' in info.call_args.args[2]
            assert launch.call_count == 0
            # Applying unchanged values does not repeat the same notice.
            form.applyChanges()
            assert info.call_count == 1
            assert launch.call_count == 0
            form.close()
            app.processEvents()
            assert launch.call_count == 1
            assert error.call_count == 1
            assert window.isVisible()
            assert not window._restart_scheduled
            program, arguments, cwd = launch.call_args.args
            assert 'drawing-that-must-not-reopen.dxf' not in arguments
            assert not any(arg in ('--quiet', '--export', '-q', '-e', '-o') for arg in arguments)
            assert Path(arguments[0]).name == 'dxf2gcode.py'
            # Reverting saved restart changes cancels the pending restart.
            form.show()
            fields['General']['mode3d'].setValue(False)
            form.applyChanges()
            assert not window._restart_pending
            form.close()
            app.processEvents()
            assert launch.call_count == 1
            # Live settings and discarded edits never request a restart.
            form.show()
            fields['General']['show_scale_bar'].setValue(not fields['General']['show_scale_bar'].getValue())
            form.applyChanges()
            assert info.call_count == 1
            for units in ('in', 'mm'):
                fields['General']['tool_units'].setValue(units)
                form.applyChanges()
                assert g.config.tool_units == units
                assert info.call_count == 1
                assert not window._restart_pending
            fields['General']['mode3d'].setValue(True)
            form.discardChanges()
            form.close()
            app.processEvents()
            assert launch.call_count == 1
            form.show()
            fields['General']['mode3d'].setValue(True)
            fields['Logging']['console_loglevel'].setValue('DEBUG')
            form.applyChanges()
            assert info.call_count == 2
            notice = info.call_args.args[2]
            assert all(name in notice for name in ('3D display', 'Logging'))
            assert g.config.mode3d is False
            assert launch.call_count == 1
            # Packaged applications relaunch their executable, retain the
            # profile and only close the current process after launch succeeds.
            launch.return_value = (True, 1234)
            with patch.object(sys, 'frozen', True, create=True), \
                    patch.object(app_module, 'active_config_profile_suffix', return_value='knife'), \
                    patch.object(window, 'close') as close, patch.object(app, 'quit') as quit_app:
                form.close()
                app.processEvents()
                assert launch.call_count == 2
                assert launch.call_args.args[0] == sys.executable
                assert launch.call_args.args[1] == ['--cfg', 'knife']
                assert close.call_count == quit_app.call_count == 1
        window._restart_pending = False
        window.close()
        return
    if profile_worker:
        from unittest.mock import patch
        from pathlib import Path
        defaults=dict(show_disabled_paths=True,live_update_export_route=False,
                      split_line_segments=False,automatic_cutter_compensation=False,
                      machine_type='milling')
        actions=dict(show_disabled_paths=window.ui.actionShowDisabledPaths,
                     live_update_export_route=window.ui.actionLiveUpdateExportRoute,
                     split_line_segments=window.ui.actionSplitLineSegments,
                     automatic_cutter_compensation=window.ui.actionAutomaticCutterCompensation)
        for key,action in actions.items():
            assert action.isChecked() is defaults[key],key
        assert window.ui.actionMilling.isChecked()
        individual={key:(not value if isinstance(value,bool) else 'lathe') for key,value in defaults.items()}
        g.config.var_dict['General'].update(individual)
        g.config.update_config()
        g.config.save_varspace()
        original=g.config
        file_before=Path(original.filename).read_bytes()
        old_folder=g.folder
        fresh_folder=os.path.join(temp_dir,'fresh-profile')
        with patch.object(app_module,'config_profile_folder',return_value=fresh_folder):
            assert window.initializeConfigProfile('fresh')
        assert g.folder==old_folder and g.config is original
        assert Path(original.filename).read_bytes()==file_before
        with patch.object(g,'folder',fresh_folder):
            fresh=MyConfig()
            for key,value in defaults.items():
                assert fresh.var_dict['General'][key]==value,key
        g.config=MyConfig()
        window.connectToolbarToConfig(block_signals=True)
        for key,action in actions.items():
            assert action.isChecked() is individual[key],key
        assert g.config.machine_type=='lathe' and window.ui.actionLathe.isChecked()
        window.config_window.setValuesFromConfig(window.config_window.cfg_window_def,
                                                g.config.var_dict,g.config.var_dict.configspec)
        for key,value in individual.items():
            assert window.config_window.cfg_window_def['General'][key].getValue()==value,key
        window.close()
        return
    assert window.windowTitle() == "Dxf2gcode"
    required_icon_sizes = {16, 20, 24, 28, 32, 36, 40, 48, 56, 64, 72, 80, 96, 128, 256}
    for widget in (window, window.config_window):
        assert required_icon_sizes.issubset(
            {size.width() for size in widget.windowIcon().availableSizes()})
    if translation_worker:
        from unittest.mock import patch
        for language, labels in (
            ("de", ("&Fräsen", "&Drehmaschine", "&Schleppmesser")),
            ("fr", ("&Fraisage", "&Tour", "&Couteau traînant")),
            ("ru", ("&Фрезерная", "&Токарная", "&Флюгерный нож")),
        ):
            translator = QtCore.QTranslator()
            assert translator.load(os.path.join(
                _REPO_DIR, "source", "i18n", "dxf2gcode_" + language + ".qm"))
            app.installTranslator(translator)
            window.ui.retranslateUi(window)
            with patch.object(window.d2g, "small_reload"):
                for action, value, label in zip(
                    (window.ui.actionMilling, window.ui.actionLathe, window.ui.actionDragKnife),
                    ("milling", "lathe", "drag_knife"), labels,
                ):
                    assert action.text() == label, (language, action.text())
                    action.trigger()
                    app.processEvents()
                    assert g.config.machine_type == value
            app.removeTranslator(translator)
        window.close()
        return
    assert window.config_window.cfg_window_def["General"][
        "expand_layers_on_load"].getValue() is True
    window.settings = QtCore.QSettings(
        QtCore.QSettings.Format.IniFormat,
        QtCore.QSettings.Scope.UserScope,
        "dxf2gcode-test", "mainwindow-workflow")

    def assert_empty_machining_dropdowns():
        for name in ("toolDiameterComboBox", "leadInComboBox",
                     "leadOutComboBox", "overcutComboBox"):
            combo = getattr(window.ui, name)
            assert combo.count() > 0, name + " has lost its choices"
            assert combo.currentIndex() == -1, name + " has an unexpected selection"
            assert combo.currentText() == "", name + " is not empty"

    assert_empty_machining_dropdowns()
    for name in ("layersCollapsePushButton", "layersExpandPushButton",
                 "blocksCollapsePushButton", "blocksExpandPushButton"):
        assert not getattr(window.ui, name).isEnabled(), name
    window.TreeHandler.updateConfiguration()
    assert_empty_machining_dropdowns()

    from unittest.mock import patch
    from dxf2gcode import __version__
    with patch.object(app_module, "AboutDialog") as dialog:
        window.about()
        message = dialog.call_args.kwargs["message"]
        assert __version__ in message
        assert "Version:" in message
        assert "Runtime:" in message
        assert "Package version:" not in message
        assert "$Date" not in message and "$Revision" not in message

    fixture = os.path.join(_REPO_DIR, "dxf", "Frontplatte_Texte_aufgebrochen.dxf"
                           if fold_worker else "1997.DXF" if startpoint_worker else "test.dxf")
    if fold_worker:
        window.show()
        app.processEvents()
    window.filename = fixture
    assert window.load() is True
    assert len(window.shapes) > 0
    assert window.canvas.scene() is window.canvas_scene
    assert len(window.canvas_scene.items()) > len(window.shapes)
    assert_empty_machining_dropdowns()

    if startpoint_worker:
        _check_startpoint_route_display(window, app)
        window.close()
        return

    if fold_worker:
        from importlib import import_module
        QTest = import_module("PyQt%d.QtTest" % PYQT_VERSION).QTest
        for tab, view, collapse, expand in (
                (1, window.ui.layersShapesTreeView, window.ui.layersCollapsePushButton,
                 window.ui.layersExpandPushButton),
                (0, window.ui.entitiesTreeView, window.ui.blocksCollapsePushButton,
                 window.ui.blocksExpandPushButton)):
            window.ui.mytabWidget.setCurrentWidget(window.geometry_panel)
            view.expandAll()
            app.processEvents()
            for row in range(view.model().rowCount()):
                index = view.model().index(row, 0)
                if not view.model().hasChildren(index):
                    continue
                for button in (expand, collapse):
                    view.setCurrentIndex(view.model().index(0, 0, index))
                    view.scrollTo(index)
                    app.processEvents()
                    rect = view.visualRect(index)
                    branch = QtCore.QPoint(
                        rect.left() - view.indentation() // 2, rect.center().y())
                    QTest.mouseClick(view.viewport(), QtCore.Qt.MouseButton.LeftButton,
                                     pos=branch)
                    app.processEvents()
                    assert not view.isExpanded(index), (tab, row)
                    print("Click fold button", tab, row, button.objectName(), flush=True)
                    QTest.mouseClick(button, QtCore.Qt.MouseButton.LeftButton)
                    app.processEvents()
                    view.expandAll()
                    app.processEvents()
        window.close()
        faulthandler.cancel_dump_traceback_later()
        return

    # Both actual toolbars follow their own tree, including the Entities root.
    for view, collapse, expand in (
            (window.ui.layersShapesTreeView, window.ui.layersCollapsePushButton,
             window.ui.layersExpandPushButton),
            (window.ui.entitiesTreeView, window.ui.blocksCollapsePushButton,
             window.ui.blocksExpandPushButton)):
        view.expandAll()
        assert collapse.isEnabled() and not expand.isEnabled()
        collapse.click()
        assert not collapse.isEnabled() and expand.isEnabled()
        assert not view.isExpanded(view.model().index(0, 0))
        expand.click()
        assert collapse.isEnabled() and not expand.isEnabled()

    shape = window.shapes[0]
    assert shape.stmove is not None
    index = window.TreeHandler.findLayerItemIndexFromShape(shape)
    assert index.isValid()
    selection = window.ui.layersShapesTreeView.selectionModel()
    selection.select(
        index,
        QtCore.QItemSelectionModel.SelectionFlag.Select |
        QtCore.QItemSelectionModel.SelectionFlag.Rows)
    assert shape.isSelected()
    panel = window.machining_panel
    from dxf2gcode.presentation.qt.machining_panel import ROLE
    assert panel.isAncestorOf(window.ui.millSettingsFrame)
    item = next(panel.tree.topLevelItem(i).child(j)
                for i in range(panel.tree.topLevelItemCount())
                for j in range(panel.tree.topLevelItem(i).childCount())
                if panel.tree.topLevelItem(i).child(j).data(0, ROLE) == ('entry', shape.operation_id))
    panel.tree.clearSelection()
    panel.tree.setCurrentItem(item)
    entry_id = shape.operation_id
    for expected_disabled in (True, False):
        panel.execute(lambda: panel.commands.update_entries([entry_id], enabled=not expected_disabled))
        assert shape.isDisabled() == expected_disabled
    for optimize in (True, False):
        panel.execute(lambda: panel.commands.update_entries([entry_id], optimize=optimize))
        assert shape.send_to_TSP == optimize

    previous_preview = shape.stmove
    new_offset = 0.25
    window.ui.millingOffsetLineEdit.setText(str(new_offset))
    window.ui.millingOffsetLineEdit.setModified(True)
    window.ui.millingOffsetLineEdit.editingFinished.emit()
    app.processEvents()
    assert abs(shape.milling_offset - new_offset) < 1e-9
    assert shape.stmove is not None
    assert shape.stmove is not previous_preview
    assert window.canvas_scene.shapes[shape.nr] is shape

    output_base = os.path.join(temp_dir, "mainwindow-workflow")
    output_format = "%s (*%s)" % (
        window.MyPostProcessor.output_text[0],
        window.MyPostProcessor.output_format[0])
    app_module.options = SimpleNamespace(post_pro=output_format)
    # A manual tree edit is authoritative even with route live update off.
    window.TreeHandler.setLiveUpdateExportRoute(False)
    for row in range(panel.tree.topLevelItemCount()):
        step_item = panel.tree.topLevelItem(row)
        if step_item.childCount() > 1:
            panel.tree.clearSelection()
            panel.tree.setCurrentItem(step_item.child(0))
            panel.nudge(1)
            break
    else:
        raise AssertionError("workflow fixture needs two shapes in one layer")
    window.TreeHandler.updateExportOrder()
    expected_sequence = [layer.shapes[index].nr
                         for layer in panel.binding.materialize().non_break_layer_iter()
                         for index in layer.exp_order_complete]
    startpoints = [shape.get_start_end_points() for shape in window.shapes]
    window.updateExportRoute()
    window.exportShapes(None, output_base)
    output = output_base + window.MyPostProcessor.output_format[0]
    assert os.path.isfile(output), "MainWindow.exportShapes did not create output"
    with open(output, "r", encoding="utf-8", errors="replace") as stream:
        gcode = stream.read()
    assert "G21" in gcode
    assert "G1 X" in gcode
    assert "M2" in gcode
    import re
    assert [int(nr) for nr in re.findall(r"SHAPE Nr: (\d+)", gcode)] == expected_sequence
    assert [shape.get_start_end_points() for shape in window.shapes] == startpoints

    machining_values = (shape.lead_in_mode, shape.lead_out_mode,
                        shape.overcut_enabled, shape.tool_override)
    selection.clearSelection()
    window.TreeHandler.updateToolParameters()
    assert_empty_machining_dropdowns()
    assert (shape.lead_in_mode, shape.lead_out_mode,
            shape.overcut_enabled, shape.tool_override) == machining_values

    # The configured load preference applies only to the layer tree and
    # never changes machining values or the layer/shape order.
    entities_view = window.ui.entitiesTreeView
    entities_view.expandAll()
    entities_root = entities_view.model().index(0, 0)
    order = [(layer.nr, [item.nr for item in layer.shapes])
             for layer in window.layerContents]
    layer_view = window.ui.layersShapesTreeView
    for expand_on_load in (False, True):
        g.config.vars.General.expand_layers_on_load = expand_on_load
        window.TreeHandler.buildLayerTree(window.layerContents)
        for row in range(layer_view.model().rowCount()):
            layer_index = layer_view.model().index(row, 0)
            if layer_view.model().hasChildren(layer_index):
                assert layer_view.isExpanded(layer_index) == expand_on_load
        assert window.ui.layersCollapsePushButton.isEnabled() == expand_on_load
        assert window.ui.layersExpandPushButton.isEnabled() != expand_on_load
        assert entities_view.isExpanded(entities_root)
        assert [(layer.nr, [item.nr for item in layer.shapes])
                for layer in window.layerContents] == order
        assert (shape.lead_in_mode, shape.lead_out_mode,
                shape.overcut_enabled, shape.tool_override) == machining_values

    from pathlib import Path
    from dxf2gcode_import_filters_test import write_layer_filter_fixture

    filtered_fixture = write_layer_filter_fixture(Path(temp_dir) / "filter-layers.dxf")
    for ignore, zero, names in (
            (False, False, {"0", "IGNORE:guide", "Cut"}),
            (True, False, {"0", "Cut"}),
            (False, True, {"IGNORE:guide", "Cut"}),
            (True, True, {"Cut"})):
        g.config.vars.Import_Parameters.exclude_ignore_layers = ignore
        g.config.vars.Import_Parameters.exclude_layer_zero = zero
        window.filename = filtered_fixture.as_posix()
        assert window.load() is True
        assert {layer.name for layer in window.layerContents} == names
        assert len(window.shapes) == len(names)
        assert len(window.canvas_scene.shapes) == len(names)
        assert window.ui.layersShapesTreeView.model().rowCount() == len(names)
        assert [item.nr for item in window.shapes] == list(range(len(names)))

    filtered_fixture.write_text(
        filtered_fixture.read_text().replace("Cut", "IGNORE:cut"), encoding="ascii")
    assert window.load() is True
    assert not window.shapes and not window.layerContents
    for name in ("layersCollapsePushButton", "layersExpandPushButton",
                 "blocksCollapsePushButton", "blocksExpandPushButton"):
        assert not getattr(window.ui, name).isEnabled(), name

    window.close()
    app.processEvents()


if __name__ == "__main__" and "--worker" in sys.argv:
    _run_mainwindow_workflow()
elif __name__ == "__main__":
    unittest.main()
