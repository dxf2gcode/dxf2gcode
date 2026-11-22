"""Immutable, renderer-independent projections; never plan or change a project."""

from dataclasses import dataclass
from math import cos, hypot, isfinite, pi, sin
from functools import lru_cache

from dxf2gcode.application.toolpath.projections import plan_preview_segments


@dataclass(frozen=True)
class ScenePath:
    identity: str
    geometry: str
    kind: str
    segments: tuple
    title: str = ''
    enabled: bool = True
    plan: object = None
    diagnostic: str = ''

    def projected(self, spatial=True):
        if spatial or self.plan is None:
            return self.segments
        # Deduplicate depth passes using the same semantic projection as 2D.
        return tuple(((*s.start, 0.), (*s.end, 0.), s.role)
                     for s in plan_preview_segments(self.plan, dimensions=2))


@dataclass(frozen=True)
class ViewScene:
    paths: tuple = ()
    units: str = 'mm'


@dataclass(frozen=True)
class PreviewToolBody:
    identity: str
    position: tuple
    radius: float
    length: float

    @property
    def corners(self):
        x, y, z = self.position
        return tuple((a, b, c) for a in (x-self.radius, x+self.radius)
                     for b in (y-self.radius, y+self.radius) for c in (z, z+self.length))


def preview_tool_bodies(scene, selected, spatial=True):
    """Visual-only cylinders; length is four diameters, never a tool-table value."""
    bodies = []
    for path in scene.paths:
        if path.kind != 'operation' or path.identity not in selected or not path.enabled or path.plan is None:
            continue
        radius = getattr(path.plan, 'tool_radius', 0.)
        segments = path.projected(spatial)
        if radius > 0 and isfinite(radius) and segments:
            bodies.append(PreviewToolBody(path.identity, segments[0][0], radius, radius*8))
    return tuple(bodies)


@lru_cache(maxsize=1)
def tool_cylinder_mesh(sides=48):
    """Shared unit cylinder, Z-up, with matching triangles/normals in both views."""
    ring = [(cos(2*pi*i/sides), sin(2*pi*i/sides)) for i in range(sides)]
    vertices = tuple((x, y, z) for z in (0., 1.) for x, y in ring)
    normals = tuple((x, y, 0.) for _ in (0, 1) for x, y in ring)
    faces = []
    for i in range(sides):
        j = (i+1) % sides
        faces.extend(((i, j, sides+i), (j, sides+j, sides+i)))
    for z, normal in ((0., -1.), (1., 1.)):
        offset = len(vertices)
        vertices += tuple((x, y, z) for x, y in ring) + ((0., 0., z),)
        normals += ((0., 0., normal),)*(sides+1)
        for i in range(sides):
            j = (i+1) % sides
            faces.append((offset+sides, offset+j, offset+i) if z == 0 else
                         (offset+sides, offset+i, offset+j))
    return vertices, normals, tuple(faces)


def segment_distance(point, start, end):
    """Screen-space hit distance, including zero-length/drilling segments."""
    dx, dy = end[0]-start[0], end[1]-start[1]
    length = dx*dx + dy*dy
    t = max(0., min(1., ((point[0]-start[0])*dx +
                        (point[1]-start[1])*dy)/length)) if length else 0.
    return hypot(point[0]-start[0]-t*dx, point[1]-start[1]-t*dy)


def hit_paths(scene, point, project, spatial=True, tolerance=7., show_disabled=False,
              kinds=('operation', 'region')):
    """Return stable operation/region IDs nearest first, without choosing one.

    Original contours are visual references. Resolve overlapping operations in
    the UI instead of silently changing all operations of the same geometry.
    """
    hits = []
    for path in scene.paths:
        if path.kind not in kinds or not path.enabled and not show_disabled:
            continue
        distance = min((segment_distance(point, project(start), project(end))
                        for start, end, _ in path.projected(spatial)), default=float('inf'))
        if distance <= tolerance:
            hits.append((distance, path.identity))
    return tuple(identity for _, identity in sorted(hits, key=lambda hit: hit[0]))
