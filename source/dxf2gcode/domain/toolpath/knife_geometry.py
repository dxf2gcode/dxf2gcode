"""Tip geometry and exact passive-knife holder geometry, independent of Qt."""

from dataclasses import replace
from math import atan2, cos, hypot, pi, sin, sqrt

from dxf2gcode.domain.toolpath.inputs import PathGeometry
from dxf2gcode.domain.toolpath.leadmove import build_lead_in, build_lead_out, SPACE_NOMINAL, ERROR
from dxf2gcode.domain.geometry.point import Point


def tangent(geo, end=False):
    if geo.kind == 'line':
        return atan2(geo.end[1] - geo.start[1], geo.end[0] - geo.start[0])
    return (geo.end_angle if end else geo.start_angle) + (pi / 2 if geo.sweep > 0 else -pi / 2)


def shifted(point, angle, distance):
    return (point[0] + distance * cos(angle), point[1] + distance * sin(angle))


def part(geo, start, end):
    """Keep a fractional interval of a tip line or arc, including a full circle."""
    if geo.kind == 'line':
        def at(f):
            return tuple(a + f * (b - a) for a, b in zip(geo.start, geo.end))
        return replace(geo, start=at(start), end=at(end), length=geo.length * (end - start))
    a, b = geo.start_angle + geo.sweep * start, geo.start_angle + geo.sweep * end
    return replace(geo, start=geo.arc_point(a), end=geo.arc_point(b),
                   start_angle=a, end_angle=b, sweep=b - a,
                   length=geo.length * (end - start))


def prefix(chain, length):
    result = []
    for geo in chain:
        if length <= 1e-10:
            break
        used = min(geo.length, length)
        if used > 0:
            result.append(part(geo, 0, used / geo.length))
        length -= used
    return tuple(result)


def rotated(chain, distance):
    """A closed chain starting at an arclength position, without a jump."""
    total = sum(g.length for g in chain)
    distance %= total
    if distance <= 1e-10:
        return chain
    tail, remaining = [], distance
    for geo in chain:
        if remaining >= geo.length - 1e-10:
            remaining -= geo.length
            continue
        tail.append(part(geo, remaining / geo.length, 1))
        remaining = 0.0
    return tuple(tail) + prefix(chain, distance)


def holder(geo, offset):
    start = shifted(geo.start, tangent(geo), offset)
    end = shifted(geo.end, tangent(geo, True), offset)
    if geo.kind == 'line':
        return replace(geo, start=start, end=end)
    radius = sqrt(geo.radius ** 2 + offset ** 2)
    angle = atan2(start[1] - geo.center[1], start[0] - geo.center[0])
    return replace(geo, start=start, end=end, radius=radius,
                   start_angle=angle, end_angle=angle + geo.sweep,
                   length=radius * abs(geo.sweep))


def swivel(point, previous, target, offset):
    sweep = (target - previous + pi) % (2 * pi) - pi
    if offset <= 1e-12 or abs(sweep) <= 1e-10:
        return None
    return PathGeometry('arc', shifted(point, previous, offset),
                        shifted(point, previous + sweep, offset),
                        abs(sweep) * offset, center=point, radius=offset,
                        start_angle=previous, end_angle=previous + sweep,
                        sweep=sweep, drag=True)


def lead(geo, mode, radius, length, side, entering):
    if mode == 'off':
        return ()
    point = geo.start if entering else geo.end
    angle = tangent(geo, not entering)
    builder = build_lead_in if entering else build_lead_out
    kwargs = dict(length=length)
    if entering:
        kwargs['use_lead_length'] = True
    geos, status, message = builder(Point(*point), angle, side, radius, 0.0,
                                    SPACE_NOMINAL, mode, **kwargs)
    if status == ERROR:
        raise ValueError(message)
    result = []
    for item in geos:
        start, end = (item.Ps.x, item.Ps.y), (item.Pe.x, item.Pe.y)
        if hasattr(item, 'O'):
            result.append(PathGeometry('arc', start, end, item.length,
                          center=(item.O.x, item.O.y), radius=item.r,
                          start_angle=item.s_ang, end_angle=item.s_ang + item.ext,
                          sweep=item.ext))
        else:
            result.append(PathGeometry('line', start, end, hypot(end[0]-start[0], end[1]-start[1])))
    return tuple(result)
