"""Map nominal contour tab intervals onto a prepared tool-centre path.

Only values cross this boundary. Regions never intersect the compensated path:
line normals and concentric arc radii preserve the nominal point of contact.
"""
from dataclasses import dataclass, replace
from math import atan2, cos, sin, hypot, pi, sqrt


@dataclass(frozen=True)
class TabRegion:
    vertices: tuple
    height: float
    xy_feed: float
    z_feed: float
    identity: str = ''


def point(geo, fraction):
    if geo.kind == 'arc':
        angle = geo.start_angle + fraction * geo.sweep
        return (geo.center[0] + geo.radius*cos(angle), geo.center[1] + geo.radius*sin(angle))
    return tuple(a + fraction*(b-a) for a, b in zip(geo.start, geo.end))


def portion(geo, first, last):
    return replace(geo, start=point(geo, first), end=point(geo, last),
                   length=geo.length*(last-first), absolute=None,
                   start_angle=geo.start_angle+first*geo.sweep,
                   end_angle=geo.start_angle+last*geo.sweep,
                   sweep=geo.sweep*(last-first))


def _cross(a, b):
    return a[0]*b[1]-a[1]*b[0]


def _sub(a, b):
    return a[0]-b[0], a[1]-b[1]


def _distance(a, b):
    return hypot(a[0]-b[0], a[1]-b[1])


def _arc_fraction(geo, xy):
    angle = atan2(xy[1]-geo.center[1], xy[0]-geo.center[0])
    advance = (angle-geo.start_angle) % (2*pi) if geo.sweep > 0 else (geo.start_angle-angle) % (2*pi)
    return advance/abs(geo.sweep)


def _inside(xy, vertices, tolerance):
    inside = False
    for a, b in zip(vertices, vertices[1:]+vertices[:1]):
        delta, rel = _sub(b, a), _sub(xy, a)
        length = hypot(*delta)
        if length <= tolerance:
            continue
        along = sum(x*y for x, y in zip(delta, rel))/length
        if abs(_cross(delta, rel))/length <= tolerance and -tolerance <= along <= length+tolerance:
            return True
        if (a[1] > xy[1]) != (b[1] > xy[1]):
            if xy[0] < a[0]+(xy[1]-a[1])*(b[0]-a[0])/(b[1]-a[1]):
                inside = not inside
    return inside


def _crossings(geo, vertices):
    result = [0., 1.]
    for a, b in zip(vertices, vertices[1:]+vertices[:1]):
        edge = _sub(b, a)
        if geo.kind == 'line':
            direction = _sub(geo.end, geo.start)
            denominator = _cross(direction, edge)
            if abs(denominator) < 1e-14:
                continue
            rel = _sub(a, geo.start)
            t, u = _cross(rel, edge)/denominator, _cross(rel, direction)/denominator
            if -1e-10 <= u <= 1+1e-10 and 0 < t < 1:
                result.append(t)
        elif geo.kind == 'arc':
            rel = _sub(a, geo.center)
            aa = sum(v*v for v in edge)
            if aa < 1e-24:
                continue
            bb = 2*sum(x*y for x, y in zip(edge, rel))
            cc = sum(v*v for v in rel)-geo.radius**2
            discriminant = bb*bb-4*aa*cc
            if discriminant <= 0:
                continue
            for u in ((-bb-sqrt(discriminant))/(2*aa), (-bb+sqrt(discriminant))/(2*aa)):
                if -1e-10 <= u <= 1+1e-10:
                    xy = (a[0]+u*edge[0], a[1]+u*edge[1])
                    t = _arc_fraction(geo, xy)
                    if 0 < t < 1:
                        result.append(t)
    return _unique(result)


def _unique(values):
    result = []
    for value in sorted(values):
        if not result or value-result[-1] > 1e-10:
            result.append(value)
    return result


def _nominal_spans(contour, regions, tolerance, closed):
    spans, group = [], -1
    previous = None
    for index, geo in enumerate(contour):
        cuts = _unique([t for region in regions for t in _crossings(geo, region.vertices)])
        for a, b in zip(cuts, cuts[1:]):
            region = next((r for r in regions if _inside(point(geo, (a+b)/2), r.vertices, tolerance)), None)
            if region is None:
                previous = None
                continue
            if previous is not region:
                group += 1
            spans.append((index, a, b, region, group))
            previous = region
        if index+1 < len(contour) and _distance(geo.end, contour[index+1].start) > tolerance:
            previous = None
    if closed and len(spans) > 1:
        first, last = spans[0], spans[-1]
        if (first[0] == 0 and first[1] == 0 and last[0] == len(contour)-1 and last[2] == 1
                and first[3] is last[3] and _distance(contour[-1].end, contour[0].start) <= tolerance):
            spans = [(*span[:4], first[4] if span[4] == last[4] else span[4]) for span in spans]
    return spans


