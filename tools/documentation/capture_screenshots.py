"""Capture the user guide's screenshots from the current Qt application."""

import argparse
import os
from pathlib import Path
import shutil
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = ROOT / 'docs/assets/examples'


def capture(output, spatial):
    sys.path.insert(0, str(ROOT / 'source'))
    os.environ['DXF2GCODE_QT'] = '6'
    if not spatial:
        os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    os.environ.setdefault('QT_SCALE_FACTOR', '1')

    from PyQt6.QtCore import QEvent, QLocale, QPoint, QPointF, QRectF, QSettings, Qt
    from PyQt6.QtGui import QMouseEvent
    from PyQt6.QtTest import QTest
    from PyQt6.QtWidgets import QApplication, QComboBox, QDialog, QListWidget
    import dxf2gcode.bootstrap.runtime_state as runtime
    from dxf2gcode.adapters.config.runtime_config import MyConfig
    from dxf2gcode.application.tab_regions import world_vertices
    from dxf2gcode.domain.project.tool_settings import ToolSettings
    from dxf2gcode.presentation.qt import application
    from dxf2gcode.presentation.qt.configwindow import ConfigWindow
    from dxf2gcode.presentation.qt.generated.dxf2gcode_ui6 import Ui_MainWindow

    QLocale.setDefault(QLocale('en_US'))
    app = QApplication([])
    with tempfile.TemporaryDirectory(prefix='dxf2gcode-screenshots-') as folder:
        temporary = Path(folder)
        images = temporary / 'images'
        runtime.folder = str(temporary / 'config')
        runtime.config = config = MyConfig()
        runtime.quiet = True
        config.var_dict['General']['use_vispy'] = False
        config.var_dict['Cutter_Compensation']['done_by_machine'] = False
        config.var_dict['Tool_Parameters']['2'] = dict(
            config.var_dict['Tool_Parameters']['1'], diameter=1., speed=8000.)
        config.update_config()
        settings = QSettings(str(temporary / 'window.ini'), QSettings.Format.IniFormat)
        application.Ui_MainWindow = Ui_MainWindow
        with patch.object(application.QtCore, 'QSettings', return_value=settings):
            window = runtime.window = application.MainWindow(app)
        application.options = SimpleNamespace(post_pro=window.MyPostProcessor.output_text[0])
        window.showNormal()
        window.resize(1460, 1060)
        panel = window.machining_panel

        def settle():
            app.processEvents()
            QTest.qWait(35)
            app.processEvents()

        def layout():
            window.ui.splitter.setSizes([580, 880])
            window.ui.messageSplitter.setSizes([920, 70])
            panel.splitter.setSizes([255, 650])
            settle()

        def save(widget, relative, *, fit=True):
            settle()
            if fit and widget is window and window.view_comparison.renderer is None:
                bounds = window.canvas_scene.BB
                rect = QRectF(bounds.Ps.x, -bounds.Pe.y,
                              bounds.Pe.x - bounds.Ps.x, bounds.Pe.y - bounds.Ps.y)
                window.canvas.fitInView(rect.adjusted(-3, -3, 3, 3),
                                        Qt.AspectRatioMode.KeepAspectRatio)
                settle()
            path = images / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            if not widget.grab().save(str(path)):
                raise RuntimeError(f'Could not save {path}')
            print(relative, flush=True)

        def load(path):
            window.cont_dx = window.cont_dy = window.cont_rotate = 0
            window.cont_scale = 1
            window.cont_mirrorx = window.cont_mirrory = False
            window.filename = str(path)
            previous = panel.binding
            window.ui.messageBox.clear()
            if not window.load() or panel.binding is None or panel.binding is previous:
                raise RuntimeError(f'Could not open {path}')
            # Use the drawing name in the caption for portable screenshots.
            window.setWindowTitle(f'Dxf2gcode - [{path.name}]')
            window.ui.mytabWidget.setCurrentWidget(panel)
            layout()
            return panel.binding.project.steps[0].entries[0].id

        def configure(entry, **values):
            parameters = dict(axis3_start_mill_depth=0., axis3_slice_depth=-.5,
                              axis3_mill_depth=-1., f_g1_plane=200., f_g1_depth=100.,
                              milling_offset=0., cut_cor=40, lead_in_mode='off',
                              lead_out_mode='off', overcut_enabled=False)
            parameters.update(values)
            panel.execute(lambda: panel.commands.update_entries([entry], parameters))
            panel.select_canvas_operation(entry)

        def assignment(dialog):
            dialog.show()
            save(dialog, 'machining/assign-existing.png')
            target = dialog.findChild(QComboBox, 'assignmentTargetType')
            target.setCurrentIndex(target.findData('new'))
            save(dialog, 'machining/assign-new.png')
            dialog.close()
            return QDialog.DialogCode.Rejected

        def region_settings(dialog):
            dialog.show()
            save(dialog, 'machining/tab-dialog.png')
            dialog.close()
            return QDialog.DialogCode.Rejected

        rectangle = EXAMPLES / 'first-dxf/rectangle-20x10-mm.dxf'
        entry = load(rectangle)
        save(window, 'first-dxf/01-import.png')
        configure(entry)
        save(window, 'first-dxf/02-parameters.png')
        save(panel.parameter_editor.frame, 'machining/parameter-groups.png')

        original = load(EXAMPLES / 'machining-basics/three-shapes-mm.dxf')
        save(window, 'machining-basics/three-shapes.png')
        first = panel.binding.project.steps[0]
        configure(original)
        panel.execute(lambda: panel.commands.edit_step(first.id, 'Roughing', 'contour', first.tool_id))
        tool = ToolSettings.from_profile(2, config.vars.Tool_Parameters['2'])
        panel.execute(lambda: panel.commands.create_step('Finishing', 'contour', tool))
        finishing = panel.binding.project.steps[-1]
        panel.execute(lambda: panel.commands.transfer([original], finishing.id, copy=True))
        copied = panel.binding.project.steps[-1].entries[0].id
        panel.execute(lambda: panel.commands.update_entries([copied], dict(cut_cor=41)))
        panel.select_canvas_operation(copied)
        panel.tree.expandAll()
        save(window, 'machining/operations.png')
        with patch.object(QDialog, 'exec', new=assignment):
            panel.assignment_dialog([original], [])

        entry = load(rectangle)
        configure(entry, cut_cor=41, lead_in_mode='radius', lead_out_mode='radius',
                  lead_radius=2., lead_length=3., overcut_enabled=True, overcut_length=1.)
        save(window, 'machining-basics/software-compensation-leads.png')

        entry = load(EXAMPLES / 'tabs/rectangle-with-tab-mm.dxf')
        tabs = panel.modifiers
        region = next(iter(tabs.records()))
        panel.execute(lambda: panel.commands.update_region(region, name='Tab 1'))
        window.ui.mytabWidget.setCurrentWidget(window.geometry_panel)
        window.ui.entitiesTreeView.expandAll()
        window.ui.layersShapesTreeView.expandAll()
        save(window, 'machining/geometry-regions.png')
        window.ui.mytabWidget.setCurrentWidget(panel)
        panel.select_canvas_operation(entry)
        panel.buttons['tabs'].trigger()
        tabs.select(region, operation=entry)
        panel.tree.expandAll()
        layout()
        save(window, 'machining/tab-selected.png')
        viewport = window.canvas.viewport()
        corner = world_vertices(panel.binding, tabs.records()[region])[0]
        start = tabs.projection(corner).toPoint()
        end = start + QPoint(25, 0)
        QTest.mousePress(viewport, Qt.MouseButton.LeftButton, pos=start)
        event = QMouseEvent(QEvent.Type.MouseMove, QPointF(end), QPointF(viewport.mapToGlobal(end)),
                            Qt.MouseButton.NoButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
        app.sendEvent(viewport, event)
        if tabs.gesture is None or tabs.dimension_labels():
            raise RuntimeError('Expected a tab drag without dimension fields')
        save(window, 'machining/tab-drag.png', fit=False)
        QTest.keyClick(viewport, Qt.Key.Key_Escape)
        QTest.mouseRelease(viewport, Qt.MouseButton.LeftButton, pos=end)
        tabs.select(region, operation=entry)
        with patch.object(QDialog, 'exec', new=region_settings):
            tabs.edit_assignment()
        tabs.set_mode(False)

        load(EXAMPLES / 'ignored-layers/ignore-layers-mm.dxf')
        panel.tree.expandAll()
        save(window, 'machining/ignore-unassigned.png')

        defaults = MyConfig()
        dialog = ConfigWindow(defaults.makeConfigWidgets(), defaults.var_dict,
                              defaults.var_dict.configspec, parent=window)
        dialog.resize(1100, 880)
        dialog.show()
        selector = dialog.findChild(QListWidget)
        for label, image in (('General settings', 'settings/general-settings.png'),
                             ('Parameter names', 'settings/parameter-names.png'),
                             ('Tools table', 'machining/tools-table.png')):
            selector.setCurrentItem(selector.findItems(label, Qt.MatchFlag.MatchExactly)[0])
            save(dialog, image)
        dialog.close()

        if spatial:
            project = ROOT / 'dxf/1997.d2g'
            load(project)
            band = window.view_comparison
            band.start(True)
            if band.renderer is None:
                raise RuntimeError('The spatial screenshot requires VisPy and working OpenGL')
            panel.select_canvas_operation(panel.binding.project.steps[-1].entries[0].id)
            band.origin_axes_action.setChecked(True)
            band.retracts_action.setChecked(False)
            band.renderer.camera.elevation = 48
            band.renderer.camera.azimuth = 12
            band.fit()
            layout()
            if band.renderer.canvas.render()[..., :3].min() >= 150:
                raise RuntimeError('The spatial screenshot has a blank canvas')
            save(window, 'interface/1997-spatial.png')
        window.close()
        for path in images.rglob('*.png'):
            target = output / path.relative_to(images)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'docs/assets/images',
                        help='image directory (default: docs/assets/images)')
    parser.add_argument('--spatial', action='store_true',
                        help='also capture 1997.d2g in VisPy using a native display and OpenGL')
    args = parser.parse_args()
    capture(args.output, args.spatial)


if __name__ == '__main__':
    main()
