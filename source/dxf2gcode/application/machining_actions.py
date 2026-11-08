"""Atomic machining commands and history, shared by every presentation path."""

from copy import deepcopy
from dataclasses import dataclass, replace
from math import pi

from dxf2gcode.application.machining import contour_key, _register_tool
from dxf2gcode.domain.project.machining_project import (
    GeometryReference, LiteralAction, MachiningOperation, MachiningStep, new_id)
from dxf2gcode.domain.project.tool_settings import ToolSettings
from dxf2gcode.domain.project.machining import machining_conflict


@dataclass
class MachiningChange:
    label: str
    changes: tuple = ()
    selection: tuple = ()


class MachiningTargetChoiceRequired(ValueError):
    """Let a presentation choose among equally compatible existing steps."""
    def __init__(self, source, kind, candidates, project):
        super().__init__('Choose a matching machining step')
        self.key = (source.id, kind)
        self.source_name = source.name
        self.candidates = tuple((step.id, step.name, step.kind, project.tools[step.tool_id].tool_nr)
                                for step in candidates)


def default_step_values(project):
    config = project.configuration
    result = dict(config['Depth_Coordinates'], **config['Feed_Rates'],
                  **config['Lead_In_Out'])
    result.update(cut_cor=40, milling_offset=0, break_pass=-1,
                  drag_swivel_depth=config['Drag_Knife_Options']['swivel_depth'],
                  drag_angle=config['Drag_Knife_Options']['drag_angle'])
    return result


def validate_target(binding, project, step, entry, source_kind=None):
    """Reject incompatible assignments without normalizing their own values."""
    if isinstance(entry, LiteralAction):
        if step.kind in ('break', 'ignored'):
            raise ValueError(entry.name + ': literal actions require a machining step')
        return
    shape = binding.sources.get(entry.geometry_id)
    if shape is None:
        raise ValueError(entry.id + ': unresolved source contour')
    label = '%s / %s' % (shape.parentLayer.name, shape.nr)
    if source_kind in ('break', 'ignored') or step.kind in ('break', 'ignored'):
        if source_kind != step.kind:
            raise ValueError(label + ': special-layer assignments cannot change kind')
        return
    hole = shape.type == 'Hole'
    circle = (shape.closed and bool(shape.geos) and
              all(hasattr(geo, 'O') and hasattr(geo, 'r') for geo in shape.geos) and
              all(geo.O == shape.geos[0].O and geo.r == shape.geos[0].r for geo in shape.geos) and
              abs(sum(abs(geo.ext) for geo in shape.geos) - 2*pi) < 1e-6)
    values, _, _ = project.resolve(step, entry)
    machine = project.configuration['General']['machine_type']
    if step.kind == 'drill' and (not (hole or circle) or values.get('cut_cor', 40) != 40):
        raise ValueError(label + ': drilling requires a point/circle and G40')
    if step.kind == 'contour' and hole:
        raise ValueError(label + ': a drilling point is not a milling contour')
    if step.kind == 'pocket' and (hole or not shape.closed or machine != 'milling' or
            project.configuration['Cutter_Compensation']['done_by_machine']):
        raise ValueError(label + ': pocketing requires a closed contour and internal milling compensation')


