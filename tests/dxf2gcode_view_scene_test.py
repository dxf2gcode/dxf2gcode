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
    def test_windows_startup_activation_is_limited_to_original_foreground(self):
        from unittest.mock import Mock
        from dxf2gcode.presentation.qt.startup_activation import WindowsStartupActivation

        activation = WindowsStartupActivation.__new__(WindowsStartupActivation)
        activation.launch_window = 1
        activation.foreground = Mock(return_value=3)
        activation.set_foreground = Mock(return_value=False)
        activation.window_thread = Mock(return_value=10)
        activation.current_thread = Mock(return_value=20)
        activation.is_hung = Mock(return_value=False)
        activation.attach_input = Mock(return_value=True)
        activation.bring_to_top = Mock()
        activation.set_active = Mock()
        activation.activate(2)
        activation.set_foreground.assert_not_called()
        activation.attach_input.assert_not_called()
        activation.foreground.side_effect = (1, 1, 1, 2)
        activation.activate(2)
        activation.set_foreground.assert_called_once_with(2)
        self.assertEqual([call.args for call in activation.attach_input.call_args_list],
                         [(20, 10, True), (20, 10, False)])
        activation.bring_to_top.assert_called_once_with(2)
        activation.set_active.assert_called_once_with(2)

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

    def test_legacy_profile_migrates_and_later_2d_choice_persists(self):
        from unittest.mock import patch
        import dxf2gcode.bootstrap.runtime_state as g
        from dxf2gcode.adapters.config.runtime_config import MyConfig
        with tempfile.TemporaryDirectory() as folder, patch.object(g, 'folder', folder):
            config = MyConfig()
            general = config.var_dict['General']
            general.pop('use_vispy')
            general['mode3d'] = False
            config.save_varspace()
            migrated = MyConfig()
            self.assertTrue(migrated.use_vispy)
            self.assertNotIn('mode3d', migrated.var_dict['General'])
            migrated.var_dict['General']['use_vispy'] = False
            migrated.save_varspace()
            self.assertFalse(MyConfig().use_vispy)

    def test_all_new_messages_are_translated(self):
        import ast
        import xml.etree.ElementTree as ET
        source = ROOT / 'source/dxf2gcode/presentation/qt/view_comparison.py'
        messages = {node.args[0].value for node in ast.walk(ast.parse(source.read_text(encoding='utf-8')))
                    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and isinstance(node.func.value, ast.Name) and node.func.value.id == 'self'
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


def verify_vispy_shared_drawing(app, renderer):
    """Both cameras preserve front-to-back order at the animation handoff."""
    import numpy as np
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QColor, QPen
    def line(z):
        return (((0., 0., z), (10., 0., z), 'cut'),)
    # Separate the sample depths enough to survive framebuffer depth quantization.
    paths = (ScenePath('deep', 'geo', 'operation', line(-300.)),
             ScenePath('geo', 'geo', 'geometry', line(0.)),
             ScenePath('dash', 'geo', 'operation', (((0., 2., -300.), (10., 2., -300.), 'rapid'),)))
    original_style = renderer.path_style
    renderer.path_style = lambda path, role: QPen(QColor(
        'blue' if path.kind == 'operation' else 'black'), 3. if role == 'cut' else 1.,
        Qt.PenStyle.SolidLine if role == 'cut' else Qt.PenStyle.DashLine)
    def render_depths():
        node = next(iter(renderer.nodes.values()))
        transform = node.transforms.get_transform('visual', 'render')
        clip = transform.map(((5., 0., 0.), (5., 0., -150.), (5., 0., -300.)))
        return clip[:, 2] / clip[:, 3]

    try:
        renderer.set_spatial(False)
        renderer.set_scene(ViewScene(paths), {'deep'})
        renderer.camera.rect = (-2., -5., 14., 10.)
        renderer.fitted.add(False)
        app.processEvents()
        renderer.set_spatial(True)
        assert renderer.animate_top()
        renderer._animate_top_frame(1.)
        renderer.redraw()
        orbit_frame = renderer.canvas.render()
        orbit_depths = render_depths()
        nodes = dict(renderer.nodes)
        uploads = dict(renderer._uploads)
        renderer.finish_top_transition()
        plane_frame = renderer.canvas.render()
        plane_depths = render_depths()
        assert np.all(np.diff(orbit_depths) > 0) and np.all(np.diff(plane_depths) > 0)
        np.testing.assert_allclose(np.diff(plane_depths), np.diff(orbit_depths), rtol=1e-5)
        assert renderer.nodes == nodes and renderer._uploads == uploads
        x, y = renderer.project((5., 0., 0.))
        x = round(x*plane_frame.shape[1]/renderer.viewport().width())
        y = round(y*plane_frame.shape[0]/renderer.viewport().height())
        # A viewport height change can move the one-pixel line across the rounding boundary.
        orbit_strip = orbit_frame[y-1:y+2, x, :3]
        plane_strip = plane_frame[y-1:y+2, x, :3]
        orbit_pixel = orbit_strip[np.argmin(orbit_strip.max(axis=1))]
        plane_pixel = plane_strip[np.argmin(plane_strip.max(axis=1))]
        np.testing.assert_allclose(orbit_pixel, plane_pixel, atol=8)
        assert max(plane_pixel) < 32
    finally:
        renderer.path_style = original_style


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
            band.failed('test render failure')
            assert band.stack.currentWidget() is window.canvas
            assert legacy.call_count == 1 and not band.legacy_stale
            assert operation.identity in panel.canvas_preview.selected
        band.start(True)
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
                       if key == (cut_color, 3.)), 'Zoom uploaded unchanged solid cuts'
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
    from dxf2gcode.application.toolpath.projections import plan_preview_segments
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
        verify_depth_dash_alignment(renderer, cut_color)
        renderer.canvas.render()
    renderer.set_spatial(True)
    assert renderer.projected_data() is drawing_data
    shallow = renderer.project((5., 0., -1.5))
    deep = renderer.project((5., 0., -3.))
    assert max(abs(a-b) for a, b in zip(shallow, deep)) > 1.
    for zoom in (0.83, 1.37):
        renderer.camera.scale_factor *= zoom
        renderer.redraw()
        verify_depth_dash_alignment(renderer, cut_color)
        renderer.canvas.render()
    print('VisPy shared XYZ: both passes and plunges retained with fixed overhead and tilted views')


