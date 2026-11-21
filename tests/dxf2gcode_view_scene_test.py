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
    def test_vispy_original_colour_and_full_vs_partial_selection(self):
        from unittest.mock import patch
        import dxf2gcode.bootstrap.runtime_state as g
        with patch.object(g, 'config', g.config or SimpleNamespace(mode3d=False)):
            from dxf2gcode.presentation.qt.canvas2d import ShapeGUI
        from dxf2gcode.presentation.qt.vispy_view import vispy_path_pen
        from dxf2gcode.presentation.qt.machining_preview import MachiningPreview
        from dxf2gcode.presentation.qt.qt_compat import QtCore
        preview = SimpleNamespace(view=SimpleNamespace(viewportTransform=True))
        source = SimpleNamespace(cut_cor=42, isSelected=lambda: False, isDisabled=lambda: False)
        panel = SimpleNamespace(context='a', binding=SimpleNamespace(sources={'g': source}),
            canvas_preview=SimpleNamespace(path_pen=lambda *args: MachiningPreview.path_pen(preview, *args)))
        view = SimpleNamespace(panel=panel, selected=set(), geometry_selection={'g': (0, 2)})
        geometry = ScenePath('g', 'g', 'geometry', ())
        a, b = (ScenePath(name, 'g', 'operation', ()) for name in ('a', 'b'))
        for correction in (40, 41, 42):
            source.cut_cor = correction
            pen = vispy_path_pen(view, geometry, 'geometry')
            self.assertEqual((pen.color().name(), pen.widthF()), ('#000000', 1.))
        view.selected, view.geometry_selection = {'a', 'b'}, {'g': (2, 2)}
        pen = vispy_path_pen(view, geometry, 'geometry')
        self.assertEqual((pen.color().name(), pen.widthF()), ('#ff0000', 3.))
        for operation in (a, b):
            pen = vispy_path_pen(view, operation, 'cut')
            self.assertEqual(pen.widthF(), .6)
            self.assertEqual(pen.style(), QtCore.Qt.PenStyle.SolidLine)
        view.selected, view.geometry_selection = {'a'}, {'g': (1, 2)}
        source.isSelected = lambda: True
        original = vispy_path_pen(view, geometry, 'geometry')
        self.assertEqual((original.widthF(), original.style()), (1., QtCore.Qt.PenStyle.DotLine))
        self.assertEqual(vispy_path_pen(view, a, 'cut').widthF(), 3.)
        other = vispy_path_pen(view, b, 'cut')
        self.assertEqual((other.widthF(), other.style()), (.6, QtCore.Qt.PenStyle.DashLine))
        view.geometry_selection = {'g': (1, 1)}
        self.assertEqual(vispy_path_pen(view, a, 'cut').widthF(), .6)

    def test_connected_line_chains_keep_corners_and_gaps(self):
        from dxf2gcode.presentation.qt.vispy_view import connected_chains
        a, b, c, d = (0, 0, 0), (1, 0, 0), (1, 1, 0), (3, 3, 0)
        self.assertEqual(list(connected_chains(((a, b), (b, c), (c, a), (d, c)))),
                         [[a, b, c, a], [d, c]])
        self.assertEqual(list(connected_chains(((a, a), (d, c)))), [[d, c]])

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


