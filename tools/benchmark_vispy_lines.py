"""Explicit Windows GPU/RAM experiment; never selects a production renderer.

Run each method in a fresh PyQt6 process. The batched AGG experiment reuses
VisPy 0.17's private strip baker to combine independent paths in one VBO;
that dependency must be reviewed before any production adoption.
"""

import argparse
import ctypes
from ctypes import wintypes
import faulthandler
import hashlib
import json
import os
import platform
from pathlib import Path
from statistics import median
import sys
import tempfile
from time import perf_counter
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'source'))


def memory():
    class Counters(ctypes.Structure):
        _fields_ = [('cb', wintypes.DWORD), ('PageFaultCount', wintypes.DWORD)] + [
            (name, ctypes.c_size_t) for name in (
                'PeakWorkingSetSize', 'WorkingSetSize', 'QuotaPeakPagedPoolUsage',
                'QuotaPagedPoolUsage', 'QuotaPeakNonPagedPoolUsage',
                'QuotaNonPagedPoolUsage', 'PagefileUsage', 'PeakPagefileUsage',
                'PrivateUsage')]
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    query = ctypes.WinDLL('psapi', use_last_error=True).GetProcessMemoryInfo
    query.argtypes = (wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD)
    counters = Counters()
    counters.cb = ctypes.sizeof(counters)
    if not query(kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
        raise ctypes.WinError(ctypes.get_last_error())
    return {name: round(getattr(counters, field)/1024**2, 2) for name, field in (
        ('working_mib', 'WorkingSetSize'), ('private_mib', 'PrivateUsage'),
        ('peak_working_mib', 'PeakWorkingSetSize'), ('peak_commit_mib', 'PeakPagefileUsage'))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--method', choices=('gl', 'agg', 'agg-batched', 'current'), required=True)
    parser.add_argument('--drawing', type=Path, default=ROOT/'dxf/AFluegel Rippen b2 0201.dxf')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--samples', type=int, default=12)
    parser.add_argument('--max-nodes', type=int, default=1500)
    parser.add_argument('--camera-only', action='store_true', help='Isolate camera-only panning without rebuilding line geometry')
    parser.add_argument('--clicks-only', action='store_true', help='Measure real Qt canvas clicks, including hit testing')
    args = parser.parse_args()
    if sys.platform != 'win32':
        parser.error('This measurement uses Windows process memory counters.')
    os.environ['DXF2GCODE_QT'] = '6'
    args.output.parent.mkdir(parents=True, exist_ok=True)
    faulthandler.dump_traceback_later(180, exit=True)
    import numpy as np
    import vispy
    from vispy import gloo
    from vispy.visuals.line.line import _AggLineVisual
    from dxf2gcode.presentation.qt.qt_compat import QtCore
    from dxf2gcode.presentation.qt.qt_compat.QtWidgets import QApplication
    from dxf2gcode.presentation.qt.vispy_view import VispyView, connected_chains
    from dxf2gcode.presentation.qt.view_interaction import dash_segments
    import dxf2gcode.bootstrap.runtime_state as g
    from dxf2gcode.adapters.config.runtime_config import MyConfig

    report = dict(method=args.method, drawing=args.drawing.name,
        drawing_sha256=hashlib.sha256(args.drawing.read_bytes()).hexdigest(),
        python=sys.version, platform=platform.platform(), processor=platform.processor(),
        vispy=vispy.__version__, samples=args.samples, camera_only=args.camera_only, clicks_only=args.clicks_only,
        measurements={}, checkpoints={}, status='running')

    def checkpoint(name, enforce=True):
        report['checkpoints'][name] = memory()
        print(name, report['checkpoints'][name], flush=True)
        if enforce and report['checkpoints'][name]['private_mib'] > 1800:
            raise RuntimeError('Experiment stopped at 1800 MiB private memory budget')

    class BenchmarkView(VispyView):
        def set_scene(self, snapshot, selected):
            if snapshot.paths and not self.snapshot.paths:
                # Production currently uploads before the first fit. Avoid
                # benchmarking an enormous transient dash count at unit zoom.
                points = [p for path in snapshot.paths for a, b, _ in path.projected(False) for p in (a, b)]
                self.camera.set_range(x=(min(p[0] for p in points), max(p[0] for p in points)),
                    y=(min(p[1] for p in points), max(p[1] for p in points)), margin=.08)
                self.fitted.add(False)
            super().set_scene(snapshot, selected)

        def _redraw(self):
            if args.method == 'current':
                return super()._redraw()
            groups = {}
            unit = max(self.camera.rect.height/max(1, self.height()), 1e-12)
            for path in self.snapshot.paths:
                if path.kind == 'region' or not path.enabled and not self.show_disabled:
                    continue
                order = (2 if path.identity in self.selected else 0) if path.kind == 'operation' else 1
                roles = {}
                for a, b, role in path.projected(False):
                    roles.setdefault(role, []).append((a, b))
                for role, pairs in roles.items():
                    pen = self.path_style(path, role)
                    dashed = pen.style() != QtCore.Qt.PenStyle.SolidLine
                    if dashed:
                        points = dash_segments(pairs, unit, pen.style() == QtCore.Qt.PenStyle.DotLine)
                        pairs = list(zip(points[::2], points[1::2]))
                    key = (order, pen.color().getRgbF(), pen.widthF() or 1.)
                    if args.method == 'gl':
                        groups.setdefault(key, []).extend(p for pair in pairs for p in pair)
                    else:
                        for index, chain in enumerate(connected_chains(pairs)):
                            target = key if args.method == 'agg-batched' else (*key, path.identity, role, index)
                            groups.setdefault(target, []).append(np.asarray([p[:2] for p in chain], dtype=np.float32))
            if len(groups) > args.max_nodes:
                report['required_nodes'] = len(groups)
                raise RuntimeError('Experiment stopped: required %d visuals exceeds node budget %d' % (len(groups), args.max_nodes))
            # Discard obsolete selection/dash geometries rather than retaining
            # invisible objects, so memory growth reflects an intended adapter.
            for key in set(self.nodes)-set(groups):
                self.nodes.pop(key).parent = None
            for key, values in groups.items():
                if key not in self.nodes:
                    self.nodes[key] = self.scene_api.visuals.Line(parent=self.view.scene,
                        method='gl' if args.method == 'gl' else 'agg',
                        connect='segments' if args.method == 'gl' else 'strip', antialias=True)
                node = self.nodes[key]
                node.order = key[0]
                node.set_gl_state(depth_test=False, blend=True,
                    blend_func=('src_alpha', 'one_minus_src_alpha'))
                if args.method == 'gl':
                    positions = np.asarray(values, dtype=np.float32)
                else:
                    positions = np.concatenate(values)
                    if args.method == 'agg-batched':
                        # All chains retain independent joins, caps and gaps.
                        vertices, indices, offset = [], [], 0
                        for chain in values:
                            v, i = _AggLineVisual._agg_bake(chain, np.asarray(key[1]))
                            vertices.append(v)
                            indices.append(i+offset)
                            offset += len(v)
                        baked = np.concatenate(vertices), np.concatenate(indices)
                        node._line_visual._agg_bake = lambda pos, color, baked=baked: baked
                node.set_data(pos=positions, color=key[1], width=key[2])
            self.labels.setGeometry(self.canvas.native.rect())
            self.labels.update()
            self.canvas.update()

        def redraw(self):
            # Benchmark errors must abort the experiment, not silently fall
            # back to the original Qt canvas and produce misleading timings.
            if self.isVisible():
                self._redraw()

    with tempfile.TemporaryDirectory(prefix='d2g-vispy-lines-') as folder:
        g.folder = str(Path(folder)/'config')
        Path(g.folder).mkdir()
        g.config = MyConfig()
        g.config.mode3d, g.quiet = False, True
        from dxf2gcode.presentation.qt import application as module
        from dxf2gcode.presentation.qt import vispy_view
        from dxf2gcode.presentation.qt.canvas2d import MyGraphicsScene
        from dxf2gcode.presentation.qt.generated.dxf2gcode_ui6 import Ui_MainWindow
        module.Ui_MainWindow, module.MyGraphicsScene = Ui_MainWindow, MyGraphicsScene
        vispy_view.VispyView = BenchmarkView
        g.folder = str(Path(folder)/'config')
        QtCore.QSettings.setDefaultFormat(QtCore.QSettings.Format.IniFormat)
        QtCore.QSettings.setPath(QtCore.QSettings.Format.IniFormat, QtCore.QSettings.Scope.UserScope, folder)
        app = QApplication([])
        from PyQt6.QtCore import QT_VERSION_STR, PYQT_VERSION_STR
        report.update(qt=QT_VERSION_STR, pyqt=PYQT_VERSION_STR)
        window = module.MainWindow(app)
        g.window = window
        window.showNormal()
        window.resize(1280, 900)
        app.processEvents()
        module.options = SimpleNamespace(post_pro=window.MyPostProcessor.output_text[0])
        window.filename = str(args.drawing.resolve())
        checkpoint('before_load')
        started = perf_counter()
        assert window.load(), 'DXF load failed'
        report['load_ms'] = round((perf_counter()-started)*1000, 2)
        panel, band = window.machining_panel, window.view_comparison
        before = panel.binding.project.to_dict()
        checkpoint('after_load')

        def render():
            frame = renderer.canvas.render()
            assert frame[..., :3].min() < 150, 'Empty frame'
            return frame

        def timed(name, action, count=None):
            for index in range(2):
                action(index)
                render()
            samples, updates = [], []
            for index in range(count or args.samples):
                started = perf_counter()
                action(index)
                updates.append((perf_counter()-started)*1000)
                render()
                samples.append((perf_counter()-started)*1000)
            report['measurements'][name] = dict(
                update_median_ms=round(median(updates), 2),
                frame_median_ms=round(median(samples), 2),
                frame_p95_ms=round(float(np.percentile(samples, 95)), 2),
                frame_max_ms=round(max(samples), 2), count=len(samples),
                visuals=len(renderer.nodes))
            checkpoint(name)
            print(name, report['measurements'][name], flush=True)

        renderer = None
        try:
            started = perf_counter()
            band.activate('plane')
            renderer = band.renderer
            assert isinstance(renderer, BenchmarkView), 'Renderer failed or fell back'
            app.processEvents()
            render()
            report['first_view_ms'] = round((perf_counter()-started)*1000, 2)
            report.update(gl_renderer=str(gloo.gl.glGetParameter(gloo.gl.GL_RENDERER)),
                gl_version=str(gloo.gl.glGetParameter(gloo.gl.GL_VERSION)),
                logical_canvas=[renderer.viewport().width(), renderer.viewport().height()],
                framebuffer=list(render().shape), dpr=renderer.viewport().devicePixelRatioF(),
                geometries=sum(p.kind == 'geometry' for p in renderer.snapshot.paths),
                operations=sum(p.kind == 'operation' for p in renderer.snapshot.paths),
                segments=sum(len(p.projected(False)) for p in renderer.snapshot.paths),
                initial_visuals=len(renderer.nodes))
            checkpoint('first_view')
            operation_ids = [p.identity for p in renderer.snapshot.paths if p.kind == 'operation']
            assert operation_ids

            def select(ids):
                panel.busy = True
                try:
                    panel.tree.clearSelection()
                    panel.tree.setCurrentItem(panel.entry_items[ids[0]] if ids else None)
                    for identity in ids:
                        panel.entry_items[identity].setSelected(True)
                finally:
                    panel.busy = False
                panel.selection_changed()

            def pan(index, rebuild=True):
                x, y = renderer.camera.rect.pos
                w, h = renderer.camera.rect.size
                renderer.camera.rect = (x+w*.002*(1 if index % 2 else -1), y, w, h)
                if rebuild:
                    renderer.redraw()

            def zoom(index):
                renderer.camera.zoom(1.01 if index % 2 else 1/1.01)
                renderer.redraw()

            timed('idle', lambda index: None)
            if args.clicks_only:
                from PyQt6.QtTest import QTest
                from dxf2gcode.presentation.qt.qt_compat.QtWidgets import QMenu
                from unittest.mock import patch
                path = next(p for p in renderer.snapshot.paths if p.kind == 'operation')
                a, b, _ = next(segment for segment in path.projected(False) if segment[2] == 'cut')
                midpoint = tuple((a[i]+b[i])/2 for i in range(3))
                def click(index, blank=False):
                    position = QtCore.QPoint(5, 5) if blank else QtCore.QPoint(*map(round, renderer.project(midpoint)))
                    QTest.mouseClick(renderer.viewport(), QtCore.Qt.MouseButton.LeftButton, pos=position)
                # Deterministic choice for overlapping operations in this test;
                # production still offers the normal disambiguation menu.
                with patch.object(QMenu, 'exec', lambda menu, *unused: menu.actions()[0]):
                    timed('canvas_select', click, 3)
                    timed('canvas_clear', lambda index: (click(index), click(index, blank=True)), 3)
            elif args.camera_only:
                from contextlib import ExitStack
                from unittest.mock import patch
                for label, identities in (('unselected', []), ('multiple', operation_ids[:24])):
                    select(identities)
                    render()
                    renderer.timer.stop()
                    with ExitStack() as stack:
                        uploads = [stack.enter_context(patch.object(node, 'set_data', wraps=node.set_data)) for node in renderer.nodes.values()]
                        timed('pan_camera_only_'+label, lambda index: pan(index, rebuild=False))
                        assert not any(upload.call_count for upload in uploads), 'Camera-only motion uploaded geometry'
            else:
                timed('pan_unselected', pan)
                timed('zoom_unselected', zoom)
                timed('selection_single', lambda index: select([operation_ids[index % len(operation_ids)]]), 8)
                timed('selection_multiple', lambda index: select(operation_ids[index % 2::2][:24]), 8)
                timed('pan_multiple', pan)
                timed('zoom_multiple', zoom)
                select(operation_ids)
                timed('pan_all_selected', pan)
            renderer.grab().save(str(args.output.with_suffix('.png')))
            assert panel.binding.project.to_dict() == before, 'Benchmark changed project data'
            report['project_unchanged'] = True
            report['status'] = 'passed'
        except Exception as error:
            report['status'], report['error'] = 'stopped', str(error)
            print('STOPPED:', error, flush=True)
        finally:
            checkpoint('end', enforce=False)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(report, indent=2), encoding='utf-8')
            print('RESULT', args.output, report['status'], flush=True)
            window.close()
            app.processEvents()
            faulthandler.cancel_dump_traceback_later()
    return 0 if report['status'] == 'passed' else 2


if __name__ == '__main__':
    sys.exit(main())