def verify_depth_dash_alignment(renderer, cut_color):
    import numpy as np
    node = renderer.nodes[(cut_color, .6)]
    pairs = node.pos.reshape(-1, 2, 3)
    horizontal = pairs[pairs[:, 0, 2] == pairs[:, 1, 2]]
    shallow = horizontal[horizontal[:, 0, 2] == -1.5, :, :2]
    deep = horizontal[horizontal[:, 0, 2] == -3., :, :2]
    assert len(shallow) > 1
    np.testing.assert_allclose(shallow, deep)


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
    from unittest.mock import Mock, patch
    from PyQt6.QtCore import QPoint, Qt
    panel, band = window.machining_panel, window.view_comparison
    band.activate('plane')
    groups = {}
    for path in band.snapshot.paths:
        if path.kind == 'operation':
            groups.setdefault(path.geometry, []).append(path.identity)
    geometry, identities = next((g, ids) for g, ids in groups.items() if len(ids) > 1)
    before = panel.binding.project.to_dict()
    renderer = band.renderer
    linked = [path for path in band.snapshot.paths if path.identity in identities[:2]]
    anchor = renderer.labels.rect().center()
    labels = {geometry: [((anchor.x(), anchor.y()), path.title, '') for path in linked]}
    painter = Mock()
    painter.fontMetrics.return_value = renderer.labels.fontMetrics()
    with patch.object(renderer, 'world_units_per_pixel', return_value=1e6):
        renderer.labels.paint_operation_labels(painter, labels)
    assert [call.args[1] for call in painter.drawText.call_args_list] == [
        panel.modifiers.tr('{0} operations').format(2)]
    painter.reset_mock()
    with patch.object(renderer, 'world_units_per_pixel', return_value=1e-6):
        renderer.labels.paint_operation_labels(painter, labels)
    assert [call.args[1] for call in painter.drawText.call_args_list] == [path.title for path in linked]
    assert len({call.args[0].y() for call in painter.drawText.call_args_list}) == 2
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
    verify_canvas_tab_multiselection(window)
    other = next(p for p in band.snapshot.paths if p.kind == 'operation' and p.geometry != operation.geometry)
    outline = next(p for p in band.snapshot.paths if p.identity == region.id)
    assert operation.identity in modifiers.affected(region.id)
    panel.select_canvas_operation(other.identity)
    assert renderer.path_visible(outline)
    band.buttons['selected_paths'].click()
    assert not renderer.path_visible(outline)
    modifiers.set_mode(True)
    assert region.id not in modifiers.paths(renderer)
    panel.select_canvas_operation(operation.identity)
    assert renderer.path_visible(outline)
    assert region.id in modifiers.paths(renderer)
    modifiers.set_mode(False)
    band.buttons['selected_paths'].click()
    band.buttons['tabs'].click()
    assert band.buttons['tabs'].isChecked() and panel.tab_placement.isVisible()
    modifiers.cancel()
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
    band.buttons['undo'].click()
    assert panel.binding.project.to_dict() == before
    band.buttons['redo'].click()
    assert panel.binding.project.to_dict() == after
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
    from dxf2gcode.presentation.qt import tab_modifiers
    with patch.object(tab_modifiers, 'preview_result', wraps=tab_modifiers.preview_result) as plan:
        QtTest.QTest.mouseMove(surface, pixel((x+2, y+2)))
        assert modifiers.preview_timer.isActive()
        plan.assert_not_called()
        assert set(modifiers.records()) == original_ids
        QtTest.QTest.qWait(180)
        assert [call.args[0].operation_id for call in plan.call_args_list] == [operation.identity]
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
    verify_tab_inline_parameters(app, window)
    verify_vispy_selection_appearance(app, window)
    verify_vispy_top_transition(window)
    verify_vispy_selection_cache(window)
    renderer = band.renderer
    verify_vispy_shared_drawing(app, renderer)
    verify_vispy_caches(app, renderer)
    verify_vispy_picking(app, renderer)
    verify_vispy_shared_depth_passes(renderer)
    verify_vispy_segment_gaps(app, renderer)
    print('VisPy tab editing: select, drag, dimension, Ctrl snap, draw, double click, undo/redo passed')
    print('VisPy shared rendering: line buffers and depth ordering match at handoff')


