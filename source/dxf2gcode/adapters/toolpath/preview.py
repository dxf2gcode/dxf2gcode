"""Prepare preview plans through the same input adapter and planner as export."""

from functools import lru_cache

import dxf2gcode.bootstrap.runtime_state as g
from dxf2gcode.adapters.postprocessor.dialect import ProfileDialect
from dxf2gcode.adapters.postprocessor.breaks import Breaks
from dxf2gcode.adapters.toolpath.planning import ShapePlanningInputs, exit_geometry
from dxf2gcode.domain.toolpath.planner import ToolpathPlanner


@lru_cache(maxsize=1)
def default_preview_profile():
    from configobj import ConfigObj
    from validate import Validator
    from dxf2gcode.adapters.postprocessor.postprocessorconfig import (
        POSTPRO_SPEC, MyPostProConfig)
    values = ConfigObj(configspec=POSTPRO_SPEC)
    values.validate(Validator(), copy=True)
    values.main.interpolation = False
    config = MyPostProConfig.__new__(MyPostProConfig)
    config.var_dict = values
    config.update_config()
    return config.vars


def preview_result(shape, postprocessor=None, layers=None):
    """Always snapshot current values; no cached plan can survive an edit."""
    if getattr(shape, 'machining_binding', None) is not None and getattr(shape, '_machining_view', None) is None:
        from dxf2gcode.domain.toolpath.plan import ToolpathPlanningResult
        shape.toolpath_plan = None
        shape.toolpath_diagnostics = ()
        return ToolpathPlanningResult(None, ())
    config = getattr(shape, 'machining_config', None) or g.config
    if postprocessor is not None and not hasattr(postprocessor, "vars"):
        if getattr(postprocessor, "postprocessor_files", ()):
            postprocessor.getPostProVars(0)
    profile = getattr(postprocessor, "vars", None) or default_preview_profile()
    plane = config.vars.Plane_Coordinates
    dialect = ProfileDialect(
        profile, (plane['axis1_start_end'], plane['axis2_start_end']),
        config.vars.Depth_Coordinates['axis3_retract'],
        diameter_factor=2 if config.machine_type == 'lathe' else 1)
    dialect.breaks = Breaks(layers) if layers is not None else getattr(postprocessor, "breaks", None)
    if (config.machine_type == 'drag_knife'
            and getattr(config.vars.Drag_Knife_Options, 'entry_mode', 'fixed') == 'previous'
            and layers is not None):
        _set_previous_knife_state(shape, layers, dialect)
    request = ShapePlanningInputs(lambda: config).request(shape, dialect)
    result = ToolpathPlanner(exit_geometry).plan(request)
    shape.toolpath_plan = result.plan
    shape.toolpath_diagnostics = result.diagnostics
    shape.stmove.exit_error = next((item.message for item in result.diagnostics
                                   if item.code == "lead.invalid_exit"), "")
    return result


def _set_previous_knife_state(shape, layers, dialect):
    """Read the immediate predecessor in export order; never redraw the route.

    Its final direction is independent of its assumed entry angle. Planning
    just that predecessor avoids recursively planning an entire prefix.
    """
    previous = None
    layer_iter = layers.non_break_layer_iter() if hasattr(layers, 'non_break_layer_iter') else layers
    found = False
    for layer in layer_iter:
        for index in getattr(layer, 'exp_order_complete', ()):
            candidate = layer.shapes[index]
            if candidate is shape:
                found = True
                break
            previous = candidate
        if found:
            break
    if not found or previous is None:
        return
    from dxf2gcode.domain.toolpath.customgcode import CustomGCode
    if isinstance(previous, CustomGCode):
        return
    if getattr(previous, 'stmove', None) is None:
        from dxf2gcode.adapters.toolpath.preparation import prepare_shape
        prepare_shape(previous, build_preview=False)
    request = ShapePlanningInputs(lambda: g.config).request(previous, dialect)
    result = ToolpathPlanner(exit_geometry).plan(request)
    if result.plan is not None and not result.has_errors:
        dialect.knife_heading = result.plan.knife_heading
        dialect.knife_tool = result.plan.knife_tool


def preview_plan(shape):
    window = getattr(g, "window", None)
    return preview_result(shape, getattr(window, "MyPostProcessor", None),
                          getattr(window, "layerContents", None)).plan