def verify_vispy_plane_stacking(app, renderer):
    """Coincident paths stay ordered even after cached styles change selection."""
    import numpy as np
    from dxf2gcode.presentation.qt.qt_compat.QtGui import QColor, QPen
    line = (((0., 0., 0.), (10., 0., 0.), 'cut'),)
    paths = (ScenePath('selected', 'geo', 'operation', line),
             ScenePath('geo', 'geo', 'geometry', line),
             ScenePath('other', 'geo', 'operation', line))
    original_style = renderer.path_style
    # Distinct test colours make a wrong draw order visible in the framebuffer.
    renderer.path_style = lambda path, role: QPen(QColor(
        'blue' if path.kind == 'operation' and path.identity in renderer.selected else
        'lime' if path.kind == 'operation' else 'red'), 3.)
    try:
        for spatial in (False, True, False):
            renderer.set_spatial(spatial)
            for selected in ('selected', 'other'):
                renderer.set_scene(ViewScene(paths), {selected})
                if spatial:
                    assert all(key[0] == 0 for key, node in renderer.nodes.items() if node.visible)
                    continue
                renderer.camera.rect = (-2., -5., 14., 10.)
                app.processEvents()
                renderer.redraw()
                assert {key[0] for key, node in renderer.nodes.items() if node.visible} == {0, 1, 2}
                assert all(key[2] == 3. and node.method == 'gl' for key, node in renderer.nodes.items() if node.visible)
                frame = renderer.canvas.render()
                x, y = renderer.project((5., 0., 0.))
                x = round(x*frame.shape[1]/renderer.viewport().width())
                y = round(y*frame.shape[0]/renderer.viewport().height())
                pixels = frame[max(0, y-1):y+2, max(0, x-1):x+2, :3].astype(float)
                assert np.min(np.linalg.norm(pixels-(0., 0., 255.), axis=2)) < 10, 'Selected path is covered'
        # Reordering the snapshot must not change the stacking contract.
        renderer.set_scene(ViewScene(tuple(reversed(paths))), {'selected'})
        assert all(node.order == key[0] for key, node in renderer.nodes.items() if node.visible)
    finally:
        renderer.path_style = original_style
    # The actual semantic palette: an unselected circle stays black, while a
    # selected right-angle contour has a joined blue corner.
    from math import cos, sin, pi
    circle = [(15.+5*cos(i*2*pi/180), 5*sin(i*2*pi/180), 0.) for i in range(180)]
    circle.append(circle[0])
    circle_segments = tuple((a, b, 'cut') for a, b in zip(circle, circle[1:]))
    rectangle = ((0., -5., 0.), (0., 5., 0.), (5., 5., 0.), (5., -5., 0.), (0., -5., 0.))
    rect_segments = tuple((a, b, 'cut') for a, b in zip(rectangle, rectangle[1:]))
    renderer.set_scene(ViewScene((ScenePath('circle', 'circle', 'geometry', circle_segments),
        ScenePath('circle-op', 'circle', 'operation', circle_segments),
        ScenePath('rect', 'rect', 'geometry', rect_segments),
        ScenePath('rect-op', 'rect', 'operation', rect_segments))), {'rect-op'})
    renderer.camera.rect = (-3., -7., 26., 14.)
    app.processEvents()
    frame = renderer.canvas.render()
    def location(point):
        x, y = renderer.project(point)
        return (round(x*frame.shape[1]/renderer.viewport().width()),
                round(y*frame.shape[0]/renderer.viewport().height()))
    left, top = location((9., 6., 0.))
    right, bottom = location((21., -6., 0.))
    pixels = frame[top:bottom+1, left:right+1, :3].astype(int)
    assert not np.any(pixels[..., 2]-pixels[..., 0] > 15), 'Unselected circle shows blue fragments'
    selected_nodes = [node for key, node in renderer.nodes.items() if node.visible and key[0] == 2]
    assert selected_nodes and all(node.method == 'gl' and node.connect == 'segments' for node in selected_nodes)
    assert all(node.width == .6 for node in selected_nodes)
    assert any(node.width == 1. and key[1][:3] == (0., 0., 0.)
               for key, node in renderer.nodes.items() if node.visible and key[0] == 1)
    renderer.grab().save(str(ROOT / '.tox/vispy-line-joins.png'))