def verify_canvas_tab_multiselection(window):
    from PyQt6.QtCore import QPoint, Qt
    from PyQt6.QtTest import QTest

    panel, band = window.machining_panel, window.view_comparison
    renderer, tabs = band.renderer, panel.modifiers
    before = panel.binding.project.to_dict()
    for spatial in (True, False):
        band.activate('spatial' if spatial else 'plane')
        tabs.set_mode(not spatial)
        candidates = {}
        if spatial:
            for path in renderer.snapshot.paths:
                if path.kind != 'region':
                    continue
                for a, b, _ in path.segments:
                    point = QPoint(*(round(value) for value in renderer.project(tuple((u+v)/2 for u, v in zip(a,b)))))
                    if renderer.viewport().rect().contains(point) and renderer.path_hits(point, kinds=('region',)) == (path.identity,):
                        candidates[path.identity] = point
                        break
        else:
            paths = tabs.paths(renderer)
            for identity, path in paths.items():
                point = path.boundingRect().center()
                if renderer.viewport().rect().contains(point.toPoint()) and [
                        key for key, outline in paths.items() if outline.contains(point)] == [identity]:
                    candidates[identity] = point.toPoint()
        first, second = tuple(candidates)[:2]
        tabs.select(first)
        QTest.mouseClick(renderer.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.ControlModifier,
                         candidates[second])
        assert tabs.selected_regions == {first, second}
        assert len(tabs.editable_regions()) == 2
        QTest.mouseClick(renderer.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.ControlModifier,
                         candidates[second])
        assert tabs.selected_regions == {first} and tabs.context == first
    tabs.set_mode(False)
    band.activate('spatial')
    assert panel.binding.project.to_dict() == before
    print('Canvas tab selection: Ctrl add/remove in top and spatial views passed')


def verify_tab_inline_parameters(app, window):
    from importlib import import_module
    from dxf2gcode.presentation.qt.qt_compat import QtCore, PYQT_VERSION
    from dxf2gcode.presentation.qt.tab_modifiers import ROLE
    QTest = import_module(f'PyQt{PYQT_VERSION}.QtTest').QTest
    Qt = QtCore.Qt

    panel, tree = window.machining_panel, window.machining_panel.tree
    tabs = panel.modifiers
    window.ui.mytabWidget.setCurrentWidget(panel)
    group = next(group for group in tabs.groups if group.childCount() >= 2)
    group.parent().setExpanded(True)
    group.setExpanded(True)
    items = [group.child(i) for i in range(2)]
    identities = {item.data(0, ROLE)[1] for item in items}
    initial = panel.binding.project.to_dict()
    for i, item in enumerate(items):
        tree.scrollToItem(item)
        app.processEvents()
        QTest.mouseClick(tree.viewport(), Qt.MouseButton.LeftButton,
                         Qt.KeyboardModifier.ControlModifier if i else Qt.KeyboardModifier.NoModifier,
                         tree.visualItemRect(item).center())
    assert tabs.selected_regions == identities and not tabs.mode
    height = tabs.fields['height']
    assert height.isVisible() and not height.isReadOnly() and tabs.enabled.isEnabled()
    history = len(panel.commands.undo_stack)
    height.setFocus()
    height.selectAll()
    QTest.keyClicks(height, '-1.75')
    QTest.keyClick(height, Qt.Key.Key_Return)
    assert all(tabs.records()[key].height == -1.75 for key in identities)
    assert len(panel.commands.undo_stack) == history + 1 and tabs.selected_regions == identities
    name = tabs.name_field
    name.setFocus()
    name.selectAll()
    QTest.keyClicks(name, 'Shared name')
    QTest.keyClick(name, Qt.Key.Key_Return)
    assert all(tabs.records()[key].name == 'Shared name' for key in identities)
    tabs.enabled.setChecked(False)
    assert all(not tabs.records()[key].enabled for key in identities)
    panel.undo()
    assert all(tabs.records()[key].enabled for key in identities)
    panel.undo()
    tabs.assignment_scope.setCurrentIndex(tabs.assignment_scope.findData('operations'))
    target = tabs.assignment_targets.topLevelItem(0)
    assert target is not None
    target.setCheckState(0, Qt.CheckState.Checked)
    expected = tabs.assignment_values()
    if not tabs.assignment_button.isEnabled():
        tabs.assignment_scope.setCurrentIndex(tabs.assignment_scope.findData('global'))
        expected = tabs.assignment_values()
    assert tabs.assignment_button.isEnabled()
    tabs.assignment_button.click()
    assert all(all(getattr(tabs.records()[key], field) == value
                   for field, value in expected.items()) for key in identities)
    panel.undo()
    panel.undo()
    assert panel.binding.project.to_dict() == initial
    print('Inline tab editor: Ctrl selection, batch height, assignment and undo passed')


