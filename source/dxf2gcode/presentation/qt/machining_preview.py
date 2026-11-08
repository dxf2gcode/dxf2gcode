"""Per-operation, screen-space previews shared by the 2D and 3D canvases."""

from dataclasses import dataclass
from math import atan2, cos, sin, pi

from dxf2gcode.presentation.qt.qt_compat import QtCore
from dxf2gcode.presentation.qt.qt_compat.QtGui import QColor, QPainter, QPainterPath, QPainterPathStroker, QPen, QPolygonF
from dxf2gcode.presentation.qt.qt_compat.QtWidgets import QWidget, QMenu
from dxf2gcode.presentation.qt.numeric_display import format_number
from dxf2gcode.domain.project.machining_project import MachiningOperation
from dxf2gcode.adapters.toolpath.preparation import prepare_shape
from dxf2gcode.adapters.toolpath.preview import preview_result
from dxf2gcode.application.toolpath.projections import plan_preview_segments

Qt = QtCore.Qt


@dataclass
class OperationPreview:
    identity: str
    geometry: str
    title: str
    enabled: bool
    plan: object
    segments: tuple
    start: tuple
    end: tuple
    color: object
    tooltip: str


class PreviewOverlay(QWidget):
    def __init__(self, owner, parent):
        super().__init__(parent)
        self.owner = owner
        self.setObjectName('machiningPreviewOverlay')
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setGeometry(parent.rect())
        self.show()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.owner.paint(painter)


