"""Exercise the installed application's machining/project workflow, without source imports.

Run from a fresh wheel environment with --fixture rectangle-with-tab-mm.dxf.
All profiles, Qt settings, projects and output are temporary. No machine is used.
"""
import argparse
import importlib.metadata
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fixture', required=True, type=Path)
    args = parser.parse_args()
    fixture = args.fixture.resolve()
    import dxf2gcode
    import sys
    assert Path(sys.prefix) in Path(dxf2gcode.__file__).resolve().parents
    with tempfile.TemporaryDirectory(prefix='d2g-installed-machining-') as temporary:
        folder = Path(temporary)
        # Set these before constructing configuration or importing the Qt runtime.
        os.environ.update(HOME=temporary, USERPROFILE=temporary,
                          APPDATA=temporary, LOCALAPPDATA=temporary)
        import dxf2gcode.bootstrap.runtime_state as g
        from dxf2gcode.adapters.config.runtime_config import MyConfig
        g.folder = str(folder / 'config')
        Path(g.folder).mkdir()
        g.config = MyConfig()
        g.config.mode3d = False
        g.quiet = True
        g.config.var_dict['Tool_Parameters']['2'] = dict(
            g.config.var_dict['Tool_Parameters']['1'], diameter=1.)
        g.config.update_config()
        from dxf2gcode.presentation.qt.qt_compat import QtCore, PYQT_VERSION
        from dxf2gcode.presentation.qt.qt_compat.QtWidgets import QApplication
        from dxf2gcode.presentation.qt import application as runtime
        from dxf2gcode.presentation.qt.canvas2d import MyGraphicsScene, ShapeGUI
        if PYQT_VERSION == 5:
            from dxf2gcode.presentation.qt.generated.dxf2gcode_ui5 import Ui_MainWindow
        else:
            from dxf2gcode.presentation.qt.generated.dxf2gcode_ui6 import Ui_MainWindow
        runtime.Ui_MainWindow = Ui_MainWindow
        runtime.MyGraphicsScene = MyGraphicsScene
        runtime.Shape = ShapeGUI
        g.folder = str(folder / 'config')
        QtCore.QSettings.setDefaultFormat(QtCore.QSettings.Format.IniFormat)
        QtCore.QSettings.setPath(QtCore.QSettings.Format.IniFormat,
                                QtCore.QSettings.Scope.UserScope, temporary)
        app = QApplication([])
        window = runtime.MainWindow(app)
        window.settings = QtCore.QSettings(str(folder / 'window.ini'),
                                          QtCore.QSettings.Format.IniFormat)
        g.window = window
        runtime.options = SimpleNamespace(post_pro=window.MyPostProcessor.output_text[0])
        drawing = folder / fixture.name
        drawing.write_bytes(fixture.read_bytes())
        window.filename = str(drawing)
        assert window.load()
        panel = window.machining_panel
        assert window.ui.mytabWidget.currentWidget() is panel
        step = panel.binding.project.steps[0]
        entry = step.entries[0].id
        panel.select_canvas_operation(entry)
        assert panel.execute(lambda: panel.commands.update_entries(
            [entry], dict(axis3_mill_depth=-1.5, cut_cor=40,
                          lead_in_mode='off', lead_out_mode='off')))
        tool = panel.profile_tool(2, g.config.vars.Tool_Parameters['2'])
        assert panel.execute(lambda: panel.commands.create_step('Finish', 'contour', tool))
        target = panel.binding.project.steps[-1]
        assert panel.execute(lambda: panel.commands.transfer([entry], target.id, copy=True))
        regions = panel.modifiers.records()
        assert len(regions) == 1
        region_id = next(iter(regions))
        assert panel.execute(lambda: panel.commands.update_region(region_id, name='Acceptance tab'))
        before = panel.binding.project.to_dict()
        project = folder / 'acceptance.d2g'
        project.write_text(window.d2g.export_current(), encoding='utf-8')
        window.loadProject(str(project))
        assert window.machining_panel.binding.project.to_dict() == before
        assert region_id in window.machining_panel.modifiers.records()
        output = folder / 'acceptance.ngc'
        assert window.exportShapes(saveas=str(output))
        program = output.read_text(encoding='utf-8')
        assert program.count('* SHAPE Nr:') == 2, program
        assert '-1.500' in program and '-1.000' in program
        window.close()
        app.processEvents()
        print('Installed machining workflow passed:',
              importlib.metadata.version('dxf2gcode'), 'Qt', PYQT_VERSION)


if __name__ == '__main__':
    main()
