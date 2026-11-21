"""Optional VisPy viewport. Imports GPU packages only on explicit activation."""

from dxf2gcode.presentation.qt.qt_compat import QtCore
from dxf2gcode.presentation.qt.qt_compat.QtGui import QColor, QPainter, QPen
from dxf2gcode.presentation.qt.qt_compat.QtWidgets import QWidget, QVBoxLayout
from dxf2gcode.application.view_scene import ViewScene, preview_tool_bodies, tool_cylinder_mesh
from dxf2gcode.presentation.qt.view_interaction import ViewInteraction, dash_segments


def connected_chains(pairs):
    """Join adjacent pieces without connecting independent paths or dash gaps."""
    chain = []
    for start, end in pairs:
        if chain and start != chain[-1]:
            if len(chain) > 1:
                yield chain
            chain = []
        if not chain:
            chain.append(start)
        if end != chain[-1]:
            chain.append(end)
    if len(chain) > 1:
        yield chain


def plane_dash_pairs(pairs):
    """Apply a single dash pattern to coincident XY segments of one role."""
    seen = set()
    for start, end in pairs:
        a, b = start[:2], end[:2]
        key = tuple(sorted((tuple(round(v, 12) for v in a), tuple(round(v, 12) for v in b))))
        if key[0] == key[1] or key in seen:
            continue
        seen.add(key)
        yield (*a, 0.), (*b, 0.)


def vispy_path_pen(view, path, role):
    """Original geometry has no machining colour; emphasize selection scope."""
    from dxf2gcode.presentation.qt.canvas2d import ShapeGUI
    selected = path.identity in view.selected
    if path.kind == 'region':
        pen = QPen(ShapeGUI.PEN_BREAK)
        pen.setWidthF(2 if selected else .6)
        return pen
    if path.kind == 'operation':
        # Keep semantic colours/patterns but do not let the parameter editor's
        # active operation override the full-vs-partial selection rule.
        pen = view.panel.canvas_preview.path_pen(role, path.enabled, False, selected)
        count, total = view.geometry_selection.get(path.geometry, (0, 0))
        if not selected or count == total:
            pen.setWidthF(.6)
        else:
            pen.setWidthF(pen.widthF()+1.)
        return pen
    count, total = view.geometry_selection.get(path.identity, (0, 0))
    partial = 0 < count < total
    source = view.panel.binding.sources.get(path.identity)
    selected_original = bool(count) or source is not None and source.isSelected()
    disabled = source is not None and source.isDisabled()
    if disabled:
        pen = QPen(ShapeGUI.PEN_SELECT_DISABLED if selected_original else ShapeGUI.PEN_NORMAL_DISABLED)
    else:
        pen = QPen(ShapeGUI.PEN_SELECT if selected_original else ShapeGUI.PEN_NORMAL)
    pen.setWidthF(3. if selected_original and not partial else 1.)
    if partial:
        pen.setStyle(QtCore.Qt.PenStyle.DotLine)
    return pen



class ViewLabels(QWidget):
    def __init__(self, owner, parent):
        super().__init__(parent)
        self.owner = owner
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)

    def paintEvent(self, event):
        owner = self.owner
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        for path in owner.snapshot.paths:
            if path.identity not in owner.selected or path.kind != 'operation':
                continue
            segments = owner.projected_segments(path)
            if not segments:
                continue
            points = (segments[0][0], segments[-1][1])
            for point, text, role in zip(points, ('S', 'E'), ('lead_in', 'lead_out')):
                x, y = owner.project(point)
                painter.setPen(QPen(owner.panel.canvas_preview.path_pen(role).color(), 2))
                painter.drawEllipse(QtCore.QPointF(x, y), 4, 4)
                painter.drawText(QtCore.QPointF(x+6, y-4), text)
            x, y = owner.project(points[0])
            painter.setPen(QColor('black'))
            painter.drawText(QtCore.QPointF(x+8, y+16), path.title)
            if path.diagnostic:
                painter.setPen(QColor('red'))
                painter.drawText(QtCore.QPointF(x+8, y+32), path.diagnostic)
        if not owner.spatial:
            owner.panel.modifiers.paint(painter, owner)


