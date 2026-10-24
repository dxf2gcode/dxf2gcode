# -*- coding: utf-8 -*-
"""
Tests of the four methods of the lead in and of the lead out.

The methods are selected independently for the lead in and for the lead out:

* 'off'       : no geometry at all
* 'straight'  : a straight line of the common length
* 'radius'    : a quarter arc of the common radius. With G41/G42 the arc is
                nominal (the machine offsets it) and is preceded by the radial
                straight line which builds up the cutter compensation. That
                straight line is NOT an additional lead in segment: it is
                required to build up the tool radius compensation and its
                length is derived from the tool radius (not from the common
                length). With the internal compensation the arc is the tool
                center path and the straight line is the radial transition
                from the dive point to the start of the arc.
* 'startmove' : the start move of the program: a straight line (the common
                length) and a quarter arc (the common radius). It is only
                generated with G41/G42.

The tests check the generated geometry elements and the resulting G-Code
movements of every method, the lead out compared to the lead in and the
passing of the method from the GUI (the dropdown) to the geometry.

Run from the repository root:

    python -m unittest discover -s tests -t tests -p "dxf2gcode_leadmove_modes_test.py" -v
"""
from __future__ import absolute_import

import os
import shutil
import sys
import tempfile
import unittest
from math import sqrt

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [_TEST_DIR, os.path.join(os.path.dirname(_TEST_DIR), "source")]

import dxf2gcode.globals.globals as g  # noqa: E402
from dxf2gcode.core.arcgeo import ArcGeo  # noqa: E402
from dxf2gcode.core.leadmove import (LEAD_OFF, LEAD_RADIUS,  # noqa: E402
                                     LEAD_STARTMOVE, LEAD_STRAIGHT)
from dxf2gcode.core.linegeo import LineGeo  # noqa: E402
from dxf2gcode.core.point import Point  # noqa: E402
from dxf2gcode.globals.config import MyConfig  # noqa: E402
from dxf2gcode.Qt.QtWidgets import QApplication  # noqa: E402

from dxf2gcode_leadmove_golden_test import (GoldenTestBase, build_shape,
                                           export_gcode)

_APP = None

TOOL_DIAMETER = 10.0
TOOL_RADIUS = TOOL_DIAMETER / 2.0
WORKPIECE_RADIUS = 20.0    # the radius at the workpiece (R_w)
COMMON_LENGTH = 5.0        # the common length (L)


def _app():
    global _APP
    if _APP is None:
        _APP = QApplication.instance() or QApplication([])
    return _APP


class LeadInModeTestBase(GoldenTestBase):

    def setUp(self):
        GoldenTestBase.setUp(self)
        _app()
        self._old_done_by_machine = g.config.vars.Cutter_Compensation[
            "done_by_machine"]

    def tearDown(self):
        g.config.vars.Cutter_Compensation["done_by_machine"] = \
            self._old_done_by_machine
        GoldenTestBase.tearDown(self)

    def shape_with(self, mode, length=COMMON_LENGTH, done_by_machine=True,
                   lead_out_mode=LEAD_OFF, radius=WORKPIECE_RADIUS):
        """
        A closed contour with the given lead in method.
        """
        shape, layer = build_shape(
            closed=True, cut_cor=41, done_by_machine=done_by_machine,
            tool_diameter=TOOL_DIAMETER,
            layer_settings=dict(lead_in_mode=mode, lead_out_mode=lead_out_mode,
                                lead_radius=radius, lead_length=length))
        return shape, layer

    def gcode_moves(self, gcode):
        """The positions of the G-Code (the movements in the XY plane)."""
        moves = []
        for line in gcode.splitlines():
            fields = line.split()
            if not fields or fields[0] not in ("G0", "G1", "G2", "G3"):
                continue
            values = {}
            for index in range(1, len(fields) - 1, 2):
                try:
                    values[fields[index]] = float(fields[index + 1])
                except ValueError:
                    pass
            if "X" in values and "Y" in values:
                moves.append((fields[0], values["X"], values["Y"]))
        return moves

    def gcode_blocks(self, gcode):
        """The G-Code blocks of the movements in the XY plane."""
        return [line.split()[0] for line in gcode.splitlines()
                if line.split() and line.split()[0] in ("G0", "G1", "G2", "G3")
                and "X" in line and "Y" in line]


