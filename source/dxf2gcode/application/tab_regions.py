"""Drawing-root coordinates and detached planner projections of tab regions."""
from copy import deepcopy
from dxf2gcode.domain.geometry.point import Point
from dxf2gcode.domain.geometry.linegeo import LineGeo
from dxf2gcode.domain.project.shape import Shape, Geos
from dxf2gcode.domain.project.layercontent import LayerContent, Shapes


def drawing_root(binding):
    entity = next((s.parentEntity for s in binding.sources.values() if s.parentEntity is not None), None)
    while entity is not None and entity.parent is not None:
        entity = entity.parent
    return entity


def to_world(binding, vertices):
    root = drawing_root(binding)
    return tuple((p.x, p.y) for p in (Point(*v).rot_sca_abs(parent=root) for v in vertices))


def to_drawing(binding, vertices):
    origin, xaxis, yaxis = to_world(binding, ((0, 0), (1, 0), (0, 1)))
    a, b = xaxis[0]-origin[0], yaxis[0]-origin[0]
    c, d = xaxis[1]-origin[1], yaxis[1]-origin[1]
    determinant = a*d-b*c
    if abs(determinant) < 1e-15:
        raise ValueError('Singular drawing transform')
    return tuple(((d*(x-origin[0])-b*(y-origin[1]))/determinant,
                  (a*(y-origin[1])-c*(x-origin[0]))/determinant) for x, y in vertices)


def world_vertices(binding, region):
    if region.vertices:
        return to_world(binding, region.vertices)
    source = binding.sources.get(region.geometry_id)
    return tuple((geo.Ps.x, geo.Ps.y) for geo in source.geos.abs_iter()) if source else ()


def rectangle_size(vertices):
    from math import hypot
    return tuple(hypot(vertices[i+1][0]-vertices[0][0], vertices[i+1][1]-vertices[0][1])
                 for i in (0, 2))


def configured_tab_length(configuration, units):
    length = float(configuration.get('Tab_Regions', {}).get('tab_length', 2.))
    if configuration.get('General', {}).get('tool_units', 'mm') != units:
        length *= 25.4 if units == 'mm' else 1/25.4
    return length


def resize_automatic_regions(binding, before, after, length=None):
    """Apply diameter changes in the same transaction as the tool command."""
    from copy import copy
    from dxf2gcode.domain.project.machining_project import MachiningOperation
    old = {e.id: before.tools[s.tool_id].tool_diameter for s in before.steps
           for e in s.entries if isinstance(e, MachiningOperation)}
    new = {e.id: (s, e, after.tools[s.tool_id].tool_diameter) for s in after.steps
           for e in s.entries if isinstance(e, MachiningOperation)}
    changed = {identity for identity in old.keys() & new.keys() if old[identity] != new[identity][2]}
    if not changed or before.units != after.units or not any(r.placement_mode == 'snap' for r in after.regions.values()):
        return
    staged = copy(binding)
    staged.project = after
    length = configured_tab_length(after.configuration, after.units) if length is None else length
    original = copy(binding)
    original.project = before
    for region in list(after.regions.values()):
        if region.placement_mode != 'snap' or region.id not in before.regions:
            continue
        previous = before.regions[region.id]
        eligible = {e for _, e in overlapping_operations(original, previous)}
        assigned = {e.id for step in before.steps for e in step.entries
                    if isinstance(e, MachiningOperation) and e.id in eligible and
                    e.id not in previous.excluded and
                    (previous.scope == 'global' or previous.scope == 'steps' and step.id in previous.targets or
                     previous.scope == 'operations' and e.id in previous.targets)}
        candidates = [new[identity] for identity in new if identity in assigned]
        affected = changed.intersection(assigned)
        if not affected:
            continue
        vertices = world_vertices(staged, region)
        centre = tuple(sum(p[j] for p in vertices)/len(vertices) for j in (0, 1))
        def update_size(target, entry, diameter):
            square = square_on_contour(nominal_contour(staged.sources[entry.geometry_id]), centre, diameter+length)
            target.vertices = to_drawing(staged, square)
        if len({diameter for _, _, diameter in candidates}) > 1:
            from dxf2gcode.domain.project.machining_project import new_id
            # Preserve the original ID for an unaffected use when possible.
            candidates.sort(key=lambda pair: pair[1].id in affected)
            template = deepcopy(region)
            for index, (step, entry, diameter) in enumerate(candidates):
                target = region if index == 0 else deepcopy(template)
                if index:
                    target.id = new_id()
                target.name = template.name+' / '+step.name
                target.scope, target.targets, target.excluded = 'operations', [entry.id], []
                if entry.id in affected:
                    update_size(target, entry, diameter)
                after.regions[target.id] = target
        else:
            step, entry, diameter = next(pair for pair in candidates if pair[1].id in affected)
            update_size(region, entry, diameter)
            # An operation may have moved to a new tool step in this command.
            if region.scope == 'steps' and any(s.id not in region.targets for s, _, _ in candidates):
                region.scope, region.targets = 'operations', [e.id for _, e, _ in candidates]


