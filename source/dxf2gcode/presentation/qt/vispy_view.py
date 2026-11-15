"""Optional VisPy viewport. Imports GPU packages only on explicit activation."""

from dxf2gcode.presentation.qt.qt_compat import QtCore
from dxf2gcode.presentation.qt.qt_compat.QtGui import QColor, QPainter, QPen
from dxf2gcode.presentation.qt.qt_compat.QtWidgets import QWidget, QVBoxLayout
from dxf2gcode.application.view_scene import ViewScene, preview_tool_bodies, tool_cylinder_mesh
from dxf2gcode.presentation.qt.view_interaction import ViewInteraction, dash_segments




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
            segments = path.projected(owner.spatial)
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


class VispyView(QWidget, ViewInteraction):
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
        self.tools_visible, self.tool_nodes, self._tool_key = False, {}, None
        self.geometry_selection = {}
        self.pick_widget = self.canvas.native
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas.native)
        self.view = self.canvas.central_widget.add_view()
        self.camera = scene.cameras.TurntableCamera(fov=0, elevation=30, azimuth=30, up='+z')
        self.spatial_camera = self.camera
        self.plane_camera = scene.cameras.PanZoomCamera(aspect=1)
        self.view.camera = self.camera
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
        self.timer.start(20)

    def set_scene(self, snapshot, selected):
        changed = snapshot is not self.snapshot
        if changed:
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
        self.redraw()
        if self.spatial not in self.fitted or changed and not self.snapshot.paths:
            if self.fit():
                self.fitted.add(self.spatial)

    def set_spatial(self, spatial):
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

    def fit(self):
        points = [p for path in self.snapshot.paths if path.enabled or self.show_disabled
                  for a, b, _ in path.projected(self.spatial) for p in (a, b)]
        if self.tools_visible:
            points.extend(p for body in preview_tool_bodies(self.snapshot, self.selected, self.spatial) for p in body.corners)
        if not points:
            return False
        bounds = [(min(p[i] for p in points), max(p[i] for p in points)) for i in range(3)]
        bounds = [(a-.5, b+.5) if a == b else (a, b) for a, b in bounds]
        self.camera.set_range(x=bounds[0], y=bounds[1], z=bounds[2], margin=.08)
        self.schedule()
        return True

    def project(self, point):
        mapped = self.view.scene.node_transform(self.canvas.scene).map(point)
        return mapped[0]/mapped[3], mapped[1]/mapped[3]


    def redraw(self):
        if not self.isVisible():
            return
        try:
            self._redraw()
        except Exception as error:
            self.failure(error)

    def _redraw(self):
        import numpy as np
        groups = {}
        scale = self.camera.scale_factor if self.spatial else self.camera.rect.height
        unit = max(float(scale or 1.) / max(1, self.height()), 1e-12)
        for path in self.snapshot.paths:
            if not path.enabled and not self.show_disabled:
                continue
            roles = {}
            for a, b, role in path.projected(self.spatial):
                roles.setdefault(role, []).append((a, b))
            for role, pairs in roles.items():
                pen = self.path_style(path, role)
                color, width = pen.color().getRgbF(), pen.widthF()
                dashed = pen.style() != QtCore.Qt.PenStyle.SolidLine
                points = dash_segments(pairs, unit, pen.style() == QtCore.Qt.PenStyle.DotLine) if dashed else [p for pair in pairs for p in pair]
                groups.setdefault((color, width), []).extend(points)
        for key, node in self.nodes.items():
            node.visible = key in groups
        for key, points in groups.items():
            if not points:
                continue
            if key not in self.nodes:
                node = self.scene_api.visuals.Line(parent=self.view.scene, method='gl',
                    connect='segments', antialias=True)
                node.set_gl_state(depth_test=True, blend=True)
                self.nodes[key] = node
            self.nodes[key].visible = True
            self.nodes[key].set_data(pos=np.asarray(points, dtype=np.float32),
                                     color=key[0], width=key[1])
        self.labels.setGeometry(self.canvas.native.rect())
        self.labels.raise_()
        self.labels.update()
        self.canvas.update()

    def set_tools_visible(self, visible):
        self.tools_visible = visible
        self.update_tools()
        self.canvas.update()

    def update_tools(self):
        bodies = preview_tool_bodies(self.snapshot, self.selected, self.spatial) if self.tools_visible else ()
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
        kind = event.type()
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
        self.timer.stop()
        self.canvas.close()