class TestLeadInModes(LeadInModeTestBase):
    """The geometry of the four methods of the lead in."""

    def test_off_has_no_geometry(self):
        shape, layer = self.shape_with(LEAD_OFF)
        self.assertEqual(list(shape.stmove.lead_in_geos), [])

    def test_straight_is_one_line_of_the_common_length(self):
        shape, layer = self.shape_with(LEAD_STRAIGHT, length=7.5)
        geos = list(shape.stmove.lead_in_geos)
        self.assertEqual(len(geos), 1)
        self.assertIsInstance(geos[0], LineGeo)
        self.assertAlmostEqual(geos[0].length, 7.5)
        # The contour is extended backwards in the tool center plane: the lead
        # in ends at the tool center start (the contour start offset to the
        # compensation side by the tool radius), because it is cut with G40
        # before the machine compensation is activated.
        self.assertAlmostEqual(geos[0].Pe.x, 0.0)
        self.assertAlmostEqual(geos[0].Pe.y, TOOL_RADIUS)
        self.assertAlmostEqual(geos[0].Ps.y, TOOL_RADIUS)

    def test_radius_is_the_arc_with_the_compensation_build_up(self):
        shape, layer = self.shape_with(LEAD_RADIUS)
        geos = list(shape.stmove.lead_in_geos)
        # The G40 approach line (tool center path), the nominal build up line
        # and the nominal quarter arc.
        self.assertEqual(len(geos), 3)
        self.assertIsInstance(geos[0], LineGeo)   # G40 approach line
        self.assertIsInstance(geos[1], LineGeo)   # nominal build up line
        self.assertIsInstance(geos[2], ArcGeo)    # nominal arc
        # The nominal arc is programmed in the nominal plane (the machine
        # compensates it): it ends at the contour start and has the radius at
        # the workpiece.
        self.assertAlmostEqual(geos[2].Pe.x, 0.0)
        self.assertAlmostEqual(geos[2].Pe.y, 0.0)
        self.assertAlmostEqual(geos[2].r, WORKPIECE_RADIUS)
        # The nominal line approaches the start of the arc radially (it is
        # tangent to the arc there): it is perpendicular to the travel
        # direction and its length is derived from the tool radius.
        self.assertAlmostEqual(geos[1].Pe.x, geos[2].Ps.x)
        self.assertAlmostEqual(geos[1].Pe.y, geos[2].Ps.y)
        self.assertAlmostEqual(geos[1].Ps.x, geos[2].Ps.x)
        self.assertAlmostEqual(geos[1].Ps.y,
                               geos[2].Ps.y + (WORKPIECE_RADIUS - TOOL_RADIUS))
        # The G40 approach line is parallel to the nominal line and offset to
        # the compensation side by the tool radius: the tool center is beside
        # the nominal line while G40 is active.
        self.assertAlmostEqual(geos[0].length, COMMON_LENGTH)
        self.assertAlmostEqual(geos[0].Pe.x, geos[1].Ps.x + TOOL_RADIUS)
        self.assertAlmostEqual(geos[0].Pe.y, geos[1].Ps.y)
        self.assertAlmostEqual(geos[0].Ps.x, geos[1].Ps.x + TOOL_RADIUS)
        self.assertAlmostEqual(geos[0].Ps.y, geos[1].Ps.y + COMMON_LENGTH)

    def test_the_build_up_does_not_depend_on_the_common_length(self):
        # The straight line of the 'startmove' method (the nominal build up
        # line) is the movement which builds up the cutter compensation: its
        # length is derived from the tool radius, not from the common length.
        # The common length is only used by the 'straight' method and by the
        # G40 approach line of the machine compensation.
        lengths = []
        for common_length in (2.0, 50.0):
            shape, layer = self.shape_with(LEAD_STARTMOVE,
                                           length=common_length)
            geos = list(shape.stmove.lead_in_geos)
            lengths.append(geos[1].length)
        self.assertAlmostEqual(lengths[0], lengths[1])
        # The radial build up line has the length of the tool center radius
        # (the workpiece radius minus the tool radius).
        tool_center_radius = WORKPIECE_RADIUS - TOOL_RADIUS
        self.assertAlmostEqual(lengths[0], tool_center_radius)

    def test_startmove_is_a_straight_line_and_an_arc(self):
        shape, layer = self.shape_with(LEAD_STARTMOVE, length=7.5)
        geos = list(shape.stmove.lead_in_geos)
        self.assertEqual(len(geos), 3)
        self.assertIsInstance(geos[0], LineGeo)   # G40 approach line
        self.assertIsInstance(geos[1], LineGeo)   # nominal line
        self.assertIsInstance(geos[2], ArcGeo)    # nominal arc
        # The arc is nominal (the lead in is programmed in the nominal plane,
        # the machine offsets it by the tool radius).
        self.assertAlmostEqual(geos[2].r, WORKPIECE_RADIUS)

    def test_the_startmove_uses_the_common_length(self):
        # The straight line of the start move is longer if the common length
        # is bigger (in contrast to the build up of the 'radius' method).
        lengths = []
        for common_length in (2.0, 50.0):
            shape, layer = self.shape_with(LEAD_STARTMOVE,
                                           length=common_length)
            geos = list(shape.stmove.lead_in_geos)
            lengths.append(geos[0].length)
        self.assertNotAlmostEqual(lengths[0], lengths[1])
        self.assertGreater(lengths[1], lengths[0])

    def test_the_startmove_is_the_circle_for_the_internal_compensation(self):
        # With the internal compensation the start move is the same as the
        # 'circle' lead in (a radial line and a quarter arc of the tool center
        # path).
        shape, layer = self.shape_with(LEAD_STARTMOVE, done_by_machine=False)
        geos = list(shape.stmove.lead_in_geos)
        self.assertEqual(len(geos), 2)
        self.assertIsInstance(geos[0], LineGeo)
        self.assertIsInstance(geos[1], ArcGeo)
        # The tool center arc has the tool center radius (R_w - r_tool).
        self.assertAlmostEqual(geos[1].r, WORKPIECE_RADIUS - TOOL_RADIUS)

    def test_the_radius_lead_in_exists_with_the_internal_compensation(self):
        shape, layer = self.shape_with(LEAD_RADIUS, done_by_machine=False)
        geos = list(shape.stmove.lead_in_geos)
        self.assertEqual(len(geos), 2)
        self.assertIsInstance(geos[0], LineGeo)
        self.assertIsInstance(geos[1], ArcGeo)


