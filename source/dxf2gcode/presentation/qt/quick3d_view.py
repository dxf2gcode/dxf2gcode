"""Qt Quick 3D adapter with a native window, independent of VisPy's GL context."""

from array import array
from pathlib import Path

from PyQt6 import QtCore
from PyQt6.QtGui import QQuaternion, QVector3D
from PyQt6.QtQml import QQmlEngine
from PyQt6.QtQuick import QQuickView, QSGRendererInterface
from PyQt6.QtQuick3D import QQuick3DGeometry, QQuick3DObject
from PyQt6.QtWidgets import QWidget, QVBoxLayout

from dxf2gcode.application.view_scene import ViewScene, preview_tool_bodies, tool_cylinder_mesh
from dxf2gcode.presentation.qt.view_interaction import ViewInteraction, dash_segments


def qt_point(point):
    """Drawing Z-up to Qt Y-up; orthogonal conversion, never an XY offset."""
    return QVector3D(point[0], point[2], -point[1])


class LineGeometry(QQuick3DGeometry):
    """Screen-width ribbons: portable thick/dashed lines on all RHI backends."""
    def __init__(self):
        super().__init__()
        self.setPrimitiveType(self.PrimitiveType.Triangles)
        self.setStride(28)
        attribute = self.Attribute
        self.addAttribute(attribute.Semantic.PositionSemantic, 0, attribute.ComponentType.F32Type)
        self.addAttribute(attribute.Semantic.ColorSemantic, 12, attribute.ComponentType.F32Type)
        self._groups, self._segments = None, ()

    def prepare(self, groups):
        """Convert endpoints and compute bounds only when styled data changes."""
        if groups is self._groups:
            return
        segments = []
        lower, upper = [float('inf')]*3, [-float('inf')]*3
        self._max_width = 0.
        for (color, width), points in groups.items():
            self._max_width = max(self._max_width, width)
            for start, end in zip(points[::2], points[1::2]):
                a, b = (start[0], start[2], -start[1]), (end[0], end[2], -end[1])
                segments.append((color, width, a, b))
                for i in range(3):
                    lower[i] = min(lower[i], a[i], b[i])
                    upper[i] = max(upper[i], a[i], b[i])
        self._groups, self._segments = groups, segments
        self._lower, self._upper = lower, upper

    def upload(self, groups, rotation, zoom):
        values = array('f')
        self.prepare(groups)
        right_vector = rotation.rotatedVector(QVector3D(1, 0, 0))
        up_vector = rotation.rotatedVector(QVector3D(0, 1, 0))
        right = right_vector.x(), right_vector.y(), right_vector.z()
        up = up_vector.x(), up_vector.y(), up_vector.z()
        for color, width, a, b in self._segments:
            dx, dy, dz = (b[i]-a[i] for i in range(3))
            x = dx*right[0]+dy*right[1]+dz*right[2]
            y = dx*up[0]+dy*up[1]+dz*up[2]
            length = (x*x+y*y)**.5
            half = width/zoom/2
            if length > 1e-12:
                offset = tuple((-y*right[i]+x*up[i])*half/length for i in range(3))
            else:
                offset = tuple(v*half for v in right)
                b = tuple(b[i]+up[i]*width/zoom for i in range(3))
            p = tuple(a[i]+offset[i] for i in range(3))
            q = tuple(a[i]-offset[i] for i in range(3))
            r = tuple(b[i]+offset[i] for i in range(3))
            s = tuple(b[i]-offset[i] for i in range(3))
            values.extend((*p, *color, *q, *color, *r, *color,
                           *r, *color, *q, *color, *s, *color))
        self.setVertexData(QtCore.QByteArray(values.tobytes()))
        margin = 1.5*self._max_width/zoom
        self.setBounds(QVector3D(*(v-margin for v in self._lower)) if values else QVector3D(),
                       QVector3D(*(v+margin for v in self._upper)) if values else QVector3D())
        self.update()


class ToolGeometry(QQuick3DGeometry):
    def __init__(self):
        super().__init__()
        vertices, normals, faces = tool_cylinder_mesh()
        data = array('f')
        for vertex, normal in zip(vertices, normals):
            data.extend((vertex[0], vertex[2], -vertex[1], normal[0], normal[2], -normal[1]))
        self.setStride(24)
        self.setPrimitiveType(self.PrimitiveType.Triangles)
        attribute = self.Attribute
        self.addAttribute(attribute.Semantic.PositionSemantic, 0, attribute.ComponentType.F32Type)
        self.addAttribute(attribute.Semantic.NormalSemantic, 12, attribute.ComponentType.F32Type)
        self.addAttribute(attribute.Semantic.IndexSemantic, 0, attribute.ComponentType.U32Type)
        self.setVertexData(QtCore.QByteArray(data.tobytes()))
        self.setIndexData(QtCore.QByteArray(array('I', (i for face in faces for i in face)).tobytes()))
        self.setBounds(QVector3D(-1, 0, -1), QVector3D(1, 1, 1))
        self.update()


