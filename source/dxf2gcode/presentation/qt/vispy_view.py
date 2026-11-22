"""VisPy viewport with shared rendering for the spatial view and top view."""

from functools import partial
from math import hypot

from dxf2gcode.presentation.qt.qt_compat import QtCore
from dxf2gcode.presentation.qt.qt_compat.QtGui import QColor, QPainter, QPainterPath, QPainterPathStroker, QPen, QPolygonF, QRegion
from dxf2gcode.presentation.qt.qt_compat.QtWidgets import QWidget, QVBoxLayout
from dxf2gcode.application.view_scene import ViewScene, preview_tool_bodies, tool_cylinder_mesh
from dxf2gcode.presentation.qt.scalebar import ScaleBar, drawing_unit, scale_bar_enabled
from dxf2gcode.presentation.qt.view_interaction import ViewInteraction, dash_segments
from dxf2gcode.presentation.qt.wpzero import paint_workpiece_zero


WORLD_AXES = (('X', (1., 0., 0.), '#c52222'), ('Y', (0., 1., 0.), '#218539'), ('Z', (0., 0., 1.), '#2454c2'))


def projected_axes(project, origin, length):
    start = QtCore.QPointF(*origin)
    for axis, direction, color in WORLD_AXES:
        endpoint = tuple(length * unit for unit in direction)
        yield axis, color, QtCore.QPointF(*project(endpoint)) - start


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
        pen = view.panel.canvas_preview.path_pen('rapid' if role == 'retract' else role,
                                                 path.enabled, False, selected)
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


def paint_arrowhead(painter, tip, start, end):
    dx, dy = end[0]-start[0], end[1]-start[1]
    length = hypot(dx, dy)
    if length:
        back = QtCore.QPointF(dx, dy)*(9./length)
        wing = QtCore.QPointF(-dy, dx)*(4./length)
        painter.drawPolygon(QPolygonF((tip, tip-back+wing, tip-back-wing)))


def paint_origin_axes(painter, project, origin, length):
    """Draw the positive world axes with a zoom-independent maximum size."""
    x, y = origin
    start = QtCore.QPointF(x, y)
    painter.save()
    for axis, color, delta in projected_axes(project, origin, length):
        tip = start + delta
        pixels = hypot(delta.x(), delta.y())
        if pixels < 9.:
            continue
        color = QColor(color)
        painter.setPen(QPen(color, 1.6))
        painter.setBrush(color)
        painter.drawLine(start, tip)
        paint_arrowhead(painter, tip, origin, (tip.x(), tip.y()))
        label = tip + delta * (9. / pixels)
        metrics = painter.fontMetrics()
        painter.drawText(label + QtCore.QPointF(-metrics.horizontalAdvance(axis) / 2, metrics.ascent() / 2), axis)
    painter.restore()


def direction_arrow(segments, project):
    for start, end, role in segments:
        if role in ('rapid', 'retract') or start == end:
            continue
        a, b = project(start), project(end)
        if a != b:
            return a, b
    return None


