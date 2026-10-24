# -*- coding: utf-8 -*-
"""
Tests for the lead in / lead out / overcut geometry (core/leadmove.py).

Run from the repository root:

    python -m unittest discover -s tests -t tests -p "dxf2gcode_leadmove_test.py" -v
"""
from __future__ import absolute_import

import os
import sys
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [_TEST_DIR, os.path.join(os.path.dirname(_TEST_DIR), "source")]

from dxf2gcode.core.arcgeo import ArcGeo  # noqa: E402
from dxf2gcode.core.breakgeo import BreakGeo  # noqa: E402
from dxf2gcode.core.leadmove import (  # noqa: E402
    ERROR, LEAD_OFF, LEAD_RADIUS, LEAD_STARTMOVE, LEAD_STRAIGHT, OK,
    SPACE_NOMINAL, SPACE_TOOL_CENTER, WARNING, build_exit_geometries,
    build_lead_in, build_lead_out, build_overcut, chain_cut_length,
    chain_direction, resolve_radius,
    validate_lead_move)
from dxf2gcode.core.linegeo import LineGeo  # noqa: E402
from dxf2gcode.core.point import Point  # noqa: E402

from math import pi, sqrt


def square_chain():
    """A closed square contour as a chain of geometries."""
    return [LineGeo(Point(0, 0), Point(100, 0)),
            LineGeo(Point(100, 0), Point(100, 100)),
            LineGeo(Point(100, 100), Point(0, 100)),
            LineGeo(Point(0, 100), Point(0, 0))]


class TestResolveRadius(unittest.TestCase):

    def test_nominal_space_keeps_the_workpiece_radius(self):
        radius, status, message = resolve_radius(10.0, 5.0, SPACE_NOMINAL)
        self.assertEqual(status, OK)
        self.assertEqual(radius, 10.0)
        self.assertEqual(message, "")

    def test_tool_center_space_uses_the_tool_center_radius(self):
        radius, status, message = resolve_radius(10.0, 5.0,
                                                  SPACE_TOOL_CENTER)
        self.assertEqual(status, OK)
        self.assertEqual(radius, 5.0)

    def test_radius_smaller_than_the_tool_radius_is_an_error(self):
        radius, status, message = resolve_radius(3.0, 5.0, SPACE_NOMINAL)
        self.assertEqual(status, ERROR)
        self.assertEqual(radius, 0.0)
        self.assertTrue(message)

    def test_radius_equal_to_the_tool_radius_is_a_warning(self):
        radius, status, message = resolve_radius(5.0, 5.0, SPACE_NOMINAL)
        self.assertEqual(status, WARNING)
        self.assertEqual(radius, 5.0)
        self.assertTrue(message)

    def test_radius_equal_to_the_tool_radius_is_an_error_in_the_tool_center(self):
        # The tool center would not move at all: the arc can not be built.
        radius, status, message = resolve_radius(5.0, 5.0, SPACE_TOOL_CENTER)
        self.assertEqual(status, ERROR)
        self.assertTrue(message)

    def test_zero_radius_is_an_error(self):
        for radius_in in (0.0, -1.0):
            radius, status, message = resolve_radius(radius_in, 5.0,
                                                      SPACE_NOMINAL)
            self.assertEqual(status, ERROR)
            self.assertTrue(message)