def verify_vispy_selection_cache(window):
    from unittest.mock import patch
    from PyQt6.QtCore import QPoint
    panel, band = window.machining_panel, window.view_comparison
    original = window.TreeHandler.auto_update_export_order
    window.TreeHandler.auto_update_export_order = False
    try:
        band.activate('plane')
        snapshot = band.snapshot
        operation = next(p for p in snapshot.paths if p.kind == 'operation')
        with patch.object(panel.canvas_preview, 'refresh', wraps=panel.canvas_preview.refresh) as legacy:
            with patch.object(panel.binding, 'materialize', wraps=panel.binding.materialize) as materialize:
                panel.select_canvas_operation(operation.identity)
                assert materialize.call_count == legacy.call_count == 0, 'Selection rebuilt the hidden legacy preview'
            assert band.snapshot is snapshot and operation.identity in band.renderer.selected
            assert band.legacy_stale
            with patch.object(panel, 'selection_changed', wraps=panel.selection_changed) as changed:
                band.renderer.pick(QPoint(-10000, -10000))
                assert changed.call_count == 1
                assert not panel.selected_entries() and panel.context is None
                assert legacy.call_count == 0
            panel.select_canvas_operation(operation.identity)
            band.activate('legacy')
            assert legacy.call_count == 1 and not band.legacy_stale
            assert operation.identity in panel.canvas_preview.selected
        band.activate('plane')
    finally:
        window.TreeHandler.auto_update_export_order = original
    print('VisPy selection cache: hidden legacy preview deferred and refreshed on return passed')


def verify_vispy_caches(app, renderer):
    from contextlib import ExitStack
    from unittest.mock import patch
    from dxf2gcode.presentation.qt import vispy_view
    from PyQt6 import QtCore, QtTest
    a, b = (0., 0., 0.), (10., 0., 0.)
    scene = ViewScene((ScenePath('g', 'g', 'geometry', ((a, b, 'geometry'),)),
        ScenePath('a', 'g', 'operation', (((0., 1., 0.), (10., 1., 0.), 'cut'),
                                       ((-2., 1., 0.), (0., 1., 0.), 'lead_in'))),
        ScenePath('b', 'g', 'operation', (((0., 2., 0.), (10., 2., 0.), 'cut'),))))
    renderer.set_scene(scene, {'a'})
    app.processEvents()
    renderer.canvas.render()
    with ExitStack() as stack:
        projection = stack.enter_context(patch.object(ScenePath, 'projected', autospec=True, side_effect=ScenePath.projected))
        dash = stack.enter_context(patch.object(vispy_view, 'dash_segments', wraps=vispy_view.dash_segments))
        uploads = [stack.enter_context(patch.object(node, 'set_data', wraps=node.set_data)) for node in renderer.nodes.values()]
        x, y = renderer.camera.rect.pos
        w, h = renderer.camera.rect.size
        renderer.camera.rect = (x+.1, y, w, h)
        renderer.redraw()
        renderer.canvas.render()
        assert projection.call_count == dash.call_count == 0
        assert not any(upload.call_count for upload in uploads), 'Pan uploaded unchanged lines'
        renderer.set_scene(scene, {'a'})
        assert not any(upload.call_count for upload in uploads), 'Unchanged selection uploaded lines'
        renderer.camera.zoom(1.02)
        renderer.redraw()
        renderer.canvas.render()
        assert dash.call_count > 0 and projection.call_count == 0
        cut_color = renderer.panel.canvas_preview.path_pen('cut').color().getRgbF()
        assert not any(upload.call_count for key, upload in zip(renderer.nodes, uploads)
                       if key[1] == cut_color and key[0] == 2), 'Zoom uploaded unchanged solid cuts'
        renderer.set_scene(scene, {'b'})
        assert projection.call_count == 0, 'Selection recalculated plan projections'
    for index in range(12):
        renderer.set_scene(scene, {'a' if index % 2 else 'b'})
    assert len(renderer.nodes) < 12, 'Obsolete style nodes accumulated'
    assert all(node.method == 'gl' for node in renderer.nodes.values())
    replacement = ViewScene(scene.paths[:1])
    with patch.object(ScenePath, 'projected', autospec=True, side_effect=ScenePath.projected) as projection:
        renderer.set_scene(replacement, set())
        assert projection.call_count == 1
    assert len(renderer.nodes) == 1
    # A continuous mouse stream must not indefinitely postpone the redraw.
    renderer.canvas.render()
    app.processEvents()
    renderer.timer.stop()
    pulse = QtCore.QTimer()
    pulse.setInterval(2)
    pulse.timeout.connect(renderer.schedule)
    draws = QtTest.QSignalSpy(renderer.timer.timeout)
    loop = QtCore.QEventLoop()
    pulse.start()
    QtCore.QTimer.singleShot(150, loop.quit)
    loop.exec()
    pulse.stop()
    assert len(draws) > 0
    print('VisPy GL caches: pan without projection/dash/upload; zoom/selection invalidation and bounded nodes passed')