class MachiningCommands:
    """One history entry per complete action; rejected actions leave no trace."""
    def __init__(self, binding):
        self.binding = binding
        self.selection = ()
        self.undo_stack = []
        self.redo_stack = []
        self.target_choices = {}

    def _state(self):
        return deepcopy(self.binding.project), dict(self.binding.active_operations), self.selection

    def _restore(self, state):
        project, active, selection = state
        self.binding.project = deepcopy(project)
        self.binding.active_operations = dict(active)
        self.selection = selection
        self.binding.bind()
        self.binding.bind_legacy_editor()

    def perform(self, label, change):
        self.binding.synchronize_editor()
        before = self._state()
        staged = deepcopy(self.binding.project)
        result = change(staged) or MachiningChange(label)
        staged.validate()
        if staged.to_dict() == before[0].to_dict():
            return result
        self.binding.project = staged
        self.selection = result.selection
        self.binding.bind()
        self.binding.bind_legacy_editor()
        after = self._state()
        self.undo_stack.append((before, after, result))
        self.redo_stack.clear()
        return result

    def undo(self):
        if not self.undo_stack:
            return None
        item = self.undo_stack.pop()
        self._restore(item[0])
        self.redo_stack.append(item)
        return item[2]

    def redo(self):
        if not self.redo_stack:
            return None
        item = self.redo_stack.pop()
        self._restore(item[1])
        self.undo_stack.append(item)
        return item[2]

    @staticmethod
    def step(project, identity):
        step = next((step for step in project.steps if step.id == identity), None)
        if step is None:
            raise ValueError('Unknown machining step')
        return step

    @staticmethod
    def entries(project, identities):
        identities = tuple(identities)
        if len(set(identities)) != len(identities):
            raise ValueError('Duplicate machining selection')
        selected = [(s, e) for s in project.steps for e in s.entries if e.id in identities]
        if len(selected) != len(identities):
            raise ValueError('Unknown machining selection')
        return selected

    def create_step(self, name, kind, tool_id, identities=(), copy=False, geometries=()):
        step_id = new_id()
        def change(project):
            tool = _register_tool(project, tool_id) if isinstance(tool_id, ToolSettings) else tool_id
            step = MachiningStep(step_id, name, kind, tool, default_step_values(project))
            project.steps.append(step)
            result = self._transfer(project, identities, step_id, None, copy)
            assigned = self._assign(project, geometries, step)
            return MachiningChange('create', result.changes, result.selection + tuple(assigned) or (step_id,))
        return self.perform('create', change)

    def edit_step(self, identity, name, kind, tool_id, defaults=None, resolve_conflict=False,
                  replace_shared_tool=False):
        def change(project):
            step = self.step(project, identity)
            old_kind = step.kind
            old_tool_id = step.tool_id
            old_defaults = dict(step.defaults)
            old_values = {entry.id: project.resolve(step, entry)[0] for entry in step.entries
                          if isinstance(entry, MachiningOperation)}
            step.name, step.kind = name, kind
            step.tool_id = _register_tool(project, tool_id) if isinstance(tool_id, ToolSettings) else tool_id
            tool_changes = []
            if replace_shared_tool and old_tool_id != step.tool_id:
                old_tool, new_tool = project.tools[old_tool_id], project.tools[step.tool_id]
                delta = {key: (getattr(old_tool, key), getattr(new_tool, key))
                         for key in ToolSettings.__dataclass_fields__
                         if getattr(old_tool, key) != getattr(new_tool, key)}
                for other in project.steps:
                    if other.tool_id == old_tool_id or other.id == identity:
                        other.tool_id = step.tool_id
                        tool_changes.append((other.id, delta))
                del project.tools[old_tool_id]
            if defaults is not None:
                step.defaults = dict(defaults)
            if old_kind != step.kind or old_tool_id != step.tool_id or resolve_conflict:
                errors = []
                for entry in step.entries:
                    try:
                        validate_target(self.binding, project, step, entry, old_kind)
                    except ValueError as error:
                        errors.append(str(error))
                if errors:
                    raise ValueError('\n'.join(errors))
            if old_kind != step.kind or resolve_conflict:
                for entry in step.entries:
                    if isinstance(entry, MachiningOperation):
                        entry.legacy_conflict = ()
            changes = tool_changes
            for entry in step.entries:
                if isinstance(entry, MachiningOperation):
                    old = old_values[entry.id]
                    new = project.resolve(step, entry)[0]
                    delta = {key: (old.get(key), new.get(key)) for key in old.keys() | new.keys()
                             if old.get(key) != new.get(key)}
                    if delta:
                        changes.append((entry.id, delta))
            if not step.entries and defaults is not None:
                changes.append((identity, {key: (old_defaults.get(key), step.defaults.get(key))
                    for key in old_defaults.keys() | step.defaults.keys()
                    if old_defaults.get(key) != step.defaults.get(key)}))
            return MachiningChange('step', tuple(changes), (identity,))
        return self.perform('step', change)

    def _transfer(self, project, identities, target_id, position, copy):
        target = self.step(project, target_id)
        selected = self.entries(project, identities)
        if position is None:
            position = len(target.entries)
        if type(position) is not int or not 0 <= position <= len(target.entries):
            raise ValueError('Invalid machining insertion position')
        inserted, differences = [], []
        errors = []
        for source, entry in selected:
            try:
                validate_target(self.binding, project, target, entry, source.kind)
            except ValueError as error:
                errors.append(str(error))
        if errors:
            raise ValueError('\n'.join(errors))
        for source, entry in selected:
            cloned = deepcopy(entry)
            if copy:
                cloned.id = new_id()
            inserted.append(cloned)
            if isinstance(entry, MachiningOperation):
                old, _, old_tool = project.resolve(source, entry)
                new, _, new_tool = project.resolve(target, cloned)
                delta = {key: (old.get(key), new.get(key)) for key in old.keys() | new.keys()
                         if old.get(key) != new.get(key)}
                if old_tool != new_tool:
                    delta['tool'] = (old_tool.tool_nr, new_tool.tool_nr)
                    delta['diameter'] = (old_tool.tool_diameter, new_tool.tool_diameter)
                if source.kind != target.kind:
                    delta['kind'] = (source.kind, target.kind)
                if delta:
                    differences.append((entry.id, delta))
        if not copy:
            removed_before = sum(1 for e in target.entries[:position] if e.id in identities)
            position -= removed_before
            for source in project.steps:
                source.entries[:] = [e for e in source.entries if e.id not in identities]
        target.entries[position:position] = inserted
        return MachiningChange('copy' if copy else 'move', tuple(differences), tuple(e.id for e in inserted))

    def transfer(self, identities, target_id, position=None, copy=False):
        return self.perform('copy' if copy else 'move',
                            lambda p: self._transfer(p, identities, target_id, position, copy))

    def assign_to_step(self, identities, shapes, target_id, copy=False):
        """Transfer assignments and add unassigned geometry in one transaction."""
        def change(project):
            result = self._transfer(project, identities, target_id, None, copy)
            assigned = self._assign(project, shapes, self.step(project, target_id))
            return MachiningChange('copy' if copy else 'move', result.changes,
                                   result.selection + tuple(assigned))
        return self.perform('copy' if copy else 'move', change)

    def _assign(self, project, shapes, step):
        shapes = tuple(shapes)
        originals = {shape for layer in self.binding.source_layers for shape in layer.shapes}
        if len({id(shape) for shape in shapes}) != len(shapes) or any(
                shape not in originals or not hasattr(shape, 'geos') for shape in shapes):
            raise ValueError('Invalid or foreign geometry selection')
        assigned = []
        errors = []
        for shape in shapes:
            identity = getattr(shape, 'geometry_id', None)
            if identity not in project.geometries or self.binding.sources.get(identity) is not shape:
                identity = new_id()
                project.geometries[identity] = GeometryReference(identity, *contour_key(shape))
            start = shape.geos[0].get_start_end_points(True)
            entry = MachiningOperation(new_id(), identity, clockwise=shape.cw, start=(start.x, start.y))
            # The transaction has not yet rebound newly registered contours.
            sources = self.binding.sources
            self.binding.sources = dict(sources, **{identity: shape})
            try:
                source_kind = 'break' if shape.parentLayer.isBreakLayer() else 'ignored' if shape.parentLayer.should_ignore() else None
                validate_target(self.binding, project, step, entry, source_kind)
            except ValueError as error:
                errors.append(str(error))
            finally:
                self.binding.sources = sources
            step.entries.append(entry)
            assigned.append(entry.id)
        if errors:
            raise ValueError('\n'.join(errors))
        return assigned

    def assign(self, shapes, target_id):
        def change(project):
            ids = self._assign(project, shapes, self.step(project, target_id))
            return MachiningChange('assign', selection=tuple(ids))
        return self.perform('assign', change)

    def remove(self, identities):
        def change(project):
            self.entries(project, identities)
            for step in project.steps:
                step.entries[:] = [e for e in step.entries if e.id not in identities]
            return MachiningChange('remove')
        return self.perform('remove', change)

    def delete_step(self, identity, target_id=None):
        def change(project):
            step = self.step(project, identity)
            if target_id == identity:
                raise ValueError('Cannot move a step into itself')
            result = self._transfer(project, [e.id for e in step.entries], target_id, None, False) if target_id else MachiningChange('remove')
            project.steps.remove(step)
            return result
        return self.perform('remove', change)

    def reorder_steps(self, identities, selection=None):
        selection = tuple(self.selection if selection is None else selection)
        def change(project):
            if len(identities) != len(project.steps) or set(identities) != {s.id for s in project.steps}:
                raise ValueError('Invalid step order')
            by_id = {s.id: s for s in project.steps}
            project.steps[:] = [by_id[i] for i in identities]
            return MachiningChange('order', selection=selection)
        return self.perform('order', change)

    def edit_operation_paths(self, identities, action, points=None):
        """Apply the familiar contour-start algorithms to isolated operation views."""
        if action not in ('reverse', 'nearest', 'sharpest'):
            raise ValueError('Invalid operation setting')
        def change(project):
            views = {shape.operation_id: shape for layer in self.binding.materialize(allow_unresolved=True)
                     for shape in layer.shapes if hasattr(shape, 'operation_id')}
            for step, entry in self.entries(project, identities):
                if not isinstance(entry, MachiningOperation) or entry.id not in views:
                    raise ValueError('unresolved source contour')
                view = views[entry.id]
                if action == 'reverse':
                    entry.clockwise = not entry.clockwise
                    continue
                if not view.geos:
                    continue
                if action == 'nearest':
                    from dxf2gcode.domain.geometry.point import Point
                    view.setNearestStPoint(Point(*points[entry.id]))
                elif view.closed:
                    view.setSharpestStPoint()
                else:
                    continue
                start = view.geos[0].get_start_end_points(True)
                entry.start = (start.x, start.y)
                entry.clockwise = view.cw
            return MachiningChange('path', selection=tuple(identities))
        return self.perform('path', change)

    def _matching_target(self, project, source, kind, tool_id):
        definition = project.tools[tool_id]
        candidates = [step for step in project.steps if step.id != source.id and
                      step.kind == kind and project.tools[step.tool_id] == definition and
                      step.defaults == source.defaults]
        key = (source.id, kind)
        chosen = self.target_choices.get(key)
        if chosen is not None:
            target = next((step for step in candidates if step.id == chosen), None)
            if target is None:
                raise ValueError('Chosen machining target is no longer compatible')
            return target
        if len(candidates) > 1:
            raise MachiningTargetChoiceRequired(source, kind, candidates, project)
        return candidates[0] if candidates else None

    def set_operation_mode(self, identities, kind=None, compensation=None, names=None):
        """Change only selected assignments; keep each step's kind homogeneous."""
        if ((kind is None and compensation is None) or
                kind not in (None, 'contour', 'pocket', 'drill') or compensation not in (None, 40, 41, 42)):
            raise ValueError('Invalid machining mode')
        def change(project):
            selected = self.entries(project, identities)
            groups, differences, errors = {}, [], []
            for source, entry in selected:
                if not isinstance(entry, MachiningOperation) or source.kind in ('break', 'ignored'):
                    raise ValueError('special-layer assignments cannot change kind')
                target_kind = kind or source.kind
                if compensation is not None:
                    # Explicit compensation selects milling, as in the legacy menu.
                    if entry.legacy_conflict and entry.legacy_conflict[1]:
                        target_kind = 'pocket'
                    elif target_kind == 'drill':
                        target_kind = 'contour'
                before = project.resolve(source, entry)[0]
                if target_kind == source.kind:
                    target = source
                else:
                    key = (source.id, target_kind)
                    if key not in groups:
                        target = self._matching_target(project, source, target_kind, source.tool_id)
                        if target is None:
                            target = MachiningStep(new_id(), source.name + ' · ' + (names or {}).get(target_kind, target_kind),
                                                   target_kind, source.tool_id, deepcopy(source.defaults))
                            project.steps.insert(project.steps.index(source)+1, target)
                        groups[key] = target
                    target = groups[key]
                if compensation is not None or target_kind == 'drill':
                    entry.overrides['cut_cor'] = compensation if compensation is not None else 40
                try:
                    validate_target(self.binding, project, target, entry, source.kind)
                except ValueError as error:
                    errors.append(str(error))
                entry.legacy_conflict = ()
                after = project.resolve(target, entry)[0]
                delta = {key: (before.get(key), after.get(key)) for key in before.keys() | after.keys()
                         if before.get(key) != after.get(key)}
                if target is not source:
                    source.entries.remove(entry)
                    target.entries.append(entry)
                    delta['kind'] = (source.kind, target.kind)
                if delta:
                    differences.append((entry.id, delta))
            if errors:
                raise ValueError('\n'.join(errors))
            return MachiningChange('mode', tuple(differences), tuple(identities))
        return self.perform('mode', change)

    def set_operation_tool(self, identities, tool):
        """Change selected assignments only, splitting partially selected steps."""
        identities = tuple(identities)
        def change(project):
            selected = self.entries(project, identities)
            if not selected or any(not isinstance(entry, MachiningOperation) or
                    source.kind in ('break', 'ignored') for source, entry in selected):
                raise ValueError('Select machining contours to change tools')
            tool_id = _register_tool(project, tool) if isinstance(tool, ToolSettings) else tool
            definition = project.tools[tool_id]
            groups = {}
            for source, entry in selected:
                groups.setdefault(source.id, (source, []))[1].append(entry)
            differences = []
            for source, entries in groups.values():
                old_tool = project.tools[source.tool_id]
                if old_tool == definition:
                    continue
                before = {entry.id: project.resolve(source, entry)[0] for entry in entries}
                target = self._matching_target(project, source, source.kind, tool_id)
                if target is None:
                    if len(entries) == len(source.entries):
                        target = source
                        target.tool_id = tool_id
                    else:
                        target = MachiningStep(new_id(), source.name + ' · T%d' % definition.tool_nr,
                            source.kind, tool_id, deepcopy(source.defaults))
                        project.steps.insert(project.steps.index(source)+1, target)
                for entry in entries:
                    validate_target(self.binding, project, target, entry, source.kind)
                    after = project.resolve(target, entry)[0]
                    delta = {key: (before[entry.id].get(key), after.get(key))
                             for key in before[entry.id].keys() | after.keys()
                             if before[entry.id].get(key) != after.get(key)}
                    delta.update(tool=(old_tool.tool_nr, definition.tool_nr),
                                 diameter=(old_tool.tool_diameter, definition.tool_diameter))
                    differences.append((entry.id, delta))
                    if target is not source:
                        source.entries.remove(entry)
                        target.entries.append(entry)
            return MachiningChange('tool', tuple(differences), identities)
        return self.perform('tool', change)

    def update_entries(self, identities, overrides=None, **state):
        def change(project):
            for step, entry in self.entries(project, identities):
                if overrides is not None and isinstance(entry, MachiningOperation):
                    for key, value in overrides.items():
                        if value is None:
                            entry.overrides.pop(key, None)
                        else:
                            entry.overrides[key] = value
                for key, value in state.items():
                    if key not in ('enabled', 'optimize', 'clockwise', 'start') or not hasattr(entry, key):
                        raise ValueError('Invalid operation setting')
                    setattr(entry, key, value)
                if isinstance(entry, MachiningOperation):
                    # Only explicit corrections clear a preserved conflict.
                    if 'cut_cor' in (overrides or {}) and entry.legacy_conflict:
                        drill, pocket, _ = entry.legacy_conflict
                        compensation = project.resolve(step, entry)[0].get('cut_cor', 40)
                        entry.legacy_conflict = ((drill, pocket, compensation)
                            if machining_conflict(drill, pocket, compensation) else ())
            return MachiningChange('parameters', selection=tuple(identities))
        return self.perform('parameters', change)

    def update_selected_step_defaults(self, identities, values):
        """Change shared clearance once per step in one selection command."""
        if not values or set(values) - {'axis3_retract', 'axis3_safe_margin'}:
            raise ValueError('Invalid shared clearance parameter')
        def change(project):
            selected = self.entries(project, identities)
            if any(not isinstance(entry, MachiningOperation) for _, entry in selected):
                raise ValueError('Select machining operations')
            steps = {step.id: step for step, _ in selected}
            changes = []
            for step in steps.values():
                old = {key: project.resolve(step, MachiningOperation('', ''))[0].get(key) for key in values}
                step.defaults.update(values)
                changes.append((step.id, {key: (old[key], value) for key, value in values.items()}))
            return MachiningChange('parameters', tuple(changes), tuple(identities))
        return self.perform('parameters', change)

    def update_start_coordinate(self, identities, coordinate, value):
        """Edit one local start coordinate without replacing the other axis."""
        if coordinate not in (0, 1):
            raise ValueError('Invalid start coordinate')
        def change(project):
            for _, entry in self.entries(project, identities):
                if not isinstance(entry, MachiningOperation):
                    raise ValueError('Select machining operations')
                point = list(entry.start)
                point[coordinate] = value
                entry.start = tuple(point)
            return MachiningChange('parameters', selection=tuple(identities))
        return self.perform('parameters', change)

    def refresh_tool(self, identity, tool):
        def change(project):
            old = project.update_tool(identity, tool)
            delta = {key: (getattr(old, key), getattr(tool, key)) for key in ToolSettings.__dataclass_fields__
                     if getattr(old, key) != getattr(tool, key)}
            affected = [s for s in project.steps if s.tool_id == identity]
            canonical = next((key for key, value in project.tools.items()
                              if key != identity and value == tool), identity)
            if canonical != identity:
                for step in affected:
                    step.tool_id = canonical
                del project.tools[identity]
            return MachiningChange('tool', tuple((s.id, delta) for s in affected))
        return self.perform('tool', change)

    def update_literal(self, identity, name, gcode):
        def change(project):
            entry = self.entries(project, [identity])[0][1]
            if not isinstance(entry, LiteralAction):
                raise ValueError('Select a literal action')
            entry.name, entry.gcode = name, gcode
            return MachiningChange('literal', selection=(identity,))
        return self.perform('literal', change)

    def update_settings(self, settings):
        def change(project):
            for section, values in settings.items():
                project.configuration[section].update(values)
            return MachiningChange('settings', selection=self.selection)
        return self.perform('settings', change)

    def change_units(self, units):
        def change(project):
            if units == project.units:
                return
            factor = 25.4 if units == 'mm' else 1/25.4
            lengths = {'axis3_start_mill_depth', 'axis3_slice_depth', 'axis3_mill_depth',
                'axis3_retract', 'axis3_safe_margin', 'f_g1_plane', 'f_g1_depth', 'milling_offset',
                'lead_radius', 'lead_length', 'overcut_length', 'drag_swivel_depth', 'start_radius'}
            def scale(values, fields):
                for key in set(values) & fields:
                    if values[key] is not None:
                        values[key] *= factor
            scale(project.defaults, lengths)
            for step in project.steps:
                scale(step.defaults, lengths)
                for entry in step.entries:
                    if isinstance(entry, MachiningOperation):
                        scale(entry.overrides, lengths)
            project.tools = {identity: tool.scaled(factor) for identity, tool in project.tools.items()}
            config = project.configuration
            for section in ('Depth_Coordinates', 'Feed_Rates'):
                scale(config[section], set(config[section]))
            scale(config['Plane_Coordinates'], {'axis1_start_end', 'axis2_start_end'})
            scale(config['Drag_Knife_Options'], {'swivel_depth', 'ramp_in_length', 'lead_out_length', 'alignment_length'})
            for tool in config['Tool_Parameters'].values():
                scale(tool, {'diameter', 'start_radius', 'lead_radius', 'lead_length', 'overcut_length', 'milling_offset'})
            project.units = units
            config['General']['drawing_units_override'] = units
            return MachiningChange('units', selection=self.selection)
        return self.perform('units', change)

    def optimize(self, optimizer_factory):
        from dxf2gcode.application.machining import MachiningDrawing
        from dxf2gcode.application.optimization.routes import OptimizeRoutes
        from dxf2gcode.domain.geometry.point import Point
        def change(project):
            binding = MachiningDrawing(project, self.binding.source_layers)
            layers = binding.materialize()
            shapes = [shape for layer in layers for shape in layer.shapes]
            config = project.configuration
            plane = config['Plane_Coordinates']
            OptimizeRoutes(optimizer_factory, config['Route_Optimisation']['max_iterations'],
                Point(plane['axis1_start_end'], plane['axis2_start_end']),
                config['Route_Optimisation']).execute(layers.non_break_layer_iter(), shapes)
            for step, layer in zip(project.steps, layers):
                entries = {e.id: e for e in step.entries}
                step.entries[:] = [entries[s.operation_id] for s in layer.shapes]
                for shape in layer.shapes:
                    entry = entries[shape.operation_id]
                    if isinstance(entry, MachiningOperation):
                        point = shape.geos[0].get_start_end_points(True)
                        entry.start, entry.clockwise = (point.x, point.y), shape.cw
            return MachiningChange('optimize', selection=self.selection)
        return self.perform('optimize', change)