class TestBuildLeadIn(unittest.TestCase):

    def test_nominal_radius_starts_the_arc_radially(self):
        # The G41/G42 lead in of the program is a straight line plus a quarter
        # arc. With the machine compensation the programmed path is nominal
        # (the machine offsets it): the arc has the workpiece radius and the
        # straight line approaches the start of the arc radially (it is
        # tangent to the arc there). Its length is derived from the tool
        # radius (R_w - r_tool).
        workpiece_radius = 10.0
        tool_radius = 5.0
        build_up_length = workpiece_radius - tool_radius
        start = Point(0, 0)
        angle = 0.0
        side = 1

        geos, status, message = build_lead_in(start, angle, side,
                                              workpiece_radius, tool_radius,
                                              SPACE_NOMINAL, LEAD_RADIUS,
                                              length=build_up_length)
        self.assertEqual(status, OK, message)
        self.assertEqual(len(geos), 2)

        # The arc is nominal: its center is the start point offset by the
        # workpiece radius, its start is the start of the nominal arc (A).
        Oein = start.get_arc_point(angle + pi / 2, workpiece_radius)
        Ps_ein = Oein.get_arc_point(angle + pi, workpiece_radius)
        # The straight line approaches A radially, its length is the common
        # length (the 'radius' method is merged into the 'startmove').
        start_ein = Ps_ein.get_arc_point(angle + pi / 2, build_up_length)

        self.assertAlmostEqual(geos[0].Ps.x, start_ein.x)
        self.assertAlmostEqual(geos[0].Ps.y, start_ein.y)
        self.assertAlmostEqual(geos[0].Pe.x, Ps_ein.x)
        self.assertAlmostEqual(geos[0].Pe.y, Ps_ein.y)
        self.assertAlmostEqual(geos[1].Ps.x, Ps_ein.x)
        self.assertAlmostEqual(geos[1].Ps.y, Ps_ein.y)
        self.assertAlmostEqual(geos[1].O.x, Oein.x)
        self.assertAlmostEqual(geos[1].O.y, Oein.y)
        self.assertAlmostEqual(geos[1].r, workpiece_radius)

    def test_arc_is_tangent_to_the_contour(self):
        geos, status, message = build_lead_in(Point(0, 0), 0.0, 1, 10.0, 5.0,
                                              SPACE_NOMINAL, LEAD_RADIUS,
                                              length=5.0)
        self.assertEqual(status, OK, message)
        arc = geos[1]
        self.assertEqual(arc.Pe.x, 0.0)
        self.assertEqual(arc.Pe.y, 0.0)
        # The tangent of the arc at its end is the travel direction (+x)
        _, tangent = arc.get_start_end_points(False, False)
        self.assertAlmostEqual(tangent.x, 1.0)
        self.assertAlmostEqual(tangent.y, 0.0)

    def test_tool_center_space_uses_the_tool_center_radius(self):
        geos, status, message = build_lead_in(Point(0, 0), 0.0, 1, 10.0, 5.0,
                                              SPACE_TOOL_CENTER, LEAD_RADIUS,
                                              length=5.0)
        self.assertEqual(status, OK, message)
        self.assertEqual(geos[1].r, 5.0)
        # The straight line is tangent to the arc (perpendicular to the
        # contour) and has the length of the tool center radius
        self.assertAlmostEqual(geos[0].length, 5.0)

    def test_straight_lead_in_extends_the_contour(self):
        geos, status, message = build_lead_in(Point(0, 0), 0.0, 1, 10.0, 5.0,
                                              SPACE_NOMINAL, LEAD_STRAIGHT,
                                              length=5.0)
        self.assertEqual(status, OK, message)
        self.assertEqual(len(geos), 1)
        self.assertAlmostEqual(geos[0].length, 5.0)
        # The dive point is behind the contour start
        self.assertAlmostEqual(geos[0].Ps.x, -5.0)
        self.assertAlmostEqual(geos[0].Ps.y, 0.0)

    def test_straight_lead_in_uses_the_common_length(self):
        geos, status, message = build_lead_in(Point(0, 0), 0.0, 1, 10.0, 5.0,
                                              SPACE_NOMINAL, LEAD_STRAIGHT,
                                              length=12.5)
        self.assertEqual(status, OK, message)
        self.assertAlmostEqual(geos[0].length, 12.5)
        self.assertAlmostEqual(geos[0].Ps.x, -12.5)

    def test_straight_lead_in_without_length_is_an_error(self):
        geos, status, message = build_lead_in(Point(0, 0), 0.0, 1, 10.0, 5.0,
                                              SPACE_NOMINAL, LEAD_STRAIGHT)
        self.assertEqual(status, ERROR)
        self.assertEqual(geos, [])
        self.assertTrue(message)

    def test_startmove_lead_in_is_the_start_move_of_the_program(self):
        # The start move of the program: a straight line and a quarter arc
        # whose radius is the workpiece radius (the machine offsets the
        # nominal path by the tool radius). The straight line approaches the
        # arc radially and its length is the common length.
        workpiece_radius = 10.0
        tool_radius = 5.0
        length = tool_radius
        start = Point(0, 0)
        angle = 0.0
        side = 1

        geos, status, message = build_lead_in(start, angle, side,
                                              workpiece_radius, tool_radius,
                                              SPACE_NOMINAL, LEAD_STARTMOVE,
                                              length=length)
        self.assertEqual(status, OK, message)
        self.assertEqual(len(geos), 2)

        # The nominal arc: its center is the start point offset by the
        # workpiece radius, its start is the start of the nominal arc (A).
        Oein = start.get_arc_point(angle + side * pi / 2, workpiece_radius)
        Ps_ein = Oein.get_arc_point(angle + pi, workpiece_radius)
        # The straight line approaches A radially, its length is the common
        # length.
        start_ein = Ps_ein.get_arc_point(angle + side * pi / 2, length)

        self.assertAlmostEqual(geos[0].Ps.x, start_ein.x)
        self.assertAlmostEqual(geos[0].Ps.y, start_ein.y)
        self.assertAlmostEqual(geos[0].length, length)
        self.assertAlmostEqual(geos[0].Pe.x, Ps_ein.x)
        self.assertAlmostEqual(geos[0].Pe.y, Ps_ein.y)
        self.assertAlmostEqual(geos[1].O.x, Oein.x)
        self.assertAlmostEqual(geos[1].O.y, Oein.y)
        self.assertAlmostEqual(geos[1].r, workpiece_radius)

    def test_startmove_lead_in_uses_the_common_length(self):
        # The straight line of the start move is longer if the common length
        # is bigger: it is a radial line of the common length.
        geos, status, message = build_lead_in(Point(0, 0), 0.0, 1, 10.0, 5.0,
                                              SPACE_NOMINAL, LEAD_STARTMOVE,
                                              length=8.0)
        self.assertEqual(status, OK, message)
        self.assertEqual(len(geos), 2)
        self.assertAlmostEqual(geos[0].length, 8.0)

    def test_startmove_is_the_circle_lead_in_in_the_tool_center_space(self):
        # With the internal cutter compensation the start move is the same as
        # the 'circle' lead in: a radial line and a quarter arc of the already
        # offset tool center path (radius R_w - r_tool).
        geos, status, message = build_lead_in(Point(0, 0), 0.0, 1, 10.0, 5.0,
                                              SPACE_TOOL_CENTER, LEAD_STARTMOVE,
                                              length=5.0)
        self.assertEqual(status, OK, message)
        self.assertEqual(len(geos), 2)
        self.assertAlmostEqual(geos[1].r, 5.0)

    def test_invalid_radius_is_rejected(self):
        geos, status, message = build_lead_in(Point(0, 0), 0.0, 1, 3.0, 5.0,
                                              SPACE_NOMINAL, LEAD_RADIUS,
                                              length=5.0)
        self.assertEqual(status, ERROR)
        self.assertEqual(geos, [])

    def test_radius_lead_in_without_length_is_an_error(self):
        # The 'radius' method is merged into the 'startmove' method: it needs
        # the common length of the straight part (the G40 approach line).
        geos, status, message = build_lead_in(Point(0, 0), 0.0, 1, 10.0, 5.0,
                                              SPACE_NOMINAL, LEAD_RADIUS)
        self.assertEqual(status, ERROR)
        self.assertEqual(geos, [])


