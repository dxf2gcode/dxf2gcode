"""Plan prepared drag-knife tip paths and the ramp into the workpiece."""

from math import acos, ceil, hypot, sqrt

from dxf2gcode.domain.toolpath.knife_geometry import part
from dxf2gcode.domain.toolpath.messages import QT_TRANSLATE_NOOP

from dxf2gcode.domain.toolpath.movements import MovementPlan


class DragKnifeStrategy:
    def plan(self, request):
        settings = request.settings
        plan = MovementPlan(request)
        safe = settings.workpiece_top + abs(settings.safe_margin)
        plan.geometry(request.prepared_path[0].resolved, role="approach")
        plan.add("pre_cut")
        plan.add("rapid_z", safe, role="approach")
        plan.add("feed", settings.feed_depth)
        path = tuple(geo.resolved for geo in request.prepared_path[1:])
        if settings.drag_ramp_length > 0:
            self._ramp_path(plan, path, safe, settings)
        else:
            first = path[0]
            drag = first.kind == "arc" and first.drag
            plan.add("linear_z", settings.slice_depth if drag else settings.final_depth,
                     role="drag_swivel" if drag else "plunge")
            plan.add("feed", settings.feed_xy)
            plan.geometry(first, role="drag_swivel" if drag else "cut")
            for geo in path[1:]:
                is_drag = geo.kind == "arc" and geo.drag
                if is_drag or drag:
                    plan.add("feed", settings.feed_depth)
                    plan.add("linear_z",
                             settings.slice_depth if is_drag else settings.final_depth,
                             role="drag_swivel")
                    plan.add("feed", settings.feed_xy)
                drag = is_drag
                plan.cut_geometry(geo, role="drag_swivel" if is_drag else "cut")
        plan.add("feed", settings.feed_depth)
        plan.add("linear_z", safe, role="retract")
        plan.add("rapid_z", settings.retract_depth, role="retract")
        plan.add("post_cut")
        return plan.finish()

    def _ramp_path(self, plan, path, start_z, settings):
        """Keep the legacy path, but ramp continuously and retain each tail."""
        length = settings.drag_ramp_length
        if min(settings.feed_xy, settings.feed_depth) <= 0:
            raise ValueError(QT_TRANSLATE_NOOP('Shape', 'Invalid drag-knife settings or contour.'))
        if sum(g.length for g in path if not (g.kind == 'arc' and g.drag)) < length - 1e-9:
            raise ValueError(QT_TRANSLATE_NOOP('Shape', 'The drag-knife ramp is longer than the available cutting path.'))
        covered, z = 0.0, start_z
        for geo in path:
            is_drag = geo.kind == "arc" and geo.drag
            if is_drag:
                lifted = max(z, settings.slice_depth)
                plan.add("feed", settings.feed_depth)
                plan.add("linear_z", lifted, role="drag_swivel")
                plan.add("feed", settings.feed_xy)
                plan.cut_geometry(geo, role="drag_swivel")
                plan.add("feed", settings.feed_depth)
                plan.add("linear_z", z, role="drag_swivel")
                plan.add("feed", settings.feed_xy)
                continue
            used = min(geo.length, max(0.0, length - covered))
            if used > 1e-12:
                head = part(geo, 0, used / geo.length)
                count = 1
                if head.kind == "arc":
                    ratio = min(1.0, max(1e-12, plan.request.capabilities.fitting_tolerance / head.radius))
                    count = max(1, int(ceil(abs(head.sweep) / (2 * acos(1 - ratio)))))
                previous = head.start
                for index in range(1, count + 1):
                    fraction = index / count
                    point = head.end if index == count else head.arc_point(head.start_angle + head.sweep * fraction)
                    target = start_z + (settings.final_depth - start_z) * min(1.0, (covered + used * fraction) / length)
                    xy, dz = hypot(point[0]-previous[0], point[1]-previous[1]), abs(target-z)
                    duration = max(xy/settings.feed_xy, dz/settings.feed_depth)
                    plan.add("feed", sqrt(xy*xy+dz*dz)/duration)
                    if plan.request.capabilities.output_type == 'g-code':
                        plan.add("linear_xyz", previous, point, z, target, role="ramp")
                    else:
                        # Non-G-code profiles retain their own XY/Z templates.
                        plan.add('linear_z', target, role='ramp')
                        plan.add('linear_xy', previous, point, role='ramp')
                    previous, z = point, target
                plan.add("feed", settings.feed_xy)
            if used < geo.length - 1e-12:
                plan.cut_geometry(part(geo, used / geo.length, 1))
            covered += geo.length