def verify_tab_context_menu(app, window):
    from dataclasses import replace
    from uuid import uuid4
    from unittest.mock import patch
    from dxf2gcode.presentation.qt.qt_compat import QtCore
    from dxf2gcode.presentation.qt.qt_compat.QtGui import QContextMenuEvent
    from dxf2gcode.presentation.qt.qt_compat.QtWidgets import QMenu

    panel, band = window.machining_panel, window.view_comparison.band
    tabs = panel.modifiers
    before = panel.binding.project.to_dict()
    region = replace(next(iter(tabs.records().values())), id=str(uuid4()))
    tabs.start_draw()
    panel.execute(lambda: panel.commands.create_region(region))
    surface = window.canvas.viewport()
    point = surface.rect().center()
    calls = []

    def inspect(menu, position):
        calls.append(position)
        assert band.toggleViewAction() not in menu.actions()
        assert any(action.text() == 'Move workpiece zero here ...' for action in menu.actions())

    with patch.object(QMenu, 'exec', new=inspect):
        for undo in (False, True):
            if undo:
                panel.undo()
                assert panel.binding.project.to_dict() == before
            assert tabs.mode
            app.sendEvent(surface, QContextMenuEvent(QContextMenuEvent.Reason.Mouse,
                          point, surface.mapToGlobal(point)))
            assert not band.isHidden()
        assert len(calls) == 2
    tabs.set_mode(False)
    assert window.createPopupMenu() is None
    band.hide()
    window.saveWindowState()
    window.restoreWindowState()
    assert not band.isHidden()


def verify_vispy_mouse_controls(app, window):
    from unittest.mock import patch
    from PyQt6.QtCore import QEvent, QPoint, QPointF, Qt
    from PyQt6.QtGui import QContextMenuEvent, QMouseEvent
    from PyQt6.QtTest import QTest
    from PyQt6.QtWidgets import QMenu

    band, panel = window.view_comparison, window.machining_panel
    band.activate('plane')
    renderer = band.renderer
    operation_geometries = {p.geometry for p in band.snapshot.paths if p.kind == 'operation'}
    path = next(p for p in band.snapshot.paths
                if p.kind == 'geometry' and p.enabled and p.identity in operation_geometries)
    start, end, _ = renderer.projected_segments(path)[0]
    x, y = renderer.project(tuple((a+b)/2 for a, b in zip(start, end)))
    point = QPoint(round(x), round(y))
    widget = renderer.pick_widget
    QTest.mousePress(widget, Qt.MouseButton.LeftButton, pos=point-QPoint(8, 8))
    end = point+QPoint(8, 8)
    app.sendEvent(widget, QMouseEvent(QEvent.Type.MouseMove, QPointF(end), QPointF(widget.mapToGlobal(end)),
                                     Qt.MouseButton.NoButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier))
    assert renderer.selection_band.frame.isActive()
    assert renderer.selection_band.pending.bottomRight() == end
    renderer.selection_band.frame.stop()
    renderer.selection_band.update_outline()
    assert not renderer.selection_band.outline.isEmpty()
    pixmap = renderer.selection_band.grab()
    pixel = (QPointF(renderer.selection_band.outline.center()) * pixmap.devicePixelRatio()).toPoint()
    assert pixmap.toImage().pixelColor(pixel).alpha() > 0
    rows = dict(panel.entry_items)
    QTest.mouseRelease(widget, Qt.MouseButton.LeftButton, pos=end)
    assert renderer.selection_band.outline.isEmpty()
    assert panel.binding.sources[path.identity].isSelected()
    assert panel.entry_items == rows
    assert any(p.identity in panel.selected_entries() for p in band.snapshot.paths
               if p.kind == 'operation' and p.geometry == path.identity)
    with patch('dxf2gcode.presentation.qt.canvas.MyDropDownMenu') as menu:
        app.sendEvent(widget, QContextMenuEvent(QContextMenuEvent.Reason.Mouse,
                                                point, widget.mapToGlobal(point)))
        scene, position, clicked = menu.call_args.args
        assert scene is window.canvas_scene and position == widget.mapToGlobal(point)
        assert (clicked.x, clicked.y) == renderer.tab_scene_point(point)
    window.ui.actionLiveUpdateExportRoute.setChecked(True)
    assert window.canvas_scene.routearrows
    with patch('dxf2gcode.presentation.qt.vispy_view.paint_arrowhead') as arrows:
        renderer.labels.grab()
        assert arrows.call_count >= len(window.canvas_scene.routearrows)
    with patch('dxf2gcode.presentation.qt.vispy_view.scale_bar_enabled', return_value=True):
        with patch.object(renderer.scale_bar, 'paint', wraps=renderer.scale_bar.paint) as paint:
            renderer.labels.grab()
            paint.assert_called_once()
    window.ui.actionLiveUpdateExportRoute.setChecked(False)
    assert not window.canvas_scene.routearrows and not window.canvas_scene.routetext
    window.updateExportRoute()
    assert not window.canvas_scene.routearrows

    band.activate('spatial')
    operation = next(p for p in band.snapshot.paths if p.kind == 'operation' and p.geometry == path.identity)
    panel.select_canvas_operation(operation.identity)
    right = Qt.MouseButton.RightButton
    point = widget.rect().center()
    global_point = widget.mapToGlobal(point)
    menu_positions = []

    def inspect_menu(menu, position):
        menu_positions.append(position)
        actions = {action.text(): action for action in menu.actions()}
        for label in ('Move workpiece zero here ...', 'Set Nearest StartPoint', 'Draw new tab region…'):
            assert not actions[label].isEnabled()
            assert actions[label].toolTip() == 'Available in top view.'
        for label in ('Invert Selection', 'Switch Direction', 'Set Sharpest StartPoint', 'Assign machining…'):
            assert actions[label].isEnabled(), label

    with patch.object(QMenu, 'exec', new=inspect_menu):
        QTest.mouseClick(widget, right, pos=point)
        app.sendEvent(widget, QContextMenuEvent(QContextMenuEvent.Reason.Mouse, point, global_point))
        app.processEvents()
        assert menu_positions == [global_point]

        scale = renderer.camera.scale_factor
        end = point + QPoint(0, 35)
        QTest.mousePress(widget, right, pos=point)
        app.sendEvent(widget, QMouseEvent(QEvent.Type.MouseMove, QPointF(end), QPointF(widget.mapToGlobal(end)),
                                         Qt.MouseButton.NoButton, right, Qt.KeyboardModifier.NoModifier))
        QTest.mouseRelease(widget, right, pos=end)
        app.processEvents()
        assert renderer.camera.scale_factor != scale
        assert menu_positions == [global_point]
    band.activate('plane')