class TestLeadOutModes(LeadInModeTestBase):
    """The lead out: the cutter compensation is already active, so no build
    up movement is needed."""

    def test_off_has_no_geometry(self):
        shape, layer = self.shape_with(LEAD_OFF, lead_out_mode=LEAD_OFF)
        self.assertEqual(list(shape.stmove.exit_geos), [])

    def test_radius_is_the_arc_only(self):
        shape, layer = self.shape_with(LEAD_OFF, lead_out_mode=LEAD_RADIUS)
        geos = list(shape.stmove.exit_geos)
        self.assertEqual(len(geos), 1)
        self.assertIsInstance(geos[0], ArcGeo)
        self.assertAlmostEqual(geos[0].r, WORKPIECE_RADIUS)

    def test_straight_is_one_line_of_the_common_length(self):
        shape, layer = self.shape_with(LEAD_OFF, lead_out_mode=LEAD_STRAIGHT)
        geos = list(shape.stmove.exit_geos)
        self.assertEqual(len(geos), 1)
        self.assertIsInstance(geos[0], LineGeo)

    def test_startmove_is_a_straight_line_and_an_arc(self):
        shape, layer = self.shape_with(LEAD_OFF, lead_out_mode=LEAD_STARTMOVE)
        geos = list(shape.stmove.exit_geos)
        self.assertEqual(len(geos), 2)
        self.assertIsInstance(geos[0], LineGeo)
        self.assertIsInstance(geos[1], ArcGeo)