class ViewLabels(QWidget):
    DETAIL_CONTOUR_PIXELS = 400

    def __init__(self, owner, parent):
        super().__init__(parent)
        self.owner = owner
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)

    def paintEvent(self, event):
        with QPainter(self) as painter:
            self.paint_overlay(painter)

    def paint_overlay(self, painter):
        owner = self.owner
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        project = partial(owner.project, transform=owner.view.scene.node_transform(owner.canvas.scene))
        owner.paint_route(painter, project)
        show_directions = owner.panel.window.ui.actionShowPathDirections.isChecked()
        labels = {}
        for path in owner.snapshot.paths:
            selected = path.identity in owner.selected
            if (path.kind != 'operation' or not (selected or show_directions)
                    or not owner.path_visible(path)):
                continue
            segments = owner.projected_segments(path)
            if not segments:
                continue
            first, last = segments[0], segments[-1]
            if not owner.show_retracts:
                first = next((segment for segment in segments if segment[2] != 'retract'), None)
                if first is None:
                    continue
                last = next(segment for segment in reversed(segments) if segment[2] != 'retract')
            points = (project(first[0]), project(last[1]))
            for index, ((x, y), text, role) in enumerate(zip(points, ('S', 'E'), ('lead_in', 'lead_out'))):
                painter.setPen(QPen(owner.panel.canvas_preview.path_pen(role).color(), 2))
                painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
                painter.drawEllipse(QtCore.QPointF(x, y), 4, 4)
                painter.drawText(QtCore.QPointF(x+6, y-4), text)
                arrow = direction_arrow(reversed(segments) if index else segments, project)
                if arrow is not None:
                    a, b = arrow
                    tip = QtCore.QPointF(*(b if index else a))
                    painter.setBrush(painter.pen().color())
                    paint_arrowhead(painter, tip, a, b)
            if selected and self.rect().adjusted(-4, -4, 4, 4).contains(QtCore.QPointF(*points[0]).toPoint()):
                labels.setdefault(path.geometry, []).append((points[0], path.title, path.diagnostic))
        self.paint_operation_labels(painter, labels)
        if owner.editing_tabs:
            owner.panel.modifiers.paint(painter, owner)
        if owner.snapshot.paths:
            x, y = project((0., 0., 0.))
            if owner.spatial and owner.show_origin_axes:
                if self.rect().adjusted(-44, -44, 44, 44).contains(QtCore.QPointF(x, y).toPoint()):
                    paint_origin_axes(painter, project, (x, y), 30. * owner.world_units_per_pixel())
            elif not owner.spatial and self.rect().adjusted(-12, -12, 12, 12).contains(QtCore.QPointF(x, y).toPoint()):
                paint_workpiece_zero(painter, QtCore.QPointF(x, y))
            if scale_bar_enabled():
                bar = owner.spatial_scale_bar if owner.spatial else owner.scale_bar
                length, _ = bar.update(1. / owner.world_units_per_pixel(), drawing_unit())
                if owner.spatial and length:
                    bar.paint_spatial(painter, self.rect(), tuple(projected_axes(project, (x, y), length)))
                else:
                    bar.paint(painter, self.rect())

    def operation_labels(self, labels):
        owner = self.owner
        detail_span = self.DETAIL_CONTOUR_PIXELS * owner.world_units_per_pixel()
        for geometry, entries in labels.items():
            source = owner.panel.binding.sources.get(geometry)
            bounds = getattr(source, 'BB', None)
            span = 0. if bounds is None else max(bounds.Pe.x-bounds.Ps.x, bounds.Pe.y-bounds.Ps.y)
            if len(entries) > 1 and span < detail_span:
                summary = owner.panel.modifiers.tr('{0} operations').format(len(entries))
                yield entries[0][0], ((summary, 'red' if any(e[2] for e in entries) else 'black'),)
                continue
            for anchor, title, diagnostic in entries:
                lines = ((title, 'black'),)
                if diagnostic:
                    lines += ((diagnostic, 'red'),)
                yield anchor, lines

    def paint_operation_labels(self, painter, labels):
        if not labels:
            return
        viewport = QtCore.QRectF(self.rect().adjusted(4, 4, -4, -4))
        metrics = painter.fontMetrics()
        height, gap = metrics.lineSpacing(), 3
        occupied = []
        for (x, y), lines in self.operation_labels(labels):
            if not viewport.adjusted(-8, -8, 8, 8).contains(QtCore.QPointF(x, y)):
                continue
            lines = [(metrics.elidedText(text, QtCore.Qt.TextElideMode.ElideRight, int(viewport.width())), color)
                     for text, color in lines]
            width = max(metrics.horizontalAdvance(text) for text, _ in lines)
            top = max(viewport.top(), y + 16 - metrics.ascent())
            left = max(viewport.left(), min(x+8, viewport.right()-width))
            rect = QtCore.QRectF(left, top, width, len(lines)*height)
            while (overlap := next((other for other in occupied if other.intersects(rect)), None)) is not None:
                rect.moveTop(overlap.bottom()+gap)
            if rect.bottom() > viewport.bottom():
                rect.moveBottom(min(top-gap, viewport.bottom()))
                while (overlap := next((other for other in occupied if other.intersects(rect)), None)) is not None:
                    rect.moveBottom(overlap.top()-gap)
            if rect.top() < viewport.top():
                continue
            occupied.append(rect)
            for index, (text, color) in enumerate(lines):
                painter.setPen(QColor(color))
                painter.drawText(rect.topLeft()+QtCore.QPointF(0, metrics.ascent()+index*height), text)