def verify_machining_checkboxes(app, window):
    from importlib import import_module
    from unittest.mock import patch
    from dxf2gcode.presentation.qt.qt_compat import QtCore, PYQT_VERSION
    from dxf2gcode.presentation.qt.qt_compat.QtGui import QContextMenuEvent
    from dxf2gcode.presentation.qt.qt_compat.QtWidgets import QMenu
    QTest = import_module(f'PyQt{PYQT_VERSION}.QtTest').QTest
    Qt = QtCore.Qt
    panel = window.machining_panel
    tree = panel.tree
    first, second = tuple(panel.entry_items)[:2]
    window.show()
    window.ui.mytabWidget.setCurrentWidget(panel)
    panel.select_canvas_operation(first)
    app.processEvents()

    def entry(identity):
        return panel.commands.entries(panel.binding.project, [identity])[0][1]

    def indicator(column):
        item = panel.entry_items[second]
        tree.scrollToItem(item)
        rect = tree.visualRect(tree.indexFromItem(item, column))
        return next(point for x in range(rect.left(), rect.right() + 1)
                    if tree.checkbox_at(point := QtCore.QPoint(x, rect.center().y())).isValid())

    def assert_selection():
        assert tree.currentItem() is panel.entry_items[first]
        assert panel.selected_entries() == [first] and panel.context == first

    for column, field in ((1, 'enabled'), (2, 'optimize')):
        previous = getattr(entry(second), field)
        selected_item = tree.currentItem()
        QTest.mouseClick(tree.viewport(), Qt.MouseButton.LeftButton, pos=indicator(column))
        app.processEvents()
        assert getattr(entry(second), field) != previous
        assert_selection()
        assert tree.currentItem() is selected_item
        position = indicator(column)
        history = len(panel.commands.undo_stack)

        def disable_all(menu, *_):
            assert_selection()
            expected = 'Disable export for all' if column == 1 else 'Disable optimization for all'
            action = next(a for a in menu.actions() if a.text() == panel.tr(expected))
            assert action.isEnabled()
            action.trigger()
        with patch.object(QMenu, 'exec', new=disable_all):
            QTest.mouseClick(tree.viewport(), Qt.MouseButton.RightButton, pos=position)
            app.sendEvent(tree.viewport(), QContextMenuEvent(QContextMenuEvent.Reason.Mouse,
                position, tree.viewport().mapToGlobal(position)))
        assert len(panel.commands.undo_stack) == history + 1
        assert not any(getattr(entry(identity), field) for identity in panel.entry_items)
        assert_selection()
        def enable_all(menu, *_):
            assert_selection()
            expected = 'Enable export for all' if column == 1 else 'Enable optimization for all'
            action = next(a for a in menu.actions() if a.text() == panel.tr(expected))
            assert action.isEnabled()
            action.trigger()
        header = tree.header()
        position = QtCore.QPoint(header.sectionViewportPosition(column) + 1, 1)
        with patch.object(QMenu, 'exec', new=enable_all):
            app.sendEvent(header.viewport(), QContextMenuEvent(QContextMenuEvent.Reason.Mouse,
                position, header.viewport().mapToGlobal(position)))
        assert len(panel.commands.undo_stack) == history + 2
        assert all(getattr(entry(identity), field) for identity in panel.entry_items)
        assert_selection()
        panel.undo()
        assert not any(getattr(entry(identity), field) for identity in panel.entry_items)
        panel.undo()
        if field == 'enabled':
            assert entry(first).enabled
        panel.undo()
        assert getattr(entry(second), field) == previous


