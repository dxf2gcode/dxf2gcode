# -*- coding: utf-8 -*-
"""
Tests of the four methods of the lead in and of the lead out.

The methods are selected independently for the lead in and for the lead out:

* 'off'       : no geometry at all
* 'straight'  : a straight line of the common length
* 'radius'    : a quarter arc of the common radius. With G41/G42 the arc is
                nominal (the machine offsets it) and with the internal
                compensation it is the tool center path. In both cases the arc
                is preceded by the radial straight line of the common length
                (definition B). G40 keeps the historical tool center radius as
                the straight part.
* 'startmove' : the start move of the program: a straight line (the common
                length) and a quarter arc (the common radius). It is generated
                with G41/G42 and with the internal compensation.

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
from math import pi, sqrt

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [_TEST_DIR, os.path.join(os.path.dirname(_TEST_DIR), "source")]
from toolpath_test_support import serialize_gcode, serialize_shape_geometry

import dxf2gcode.bootstrap.runtime_state as g  # noqa: E402
from dxf2gcode.domain.geometry.arcgeo import ArcGeo  # noqa: E402
from dxf2gcode.domain.toolpath.leadmove import (LEAD_OFF, LEAD_RADIUS,  # noqa: E402
                                     LEAD_STARTMOVE, LEAD_STRAIGHT)
from dxf2gcode.domain.geometry.linegeo import LineGeo  # noqa: E402
from dxf2gcode.domain.geometry.point import Point  # noqa: E402
from dxf2gcode.adapters.config.runtime_config import MyConfig  # noqa: E402
from dxf2gcode.presentation.qt.qt_compat.QtWidgets import QApplication  # noqa: E402

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
        # The nominal straight line of the common length and the nominal
        # quarter arc. There is no separate G40 approach line.
        self.assertEqual(len(geos), 2)
        self.assertIsInstance(geos[0], LineGeo)   # nominal straight line
        self.assertIsInstance(geos[1], ArcGeo)    # nominal arc
        # The nominal arc is programmed in the nominal plane (the machine
        # compensates it): it ends at the contour start and has the radius at
        # the workpiece.
        self.assertAlmostEqual(geos[1].Pe.x, 0.0)
        self.assertAlmostEqual(geos[1].Pe.y, 0.0)
        self.assertAlmostEqual(geos[1].r, WORKPIECE_RADIUS)
        # The nominal line approaches the start of the arc radially (it is
        # tangent to the arc there) and has the common length.
        self.assertAlmostEqual(geos[0].Pe.x, geos[1].Ps.x)
        self.assertAlmostEqual(geos[0].Pe.y, geos[1].Ps.y)
        self.assertAlmostEqual(geos[0].length, COMMON_LENGTH)

    def test_the_straight_part_uses_the_common_length(self):
        # Definition B: the straight part of the start move is the common
        # length (both for the machine and for the software compensation).
        lengths = []
        for common_length in (2.0, 50.0):
            shape, layer = self.shape_with(LEAD_STARTMOVE,
                                           length=common_length)
            geos = list(shape.stmove.lead_in_geos)
            lengths.append(geos[0].length)
        self.assertAlmostEqual(lengths[0], 2.0)
        self.assertAlmostEqual(lengths[1], 50.0)

    def test_startmove_is_a_straight_line_and_an_arc(self):
        shape, layer = self.shape_with(LEAD_STARTMOVE, length=7.5)
        geos = list(shape.stmove.lead_in_geos)
        self.assertEqual(len(geos), 2)
        self.assertIsInstance(geos[0], LineGeo)   # nominal line
        self.assertIsInstance(geos[1], ArcGeo)    # nominal arc
        self.assertAlmostEqual(geos[0].length, 7.5)
        # The arc is nominal (the lead in is programmed in the nominal plane,
        # the machine offsets it by the tool radius).
        self.assertAlmostEqual(geos[1].r, WORKPIECE_RADIUS)

    def test_the_startmove_uses_the_common_length(self):
        # The straight line of the start move is longer if the common length
        # is bigger.
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
        # Definition B: the straight part is the common length.
        self.assertAlmostEqual(geos[0].length, COMMON_LENGTH)
        # The tool center arc has the tool center radius (R_w - r_tool).
        self.assertAlmostEqual(geos[1].r, WORKPIECE_RADIUS - TOOL_RADIUS)

    def test_the_radius_lead_in_exists_with_the_internal_compensation(self):
        shape, layer = self.shape_with(LEAD_RADIUS, done_by_machine=False)
        geos = list(shape.stmove.lead_in_geos)
        self.assertEqual(len(geos), 2)
        self.assertIsInstance(geos[0], LineGeo)
        self.assertIsInstance(geos[1], ArcGeo)
        self.assertAlmostEqual(geos[0].length, COMMON_LENGTH)
        self.assertAlmostEqual(geos[1].r, WORKPIECE_RADIUS - TOOL_RADIUS)


class TestLeadLengthInvariants(LeadInModeTestBase):
    """Definition B: `lead_length` is the straight part of the lead in.

    It applies to the radius / start move lead in for the software
    compensation and for the machine compensation G41/G42. G40 keeps the
    historical tool center radius, so that its path does not change.
    """

    def _lead_in(self, shape):
        geos = list(shape.stmove.lead_in_geos)
        self.assertEqual(len(geos), 2)
        self.assertIsInstance(geos[0], LineGeo)
        self.assertIsInstance(geos[1], ArcGeo)
        return geos[0], geos[1]

    def test_software_uses_the_configured_length(self):
        # L = 5 differs clearly from R_m = R_w - r = 15: the previous
        # behaviour used R_m for the software compensation.
        shape, layer = self.shape_with(LEAD_STARTMOVE, length=COMMON_LENGTH,
                                       done_by_machine=False)
        line, arc = self._lead_in(shape)
        self.assertAlmostEqual(line.length, COMMON_LENGTH)
        self.assertAlmostEqual(arc.r, WORKPIECE_RADIUS - TOOL_RADIUS)
        self.assertAlmostEqual(
            abs(arc.ext) * arc.r,
            (pi / 2.0) * (WORKPIECE_RADIUS - TOOL_RADIUS))

    def test_machine_g41_uses_the_configured_length(self):
        shape, layer = self.shape_with(LEAD_STARTMOVE, length=COMMON_LENGTH)
        line, arc = self._lead_in(shape)
        self.assertAlmostEqual(line.length, COMMON_LENGTH)
        self.assertAlmostEqual(arc.r, WORKPIECE_RADIUS)
        self.assertAlmostEqual(abs(arc.ext) * arc.r,
                               (pi / 2.0) * WORKPIECE_RADIUS)

    def test_machine_g42_uses_the_configured_length(self):
        shape, layer = build_shape(
            closed=True, cut_cor=42,
            layer_settings=dict(lead_in_mode=LEAD_STARTMOVE,
                                lead_out_mode=LEAD_OFF,
                                lead_radius=WORKPIECE_RADIUS,
                                lead_length=COMMON_LENGTH))
        line, arc = self._lead_in(shape)
        self.assertAlmostEqual(line.length, COMMON_LENGTH)
        self.assertAlmostEqual(arc.r, WORKPIECE_RADIUS)

    def test_radius_and_startmove_are_equal(self):
        for mode in (LEAD_RADIUS, LEAD_STARTMOVE):
            for machine in (True, False):
                shape, layer = self.shape_with(mode, length=COMMON_LENGTH,
                                               done_by_machine=machine)
                line, arc = self._lead_in(shape)
                self.assertAlmostEqual(line.length, COMMON_LENGTH,
                                       msg=str((mode, machine)))
                self.assertAlmostEqual(
                    arc.r,
                    WORKPIECE_RADIUS if machine
                    else WORKPIECE_RADIUS - TOOL_RADIUS,
                    msg=str((mode, machine)))

    def test_the_tool_center_paths_match(self):
        sw_shape, _ = self.shape_with(LEAD_STARTMOVE, length=COMMON_LENGTH,
                                      done_by_machine=False)
        mc_shape, _ = self.shape_with(LEAD_STARTMOVE, length=COMMON_LENGTH)
        sw_line, sw_arc = self._lead_in(sw_shape)
        mc_line, mc_arc = self._lead_in(mc_shape)
        self.assertAlmostEqual(sw_line.length, mc_line.length)
        self.assertAlmostEqual(sw_arc.r, mc_arc.r - TOOL_RADIUS)
        self.assertAlmostEqual(abs(sw_arc.ext) * sw_arc.r,
                               abs(mc_arc.ext) * (mc_arc.r - TOOL_RADIUS))

    def test_the_special_case_length_equals_the_tool_center_radius(self):
        # L == R_m: the historical and the new definition agree.
        shape, layer = self.shape_with(
            LEAD_STARTMOVE, length=WORKPIECE_RADIUS - TOOL_RADIUS,
            done_by_machine=False)
        line, arc = self._lead_in(shape)
        self.assertAlmostEqual(line.length,
                               WORKPIECE_RADIUS - TOOL_RADIUS)

    def test_open_and_closed_contours_use_the_same_length(self):
        for closed in (True, False):
            shape, layer = build_shape(
                closed=closed, cut_cor=41,
                layer_settings=dict(lead_in_mode=LEAD_STARTMOVE,
                                    lead_out_mode=LEAD_OFF,
                                    lead_radius=WORKPIECE_RADIUS,
                                    lead_length=COMMON_LENGTH))
            line, arc = self._lead_in(shape)
            self.assertAlmostEqual(line.length, COMMON_LENGTH)

    def test_straight_is_unchanged(self):
        for machine in (True, False):
            shape, layer = self.shape_with(LEAD_STRAIGHT, length=7.5,
                                           done_by_machine=machine)
            geos = list(shape.stmove.lead_in_geos)
            self.assertEqual(len(geos), 1)
            self.assertIsInstance(geos[0], LineGeo)
            self.assertAlmostEqual(geos[0].length, 7.5)

    def test_g40_keeps_the_historical_tool_center_radius(self):
        # G40 has no cutter compensation: its path is not changed by
        # definition B.
        shape, layer = build_shape(
            closed=True, cut_cor=40,
            layer_settings=dict(lead_in_mode=LEAD_STARTMOVE,
                                lead_out_mode=LEAD_OFF,
                                lead_radius=WORKPIECE_RADIUS,
                                lead_length=TOOL_RADIUS))
        line, arc = self._lead_in(shape)
        self.assertAlmostEqual(line.length, WORKPIECE_RADIUS - TOOL_RADIUS)
        self.assertAlmostEqual(arc.r, WORKPIECE_RADIUS - TOOL_RADIUS)

    def test_the_compensated_radius_lead_in_without_length_is_an_error(self):
        # Definition B needs a positive length for the compensated radius
        # lead in: the shape is not milled and the error is reported.
        for machine in (True, False):
            shape, layer = self.shape_with(LEAD_RADIUS, length=0.0,
                                           done_by_machine=machine)
            self.assertTrue(shape.stmove.start_move_error,
                            "machine=%s" % machine)
            self.assertEqual(list(shape.stmove.lead_in_geos), [])

    def test_the_g40_radius_lead_in_without_length_still_works(self):
        # G40 does not use the length for the radius lead in (it uses the
        # historical tool center radius), so a zero length must not break it.
        shape, layer = build_shape(
            closed=True, cut_cor=40,
            layer_settings=dict(lead_in_mode=LEAD_RADIUS,
                                lead_out_mode=LEAD_OFF,
                                lead_radius=WORKPIECE_RADIUS,
                                lead_length=0.0))
        line, arc = self._lead_in(shape)
        self.assertAlmostEqual(line.length, WORKPIECE_RADIUS - TOOL_RADIUS)
        self.assertAlmostEqual(arc.r, WORKPIECE_RADIUS - TOOL_RADIUS)
        self.assertEqual(getattr(shape.stmove, 'start_move_error', ''), "")


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
        # The rapid to the compensated start point, the nominal line (G1) and
        # the nominal arc (G3). There is no separate G40 approach line.
        self.assertEqual(blocks[0], "G0")
        self.assertEqual(blocks[1], "G1")
        self.assertEqual(blocks[2], "G3")
        # G41/G42 is activated before the nominal line and the nominal arc.
        g41 = gcode.index("G41")
        self.assertLess(g41, gcode.index("G3"))
        self.assertGreater(g41, gcode.index("G0"))

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
        # The rapid to the compensated start point, the nominal line (G1) and
        # the nominal arc (G3). There is no separate G40 approach line.
        self.assertEqual(blocks[0], "G0")
        self.assertEqual(blocks[1], "G1")
        self.assertEqual(blocks[2], "G3")

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
        from dxf2gcode.domain.toolpath.stmove import StMove
        for mode, expected in ((LEAD_OFF, 0), (LEAD_STRAIGHT, 1),
                               (LEAD_RADIUS, 2), (LEAD_STARTMOVE, 2)):
            shape, layer = self.shape_with(mode)
            self.assertEqual(len(shape.stmove.lead_in_geos), expected, mode)
            # The layer holds the selected method and the toolpath is built
            # from it.
            self.assertEqual(layer.get_lead_in_mode(), mode)
            shape.stmove = StMove(shape)
            self.assertEqual(len(shape.stmove.lead_in_geos), expected, mode)


class TestMachineCompCircleLeadIn(LeadInModeTestBase):
    """The circle / start move lead in of the machine cutter compensation.

    The lead in is programmed in the nominal plane: a straight line of the
    common length and a quarter arc of the radius at the workpiece. The
    machine is positioned directly at the compensated start of the nominal
    line (no separate G40 approach line); G41/G42 is activated after the
    plunge and the machine offsets the nominal path.
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

    def _check(self, shape, geos, side, tool_radius, workpiece_radius,
               common_length):
        self.assertEqual(len(geos), 2)
        nominal_line, arc = geos
        self.assertIsInstance(nominal_line, LineGeo)
        self.assertIsInstance(arc, ArcGeo)
        # The nominal line ends at the start of the nominal arc.
        self.assertAlmostEqual(nominal_line.Pe.x, arc.Ps.x)
        self.assertAlmostEqual(nominal_line.Pe.y, arc.Ps.y)
        # The nominal arc ends at the contour start and has the nominal radius.
        self.assertAlmostEqual(arc.Pe.x, 0.0)
        self.assertAlmostEqual(arc.Pe.y, 0.0)
        self.assertAlmostEqual(arc.r, workpiece_radius)
        # Definition B: the nominal line has the common length.
        self.assertAlmostEqual(nominal_line.length, common_length)
        # The rapid start is the compensated start of the nominal line: it is
        # offset by the tool radius to the side the machine compensates to
        # (left for G41, right for G42). There is no separate G40 line.
        rapid = shape.stmove.geos[0]
        dx = nominal_line.Pe.x - nominal_line.Ps.x
        dy = nominal_line.Pe.y - nominal_line.Ps.y
        norm = sqrt(dx * dx + dy * dy)
        vx = rapid.x - nominal_line.Ps.x
        vy = rapid.y - nominal_line.Ps.y
        signed = vx * (-dy / norm) + vy * (dx / norm)
        self.assertAlmostEqual(abs(signed), tool_radius)
        self.assertAlmostEqual(signed, side * tool_radius)
        # The rapid start is beside the nominal start (no offset along the
        # travel direction): the machine takes over without a lateral jump.
        self.assertAlmostEqual(vx * (dx / norm) + vy * (dy / norm), 0.0)

    def test_the_compensated_start_is_offset_g41(self):
        shape, layer, geos = self._shape_with(cut_cor=41)
        self._check(shape, geos, side=1, tool_radius=TOOL_RADIUS,
                    workpiece_radius=WORKPIECE_RADIUS,
                    common_length=COMMON_LENGTH)

    def test_the_compensated_start_is_offset_g42(self):
        shape, layer, geos = self._shape_with(cut_cor=42)
        self._check(shape, geos, side=-1, tool_radius=TOOL_RADIUS,
                    workpiece_radius=WORKPIECE_RADIUS,
                    common_length=COMMON_LENGTH)

    def test_the_offset_scales_with_the_tool_radius(self):
        tool_radius = 2.0
        shape, layer, geos = self._shape_with(cut_cor=41,
                                              tool_diameter=tool_radius * 2.0)
        self._check(shape, geos, side=1, tool_radius=tool_radius,
                    workpiece_radius=WORKPIECE_RADIUS,
                    common_length=COMMON_LENGTH)

    def test_the_geometry_scales_with_the_lead_radius(self):
        radius = 30.0
        shape, layer, geos = self._shape_with(cut_cor=41, radius=radius)
        self._check(shape, geos, side=1, tool_radius=TOOL_RADIUS,
                    workpiece_radius=radius, common_length=COMMON_LENGTH)

    def test_the_open_contour_uses_the_same_approach(self):
        shape, layer, geos = self._shape_with(cut_cor=41, closed=False)
        self._check(shape, geos, side=1, tool_radius=TOOL_RADIUS,
                    workpiece_radius=WORKPIECE_RADIUS,
                    common_length=COMMON_LENGTH)

    def test_the_startmove_uses_the_same_approach(self):
        shape, layer, geos = self._shape_with(cut_cor=41, mode=LEAD_STARTMOVE)
        self._check(shape, geos, side=1, tool_radius=TOOL_RADIUS,
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
        return serialize_gcode(shape, postpro)

    def _check_gcode_order(self, gcode):
        # The rapid, the plunge (G40), G41/G42 and then the nominal line and
        # the nominal arc. There is no linear G40 approach move in the XY plane
        # before the compensation is activated.
        lines = [line for line in gcode.splitlines() if line.strip()]
        commands = [line.split()[0] for line in lines]
        self.assertEqual(commands[0], "G0")     # rapid to the compensated start
        g41 = commands.index("G41")
        g3 = commands.index("G3")               # the nominal arc
        for line in lines[:g41]:
            fields = line.split()
            self.assertFalse(fields[0] == "G1" and "X" in fields and
                             "Y" in fields, line)
        # The nominal line is written after G41/G42 and before the arc.
        nominal_line = commands.index("G1", g41)
        self.assertLess(g41, nominal_line)
        self.assertLess(nominal_line, g3)

    def test_the_gcode_order_outside_the_piece(self):
        shape, layer, geos = self._shape_with(cut_cor=41)
        self._check_gcode_order(self._export(shape, outside=True))

    def test_the_gcode_order_inside_the_piece(self):
        shape, layer, geos = self._shape_with(cut_cor=41)
        self._check_gcode_order(self._export(shape, outside=False))


if __name__ == "__main__":
    unittest.main(verbosity=2)