class TestBuildLeadOut(unittest.TestCase):

    def test_radius_lead_out_leaves_the_contour(self):
        geos, status, message = build_lead_out(Point(0, 0), 0.0, 1, 10.0, 5.0,
                                               SPACE_NOMINAL, LEAD_RADIUS)
        self.assertEqual(status, OK, message)
        self.assertEqual(len(geos), 1)
        arc = geos[0]
        self.assertEqual(arc.r, 10.0)
        self.assertEqual(arc.Ps.x, 0.0)
        self.assertEqual(arc.Ps.y, 0.0)
        # The arc leaves the contour: its end is not on the tangent line
        self.assertNotAlmostEqual(arc.Pe.y, 0.0)

    def test_straight_lead_out_continues_the_cut(self):
        geos, status, message = build_lead_out(Point(0, 0), 0.0, 1, 10.0, 5.0,
                                               SPACE_NOMINAL, LEAD_STRAIGHT,
                                               length=5.0)
        self.assertEqual(status, OK, message)
        self.assertEqual(len(geos), 1)
        self.assertAlmostEqual(geos[0].length, 5.0)
        self.assertAlmostEqual(geos[0].Pe.x, 5.0)

    def test_straight_lead_out_uses_the_common_length(self):
        geos, status, message = build_lead_out(Point(0, 0), 0.0, 1, 10.0, 5.0,
                                               SPACE_NOMINAL, LEAD_STRAIGHT,
                                               length=12.5)
        self.assertEqual(status, OK, message)
        self.assertAlmostEqual(geos[0].length, 12.5)
        self.assertAlmostEqual(geos[0].Pe.x, 12.5)

    def test_straight_lead_out_without_length_is_an_error(self):
        geos, status, message = build_lead_out(Point(0, 0), 0.0, 1, 10.0, 5.0,
                                               SPACE_NOMINAL, LEAD_STRAIGHT)
        self.assertEqual(status, ERROR)
        self.assertEqual(geos, [])
        self.assertTrue(message)

    def test_startmove_lead_out_is_a_straight_line_and_an_arc(self):
        geos, status, message = build_lead_out(Point(0, 0), 0.0, 1, 10.0, 5.0,
                                               SPACE_NOMINAL, LEAD_STARTMOVE,
                                               length=7.0)
        self.assertEqual(status, OK, message)
        self.assertEqual(len(geos), 2)
        # The straight line continues the cut
        self.assertAlmostEqual(geos[0].length, 7.0)
        self.assertAlmostEqual(geos[0].Pe.x, 7.0)
        # The arc leaves the contour
        self.assertIsInstance(geos[1], ArcGeo)
        self.assertAlmostEqual(geos[1].Ps.x, 7.0)
        self.assertAlmostEqual(geos[1].Ps.y, 0.0)
        self.assertNotAlmostEqual(geos[1].Pe.y, 0.0)

    def test_straight_lead_out_along_the_contour_is_allowed(self):
        # A straight lead out which would run along the contour is written as
        # it is (no error): the caller decides whether this is useful.
        geos, status, message = build_lead_out(Point(0, 0), 0.0, 1, 10.0, 5.0,
                                               SPACE_NOMINAL, LEAD_STRAIGHT,
                                               length=5.0)
        self.assertEqual(status, OK, message)
        self.assertEqual(len(geos), 1)
        self.assertAlmostEqual(geos[0].length, 5.0)
        self.assertAlmostEqual(geos[0].Pe.x, 5.0)