class SelectionOverlay(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        self.outline = self.pending = QtCore.QRect()
        self.frame = QtCore.QTimer(self)
        self.frame.setSingleShot(True)
        self.frame.timeout.connect(self.update_outline)

    def set_outline(self, rect):
        self.pending = rect
        if rect.isEmpty():
            self.frame.stop()
            self.update_outline()
        elif not self.frame.isActive():
            self.frame.start(16)

    def update_outline(self):
        dirty = QRegion()
        for rect in (self.outline, self.pending):
            if not rect.isEmpty():
                dirty |= QRegion(rect.adjusted(-1, -1, 1, 1))
        self.outline = self.pending
        self.update(dirty)

    def paintEvent(self, event):
        if not self.outline.isEmpty():
            edge = self.palette().highlight().color()
            fill = QColor(edge)
            fill.setAlpha(32)
            with QPainter(self) as painter:
                painter.setPen(QPen(edge))
                painter.setBrush(fill)
                painter.drawRect(self.outline)


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
            # existing handler during native window teardown.
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
        self.show_origin_axes = True
        self.selected_paths_only, self.show_retracts = False, True
        self.visible_regions = set()
        self.nodes = {}
        self._projections, self._dash_cache, self._uploads = {}, (None, {}), {}
        self._hit_data, self._hit_screen = {}, {}
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
        # Keep XY upright while mapping new Z depths in the same direction as
        # the orbit camera at elevation 90°, so both depth tests agree.
        self.plane_camera = scene.cameras.PanZoomCamera(aspect=1, up='-z')
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
        self.scale_bar = ScaleBar()
        self.spatial_scale_bar = ScaleBar(target_px=64., min_px=40., max_px=95.)
        self.selection_band = SelectionOverlay(self.canvas.native)
        self.selection_band.show()
        self.canvas.native.installEventFilter(self)
        self.press = None
        self.context_press = None
        self.plane_pan = False
        self.timer = QtCore.QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.redraw)
        self.canvas.events.mouse_move.connect(lambda event: self.schedule())
        self.canvas.events.mouse_wheel.connect(lambda event: self.schedule())
        self.canvas.events.resize.connect(lambda event: self.schedule())
        self.fitted = set()

    def schedule(self):
        self.labels.setGeometry(self.canvas.native.rect())
        self.selection_band.setGeometry(self.canvas.native.rect())
        self.labels.update()
        if not self.timer.isActive():
            self.timer.start(20)

    def set_scene(self, snapshot, selected):
        changed = snapshot is not self.snapshot
        if changed:
            self._scene_revision += 1
            self._projections.clear()
            self._dash_cache = None, {}
            self._hit_data.clear()
            self._hit_screen.clear()
            for node in self.tool_nodes.values():
                node.parent = None
            self.tool_nodes.clear()
            self._tool_key = None
        self.snapshot, self.selected = snapshot, set(selected)
        self.update_region_visibility()
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
        self.context_press = None
        self.selection_band.set_outline(QtCore.QRect())
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

    def set_display_filters(self, selected_only, show_retracts):
        if (self.selected_paths_only, self.show_retracts) == (selected_only, show_retracts):
            return
        if self.show_retracts != show_retracts:
            self._hit_data.pop(False, None)
            self._hit_screen.clear()
        self.selected_paths_only, self.show_retracts = selected_only, show_retracts
        self.update_region_visibility()
        self.redraw()

    def update_region_visibility(self):
        if self.selected_paths_only:
            modifiers = self.panel.modifiers
            self.visible_regions = modifiers.regions_for_operations(self.selected) | modifiers.selected_regions

    def path_visible(self, path):
        if not path.enabled and not self.show_disabled:
            return False
        if not self.selected_paths_only:
            return True
        if path.kind == 'operation':
            return path.identity in self.selected
        if path.kind == 'region':
            return path.identity in self.visible_regions
        return True

    def scene_bounds(self):
        points = [p for path, segments, roles in self.projected_data().values()
                  if self.path_visible(path)
                  for a, b, role in segments if self.show_retracts or role != 'retract'
                  for p in (a, b)]
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
            self._projections = data
        return self._projections

    def projected_segments(self, path):
        return self.projected_data()[path.identity][1]

    def screen_segments(self, *, geometry_only=False):
        """Project all line segments once for the current camera.

        A four-point homogeneous basis fingerprints the current linear camera
        transform, covering pan, zoom, rotation, viewport and device scaling.
        No per-endpoint traversal of the VisPy scene graph is needed.
        """
        import numpy as np
        if geometry_only not in self._hit_data:
            paths, points, offset = [], [], 0
            for path in self.snapshot.paths:
                if geometry_only and path.kind != 'geometry':
                    continue
                segments = self.projected_segments(path)
                vertices = [p for a, b, role in segments if self.show_retracts or role != 'retract'
                            for p in (a, b)]
                count = len(vertices)//2
                paths.append((path, offset, offset+count))
                points.extend(vertices)
                offset += count
            self._hit_data[geometry_only] = paths, np.asarray(points, dtype=np.float64).reshape(-1, 3)
        paths, points = self._hit_data[geometry_only]
        if not len(points):
            return paths, points[:, :2], points[:, :2], np.empty(0)
        transform = self.view.scene.node_transform(self.canvas.scene)
        basis = transform.map(((0., 0., 0., 1.), (1., 0., 0., 1.),
                               (0., 1., 0., 1.), (0., 0., 1., 1.)))
        key = tuple(basis.ravel())
        cache_key = (self.spatial, True) if geometry_only else self.spatial
        cached = self._hit_screen.get(cache_key)
        if cached is None or cached[0] != key:
            mapped = transform.map(points)
            with np.errstate(divide='ignore', invalid='ignore'):
                xy = mapped[:, :2]/mapped[:, 3:4]
            starts, ends = xy[::2], xy[1::2]
            delta = ends-starts
            lengths = np.einsum('ij,ij->i', delta, delta)
            cached = key, starts, delta, lengths
            self._hit_screen[cache_key] = cached
        return paths, *cached[1:]

    def path_hits(self, point, kinds=('operation', 'region')):
        import numpy as np
        paths, starts, delta, lengths = self.screen_segments()
        relative = (point.x(), point.y())-starts
        t = np.divide(np.einsum('ij,ij->i', relative, delta), lengths,
                      out=np.zeros_like(lengths), where=lengths > 0)
        residual = relative-np.clip(t, 0., 1.)[:, None]*delta
        distances = np.einsum('ij,ij->i', residual, residual)
        distances[~np.isfinite(distances)] = float('inf')
        hits = []
        for path, start, end in paths:
            if path.kind not in kinds or not self.path_visible(path) or start == end:
                continue
            distance = float(np.min(distances[start:end]))
            if distance <= 7.**2:
                hits.append((distance, path.identity))
        return tuple(identity for distance, identity in sorted(hits, key=lambda hit: hit[0]))

    def project(self, point, transform=None):
        if transform is None:
            transform = self.view.scene.node_transform(self.canvas.scene)
        mapped = transform.map(point)
        return float(mapped[0]/mapped[3]), float(mapped[1]/mapped[3])

    def viewport(self):
        """Qt surface hosting the shared tab dimension editor."""
        return self.canvas.native

    def paint_route(self, painter, project):
        scene = getattr(self.panel.window, 'canvas_scene', None)
        for arrow in getattr(scene, 'routearrows', ()):
            end = project((arrow.startp.x(), -arrow.startp.y(), 0.))
            start = project((arrow.endp.x, arrow.endp.y, 0.))
            a, b = (start, end) if arrow.startarrow else (end, start)
            painter.setPen(arrow.pen)
            painter.setBrush(arrow.myColor)
            painter.drawLine(QtCore.QPointF(*a), QtCore.QPointF(*b))
            paint_arrowhead(painter, QtCore.QPointF(*b), a, b)
        for label in getattr(scene, 'routetext', ()):
            x, y = project((label.startp.x(), -label.startp.y(), 0.))
            painter.setPen(QPen(label.brush))
            painter.drawText(QtCore.QPointF(x+3, y-3), label.text)

    def select_rectangle(self, rect, toggle):
        import numpy as np
        sources = self.panel.binding.sources
        stroker = QPainterPathStroker()
        stroker.setWidth(1.)
        paths, starts, delta, _ = self.screen_segments(geometry_only=True)
        ends = starts+delta
        low, high = np.minimum(starts, ends), np.maximum(starts, ends)
        candidates = ((high >= (rect.left()-.5, rect.top()-.5))
                      & (low <= (rect.right()+.5, rect.bottom()+.5))).all(axis=1)
        hits = set()
        for path, first, last in paths:
            if not (path.enabled or self.show_disabled):
                continue
            outline = QPainterPath()
            for index in np.flatnonzero(candidates[first:last])+first:
                outline.moveTo(QtCore.QPointF(*starts[index]))
                outline.lineTo(QtCore.QPointF(*ends[index]))
            if stroker.createStroke(outline).intersects(rect):
                hits.add(path.identity)
        for identity, shape in sources.items():
            selected = (shape.isSelected() != (identity in hits)) if toggle else identity in hits
            if shape.isSelected() != selected:
                self.panel.window.TreeHandler.setShapeSelected(shape, selected)
        self.panel.geometry_selected(update_tree_only=True)

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

    @property
    def editing_tabs(self):
        return not self.spatial and self.panel.modifiers.mode

    def world_units_per_pixel(self):
        width, height = (max(1, size) for size in self.view.size)
        if self.spatial:
            return (self.camera.scale_factor or 1.) / min(width, height)
        rect = self.camera.rect
        return max(rect.width / width, rect.height / height)

    def _redraw(self):
        import numpy as np
        groups, signatures = {}, {}
        unit = max(self.world_units_per_pixel(), 1e-12)
        previous_unit, dash_cache = self._dash_cache
        if previous_unit is not None and abs(unit - previous_unit) <= 1e-12 * unit:
            unit = previous_unit
        else:
            dash_cache = {}
        self._dash_cache = unit, dash_cache
        for path, _, roles in self.projected_data().values():
            # Live tab outlines and handles belong to the editor overlay.
            if path.kind == 'region' and self.editing_tabs:
                continue
            if not self.path_visible(path):
                continue
            for role, pairs, solid_points in roles:
                if role == 'retract' and not self.show_retracts:
                    continue
                pen = self.path_style(path, role)
                color, width = pen.color().getRgbF(), pen.widthF()
                dashed = pen.style() != QtCore.Qt.PenStyle.SolidLine
                points = solid_points
                if dashed:
                    dash_key = (path.identity, role, pen.style())
                    if dash_key not in dash_cache:
                        dash_cache[dash_key] = np.asarray(dash_segments(pairs, unit,
                            pen.style() == QtCore.Qt.PenStyle.DotLine,
                            align_depth_passes=True), dtype=np.float32)
                    points = dash_cache[dash_key]
                if not len(points):
                    continue
                key = (color, width or 1.)
                groups.setdefault(key, []).append(points)
                signatures.setdefault(key, []).append((path.identity, role, pen.style(), unit if dashed else None))
        for key in set(self.nodes)-set(groups):
            self.nodes.pop(key).parent = None
            self._uploads.pop(key, None)
        for key, arrays in groups.items():
            if not any(len(points) for points in arrays):
                continue
            if key not in self.nodes:
                node = self.scene_api.visuals.Line(parent=self.view.scene, method='gl',
                    connect='segments', antialias=True)
                node.set_gl_state(depth_test=True, blend=True,
                                  blend_func=('src_alpha', 'one_minus_src_alpha'))
                self.nodes[key] = node
            node = self.nodes[key]
            signature = self._scene_revision, tuple(signatures[key])
            if self._uploads.get(key) != signature:
                node.set_data(pos=np.concatenate([p for p in arrays if len(p)]),
                              color=key[0], width=key[1])
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

    def open_context_menu(self, global_pos, point=None):
        scene = self.panel.window.canvas_scene
        if scene is not None and self.isVisible():
            from dxf2gcode.presentation.qt.canvas import MyDropDownMenu
            MyDropDownMenu(scene, global_pos, point)

    def eventFilter(self, watched, event):
        if not self.spatial and self.panel.modifiers.eventFilter(watched, event):
            self.press = None
            return True
        kind = event.type()
        if self._top_start is not None and kind in (QtCore.QEvent.Type.MouseButtonPress,
                QtCore.QEvent.Type.MouseButtonRelease, QtCore.QEvent.Type.MouseButtonDblClick,
                QtCore.QEvent.Type.MouseMove, QtCore.QEvent.Type.Wheel):
            return True
        if kind == QtCore.QEvent.Type.ContextMenu:
            if not self.spatial:
                from dxf2gcode.domain.geometry.point import Point
                self.open_context_menu(event.globalPos(), Point(*self.tab_scene_point(event.pos())))
            elif event.reason() != event.Reason.Mouse:
                self.open_context_menu(event.globalPos())
            return True
        if self.spatial:
            right_button = QtCore.Qt.MouseButton.RightButton
            if kind == QtCore.QEvent.Type.MouseButtonPress and event.button() == right_button:
                self.context_press = event.pos()
            elif kind == QtCore.QEvent.Type.MouseMove and self.context_press is not None:
                if (event.pos() - self.context_press).manhattanLength() > 4:
                    self.context_press = None
            elif kind == QtCore.QEvent.Type.MouseButtonRelease and event.button() == right_button:
                start, self.context_press = self.context_press, None
                if start is not None and (event.pos() - start).manhattanLength() <= 4:
                    # Let VisPy process the release before opening the modal menu.
                    QtCore.QTimer.singleShot(0, partial(self.open_context_menu, watched.mapToGlobal(event.pos())))
        if kind == QtCore.QEvent.Type.MouseButtonPress and event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.press = event.pos()
            self.plane_pan = bool(event.modifiers() & QtCore.Qt.KeyboardModifier.ShiftModifier)
            return not self.spatial
        if self.press is None:
            return False
        if kind == QtCore.QEvent.Type.MouseMove and not self.spatial:
            if self.plane_pan:
                before = self.tab_scene_point(self.press)
                after = self.tab_scene_point(event.pos())
                self.camera.pan(tuple(a-b for a, b in zip(before, after)))
                self.press = event.pos()
                self.schedule()
            elif (event.pos()-self.press).manhattanLength() > 4:
                self.selection_band.set_outline(QtCore.QRect(self.press, event.pos()).normalized())
            return True
        if kind == QtCore.QEvent.Type.MouseButtonRelease and event.button() == QtCore.Qt.MouseButton.LeftButton:
            start, self.press = self.press, None
            toggle = bool(event.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier)
            self.selection_band.set_outline(QtCore.QRect())
            if not self.spatial and self.plane_pan:
                return True
            if self.panel.binding is not None:
                if (event.pos()-start).manhattanLength() <= 4:
                    self.pick(event.pos(), toggle)
                elif not self.spatial:
                    rect = QtCore.QRectF(QtCore.QRect(start, event.pos()).normalized())
                    self.select_rectangle(rect, toggle)
            return not self.spatial
        return False


    def verify(self):
        """Force a real render: successful import is not a capability check."""
        from vispy import gloo
        self.canvas.set_current()
        if not gloo.gl.glGetParameter(gloo.gl.GL_VERSION):
            raise RuntimeError('OpenGL context unavailable')
        self.canvas.render(size=(1, 1))

    def dispose(self):
        self.cancel_top_transition()
        self.timer.stop()
        self._projections.clear()
        self._dash_cache = None, {}
        self._uploads.clear()
        self._hit_data.clear()
        self._hit_screen.clear()
        self.canvas.close()