class TestLeadInGCode(LeadInModeTestBase):
    """The G-Code of the four methods of the lead in."""

    def test_the_radius_lead_in_has_one_straight_move_before_the_arc(self):
        shape, layer = self.shape_with(LEAD_RADIUS)
        gcode = export_gcode(shape, layer)
        blocks = self.gcode_blocks(gcode)
        # The rapid to the dive point, the G40 approach line (G1, tool center
        # path), the nominal line (G1) and the nominal arc (G3).
        self.assertEqual(blocks[0], "G0")
        self.assertEqual(blocks[1], "G1")
        self.assertEqual(blocks[2], "G1")
        self.assertEqual(blocks[3], "G3")
        # The G40 approach line is cut without compensation; G41/G42 is
        # activated after it (and after the plunge) so that the machine offsets
        # the nominal line and the nominal arc.
        g41 = gcode.index("G41")
        self.assertGreater(g41, gcode.index("G1"))
        self.assertLess(g41, gcode.index("G3"))

    def test_the_straight_lead_in_has_no_arc(self):
        shape, layer = self.shape_with(LEAD_STRAIGHT)
        gcode = export_gcode(shape, layer)
        blocks = self.gcode_blocks(gcode)
        self.assertEqual(blocks[0], "G0")
        self.assertEqual(blocks[1], "G1")
        self.assertNotIn("G3", blocks)

    def test_the_startmove_lead_in_has_one_straight_move_before_the_arc(self):
        shape, layer = self.shape_with(LEAD_STARTMOVE)
        gcode = export_gcode(shape, layer)
        blocks = self.gcode_blocks(gcode)
        self.assertEqual(blocks[0], "G0")
        self.assertEqual(blocks[1], "G1")
        self.assertEqual(blocks[2], "G1")
        self.assertEqual(blocks[3], "G3")

    def test_the_off_lead_in_is_an_error_with_g41(self):
        # The machine can only build the compensation with a movement in the
        # XY plane: without a lead in the shape is not milled.
        shape, layer = self.shape_with(LEAD_OFF)
        gcode = export_gcode(shape, layer)
        self.assertEqual(gcode, "")

    def test_the_lead_in_ends_at_the_start_point_of_the_contour(self):
        for mode in (LEAD_STRAIGHT, LEAD_RADIUS, LEAD_STARTMOVE):
            shape, layer = self.shape_with(mode)
            gcode = export_gcode(shape, layer)
            moves = self.gcode_moves(gcode)
            # The last element of the lead in ends at the start point of the
            # contour (the contour of the test starts at (0, 0)) - and the
            # G-Code contains this position.
            lead_in = list(shape.stmove.lead_in_geos)
            end = lead_in[-1].Pe
            self.assertTrue(
                any(abs(move[1] - end.x) < 1e-6 and
                    abs(move[2] - end.y) < 1e-6 for move in moves),
                "%s: %s" % (mode, gcode))


class TestModeFromTheGui(LeadInModeTestBase):
    """The method selected in the GUI is really used for the geometry."""

    def test_the_selected_method_is_used(self):
        from dxf2gcode.core.stmove import StMove
        for mode, expected in ((LEAD_OFF, 0), (LEAD_STRAIGHT, 1),
                               (LEAD_RADIUS, 3), (LEAD_STARTMOVE, 3)):
            shape, layer = self.shape_with(mode)
            self.assertEqual(len(shape.stmove.lead_in_geos), expected, mode)
            # The layer holds the selected method and the toolpath is built
            # from it.
            self.assertEqual(layer.get_lead_in_mode(), mode)
            shape.stmove = StMove(shape)
            self.assertEqual(len(shape.stmove.lead_in_geos), expected, mode)