class TestValidateLeadMove(unittest.TestCase):
    """The central validation of the lead in / lead out parameters."""

    def test_valid_combination(self):
        ok, errors, warnings = validate_lead_move(10.0, 20.0, 5.0,
                                                   LEAD_RADIUS, LEAD_STRAIGHT)
        self.assertTrue(ok)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_invalid_tool_diameter(self):
        for diameter in (0.0, -1.0):
            ok, errors, warnings = validate_lead_move(diameter, 20.0, 5.0,
                                                       LEAD_RADIUS, LEAD_STRAIGHT)
            self.assertFalse(ok)
            self.assertEqual(errors[0][0], 'tool_diameter')
            self.assertTrue(errors[0][1])

    def test_radius_smaller_than_the_tool_radius_is_an_error(self):
        ok, errors, warnings = validate_lead_move(10.0, 4.0, 5.0,
                                                   LEAD_RADIUS, LEAD_STRAIGHT)
        self.assertFalse(ok)
        self.assertEqual(errors[0][0], 'lead_radius')
        self.assertTrue(errors[0][1])

    def test_radius_equal_to_the_tool_radius_is_a_warning(self):
        ok, errors, warnings = validate_lead_move(10.0, 5.0, 5.0,
                                                   LEAD_RADIUS, LEAD_STRAIGHT)
        self.assertTrue(ok)
        self.assertEqual(errors, [])
        self.assertEqual(warnings[0][0], 'lead_radius')

    def test_unused_radius_does_not_prevent_a_straight_movement(self):
        # Neither the lead in nor the lead out uses a circle: the radius is
        # not needed, so it must not be validated.
        ok, errors, warnings = validate_lead_move(10.0, 1.0, 5.0,
                                                   LEAD_STRAIGHT, LEAD_STRAIGHT)
        self.assertTrue(ok)
        self.assertEqual(errors, [])

    def test_unused_length_does_not_prevent_a_radius_movement(self):
        ok, errors, warnings = validate_lead_move(10.0, 20.0, 0.0,
                                                   LEAD_RADIUS, LEAD_RADIUS)
        self.assertTrue(ok)
        self.assertEqual(errors, [])

    def test_length_is_needed_by_the_straight_methods(self):
        for modes in ((LEAD_STRAIGHT, LEAD_OFF), (LEAD_OFF, LEAD_STRAIGHT),
                      (LEAD_STARTMOVE, LEAD_OFF)):
            ok, errors, warnings = validate_lead_move(10.0, 20.0, 0.0,
                                                       modes[0], modes[1])
            self.assertFalse(ok)
            self.assertEqual(errors[0][0], 'lead_length')

    def test_radius_is_needed_by_the_arc_methods(self):
        for modes in ((LEAD_RADIUS, LEAD_OFF), (LEAD_OFF, LEAD_RADIUS),
                      (LEAD_STARTMOVE, LEAD_OFF)):
            ok, errors, warnings = validate_lead_move(10.0, 0.0, 5.0,
                                                       modes[0], modes[1])
            self.assertFalse(ok)
            self.assertEqual(errors[0][0], 'lead_radius')

    def test_no_method_needs_no_parameter(self):
        ok, errors, warnings = validate_lead_move(10.0, 0.0, 0.0,
                                                   LEAD_OFF, LEAD_OFF)
        self.assertTrue(ok)
        self.assertEqual(errors, [])