def resize_rectangle(vertices, axis, value):
    """Change one edge length about the centre, keeping the other edge intact."""
    from math import isfinite
    size = rectangle_size(vertices)
    if not isfinite(value) or value <= 0 or min(size) <= 1e-12:
        raise ValueError('Invalid rectangle size')
    centre = tuple(sum(p[j] for p in vertices)/4 for j in (0, 1))
    u = tuple((vertices[1][j]-vertices[0][j])/2 for j in (0, 1))
    v = tuple((vertices[3][j]-vertices[0][j])/2 for j in (0, 1))
    u = tuple(x*(value/size[0] if axis == 0 else 1) for x in u)
    v = tuple(x*(value/size[1] if axis == 1 else 1) for x in v)
    return tuple(tuple(centre[j]+a*u[j]+b*v[j] for j in (0, 1))
                 for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1)))


def align_rectangle(vertices, contacts):
    """Preserve edge lengths; align the first edge with the contact chord."""
    from math import hypot
    a, b = contacts
    length = hypot(b[0]-a[0], b[1]-a[1])
    if length <= 1e-12:
        return vertices
    width, height = rectangle_size(vertices)
    centre = ((a[0]+b[0])/2, (a[1]+b[1])/2)
    u = ((b[0]-a[0])/length, (b[1]-a[1])/length)
    # Keep the first edge's orientation stable while dragging.
    if sum(u[j]*(vertices[1][j]-vertices[0][j]) for j in (0, 1)) < 0:
        u = (-u[0], -u[1])
    v = (-u[1], u[0])
    if sum(v[j]*(vertices[3][j]-vertices[0][j]) for j in (0, 1)) < 0:
        v = (-v[0], -v[1])
    return tuple(tuple(centre[j]+x*width*u[j]/2+y*height*v[j]/2 for j in (0, 1))
                 for x, y in ((-1, -1), (1, -1), (1, 1), (-1, 1)))


def nominal_contour(source):
    from dxf2gcode.domain.geometry.arcgeo import ArcGeo
    from dxf2gcode.domain.toolpath.inputs import PathGeometry
    contour = []
    for geo in source.geos.abs_iter():
        if not isinstance(geo, (LineGeo, ArcGeo)):
            continue
        start, end = geo.get_start_end_points(True), geo.get_start_end_points(False)
        arc = dict(center=(geo.O.x, geo.O.y), radius=geo.r,
                   start_angle=geo.s_ang, end_angle=geo.e_ang, sweep=geo.ext) if isinstance(geo, ArcGeo) else {}
        contour.append(PathGeometry('arc' if arc else 'line', (start.x, start.y),
                                    (end.x, end.y), geo.length, **arc))
    return tuple(contour)


def alignment_candidates(binding, vertices):
    """One candidate per original contour, independent of repeated machining uses."""
    from dxf2gcode.domain.project.machining_project import MachiningOperation
    from dxf2gcode.domain.toolpath.tabs import region_crossings
    tolerance = binding.project.configuration['Import_Parameters']['point_tolerance']
    identities = dict.fromkeys(e.geometry_id for s in binding.project.steps if s.kind in ('contour', 'pocket')
                               for e in s.entries if isinstance(e, MachiningOperation))
    result = {}
    for identity in identities:
        source = binding.sources.get(identity)
        if source is not None:
            contacts = region_crossings(nominal_contour(source), vertices, tolerance)
            if len(contacts) == 2:
                result[identity] = contacts
    return result


