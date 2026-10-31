"""Small projections of semantic toolpath plans for presentation layers."""

from math import atan2, ceil, cos, pi, sin
from dataclasses import dataclass
from dxf2gcode.domain.toolpath.plan import ToolpathMove


@dataclass(frozen=True)
class PreviewSegment:
    start: tuple
    end: tuple
    role: str
    space: str


def plan_preview_segments(plan, dimensions=3):
    """Project ordered actions, retaining movement roles and compensation space."""
    if plan is None:
        return ()
    xy, z = plan.approach_xy, plan.workpiece_top
    segments, seen = [], set()

    def add(start, end, role):
        if dimensions == 2:
            start, end = start[:2], end[:2]
            if start == end:
                return
            key = (role, tuple(sorted(tuple(round(v, 12) for v in p)
                                      for p in (start, end))))
            if key in seen:
                return
            seen.add(key)
        segments.append(PreviewSegment(start, end, role, plan.compensation_space))

    for action in plan.actions:
        kind, args = action.kind, action.args
        if kind == "rapid_xy":
            add((*xy, z), (*args[0], z), "rapid")
            xy = args[0]
        elif kind in ("rapid_z", "linear_z", "drill", "drill_retract"):
            add((*xy, z), (*xy, args[0]),
                "rapid" if kind in ("rapid_z", "drill_retract") else action.role)
            z = args[0]
        elif kind in ("linear_xy", "arc"):
            move = (ToolpathMove("linear_xy", *args) if kind == "linear_xy" else
                    ToolpathMove("arc", args[1], args[2], args[6],
                                 abs(args[8]) if args[0] == "ccw" else -abs(args[8])))
            for start, end in _move_segments(move):
                add((*start, z), (*end, z), action.role)
            xy = move.end_xy
    return tuple(segments)


def _move_segments(move):
    if move.kind != "arc" or move.center_xy is None:
        return ((move.start_xy, move.end_xy),)
    cx, cy = move.center_xy
    sx, sy = move.start_xy
    radius = ((sx - cx) ** 2 + (sy - cy) ** 2) ** 0.5
    start_angle = atan2(sy - cy, sx - cx)
    count = max(1, int(ceil(abs(move.sweep) / (pi / 36.0))))
    points = [move.start_xy]
    for index in range(1, count):
        angle = start_angle + move.sweep * index / count
        points.append((cx + radius * cos(angle), cy + radius * sin(angle)))
    points.append(move.end_xy)
    return tuple(zip(points, points[1:]))


def plan_xy_segments(plan):
    """Return the XY contour once, even when the plan has several depth passes."""
    if not plan.passes:
        # Drill actions have no cutting XY moves. Keep the tool-sized hole
        # marker using the position and tool captured in the same plan.
        if not any(a.kind in ("drill", "hole_marker") for a in plan.actions):
            return ()
        x, y = plan.approach_xy
        points = [(x + plan.tool_radius * cos(i * pi / 18),
                   y + plan.tool_radius * sin(i * pi / 18)) for i in range(36)]
        return tuple(zip(points, points[1:] + points[:1]))
    seen = set()
    segments = []
    for toolpath_pass in plan.passes:
        for move in toolpath_pass.moves:
            for segment in _move_segments(move):
                # Opposite pass directions cover the same XY line. Rounding
                # absorbs floating-point noise from tessellating reversed arcs.
                key = tuple(sorted(tuple(round(value, 12) for value in point)
                                   for point in segment))
                if key not in seen:
                    seen.add(key)
                    segments.append(segment)
    return tuple(segments)


def plan_xyz_segments(plan):
    """Project plan XY moves at the top surface and at each cutting depth."""
    segments = []

    if not plan.passes and any(a.kind in ("drill", "hole_marker")
                               for a in plan.actions):
        xy, z = plan.approach_xy, plan.workpiece_top
        for action in plan.actions:
            if action.kind == "rapid_xy":
                xy = action.args[0]
            elif action.kind in ("rapid_z", "linear_z", "drill", "drill_retract"):
                target = action.args[0]
                if action.kind != "rapid_z" or action.role == "retract":
                    segments.append(((*xy, z), (*xy, target)))
                z = target
        return tuple(segments)

    def add_pass_moves(toolpath_pass, depth):
        for move in toolpath_pass.moves:
            for start_xy, end_xy in _move_segments(move):
                start = (start_xy[0], start_xy[1], depth)
                end = (end_xy[0], end_xy[1], depth)
                segments.append((start, end))

    if plan.passes:
        add_pass_moves(plan.passes[0], plan.workpiece_top)
        for toolpath_pass in plan.passes:
            add_pass_moves(toolpath_pass, toolpath_pass.depth)
    return tuple(segments)
