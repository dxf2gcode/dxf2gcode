"""Continuous tip-aware drag-knife passes with explicit entry and exit geometry."""

from math import acos, ceil, hypot, isfinite, pi, radians, sqrt
from dataclasses import replace

from dxf2gcode.domain.toolpath.inputs import reverse_chain
from dxf2gcode.domain.toolpath.knife_geometry import tangent, shifted, part, prefix, rotated, holder, swivel, lead
from dxf2gcode.domain.toolpath.movements import MovementPlan
from dxf2gcode.domain.toolpath.messages import QT_TRANSLATE_NOOP


INVALID = QT_TRANSLATE_NOOP('Shape', 'Invalid drag-knife settings or contour.')
SHORT_RAMP = QT_TRANSLATE_NOOP('Shape', 'The drag-knife ramp is longer than the available cutting path.')
SHORT_LEAD = QT_TRANSLATE_NOOP('Shape', 'The drag-knife lead is too short for external alignment.')
TURN_LEADS = QT_TRANSLATE_NOOP('Shape', 'Alternating drag-knife cuts require straight lead in and lead out.')
UNKNOWN_ENTRY = QT_TRANSLATE_NOOP('Shape', 'Unknown knife orientation requires an external lead and an alignment length of at least twice the knife offset.')
RETURN_LEAD = QT_TRANSLATE_NOOP('Shape', 'Knife return alignment requires a lead out.')


class KnifePassStrategy:
    def plan(self, request):
        # One builder per request; no mutable state is shared between shapes.
        return _KnifePassBuilder(request).build()