def square_on_contour(contour, position, side):
    """Place a square on the nearest nominal point, with one edge tangent."""
    from math import atan2, cos, sin, hypot, pi, isfinite
    from dxf2gcode.domain.toolpath.tabs import point, region_crossings
    if not isfinite(side) or side <= 0:
        raise ValueError('Invalid square size')
    candidates = []
    for geo in contour:
        fractions = [0., 1.]
        if geo.kind == 'arc' and abs(geo.sweep) > 1e-15:
            angle = atan2(position[1]-geo.center[1], position[0]-geo.center[0])
            advance = ((angle-geo.start_angle) if geo.sweep > 0 else (geo.start_angle-angle)) % (2*pi)
            fraction = advance/abs(geo.sweep)
            if fraction <= 1:
                fractions.append(fraction)
        elif geo.kind == 'line' and geo.length > 1e-15:
            delta = tuple(geo.end[j]-geo.start[j] for j in (0, 1))
            fraction = sum((position[j]-geo.start[j])*delta[j] for j in (0, 1))/sum(x*x for x in delta)
            fractions.append(max(0., min(1., fraction)))
        for fraction in fractions:
            xy = point(geo, fraction)
            candidates.append((hypot(xy[0]-position[0], xy[1]-position[1]), xy, geo, fraction))
    if not candidates:
        raise ValueError('No supported contour geometry')
    _, centre, geo, fraction = min(candidates, key=lambda item: item[0])
    if geo.kind == 'arc':
        angle = geo.start_angle+fraction*geo.sweep
        u = (-sin(angle), cos(angle))
    else:
        length = hypot(geo.end[0]-geo.start[0], geo.end[1]-geo.start[1])
        if length <= 1e-15:
            raise ValueError('Degenerate contour')
        u = tuple((geo.end[j]-geo.start[j])/length for j in (0, 1))
    v = (-u[1], u[0])
    vertices = tuple(tuple(centre[j]+side*(x*u[j]+y*v[j])/2 for j in (0, 1))
                     for x, y in ((-1, -1), (1, -1), (1, 1), (-1, 1)))
    contacts = region_crossings(contour, vertices)
    return align_rectangle(vertices, contacts) if len(contacts) == 2 else vertices


def overlapping_operations(binding, region):
    """Geometrically eligible assignments, including repeated machining uses."""
    from dxf2gcode.domain.project.machining_project import MachiningOperation
    from dxf2gcode.domain.toolpath.tabs import contour_crosses_region
    vertices = world_vertices(binding, region)
    tolerance = binding.project.configuration['Import_Parameters']['point_tolerance']
    cache, matches = {}, []
    for step in binding.project.steps:
        if step.kind not in ('contour', 'pocket'):
            continue
        for entry in step.entries:
            if not isinstance(entry, MachiningOperation):
                continue
            source = binding.sources.get(entry.geometry_id)
            if source is None:
                continue
            if entry.geometry_id not in cache:
                cache[entry.geometry_id] = contour_crosses_region(nominal_contour(source), vertices, tolerance)
            if cache[entry.geometry_id]:
                matches.append((step.id, entry.id))
    return tuple(matches)


def materialize_regions(binding, configuration):
    layer = LayerContent(-1, 'BREAKS:', [], config=configuration)
    layer.shapes = Shapes()
    for region in binding.project.regions.values():
        vertices = world_vertices(binding, region)
        if region.vertices:
            geos = Geos(LineGeo(Point(*a), Point(*b)) for a, b in zip(vertices, vertices[1:]+vertices[:1]))
        else:
            source = binding.sources.get(region.geometry_id)
            if source is None:
                continue
            geos = deepcopy(Geos(source.geos.abs_iter()))
        shape = Shape(len(layer.shapes), True, geos=geos, config=configuration)
        shape.parentLayer = layer
        shape.parentEntity = None
        shape.operation_id = region.id
        shape.region_definition = region
        shape.disabled = not region.enabled
        shape.axis3_mill_depth, shape.f_g1_plane, shape.f_g1_depth = region.height, region.xy_feed, region.z_feed
        shape.axis3_start_mill_depth = configuration.vars.Depth_Coordinates['axis3_start_mill_depth']
        layer.shapes.append(shape)
    return layer
