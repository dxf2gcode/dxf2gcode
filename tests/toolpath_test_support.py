"""Adapter-level helpers for G-Code regression tests."""


def serialize_gcode(value, postprocessor):
    """Serialize a Shape or geometry object without model writer methods."""
    if hasattr(value, "stmove") or hasattr(value, "gcode"):
        return postprocessor.write_shape_gcode(value)

    return serialize_geometry(value, postprocessor)


def serialize_geometry(geometry, postprocessor):
    """Use production semantic movements for individual geometry regressions."""
    import dxf2gcode.bootstrap.runtime_state as g
    from dxf2gcode.adapters.toolpath.planning import (
        snapshot_capabilities, snapshot_geometry)
    from dxf2gcode.adapters.toolpath.gcode_exporter import ToolpathGCodeExporter
    from dxf2gcode.domain.toolpath.inputs import (
        MachiningSettings, PlanningState, ToolpathRequest)
    from dxf2gcode.domain.toolpath.movements import MovementPlan
    request = ToolpathRequest(
        0, MachiningSettings(), snapshot_capabilities(postprocessor, g.config),
        initial_state=PlanningState(
            postprocessor.feed, postprocessor.ze, postprocessor.lz))
    plan = MovementPlan(request)
    plan.geometry(snapshot_geometry(geometry))
    return ToolpathGCodeExporter().export(plan.finish(), postprocessor)


def serialize_shape_geometry(shape, geometry, postprocessor):
    """Apply Shape's historical precision filter, then serialize geometry."""
    from math import pi
    from dxf2gcode.domain.geometry.arcgeo import ArcGeo
    from dxf2gcode.domain.geometry.holegeo import HoleGeo
    from dxf2gcode.domain.geometry.point import Point
    from dxf2gcode.domain.toolpath.pocketmove import PocketMove

    if isinstance(geometry, PocketMove):
        return serialize_geometry(geometry, postprocessor)
    if shape.Drill:
        return serialize_geometry(HoleGeo(Point(geometry.O.x, geometry.O.y)),
                                  postprocessor)
    decimals = postprocessor.vars.Number_Format["post_decimals"]
    if (isinstance(geometry, HoleGeo) or
            round(geometry.Ps.x, decimals) != round(geometry.Pe.x, decimals) or
            round(geometry.Ps.y, decimals) != round(geometry.Pe.y, decimals) or
            isinstance(geometry, ArcGeo) and
            geometry.length > 0.05 * 0.1 ** decimals * pi):
        return serialize_geometry(geometry, postprocessor)
    return ""