def verify_vispy_picking(app, renderer):
    from unittest.mock import patch
    from PyQt6.QtCore import QPoint
    line = (((0., 0., -2.), (10., 0., -2.), 'cut'),)
    scene = ViewScene((ScenePath('original', 'original', 'geometry', line),
        ScenePath('op-a', 'original', 'operation', line),
        ScenePath('op-b', 'original', 'operation', line),
        ScenePath('disabled', 'original', 'operation', line, enabled=False),
        ScenePath('region', '', 'region', (((4., -1., 0.), (4., 1., 0.), 'tab'),)),
        ScenePath('zero', 'zero', 'operation', (((3., 3., 0.), (3., 3., 0.), 'cut'),))))
    for spatial in (False, True, False):
        renderer.set_spatial(spatial)
        renderer.set_scene(scene, set())
        renderer.fit()
        app.processEvents()
        for moved in (False, True):
            if moved:
                if spatial:
                    renderer.camera.azimuth += 17
                else:
                    renderer.camera.zoom(1.13)
            positions = [QPoint(4, 4)] + [QPoint(*map(round, renderer.project(p)))
                for p in ((5., 0., -2.), (4., 0., 0.), (3., 3., 0.))]
            for disabled in (False, True):
                renderer.show_disabled = disabled
                for position in positions:
                    for kinds in (('operation', 'region'), ('geometry',)):
                        reference = hit_paths(scene, (position.x(), position.y()), renderer.project,
                            True, kinds=kinds, show_disabled=disabled)
                        with patch.object(renderer, 'project', side_effect=AssertionError('Per-point projection used')):
                            assert renderer.path_hits(position, kinds) == reference
        cached = renderer._hit_screen[spatial]
        renderer.path_hits(QPoint(10, 10))
        assert renderer._hit_screen[spatial] is cached
    renderer.set_scene(ViewScene(), set())
    assert not renderer.path_hits(QPoint(0, 0))
    assert not renderer._hit_screen
    print('VisPy picking: vectorized hits match reference, camera/scene/visibility invalidation passed')


