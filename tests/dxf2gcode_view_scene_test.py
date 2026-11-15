"""Renderer contract and real Qt fallback; native GPU exercise is explicit."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'source'))

from dxf2gcode.application.view_scene import ScenePath, ViewScene, hit_paths, preview_tool_bodies, tool_cylinder_mesh


class TestViewScene(unittest.TestCase):
    def test_test_tools_use_plan_radius_and_shared_closed_mesh(self):
        path = ScenePath('op', 'geo', 'operation', (((2, 3, -1), (5, 3, -1), 'cut'),),
                         plan=SimpleNamespace(tool_radius=2.))
        scene = ViewScene((path,))
        self.assertFalse(preview_tool_bodies(scene, set()))
        body, = preview_tool_bodies(scene, {'op'})
        self.assertEqual((body.position, body.radius, body.length), ((2, 3, -1), 2., 16.))
        from dataclasses import replace
        self.assertFalse(preview_tool_bodies(ViewScene((replace(path, enabled=False),)), {'op'}))
        vertices, normals, faces = tool_cylinder_mesh()
        self.assertEqual((len(vertices), len(normals), len(faces)), (194, 194, 192))
        self.assertTrue(all(0 <= i < len(vertices) for face in faces for i in face))
        self.assertEqual({v[2] for v in vertices}, {0., 1.})

    def test_quick_geometry_preserves_centerline_and_pixel_width(self):
        from dxf2gcode.presentation.qt.qt_compat import PYQT_VERSION
        if PYQT_VERSION != 6:
            self.skipTest('Qt Quick 3D prototype uses PyQt6')
        from array import array
        from PyQt6.QtGui import QQuaternion, QVector3D
        from PyQt6.QtWidgets import QApplication
        from dxf2gcode.presentation.qt.quick3d_view import LineGeometry, qt_point
        app = QApplication.instance() or QApplication([])
        self.assertIsNotNone(app)
        geometry = LineGeometry()
        rotation = QQuaternion.fromEulerAngles(-90, 0, 0)
        a, b = (0., 0., 0.), (10., 0., 0.)
        geometry.upload({((.1, .2, .3, 1.), 2.): [a, b]}, rotation, 2.)
        values = array('f')
        values.frombytes(geometry.vertexData().data())
        self.assertEqual(len(values), 6*7)
        p, q = QVector3D(*values[:3]), QVector3D(*values[7:10])
        self.assertLess(((p+q)/2-qt_point(a)).length(), 1e-5)
        self.assertAlmostEqual((p-q).length()*2., 2., places=5)

    def test_plane_deduplicates_depth_passes_and_preserves_3d(self):
        action = SimpleNamespace(kind='linear_xy', args=((0, 0), (10, 0)), role='cut')
        plan = SimpleNamespace(approach_xy=(0, 0), workpiece_top=0,
            compensation_space='nominal', actions=(
                SimpleNamespace(kind='linear_z', args=(-1,), role='plunge'), action,
                SimpleNamespace(kind='rapid_xy', args=((0, 0),), role='rapid'),
                SimpleNamespace(kind='linear_z', args=(-2,), role='plunge'), action))
        from dxf2gcode.application.toolpath.projections import plan_preview_segments
        segments = tuple((s.start, s.end, s.role) for s in plan_preview_segments(plan))
        path = ScenePath('op', 'geo', 'operation', segments, plan=plan)
        self.assertEqual(sum(s[2] == 'cut' for s in path.projected(False)), 1)
        self.assertEqual(sum(s[2] == 'cut' for s in path.projected(True)), 2)
        self.assertEqual({p[2] for a, b, _ in path.projected(False) for p in (a, b)}, {0})
        self.assertIn(-2, {p[2] for a, b, _ in path.projected(True) for p in (a, b)})

    def test_hits_keep_multiple_operation_ids_and_ignore_hidden_paths(self):
        line = (((0, 0, 0), (10, 0, 0), 'cut'),)
        scene = ViewScene((ScenePath('geo', 'geo', 'geometry', line),
                           ScenePath('a', 'geo', 'operation', line),
                           ScenePath('b', 'geo', 'operation', line),
                           ScenePath('off', 'geo', 'operation', line, enabled=False)))
        self.assertEqual(hit_paths(scene, (4, 1), lambda p: p[:2]), ('a', 'b'))
        self.assertEqual(hit_paths(scene, (4, 1), lambda p: p[:2], show_disabled=True), ('a', 'b', 'off'))
        self.assertFalse(hit_paths(scene, (4, 20), lambda p: p[:2]))

    def test_qt_missing_and_failed_renderer_preserve_canvas(self):
        result = subprocess.run([sys.executable, __file__, '--fallback-worker'],
            env=dict(os.environ, QT_QPA_PLATFORM='offscreen'), capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout.decode(errors='replace')+
                         result.stderr.decode(errors='replace'))

    def test_all_new_messages_are_translated(self):
        import ast
        import xml.etree.ElementTree as ET
        source = ROOT / 'source/dxf2gcode/presentation/qt/view_comparison.py'
        messages = {node.args[0].value for node in ast.walk(ast.parse(source.read_text(encoding='utf-8')))
                    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr == 'tr' and node.args and isinstance(node.args[0], ast.Constant)}
        for language in ('de', 'fr', 'ru'):
            contexts = ET.parse(ROOT / ('source/i18n/dxf2gcode_'+language+'.ts')).findall('context')
            context = next(c for c in contexts if c.findtext('name') == 'ViewComparison')
            entries = {m.findtext('source'): m.find('translation') for m in context.findall('message')}
            self.assertLessEqual(messages, entries.keys())
            for message in messages:
                self.assertTrue(entries[message].text)
                self.assertNotEqual(entries[message].get('type'), 'unfinished')
            from dxf2gcode.presentation.qt.qt_compat.QtCore import QTranslator
            translator = QTranslator()
            self.assertTrue(translator.load(str(ROOT / ('source/i18n/dxf2gcode_'+language+'.qm'))))
            for message in messages:
                self.assertEqual(translator.translate('ViewComparison', message), entries[message].text)


def worker(gpu=False, kind='vispy', interop=True, benchmark=False, tools_benchmark=False):
    import faulthandler
    faulthandler.dump_traceback_later(20, exit=True)
    from unittest.mock import patch
    import traceback
    def exception(kind, value, trace):
        traceback.print_exception(kind, value, trace)
        os._exit(1)
    sys.excepthook = exception
    from dxf2gcode.presentation.qt.qt_compat import QtCore, PYQT_VERSION
    from dxf2gcode.presentation.qt.qt_compat.QtWidgets import QApplication
    import dxf2gcode.bootstrap.runtime_state as g
    from dxf2gcode.adapters.config.runtime_config import MyConfig
    with tempfile.TemporaryDirectory() as folder:
        g.folder = str(Path(folder) / 'config')
        Path(g.folder).mkdir()
        g.config = MyConfig()
        g.config.mode3d, g.quiet = False, True
        from dxf2gcode.presentation.qt import application as module
        from dxf2gcode.presentation.qt.canvas2d import MyGraphicsScene
        if PYQT_VERSION == 6:
            from dxf2gcode.presentation.qt.generated.dxf2gcode_ui6 import Ui_MainWindow
        else:
            from dxf2gcode.presentation.qt.generated.dxf2gcode_ui5 import Ui_MainWindow
        module.Ui_MainWindow, module.MyGraphicsScene = Ui_MainWindow, MyGraphicsScene
        g.folder = str(Path(folder) / 'config')
        QtCore.QSettings.setDefaultFormat(QtCore.QSettings.Format.IniFormat)
        QtCore.QSettings.setPath(QtCore.QSettings.Format.IniFormat,
                                QtCore.QSettings.Scope.UserScope, folder)
        app = QApplication([])
        if gpu:
            window = module.MainWindow(app)
        else:
            with patch('dxf2gcode.presentation.qt.view_comparison.importlib.util.find_spec', return_value=None):
                window = module.MainWindow(app)
        g.window = window
        module.options = SimpleNamespace(post_pro=window.MyPostProcessor.output_text[0])
        window.filename = str(ROOT / 'dxf/BreakExample_Circle.dxf')
        assert window.load()
        band, panel = window.view_comparison, window.machining_panel
        if gpu:
            from copy import deepcopy
            from dataclasses import replace
            from dxf2gcode.domain.project.machining_project import new_id
            step = panel.binding.project.steps[0]
            duplicate = replace(deepcopy(step), id=new_id(), name='Finish', entries=[
                replace(deepcopy(step.entries[0]), id=new_id())])
            panel.binding.project.steps.append(duplicate)
            panel.refresh()
            panel.refresh_preview()
        before = panel.binding.project.to_dict()
        if gpu:
            plane_key = 'quickplane' if kind == 'quick3d' else 'plane'
            spatial_key = 'quickspatial' if kind == 'quick3d' else 'spatial'
            def capture(renderer):
                if kind == 'vispy':
                    return renderer.canvas.render()[..., :3].min() < 100
                from PyQt6.QtGui import QImage
                image = renderer.view.grabWindow().convertToFormat(QImage.Format.Format_RGBA8888)
                assert not image.isNull()
                pixels = image.bits().asstring(image.sizeInBytes())
                return min(pixels[0::4]+pixels[1::4]+pixels[2::4]) < 100
            assert band.actions['spatial'].isEnabled()
            band.actions[plane_key].trigger()
            app.processEvents()
            assert band.renderer is not None, band.actions[plane_key].toolTip()
            if kind == 'quick3d':
                if not band.renderer.verified:
                    loop = QtCore.QEventLoop()
                    band.renderer.view.frameSwapped.connect(loop.quit)
                    QtCore.QTimer.singleShot(1500, loop.quit)
                    band.renderer.view.update()
                    loop.exec()
                    band.renderer.view.frameSwapped.disconnect(loop.quit)
                assert band.renderer.verified, 'No native Qt Quick 3D frame'
            assert capture(band.renderer), 'Initial top view is blank'
            band.actions[spatial_key].trigger()
            app.processEvents()
            assert band.renderer is not None, band.actions['spatial'].toolTip()
            renderer = band.renderer
            assert any(p.kind == 'operation' and p.plan for p in band.snapshot.paths)
            assert any(p.kind == 'region' for p in band.snapshot.paths)
            snapshot = band.snapshot
            operations = [p for p in snapshot.paths if p.kind == 'operation']
            # Exercise a viewport hit, not only direct calls into tree selection.
            middle = tuple((a+b)/2 for a, b in zip(operations[0].segments[5][0], operations[0].segments[5][1]))
            position = renderer.project(middle)
            assert operations[0].identity in hit_paths(snapshot, position, renderer.project)
            if kind == 'quick3d':
                from dxf2gcode.presentation.qt.quick3d_view import qt_point
                mapped = QtCore.QMetaObject.invokeMethod(renderer.view.rootObject(), 'projectPoint',
                    QtCore.Q_RETURN_ARG('QVariant'), QtCore.Q_ARG('QVariant', qt_point(middle)))
                assert abs(mapped.x()-position[0]) < 1 and abs(mapped.y()-position[1]) < 1, (mapped, position)
                from PyQt6.QtTest import QTest
                from math import dist
                target = operations[1]
                a, b, _ = next(s for s in target.segments if s[2] == 'cut' and dist(s[0], s[1]) > 20)
                x, y = renderer.project(tuple((a+b)/2 for a, b in zip(a, b)))
                QTest.mouseClick(renderer.view, QtCore.Qt.MouseButton.LeftButton,
                                 QtCore.Qt.KeyboardModifier.NoModifier, QtCore.QPoint(round(x), round(y)))
                app.processEvents()
                assert target.identity in renderer.selected, 'QML click did not select the operation'
                yaw = renderer.state['yaw']
                renderer.mousePress(200., 200., 1, 0)
                renderer.mouseMove(240., 220.)
                renderer.mouseRelease(240., 220., 0)
                assert renderer.state['yaw'] != yaw
                zoom = renderer.zoom
                renderer.mouseWheel(120., 300., 300.)
                assert renderer.zoom > zoom
                renderer.redraw()
                from PyQt6.QtGui import QVector3D
                with patch.object(renderer._mesh, 'upload', wraps=renderer._mesh.upload) as upload:
                    renderer.state['center'] += QVector3D(.1, 0, 0)
                    renderer.redraw()
                    assert upload.call_count == 0, 'Panning uploaded unchanged geometry'
                    renderer.state['yaw'] += .1
                    renderer.redraw()
                    assert upload.call_count == 1, 'Rotation did not update camera-facing bands'
                # A continuous input stream must still produce scheduled draws.
                from PyQt6.QtTest import QSignalSpy
                pulse = QtCore.QTimer()
                pulse.setInterval(2)
                pulse.timeout.connect(renderer.schedule)
                draws = QSignalSpy(renderer.timer.timeout)
                loop = QtCore.QEventLoop()
                pulse.start()
                QtCore.QTimer.singleShot(80, loop.quit)
                loop.exec()
                pulse.stop()
                assert len(draws) > 0, 'Continuous input starved the redraw timer'
            if len(hit_paths(snapshot, position, renderer.project)) == 1:
                renderer.pick(QtCore.QPoint(round(position[0]), round(position[1])))
            panel.select_canvas_operation(operations[0].identity)
            assert band.snapshot is snapshot, 'Selection rebuilt the scene/plans'
            assert operations[0].identity in renderer.selected
            assert operations[0].geometry == operations[-1].geometry
            if len(operations) > 1:
                panel.select_canvas_operation(operations[1].identity, True)
                assert {p.identity for p in operations[:2]} <= renderer.selected
            # Editing a parameter invalidates data; pure selection did not.
            entry = panel.binding.project.steps[0].entries[0]
            original_overrides = dict(entry.overrides)
            entry.overrides['axis3_mill_depth'] = -4.2
            panel.refresh_preview()
            assert band.snapshot is not snapshot
            assert -4.2 in {p[2] for path in band.snapshot.paths if path.identity == entry.id
                            for a, b, _ in path.segments for p in (a, b)}
            entry.overrides = original_overrides
            panel.refresh_preview()
            app.processEvents()
            if kind == 'vispy':
                window.grab().save(str(ROOT / '.tox/view-prototype-spatial.png'))
            else:
                renderer.view.grabWindow().save(str(ROOT / '.tox/quick3d-prototype-spatial.png'))
            band.actions[plane_key].trigger()
            app.processEvents()
            renderer.verify()
            assert capture(renderer), 'Blank framebuffer'
            # Native rendering evidence lives outside tracked source files.
            if kind == 'vispy':
                window.grab().save(str(ROOT / '.tox/view-prototype.png'))
            else:
                renderer.view.grabWindow().save(str(ROOT / '.tox/quick3d-prototype.png'))
            band.actions['legacy'].trigger()
            assert band.stack.currentWidget() is window.canvas
            assert panel.binding.project.to_dict() == before
            print('Native GPU, snapshot reuse, multi-selection, tabs, top view and 2D return OK')
            if kind == 'vispy':
                from vispy import gloo
                print('OpenGL:', gloo.gl.glGetParameter(gloo.gl.GL_VERSION))
            else:
                print('Qt Quick 3D:', renderer.view.rendererInterface().graphicsApi())
            # A native Quick window must coexist with the other renderer without
            # forcing both engines onto the same graphics API.
            if interop:
                other = 'spatial' if kind == 'quick3d' else 'quickspatial'
                band.actions[other].trigger()
                app.processEvents()
                assert band.renderer is not None, band.actions[other].toolTip()
                assert band.snapshot is renderer.snapshot
                band.actions[spatial_key].trigger()
                app.processEvents()
                assert band.renderer is renderer
                assert capture(renderer)
            # Same static transparent cylinders in either renderer; no project edit.
            band.actions[spatial_key].trigger()
            app.processEvents()
            snapshot = band.snapshot
            project_values = panel.binding.project.to_dict()
            if kind == 'vispy':
                baseline_image = renderer.canvas.render()
                baseline_pixels = (baseline_image[..., :3] < 240).any(axis=2).sum()
            band.tools_action.setChecked(True)
            app.processEvents()
            expected = len(preview_tool_bodies(snapshot, renderer.selected))
            assert expected > 0
            if kind == 'quick3d':
                assert len(renderer.toolBodies) == expected
                renderer.view.grabWindow().save(str(ROOT / '.tox/quick3d-transparent-tools.png'))
            else:
                assert sum(node.visible for node in renderer.tool_nodes.values()) == expected
                from vispy import io
                tool_image = renderer.canvas.render()
                assert (tool_image[..., :3] < 240).any(axis=2).sum() > baseline_pixels*.75, 'Transparent pass lost contour lines'
                io.write_png(str(ROOT / '.tox/vispy-transparent-tools.png'), tool_image)
            assert band.snapshot is snapshot
            assert panel.binding.project.to_dict() == project_values
            band.tools_action.setChecked(False)
            app.processEvents()
            assert not renderer.toolBodies if kind == 'quick3d' else not any(n.visible for n in renderer.tool_nodes.values())
            if benchmark:
                from contextlib import ExitStack
                band.actions[spatial_key].trigger()
                app.processEvents()
                assert renderer.isVisible()
                from statistics import median
                from time import perf_counter
                from PyQt6.QtGui import QVector3D
                timings = {}
                update_timings = {}
                uploads = {}
                for action in ('pan', 'rotate', 'zoom'):
                    samples = []
                    update_samples = []
                    with ExitStack() as stack:
                        if kind == 'quick3d':
                            observers = [stack.enter_context(patch.object(renderer._mesh, 'upload', wraps=renderer._mesh.upload))]
                        else:
                            observers = [stack.enter_context(patch.object(node, 'set_data', wraps=node.set_data))
                                         for node in renderer.nodes.values()]
                        for index in range(12):
                            update_started = perf_counter()
                            if kind == 'quick3d':
                                if action == 'pan':
                                    renderer.state['center'] += QVector3D(.1, 0, 0)
                                elif action == 'rotate':
                                    renderer.state['yaw'] += .1
                                else:
                                    renderer.state['zoom'] *= 1.001
                            else:
                                if action == 'pan':
                                    x, y, z = renderer.camera.center
                                    renderer.camera.center = (x+.1, y, z)
                                elif action == 'rotate':
                                    renderer.camera.azimuth += .1
                                else:
                                    renderer.camera.scale_factor /= 1.001
                            started = perf_counter()
                            renderer.redraw()
                            samples.append((perf_counter()-started)*1000)
                            update_samples.append((perf_counter()-update_started)*1000)
                        uploads[action] = sum(observer.call_count for observer in observers)
                    timings[action] = round(median(samples), 3)
                    update_timings[action] = round(median(update_samples), 3)
                print('CPU redraw medians in ms (12 updates each):', timings)
                print('CPU update including camera mutation in ms:', update_timings)
                print('Geometry update calls:', uploads)
                if kind == 'quick3d':
                    assert uploads == dict(pan=0, rotate=12, zoom=12)
            if tools_benchmark:
                from statistics import median
                from time import perf_counter
                timings = {}
                for enabled in (False, True):
                    band.tools_action.setChecked(enabled)
                    app.processEvents()
                    samples = []
                    for index in range(7):
                        started = perf_counter()
                        if kind == 'quick3d':
                            renderer.state['yaw'] += .5
                        else:
                            renderer.camera.azimuth += .5
                        renderer.redraw()
                        if kind == 'quick3d':
                            image = renderer.view.grabWindow()
                            pixels = (image.width(), image.height())
                        else:
                            image = renderer.canvas.render()
                            pixels = (image.shape[1], image.shape[0])
                        if index:
                            samples.append((perf_counter()-started)*1000)
                    timings['on' if enabled else 'off'] = round(median(samples), 3)
                print('Rotating + render/readback median ms (6 samples, 1 warmup each):', timings,
                      'tools:', expected, 'pixels:', pixels)
                print('Readback APIs differ; use this as an on/off comparison, not FPS.')
        else:
            assert 'vispy' not in sys.modules
            assert not band.actions['spatial'].isEnabled()
            assert band.stack.currentWidget() is window.canvas
            with patch('dxf2gcode.presentation.qt.vispy_view.VispyView', side_effect=RuntimeError('test context failure')):
                band.activate('spatial')
            assert band.stack.currentWidget() is window.canvas
            assert panel.binding.project.to_dict() == before
            assert not band.actions['quickspatial'].isEnabled()
            if PYQT_VERSION == 6:
                band.actions['spatial'].setEnabled(True)
                with patch('dxf2gcode.presentation.qt.quick3d_view.Quick3DView', side_effect=RuntimeError('test QML failure')):
                    band.activate('quickspatial')
                assert band.actions['spatial'].isEnabled(), 'Quick failure disabled VisPy'
                assert not band.actions['quickspatial'].isEnabled()
                assert band.stack.currentWidget() is window.canvas
            print('Missing/failed renderer leaves 2D usable')
        window.close()
        app.processEvents()
        faulthandler.cancel_dump_traceback_later()


if __name__ == '__main__':
    if '--gpu-worker' in sys.argv:
        worker(True)
    elif '--quick-worker' in sys.argv:
        worker(True, 'quick3d')
    elif '--quick-only-worker' in sys.argv:
        worker(True, 'quick3d', False)
    elif '--quick-benchmark' in sys.argv:
        worker(True, 'quick3d', False, True)
    elif '--vispy-benchmark' in sys.argv:
        worker(True, 'vispy', False, True)
    elif '--quick-tools-benchmark' in sys.argv:
        worker(True, 'quick3d', False, False, True)
    elif '--vispy-tools-benchmark' in sys.argv:
        worker(True, 'vispy', False, False, True)
    elif '--fallback-worker' in sys.argv:
        worker()
    else:
        unittest.main()