def worker(gpu=False, editing=False, appearance_project=None):
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
        g.quiet = True
        from dxf2gcode.presentation.qt import application as module
        from dxf2gcode.presentation.qt.canvas2d import MyGraphicsScene
        if PYQT_VERSION == 6:
            from dxf2gcode.presentation.qt.generated.dxf2gcode_ui6 import Ui_MainWindow
        else:
            from dxf2gcode.presentation.qt.generated.dxf2gcode_ui5 import Ui_MainWindow
        module.Ui_MainWindow, module.MyGraphicsScene = Ui_MainWindow, MyGraphicsScene
        g.folder = str(Path(folder) / 'config')
        app = QApplication([])
        settings = QtCore.QSettings(str(Path(folder) / 'window.ini'), QtCore.QSettings.Format.IniFormat)
        settings.setValue('MainWindow/view/selectedPathsOnly', True)
        settings.setValue('MainWindow/view/showRetracts', False)
        settings.setValue('MainWindow/view/showOriginAxes', False)
        if not gpu:
            from dxf2gcode.presentation.qt.qt_compat.QtWidgets import QMainWindow, QToolBar
            old_window = QMainWindow()
            old_band = QToolBar(old_window)
            old_band.setObjectName('viewBand')
            old_window.addToolBar(old_band)
            old_band.hide()
            settings.setValue('MainWindow/geometry', old_window.saveGeometry())
            settings.setValue('MainWindow/state', old_window.saveState())
            old_window.deleteLater()
        with patch.object(QtCore, 'QSettings', return_value=settings):
            window = module.MainWindow(app)
        assert not window.view_comparison.band.isHidden()
        g.window = window
        module.options = SimpleNamespace(post_pro=window.MyPostProcessor.output_text[0])
        band, panel = window.view_comparison, window.machining_panel
        assert band.selected_paths_action.isChecked() and not band.retracts_action.isChecked()
        assert not band.origin_axes_action.isChecked()
        band.selected_paths_action.setChecked(False)
        band.retracts_action.setChecked(True)
        def check_view_band(vispy):
            groups = (
                (('open', window.ui.actionOpen), ('reload', window.ui.actionReload),
                 ('save_project', window.ui.actionSaveProjectAs),
                 ('options', band.buttons['options'].defaultAction()), ('exit', window.ui.actionClose)),
                (('workpiece_zero', window.ui.actionMoveWorkpieceZero), ('scale', window.ui.actionScaleAll),
                 ('rotate', window.ui.actionRotateAll), ('mirror', window.ui.actionMirrorAll)),
                (('new', panel.buttons['new']), ('tabs', panel.buttons['tabs'])),
                (('export', window.ui.actionExportShapes), ('optimize', window.ui.actionOptimizePaths),
                 ('optimize_export', window.ui.actionOptimizeAndExportShapes),
                 ('route_live', window.ui.actionLiveUpdateExportRoute)),
                (('plane', window.ui.actionTopView), ('spatial', window.ui.actionIsometricView),
                 ('fit', window.ui.actionAutoscale), ('disabled_paths', window.ui.actionShowDisabledPaths),
                 ('directions', window.ui.actionShowPathDirections), ('selected_paths', band.selected_paths_action),
                 ('retracts', band.retracts_action), ('scale_bar', band.scale_bar_action),
                 ('origin_axes', band.origin_axes_action), ('tools', band.tools_action)),
                (('info', window.ui.actionAbout),),
            )
            topics = ('Program', 'Drawing', 'Machining', 'Output', 'View', 'Info')
            if window.title_bar is None:
                groups = (*groups[:3], (('undo', panel.buttons['undo']), ('redo', panel.buttons['redo'])),
                          *groups[3:])
                topics = (*topics[:3], 'History', *topics[3:])
            else:
                for name in ('undo', 'redo'):
                    button = band.buttons[name]
                    assert button.parent() is window.title_bar and button.defaultAction() is panel.buttons[name]
                    assert button.toolTip()
            parents = []
            for group in groups:
                parents.append(band.buttons[group[0][0]].parent())
                for name, action in group:
                    button = band.buttons[name]
                    assert button.parent() is parents[-1]
                    assert button.defaultAction() is action and not button.icon().isNull(), name
                    large = name in ('open', 'new', 'export')
                    assert button.toolButtonStyle() == (QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon
                                                        if large else QtCore.Qt.ToolButtonStyle.ToolButtonIconOnly)
                    assert button.iconSize().width() == (28 if large else 18)
                    assert button.toolTip() and button.accessibleName()
                    assert button.isHidden() == (not vispy and name in ('plane', 'spatial', 'origin_axes', 'tools'))
                    if not action.shortcut().isEmpty():
                        assert action in window.actions()
            assert len(set(parents)) == len(topics)
            assert [parent.layout().itemAt(1).widget().text() for parent in parents] == [
                band.tr(topic) for topic in topics]
            toolbar_widgets = [band.band.widgetForAction(action) for action in band.band.actions()]
            assert [widget for widget in toolbar_widgets if widget in parents] == parents
            assert band.band.widgetForAction(band.band.actions()[-1]) is parents[-1]
            assert panel.tab_placement.parent() is band.buttons['tabs'].parent()
            assert not panel.tab_placement.isHidden()
            assert all(not panel.tab_placement.itemIcon(i).isNull() for i in range(panel.tab_placement.count()))
            for first, second in (('reload', 'save_project'), ('options', 'exit'),
                                  ('optimize', 'optimize_export')):
                grid = band.buttons[first].parent().layout().itemAt(0).layout()
                top = grid.getItemPosition(grid.indexOf(band.buttons[first]))
                bottom = grid.getItemPosition(grid.indexOf(band.buttons[second]))
                assert top[0] == 0 and bottom[0] == 1 and top[1] == bottom[1]

        check_view_band(False)
        placement = panel.tab_placement
        initial_placement = placement.currentIndex()
        placement.setCurrentIndex(placement.findData('manual'))
        assert panel.modifiers.drawing_mode() == 'manual'
        assert placement.toolTip() == placement.currentText() and not panel.modifiers.mode
        placement.setCurrentIndex(initial_placement)
        assert window.menuWidget() is window.title_bar
        options = window.ui.menuOptions
        assert band.buttons['options'].menu() is options
        assert band.buttons['info'].menu() is None
        assert [action for action in options.actions() if action.menu() is not None] == [
            window.menu_config_profile.menuAction(), window.ui.menuMachine_Type.menuAction(),
            window.ui.menu_Measurement_units.menuAction()]
        assert {window.ui.actionConfiguration, window.ui.actionConfigurationPostprocessor}.issubset(window.actions())
        assert not {button.defaultAction() for button in band.buttons.values()}.intersection(
            options.actions())
        with patch.object(module, 'AboutDialog') as about:
            band.buttons['info'].click()
        about.assert_called_once()
        document_buttons = ('reload', 'save_project', 'workpiece_zero', 'scale', 'rotate', 'mirror',
                            'optimize', 'export', 'optimize_export')
        assert band.buttons['open'].isEnabled() and band.buttons['exit'].isEnabled()
        assert all(not band.buttons[name].isEnabled() for name in document_buttons)
        with patch.object(window, 'OpenFileDialog') as open_dialog:
            band.buttons['open'].click()
        open_dialog.assert_called_once()
        assert not band.buttons['new'].isEnabled()
        assert not band.buttons['tabs'].isEnabled() and not band.buttons['undo'].isEnabled()
        if gpu:
            from PyQt6.QtTest import QTest
            assert not window.isVisible()
            show = window.show
            def show_with_complete_ribbon():
                assert band.renderer is not None and band.stack.currentWidget() is band.renderer
                assert not band.buttons['spatial'].isHidden() and band.buttons['spatial'].isChecked()
                show()
            with patch.object(window, 'show', side_effect=show_with_complete_ribbon) as first_show:
                window.show_at_startup()
                first_show.assert_called_once()
            app.processEvents()
            assert window.isVisible()
            if app.platformName() == 'windows':
                assert window.isActiveWindow()
            if app.platformName() == 'windows' and hasattr(QtCore.Qt.WindowType, 'ExpandedClientAreaHint'):
                title_bar = window.title_bar
                assert title_bar is not None
                for show in (window.showNormal, window.showMaximized):
                    show()
                    app.processEvents()
                    assert title_bar.y() == 0 and title_bar.height() == window.windowHandle().safeAreaMargins().top()
                    assert band.band.y() >= title_bar.height()
                    assert title_bar.icon.x() < band.buttons['undo'].x() < band.buttons['redo'].x() < title_bar.text.x()
                    assert all(button.isVisible() for button in (band.buttons['undo'], band.buttons['redo']))
                flags = window.windowHandle().flags()
                assert flags & QtCore.Qt.WindowType.WindowCloseButtonHint
                assert flags & QtCore.Qt.WindowType.WindowMinMaxButtonsHint == QtCore.Qt.WindowType.WindowMinMaxButtonsHint
                assert not flags & QtCore.Qt.WindowType.WindowTitleHint
            opened = []
            def dismiss_options():
                opened.append(True)
                QtCore.QTimer.singleShot(0, options.close)
            options.aboutToShow.connect(dismiss_options)
            QTest.mouseClick(band.buttons['options'], QtCore.Qt.MouseButton.LeftButton)
            options.aboutToShow.disconnect(dismiss_options)
            assert opened == [True]
            app.processEvents()
            app.setActiveWindow(window)
            with patch.object(window, 'OpenFileDialog') as open_dialog:
                QTest.keyClick(window, QtCore.Qt.Key.Key_O, QtCore.Qt.KeyboardModifier.ControlModifier)
            open_dialog.assert_called_once()
            assert band.renderer is not None, 'VisPy startup unexpectedly fell back'
            assert band.renderer.spatial
            assert band.actions['spatial'].isChecked()
            check_view_band(True)
            assert band.buttons['spatial'].isChecked() and not band.buttons['plane'].isChecked()
        window.filename = str(appearance_project or ROOT / 'dxf/BreakExample_Circle.dxf')
        assert window.load()
        if window.title_bar is not None:
            assert window.filename in window.title_bar.text.text()
            assert not window.windowHandle().flags() & QtCore.Qt.WindowType.WindowTitleHint
        assert all(band.buttons[name].isEnabled() for name in document_buttons)
        assert band.buttons['tabs'].isEnabled()
        assert band.buttons['new'].isEnabled()
        with patch.object(panel, 'step_dialog', return_value=None) as dialog:
            band.buttons['new'].click()
        dialog.assert_called_once()
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
            renderer = band.renderer
            snapshot = renderer.snapshot
            assert band.scale_bar_action.isChecked()
            from dxf2gcode.presentation.qt.vispy_view import paint_origin_axes
            with patch('dxf2gcode.presentation.qt.vispy_view.paint_origin_axes', wraps=paint_origin_axes) as axes, \
                    patch('dxf2gcode.presentation.qt.vispy_view.paint_workpiece_zero') as zero, \
                    patch.object(renderer.scale_bar, 'paint') as scale, \
                    patch.object(renderer.spatial_scale_bar, 'paint_spatial',
                                 wraps=renderer.spatial_scale_bar.paint_spatial) as spatial_scale:
                renderer.labels.grab()
                axes.assert_not_called()
                zero.assert_not_called()
                scale.assert_not_called()
                assert [axis for axis, _, _ in spatial_scale.call_args.args[2]] == ['X', 'Y', 'Z']
                first_axes = spatial_scale.call_args.args[2]
                first_length = renderer.spatial_scale_bar.length
                camera_state = renderer.camera.get_state()
                renderer.camera.azimuth += 30
                renderer.labels.grab()
                assert spatial_scale.call_args.args[2] != first_axes
                renderer.camera.scale_factor *= 4
                renderer.labels.grab()
                assert renderer.spatial_scale_bar.length > first_length
                renderer.camera.set_state(camera_state)
                band.buttons['origin_axes'].click()
                renderer.labels.grab()
                axes.assert_called()
                assert axes.call_args.args[2] == renderer.project((0., 0., 0.))
                band.activate('plane')
                axes.reset_mock()
                renderer.labels.grab()
                axes.assert_not_called()
                zero.assert_called()
                band.activate('spatial')
                scale.assert_called()
                band.buttons['scale_bar'].click()
                spatial_scale.reset_mock()
                renderer.labels.grab()
                spatial_scale.assert_not_called()
                band.buttons['scale_bar'].click()
            operation = next(path for path in snapshot.paths if path.kind == 'operation')
            retracts = [(a, b) for a, b, role in operation.segments if role == 'retract']
            assert retracts and all(a[:2] == b[:2] and a[2] < b[2] for a, b in retracts)
            with patch.object(panel, 'refresh_preview', wraps=panel.refresh_preview) as refresh:
                band.buttons['selected_paths'].click()
                assert operation.identity not in renderer.selected
                assert not renderer.path_visible(operation)
                assert all(renderer.path_visible(path) for path in snapshot.paths if path.kind == 'geometry')
                assert not any(role == 'cut' for _, paths in renderer._uploads.values()
                               for _, role, _, _ in paths)
                band.buttons['selected_paths'].click()
                assert renderer.path_visible(operation)
                band.buttons['retracts'].click()
                assert not any(role == 'retract' for _, paths in renderer._uploads.values()
                               for _, role, _, _ in paths)
                band.buttons['retracts'].click()
                assert any(role == 'retract' for _, paths in renderer._uploads.values()
                           for _, role, _, _ in paths)
                assert renderer.snapshot is snapshot
                refresh.assert_not_called()
            with patch.object(panel, 'refresh_preview', wraps=panel.refresh_preview) as refresh:
                band.buttons['directions'].click()
                assert window.ui.actionShowPathDirections.isChecked()
                renderer.labels.grab()
                assert renderer.snapshot is snapshot
                band.buttons['directions'].click()
                refresh.assert_not_called()
            verify_vispy_mouse_controls(app, window)
            renderer = band.renderer
            assert renderer.canvas.render()[..., :3].min() < 100, 'Top view is blank'
            verify_vispy_shared_drawing(app, renderer)
            verify_vispy_selection_cache(window)
            renderer = band.renderer
            snapshot = band.snapshot
            operation = next(path for path in snapshot.paths if path.kind == 'operation')
            panel.select_canvas_operation(operation.identity)
            assert band.snapshot is snapshot
            band.buttons['selected_paths'].click()
            visible = {path.identity for path in snapshot.paths
                       if path.kind == 'operation' and renderer.path_visible(path)}
            assert visible == {operation.identity}
            band.buttons['selected_paths'].click()
            band.buttons['tools'].click()
            assert band.tools_action.isChecked()
            app.processEvents()
            expected = len(preview_tool_bodies(snapshot, renderer.selected))
            assert expected > 0
            assert sum(node.visible for node in renderer.tool_nodes.values()) == expected
            band.buttons['tools'].click()
            assert not band.tools_action.isChecked()
            app.processEvents()
            assert not any(node.visible for node in renderer.tool_nodes.values())
            assert panel.binding.project.to_dict() == before
        else:
            method = 'dxf2gcode.presentation.qt.view_comparison'
            assert window.canvas is band.stack.currentWidget()
            with patch(method+'.PYQT_VERSION', 6), patch(method+'.importlib.util.find_spec', return_value=None):
                band.start(True)
            assert 'vispy' not in sys.modules
            assert not band.actions['spatial'].isVisible()
            check_view_band(False)
            assert band.stack.currentWidget() is window.canvas
            with patch(method+'.PYQT_VERSION', 6), patch(method+'.importlib.util.find_spec', return_value=True):
                with patch('dxf2gcode.presentation.qt.vispy_view.VispyView', side_effect=RuntimeError('test context failure')):
                    band.start(True)
            assert band.stack.currentWidget() is window.canvas
            assert g.config.vars.General['use_vispy']
            assert panel.binding.project.to_dict() == before
            band.buttons['directions'].click()
            assert panel.canvas_preview.visible_records()
            band.buttons['selected_paths'].click()
            assert not panel.canvas_preview.visible_records()
            entry = panel.canvas_preview.records[0]
            panel.select_canvas_operation(entry.identity)
            assert [record.identity for record in panel.canvas_preview.visible_records()] == [entry.identity]
            band.buttons['selected_paths'].click()
        window.saveWindowState()
        assert settings.value('MainWindow/view/selectedPathsOnly', type=bool) is False
        assert settings.value('MainWindow/view/showRetracts', type=bool) is True
        assert settings.value('MainWindow/view/showOriginAxes', type=bool) == gpu
        verify_machining_checkboxes(app, window)
        if not gpu:
            verify_tab_inline_parameters(app, window)
            verify_tab_context_menu(app, window)
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
    elif '--fallback-worker' in sys.argv:
        worker()
    else:
        unittest.main()
