"""Bridge original drawing contours to project-owned machining operations.

The existing Shape/Layer APIs are temporary projections, never the persisted
identity of a machining step. Geometry is copied before start/direction edits.
"""

from collections import defaultdict
from contextlib import contextmanager
from copy import copy, deepcopy
from dataclasses import asdict, replace
import hashlib
import json

from dxf2gcode.domain.project.machining_project import (
    GeometryReference, LiteralAction, MachiningOperation, MachiningProject,
    MachiningStep, PARAMETERS, TOOL_PARAMETERS, new_id)
from dxf2gcode.domain.project.layercontent import LayerContent, Layers, Shapes
from dxf2gcode.domain.project.machining import machining_conflict
from dxf2gcode.domain.project.tool_settings import ToolSettings, effective_tool
from dxf2gcode.domain.geometry.point import Point
from dxf2gcode.domain.toolpath.customgcode import CustomGCode
from dxf2gcode.domain.toolpath.leadmove import (
    get_lead_in_mode, get_lead_out_mode, get_overcut_enabled)


class AttributeValues(dict):
    """Read configuration through the same mapping/attribute protocol as callers."""
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError as error:
            raise AttributeError(key) from error


def plain(value):
    if isinstance(value, dict):
        return {str(k): plain(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [plain(v) for v in value]
    if hasattr(value, '__dict__'):
        return plain(vars(value))
    return value


def attributes(value):
    return AttributeValues({key: attributes(v) for key, v in value.items()}) if isinstance(value, dict) else value


class ProjectConfiguration:
    """Effective saved machining settings, without profile I/O or Qt."""
    def __init__(self, project):
        self.vars = attributes(deepcopy(project.configuration))
        self.var_dict = self.vars
        self.machine_type = self.vars.General['machine_type']
        self.metric = int(project.units == 'mm')
        self.tool_units = project.units
        self.point_tolerance = self.vars.Import_Parameters['point_tolerance']
        self.fitting_tolerance = self.vars.Import_Parameters['fitting_tolerance']

    def update_tool_values(self):
        # The parser reports the drawing unit through metric. The snapshot
        # already uses that unit; a changed source unit requires reassignment.
        if self.vars.General.get('drawing_units_override') == self.tool_units:
            self.metric = int(self.tool_units == 'mm')
        elif self.metric != int(self.tool_units == 'mm'):
            raise ValueError('Drawing units differ from saved machining project')


def snapshot_configuration(config):
    sections = ('Cutter_Compensation', 'Pocketing', 'Drag_Knife_Options',
                'Lead_In_Out', 'Depth_Coordinates', 'Feed_Rates', 'Plane_Coordinates',
                'Route_Optimisation', 'Import_Parameters', 'Layer_Options', 'Tool_Parameters')
    values = {key: plain(getattr(config.vars, key)) for key in sections}
    for tool in values['Tool_Parameters'].values():
        # The runtime lookup returns None for this retired optional setting.
        tool.setdefault('start_radius', None)
    values['General'] = {key: config.vars.General[key] for key in (
        'machine_type', 'split_line_segments', 'automatic_cutter_compensation')}
    values['General']['machine_type'] = config.machine_type
    values['Import_Parameters'].update(point_tolerance=config.point_tolerance,
                                       fitting_tolerance=config.fitting_tolerance)
    return values


def contour_key(shape):
    """Direction-independent local geometry plus block-instance provenance."""
    candidate = copy(shape)
    candidate.geos = deepcopy(shape.geos)
    signatures = []
    for _ in range(2):
        signatures.append(tuple(sorted(_geometry_signature(geo) for geo in candidate.geos)))
        candidate.reverse()
    fingerprint = hashlib.sha256(repr((shape.closed, min(signatures))).encode('utf-8')).hexdigest()
    instances = []
    entity = shape.parentEntity
    while entity is not None and entity.parent is not None:
        instances.append((entity.name, entity.p0.x, entity.p0.y,
                          tuple(entity.sca), entity.rot, entity.pb.x, entity.pb.y))
        entity = entity.parent
    return shape.parentLayer.name, json.dumps(instances, separators=(',', ':')), fingerprint


def _geometry_signature(geo):
    # save_v1 rounds to three decimals, which is not a safe identity at the
    # supported sub-millimetre import tolerances.
    points = tuple((float(getattr(geo, key).x), float(getattr(geo, key).y))
                   if hasattr(geo, key) else () for key in ('Ps', 'Pe', 'O'))
    return (type(geo).__name__, points, float(getattr(geo, 'r', 0)),
            float(getattr(geo, 'ext', 0)))


def parameter_snapshot(shape):
    values = {key: getattr(shape, key) for key in PARAMETERS if hasattr(shape, key)}
    values.update(lead_in_mode=get_lead_in_mode(shape), lead_out_mode=get_lead_out_mode(shape),
                  overcut_enabled=get_overcut_enabled(shape))
    tool = effective_tool(shape)
    for key in ('lead_radius', 'lead_length', 'overcut_length', 'speed', 'start_radius'):
        value = getattr(tool, key)
        if value is not None:
            values[key] = value
    values['axis3_retract'] = shape.parentLayer.axis3_retract
    values['axis3_safe_margin'] = shape.parentLayer.axis3_safe_margin
    return values


def _kind(layer, shape):
    if layer.isBreakLayer():
        return 'break'
    if layer.should_ignore():
        return 'ignored'
    return 'drill' if shape.Drill else 'pocket' if shape.Pocket else 'contour'


def _step_defaults(layer, config):
    values = {key: value for section in (config.vars.Depth_Coordinates, config.vars.Feed_Rates)
              for key, value in plain(section).items() if key in PARAMETERS}
    values.update(axis3_retract=layer.axis3_retract, axis3_safe_margin=layer.axis3_safe_margin,
                  lead_in_mode=layer.get_lead_in_mode(), lead_out_mode=layer.get_lead_out_mode(),
                  overcut_enabled=layer.get_overcut_enabled(), milling_offset=layer.milling_offset,
                  drag_swivel_depth=config.vars.Drag_Knife_Options['swivel_depth'], cut_cor=40,
                  break_pass=-1)
    return values


class MachiningDrawing:
    """Bind a machining document to one actual imported drawing revision."""
    def __init__(self, project, layers):
        self.project = project
        self.source_layers = layers
        self.sources = {}
        self._baseline = {}
        self.active_operations = {}
        self.preview_layers = None
        self.bind()

    @classmethod
    def capture(cls, layers, config):
        """Migrate effective legacy state, preserving order and uncertain values."""
        project = MachiningProject(configuration=snapshot_configuration(config),
                                   units='mm' if config.metric else 'in')
        previous = None
        for layer in layers:
            order = list(getattr(layer, 'exp_order_complete', ()))
            order += [i for i in range(len(layer.shapes)) if i not in order]
            step = None
            for index in order:
                shape = layer.shapes[index]
                if isinstance(shape, CustomGCode):
                    if step is None:
                        tool = effective_tool(layer.shapes[next((i for i in order if not
                            isinstance(layer.shapes[i], CustomGCode)), index)], layer)
                        tool = ToolSettings(**{key: getattr(tool, key) for key in ToolSettings.__dataclass_fields__})
                        tool_id = _register_tool(project, tool)
                        step = MachiningStep(new_id(), layer.name, 'contour', tool_id)
                        project.steps.append(step)
                    step.entries.append(LiteralAction(getattr(shape, 'operation_id', None) or new_id(),
                                                     shape.name, shape.gcode, not shape.disabled))
                    previous = None  # retain the literal as an optimization/migration boundary
                    continue
                key = contour_key(shape)
                geometry_id = getattr(shape, 'geometry_id', None) or new_id()
                shape.geometry_id = geometry_id
                project.geometries[geometry_id] = GeometryReference(geometry_id, *key)
                tool = effective_tool(shape)
                tool = ToolSettings(**{key: getattr(tool, key) for key in ToolSettings.__dataclass_fields__})
                tool_id = _register_tool(project, tool)
                kind = _kind(layer, shape)
                grouping = (id(layer), tool_id, kind)
                if step is None or previous != grouping:
                    defaults = _step_defaults(layer, config)
                    step = MachiningStep(new_id(), layer.name, kind, tool_id, defaults)
                    project.steps.append(step)
                previous = grouping
                values = parameter_snapshot(shape)
                values.pop('axis3_retract', None)
                values.pop('axis3_safe_margin', None)
                # These values are known to come from the effective tool
                # definition (including a legacy shape tool override).
                for key in TOOL_PARAMETERS:
                    values.pop(key, None)
                # Only explicit flags prove inheritance. Numeric legacy values
                # stay own values even when they happen to equal the defaults.
                for key in ('lead_in_mode', 'lead_out_mode', 'overcut_enabled'):
                    if getattr(shape, key, 'default') == 'default':
                        values.pop(key, None)
                if getattr(shape, '_drag_swivel_depth', None) is None:
                    values.pop('drag_swivel_depth', None)
                local_start = shape.geos[0].get_start_end_points(True)
                operation_id = getattr(shape, 'operation_id', None) or new_id()
                shape.operation_id = operation_id
                conflict = ((shape.Drill, shape.Pocket, shape.cut_cor) if
                            machining_conflict(shape.Drill, shape.Pocket, shape.cut_cor) else ())
                step.entries.append(MachiningOperation(operation_id, geometry_id, values,
                    not shape.disabled, shape.send_to_TSP, shape.cw,
                    (local_start.x, local_start.y), conflict))
        project.validate()
        return cls(project, layers)

    def bind(self):
        candidates = defaultdict(list)
        for layer in self.source_layers:
            for shape in layer.shapes:
                if not isinstance(shape, CustomGCode):
                    candidates[contour_key(shape)].append(shape)
        self.project.unresolved.clear()
        self.sources.clear()
        for identity, reference in self.project.geometries.items():
            matches = candidates[(reference.source_layer, reference.source_instance, reference.fingerprint)]
            if len(matches) == 1:
                self.sources[identity] = matches[0]
                matches[0].geometry_id = identity
            else:
                self.project.unresolved[identity] = 'missing' if not matches else 'ambiguous'
        known = set(self.sources.values())
        self.unassigned = tuple(shape for matches in candidates.values() for shape in matches
                                if shape not in known)

    def materialize(self, allow_unresolved=False):
        """Create detached Shape/Layer projections for the existing planner."""
        if not allow_unresolved:
            self.project.assert_exportable()
        configuration = ProjectConfiguration(self.project)
        layers = Layers()
        layers.machining_config = configuration
        layers.machining_project = self.project
        for step in self.project.steps:
            source_layer = next((self.sources[e.geometry_id].parentLayer for e in step.entries
                if isinstance(e, MachiningOperation) and e.geometry_id in self.sources), None)
            if source_layer is None:
                source_layer = next(iter(self.source_layers), None)
            if source_layer is None:
                source_layer = LayerContent(len(layers), step.name, [], config=configuration)
            layer = copy(source_layer)
            layer.nr = len(layers)
            layer.machining_step_id = step.id
            layer.config = configuration
            layer.name = ('BREAKS:' + step.name if step.kind == 'break' else
                          'IGNORE:' + step.name if step.kind == 'ignored' else step.name)
            # User names do not acquire import-layer semantics.
            layer.isBreakLayer = lambda kind=step.kind: kind == 'break'
            layer.should_ignore = lambda kind=step.kind: kind == 'ignored'
            layer.shapes = Shapes()
            layer.exp_order_complete = []
            layer.exp_order = []
            tool = self.project.tools[step.tool_id]
            for key, value in asdict(tool).items():
                setattr(layer, key, value)
            for entry in step.entries:
                if isinstance(entry, LiteralAction):
                    shape = CustomGCode(entry.name, sum(len(l.shapes) for l in layers) + len(layer.shapes),
                                        entry.gcode, layer)
                    shape.disabled = not entry.enabled or step.kind == 'ignored'
                elif entry.geometry_id not in self.sources:
                    continue  # disabled unresolved entries are retained in the document
                else:
                    source = self.sources[entry.geometry_id]
                    shape = copy(source)
                    shape.__dict__.pop('machining_binding', None)
                    shape.__dict__.pop('_machining_view', None)
                    shape.geos = deepcopy(source.geos)
                    if shape.parentEntity is not None:
                        for geo in shape.geos:
                            geo.make_abs_geo(shape.parentEntity)
                    shape.selectionChangedCallback = None
                    shape.enableDisableCallback = None
                    shape.stmove = None
                    shape.toolpath_plan = None
                    shape.nr = sum(len(l.shapes) for l in layers) + len(layer.shapes)
                    shape.config = configuration
                    shape.machining_config = configuration
                    shape.operation_id = entry.id
                    shape.geometry_id = entry.geometry_id
                    values, origins, tool = self.project.resolve(step, entry)
                    for key, value in values.items():
                        if key in ('axis3_retract', 'axis3_safe_margin'):
                            setattr(layer, key, value)
                        else:
                            setattr(shape, key, value)
                    shape.tool_override = replace(tool, **{key: values.get(key, getattr(tool, key))
                        for key in ('lead_radius', 'lead_length', 'overcut_length', 'speed', 'start_radius')})
                    shape.Drill, shape.Pocket = step.kind == 'drill', step.kind == 'pocket'
                    if entry.legacy_conflict:
                        shape.Drill, shape.Pocket, shape.cut_cor = entry.legacy_conflict
                    shape.disabled = not entry.enabled or step.kind == 'ignored'
                    shape.send_to_TSP = entry.optimize
                    if shape.cw != entry.clockwise:
                        shape.reverse()
                    # Convert the saved local start through the current entity
                    # transform using the same geometry API as imported points.
                    anchor = Point(*entry.start)
                    if shape.parentEntity is not None:
                        anchor = anchor.rot_sca_abs(parent=shape.parentEntity)
                    shape.setNearestStPoint(anchor)
                    shape.parameter_origins = origins
                shape.parentLayer = layer
                shape.operation_id = entry.id
                layer.shapes.append(shape)
                if not shape.disabled:
                    layer.exp_order_complete.append(len(layer.shapes) - 1)
                    if not isinstance(shape, CustomGCode):
                        layer.exp_order.append(shape.nr)
            layers.append(layer)
        return layers

    def bind_legacy_editor(self):
        """Keep the existing editor as an input projection until the third tab.

        Only an unambiguous/explicitly active operation can be edited. Deltas
        are applied as commands to the machining document, not by rebuilding it.
        """
        self._baseline.clear()
        configuration = ProjectConfiguration(self.project)
        for layer in self.source_layers:
            layer.project_values_locked = True
            layer.exp_order_complete = list(range(len(layer.shapes)))
            layer.exp_order = [shape.nr for shape in layer.shapes if not isinstance(shape, CustomGCode)]
        by_geometry = self.operations_by_geometry()
        for identity, source in self.sources.items():
            source.machining_binding = self
            source.machining_config = configuration
            operations = by_geometry.get(identity, ())
            active = self.active_operations.get(identity)
            if len(operations) == 1:
                active = operations[0][1].id
                self.active_operations[identity] = active
            selected = next(((step, entry) for step, entry in operations if entry.id == active), None)
            if selected is not None:
                step, entry = selected
                values, origins, tool = self.project.resolve(step, entry)
                for key, value in values.items():
                    if key not in ('axis3_retract', 'axis3_safe_margin'):
                        setattr(source, key, value)
                source.tool_override = replace(tool, **{key: values.get(key, getattr(tool, key))
                    for key in ('lead_radius', 'lead_length', 'overcut_length', 'speed', 'start_radius')})
                source.Drill, source.Pocket = step.kind == 'drill', step.kind == 'pocket'
                if entry.legacy_conflict:
                    source.Drill, source.Pocket, source.cut_cor = entry.legacy_conflict
                source.send_to_TSP = entry.optimize
                source.operation_id = entry.id
            source.disabled = not any(entry.enabled for step, entry in operations)
            self._baseline[identity] = self._editor_state(source)
        for source in self.unassigned:
            source.machining_binding = self
            source.machining_config = configuration
            source.disabled = True

    def operations_by_geometry(self):
        result = defaultdict(list)
        for step in self.project.steps:
            for entry in step.entries:
                if isinstance(entry, MachiningOperation):
                    result[entry.geometry_id].append((step, entry))
        return result

    def activate_operation(self, operation_id):
        """Select the editing/preview context without changing shared geometry."""
        operation = next((entry for step in self.project.steps for entry in step.entries
                          if isinstance(entry, MachiningOperation) and entry.id == operation_id), None)
        if operation is None or operation.geometry_id not in self.sources:
            raise ValueError('Unknown or unresolved machining operation')
        self.synchronize_editor()
        self.active_operations[operation.geometry_id] = operation_id
        self.bind_legacy_editor()

    @staticmethod
    def _editor_state(source):
        tool = effective_tool(source)
        tool = ToolSettings(**{key: getattr(tool, key) for key in ToolSettings.__dataclass_fields__})
        return dict(values=parameter_snapshot(source), tool=tool,
                    drill=source.Drill, pocket=source.Pocket,
                    enabled=not source.disabled, optimize=source.send_to_TSP,
                    clockwise=source.cw,
                    start=(source.geos[0].get_start_end_points(True).x,
                           source.geos[0].get_start_end_points(True).y))

    def synchronize_editor(self):
        """Consume edits in the compatibility editor without losing step IDs."""
        assignments = self.operations_by_geometry()
        changes = []
        for identity, source in self.sources.items():
            old = self._baseline.get(identity)
            current = self._editor_state(source)
            if old is None or old == current:
                continue
            options = assignments[identity]
            active = self.active_operations.get(identity)
            selected = next(((s, e) for s, e in options if e.id == active), None)
            if selected is None:
                raise ValueError('Select an explicit machining operation before editing shared geometry')
            changes.append((identity, source, selected, old, current))
        if not changes:
            return
        # Validate the complete batch on a document copy before changing it.
        staged = deepcopy(self.project)
        for identity, source, (step, entry), old, current in changes:
            target_step = next(s for s in staged.steps if any(e.id == entry.id for e in s.entries))
            target_entry = next(e for e in target_step.entries if e.id == entry.id)
            for key, value in current['values'].items():
                if key not in ('axis3_retract', 'axis3_safe_margin') and value != old['values'].get(key):
                    target_entry.overrides[key] = value
            for key in ('enabled', 'optimize', 'clockwise', 'start'):
                if current[key] != old[key]:
                    setattr(target_entry, key, current[key])
            if current['drill'] != old['drill'] or current['pocket'] != old['pocket'] or current['tool'] != old['tool']:
                kind = 'drill' if current['drill'] else 'pocket' if current['pocket'] else 'contour'
                tool = current['tool']
                tool = ToolSettings(**{key: getattr(tool, key) for key in ToolSettings.__dataclass_fields__})
                tool_id = _register_tool(staged, tool)
                if kind != target_step.kind or tool_id != target_step.tool_id:
                    position = target_step.entries.index(target_entry)
                    parts = []
                    if position:
                        parts.append(replace(target_step, entries=target_step.entries[:position]))
                    parts.append(MachiningStep(target_step.id if not parts else new_id(),
                        target_step.name, kind, tool_id, deepcopy(target_step.defaults), [target_entry]))
                    if position + 1 < len(target_step.entries):
                        parts.append(replace(target_step, id=new_id(), entries=target_step.entries[position + 1:]))
                    index = staged.steps.index(target_step)
                    staged.steps[index:index + 1] = parts
                target_entry.legacy_conflict = ((current['drill'], current['pocket'], source.cut_cor)
                    if machining_conflict(current['drill'], current['pocket'], source.cut_cor) else ())
        if changes:
            staged.validate()
            self.project = staged
            for identity, _, _, _, state in changes:
                self._baseline[identity] = state

    def active_view(self, source):
        if self.preview_layers is None:
            self.synchronize_editor()
        identity = getattr(source, 'geometry_id', None)
        active = self.active_operations.get(identity)
        if active is None:
            return None
        layers = self.preview_layers if self.preview_layers is not None else self.materialize(allow_unresolved=True)
        return next((shape for layer in layers for shape in layer.shapes
                     if getattr(shape, 'operation_id', None) == active), None)

    @contextmanager
    def preview_batch(self):
        """Reuse projections only within one synchronous repaint, never across edits."""
        self.synchronize_editor()
        previous = self.preview_layers
        self.preview_layers = self.materialize(allow_unresolved=True)
        try:
            yield
        finally:
            self.preview_layers = previous


def _register_tool(project, tool):
    for identity, existing in project.tools.items():
        if existing == tool:
            return identity
    identity = new_id()
    project.tools[identity] = tool
    return identity