def verify_vispy_top_transition(window):
    import numpy as np
    band = window.view_comparison
    band.actions['spatial'].trigger()
    renderer = band.renderer
    camera = renderer.spatial_camera
    camera.set_state(elevation=34., azimuth=120., roll=13., scale_factor=camera.scale_factor*.7,
                     center=tuple(camera.center))
    before = camera.get_state()
    band.actions['plane'].trigger()
    animation = renderer.top_transition
    assert renderer.spatial and renderer._top_start == before
    animation.setCurrentTime(animation.duration()//2)
    assert 34. < camera.elevation < 90. and camera.scale_factor != before['scale_factor']
    points = ((0., 0., 0.), (1., 0., -3.), (0., 1., -1.5))
    renderer._animate_top_frame(1.)
    end = [renderer.project(point) for point in points]
    animation.setCurrentTime(animation.duration())
    assert not renderer.spatial and renderer.camera is renderer.plane_camera
    np.testing.assert_allclose([renderer.project(point) for point in points], end, atol=.01)
    band.actions['spatial'].trigger()
    assert renderer.spatial and camera.get_state() == before, (renderer.spatial, camera.get_state(), before)
    band.actions['plane'].trigger()
    animation.setCurrentTime(animation.duration()//2)
    band.actions['spatial'].trigger()
    assert renderer._top_start is None and camera.get_state() == before
    print('VisPy top transition: orientation, zoom, seamless projection and cancel passed')


def verify_vispy_shared_depth_passes(renderer):
    import numpy as np
    from dxf2gcode.application.toolpath.projections import plan_preview_segments
    from dxf2gcode.presentation.qt.view_interaction import dash_segments
    cut = SimpleNamespace(kind='linear_xy', args=((0., 0.), (10., 0.)), role='cut')
    reverse_cut = SimpleNamespace(kind='linear_xy', args=cut.args[::-1], role='cut')
    plan = SimpleNamespace(approach_xy=(0., 0.), workpiece_top=0.,
        compensation_space='nominal', actions=(
            SimpleNamespace(kind='linear_z', args=(-1.5,), role='plunge'), cut,
            SimpleNamespace(kind='linear_z', args=(-3.,), role='plunge'), reverse_cut))
    segments = tuple((s.start, s.end, s.role) for s in plan_preview_segments(plan))
    path = ScenePath('depth-pass', 'depth-pass', 'operation', segments, plan=plan)
    renderer.set_spatial(False)
    renderer.set_scene(ViewScene((path,)), {path.identity})
    renderer.fit()
    drawing_data = renderer.projected_data()
    depths = {a[2] for a, _, role in renderer.projected_segments(path) if role == 'cut'}
    assert depths == {-1.5, -3.}
    assert any(a[:2] == b[:2] and a[2] != b[2] for a, b, _ in renderer.projected_segments(path))
    shallow = renderer.project((5., 0., -1.5))
    deep = renderer.project((5., 0., -3.))
    assert all(abs(a-b) < 1e-6 for a, b in zip(shallow, deep))
    renderer.canvas.render()
    renderer.set_scene(renderer.snapshot, set())
    cut_color = renderer.path_style(path, 'cut').color().getRgbF()
    for zoom in (0.8, 1.4):
        renderer.camera.zoom(zoom)
        renderer.redraw()
        unit = renderer.camera.rect.height / renderer.height()
        expected = dash_segments([((0., 0., 0.), (10., 0., 0.))], unit)
        node = next(node for key, node in renderer.nodes.items() if key[1] == cut_color)
        np.testing.assert_allclose(node.pos, np.asarray(expected, dtype=np.float32))
        renderer.canvas.render()
    renderer.set_spatial(True)
    assert renderer.projected_data() is drawing_data
    shallow = renderer.project((5., 0., -1.5))
    deep = renderer.project((5., 0., -3.))
    assert max(abs(a-b) for a, b in zip(shallow, deep)) > 1.
    for zoom in (0.83, 1.37):
        renderer.camera.scale_factor *= zoom
        renderer.redraw()
        node = next(node for key, node in renderer.nodes.items() if key[1] == cut_color)
        pairs = node.pos.reshape(-1, 2, 3)
        horizontal = pairs[pairs[:, 0, 2] == pairs[:, 1, 2]]
        shallow = horizontal[horizontal[:, 0, 2] == -1.5, :, :2]
        deep = horizontal[horizontal[:, 0, 2] == -3., :, :2]
        assert len(shallow) > 1
        np.testing.assert_allclose(shallow, deep)
        renderer.canvas.render()
    print('VisPy shared XYZ: both passes and plunges retained with fixed overhead and tilted views')


def verify_vispy_segment_gaps(app, renderer):
    import numpy as np
    def segments(points):
        return tuple((a, b, 'geometry') for a, b in zip(points, points[1:]))
    first = ((0., 0., 0.), (2., 0., 0.), (2., 2., 0.), (0., 2., 0.), (0., 0., 0.))
    second = tuple((x+5., y, z) for x, y, z in first)
    paths = (ScenePath('two-pieces', 'two-pieces', 'geometry', segments(first)+segments(second)),
        ScenePath('separate', 'separate', 'geometry', segments(((9., 0., 0.), (11., 0., 0.)))),
        ScenePath('dashed', 'offset', 'operation', (((0., 3., 0.), (11., 3., 0.), 'cut'),)))
    renderer.set_spatial(False)
    renderer.set_scene(ViewScene(paths), set())
    renderer.fit()
    app.processEvents()
    frame = renderer.canvas.render()
    assert len(renderer.nodes) == 2
    assert all(node.connect == 'segments' and node.method == 'gl' for node in renderer.nodes.values())
    for point in ((3.5, 0., 0.), (8., 0., 0.)):
        x, y = renderer.project(point)
        x = round(x*frame.shape[1]/renderer.viewport().width())
        y = round(y*frame.shape[0]/renderer.viewport().height())
        assert np.min(frame[y-1:y+2, x-1:x+2, :3]) > 245, 'Segments bridged independent pieces'
    print('VisPy segments: few batched visuals, separate pieces/contours and dash gaps passed')


def verify_vispy_selection_appearance(app, window, capture=False):
    from PyQt6.QtCore import QPoint, Qt
    panel, band = window.machining_panel, window.view_comparison
    band.activate('plane')
    groups = {}
    for path in band.snapshot.paths:
        if path.kind == 'operation':
            groups.setdefault(path.geometry, []).append(path.identity)
    geometry, identities = next((g, ids) for g, ids in groups.items() if len(ids) > 1)
    before = panel.binding.project.to_dict()
    for mode in ('plane', 'spatial'):
        band.activate(mode)
        renderer = band.renderer
        original = next(p for p in band.snapshot.paths if p.identity == geometry)
        paths = [p for p in band.snapshot.paths if p.identity in identities]
        for state in ('none', 'all', 'partial'):
            renderer.pick(QPoint(-10000, -10000))
            if state == 'all':
                for index, identity in enumerate(identities):
                    panel.select_canvas_operation(identity, bool(index))
            elif state == 'partial':
                panel.select_canvas_operation(identities[0])
            pen = renderer.path_style(original, 'geometry')
            assert pen.color().name() == ('#000000' if state == 'none' else '#ff0000')
            assert pen.widthF() == (3. if state == 'all' else 1.)
            for path in paths:
                pen = renderer.path_style(path, 'cut')
                thick = state == 'partial' and path.identity == identities[0]
                assert pen.widthF() == (3. if thick else .6)
                assert pen.style() == (Qt.PenStyle.SolidLine if state == 'all' or thick else Qt.PenStyle.DashLine)
            frame = renderer.canvas.render()
            assert frame[..., :3].min() < 150
            if capture:
                app.processEvents()
                renderer.grab().save(str(ROOT / ('.tox/vispy-1997-'+mode+'-'+state+'.png')))
        assert panel.binding.project.to_dict() == before
    print('VisPy selection appearance: none/all/partial, black originals, both views and unchanged project passed')


def tab_editing_worker(app, window):
    """Real Qt events and GPU projection, sharing production tab commands."""
    from unittest.mock import patch
    from PyQt6 import QtCore, QtGui, QtTest
    from dxf2gcode.application.tab_regions import world_vertices, to_drawing, rectangle_size
    panel, band = window.machining_panel, window.view_comparison
    band.actions['spatial'].trigger()
    app.processEvents()
    renderer, modifiers = band.renderer, panel.modifiers
    assert renderer is not None
    operation = next(p for p in band.snapshot.paths if p.kind == 'operation')
    # Put a manual rectangle across a real nominal contour, not a GPU-only item.
    source = panel.binding.sources[operation.geometry]
    from dxf2gcode.application.tab_regions import nominal_contour
    from dxf2gcode.domain.toolpath.tabs import point
    x, y = point(nominal_contour(source)[0], .5)
    region = modifiers.assignment_defaults()
    region.scope, region.targets, region.placement_mode = 'operations', [operation.identity], 'manual'
    vertices = ((x-3, y-3), (x+3-1e-10, y-3), (x+3-1e-10, y+3), (x-3, y+3))
    region.vertices = to_drawing(panel.binding, vertices)
    panel.execute(lambda: panel.commands.create_region(region))
    modifiers.set_mode(True)
    app.processEvents()
    assert not renderer.spatial and band.actions['plane'].isChecked()
    renderer.camera.rect = (x-12, y-12, 24, 24)
    app.processEvents()
    surface = renderer.viewport()
    def pixel(xy):
        return renderer.tab_project(xy).toPoint()
    for xy in vertices:
        actual = renderer.tab_scene_point(renderer.tab_project(xy))
        assert max(abs(a-b) for a, b in zip(actual, xy)) < 1e-6
    modifiers.clear_reference()
    QtTest.QTest.mouseClick(surface, QtCore.Qt.MouseButton.LeftButton, pos=pixel((x, y)))
    assert modifiers.context == region.id
    before = panel.binding.project.to_dict()
    count = len(panel.commands.undo_stack)
    start, end = pixel((x, y)), pixel((x+1, y+1))
    QtTest.QTest.mousePress(surface, QtCore.Qt.MouseButton.LeftButton, pos=start)
    QtTest.QTest.mouseMove(surface, end)
    assert modifiers.gesture['kind'] == 'move' and not modifiers.dimension_labels(renderer)
    QtTest.QTest.mouseRelease(surface, QtCore.Qt.MouseButton.LeftButton, pos=end)
    assert len(panel.commands.undo_stack) == count+1
    after = panel.binding.project.to_dict()
    assert after != before
    panel.undo(); assert panel.binding.project.to_dict() == before
    panel.redo(); assert panel.binding.project.to_dict() == after
    panel.undo()
    panel.execute(lambda: panel.commands.update_region(region.id, placement_mode='snap'))
    automatic = panel.binding.project.to_dict()
    modifiers.select(region.id)
    # Dimension field is hosted over the native GL canvas and keeps the centre.
    axis, rect, _, value = modifiers.dimension_labels(renderer)[0]
    QtTest.QTest.mouseClick(surface, QtCore.Qt.MouseButton.LeftButton, pos=rect.center().toPoint())
    editor = modifiers.dimension_editor
    assert editor is not None and editor.parent() is surface
    from dxf2gcode.presentation.qt.numeric_display import format_number
    assert editor.text() == format_number(value, panel.binding.project.units)
    count = len(panel.commands.undo_stack)
    QtTest.QTest.keyClick(editor, QtCore.Qt.Key.Key_Return)
    assert panel.binding.project.to_dict() == automatic
    assert len(panel.commands.undo_stack) == count, 'Unchanged formatted size rounded geometry'
    QtTest.QTest.mouseClick(surface, QtCore.Qt.MouseButton.LeftButton, pos=rect.center().toPoint())
    editor = modifiers.dimension_editor
    editor.setText(str(value+2))
    QtTest.QTest.keyClick(editor, QtCore.Qt.Key.Key_Return)
    changed = world_vertices(panel.binding, modifiers.records()[region.id])
    assert abs(rectangle_size(changed)[axis]-(value+2)) < 1e-6
    assert abs(sum(v[0] for v in changed)/4-x) < 1e-6
    assert abs(sum(v[1] for v in changed)/4-y) < 1e-6
    assert modifiers.records()[region.id].placement_mode == 'manual'
    panel.undo(); assert panel.binding.project.to_dict() == automatic
    panel.undo(); assert panel.binding.project.to_dict() == before
    modifiers.select(region.id)
    # Ctrl drag reaches the existing geometric snap and is one undo command.
    with patch.object(modifiers, 'snap_gesture', wraps=modifiers.snap_gesture) as snap:
        QtTest.QTest.mousePress(surface, QtCore.Qt.MouseButton.LeftButton, pos=start)
        event = QtGui.QMouseEvent(QtCore.QEvent.Type.MouseMove, QtCore.QPointF(end),
            QtCore.QPointF(surface.mapToGlobal(end)), QtCore.Qt.MouseButton.NoButton,
            QtCore.Qt.MouseButton.LeftButton, QtCore.Qt.KeyboardModifier.ControlModifier)
        app.sendEvent(surface, event)
        QtTest.QTest.mouseRelease(surface, QtCore.Qt.MouseButton.LeftButton,
            QtCore.Qt.KeyboardModifier.ControlModifier, end)
        assert snap.call_count == 2
    assert modifiers.gesture is None
    # Drawing works in the same view and keeps the persistent editing mode.
    panel.select_canvas_operation(operation.identity)
    modifiers.set_creation_mode('manual')
    modifiers.start_draw()
    original_ids = set(modifiers.records())
    QtTest.QTest.mousePress(surface, QtCore.Qt.MouseButton.LeftButton, pos=pixel((x-2, y-2)))
    QtTest.QTest.mouseMove(surface, pixel((x+2, y+2)))
    QtTest.QTest.mouseRelease(surface, QtCore.Qt.MouseButton.LeftButton, pos=pixel((x+2, y+2)))
    assert len(set(modifiers.records())-original_ids) == 1
    assert modifiers.drawing and modifiers.mode
    panel.undo(); assert set(modifiers.records()) == original_ids
    modifiers.select(region.id)
    with patch.object(modifiers, 'edit_assignment') as edit:
        QtTest.QTest.mouseDClick(surface, QtCore.Qt.MouseButton.LeftButton, pos=pixel((x, y)))
        assert edit.call_count == 1
    app.processEvents()
    renderer.grab().save(str(ROOT / '.tox/vispy-tab-editing.png'))
    # A spatial view cannot silently reinterpret a drawing gesture in 3D.
    band.actions['spatial'].trigger()
    assert renderer.spatial and not modifiers.mode
    verify_vispy_selection_appearance(app, window)
    verify_vispy_top_transition(window)
    verify_vispy_selection_cache(window)
    verify_vispy_plane_stacking(app, renderer)
    verify_vispy_caches(app, renderer)
    verify_vispy_picking(app, renderer)
    verify_vispy_shared_depth_passes(renderer)
    verify_vispy_segment_gaps(app, renderer)
    print('VisPy tab editing: select, drag, dimension, Ctrl snap, draw, double click, undo/redo passed')
    print('VisPy coincident lines: plane ordering, selection changes and spatial/plane switching passed')


def worker(gpu=False, kind='vispy', interop=True, benchmark=False, tools_benchmark=False, editing=False, appearance_project=None):
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
        window.filename = str(appearance_project or ROOT / 'dxf/BreakExample_Circle.dxf')
        assert window.load()
        band, panel = window.view_comparison, window.machining_panel
        if gpu and appearance_project is None:
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
        if appearance_project is not None:
            verify_vispy_selection_appearance(app, window, capture=True)
            window.close()
            app.processEvents()
            faulthandler.cancel_dump_traceback_later()
            return
        if editing:
            tab_editing_worker(app, window)
            window.close()
            app.processEvents()
            faulthandler.cancel_dump_traceback_later()
            return
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
    if '--appearance-project' in sys.argv:
        worker(True, appearance_project=Path(sys.argv[sys.argv.index('--appearance-project')+1]).resolve())
    elif '--vispy-editing-worker' in sys.argv:
        worker(True, editing=True)
    elif '--gpu-worker' in sys.argv:
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