class TestChainDirection(unittest.TestCase):
    """The travel direction at the ends of a chain.

    For an arc the travel direction is the tangent at the point, not the angle
    of the point on the arc: the direction of a quarter arc changes by 90
    degrees between its start and its end.
    """

    def arc_chain(self):
        # A line and a CCW quarter arc (radius 100, centered at the origin)
        # from (100, 0) to (100, 100).
        return [LineGeo(Point(0, 0), Point(100, 0)),
                ArcGeo(Ps=Point(100, 0), Pe=Point(100, 100), O=Point(0, 0),
                       r=100.0, direction=1)]

    def test_chain_direction_of_an_arc_is_the_end_tangent(self):
        # The start tangent of the arc is +90 degrees, the end tangent is
        # +135 degrees. The direction of the chain is the end tangent.
        angle = chain_direction(self.arc_chain())
        self.assertAlmostEqual(angle, 3.0 * pi / 4.0)

    def test_chain_direction_of_a_line_is_the_line_direction(self):
        angle = chain_direction([LineGeo(Point(0, 0), Point(0, 10))])
        self.assertAlmostEqual(angle, pi / 2.0)

    def test_chain_direction_skips_empty_geometries(self):
        chain = [LineGeo(Point(0, 0), Point(10, 0)),
                 LineGeo(Point(10, 0), Point(10, 0))]
        self.assertAlmostEqual(chain_direction(chain), 0.0)


class TestLeadOutAtAnArcEnd(unittest.TestCase):
    """The lead out at the end of a contour which ends with an arc."""

    def arc_chain(self):
        return [LineGeo(Point(0, 0), Point(100, 0)),
                ArcGeo(Ps=Point(100, 0), Pe=Point(100, 100), O=Point(0, 0),
                       r=100.0, direction=1)]

    def test_the_lead_out_leaves_the_arc_tangentially(self):
        exit_geos, status, message = build_exit_geometries(
            self.arc_chain(), side=1, space=SPACE_NOMINAL, tool_radius=5.0,
            lead_out_mode=LEAD_RADIUS, lead_radius=20.0,
            overcut_enabled=False, overcut_length=0.0)
        self.assertEqual(status, OK, message)
        self.assertEqual(len(exit_geos), 1)
        arc = exit_geos[0]
        self.assertIsInstance(arc, ArcGeo)
        # The lead out starts at the arc end.
        self.assertAlmostEqual(arc.Ps.x, 100.0)
        self.assertAlmostEqual(arc.Ps.y, 100.0)
        # Its tangent at the start equals the contour tangent at its end
        # (+135 degrees): the lead out does not kink.
        _, tangent = arc.get_start_end_points(True, False)
        self.assertAlmostEqual(tangent.x, -sqrt(2.0) / 2.0)
        self.assertAlmostEqual(tangent.y, sqrt(2.0) / 2.0)