def _sections(geo, contour, offset, tolerance):
    """Return (source index, path range, source parameter at path 0/1).

    Constant source parameters describe round joins centred on a contour vertex.
    Collinear source segments can share a single prepared path segment.
    """
    result = []
    for index, source in enumerate(contour):
        if source.kind == geo.kind == 'line':
            direction = _sub(source.end, source.start)
            length = hypot(*direction)
            path_direction = _sub(geo.end, geo.start)
            if length <= tolerance or abs(_cross(direction, path_direction)) > tolerance*length:
                continue
            distance = abs(_cross(direction, _sub(geo.start, source.start)))/length
            if abs(distance-offset) > tolerance:
                continue
            a, b = [sum(x*y for x, y in zip(_sub(p, source.start), direction))/length**2
                    for p in (geo.start, geo.end)]
            if abs(b-a) < 1e-12:
                continue
            low, high = sorted(((0-a)/(b-a), (1-a)/(b-a)))
            low, high = max(0., low), min(1., high)
            if high > low+1e-10:
                result.append((index, low, high, a, b))
        elif source.kind == geo.kind == 'arc' and _distance(source.center, geo.center) <= tolerance:
            if abs(abs(geo.radius-source.radius)-offset) > tolerance:
                continue
            # Unwrap the target arc relative to the finite source arc.
            a = _arc_fraction(source, point(geo, 0))
            delta = geo.sweep/source.sweep
            period = 2*pi/abs(source.sweep)
            for turn in (-1, 0, 1):
                start = a+turn*period
                low, high = sorted(((0-start)/delta, (1-start)/delta))
                low, high = max(0., low), min(1., high)
                if high > low+1e-10:
                    result.append((index, low, high, start, start+delta))
    if geo.kind == 'arc' and abs(geo.radius-offset) <= tolerance:
        for index, source in enumerate(contour):
            for fraction, vertex in ((0., source.start), (1., source.end)):
                if _distance(geo.center, vertex) <= tolerance:
                    result.append((index, 0., 1., fraction, fraction))
    return result


def map_tabs(contour, path, regions, offset=0., closed=True, tolerance=1e-7):
    """Return a split path and skipped nominal tab groups (export may continue)."""
    if not regions:
        return path, ()
    contour = tuple(geo.resolved for geo in contour)
    spans = _nominal_spans(contour, regions, tolerance, closed)
    if not spans:
        return path, ()
    sections = [_sections(geo.resolved, contour, offset, tolerance) if geo.kind in ('line', 'arc') else []
                for geo in path]
    skipped = set()
    # Validate both ends of each connected nominal tab. A vanished/ambiguous
    # boundary must not produce a different tab by intersecting the offset.
    for span in spans:
        index, a, b, region, group = span
        for fraction in (a, b):
            xy = point(contour[index], fraction)
            shared = sum(1 for other in spans if other[4] == group for t in (other[1], other[2])
                         if _distance(point(contour[other[0]], t), xy) <= tolerance)
            if shared > 1:
                continue
            matches = []
            for geo, candidates in zip(path, sections):
                for source, low, high, first, last in candidates:
                    if source != index:
                        continue
                    if abs(last-first) < 1e-12:
                        points = (geo.start, geo.end) if abs(fraction-first) < 1e-10 else ()
                    else:
                        t = (fraction-first)/(last-first)
                        points = (point(geo, min(1., max(0., t))),) if low-1e-10 <= t <= high+1e-10 else ()
                    for match in points:
                        if not any(_distance(match, old) <= tolerance for old in matches):
                            matches.append(match)
            if len(matches) != 1:
                skipped.add(group)
    pieces, piece_groups = [], []
    for geo, candidates in zip(path, sections):
        cuts = [0., 1.]
        for source, low, high, first, last in candidates:
            cuts.extend((low, high))
            if abs(last-first) < 1e-12:
                continue
            for index, a, b, _, group in spans:
                if source == index and group not in skipped:
                    cuts.extend(t for t in ((a-first)/(last-first), (b-first)/(last-first)) if low < t < high)
        cuts = _unique(cuts)
        for a, b in zip(cuts, cuts[1:]):
            middle = (a+b)/2
            active = []
            feet = []
            for source, low, high, first, last in candidates:
                if low-1e-10 <= middle <= high+1e-10:
                    fraction = first+middle*(last-first)
                    feet.append(point(contour[source], fraction))
                    for index, start, end, region, group in spans:
                        if index == source and group not in skipped and start-1e-10 <= fraction <= end+1e-10:
                            active.append((region, group))
            part = portion(geo, a, b) if a != 0 or b != 1 else geo
            if active and any(_distance(feet[0], xy) > tolerance for xy in feet[1:]):
                skipped.update(group for _, group in active)
                active = []
            if active:
                region, group = active[0]
                part = replace(part, kind='break', height=region.height, xy_feed=region.xy_feed,
                               z_feed=region.z_feed, modifier_id=region.identity, tab_geometry=part)
            pieces.append(part)
            piece_groups.append(active[0][1] if active else None)
    for group in set(g for g in piece_groups if g is not None):
        indices = [i for i, g in enumerate(piece_groups) if g == group]
        runs = 1 + sum(b != a+1 for a, b in zip(indices, indices[1:]))
        seam = closed and indices[0] == 0 and indices[-1] == len(pieces)-1
        if runs > (2 if seam else 1):
            skipped.add(group)
        if any(_distance(pieces[a].end, pieces[b].start) > tolerance
               for a, b in zip(indices, indices[1:]) if b == a+1):
            skipped.add(group)
    # A late ambiguity invalidates the entire connected tab, including pieces
    # already visited, while other tabs from the same region remain intact.
    return tuple(p.tab_geometry if group in skipped and p.kind == 'break' else p
                 for p, group in zip(pieces, piece_groups)), tuple(sorted(skipped))
