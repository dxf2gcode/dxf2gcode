"""Project-owned machining data, independent of drawing objects and Qt."""

from copy import deepcopy
from dataclasses import dataclass, field, asdict
from math import isfinite
from uuid import uuid4

from dxf2gcode.domain.project.tool_settings import ToolSettings


def new_id():
    return str(uuid4())


PARAMETERS = frozenset((
    'axis3_start_mill_depth', 'axis3_slice_depth', 'axis3_mill_depth',
    'axis3_retract', 'axis3_safe_margin', 'f_g1_plane', 'f_g1_depth',
    'milling_offset', 'lead_in_mode', 'lead_out_mode', 'overcut_enabled',
    'lead_radius', 'lead_length', 'overcut_length', 'drag_swivel_depth',
    'drag_angle', 'cut_cor', 'break_pass', 'speed', 'start_radius'))
KINDS = frozenset(('contour', 'pocket', 'drill', 'break', 'ignored'))
TOOL_PARAMETERS = ('lead_radius', 'lead_length', 'overcut_length', 'speed', 'start_radius')


@dataclass(frozen=True)
class GeometryReference:
    id: str
    source_layer: str
    source_instance: str
    fingerprint: str


@dataclass
class MachiningOperation:
    id: str
    geometry_id: str
    overrides: dict = field(default_factory=dict)
    enabled: bool = True
    optimize: bool = True
    clockwise: bool = True
    # Start points are in contour-local coordinates, not workpiece coordinates.
    start: tuple = (0.0, 0.0)
    legacy_conflict: tuple = ()


@dataclass
class LiteralAction:
    id: str
    name: str
    gcode: str
    enabled: bool = True


@dataclass
class MachiningStep:
    id: str
    name: str
    kind: str
    tool_id: str
    defaults: dict = field(default_factory=dict)
    entries: list = field(default_factory=list)