class MachiningPreview(QtCore.QObject):
    def __init__(self, panel):
        self.panel = panel
        self.view = panel.window.canvas
        super().__init__(self.view)
        self.target = self.view.viewport() if hasattr(self.view, 'mapToScene') else self.view
        self.records = []
        self.selected = set()
        self.counts = {}
        self.anchors = {}
        self.hovered = None
        self.overlay = PreviewOverlay(self, self.target)
        self.target.installEventFilter(self)
        self.view.machining_preview = self
        if hasattr(self.view, 'horizontalScrollBar'):
            self.view.horizontalScrollBar().valueChanged.connect(self.overlay.update)
            self.view.verticalScrollBar().valueChanged.connect(self.overlay.update)

    def tr(self, text):
        return QtCore.QCoreApplication.translate('MachiningPreview', text)

    def refresh(self, layers):
        panel, binding = self.panel, self.panel.binding
        self.records = []
        self.selected = set(panel.selected_entries())
        self.counts, self.anchors = {}, {}
        by_geometry = binding.operations_by_geometry()
        scene = panel.window.canvas_scene
        for identity, source in binding.sources.items():
            operations = by_geometry.get(identity, ())
            self.counts[identity] = (sum(entry.id in self.selected for _, entry in operations), len(operations))
            point = source.get_start_end_points(True)
            self.anchors[identity] = (point.x, point.y, source.axis3_start_mill_depth)
        scene.machining_selection_counts = self.counts
        views = {shape.operation_id: shape for layer in layers for shape in layer.shapes
                 if hasattr(shape, 'geos')}
        directions = panel.window.ui.actionShowPathDirections.isChecked()
        for step in binding.project.steps:
            if step.kind in ('ignored', 'break'):
                continue
            for entry in step.entries:
                if not isinstance(entry, MachiningOperation) or entry.id not in views:
                    continue
                source = binding.sources[entry.geometry_id]
                if not source.isSelected() and not directions:
                    continue
                if not entry.enabled and not scene.showDisabledPaths:
                    continue
                view = views[entry.id]
                if view.stmove is None:
                    prepare_shape(view, build_preview=False)
                if view.toolpath_plan is not None or getattr(view, 'toolpath_diagnostics', ()):
                    from dxf2gcode.domain.toolpath.plan import ToolpathPlanningResult
                    result = ToolpathPlanningResult(view.toolpath_plan, view.toolpath_diagnostics)
                else:
                    result = preview_result(view, panel.window.MyPostProcessor, layers)
                plan = result.plan if not result.has_errors else None
                segments = plan_preview_segments(plan)
                anchor = self.anchors[entry.geometry_id]
                start = segments[0].start if segments else anchor
                end = segments[-1].end if segments else anchor
                tool = binding.project.tools[step.tool_id]
                title = '%s · %s · T%d' % (step.name, panel.tr('Contour {0}').format(source.nr), tool.tool_nr)
                units = binding.project.units
                point_text = lambda point: [format_number(value, units) for value in point]
                tip = title
                if plan is not None:
                    tip += '\n' + self.tr('Start: X {0} · Y {1} · Z {2} {3}').format(*point_text(start), units)
                    tip += '\n' + self.tr('End: X {0} · Y {1} · Z {2} {3}').format(*point_text(end), units)
                tip += '\n' + self.tr('Final depth: {0} {1}').format(format_number(view.axis3_mill_depth, units), units)
                if result.has_errors:
                    from dxf2gcode.presentation.qt.toolpath_labels import translate_message
                    tip += '\n' + self.tr('No toolpath: {0}').format('; '.join(translate_message(d.message) for d in result.diagnostics))
                self.records.append(OperationPreview(entry.id, entry.geometry_id, title,
                    entry.enabled, plan, segments, start, end, self.path_pen('cut', entry.enabled).color(), tip))
        # One overlay owns the visible plans; legacy active-operation objects
        # remain available for existing editor/preview clients.
        graphics = getattr(scene, 'graphics_items', {})
        visible_geometry = {record.geometry for record in self.records}
        for source in binding.sources.values():
            item = graphics.get(id(source))
            if item is not None:
                for child in (item.stmove_item, item.starrow, item.enarrow):
                    child.setOpacity(0 if source.parentLayer.isBreakLayer() or source.geometry_id in visible_geometry else 1)
                item.update()
        scene.machining_overlay_geometries = visible_geometry
        self.overlay.raise_()
        self.overlay.update()

    def project(self, point):
        x, y, z = point
        if hasattr(self.view, 'mapFromScene'):
            # Use the exact floating-point transform used by scene painting.
            return self.view.viewportTransform().map(QtCore.QPointF(x, -y))
        view = self.view
        x, y, z = view.rotate(x*view.scale+view.posX, -y*view.scale+view.posY, z*view.scale+view.posZ)
        side = min(view.width(), view.height())
        return QtCore.QPointF(view.width()/2+x*side, view.height()/2+y*side)

    def projected_paths(self, record):
        paths = {}
        for segment in record.segments:
            path = paths.setdefault(segment.role, QPainterPath())
            path.moveTo(self.project(segment.start))
            path.lineTo(self.project(segment.end))
        return paths

    def label_rects(self):
        counts, result = {}, {}
        fm = self.overlay.fontMetrics()
        for record in self.records:
            source = self.panel.binding.sources.get(record.geometry)
            if source is None or not source.isSelected():
                continue
            index = counts.get(record.geometry, 0)
            counts[record.geometry] = index+1
            anchor = self.project(record.start)
            text = ('⚠ ' if record.plan is None else '') + record.title
            width = fm.horizontalAdvance(text)+10
            x = min(max(2, anchor.x()+14), max(2, self.target.width()-width-2))
            y = min(max(2, anchor.y()+14+index*(fm.height()+5)), max(2, self.target.height()-fm.height()-4))
            result[record.identity] = (QtCore.QRectF(x, y, width, fm.height()+3), text)
        return result

    def hit_records(self, point):
        point = QtCore.QPointF(point)
        labels = self.label_rects()
        label_hits = [r for r in self.records if r.identity in labels and labels[r.identity][0].contains(point)]
        if label_hits:
            return label_hits
        stroker = QPainterPathStroker()
        stroker.setWidth(12)
        result = []
        for record in self.records:
            marker = any((self.project(p)-point).manhattanLength() <= 9 for p in (record.start, record.end))
            if marker or any(stroker.createStroke(path).contains(point) for path in self.projected_paths(record).values()):
                result.append(record)
        return result

    def try_select(self, point, control=False):
        if self.panel.modifiers.mode:
            return self.panel.modifiers.hit(point)
        records = self.hit_records(point)
        if not records:
            return False
        if len(records) == 1:
            chosen = records[0].identity
        else:
            menu = QMenu(self.target)
            menu.addSection(self.tr('Choose machining operation'))
            for record in records:
                action = menu.addAction(record.title)
                action.setData(record.identity)
                action.setToolTip(record.tooltip)
            action = menu.exec(self.target.mapToGlobal(QtCore.QPoint(point)))
            chosen = action.data() if action is not None else None
        if chosen is not None:
            self.panel.select_canvas_operation(chosen, control)
        return True

    def eventFilter(self, watched, event):
        kind = event.type()
        if kind == QtCore.QEvent.Type.Resize:
            self.overlay.setGeometry(self.target.rect())
        if kind in (QtCore.QEvent.Type.Resize, QtCore.QEvent.Type.Wheel, QtCore.QEvent.Type.MouseMove):
            if kind == QtCore.QEvent.Type.MouseMove and not event.buttons():
                point = event.position().toPoint() if hasattr(event, 'position') else event.pos()
                records = self.hit_records(point)
                self.hovered = next((r.identity for r in records if r.identity == self.panel.context),
                                    records[0].identity if records else None)
                self.target.setToolTip('\n\n'.join(record.tooltip for record in records))
            self.overlay.update()
        elif kind == QtCore.QEvent.Type.Leave:
            self.hovered = None
            self.overlay.update()
        return False

    def path_pen(self, role, enabled=True, active=False, selected=True):
        """Reuse each canvas' established semantic palette, never step colours."""
        if hasattr(self.view, 'viewportTransform'):
            from dxf2gcode.presentation.qt.canvas2d import StMoveGUI, ShapeGUI
            original = {'lead_in': StMoveGUI.PEN_LEAD_IN_LINE,
                        'lead_out': StMoveGUI.PEN_EXIT_LINE, 'overcut': StMoveGUI.PEN_EXIT_LINE,
                        'rapid': StMoveGUI.PEN_RAPID_MOVE, 'pocket': StMoveGUI.PEN_POCKET_LINE,
                        'tab': ShapeGUI.PEN_BREAK}.get(role, StMoveGUI.PEN_COMP_LINE)
            pen = QPen(original if enabled else ShapeGUI.PEN_NORMAL_DISABLED)
        else:
            pen = QPen(self.view.COLOR_STMOVE if enabled else self.view.COLOR_NORMAL_DISABLED, 2)
        if active:
            pen.setWidthF(pen.widthF()+1)
        elif not selected:
            pen.setWidthF(0.6)
            pen.setStyle(Qt.PenStyle.DashLine)
        return pen

    def paint(self, painter):
        labels = self.label_rects()
        for record in self.records:
            active = record.identity == self.panel.context or record.identity == self.hovered
            selected = record.identity in self.selected
            color = self.path_pen('cut', record.enabled).color()
            for role, path in self.projected_paths(record).items():
                pen = self.path_pen(role, record.enabled, active, selected)
                painter.setPen(pen)
                painter.drawPath(path)
            if record.plan is None:
                position = self.project(record.start)
                painter.setPen(QPen(QColor(190, 20, 20), 2))
                painter.drawLine(position-QtCore.QPointF(6, 6), position+QtCore.QPointF(6, 6))
                painter.drawLine(position-QtCore.QPointF(-6, 6), position+QtCore.QPointF(-6, 6))
            if record.plan is not None and self.panel.window.application_context.config.vars.General['show_tool_circle']:
                painter.setBrush(Qt.BrushStyle.NoBrush)
                circle = QPainterPath()
                for index in range(37):
                    angle = index*pi/18
                    point = self.project((record.start[0]+record.plan.tool_radius*cos(angle),
                                          record.start[1]+record.plan.tool_radius*sin(angle), record.start[2]))
                    circle.moveTo(point) if not index else circle.lineTo(point)
                painter.setPen(QPen(self.path_pen('lead_in', record.enabled).color(),
                                    1 if selected or active else 0.6, Qt.PenStyle.DashLine))
                painter.drawPath(circle)
            for point, text in ((record.start, 'S'), (record.end, 'E')) if record.plan is not None else ():
                position = self.project(point)
                marker_color = (self.view.COLOR_ENTRY_ARROW if text == 'S' else self.view.COLOR_EXIT_ARROW) if not hasattr(self.view, 'viewportTransform') else self.path_pen('lead_in' if text == 'S' else 'lead_out', record.enabled).color()
                painter.setPen(QPen(marker_color, 2 if selected or active else 0.6))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawEllipse(position, 5, 5)
                painter.drawText(position+QtCore.QPointF(6, -5 if text == 'S' else 12), text)
            moves = [segment for segment in record.segments if segment.role != 'rapid'
                     and self.project(segment.start) != self.project(segment.end)]
            for segment, at_end in ((moves[0], False), (moves[-1], True)) if moves else ():
                start, end = self.project(segment.start), self.project(segment.end)
                position = end if at_end else start
                angle = atan2(end.y()-start.y(), end.x()-start.x())
                arrow_color = (self.view.COLOR_EXIT_ARROW if at_end else self.view.COLOR_ENTRY_ARROW) if not hasattr(self.view, 'viewportTransform') else QColor(0, 245, 100) if at_end else QColor(50, 200, 255)
                painter.setPen(self.path_pen('lead_out' if at_end else 'lead_in', record.enabled,
                                            selected=selected or active))
                painter.setBrush(arrow_color)
                painter.drawPolygon(QPolygonF([position, position-QtCore.QPointF(10*cos(angle-.45), 10*sin(angle-.45)),
                                               position-QtCore.QPointF(10*cos(angle+.45), 10*sin(angle+.45))]))
        for geometry, (selected, total) in self.counts.items():
            if not selected or total < 2:
                continue
            source = self.panel.binding.sources.get(geometry)
            if source is None or (source.disabled and not self.panel.window.canvas_scene.showDisabledPaths):
                continue
            if selected < total:
                # Keep the original's partial-selection dots visible even
                # when a machining path occupies exactly the same XY line.
                path = QPainterPath(self.project(self.anchors[geometry]))
                source.make_path(lambda caller, start, end: path.lineTo(self.project(
                    (end.x, end.y, source.axis3_start_mill_depth))), lambda caller, start: None)
                from dxf2gcode.presentation.qt.canvas2d import ShapeGUI
                original_color = ShapeGUI.PEN_SELECT.color() if hasattr(self.view, 'viewportTransform') else self.view.COLOR_SELECT
                painter.setPen(QPen(original_color, 2, Qt.PenStyle.DotLine))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawPath(path)
            anchor = self.project(self.anchors[geometry]) + QtCore.QPointF(-12, -12)
            painter.setPen(self.overlay.palette().color(self.overlay.foregroundRole()))
            painter.drawText(anchor, '%d/%d' % (selected, total))
        for record in self.records:
            if record.identity not in labels:
                continue
            rect, text = labels[record.identity]
            painter.fillRect(rect, QColor(255, 255, 255, 225))
            painter.setPen(self.overlay.palette().color(self.overlay.foregroundRole()))
            painter.drawText(rect.adjusted(4, 0, -2, 0), Qt.AlignmentFlag.AlignVCenter, text)
        self.panel.modifiers.paint(painter)
