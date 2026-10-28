"""Serialize domain geometry to postprocessor movement calls."""

import math

import dxf2gcode.bootstrap.runtime_state as g
from dxf2gcode.domain.geometry.arcgeo import ArcGeo
from dxf2gcode.domain.geometry.breakgeo import BreakGeo
from dxf2gcode.domain.toolpath.customgcode import CustomGCode
from dxf2gcode.domain.geometry.holegeo import HoleGeo
from dxf2gcode.domain.geometry.linegeo import LineGeo
from dxf2gcode.domain.toolpath.pocketmove import PocketMove
from dxf2gcode.domain.toolpath.stmove import RapidPos


class GeometryGCodeSerializer:
    """Format legacy geometric primitives through a postprocessor port."""

    def __init__(self, config=None):
        self._config = config

    def export(self, geometry, postprocessor):
        if isinstance(geometry, CustomGCode):
            return geometry.gcode
        if isinstance(geometry, BreakGeo):
            return self._break(geometry, postprocessor)
        if isinstance(geometry, PocketMove):
            return self._pocket_move(geometry, postprocessor)
        if isinstance(geometry, RapidPos):
            return postprocessor.rap_pos_xy(geometry)
        if isinstance(geometry, HoleGeo):
            return postprocessor.make_print_str("(Drilled hole)%nl")
        if isinstance(geometry, ArcGeo):
            return self._arc(geometry, postprocessor)
        if isinstance(geometry, LineGeo):
            start = geometry.get_start_end_points(True)
            end = geometry.get_start_end_points(False)
            return postprocessor.lin_pol_xy(start, end)
        raise TypeError("unsupported geometry for G-Code: %s" %
                        type(geometry).__name__)

    def _arc(self, geometry, postprocessor):
        start, start_angle = geometry.get_start_end_points(True, True)
        end, end_angle = geometry.get_start_end_points(False, True)
        center = geometry.O
        radius = geometry.r
        ij = center - start
        if radius > postprocessor.vars.General["max_arc_radius"]:
            return postprocessor.lin_pol_xy(start, end)
        if postprocessor.vars.General["export_arcs_as_lines"]:
            config = self._config or g.config
            tolerance = config.fitting_tolerance
            segment = 2 * math.sqrt(tolerance * (2 * radius - tolerance))
            alpha = 2 * math.asin(segment / (2 * radius))
            count = int(abs(geometry.ext // alpha))
            output = ""
            for index in range(1, count + 1):
                end = geometry.get_point_from_start(index, count)
                output += postprocessor.lin_pol_xy(start, end)
                start = end
            return output
        if geometry.ext > 0:
            return postprocessor.lin_pol_arc(
                "ccw", start, end, start_angle, end_angle, radius, center,
                ij, geometry.ext)
        if geometry.ext < 0 and \
                postprocessor.vars.General["export_ccw_arcs_only"]:
            return postprocessor.lin_pol_arc(
                "ccw", end, start, end_angle, start_angle, radius, center,
                center - end, geometry.ext)
        return postprocessor.lin_pol_arc(
            "cw", start, end, start_angle, end_angle, radius, center, ij,
            geometry.ext)

    @staticmethod
    def _break(geometry, postprocessor):
        old_z = postprocessor.ze
        old_feed = postprocessor.feed
        if geometry.height <= old_z:
            start = geometry.get_start_end_points(True)
            end = geometry.get_start_end_points(False)
            return postprocessor.lin_pol_xy(start, end)
        start = geometry.get_start_end_points(True)
        end = geometry.get_start_end_points(False)
        return (postprocessor.chg_feed_rate(geometry.zfeed) +
                postprocessor.lin_pol_z(geometry.height) +
                postprocessor.chg_feed_rate(geometry.xyfeed) +
                postprocessor.lin_pol_xy(start, end) +
                postprocessor.chg_feed_rate(geometry.zfeed) +
                postprocessor.lin_pol_z(old_z) +
                postprocessor.chg_feed_rate(old_feed))

    @staticmethod
    def _pocket_move(geometry, postprocessor):
        output = postprocessor.chg_feed_rate(geometry.feedZ)
        output += postprocessor.lin_pol_z(geometry.safe)
        output += postprocessor.rap_pos_z(geometry.retr)
        output += postprocessor.rap_pos_xy(geometry.Pe)
        output += postprocessor.rap_pos_z(geometry.safe)
        output += postprocessor.chg_feed_rate(geometry.feedZ)
        output += postprocessor.lin_pol_z(geometry.depth)
        output += postprocessor.chg_feed_rate(geometry.feedXY)
        return output