@dataclass
class MachiningProject:
    geometries: dict = field(default_factory=dict)
    tools: dict = field(default_factory=dict)
    steps: list = field(default_factory=list)
    defaults: dict = field(default_factory=dict)
    configuration: dict = field(default_factory=dict)
    units: str = 'mm'
    unresolved: dict = field(default_factory=dict)

    def resolve(self, step, operation):
        """Resolve values and their provenance without reading a live profile."""
        tool = self.tools[step.tool_id]
        values = {key: getattr(tool, key) for key in TOOL_PARAMETERS
                  if getattr(tool, key) is not None}
        origin = {key: 'tool' for key in values}
        values.update(self.defaults)
        origin.update({key: 'project' for key in self.defaults})
        values.update(step.defaults)
        origin.update({key: 'step' for key in step.defaults})
        values.update(operation.overrides)
        origin.update({key: 'operation' for key in operation.overrides})
        return values, origin, tool

    def validate(self):
        """Structural validation; invalid machining states remain diagnosable."""
        ids = set()
        def identity(value):
            if not isinstance(value, str) or not value or value in ids:
                raise ValueError('Invalid or duplicate machining identity')
            ids.add(value)
        for key, geometry in self.geometries.items():
            identity(key)
            if geometry.id != key or not all(isinstance(value, str) for value in (
                    geometry.source_layer, geometry.source_instance, geometry.fingerprint)):
                raise ValueError('Invalid geometry reference')
        for key, tool in self.tools.items():
            identity(key)
            if type(tool.tool_nr) is not int or tool.tool_nr < 1:
                raise ValueError('Invalid project tool number')
            if any((type(value) not in (int, float) or not isfinite(value))
                   for key, value in asdict(tool).items()
                   if not (key == 'start_radius' and value is None)):
                raise ValueError('Invalid project tool values')
            if tool.tool_diameter < 0:
                raise ValueError('Invalid project tool diameter')
        def parameters(values):
            if not isinstance(values, dict) or not set(values) <= PARAMETERS:
                raise ValueError('Unknown machining parameter')
            for key, value in values.items():
                if key in ('lead_in_mode', 'lead_out_mode'):
                    if value not in ('default', 'off', 'straight', 'radius', 'startmove'):
                        raise ValueError('Invalid lead mode')
                elif key == 'overcut_enabled':
                    if value not in ('default', 'on', 'off', True, False):
                        raise ValueError('Invalid overcut state')
                elif type(value) not in (int, float) or not isfinite(value):
                    raise ValueError('Invalid numeric machining parameter')
        parameters(self.defaults)
        def data_tree(value):
            if isinstance(value, dict):
                if any(not isinstance(key, str) for key in value):
                    raise ValueError('Invalid project configuration key')
                for item in value.values():
                    data_tree(item)
            elif isinstance(value, list):
                for item in value:
                    data_tree(item)
            elif value is not None and type(value) not in (str, bool, int, float):
                raise ValueError('Invalid project configuration data')
            elif type(value) in (int, float) and not isfinite(value):
                raise ValueError('Invalid project configuration number')
        data_tree(self.configuration)
        if self.units not in ('mm', 'in'):
            raise ValueError('Invalid project units')
        for step in self.steps:
            identity(step.id)
            if (not isinstance(step.name, str) or step.kind not in KINDS
                    or step.tool_id not in self.tools):
                raise ValueError('Invalid machining step')
            parameters(step.defaults)
            for entry in step.entries:
                identity(entry.id)
                if type(entry.enabled) is not bool:
                    raise ValueError('Invalid operation activation')
                if isinstance(entry, LiteralAction):
                    if not isinstance(entry.name, str) or not isinstance(entry.gcode, str):
                        raise ValueError('Invalid literal action')
                    continue
                if not isinstance(entry, MachiningOperation) or entry.geometry_id not in self.geometries:
                    raise ValueError('Invalid operation reference')
                parameters(entry.overrides)
                if set(entry.overrides) & {'axis3_retract', 'axis3_safe_margin'}:
                    raise ValueError('Clearance values belong to the machining step')
                if type(entry.optimize) is not bool or type(entry.clockwise) is not bool:
                    raise ValueError('Invalid operation state')
                if (len(entry.start) != 2 or any(type(v) not in (int, float)
                        or not isfinite(v) for v in entry.start)):
                    raise ValueError('Invalid operation start')
                if entry.legacy_conflict and (len(entry.legacy_conflict) != 3 or
                        type(entry.legacy_conflict[0]) is not bool or
                        type(entry.legacy_conflict[1]) is not bool or
                        entry.legacy_conflict[2] not in (40, 41, 42)):
                    raise ValueError('Invalid legacy machining conflict')

    def assert_exportable(self):
        self.validate()
        missing = [entry.id for step in self.steps for entry in step.entries
                   if isinstance(entry, MachiningOperation) and entry.enabled
                   and step.kind not in ('break', 'ignored')
                   and entry.geometry_id in self.unresolved]
        if missing:
            raise ValueError('Unresolved machining geometry: ' + ', '.join(missing))

    def update_tool(self, tool_id, tool):
        """Explicit atomic update of a project tool, shared by all its steps."""
        old = self.tools[tool_id]
        self.tools[tool_id] = tool
        try:
            self.validate()
        except Exception:
            self.tools[tool_id] = old
            raise
        return old

    def to_dict(self):
        self.validate()
        return dict(geometries=[asdict(g) for g in self.geometries.values()],
                    tools={key: asdict(tool) for key, tool in self.tools.items()},
                    defaults=deepcopy(self.defaults), configuration=deepcopy(self.configuration),
                    units=self.units, steps=[dict(id=step.id, name=step.name,
                        kind=step.kind, tool_id=step.tool_id, defaults=deepcopy(step.defaults),
                        entries=[dict(type='literal' if isinstance(e, LiteralAction) else 'operation',
                                      **asdict(e)) for e in step.entries]) for step in self.steps])

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict) or set(data) != {
                'geometries', 'tools', 'defaults', 'configuration', 'units', 'steps'}:
            raise ValueError('Invalid machining project fields')
        geometries = [GeometryReference(**value) for value in data['geometries']]
        if len({g.id for g in geometries}) != len(geometries):
            raise ValueError('Duplicate geometry identity')
        result = cls({g.id: g for g in geometries},
                     {key: ToolSettings(**value) for key, value in data['tools'].items()},
                     defaults=deepcopy(data['defaults']), configuration=deepcopy(data['configuration']),
                     units=data['units'])
        for value in data['steps']:
            fields = dict(value)
            fields['entries'] = []
            for entry in value['entries']:
                entry = dict(entry)
                kind = entry.pop('type')
                if kind == 'literal':
                    fields['entries'].append(LiteralAction(**entry))
                elif kind == 'operation':
                    entry['start'] = tuple(entry['start'])
                    entry['legacy_conflict'] = tuple(entry['legacy_conflict'])
                    fields['entries'].append(MachiningOperation(**entry))
                else:
                    raise ValueError('Unknown machining entry type')
            result.steps.append(MachiningStep(**fields))
        result.validate()
        return result
