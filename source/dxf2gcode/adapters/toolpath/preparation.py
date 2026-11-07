"""Resolve runtime settings at the boundary of geometry preparation."""

import dxf2gcode.bootstrap.runtime_state as g
from dxf2gcode.domain.geometry.collections import Geos
from dxf2gcode.domain.toolpath.inputs import PreparationSettings, PathGeometry
from dxf2gcode.domain.toolpath.stmove import StMove
from dxf2gcode.domain.project.tool_settings import ToolSettings, effective_tool
from dxf2gcode.domain.toolpath.leadmove import (
    get_lead_in_mode, get_lead_out_mode, get_overcut_enabled)
from dataclasses import replace
from math import pi


def preparation_settings(config):
    pocket = config.vars.Pocketing
    return PreparationSettings(
        machine_type=config.machine_type,
        machine_compensation=config.vars.Cutter_Compensation['done_by_machine'],
        overcut_enabled=config.vars.Lead_In_Out['overcut_enabled'],
        drag_start_angle=config.vars.Drag_Knife_Options['drag_start_angle'],
        pocket_edge_clearance=getattr(pocket, 'pocket_edge_clearance', 100.0 * 3 / 14))


def prepare_shape(shape, config=None, build_preview=True):
    from dxf2gcode.presentation.qt.qt_compat import QtCore
    from dxf2gcode.adapters.toolpath.preview import preview_plan
    from dxf2gcode.adapters.toolpath.planning import _existing_geometry
    original = shape
    binding = getattr(shape, 'machining_binding', None)
    if binding is not None:
        view = binding.active_view(shape)
        shape._machining_view = view
        if view is not None:
            shape = view
    config = getattr(shape, 'machining_config', None) or config or g.config
    source_tool = effective_tool(shape)
    settings = replace(preparation_settings(config),
                       lead_in_mode=get_lead_in_mode(shape),
                       lead_out_mode=get_lead_out_mode(shape),
                       shape_overcut=get_overcut_enabled(shape),
                       tool=ToolSettings(**{name: getattr(source_tool, name)
                                            for name in ToolSettings.__dataclass_fields__}))
    prepared = StMove(shape, settings,
                      lambda context, text: QtCore.QCoreApplication.translate(context, text))
    shape.stmove = prepared
    original.stmove = prepared
    if not build_preview:
        return prepared
    plan = preview_plan(original)
    # Compatibility data for callers displaying exit details: these values
    # are projections of the plan, never another lead/tab/pass calculation.
    prepared.exit_geos = Geos()
    if plan is not None:
        in_exit, height = False, 0.0
        for action in plan.actions:
            if action.kind == 'linear_z':
                height = action.args[0]
            if action.role in ('lead_out', 'overcut'):
                in_exit = True
            if in_exit and action.role == 'tab' and action.kind == 'linear_xy':
                prepared.exit_geos.append(_existing_geometry(PathGeometry(
                    'break', action.args[0], action.args[1], height=height)))
            if action.role not in ('lead_out', 'overcut'):
                continue
            args = action.args
            if action.kind == 'linear_xy':
                geo = PathGeometry('line', args[0], args[1])
            elif action.kind == 'arc':
                geo = PathGeometry('arc', args[1], args[2], abs(args[8]) * args[5],
                                   center=args[6], radius=args[5], sweep=args[8],
                                   start_angle=args[3] - (1 if args[8] > 0 else -1) * pi / 2,
                                   end_angle=args[4] + (1 if args[8] > 0 else -1) * pi / 2)
            else:
                continue
            prepared.exit_geos.append(_existing_geometry(geo))
    return prepared
