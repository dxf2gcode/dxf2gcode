"""Real Qt project save/load/reload through the existing MainWindow."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class TestMachiningProjectGUI(unittest.TestCase):
    def test_save_load_edit_export_and_reimport_preserve_machining_document(self):
        with tempfile.TemporaryDirectory() as folder:
            env = dict(os.environ, D2G_MACHINING_TEMP=folder, QT_QPA_PLATFORM='offscreen')
            result = subprocess.run([sys.executable, __file__, '--worker'], cwd=folder,
                                    env=env, capture_output=True, timeout=45)
            self.assertEqual(result.returncode, 0, result.stdout.decode(errors='replace') +
                             result.stderr.decode(errors='replace'))


def worker():
    import traceback
    def exception_hook(kind, value, trace):
        traceback.print_exception(kind, value, trace)
        sys.stderr.flush()
        os._exit(1)
    sys.excepthook = exception_hook
    from copy import deepcopy
    from dataclasses import replace
    from unittest.mock import patch
    from types import SimpleNamespace
    sys.path.insert(0, str(ROOT / 'source'))
    import dxf2gcode.bootstrap.runtime_state as g
    from dxf2gcode.adapters.config.runtime_config import MyConfig
    folder = Path(os.environ['D2G_MACHINING_TEMP'])
    g.folder = str(folder / 'config')
    Path(g.folder).mkdir()
    g.config = MyConfig()
    g.config.mode3d = False
    g.quiet = True
    from dxf2gcode.presentation.qt.qt_compat import QtCore, PYQT_VERSION
    from dxf2gcode.presentation.qt.qt_compat.QtWidgets import QApplication
    from dxf2gcode.presentation.qt import application as app_module
    from dxf2gcode.presentation.qt.canvas2d import MyGraphicsScene, ShapeGUI
    if PYQT_VERSION == 5:
        from dxf2gcode.presentation.qt.generated.dxf2gcode_ui5 import Ui_MainWindow
    else:
        from dxf2gcode.presentation.qt.generated.dxf2gcode_ui6 import Ui_MainWindow
    app_module.Ui_MainWindow = Ui_MainWindow
    app_module.MyGraphicsScene = MyGraphicsScene
    app_module.Shape = ShapeGUI
    g.folder = str(folder / 'config')
    QtCore.QSettings.setDefaultFormat(QtCore.QSettings.Format.IniFormat)
    QtCore.QSettings.setPath(QtCore.QSettings.Format.IniFormat, QtCore.QSettings.Scope.UserScope, str(folder))
    app = QApplication([])
    window = app_module.MainWindow(app)
    # Explicit file settings keep persistence tests out of the Windows registry.
    window.settings = QtCore.QSettings(str(folder / 'window.ini'), QtCore.QSettings.Format.IniFormat)
    app_module.options = SimpleNamespace(post_pro=window.MyPostProcessor.output_text[0])
    g.window = window
    from dxf2gcode.adapters.project.machining_d2g import decode_project
    from dxf2gcode.domain.project.machining_project import new_id
    with patch.object(app_module.QMessageBox, 'critical') as critical, \
            patch.object(app_module.QMessageBox, 'warning') as warning:
        path = folder / 'source.dxf'
        original = (ROOT / 'docs/assets/examples/first-dxf/rectangle-20x10-mm.dxf').read_text()
        path.write_text(original)
        window.filename = str(path)
        assert window.load()
        project_path = folder / 'new.d2g'
        project_path.write_text(window.d2g.export_current(), encoding='utf-8')
        document = decode_project(project_path.read_text(encoding='utf-8'))
        step_id = document.machining.steps[0].id
        operation_id = document.machining.steps[0].entries[0].id
        window.loadProject(str(project_path))
        assert window.d2g.machining_drawing is not None
        window.shapes[0].axis3_mill_depth = -4
        output = folder / 'part.ngc'
        assert window.exportShapes(saveas=str(output))
        assert output.is_file()
        assert window.d2g.machining_drawing.project.steps[0].entries[0].overrides['axis3_mill_depth'] == -4
        binding = window.d2g.machining_drawing
        step = binding.project.steps[0]
        second = replace(deepcopy(step.entries[0]), id=new_id(),
                         overrides=dict(step.entries[0].overrides, axis3_mill_depth=-6))
        binding.project.steps.append(replace(deepcopy(step), id=new_id(), name='Finish', entries=[second]))
        project_path.write_text(window.d2g.export_current(), encoding='utf-8')
        assert window.exportShapes(saveas=str(output))
        cli_output = folder / 'cli.ngc'
        cli = subprocess.run([sys.executable, str(ROOT / 'source/dxf2gcode.py'), '--cfg', 'r3',
                              '--quiet', '--export', str(cli_output), str(project_path)],
                             env=dict(os.environ, HOME=str(folder), USERPROFILE=str(folder)),
                             cwd=folder, capture_output=True, timeout=30)
        assert cli.returncode == 0, cli.stderr.decode(errors='replace')
        def program(path):
            return [line for line in path.read_text().splitlines() if line and not line.startswith('(')]
        assert program(output) == program(cli_output)
        assert output.read_text().count('* SHAPE Nr:') == 2, output.read_text()
        saved_diameter = window.shapes[0].tool_override.tool_diameter
        table_diameter = g.config.vars.Tool_Parameters['1']['diameter']
        g.config.var_dict['Tool_Parameters']['1']['diameter'] = 999
        window.TreeHandler.updateConfiguration()
        assert window.shapes[0].tool_override.tool_diameter == saved_diameter
        existing_program = output.read_bytes()
        assert not window.exportShapes(saveas=str(output))
        assert output.read_bytes() == existing_program
        assert warning.called and 'T1' in warning.call_args.args[2]
        warning.reset_mock()
        g.config.var_dict['Tool_Parameters']['1']['diameter'] = table_diameter
        g.config.update_config()
        assert window.exportShapes(saveas=str(output))
        window.cont_dx = 7
        window.d2g.small_reload()
        assert window.d2g.machining_drawing.project.steps[0].id == step_id
        assert window.d2g.machining_drawing.project.steps[0].entries[0].id == operation_id
        assert not window.d2g.machining_drawing.project.unresolved
        extra = '0\nLINE\n8\nTutorial\n10\n100\n20\n100\n11\n110\n21\n100\n'
        path.write_text(original.replace('0\nENDSEC\n0\nEOF', extra + '0\nENDSEC\n0\nEOF'))
        window.reload()
        binding = window.d2g.machining_drawing
        assert binding.project.steps[0].entries[0].id == operation_id
        assert len(binding.unassigned) == 1
        assert binding.unassigned[0].toolpath_plan is None
        assert sum(len(layer.shapes) for layer in binding.materialize()) == 2
        assert binding.project.steps[0].entries[0].overrides['axis3_mill_depth'] == -4
        window.filename = str(path)
        assert window.load()
        assert window.d2g.machining_drawing is not binding
        if os.environ.get('D2G_TEST_MACHINING_PANEL'):
            from dxf2gcode_machining_panel_test import exercise_panel
            exercise_panel(window, app, folder)
        app.processEvents()
        critical.assert_not_called()
        warning.assert_not_called()
    window.close()


if __name__ == '__main__':
    if '--worker' in sys.argv:
        worker()
    else:
        unittest.main()
