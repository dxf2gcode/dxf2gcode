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
    if postprocessor is not None and not hasattr(postprocessor, "vars"):
        if getattr(postprocessor, "postprocessor_files", ()):
            postprocessor.getPostProVars(0)
    profile = getattr(postprocessor, "vars", None) or default_preview_profile()
    plane = g.config.vars.Plane_Coordinates
    dialect = ProfileDialect(
        profile, (plane['axis1_start_end'], plane['axis2_start_end']),
        g.config.vars.Depth_Coordinates['axis3_retract'],
        diameter_factor=2 if g.config.machine_type == 'lathe' else 1)
    dialect.breaks = Breaks(layers) if layers is not None else getattr(postprocessor, "breaks", None)
    request = ShapePlanningInputs(lambda: g.config).request(shape, dialect)
    result = ToolpathPlanner(exit_geometry).plan(request)
    shape.toolpath_plan = result.plan
    shape.toolpath_diagnostics = result.diagnostics
    shape.stmove.exit_error = next((item.message for item in result.diagnostics
                                   if item.code == "lead.invalid_exit"), "")
    return result


def preview_plan(shape):
    window = getattr(g, "window", None)
    return preview_result(shape, getattr(window, "MyPostProcessor", None),
                          getattr(window, "layerContents", None)).plan