class _KnifePassBuilder:
    def __init__(self, request):
        self.request, self.s = request, request.settings
        self.plan = MovementPlan(request)
        self.heading = radians(self.s.drag_start_angle)
        if self.s.drag_entry_mode == 'previous' and request.initial_state.knife_heading is not None:
            self.heading = request.initial_state.knife_heading
        self.z = self.s.workpiece_top
        self.started = False

    def set_z(self, z, role):
        self.plan.add('feed', self.s.feed_depth)
        self.plan.add('linear_z', z, role=role)
        self.z = z
        self.plan.add('feed', self.s.feed_xy)

    def align(self, tip, heading, depth):
        arc = swivel(tip, self.heading, heading, self.s.tool_radius)
        if arc is not None:
            lifted = abs(arc.sweep) > self.s.drag_angle
            if lifted:
                self.set_z(max(depth, self.s.drag_swivel_depth), 'drag_swivel')
            self.plan.geometry(arc, role='drag_swivel')
            if lifted:
                self.set_z(depth, 'drag_swivel')
        self.heading = heading

    def run(self, chain, target, role='cut', ramp=0.0):
        """Ramp distance is measured on the tip path; swivels consume no ramp."""
        start_z, covered = self.z, 0.0
        total = sum(g.length for g in chain)
        if ramp > total + 1e-9:
            raise ValueError(SHORT_RAMP)
        if ramp <= 0 and self.z != target:
            self.set_z(target, 'plunge')
        for geo in chain:
            self.align(geo.start, tangent(geo), self.z)
            ramp_used = min(geo.length, max(0.0, ramp - covered))
            if ramp_used > 1e-10:
                tip = part(geo, 0, ramp_used / geo.length)
                center = holder(tip, self.s.tool_radius)
                # Arc ramps are tessellated to the configured geometric tolerance.
                count = 1
                if center.kind == 'arc':
                    ratio = min(1.0, max(1e-12, self.request.capabilities.fitting_tolerance / center.radius))
                    count = max(1, int(ceil(abs(center.sweep) / (2 * acos(1 - ratio)))))
                previous = center.start
                for index in range(1, count + 1):
                    f = index / count
                    end = center.end if index == count else center.arc_point(center.start_angle + center.sweep * f)
                    z = start_z + (target - start_z) * min(1.0, (covered + ramp_used * f) / ramp)
                    # Cap resultant feed so neither XY nor Z exceeds its limit.
                    xy = hypot(end[0] - previous[0], end[1] - previous[1])
                    dz = abs(z - self.z)
                    duration = max(xy / self.s.feed_xy, dz / self.s.feed_depth)
                    self.plan.add('feed', sqrt(xy * xy + dz * dz) / duration)
                    self.plan.add('linear_xyz', previous, end, self.z, z, role='ramp')
                    self.z, previous = z, end
                self.plan.add('feed', self.s.feed_xy)
            if ramp_used < geo.length - 1e-10:
                tail = part(geo, ramp_used / geo.length, 1)
                self.plan.cut_geometry(holder(tail, self.s.tool_radius), role=role)
            covered += geo.length
            self.heading = tangent(geo, True)

    def start(self, chain, target, incoming):
        entry = incoming or chain
        first = entry[0]
        unknown = self.s.drag_entry_mode == 'unknown'
        if unknown:
            # This is an operator-validated settling stroke, not an angle sensor.
            aligned = shifted(first.start, tangent(first), self.s.tool_radius)
            approach = shifted(aligned, tangent(first), -self.s.drag_alignment_length)
        else:
            approach = shifted(first.start, self.heading, self.s.tool_radius)
        self.plan.add('rapid_xy', approach, role='approach')
        if not self.started:
            self.plan.add('pre_cut')
            self.started = True
        self.plan.add('rapid_z', self.s.workpiece_top + abs(self.s.safe_margin), role='approach')
        contact = max(target, self.s.drag_swivel_depth)
        self.set_z(contact, 'alignment')
        if unknown:
            self.plan.add('linear_xy', approach, aligned, role='knife_alignment')
            self.heading = tangent(first)
        else:
            self.align(first.start, tangent(first), self.z)
        if incoming:
            self.run(incoming, target, 'lead_in', self.s.drag_ramp_length)
            return 0.0
        return self.s.drag_ramp_length

    def retract(self):
        self.set_z(self.s.workpiece_top + abs(self.s.safe_margin), 'retract')
        self.plan.add('rapid_z', self.s.retract_depth, role='retract')

    def leads(self, chain):
        s = self.s
        side = s.lead_side
        if self.request.compensation == 42:
            side = -1
        elif self.request.compensation == 40 and self.request.closed:
            # Lead arcs curve into the waste side; default G40 uses the exterior.
            area = sum((g.start[0]*g.end[1] - g.end[0]*g.start[1]) if g.kind == 'line' else
                       (g.center[0]*(g.end[1]-g.start[1]) - g.center[1]*(g.end[0]-g.start[0]) + g.radius**2*g.sweep)
                       for g in chain)
            side = -1 if area >= 0 else 1
        incoming = lead(chain[0], s.lead_in_mode, s.lead_radius, s.lead_length, side, True)
        outgoing = lead(chain[-1], s.lead_out_mode, s.lead_radius, s.drag_exit_length, side, False)
        if incoming and sum(g.length for g in incoming) < max(s.drag_ramp_length, 2*s.tool_radius) - 1e-9:
            raise ValueError(SHORT_LEAD)
        return incoming, outgoing

    def build(self):
        r, s, p = self.request, self.s, self.plan
        chain = tuple(g.resolved for g in r.contour)
        numbers = (s.slice_depth, s.final_depth, s.workpiece_top, s.feed_xy,
                   s.feed_depth, s.tool_radius, s.drag_swivel_depth, s.drag_ramp_length,
                   s.lead_length, s.drag_exit_length, s.overcut_length)
        if not all(isfinite(n) for n in numbers):
            raise ValueError(INVALID)
        if s.drag_entry_mode not in ('fixed', 'previous', 'unknown'):
            raise ValueError(INVALID)
        if (not isfinite(s.drag_alignment_length) or s.drag_alignment_length < 0):
            raise ValueError(INVALID)
        if s.drag_entry_mode == 'unknown' and (s.lead_in_mode == 'off' or
                s.drag_alignment_length < 2*s.tool_radius):
            raise ValueError(UNKNOWN_ENTRY)
        if s.drag_return and s.lead_out_mode == 'off':
            raise ValueError(RETURN_LEAD)
        if (not chain or any(g.kind not in ('line', 'arc') or g.length <= 0 or not isfinite(g.length)
                             or not all(isfinite(v) for v in (*g.start, *g.end)) for g in chain)
                or s.slice_depth == 0 or s.final_depth > s.workpiece_top
                or s.feed_xy <= 0 or s.feed_depth <= 0 or s.tool_radius <= 0
                or s.drag_swivel_depth > s.workpiece_top
                or r.capabilities.output_type != 'g-code'):
            raise ValueError(INVALID)
        tolerance = s.point_tolerance
        def same(a, b):
            return hypot(a[0]-b[0], a[1]-b[1]) <= tolerance
        if (any(not same(a.end, b.start) for a,b in zip(chain, chain[1:]))
                or (r.closed and not same(chain[-1].end, chain[0].start))):
            raise ValueError(INVALID)
        if s.drag_alternate and not r.closed and (s.lead_in_mode != 'straight' or s.lead_out_mode != 'straight'):
            raise ValueError(TURN_LEADS)
        if s.drag_alternate and not r.closed and min(s.lead_length, s.drag_exit_length) < max(2*s.tool_radius, s.drag_ramp_length):
            raise ValueError(SHORT_LEAD)
        total = sum(g.length for g in chain)
        if s.overcut_enabled and s.overcut_length > total:
            raise ValueError(INVALID)
        count = max(1, int(ceil((s.workpiece_top - s.final_depth) / abs(s.slice_depth) - 1e-10)))
        depths = [max(s.final_depth, s.workpiece_top - abs(s.slice_depth) * (i+1)) for i in range(count)]
        if not r.closed and s.lead_in_mode == 'off' and s.drag_ramp_length:
            depths.append(s.final_depth)  # Mandatory coverage, independent of the optional pass.
        if s.drag_extra_pass and not r.closed:
            depths.append(s.final_depth)
        incoming, outgoing = self.leads(chain)
        ramp = self.start(chain, depths[0], incoming)
        final_ramp = 0.0
        for index, depth in enumerate(depths):
            if index:
                if r.closed:
                    ramp = s.drag_ramp_length if self.z != depth else 0.0
                elif not s.drag_alternate:
                    self.run(outgoing, self.z, 'lead_out')
                    self.retract()
                    ramp = self.start(chain, depth, incoming)
                    if depth == depths[index-1] and not incoming:
                        ramp = 0.0
                else:
                    # Exit and return share the same external tip corridor.
                    self.run(outgoing, self.z, 'lead_out')
                    chain = reverse_chain(chain)
                    incoming = reverse_chain(outgoing)
                    # The next far end uses the other independently set length.
                    other_length = s.lead_length if index % 2 else s.drag_exit_length
                    outgoing = lead(chain[-1], 'straight', s.lead_radius, other_length, s.lead_side, False)
                    self.align(incoming[0].start, tangent(incoming[0]), max(depth, s.drag_swivel_depth))
                    self.run(incoming, depth, 'lead_in', s.drag_ramp_length if self.z != depth else 0)
                    ramp = 0.0
            self.run(chain, depth, ramp=ramp)
            final_ramp = ramp
        if r.closed:
            # Automatic coverage and the optional full pass are independent.
            extension = prefix(chain, final_ramp)
            self.run(extension, s.final_depth, 'ramp_finish')
            continuation = rotated(chain, final_ramp)
            last = extension[-1] if extension else chain[-1]
            if s.drag_extra_pass:
                self.run(continuation, s.final_depth, 'extra_cut')
                last = continuation[-1]
            if s.overcut_enabled and s.overcut_length:
                overlap = prefix(continuation, s.overcut_length)
                self.run(overlap, s.final_depth, 'overcut')
                last = overlap[-1]
            outgoing = lead(last, s.lead_out_mode, s.lead_radius, s.drag_exit_length, s.lead_side, False)
        self.run(outgoing, self.z, 'lead_out')
        if s.drag_return:
            self.set_z(max(self.z, s.drag_swivel_depth), 'return_alignment')
            self.align(outgoing[-1].end, radians(s.drag_start_angle), self.z)
        self.retract()
        p.add('post_cut')
        return replace(p.finish(), knife_heading=self.heading,
                       knife_tool=(s.tool_number, s.tool_radius))