class VispyView(QWidget, ViewInteraction):
    def path_style(self, path, role):
        return vispy_path_pen(self, path, role)

    def __init__(self, panel, failure):
        super().__init__(panel.window)
        handler = QtCore.qInstallMessageHandler(None)
        QtCore.qInstallMessageHandler(handler)
        try:
            import vispy
            vispy.use(app='pyqt6')
            from vispy import scene
            self.canvas = scene.SceneCanvas(keys=None, bgcolor='white', parent=self)
        finally:
            # VisPy installs a process-wide Qt logger. Keep the application's
            # existing handler, including during native Quick window teardown.
            QtCore.qInstallMessageHandler(handler)
        self.scene_api = scene
        class ToolMesh(scene.visuals.Mesh):
            def draw(self):
                from vispy import gloo
                try:
                    super().draw()
                finally:
                    # GL clear also obeys depth_mask. Do not leave the next
                    # frame's depth clear disabled after a transparent body.
                    gloo.set_state(depth_mask=True, cull_face=False)
        self.tool_visual_type = ToolMesh
        self.panel, self.failure = panel, failure
        self.snapshot, self.selected = ViewScene(), set()
        self.spatial, self.show_disabled = True, False
        self.nodes = {}
        self._projections, self._dash_cache, self._uploads = {}, {}, {}
        self._covered_cuts = {}
        self._plane_dash_pairs = {}
        self._hit_data, self._hit_screen = None, {}
        self._scene_revision = 0
        self.tools_visible, self.tool_nodes, self._tool_key = False, {}, None
        self.geometry_selection = {}
        self.pick_widget = self.canvas.native
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas.native)
        self.view = self.canvas.central_widget.add_view()
        self.camera = scene.cameras.TurntableCamera(fov=0, elevation=30, azimuth=30, up='+z')
        self.spatial_camera = self.camera
        self.plane_camera = scene.cameras.PanZoomCamera(aspect=1, up='+z')
        self.view.camera = self.camera
        self.top_transition = QtCore.QVariantAnimation(self)
        self.top_transition.setStartValue(0.)
        self.top_transition.setEndValue(1.)
        self.top_transition.setDuration(400)
        self.top_transition.setEasingCurve(QtCore.QEasingCurve.Type.InOutCubic)
        self.top_transition.valueChanged.connect(self._animate_top_frame)
        self.top_transition.finished.connect(self.finish_top_transition)
        self._top_start = None
        self.labels = ViewLabels(self, self.canvas.native)
        self.labels.show()
        self.canvas.native.installEventFilter(self)
        self.press = None
        self.timer = QtCore.QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.redraw)
        self.canvas.events.mouse_move.connect(lambda event: self.schedule())
        self.canvas.events.mouse_wheel.connect(lambda event: self.schedule())
        self.canvas.events.resize.connect(lambda event: self.schedule())
        self.fitted = set()

    def schedule(self):
        self.labels.setGeometry(self.canvas.native.rect())
        self.labels.update()
        if not self.timer.isActive():
            self.timer.start(20)

    def set_scene(self, snapshot, selected):
        changed = snapshot is not self.snapshot
        if changed:
            self._scene_revision += 1
            self._projections.clear()
            self._dash_cache.clear()
            self._covered_cuts.clear()
            self._plane_dash_pairs.clear()
            self._hit_data = None
            self._hit_screen.clear()
            for node in self.tool_nodes.values():
                node.parent = None
            self.tool_nodes.clear()
            self._tool_key = None
        self.snapshot, self.selected = snapshot, set(selected)
        self.geometry_selection = {}
        for path in snapshot.paths:
            if path.kind == 'operation':
                counts = self.geometry_selection.setdefault(path.geometry, [0, 0])
                counts[0] += path.identity in self.selected
                counts[1] += 1
        self.show_disabled = self.panel.window.ui.actionShowDisabledPaths.isChecked()
        self.update_tools()
        if self.spatial not in self.fitted or changed and not self.snapshot.paths:
            if self.fit():
                self.fitted.add(self.spatial)
        self.redraw()

    def set_spatial(self, spatial):
        self.cancel_top_transition()
        if spatial == self.spatial:
            return
        self.spatial = spatial
        self.update_tools()
        self.camera = self.spatial_camera if spatial else self.plane_camera
        self.view.camera = self.camera
        if spatial not in self.fitted:
            if self.fit():
                self.fitted.add(spatial)
        self.redraw()

    def animate_top(self):
        """Move the current orbit camera to the fixed view before handing off."""
        width, height = self.view.size
        if not self.spatial or min(width, height) <= 0 or not self.snapshot.paths:
            return False
        if self._top_start is not None:
            return True
        if False not in self.fitted:
            bounds = self.scene_bounds()
            if not bounds:
                return False
            (left, right), (bottom, top), _ = bounds
            w, h = right-left, top-bottom
            self.plane_camera.rect = (left-.08*w, bottom-.08*h, 1.16*w, 1.16*h)
            self.fitted.add(False)
        self.press = None
        self._top_start = self.spatial_camera.get_state()
        self.top_transition.start()
        return True

    def _animate_top_frame(self, progress):
        start = self._top_start
        if start is None:
            return
        width, height = self.view.size
        if min(width, height) <= 0:
            return
        rect = self.plane_camera.rect
        center = (*rect.center, start['center'][2])
        scale = max(rect.width/width, rect.height/height)*min(width, height)
        def lerp(a, b):
            return a+(b-a)*progress
        def straighten(angle):
            return lerp((angle+180.) % 360.-180., 0.)
        self.spatial_camera.set_state(
            center=tuple(lerp(a, b) for a, b in zip(start['center'], center)),
            scale_factor=lerp(start['scale_factor'], scale),
            elevation=lerp(start['elevation'], 90.), azimuth=straighten(start['azimuth']),
            roll=straighten(start['roll']))
        self.labels.update()

    def cancel_top_transition(self):
        if self._top_start is not None:
            self.top_transition.stop()
            self.spatial_camera.set_state(self._top_start)
            self._top_start = None

    def finish_top_transition(self):
        if self._top_start is not None:
            self.set_spatial(False)

    def scene_bounds(self):
        points = [p for path, segments, roles in self.projected_data().values()
                  if path.enabled or self.show_disabled
                  for a, b, _ in segments for p in (a, b)]
        if self.tools_visible:
            points.extend(p for body in preview_tool_bodies(self.snapshot, self.selected) for p in body.corners)
        if not points:
            return ()
        bounds = [(min(p[i] for p in points), max(p[i] for p in points)) for i in range(3)]
        return [(a-.5, b+.5) if a == b else (a, b) for a, b in bounds]

    def fit(self):
        bounds = self.scene_bounds()
        if not bounds:
            return False
        self.camera.set_range(x=bounds[0], y=bounds[1], z=bounds[2], margin=.08)
        self.schedule()
        return True

    def projected_data(self):
        """Share the XYZ positions and semantic arrays between both cameras."""
        import numpy as np
        if not self._projections and self.snapshot.paths:
            data = {}
            for path in self.snapshot.paths:
                segments = path.projected(True)
                pairs = {}
                for a, b, role in segments:
                    pairs.setdefault(role, []).append((a, b))
                roles = [(role, values, np.asarray([p for pair in values for p in pair], dtype=np.float32))
                         for role, values in pairs.items()]
                data[path.identity] = (path, segments, roles)
            if data:
                def segment_key(pair):
                    return tuple(sorted(tuple(round(float(v), 9) for v in p[:2]) for p in pair))
                originals = {path.identity: {segment_key((a, b)) for a, b, _ in segments}
                             for path, segments, roles in data.values() if path.kind == 'geometry'}
                self._covered_cuts = {}
                for path, segments, roles in data.values():
                    if path.kind != 'operation' or path.geometry not in originals:
                        continue
                    for role, pairs, points in roles:
                        if role == 'cut':
                            uncovered = [pair for pair in pairs if segment_key(pair) not in originals[path.geometry]]
                            self._covered_cuts[path.identity] = (uncovered,
                                np.asarray([p for pair in uncovered for p in pair], dtype=np.float32))
            self._projections = data
        return self._projections

    def projected_segments(self, path):
        return self.projected_data()[path.identity][1]

    def path_hits(self, point, kinds=('operation', 'region')):
        """Vectorized screen picking with the same camera transform as drawing.

        A four-point homogeneous basis fingerprints the current linear camera
        transform, covering pan, zoom, rotation, viewport and device scaling.
        No per-endpoint traversal of the VisPy scene graph is needed.
        """
        import numpy as np
        if self._hit_data is None:
            paths, points, offset = [], [], 0
            for path, segments, roles in self.projected_data().values():
                vertices = [p for a, b, role in segments for p in (a, b)]
                count = len(vertices)//2
                paths.append((path, offset, offset+count))
                points.extend(vertices)
                offset += count
            self._hit_data = paths, np.asarray(points, dtype=np.float64).reshape(-1, 3)
        paths, points = self._hit_data
        if not len(points):
            return ()
        transform = self.view.scene.node_transform(self.canvas.scene)
        basis = transform.map(((0., 0., 0., 1.), (1., 0., 0., 1.),
                               (0., 1., 0., 1.), (0., 0., 1., 1.)))
        key = tuple(basis.ravel())
        cached = self._hit_screen.get(self.spatial)
        if cached is None or cached[0] != key:
            mapped = transform.map(points)
            with np.errstate(divide='ignore', invalid='ignore'):
                xy = mapped[:, :2]/mapped[:, 3:4]
            starts, ends = xy[::2], xy[1::2]
            delta = ends-starts
            lengths = np.einsum('ij,ij->i', delta, delta)
            cached = key, starts, delta, lengths
            self._hit_screen[self.spatial] = cached
        _, starts, delta, lengths = cached
        relative = (point.x(), point.y())-starts
        t = np.divide(np.einsum('ij,ij->i', relative, delta), lengths,
                      out=np.zeros_like(lengths), where=lengths > 0)
        residual = relative-np.clip(t, 0., 1.)[:, None]*delta
        distances = np.einsum('ij,ij->i', residual, residual)
        distances[~np.isfinite(distances)] = float('inf')
        hits = []
        for path, start, end in paths:
            if path.kind not in kinds or not path.enabled and not self.show_disabled or start == end:
                continue
            distance = float(np.min(distances[start:end]))
            if distance <= 7.**2:
                hits.append((distance, path.identity))
        return tuple(identity for distance, identity in sorted(hits, key=lambda hit: hit[0]))

    def project(self, point):
        mapped = self.view.scene.node_transform(self.canvas.scene).map(point)
        return float(mapped[0]/mapped[3]), float(mapped[1]/mapped[3])

    def viewport(self):
        """Qt surface hosting the shared tab dimension editor."""
        return self.canvas.native

    def tab_project(self, xy):
        return QtCore.QPointF(*self.project((xy[0], xy[1], 0.)))

    def tab_scene_point(self, position):
        """Inverse of tab_project in the fixed XY editing plane."""
        transform = self.view.scene.node_transform(self.canvas.scene)
        mapped = transform.imap((position.x(), position.y(), 0., 1.))
        return float(mapped[0]/mapped[3]), float(mapped[1]/mapped[3])


    def redraw(self):
        if not self.isVisible():
            return
        try:
            self._redraw()
        except Exception as error:
            self.failure(error)

    def _redraw(self):
        import numpy as np
        groups, signatures = {}, {}
        scale = self.camera.scale_factor if self.spatial else self.camera.rect.height
        unit = max(float(scale or 1.) / max(1, self.height()), 1e-12)
        previous_unit, dash_cache = self._dash_cache.get(self.spatial, (None, {}))
        if unit != previous_unit:
            dash_cache = {}
        self._dash_cache[self.spatial] = (unit, dash_cache)
        for path, segments, roles in self.projected_data().values():
            # The shared Qt overlay owns region outlines and live gestures in
            # the editing plane; avoid a stale second outline underneath it.
            if path.kind == 'region' and not self.spatial:
                continue
            if not path.enabled and not self.show_disabled:
                continue
            # In the editing plane, selection must determine stacking rather
            # than equal-depth GL fragments or the order styles were created.
            order = (2 if path.identity in self.selected else 0) if path.kind == 'operation' else 1
            if self.spatial:
                order = 0
            for role, pairs, solid_points in roles:
                pen = self.path_style(path, role)
                color, width = pen.color().getRgbF(), pen.widthF()
                dashed = pen.style() != QtCore.Qt.PenStyle.SolidLine
                covered = False
                if not self.spatial and role == 'cut' and path.identity not in self.selected and path.kind == 'operation':
                    source = self.panel.binding.sources.get(path.geometry)
                    if not self.geometry_selection.get(path.geometry, (0, 0))[0] and not (source and source.isSelected()):
                        pairs, solid_points = self._covered_cuts.get(path.identity, (pairs, solid_points))
                        covered = True
                points = solid_points
                if dashed:
                    dash_key = (path.identity, role, pen.style(), covered)
                    if dash_key not in dash_cache:
                        if not self.spatial:
                            pair_key = (path.identity, role, covered)
                            if pair_key not in self._plane_dash_pairs:
                                self._plane_dash_pairs[pair_key] = tuple(plane_dash_pairs(pairs))
                            pairs = self._plane_dash_pairs[pair_key]
                        dash_cache[dash_key] = np.asarray(dash_segments(pairs, unit,
                            pen.style() == QtCore.Qt.PenStyle.DotLine,
                            align_depth_passes=self.spatial), dtype=np.float32)
                    points = dash_cache[dash_key]
                if not len(points):
                    continue
                key = (order, color, width or 1., 'gl', self.spatial)
                groups.setdefault(key, []).append(points)
                signatures.setdefault(key, []).append((path.identity, role, pen.style(), covered, unit if dashed else None))
        for key in set(self.nodes)-set(groups):
            self.nodes.pop(key).parent = None
            self._uploads.pop(key, None)
        for key, arrays in groups.items():
            if not any(len(points) for points in arrays):
                continue
            if key not in self.nodes:
                node = self.scene_api.visuals.Line(parent=self.view.scene, method='gl',
                    connect='segments', antialias=True)
                self.nodes[key] = node
            node = self.nodes[key]
            node.visible = True
            node.order = key[0]
            node.set_gl_state(depth_test=self.spatial, blend=True,
                              blend_func=('src_alpha', 'one_minus_src_alpha'))
            signature = self._scene_revision, tuple(signatures[key])
            if self._uploads.get(key) != signature:
                node.set_data(pos=np.concatenate([p for p in arrays if len(p)]),
                              color=key[1], width=key[2])
                self._uploads[key] = signature
        self.labels.setGeometry(self.canvas.native.rect())
        self.labels.raise_()
        self.labels.update()
        self.canvas.update()

    def set_tools_visible(self, visible):
        self.tools_visible = visible
        self.update_tools()
        self.canvas.update()

    def update_tools(self):
        bodies = preview_tool_bodies(self.snapshot, self.selected) if self.tools_visible else ()
        if bodies == self._tool_key:
            return
        self._tool_key = bodies
        for node in self.tool_nodes.values():
            node.visible = False
        if not bodies:
            return
        import numpy as np
        from vispy.geometry import MeshData
        from vispy.visuals.transforms import STTransform
        vertices, _, faces = tool_cylinder_mesh()
        data = MeshData(vertices=np.asarray(vertices, dtype=np.float32), faces=np.asarray(faces, dtype=np.uint32))
        for body in bodies:
            if body.identity not in self.tool_nodes:
                node = self.tool_visual_type(meshdata=data, color=(.3, .55, .75, .25),
                                             shading='smooth', parent=self.view.scene)
                node.set_gl_state(blend=True, depth_test=True, depth_mask=False,
                                  cull_face='back', blend_func=('src_alpha', 'one_minus_src_alpha'))
                node.order = 10
                self.tool_nodes[body.identity] = node
            node = self.tool_nodes[body.identity]
            node.transform = STTransform(scale=(body.radius, body.radius, body.length), translate=body.position)
            node.visible = True

    def eventFilter(self, watched, event):
        if not self.spatial and self.panel.modifiers.eventFilter(watched, event):
            self.press = None
            return True
        kind = event.type()
        if self._top_start is not None and kind in (QtCore.QEvent.Type.MouseButtonPress,
                QtCore.QEvent.Type.MouseButtonRelease, QtCore.QEvent.Type.MouseButtonDblClick,
                QtCore.QEvent.Type.MouseMove, QtCore.QEvent.Type.Wheel):
            return True
        if kind == QtCore.QEvent.Type.MouseButtonPress:
            self.press = event.pos()
        elif kind == QtCore.QEvent.Type.MouseButtonRelease and event.button() == QtCore.Qt.MouseButton.LeftButton:
            if self.press is not None and (event.pos()-self.press).manhattanLength() <= 4:
                self.pick(event.pos(), bool(event.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier))
        return False


    def verify(self):
        """Force a real render: successful import is not a capability check."""
        from vispy import gloo
        self.canvas.set_current()
        if not gloo.gl.glGetParameter(gloo.gl.GL_VERSION):
            raise RuntimeError('OpenGL context unavailable')
        self.canvas.render()

    def dispose(self):
        self.cancel_top_transition()
        self.timer.stop()
        self._projections.clear()
        self._dash_cache.clear()
        self._uploads.clear()
        self._covered_cuts.clear()
        self._plane_dash_pairs.clear()
        self._hit_data = None
        self._hit_screen.clear()
        self.canvas.close()