class TestBuildOvercut(unittest.TestCase):

    def test_overcut_repeats_the_contour_beginning(self):
        chain = square_chain()
        geos, status, message = build_overcut(chain, 50.0)
        self.assertEqual(status, OK, message)
        self.assertEqual(len(geos), 1)
        self.assertAlmostEqual(geos[0].length, 50.0)
        # The overcut starts at the closing point of the contour
        self.assertAlmostEqual(geos[0].Ps.x, 0.0)
        self.assertAlmostEqual(geos[0].Ps.y, 0.0)
        self.assertAlmostEqual(geos[0].Pe.x, 50.0)

    def test_overcut_spans_several_segments(self):
        chain = square_chain()
        geos, status, message = build_overcut(chain, 150.0)
        self.assertEqual(status, OK, message)
        self.assertEqual(len(geos), 2)
        self.assertAlmostEqual(geos[0].length, 100.0)
        self.assertAlmostEqual(geos[1].length, 50.0)

    def test_overcut_does_not_modify_the_contour(self):
        chain = square_chain()
        before = [(geo.Ps.x, geo.Ps.y, geo.Pe.x, geo.Pe.y) for geo in chain]
        build_overcut(chain, 50.0)
        after = [(geo.Ps.x, geo.Ps.y, geo.Pe.x, geo.Pe.y) for geo in chain]
        self.assertEqual(before, after)

    def test_overcut_longer_than_the_contour_is_an_error(self):
        chain = square_chain()
        geos, status, message = build_overcut(chain, 1000.0)
        self.assertEqual(status, ERROR)
        self.assertEqual(geos, [])

    def test_zero_length_overcut_is_an_error(self):
        chain = square_chain()
        geos, status, message = build_overcut(chain, 0.0)
        self.assertEqual(status, ERROR)

    def test_break_hops_are_not_counted(self):
        chain = [LineGeo(Point(0, 0), Point(100, 0)),
                 BreakGeo(Point(100, 0), Point(200, 0), 0.0, 0.0, 0.0),
                 LineGeo(Point(200, 0), Point(300, 0))]
        # The cut length is 200, the break hop is not cut
        self.assertAlmostEqual(chain_cut_length(chain), 200.0)
        geos, status, message = build_overcut(chain, 150.0)
        self.assertEqual(status, OK, message)
        # The first line (100), the repeated hop and 50 of the next line
        self.assertEqual(len(geos), 3)
        self.assertAlmostEqual(geos[0].length, 100.0)
        self.assertIsInstance(geos[1], BreakGeo)
        self.assertAlmostEqual(geos[2].length, 50.0)

    def test_break_hop_is_repeated(self):
        chain = [BreakGeo(Point(0, 0), Point(100, 0), 0.0, 0.0, 0.0),
                 LineGeo(Point(100, 0), Point(200, 0))]
        geos, status, message = build_overcut(chain, 50.0)
        self.assertEqual(status, OK, message)
        # The hop is repeated (so the tab is not cut), the line is cut
        self.assertEqual(len(geos), 2)
        self.assertIsInstance(geos[0], BreakGeo)
        self.assertAlmostEqual(geos[1].length, 50.0)

    def test_overcut_of_an_arc(self):
        chain = [ArcGeo(Ps=Point(0, 0), Pe=Point(50, 50), O=Point(0, 50),
                        r=50, direction=1)]
        geos, status, message = build_overcut(chain, 10.0)
        self.assertEqual(status, OK, message)
        self.assertEqual(len(geos), 1)
        self.assertAlmostEqual(geos[0].length, 10.0)
        self.assertAlmostEqual(geos[0].O.x, 0.0)
        self.assertAlmostEqual(geos[0].O.y, 50.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
