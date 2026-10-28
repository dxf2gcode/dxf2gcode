"""Adapter-level helpers for G-Code regression tests."""


def serialize_gcode(value, postprocessor):
    """Serialize a Shape or geometry object without model writer methods."""
    if hasattr(value, "stmove"):
        return postprocessor.write_shape_gcode(value)

    from dxf2gcode.adapters.toolpath.geometry_gcode import (
        GeometryGCodeSerializer)
    return GeometryGCodeSerializer().export(value, postprocessor)


def serialize_shape_geometry(shape, geometry, postprocessor):
    """Apply Shape's historical precision filter, then serialize geometry."""
    from math import pi
    from dxf2gcode.adapters.toolpath.geometry_gcode import GeometryGCodeSerializer
    from dxf2gcode.domain.geometry.arcgeo import ArcGeo
    from dxf2gcode.domain.geometry.holegeo import HoleGeo
    from dxf2gcode.domain.geometry.point import Point
    from dxf2gcode.domain.toolpath.pocketmove import PocketMove

    serializer = GeometryGCodeSerializer()
    if isinstance(geometry, PocketMove):
        return serializer.export(geometry, postprocessor)
    if shape.Drill:
        return serializer.export(HoleGeo(Point(geometry.O.x, geometry.O.y)),
                                 postprocessor)
    decimals = postprocessor.vars.Number_Format["post_decimals"]
    if (isinstance(geometry, HoleGeo) or
            round(geometry.Ps.x, decimals) != round(geometry.Pe.x, decimals) or
            round(geometry.Ps.y, decimals) != round(geometry.Pe.y, decimals) or
            isinstance(geometry, ArcGeo) and
            geometry.length > 0.05 * 0.1 ** decimals * pi):
        return serializer.export(geometry, postprocessor)
    return ""