class Quick3DView(QWidget, ViewInteraction):
    cameraChanged = QtCore.pyqtSignal()
    annotationsChanged = QtCore.pyqtSignal()
    toolsChanged = QtCore.pyqtSignal()

    def __init__(self, panel, failure):
        super().__init__(panel.window)
        self.panel, self.failure = panel, failure
        self.snapshot, self.selected = ViewScene(), set()
        self.geometry_selection, self.fitted = {}, set()
        self._projections, self._groups = {}, None
        self._groups_key = self._mesh_key = self._camera_key = None
        self._label_data = None
        self.tools_visible, self._tool_bodies = False, []
        self.spatial, self.show_disabled = True, False
        self.states = {
            True: dict(center=QVector3D(), zoom=1., pitch=-35., yaw=30.),
            False: dict(center=QVector3D(), zoom=1., pitch=-90., yaw=0.)}
        self._distance, self._annotations = 1000., []
        self.frame_ready, self.verified = False, False
        self.disposed = False
        self._mesh = LineGeometry()
        self._tool_mesh = ToolGeometry()
        QQmlEngine.setObjectOwnership(self._mesh, QQmlEngine.ObjectOwnership.CppOwnership)
        QQmlEngine.setObjectOwnership(self._tool_mesh, QQmlEngine.ObjectOwnership.CppOwnership)
        self.view = QQuickView()
        self.view.setResizeMode(QQuickView.ResizeMode.SizeRootObjectToView)
        self.view.rootContext().setContextProperty('viewBridge', self)
        self.view.sceneGraphError.connect(lambda code, message: self.report_failure(message),
                                         QtCore.Qt.ConnectionType.QueuedConnection)
        self.view.statusChanged.connect(self.status_changed)
        self.view.frameSwapped.connect(self.first_frame, QtCore.Qt.ConnectionType.QueuedConnection)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.container = QWidget.createWindowContainer(self.view, self)
        self.pick_widget = self.container
        layout.addWidget(self.container)
        self.view.setSource(QtCore.QUrl.fromLocalFile(str(Path(__file__).parent / 'resources/view_comparison.qml')))
        if self.view.rootObject() is not None:
            model = self.view.rootObject().findChild(QQuick3DObject, 'toolpathModel')
            self._mesh.setParentItem(model)
            self._mesh.setParent(model)
            root = self.view.rootObject().findChild(QQuick3DObject, 'toolRoot')
            self._tool_mesh.setParentItem(root)
            self._tool_mesh.setParent(root)
        self.timer = QtCore.QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.redraw)
        self.view.widthChanged.connect(lambda value: self.schedule())
        self.view.heightChanged.connect(lambda value: self.schedule())
        self.ready_timeout = QtCore.QTimer(self)
        self.ready_timeout.setSingleShot(True)
        self.ready_timeout.timeout.connect(self.check_timeout)
        self.ready_timeout.start(3000)
        self.press = self.last = None
        self.dragged = False

    @property
    def state(self):
        return self.states[self.spatial]

    @QtCore.pyqtProperty(QQuick3DGeometry, constant=True)
    def mesh(self):
        return self._mesh

    @QtCore.pyqtProperty(QQuick3DGeometry, constant=True)
    def toolMesh(self):
        return self._tool_mesh

    @QtCore.pyqtProperty('QVariantList', notify=toolsChanged)
    def toolBodies(self):
        return self._tool_bodies

    def set_tools_visible(self, visible):
        self.tools_visible = visible
        self.update_tools()

    def update_tools(self):
        bodies = preview_tool_bodies(self.snapshot, self.selected, self.spatial) if self.tools_visible else ()
        values = [dict(x=b.position[0], y=b.position[1], z=b.position[2], radius=b.radius,
                       length=b.length) for b in bodies]
        if values != self._tool_bodies:
            self._tool_bodies = values
            self.toolsChanged.emit()
            self.view.update()

    @QtCore.pyqtProperty(QVector3D, notify=cameraChanged)
    def center(self):
        return self.state['center']

    @QtCore.pyqtProperty(QQuaternion, notify=cameraChanged)
    def cameraRotation(self):
        return QQuaternion.fromEulerAngles(self.state['pitch'], self.state['yaw'], 0)

    @QtCore.pyqtProperty(float, notify=cameraChanged)
    def zoom(self):
        return self.state['zoom']

    @QtCore.pyqtProperty(float, notify=cameraChanged)
    def distance(self):
        return self._distance

    @QtCore.pyqtProperty('QVariantList', notify=annotationsChanged)
    def annotations(self):
        return self._annotations

    def status_changed(self, status):
        if status == QQuickView.Status.Error:
            self.report_failure('\n'.join(error.toString() for error in self.view.errors()))

    def report_failure(self, message):
        # Do not destroy a QML engine during its own signal/slot invocation.
        if not self.disposed:
            QtCore.QTimer.singleShot(0, lambda: self.failure(RuntimeError(message)) if not self.disposed else None)

    def schedule(self):
        # Throttle instead of debouncing: a continuous mouse stream must not
        # postpone the frame until the user stops moving.
        if hasattr(self, 'timer') and not self.timer.isActive():
            self.timer.start(16)

    def set_scene(self, snapshot, selected):
        if snapshot is not self.snapshot:
            self._projections.clear()
        self.snapshot, self.selected = snapshot, set(selected)
        self._groups = self._label_data = None
        self.geometry_selection = {}
        for path in snapshot.paths:
            if path.kind == 'operation':
                counts = self.geometry_selection.setdefault(path.geometry, [0, 0])
                counts[0] += path.identity in self.selected
                counts[1] += 1
        self.show_disabled = self.panel.window.ui.actionShowDisabledPaths.isChecked()
        self.update_tools()
        if self.spatial not in self.fitted and self.fit():
            self.fitted.add(self.spatial)
        self.redraw()

    def set_spatial(self, spatial):
        if spatial != self.spatial:
            self._groups = self._label_data = None
        self.spatial = spatial
        self.update_tools()
        if spatial not in self.fitted and self.fit():
            self.fitted.add(spatial)
        self.redraw()

    def fit(self):
        points = [qt_point(p) for path in self.snapshot.paths if path.enabled or self.show_disabled
                  for a, b, _ in path.projected(self.spatial) for p in (a, b)]
        if self.tools_visible:
            points.extend(qt_point(p) for body in preview_tool_bodies(self.snapshot, self.selected, self.spatial) for p in body.corners)
        if not points:
            return False
        lower = QVector3D(*(min(p[i] for p in points) for i in range(3)))
        upper = QVector3D(*(max(p[i] for p in points) for i in range(3)))
        self.state['center'] = (lower+upper)/2
        inverse = self.cameraRotation.conjugated()
        local = [inverse.rotatedVector(p-self.center) for p in points]
        spans = [max(p[i] for p in local)-min(p[i] for p in local) for i in range(3)]
        self.state['zoom'] = min(max(1, self.view.width())/max(1., spans[0]),
                                 max(1, self.view.height())/max(1., spans[1]))*.84
        self._distance = max(10., (upper-lower).length()*4)
        self.schedule()
        return True

    def project(self, point):
        local = self.cameraRotation.conjugated().rotatedVector(qt_point(point)-self.center)
        return self.view.width()/2+local.x()*self.zoom, self.view.height()/2-local.y()*self.zoom

    def redraw(self):
        if not self.isVisible():
            return
        try:
            self.timer.stop()
            if self.spatial not in self._projections:
                self._projections[self.spatial] = {
                    path.identity: path.projected(self.spatial) for path in self.snapshot.paths}
            projected = self._projections[self.spatial]
            groups_key = (self.spatial, self.zoom)
            if self._groups is None or self._groups_key != groups_key:
                self._groups = {}
                for path in self.snapshot.paths:
                    if not path.enabled and not self.show_disabled:
                        continue
                    roles = {}
                    for start, end, role in projected[path.identity]:
                        roles.setdefault(role, []).append((start, end))
                    for role, pairs in roles.items():
                        pen = self.path_style(path, role)
                        points = (dash_segments(pairs, 1/self.zoom, pen.style() == QtCore.Qt.PenStyle.DotLine)
                                  if pen.style() != QtCore.Qt.PenStyle.SolidLine
                                  else [p for pair in pairs for p in pair])
                        self._groups.setdefault((pen.color().getRgbF(), pen.widthF()), []).extend(points)
                self._groups_key = groups_key
            mesh_key = (id(self._groups), self.state['pitch'], self.state['yaw'], self.zoom)
            if self._mesh_key != mesh_key:
                self._mesh.upload(self._groups, self.cameraRotation, self.zoom)
                self._mesh_key = mesh_key
            if self._label_data is None:
                self._label_data = []
                for path in self.snapshot.paths:
                    segments = projected[path.identity]
                    if (path.identity in self.selected and path.kind == 'operation' and segments
                            and (path.enabled or self.show_disabled)):
                        self._label_data.append((path, segments[0][0], segments[-1][1]))
            annotations = []
            for path, start, end in self._label_data:
                x, y = self.project(start)
                endx, endy = self.project(end)
                annotations.append(dict(x=x, y=y, endx=endx, endy=endy,
                    title=path.title, diagnostic=path.diagnostic,
                    startColor=self.panel.canvas_preview.path_pen('lead_in').color().name(),
                    endColor=self.panel.canvas_preview.path_pen('lead_out').color().name()))
            if annotations != self._annotations:
                self._annotations = annotations
                self.annotationsChanged.emit()
            camera_key = ((self.center.x(), self.center.y(), self.center.z()),
                          self.state['pitch'], self.state['yaw'], self.zoom, self.distance)
            if self._camera_key != camera_key:
                self._camera_key = camera_key
                self.cameraChanged.emit()
            self.view.update()
        except Exception as error:
            self.report_failure(str(error))

    @QtCore.pyqtSlot(float, float, int, int)
    def mousePress(self, x, y, button, modifiers):
        self.press = self.last = (x, y)
        self.button, self.modifiers, self.dragged = button, modifiers, False

    @QtCore.pyqtSlot(float, float)
    def mouseMove(self, x, y):
        if self.last is None:
            return
        dx, dy = x-self.last[0], y-self.last[1]
        self.dragged |= abs(x-self.press[0])+abs(y-self.press[1]) > 4
        shift = self.modifiers & QtCore.Qt.KeyboardModifier.ShiftModifier.value
        if self.spatial and self.button == 1 and not shift:
            self.state['yaw'] += dx*.4
            self.state['pitch'] = max(-89., min(89., self.state['pitch']+dy*.4))
        else:
            self.state['center'] += self.cameraRotation.rotatedVector(QVector3D(-dx/self.zoom, dy/self.zoom, 0))
        self.last = (x, y)
        self.schedule()

    @QtCore.pyqtSlot(float, float, int)
    def mouseRelease(self, x, y, modifiers):
        if self.press is not None and not self.dragged and self.button == 1:
            self.pick(QtCore.QPoint(round(x), round(y)),
                      bool(modifiers & QtCore.Qt.KeyboardModifier.ControlModifier.value))
        self.press = self.last = None

    @QtCore.pyqtSlot(float, float, float)
    def mouseWheel(self, delta, x, y):
        old_zoom = self.zoom
        self.state['zoom'] = max(1e-5, min(1e6, old_zoom*1.15**(delta/120)))
        self.state['center'] += self.cameraRotation.rotatedVector(QVector3D(
            (x-self.view.width()/2)*(1/old_zoom-1/self.zoom),
            -(y-self.view.height()/2)*(1/old_zoom-1/self.zoom), 0))
        self.schedule()

    def verify(self):
        if self.view.status() != QQuickView.Status.Ready:
            raise RuntimeError('\n'.join(error.toString() for error in self.view.errors()))
        if not self.frame_ready:
            # A synchronous grab before the first native frame leaves Qt Quick
            # 3D's offscreen pass blank on Qt 6.12/D3D11. Verify after exposure.
            self.view.update()
            if not self.ready_timeout.isActive():
                self.ready_timeout.start(3000)
            return
        image = self.view.grabWindow()
        api = self.view.rendererInterface().graphicsApi()
        if image.isNull() or api in (QSGRendererInterface.GraphicsApi.Unknown,
                                    QSGRendererInterface.GraphicsApi.Software,
                                    QSGRendererInterface.GraphicsApi.Null):
            raise RuntimeError('Qt Quick 3D graphics backend unavailable')
        self.verified = True

    def first_frame(self):
        if self.disposed:
            return
        self.frame_ready = True
        self.ready_timeout.stop()
        if not self.verified:
            try:
                self.verify()
            except Exception as error:
                self.report_failure(str(error))

    def check_timeout(self):
        if not self.verified and self.isVisible():
            self.report_failure('Qt Quick 3D: first frame timeout')

    def dispose(self):
        if self.disposed:
            return
        self.disposed = True
        self.timer.stop()
        self.ready_timeout.stop()
        self.view.setSource(QtCore.QUrl())
        self.view.close()
        self.view.deleteLater()