class TestMachineCompCircleLeadIn(LeadInModeTestBase):
    """The circle / start move lead in of the machine cutter compensation.

    The lead in consists of the G40 approach line (the tool center path which
    dxf2gcode calculates itself, cut before G41/G42) and the nominal lead in
    (the line and the arc, compensated by the machine after G41/G42).
    """

    def _shape_with(self, cut_cor=41, mode=LEAD_RADIUS,
                    tool_diameter=TOOL_DIAMETER, radius=WORKPIECE_RADIUS,
                    length=COMMON_LENGTH, closed=True):
        shape, layer = build_shape(
            closed=closed, cut_cor=cut_cor, done_by_machine=True,
            tool_diameter=tool_diameter,
            layer_settings=dict(lead_in_mode=mode, lead_out_mode=LEAD_OFF,
                                lead_radius=radius, lead_length=length))
        return shape, layer, list(shape.stmove.lead_in_geos)

    def _check(self, geos, side, tool_radius, workpiece_radius, common_length):
        approach, nominal_line, arc = geos
        # The nominal line ends at the start of the nominal arc.
        self.assertAlmostEqual(nominal_line.Pe.x, arc.Ps.x)
        self.assertAlmostEqual(nominal_line.Pe.y, arc.Ps.y)
        # The nominal arc ends at the contour start and has the nominal radius.
        self.assertAlmostEqual(arc.Pe.x, 0.0)
        self.assertAlmostEqual(arc.Pe.y, 0.0)
        self.assertAlmostEqual(arc.r, workpiece_radius)
        # The G40 approach line has the common length.
        self.assertAlmostEqual(approach.length, common_length)
        # The G40 approach line is parallel to the nominal line and offset by
        # the tool radius to the side the machine compensates to (left for
        # G41, right for G42).
        dx = nominal_line.Pe.x - nominal_line.Ps.x
        dy = nominal_line.Pe.y - nominal_line.Ps.y
        norm = sqrt(dx * dx + dy * dy)
        # The perpendicular distance of the approach line end from the nominal
        # line.
        vx = approach.Pe.x - nominal_line.Ps.x
        vy = approach.Pe.y - nominal_line.Ps.y
        perpendicular = abs(vx * (-dy / norm) + vy * (dx / norm))
        self.assertAlmostEqual(perpendicular, tool_radius)
        # The signed offset along the left normal of the nominal line travel
        # direction: +r for G41, -r for G42.
        signed = vx * (-dy / norm) + vy * (dx / norm)
        self.assertAlmostEqual(signed, side * tool_radius)

    def test_the_g40_approach_line_is_offset_g41(self):
        shape, layer, geos = self._shape_with(cut_cor=41)
        self.assertEqual(len(geos), 3)
        self.assertIsInstance(geos[0], LineGeo)
        self.assertIsInstance(geos[1], LineGeo)
        self.assertIsInstance(geos[2], ArcGeo)
        self._check(geos, side=1, tool_radius=TOOL_RADIUS,
                    workpiece_radius=WORKPIECE_RADIUS,
                    common_length=COMMON_LENGTH)

    def test_the_g40_approach_line_is_offset_g42(self):
        shape, layer, geos = self._shape_with(cut_cor=42)
        self.assertEqual(len(geos), 3)
        self._check(geos, side=-1, tool_radius=TOOL_RADIUS,
                    workpiece_radius=WORKPIECE_RADIUS,
                    common_length=COMMON_LENGTH)

    def test_the_offset_scales_with_the_tool_radius(self):
        tool_radius = 2.0
        shape, layer, geos = self._shape_with(cut_cor=41,
                                              tool_diameter=tool_radius * 2.0)
        self._check(geos, side=1, tool_radius=tool_radius,
                    workpiece_radius=WORKPIECE_RADIUS,
                    common_length=COMMON_LENGTH)

    def test_the_geometry_scales_with_the_lead_radius(self):
        radius = 30.0
        shape, layer, geos = self._shape_with(cut_cor=41, radius=radius)
        self._check(geos, side=1, tool_radius=TOOL_RADIUS,
                    workpiece_radius=radius, common_length=COMMON_LENGTH)

    def test_the_open_contour_uses_the_same_approach(self):
        shape, layer, geos = self._shape_with(cut_cor=41, closed=False)
        self._check(geos, side=1, tool_radius=TOOL_RADIUS,
                    workpiece_radius=WORKPIECE_RADIUS,
                    common_length=COMMON_LENGTH)

    def test_the_startmove_uses_the_same_approach(self):
        shape, layer, geos = self._shape_with(cut_cor=41, mode=LEAD_STARTMOVE)
        self._check(geos, side=1, tool_radius=TOOL_RADIUS,
                    workpiece_radius=WORKPIECE_RADIUS,
                    common_length=COMMON_LENGTH)

    def _export(self, shape, outside):
        """Export with the given cc_outside_the_piece setting."""
        from dxf2gcode_leadmove_golden_test import (Breaks, MyPostProcessor,
                                                    MyPostProConfig,
                                                    _LayerContentsStub)
        postpro = MyPostProcessor()
        postpro.breaks = Breaks(_LayerContentsStub())
        config = MyPostProConfig()
        config.load_config()
        config.vars.General.cc_outside_the_piece = outside
        postpro.vars = config.vars
        postpro.initialize_export_vars()
        return shape.Write_GCode(postpro)

    def _check_gcode_order(self, gcode):
        # The G40 approach line (G1) is cut first, then the tool is plunged
        # (G40), then G41/G42 is switched on, then the nominal line (G1) and
        # the nominal arc (G3) are written.
        commands = [line.split()[0] for line in gcode.splitlines()
                    if line.strip()]
        self.assertEqual(commands[0], "G0")     # rapid to the dive point
        g40_line = commands.index("G1")         # the G40 approach line
        g41 = commands.index("G41")
        g3 = commands.index("G3")               # the nominal arc
        # The G40 approach line is before G41/G42, the nominal arc after it.
        self.assertLess(g40_line, g41)
        self.assertLess(g41, g3)

    def test_the_gcode_order_outside_the_piece(self):
        shape, layer, geos = self._shape_with(cut_cor=41)
        self._check_gcode_order(self._export(shape, outside=True))

    def test_the_gcode_order_inside_the_piece(self):
        shape, layer, geos = self._shape_with(cut_cor=41)
        self._check_gcode_order(self._export(shape, outside=False))


if __name__ == "__main__":
    unittest.main(verbosity=2)
