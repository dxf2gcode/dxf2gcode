"""First vertical toolpath adapter for a closed, line-only milling contour."""

import dxf2gcode.bootstrap.runtime_state as g
from dxf2gcode.domain.toolpath.leadmove import (
    LEAD_OFF, get_lead_in_mode, get_lead_out_mode, get_overcut_enabled)
from dxf2gcode.domain.geometry.linegeo import LineGeo
from dxf2gcode.domain.toolpath.stmove import RapidPos
from dxf2gcode.domain.toolpath.plan import (
    ToolpathMove, ToolpathPass, ToolpathPlan)
from dxf2gcode.adapters.toolpath.shape_plan_builder import (
    ShapeToolpathCommandBuilder)


class SimpleMillingToolpathPlanner:
    """Build a semantic plan when the legacy shape is in the supported slice."""

    def plan(self, shape, postprocessor):
        if not self._supports(shape, postprocessor):
            return None

        rapid = shape.stmove.geos.abs_el(0)
        geometries = list(shape.geos.abs_iter())
        decimals = postprocessor.vars.Number_Format["post_decimals"]
        moves = []
        for geo in geometries:
            if (round(geo.Ps.x, decimals) == round(geo.Pe.x, decimals) and
                    round(geo.Ps.y, decimals) == round(geo.Pe.y, decimals)):
                continue
            moves.append(ToolpathMove(
                kind="linear_xy",
                start_xy=(geo.Ps.x, geo.Ps.y),
                end_xy=(geo.Pe.x, geo.Pe.y),
            ))
        if not moves:
            return None

        depth_values = shape.get_pass_depths()
        if not depth_values or depth_values[0] < shape.axis3_mill_depth:
            return None
        plan_moves = tuple(moves)
        passes = tuple(
            ToolpathPass(number=index + 1, depth=depth, moves=plan_moves)
            for index, depth in enumerate(depth_values))
        layer = shape.parentLayer
        return ToolpathPlan(
            shape_number=shape.nr,
            approach_xy=(rapid.x, rapid.y),
            passes=passes,
            workpiece_top=shape.axis3_start_mill_depth,
            safe_margin=layer.axis3_safe_margin,
            retract_depth=layer.axis3_retract,
            feed_depth=shape.f_g1_depth,
            feed_xy=shape.f_g1_plane,
        )

    @staticmethod
    def _supports(shape, postprocessor):
        required_shape_members = (
            "closed", "cut_cor", "Pocket", "Drill", "axis3_slice_depth",
            "stmove", "geos", "parentLayer", "get_pass_depths",
            "axis3_mill_depth", "axis3_start_mill_depth", "f_g1_depth",
            "f_g1_plane",
        )
        if any(not hasattr(shape, name) for name in required_shape_members):
            return False
        if shape.stmove is None:
            return False
        if postprocessor.vars.General["output_type"] != "g-code":
            return False
        if g.config.machine_type != "milling":
            return False
        if (not shape.closed or shape.cut_cor != 40 or shape.Pocket or
                shape.Drill or abs(shape.axis3_slice_depth) == 0):
            return False
        if any(not isinstance(geo, LineGeo) for geo in shape.geos.abs_iter()):
            return False
        if shape.parentLayer is None:
            return False
        if get_lead_in_mode(shape) != LEAD_OFF:
            return False
        if get_lead_out_mode(shape) != LEAD_OFF:
            return False
        if get_overcut_enabled(
                shape, g.config.vars.Lead_In_Out["overcut_enabled"]):
            return False
        if getattr(shape, "break_pass", -1) != -1:
            return False
        if getattr(shape.stmove, "start_move_error", ""):
            return False
        if len(shape.stmove.geos) != 1:
            return False
        if not isinstance(shape.stmove.geos.abs_el(0), RapidPos):
            return False
        if getattr(shape.stmove, "lead_in_geos", ()):
            return False
        if getattr(shape.stmove, "exit_geos", ()):
            return False
        breaks = getattr(postprocessor, "breaks", None)
        if (breaks is None or not hasattr(breaks, "breakLayers") or
                breaks.breakLayers):
            return False

        geometries = list(shape.geos.abs_iter())
        if not geometries:
            return False
        tolerance = getattr(g.config, "point_tolerance", 0.001)
        if not SimpleMillingToolpathPlanner._same_point(
                geometries[0].Ps, shape.stmove.geos.abs_el(0), tolerance):
            return False
        if not SimpleMillingToolpathPlanner._same_point(
                geometries[-1].Pe, geometries[0].Ps, tolerance):
            return False
        for previous, current in zip(geometries, geometries[1:]):
            if not SimpleMillingToolpathPlanner._same_point(
                    previous.Pe, current.Ps, tolerance):
                return False
        return True

    @staticmethod
    def _same_point(left, right, tolerance):
        return (abs(left.x - right.x) <= tolerance and
                abs(left.y - right.y) <= tolerance)


class ToolpathPlanner:
    """Plan all shape types, preferring the explicit basic milling model."""

    def __init__(self):
        self._simple_milling = SimpleMillingToolpathPlanner()

    def plan(self, shape, postprocessor):
        plan = self._simple_milling.plan(shape, postprocessor)
        if plan is not None:
            return plan
        return ShapeToolpathCommandBuilder.build(shape, postprocessor)
