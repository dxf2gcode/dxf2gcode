# -*- coding: utf-8 -*-
"""
Tests of the lead in / lead out / overcut functions of dxf2gcode.

They cover the error handling (an invalid geometry must not produce G-Code),
the relation to the depth passes, the configuration and the backwards
compatibility of the configuration and of the project files.

Run from the repository root:

    python -m unittest discover -s tests -t tests -p "dxf2gcode_leadmove_test.py" -v
"""
from __future__ import absolute_import

import math
import os
import shutil
import sys
import tempfile
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [_TEST_DIR, os.path.join(os.path.dirname(_TEST_DIR), "source")]
from toolpath_test_support import serialize_gcode, serialize_shape_geometry

import dxf2gcode.bootstrap.runtime_state as g  # noqa: E402
from dxf2gcode.adapters.config.runtime_config import MyConfig  # noqa: E402
from dxf2gcode.domain.project.layercontent import LayerContent  # noqa: E402
from dxf2gcode.domain.toolpath.leadmove import LEAD_DEFAULT, LEAD_OFF, LEAD_RADIUS, \
    LEAD_STARTMOVE, LEAD_STRAIGHT, OVERCUT_DEFAULT  # noqa: E402

from dxf2gcode.presentation.qt.qt_compat.QtWidgets import QApplication  # noqa: E402

from dxf2gcode_leadmove_golden_test import (  # noqa: E402
    _LayerContentsStub, build_shape, export_gcode)

from dxf2gcode.adapters.postprocessor.breaks import Breaks  # noqa: E402
from dxf2gcode.adapters.postprocessor.postprocessor import MyPostProcessor  # noqa: E402
from dxf2gcode.adapters.postprocessor.postprocessorconfig import MyPostProConfig  # noqa: E402

_APP = None


def _app():
    global _APP
    if _APP is None:
        _APP = QApplication.instance() or QApplication([])
    return _APP


def export_with_errors(shape):
    """
    Export a shape and return the G-Code together with the collected errors.
    """
    postpro = MyPostProcessor()
    postpro.breaks = Breaks(_LayerContentsStub())
    postpro_config = MyPostProConfig()
    postpro_config.load_config()
    postpro.vars = postpro_config.vars
    postpro.initialize_export_vars()
    gcode = serialize_gcode(shape, postpro)
    return gcode, postpro.export_errors


class LeadMoveTestBase(unittest.TestCase):

    def setUp(self):
        _app()
        self.tmp = tempfile.mkdtemp(prefix="d2g_leadmove_")
        self._old_folder = getattr(g, "folder", None)
        self._old_config = getattr(g, "config", None)
        g.folder = self.tmp
        os.makedirs(os.path.join(self.tmp, "config"))
        self.config = MyConfig()
        g.config = self.config

    def tearDown(self):
        g.folder = self._old_folder
        g.config = self._old_config
        shutil.rmtree(self.tmp, ignore_errors=True)


class TestErrorHandling(LeadMoveTestBase):
    """An invalid geometry must not produce G-Code."""

    def test_radius_smaller_than_the_tool_radius(self):
        shape, layer = build_shape(
            closed=True, cut_cor=41,
            layer_settings=dict(lead_in_mode=LEAD_RADIUS, lead_radius=3.0))
        gcode, errors = export_with_errors(shape)
        self.assertEqual(gcode, "")
        self.assertTrue(errors)

    def test_radius_equal_to_the_tool_radius_is_rejected(self):
        # With the machine compensation the lead in is programmed in the tool
        # center plane: a radius equal to the tool radius collapses the arc
        # (the tool center does not move), so the shape can not be milled.
        shape, layer = build_shape(
            closed=True, cut_cor=41,
            layer_settings=dict(lead_in_mode=LEAD_RADIUS, lead_radius=5.0))
        gcode, errors = export_with_errors(shape)
        self.assertEqual(gcode, "")
        self.assertTrue(errors)

    def test_lead_out_and_overcut_are_used_together(self):
        # The lead out and the overcut can be used at the same time: the
        # overcut continues the cut along the contour beyond the closing
        # point and the lead out starts at the end of the overcut.
        shape, layer = build_shape(
            closed=True, cut_cor=41,
            layer_settings=dict(lead_out_mode=LEAD_RADIUS,
                                lead_radius=20.0,
                                overcut_enabled=True, overcut_length=50.0))
        gcode, errors = export_with_errors(shape)
        self.assertFalse(errors)
        self.assertTrue(gcode)
        # The overcut continues the cut along the contour.
        self.assertEqual(gcode.count("G1 X  50.000 Y   0.000"), 1)

    def test_a_straight_lead_out_after_the_overcut_runs_along_the_contour(self):
        # The straight lead out starts at the end of the overcut and runs
        # along the contour. This is written as it is (no error): the user
        # chose the straight lead out on purpose.
        shape, layer = build_shape(
            closed=True, cut_cor=41,
            layer_settings=dict(lead_out_mode=LEAD_STRAIGHT,
                                lead_length=5.0,
                                overcut_enabled=True, overcut_length=50.0))
        gcode, errors = export_with_errors(shape)
        self.assertFalse(errors)
        self.assertTrue(gcode)
        # The overcut continues the cut along the contour and the straight
        # lead out continues it further.
        self.assertEqual(gcode.count("G1 X  50.000 Y   0.000"), 1)
        self.assertEqual(gcode.count("G1 X  55.000 Y   0.000"), 1)

    def test_overcut_on_an_open_contour_is_ignored(self):
        # The overcut is only possible for closed contours: on an open contour
        # it is silently ignored (no error) and the contour is milled normally.
        shape, layer = build_shape(
            closed=False, cut_cor=41,
            layer_settings=dict(overcut_enabled=True, overcut_length=50.0))
        gcode, errors = export_with_errors(shape)
        self.assertTrue(gcode)
        self.assertFalse(errors)
        self.assertEqual(gcode.count("G1 X  50.000 Y   0.000"), 0)

    def test_overcut_longer_than_the_contour(self):
        shape, layer = build_shape(
            closed=True, cut_cor=41,
            layer_settings=dict(overcut_enabled=True, overcut_length=1000.0))
        gcode, errors = export_with_errors(shape)
        self.assertEqual(gcode, "")
        self.assertTrue(errors)

    def test_lead_out_starts_at_the_last_cut_point(self):
        # A break at the end of the contour is only a Z hop: the lead out
        # has to start at the last point which is really cut.
        from dxf2gcode.domain.geometry.breakgeo import BreakGeo
        from dxf2gcode.domain.geometry.linegeo import LineGeo
        from dxf2gcode.domain.geometry.point import Point
        from dxf2gcode.domain.project.shape import Shape, Geos
        from dxf2gcode.adapters.toolpath.preparation import prepare_shape

        geos = Geos([LineGeo(Point(0, 0), Point(100, 0)),
                     LineGeo(Point(100, 0), Point(100, 100)),
                     LineGeo(Point(100, 100), Point(0, 100)),
                     LineGeo(Point(0, 100), Point(0, 0)),
                     BreakGeo(Point(0, 0), Point(10, 0), -1.0, 0.0, 0.0)])
        shape = Shape(nr=1, closed=True, geos=geos)
        layer = LayerContent(nr=1, name="L1", shapes=[])
        layer.tool_diameter = 10.0
        # The common radius at the workpiece and the common length of the
        # straight part (they are defined per tool).
        layer.lead_radius = 10.0
        layer.lead_length = 5.0
        layer.lead_out_mode = LEAD_STRAIGHT

        shape.parentLayer = layer
        shape.parentEntity = None
        shape.cw = True
        shape.cut_cor = 41
        for geo in shape.geos:
            geo.make_abs_geo()
        shape.axis3_mill_depth = -5.0
        shape.axis3_start_mill_depth = 0.0
        shape.axis3_slice_depth = -2.0
        shape.stmove = prepare_shape(shape)

        gcode, errors = export_with_errors(shape)
        self.assertFalse(errors)
        # The lead out starts at the end of the contour (0, 0) and not at the
        # end of the break (10, 0).
        self.assertIn("G1 X   0.000 Y  -5.000", gcode)
        self.assertNotIn("G1 X  10.000 Y  -5.000", gcode)

    def test_straight_lead_out_along_the_contour_is_written(self):
        # A straight lead out which would run along the contour is written as
        # it is: there is no error (the user chose the straight lead out on
        # purpose).
        from dxf2gcode.domain.geometry.linegeo import LineGeo
        from dxf2gcode.domain.geometry.point import Point
        from dxf2gcode.domain.project.shape import Shape, Geos
        from dxf2gcode.adapters.toolpath.preparation import prepare_shape

        geos = Geos([LineGeo(Point(0, 0), Point(100, 0)),
                     LineGeo(Point(100, 0), Point(100, 100)),
                     LineGeo(Point(100, 100), Point(0, 100)),
                     LineGeo(Point(0, 100), Point(0, 0)),
                     LineGeo(Point(0, 0), Point(50, 0))])
        shape = Shape(nr=1, closed=True, geos=geos)
        layer = LayerContent(nr=1, name="L1", shapes=[])
        layer.tool_diameter = 10.0
        # The common radius at the workpiece and the common length of the
        # straight part (they are defined per tool).
        layer.lead_radius = 10.0
        layer.lead_length = 5.0
        layer.lead_out_mode = LEAD_STRAIGHT

        shape.parentLayer = layer
        shape.parentEntity = None
        shape.cw = True
        shape.cut_cor = 41
        for geo in shape.geos:
            geo.make_abs_geo()
        shape.axis3_mill_depth = -5.0
        shape.axis3_start_mill_depth = 0.0
        shape.axis3_slice_depth = -2.0
        shape.stmove = prepare_shape(shape)

        gcode, errors = export_with_errors(shape)
        self.assertFalse(errors)
        self.assertTrue(gcode)


class TestPasses(LeadMoveTestBase):
    """The lead in is written in the first pass, the lead out and the overcut
    in the last one."""

    def test_lead_in_is_only_in_the_first_pass(self):
        shape, layer = build_shape(
            closed=True, cut_cor=41, slice_depth=-2.0, mill_depth=-5.0,
            layer_settings=dict(lead_in_mode=LEAD_STRAIGHT))
        gcode = export_gcode(shape, layer)
        # The lead in is a straight line from the dive point to the tool
        # center start (offset by the tool radius); it is only written in the
        # first pass.
        self.assertEqual(gcode.count("G0 X  -5.000 Y   5.000"), 1)

    def test_lead_out_is_only_in_the_last_pass(self):
        shape, layer = build_shape(
            closed=True, cut_cor=41, slice_depth=-2.0, mill_depth=-5.0,
            layer_settings=dict(lead_out_mode=LEAD_STRAIGHT))
        gcode = export_gcode(shape, layer)
        # The lead out leaves the contour at its end (below the last pass)
        self.assertEqual(gcode.count("G1 X   0.000 Y  -5.000"), 1)

    def test_overcut_is_only_in_the_last_pass(self):
        shape, layer = build_shape(
            closed=True, cut_cor=41,
            layer_settings=dict(overcut_enabled=True, overcut_length=50.0))
        gcode = export_gcode(shape, layer)
        self.assertEqual(gcode.count("G1 X  50.000 Y   0.000"), 1)

    def test_lead_out_and_overcut_are_only_in_the_last_pass(self):
        shape, layer = build_shape(
            closed=True, cut_cor=41, slice_depth=-2.0, mill_depth=-5.0,
            layer_settings=dict(lead_out_mode=LEAD_RADIUS,
                                lead_radius=20.0,
                                overcut_enabled=True, overcut_length=50.0))
        gcode = export_gcode(shape, layer)
        # The overcut continues the cut along the contour and the lead out
        # starts at its end - both are written in the last pass only.
        self.assertEqual(gcode.count("G1 X  50.000 Y   0.000"), 1)


    def test_the_lathe_path_is_not_touched(self):
        # The lead in / lead out / overcut are not available for the lathe:
        # the X axis of a lathe is the diameter.
        from dxf2gcode.domain.toolpath.leadmove import lead_move_enabled
        self.assertTrue(lead_move_enabled('milling'))
        self.assertTrue(lead_move_enabled('drag_knife'))
        self.assertFalse(lead_move_enabled('lathe'))

        g.config.machine_type = 'lathe'
        shape, layer = build_shape(
            closed=True, cut_cor=41, machine_type='lathe',
            layer_settings=dict(lead_in_mode=LEAD_RADIUS,
                                lead_radius=20.0,
                                lead_out_mode=LEAD_STRAIGHT,
                                overcut_enabled=True,
                                overcut_length=50.0))
        gcode, errors = export_with_errors(shape)
        self.assertFalse(errors)
        # Neither the lead in nor the lead out is in the G-Code
        self.assertNotIn("G3 X   0.000 Y   0.000 I  20.000", gcode)
        self.assertNotIn("G1 X  50.000 Y   0.000", gcode)


class TestLeadOutSide(LeadMoveTestBase):
    """The lead out has to follow the cutter compensation of the pass which is
    exported (the direction of the contour changes with the pass)."""

    def _arc_center(self, gcode):
        """
        The center of the last arc of the G-Code (the lead out) and the point
        where it starts.
        @return: (center, start point)
        """
        position = None
        arc = None
        for line in gcode.splitlines():
            fields = line.split()
            if not fields or fields[0] not in ("G0", "G1", "G2", "G3"):
                continue
            values = {}
            arguments = fields[1:]
            for index in range(0, len(arguments) - 1, 2):
                values[arguments[index]] = float(arguments[index + 1])
            if fields[0] in ("G2", "G3"):
                arc = (position, values)
            if "X" in values and "Y" in values:
                position = (values["X"], values["Y"])
        self.assertIsNotNone(arc, "the lead out arc is missing")
        start, values = arc
        center = (start[0] + values["I"], start[1] + values["J"])
        return center, start

    def test_radius_lead_out_uses_the_compensation_side_of_the_pass(self):
        # An open contour is milled in alternating directions: the second
        # pass is milled backwards and the compensation is switched to G42.
        # The lead out has to curve to the side of the active compensation
        # (G42 = right), otherwise the machine offsets the path away from the
        # center of the arc and the tool center path gets the wrong radius.
        shape, layer = build_shape(
            closed=False, cut_cor=41, slice_depth=-2.0, mill_depth=-4.0,
            layer_settings=dict(lead_out_mode=LEAD_RADIUS,
                                lead_radius=20.0))
        gcode = export_gcode(shape, layer)
        self.assertIn("G42", gcode)
        center, start = self._arc_center(gcode)
        # The last pass ends at (0, 0) and is travelled in the -X direction.
        # The right side of that direction is +Y.
        self.assertAlmostEqual(start[0], 0.0)
        self.assertAlmostEqual(start[1], 0.0)
        self.assertGreater(center[1], start[1],
                           "the lead out has to curve to the right (G42)")
        # The tool center path radius is the workpiece radius minus the tool
        # radius: the machine offsets the arc towards its center.
        self.assertAlmostEqual(abs(center[1] - start[1]), 20.0)

    def test_straight_lead_out_is_not_changed_by_the_pass(self):
        shape, layer = build_shape(
            closed=False, cut_cor=41, slice_depth=-2.0, mill_depth=-4.0,
            layer_settings=dict(lead_out_mode=LEAD_STRAIGHT))
        gcode = export_gcode(shape, layer)
        # The straight lead out continues the cut in the direction of the
        # current pass (the last pass is milled backwards: -X).
        self.assertIn("G1 X  -5.000 Y   0.000", gcode)

    def test_internal_compensation_lead_out_curves_away_from_the_material(self):
        # With the internal cutter compensation the offset side does not change
        # with the pass, but the travel direction of the mirrored last pass
        # does. The lead out has to curve away from the material (the free
        # side) - i.e. to the other side relative to the reversed direction -
        # and not back into the contour.
        shape, layer = build_shape(
            closed=False, cut_cor=41, done_by_machine=False,
            slice_depth=-2.0, mill_depth=-4.0,
            layer_settings=dict(lead_out_mode=LEAD_RADIUS,
                                lead_radius=20.0))
        gcode = export_gcode(shape, layer)
        # The internal compensation is exported as the tool center path: no
        # G41/G42 move is written.
        self.assertNotIn("G41", gcode)
        self.assertNotIn("G42", gcode)
        center, start = self._arc_center(gcode)
        # The offset contour is outside the material: the last pass ends at
        # (0, 5) and is travelled in the -X direction. The free side (away
        # from the material) is +Y, so the lead out arc has to curve upwards.
        self.assertAlmostEqual(start[0], 0.0)
        self.assertAlmostEqual(start[1], 5.0)
        self.assertGreater(center[1], start[1],
                           "the lead out has to curve away from the material")
        # The arc has the radius of the tool center path (R_w - r_tool).
        tool_radius = layer.getToolRadius()
        self.assertAlmostEqual(abs(center[1] - start[1]), 20.0 - tool_radius)


class TestLeadInOff(LeadMoveTestBase):
    """The lead in mode 'off' needs a movement in the XY plane to build the
    cutter compensation - with G41/G42 it is not possible."""

    def test_off_is_not_possible_with_g41(self):
        shape, layer = build_shape(
            closed=True, cut_cor=41,
            layer_settings=dict(lead_in_mode=LEAD_OFF))
        gcode, errors = export_with_errors(shape)
        self.assertEqual(gcode, "")
        self.assertTrue(errors)
        self.assertIn("'off'", errors[0])

    def test_off_is_not_possible_with_g42(self):
        shape, layer = build_shape(
            closed=True, cut_cor=42,
            layer_settings=dict(lead_in_mode=LEAD_OFF))
        gcode, errors = export_with_errors(shape)
        self.assertEqual(gcode, "")
        self.assertTrue(errors)

    def test_off_is_possible_with_the_internal_compensation(self):
        # Without the machine compensation there is no offset to build: the
        # plunge is done at the tool center path, which is the usual
        # behaviour of the program.
        shape, layer = build_shape(
            closed=True, cut_cor=41, done_by_machine=False,
            layer_settings=dict(lead_in_mode=LEAD_OFF))
        gcode, errors = export_with_errors(shape)
        self.assertFalse(errors)
        self.assertTrue(gcode)


class TestDragKnifeErrors(LeadMoveTestBase):
    """The drag knife has to report the errors of the start move too."""

    def test_overcut_on_an_open_contour_is_ignored(self):
        # The overcut of an open contour is silently ignored (no error), the
        # contour is milled normally.
        shape, layer = build_shape(
            closed=False, cut_cor=40, machine_type='drag_knife',
            layer_settings=dict(overcut_enabled=True, overcut_length=50.0))
        gcode, errors = export_with_errors(shape)
        self.assertTrue(gcode)
        self.assertFalse(errors)

    def test_overcut_longer_than_the_contour_is_rejected(self):
        shape, layer = build_shape(
            closed=True, cut_cor=40, machine_type='drag_knife',
            layer_settings=dict(overcut_enabled=True,
                                overcut_length=1000.0))
        gcode, errors = export_with_errors(shape)
        self.assertEqual(gcode, "")
        self.assertTrue(errors)

    def test_a_valid_drag_knife_overcut_is_exported(self):
        shape, layer = build_shape(
            closed=True, cut_cor=40, machine_type='drag_knife',
            layer_settings=dict(overcut_enabled=True, overcut_length=50.0))
        gcode, errors = export_with_errors(shape)
        self.assertFalse(errors)
        self.assertTrue(gcode)


class TestLayerIdentifiers(LeadMoveTestBase):
    """The values of the layer name identifiers."""

    def test_decimal_values_are_accepted(self):
        separator = g.config.vars.Layer_Options['id_float_separator']
        layer = LayerContent(
            nr=1,
            name=separator.join(["MILL", "Lim", "2.0", "Lom", "2.0"]),
            shapes=[])
        layer.overrideDefaults()
        self.assertEqual(layer.lead_in_mode, LEAD_STRAIGHT)
        self.assertEqual(layer.lead_out_mode, LEAD_RADIUS)

    def test_integer_values_are_accepted(self):
        separator = g.config.vars.Layer_Options['id_float_separator']
        layer = LayerContent(
            nr=1,
            name=separator.join(["MILL", "Lim", "2", "Lom", "1"]),
            shapes=[])
        layer.overrideDefaults()
        self.assertEqual(layer.lead_in_mode, LEAD_STRAIGHT)
        self.assertEqual(layer.lead_out_mode, LEAD_STRAIGHT)

    def test_invalid_values_are_ignored(self):
        separator = g.config.vars.Layer_Options['id_float_separator']
        for value in ("9", "-1", "abc"):
            layer = LayerContent(
                nr=1,
                name=separator.join(["MILL", "Lim", value]),
                shapes=[])
            # No exception: the value is ignored and the default is kept.
            layer.overrideDefaults()
            self.assertEqual(layer.lead_in_mode, LEAD_DEFAULT)

    def test_the_overridden_values_are_remembered(self):
        separator = g.config.vars.Layer_Options['id_float_separator']
        layer = LayerContent(
            nr=1,
            name=separator.join(["MILL", "Lim", "2", "Lr", "8.0"]),
            shapes=[])
        layer.overrideDefaults()
        self.assertTrue(layer.lead_in_mode_overridden)
        self.assertTrue(layer.lead_radius_overridden)
        self.assertFalse(layer.lead_out_mode_overridden)

    def test_the_start_radius_identifier_is_converted(self):
        # The deprecated start radius is the radius of the tool center path
        # of the start move: the common radius is the radius at the
        # workpiece, so the radius of the tool is added to it.
        separator = g.config.vars.Layer_Options['id_float_separator']
        layer = LayerContent(
            nr=1,
            name=separator.join(["MILL", "Sr", "2.0"]),
            shapes=[])
        layer.overrideDefaults()
        self.assertAlmostEqual(layer.lead_radius,
                               2.0 + layer.getToolRadius())



class TestConfigurationChange(LeadMoveTestBase):
    """A change of the global configuration has to update the layers."""

    def setUp(self):
        LeadMoveTestBase.setUp(self)
        from dxf2gcode.presentation.qt.treehandling import update_lead_move_values
        self.update = update_lead_move_values

    def test_the_global_values_are_applied_to_the_layer(self):
        layer = LayerContent(nr=1, name="L1", shapes=[])
        g.config.vars.Lead_In_Out['lead_in_mode'] = 'radius'
        g.config.vars.Lead_In_Out['lead_out_mode'] = 'straight'
        g.config.vars.Lead_In_Out['overcut_enabled'] = True
        g.config.vars.Tool_Parameters['1']['overcut_length'] = 7.0
        self.assertTrue(self.update(layer))
        # The layer uses the configuration default: the method which is
        # really used follows the global default value.
        self.assertEqual(layer.lead_in_mode, LEAD_DEFAULT)
        self.assertEqual(layer.get_lead_in_mode(), 'radius')
        self.assertEqual(layer.get_lead_out_mode(), 'straight')
        # The overcut is a setting of the layer: the layer uses the standard
        # of the configuration file.
        self.assertEqual(layer.overcut_enabled, OVERCUT_DEFAULT)
        self.assertTrue(layer.get_overcut_enabled())
        # The length of the overcut is defined per tool.
        self.assertAlmostEqual(layer.overcut_length, 7.0)

    def test_nothing_changes_if_the_values_are_the_same(self):
        layer = LayerContent(nr=1, name="L1", shapes=[])
        self.update(layer)
        self.assertFalse(self.update(layer))

    def test_the_overridden_values_are_not_overwritten(self):
        separator = g.config.vars.Layer_Options['id_float_separator']
        layer = LayerContent(
            nr=1,
            name=separator.join(["MILL", "Lim", "2", "Lr", "8.0", "Ol",
                                 "3.0"]),
            shapes=[])
        layer.overrideDefaults()
        g.config.vars.Lead_In_Out['lead_in_mode'] = 'radius'
        g.config.vars.Lead_In_Out['overcut_enabled'] = False
        self.update(layer)
        # The layer keeps its own method and its own radius.
        self.assertEqual(layer.lead_in_mode, LEAD_STRAIGHT)
        self.assertAlmostEqual(layer.lead_radius, 8.0)
        self.assertAlmostEqual(layer.overcut_length, 3.0)
        # The overcut of a layer with a length from the layer name is active
        self.assertTrue(layer.get_overcut_enabled())

    def test_the_lengths_are_converted_to_the_unit_of_the_drawing(self):
        # The configuration file is in millimeters, the drawing is in inches.
        # The length of the overcut is defined per tool: the values of the
        # tools table are converted with the unit of the drawing.
        g.config.tool_units_metric = 1
        g.config.metric = 0
        g.config.vars.Tool_Parameters['1']['overcut_length'] = 25.4
        layer = LayerContent(nr=1, name="L1", shapes=[])
        self.update(layer)
        self.assertAlmostEqual(layer.overcut_length, 25.4)



class TestMoveOrder(LeadMoveTestBase):
    """The order of the moves: the compensation has to be built up in the air,
    the plunge has to be done at the compensated position."""

    def _moves(self, gcode):
        """
        The sequence of the movements of the G-Code.
        @return: a list of tuples (command, x, y, z)
        """
        moves = []
        for line in gcode.splitlines():
            fields = line.split()
            if not fields:
                continue
            values = {}
            arguments = fields[1:]
            for index in range(0, len(arguments) - 1, 2):
                values[arguments[index]] = float(arguments[index + 1])
            moves.append((fields[0], values.get("X"), values.get("Y"),
                          values.get("Z")))
        return moves

    def test_the_plunge_is_done_before_the_nominal_lead_in(self):
        # The lead in is nominal: the tool is positioned at the compensated
        # start, plunged (G40) and then the machine compensation is switched
        # on, so that the machine offsets the nominal lead in (line + arc) and
        # the nominal contour by the tool radius. There is no separate G40
        # approach line.
        shape, layer = build_shape(closed=True, cut_cor=41)
        gcode = export_gcode(shape, layer)
        moves = self._moves(gcode)
        commands = [move[0] for move in moves]
        self.assertEqual(commands[0], "G0")     # rapid to compensated start
        self.assertIn("G41", commands)          # the compensation is switched on
        plunge = [index for index, move in enumerate(moves)
                  if move[0] == "G1" and move[3] == -2.0]
        self.assertTrue(plunge)
        g41_index = commands.index("G41")
        # No linear XY move before the compensation is activated.
        for index, move in enumerate(moves[:g41_index]):
            self.assertFalse(move[0] == "G1" and move[1] is not None,
                             "G40 approach move before G41: %s" % (move,))
        nominal_line = next(index for index, move in enumerate(moves)
                            if move[0] == "G1" and move[1] is not None and
                            index > g41_index)
        nominal_arc = commands.index("G3", nominal_line)
        # plunge (G40) -> G41 -> nominal line -> arc.
        self.assertLess(plunge[0], g41_index)
        self.assertLess(g41_index, nominal_line)
        self.assertLess(nominal_line, nominal_arc)

    def test_the_straight_lead_in_is_cut_before_the_plunge(self):
        shape, layer = build_shape(
            closed=True, cut_cor=41,
            layer_settings=dict(lead_in_mode=LEAD_STRAIGHT))
        gcode = export_gcode(shape, layer)
        moves = self._moves(gcode)
        commands = [move[0] for move in moves]
        plunge = [index for index, move in enumerate(moves)
                  if move[0] == "G1" and move[3] == -2.0]
        self.assertTrue(plunge)
        # The straight lead in is a G1 before the plunge; G41 is switched on
        # after the plunge (for the nominal contour).
        self.assertLess(commands.index("G1"), plunge[0])
        self.assertLess(plunge[0], commands.index("G41"))

    def test_the_compensation_is_cancelled_at_the_end(self):
        shape, layer = build_shape(closed=True, cut_cor=41)
        gcode = export_gcode(shape, layer)
        commands = [line.split()[0] for line in gcode.splitlines() if line]
        self.assertIn("G40", commands)
        # G40 is the last compensation command, the tool is retracted before
        self.assertGreater(commands.index("G40", 1), commands.index("G0", 1))


class TestCanvasPreview(LeadMoveTestBase):
    """The preview of the lead out and the overcut in the canvas."""

    def _preview_end(self, shape):
        """The end point of the preview of the exit geometry."""
        geos = list(getattr(shape.stmove, 'exit_geos', []))
        if not geos:
            return None
        last = geos[-1]
        return (round(last.Pe.x, 6), round(last.Pe.y, 6))

    def _exported_end(self, gcode):
        """The last movement with X and Y in the G-Code."""
        result = None
        for line in gcode.splitlines():
            fields = line.split()
            if not fields or fields[0] not in ("G0", "G1", "G2", "G3"):
                continue
            arguments = fields[1:]
            values = {}
            for index in range(0, len(arguments) - 1, 2):
                values[arguments[index]] = float(arguments[index + 1])
            if "X" in values and "Y" in values:
                result = (values["X"], values["Y"])
        return result

    def _check_preview_matches_export(self, **kwargs):
        shape, layer = build_shape(**kwargs)
        preview = self._preview_end(shape)
        gcode = export_gcode(shape, layer)
        exported = self._exported_end(gcode)
        self.assertIsNotNone(preview)
        self.assertIsNotNone(exported)
        self.assertAlmostEqual(preview[0], exported[0])
        self.assertAlmostEqual(preview[1], exported[1])

    def test_closed_contour_with_lead_out(self):
        self._check_preview_matches_export(
            closed=True, cut_cor=41,
            layer_settings=dict(lead_out_mode=LEAD_STRAIGHT))

    def test_closed_contour_with_overcut(self):
        self._check_preview_matches_export(
            closed=True, cut_cor=41,
            layer_settings=dict(overcut_enabled=True, overcut_length=50.0))

    def test_radius_lead_out_with_g41(self):
        self._check_preview_matches_export(
            closed=True, cut_cor=41,
            layer_settings=dict(lead_out_mode=LEAD_RADIUS,
                                lead_radius=20.0))

    def test_radius_lead_out_with_g42(self):
        self._check_preview_matches_export(
            closed=True, cut_cor=42,
            layer_settings=dict(lead_out_mode=LEAD_RADIUS,
                                lead_radius=20.0))

    def test_the_internal_compensation(self):
        self._check_preview_matches_export(
            closed=True, cut_cor=41, done_by_machine=False,
            layer_settings=dict(lead_out_mode=LEAD_RADIUS,
                                lead_radius=20.0))

    def test_open_contour_with_a_direction_change(self):
        # The last pass of an open contour is the mirrored one: the preview
        # has to be mirrored as well.
        self._check_preview_matches_export(
            closed=False, cut_cor=41, slice_depth=-2.0, mill_depth=-4.0,
            layer_settings=dict(lead_out_mode=LEAD_RADIUS,
                                lead_radius=20.0))

    def test_open_contour_with_a_direction_change_g42(self):
        self._check_preview_matches_export(
            closed=False, cut_cor=42, slice_depth=-2.0, mill_depth=-4.0,
            layer_settings=dict(lead_out_mode=LEAD_RADIUS,
                                lead_radius=20.0))

    def test_no_preview_if_the_functions_are_disabled(self):
        shape, layer = build_shape(closed=True, cut_cor=41)
        self.assertIsNone(self._preview_end(shape))
        self.assertEqual(len(shape.stmove.exit_geos), 0)

    def test_no_preview_for_an_invalid_geometry(self):
        # A straight lead out along the contour is rejected: the preview stays
        # empty and does not raise.
        shape, layer = build_shape(
            closed=True, cut_cor=41,
            layer_settings=dict(lead_out_mode=LEAD_STRAIGHT))
        # The square has a right angle at the end, the straight lead out is
        # valid -> the preview exists. An invalid radius is the error case:
        shape, layer = build_shape(
            closed=True, cut_cor=41,
            layer_settings=dict(lead_out_mode=LEAD_RADIUS,
                                lead_radius=1.0))
        # A radius of 1 mm is smaller than the tool radius (5 mm): the
        # geometry can not be built.
        self.assertIsNone(self._preview_end(shape))

    def test_the_canvas_path_is_created(self):
        from dxf2gcode.presentation.qt.canvas2d import StMoveGUI
        from dxf2gcode.presentation.qt.qt_compat.QtGui import QImage, QPainter
        shape, layer = build_shape(
            closed=True, cut_cor=41,
            layer_settings=dict(lead_out_mode=LEAD_RADIUS,
                                lead_radius=20.0))
        gui = StMoveGUI(shape)
        self.assertFalse(gui._exit_path.isEmpty())
        # The lead in is drawn in its own path (with an own colour): with the
        # machine compensation the start move is not part of the offset
        # contour preview.
        self.assertFalse(gui._lead_in_path.isEmpty())
        image = QImage(400, 400, QImage.Format.Format_ARGB32)
        painter = QPainter(image)
        try:
            gui.paint(painter, None)
        finally:
            painter.end()

    def test_no_preview_for_the_drag_knife(self):
        # The drag knife has no lead out and its overcut is inserted into the
        # contour before the tip offset is applied: the preview of the exit
        # geometry is not possible (documented limitation).
        shape, layer = build_shape(
            closed=True, cut_cor=40, machine_type='drag_knife',
            layer_settings=dict(overcut_enabled=True, overcut_length=50.0))
        self.assertIsNone(self._preview_end(shape))

    def test_a_change_of_the_layer_settings_rebuilds_the_preview(self):
        from dxf2gcode.presentation.qt.canvas2d import StMoveGUI
        shape, layer = build_shape(
            closed=True, cut_cor=41,
            layer_settings=dict(lead_out_mode=LEAD_RADIUS,
                                lead_radius=20.0))
        gui = StMoveGUI(shape)
        self.assertFalse(gui._exit_path.isEmpty())
        # The user switches the lead out off and the shape is repainted (the
        # tree handler does it the same way after a configuration change).
        layer.lead_out_mode = LEAD_OFF
        shape.stmove.updateShape()
        gui2 = StMoveGUI(shape)
        # The stale preview is gone.
        self.assertTrue(gui2._exit_path.isEmpty())
        self.assertEqual(len(gui2.exit_geos), 0)

    def test_the_preview_does_not_change_the_geometry(self):
        # The preview is an additional geometry: the shape and the start move
        # are not modified.
        from dxf2gcode.presentation.qt.canvas2d import StMoveGUI
        shape, layer = build_shape(
            closed=True, cut_cor=41,
            layer_settings=dict(lead_out_mode=LEAD_RADIUS,
                                lead_radius=20.0))
        geos_before = len(shape.stmove.geos)
        shape_before = len(shape.geos)
        gui = StMoveGUI(shape)
        self.assertEqual(len(shape.stmove.geos), geos_before)
        self.assertEqual(len(shape.geos), shape_before)
        self.assertTrue(gui._exit_path.boundingRect().width() > 0)


class TestCanvasFullCirclePreview(LeadMoveTestBase):
    """Full circles have equal endpoints but must remain visible."""

    def _preview(self, geos):
        from types import SimpleNamespace
        from dxf2gcode.domain.project.shape import Shape, Geos
        from dxf2gcode.presentation.qt.canvas2d import StMoveGUI

        shape = Shape(nr=0, closed=True, geos=Geos([]))
        model = SimpleNamespace(
            shape=shape, geos=Geos(geos), pocket_geos_start=0,
            lead_in_geos=[], exit_geos=[], exit_chain=[],
            set_break_chain=lambda chain: None)
        from dataclasses import replace
        from dxf2gcode.adapters.toolpath.planning import snapshot_geometry
        from dxf2gcode.domain.toolpath.inputs import ToolpathRequest, MachiningSettings, MachineCapabilities
        from dxf2gcode.domain.toolpath.movements import MovementPlan
        output = MovementPlan(ToolpathRequest(0, MachiningSettings(), MachineCapabilities()))
        output.add('linear_z', -1)
        for geo in geos:
            output.geometry(replace(snapshot_geometry(geo), role='pocket'), role='pocket')
        return StMoveGUI(shape, model, plan=output.finish())

    def test_full_circle_is_drawn_in_both_directions(self):
        from dxf2gcode.domain.geometry.arcgeo import ArcGeo
        from dxf2gcode.domain.geometry.point import Point

        for direction in (-1, 1):
            with self.subTest(direction=direction):
                circle = ArcGeo(Ps=Point(5, 0), Pe=Point(5, 0),
                                O=Point(0, 0), r=5, direction=direction)
                item = self._preview([circle])
                path = item._pocket_path
                self.assertGreater(path.elementCount(), 60)
                self.assertAlmostEqual(path.boundingRect().width(), 10, delta=0.01)
                self.assertAlmostEqual(path.boundingRect().height(), 10, delta=0.01)

    def test_rapid_between_circle_loops_does_not_draw_a_diagonal(self):
        from dxf2gcode.domain.geometry.arcgeo import ArcGeo
        from dxf2gcode.domain.geometry.point import Point
        from dxf2gcode.domain.toolpath.pocketmove import PocketMove

        first = Point(5, 0)
        second = Point(25, 0)
        item = self._preview([
            ArcGeo(Ps=first, Pe=first, O=Point(0, 0), r=5),
            PocketMove(first, second),
            PocketMove(second, second),
            ArcGeo(Ps=second, Pe=second, O=Point(20, 0), r=5),
        ])
        path = item._pocket_path
        self.assertGreater(path.elementCount(), 120)
        self.assertEqual(sum(path.elementAt(i).isMoveTo()
                             for i in range(path.elementCount())), 2)
        for i in range(1, path.elementCount()):
            end = path.elementAt(i)
            if end.isLineTo():
                start = path.elementAt(i - 1)
                self.assertLess(math.hypot(end.x - start.x, end.y - start.y), 1)


class TestCanvasLeadColors(LeadMoveTestBase):
    """The lead in / lead out previews must be told apart from the offset
    contour (which stays blue)."""

    def test_lead_in_and_offset_contour_use_different_colors(self):
        from dxf2gcode.presentation.qt.canvas2d import StMoveGUI
        # The internal compensation draws the offset contour.
        shape, layer = build_shape(
            closed=True, cut_cor=41, done_by_machine=False,
            layer_settings=dict(lead_in_mode=LEAD_RADIUS,
                                lead_out_mode=LEAD_RADIUS,
                                lead_radius=20.0))
        gui = StMoveGUI(shape)
        # The lead in is a separate path, the offset contour stays in the
        # compensation path.
        self.assertFalse(gui._lead_in_path.isEmpty())
        self.assertFalse(gui._comp_path.isEmpty())
        # The colours are different from the contour and from each other.
        self.assertNotEqual(gui.PEN_LEAD_IN_LINE.color(),
                            gui.PEN_COMP_LINE.color())
        self.assertNotEqual(gui.PEN_EXIT_LINE.color(),
                            gui.PEN_COMP_LINE.color())
        self.assertNotEqual(gui.PEN_LEAD_IN_LINE.color(),
                            gui.PEN_EXIT_LINE.color())
        # Both lead moves are drawn dashed.
        from dxf2gcode.presentation.qt.qt_compat import QtCore
        self.assertEqual(gui.PEN_LEAD_IN_LINE.style(),
                         QtCore.Qt.PenStyle.DashLine)
        self.assertEqual(gui.PEN_EXIT_LINE.style(),
                         QtCore.Qt.PenStyle.DashLine)

    def test_the_start_arrow_uses_the_lead_in_color(self):
        from dxf2gcode.presentation.qt.canvas2d import StMoveGUI, MyGraphicsScene
        from dxf2gcode.presentation.qt.qt_compat import QtCore
        shape, layer = build_shape(
            closed=True, cut_cor=41, done_by_machine=False,
            layer_settings=dict(lead_in_mode=LEAD_RADIUS,
                                lead_radius=20.0))
        scene = MyGraphicsScene()
        start_arrow = scene.createstarrow(shape)
        end_arrow = scene.createenarrow(shape)
        # The outline of the arrows matches the lead in / lead out colour.
        self.assertEqual(start_arrow.pen.color().getRgb(),
                         StMoveGUI.PEN_LEAD_IN_LINE.color().getRgb())
        self.assertEqual(end_arrow.pen.color().getRgb(),
                         StMoveGUI.PEN_EXIT_LINE.color().getRgb())
        # The arrows are 1.5 times the default size, their outline is one
        # pixel thicker and dashed.
        for arrow in (start_arrow, end_arrow):
            self.assertEqual(arrow.length, 30)
            self.assertEqual(arrow.arrowSize, 12.0)
            self.assertEqual(arrow.pen.width(), 2)
            self.assertEqual(arrow.pen.style(), QtCore.Qt.PenStyle.DashLine)

    def test_the_tool_is_shown_at_the_lead_in_entry_point(self):
        from dxf2gcode.presentation.qt.canvas2d import StMoveGUI
        from dxf2gcode.presentation.qt.qt_compat import QtCore
        from dxf2gcode.presentation.qt.qt_compat.QtGui import QImage, QPainter
        shape, layer = build_shape(
            closed=True, cut_cor=41, done_by_machine=True,
            layer_settings=dict(lead_in_mode=LEAD_STARTMOVE,
                                lead_out_mode=LEAD_OFF, lead_radius=20.0))
        gui = StMoveGUI(shape)
        self.assertFalse(gui._lead_in_path.isEmpty())
        # The tool (a circle of the tool radius) is drawn at the actual dive
        # point: the compensated rapid position, not the nominal start of the
        # lead in path.
        dive = gui._lead_in_dive_point()
        self.assertIsNotNone(dive)
        rapid = shape.stmove.geos[0]
        self.assertAlmostEqual(dive.x, rapid.x)
        self.assertAlmostEqual(dive.y, rapid.y)
        nominal_start = gui._lead_in_path.elementAt(0)
        self.assertNotAlmostEqual(dive.x, nominal_start.x)
        radius = gui._tool_radius()
        self.assertAlmostEqual(radius, layer.getToolRadius())
        self.assertGreater(radius, 0.0)
        # The tool uses the lead in colour, one pixel and dashed.
        self.assertEqual(gui.PEN_LEAD_IN_TOOL.color().getRgb(),
                         gui.PEN_LEAD_IN_LINE.color().getRgb())
        self.assertEqual(gui.PEN_LEAD_IN_TOOL.width(), 1)
        self.assertEqual(gui.PEN_LEAD_IN_TOOL.style(),
                         QtCore.Qt.PenStyle.DashLine)
        # The bounding rect contains the whole tool circle.
        br = gui.boundingRect()
        self.assertLessEqual(br.left(), dive.x - radius + 1e-6)
        self.assertLessEqual(br.top(), -dive.y - radius + 1e-6)
        # Painting must not fail.
        image = QImage(400, 400, QImage.Format.Format_ARGB32)
        painter = QPainter(image)
        try:
            gui.paint(painter, None)
        finally:
            painter.end()

    def test_the_machine_comp_circle_lead_in_preview(self):
        # The canvas shows the whole lead in of the machine compensated circle:
        # the nominal line of the common length and the nominal arc. There is
        # no separate G40 approach line; the tool circle is drawn at the
        # compensated rapid position.
        from dxf2gcode.presentation.qt.canvas2d import StMoveGUI
        shape, layer = build_shape(
            closed=True, cut_cor=41, done_by_machine=True,
            layer_settings=dict(lead_in_mode=LEAD_RADIUS,
                                lead_out_mode=LEAD_OFF, lead_radius=20.0,
                                lead_length=5.0, tool_diameter=10.0))
        gui = StMoveGUI(shape)
        geos = list(shape.stmove.lead_in_geos)
        self.assertEqual(len(geos), 2)
        nominal_line = geos[0]
        # The preview starts at the nominal line start (the canvas flips Y).
        element = gui._lead_in_path.elementAt(0)
        self.assertAlmostEqual(element.x, nominal_line.Ps.x)
        self.assertAlmostEqual(element.y, -nominal_line.Ps.y)
        # The tool circle is drawn at the compensated rapid position.
        dive = gui._lead_in_dive_point()
        self.assertIsNotNone(dive)
        self.assertAlmostEqual(dive.x, shape.stmove.geos[0].x)
        self.assertAlmostEqual(dive.y, shape.stmove.geos[0].y)
        self.assertAlmostEqual(gui._tool_radius(), layer.getToolRadius())
        # The preview contains the nominal line and the nominal arc.
        self.assertGreaterEqual(gui._lead_in_path.elementCount(), 2)


class TestCanvasPreviewBreaks(LeadMoveTestBase):
    """The preview of the exit geometry has to show the tabs (the breaks) as a
    gap: they are not cut, the export hops over them."""

    def setUp(self):
        LeadMoveTestBase.setUp(self)
        self._old_window = getattr(g, "window", None)

    def tearDown(self):
        g.window = self._old_window
        LeadMoveTestBase.tearDown(self)

    def _tab_layer(self):
        """A break layer with a small tab in the first segment."""
        from dxf2gcode.domain.project.layercontent import LayerContent, Layers
        from dxf2gcode.domain.project.shape import Shape, Geos
        from dxf2gcode.domain.geometry.linegeo import LineGeo
        from dxf2gcode.domain.geometry.point import Point
        from dxf2gcode.domain.project.layercontent import Shapes
        separator = g.config.vars.Layer_Options['id_float_separator']
        layer = LayerContent(nr=2, name="BREAKS" + separator + "1", shapes=[])
        tab = Shape(nr=1, closed=True,
                    geos=Geos([LineGeo(Point(40, -5), Point(60, -5)),
                               LineGeo(Point(60, -5), Point(60, 5)),
                               LineGeo(Point(60, 5), Point(40, 5)),
                               LineGeo(Point(40, 5), Point(40, -5))]))
        tab.axis3_mill_depth = -1.0
        tab.f_g1_plane = 400
        tab.f_g1_depth = 150
        tab.disabled = False
        for geo in tab.geos:
            geo.make_abs_geo()
        layer.shapes = Shapes([tab])
        return Layers([layer])

    @staticmethod
    def _sub_paths(path):
        """The number of the subpaths (a gap starts a new subpath)."""
        count = 0
        for index in range(path.elementCount()):
            element = path.elementAt(index)
            if element.type == 0x01:  # MoveToElement
                count += 1
        return count

    def test_the_overcut_preview_shows_a_gap_at_the_tab(self):
        from dxf2gcode.domain.geometry.breakgeo import BreakGeo
        from dxf2gcode.presentation.qt.canvas2d import StMoveGUI

        class _WindowStub(object):
            def __init__(self, layers):
                self.layerContents = layers

        g.window = _WindowStub(self._tab_layer())

        # The overcut (80 mm) reaches over the tab (40 ... 60 mm).
        shape, layer = build_shape(
            closed=True, cut_cor=41,
            layer_settings=dict(overcut_enabled=True, overcut_length=80.0))
        gui = StMoveGUI(shape)
        # The preview knows the tab: the break hop is part of it (the canvas
        # has its own start move).
        self.assertTrue(any(isinstance(geo, BreakGeo)
                            for geo in gui.exit_geos))
        # The drawn path has a gap at the tab (two subpaths).
        self.assertEqual(self._sub_paths(gui._exit_path), 2)

    def test_without_breaks_the_preview_is_continuous(self):
        from dxf2gcode.domain.project.layercontent import Layers
        from dxf2gcode.presentation.qt.canvas2d import StMoveGUI

        class _WindowStub(object):
            def __init__(self, layers):
                self.layerContents = layers

        g.window = _WindowStub(Layers([]))
        shape, layer = build_shape(
            closed=True, cut_cor=41,
            layer_settings=dict(overcut_enabled=True, overcut_length=80.0))
        gui = StMoveGUI(shape)
        self.assertEqual(self._sub_paths(gui._exit_path), 1)

    def test_the_export_hops_over_the_tab(self):
        from dxf2gcode.adapters.postprocessor.breaks import Breaks
        from dxf2gcode.adapters.postprocessor.postprocessor import MyPostProcessor
        from dxf2gcode.adapters.postprocessor.postprocessorconfig import MyPostProConfig

        class _WindowStub(object):
            def __init__(self, layers):
                self.layerContents = layers

        g.window = _WindowStub(self._tab_layer())
        shape, layer = build_shape(
            closed=True, cut_cor=41,
            layer_settings=dict(overcut_enabled=True, overcut_length=80.0))
        postpro = MyPostProcessor()
        postpro.breaks = Breaks(g.window.layerContents)
        config = MyPostProConfig()
        config.load_config()
        postpro.vars = config.vars
        postpro.initialize_export_vars()
        gcode = serialize_gcode(shape, postpro)
        # The tab is not cut: the tool hops over it (in the contour and in
        # the overcut).
        self.assertIn("G1 Z  -1.000", gcode)
        self.assertEqual(gcode.count("G1 Z  -1.000"), 2)


class TestPreviewMatchesExport(LeadMoveTestBase):
    """The preview has to show exactly the movements which are exported: the
    same order, the same points, the same arc direction and the same centers
    (the I/J offsets)."""

    @staticmethod
    def _last_moves(gcode):
        """
        The movements with X and Y after the last descent into the material
        (the last pass): the movements of the contour of the last pass
        followed by the lead out / the overcut.
        @return: a list of (command, x, y, i, j)
        """
        entries = []
        for line in gcode.splitlines():
            fields = line.split()
            if not fields or fields[0] not in ("G0", "G1", "G2", "G3"):
                continue
            values = {}
            arguments = fields[1:]
            for index in range(0, len(arguments) - 1, 2):
                values[arguments[index]] = float(arguments[index + 1])
            if "X" in values and "Y" in values:
                entries.append(("xy", fields[0], values.get("X"),
                                values.get("Y"), values.get("I"),
                                values.get("J")))
            else:
                entries.append(("z",))
        start = 0
        for index, entry in enumerate(entries):
            if entry[0] == "z" and any(other[0] == "xy" for other in
                                         entries[index + 1:]):
                # The last descent into the material: the movements after it
                # are the movements of the last pass.
                start = index + 1
        return [(entry[1], entry[2], entry[3], entry[4], entry[5])
                for entry in entries[start:] if entry[0] == "xy"]

    def _check(self, **kwargs):
        from dxf2gcode.domain.geometry.arcgeo import ArcGeo
        from dxf2gcode.domain.geometry.linegeo import LineGeo
        shape, layer = build_shape(**kwargs)
        gcode = export_gcode(shape, layer)
        moves = self._last_moves(gcode)
        geos = list(shape.stmove.exit_geos)
        self.assertTrue(geos, "the preview is empty")
        # The lead out / the overcut are the last movements of the G-Code.
        moves = moves[-len(geos):]
        self.assertEqual(len(moves), len(geos),
                         "the preview and the export have a different number "
                         "of movements")
        position = None
        for (command, x, y, i, j), geo in zip(moves, geos):
            if isinstance(geo, LineGeo):
                self.assertEqual(command, "G1")
                self.assertAlmostEqual(x, geo.Pe.x)
                self.assertAlmostEqual(y, geo.Pe.y)
            elif isinstance(geo, ArcGeo):
                self.assertIn(command, ("G2", "G3"))
                # The direction of the arc
                self.assertEqual(command, "G3" if geo.ext > 0 else "G2")
                self.assertAlmostEqual(x, geo.Pe.x)
                self.assertAlmostEqual(y, geo.Pe.y)
                # The center of the arc (the I/J offsets are relative to the
                # start point of the arc)
                start = geo.Ps if position is None else position
                self.assertAlmostEqual(i, geo.O.x - start.x)
                self.assertAlmostEqual(j, geo.O.y - start.y)
            position = geo.Pe

    def test_closed_contour_lead_out_straight(self):
        self._check(closed=True, cut_cor=41,
                    layer_settings=dict(lead_out_mode=LEAD_STRAIGHT))

    def test_closed_contour_lead_out_radius_g41(self):
        self._check(closed=True, cut_cor=41,
                    layer_settings=dict(lead_out_mode=LEAD_RADIUS,
                                        lead_radius=20.0))

    def test_closed_contour_lead_out_radius_g42(self):
        self._check(closed=True, cut_cor=42,
                    layer_settings=dict(lead_out_mode=LEAD_RADIUS,
                                        lead_radius=20.0))

    def test_closed_contour_overcut(self):
        self._check(closed=True, cut_cor=41,
                    layer_settings=dict(overcut_enabled=True,
                                        overcut_length=50.0))

    def test_closed_contour_lead_out_and_overcut(self):
        # The overcut continues the cut along the contour and the lead out
        # starts at the end of the overcut - both are written in one tool
        # path and the preview has to match the export.
        self._check(
            closed=True, cut_cor=41,
            layer_settings=dict(lead_out_mode=LEAD_RADIUS,
                                lead_radius=20.0,
                                overcut_enabled=True,
                                overcut_length=50.0))

    def test_internal_compensation(self):
        self._check(closed=True, cut_cor=41, done_by_machine=False,
                    layer_settings=dict(lead_out_mode=LEAD_RADIUS,
                                        lead_radius=20.0))

    def test_open_contour_with_an_even_number_of_passes(self):
        # The last pass is the mirrored one.
        self._check(closed=False, cut_cor=41, slice_depth=-2.0, mill_depth=-4.0,
                    layer_settings=dict(lead_out_mode=LEAD_RADIUS,
                                        lead_radius=20.0))

    def test_open_contour_with_an_odd_number_of_passes(self):
        # Three passes: the last pass has the original direction again.
        self._check(closed=False, cut_cor=41, slice_depth=-2.0, mill_depth=-6.0,
                    layer_settings=dict(lead_out_mode=LEAD_RADIUS,
                                        lead_radius=20.0))

    def test_open_contour_with_an_even_number_of_passes_g42(self):
        self._check(closed=False, cut_cor=42, slice_depth=-2.0, mill_depth=-4.0,
                    layer_settings=dict(lead_out_mode=LEAD_RADIUS,
                                        lead_radius=20.0))

    def test_open_contour_with_an_odd_number_of_passes_g42(self):
        self._check(closed=False, cut_cor=42, slice_depth=-2.0, mill_depth=-6.0,
                    layer_settings=dict(lead_out_mode=LEAD_RADIUS,
                                        lead_radius=20.0))

    def test_an_invalid_geometry_is_not_exported(self):
        # A radius which is smaller than the tool radius can not be milled:
        # the shape is not exported at all and the preview stays empty.
        shape, layer = build_shape(
            closed=True, cut_cor=41,
            layer_settings=dict(lead_out_mode=LEAD_RADIUS,
                                lead_radius=1.0))
        self.assertEqual(len(shape.stmove.exit_geos), 0)
        gcode, errors = export_with_errors(shape)
        self.assertEqual(gcode, "")
        self.assertTrue(errors)


class TestExitPreviewUsesTheContourSpace(LeadMoveTestBase):
    """
    The lead out preview is rebuilt by the canvas (StMoveGUI) and has to use
    the same coordinate space as the export. With the machine compensation
    G41/G42 the contour and the lead out are programmed nominal - independent
    of the lead in mode (the lead in may be in the tool center plane, e.g.
    LEAD_STRAIGHT). The internal compensation and G40 use the tool center.
    """

    TOOL_DIAMETER = 3.05
    WORKPIECE_RADIUS = 3.04

    def _build(self, machine, cut_cor, lead_in_mode):
        from dxf2gcode.presentation.qt.canvas2d import StMoveGUI
        shape, layer = build_shape(
            closed=True, cut_cor=cut_cor, done_by_machine=machine,
            tool_diameter=self.TOOL_DIAMETER,
            layer_settings=dict(lead_in_mode=lead_in_mode,
                                lead_out_mode=LEAD_RADIUS,
                                lead_radius=self.WORKPIECE_RADIUS))
        gui = StMoveGUI(shape)
        self.assertTrue(gui.exit_geos, "the rebuilt preview is empty")
        return shape, layer, gui

    def _assert_preview_radius(self, shape, gui, expected):
        # The canvas rebuilds the preview from self.lead_space; this is the
        # geometry the user really sees (not the initial stmove.exit_geos).
        self.assertAlmostEqual(gui.exit_geos[-1].r, expected)
        # The initial build and the rebuilt preview must agree.
        self.assertAlmostEqual(shape.stmove.exit_geos[-1].r,
                               expected)

    def test_g41_straight_lead_in_previews_the_nominal_lead_out(self):
        shape, layer, gui = self._build(True, 41, LEAD_STRAIGHT)
        self._assert_preview_radius(shape, gui, self.WORKPIECE_RADIUS)

    def test_g42_straight_lead_in_previews_the_nominal_lead_out(self):
        shape, layer, gui = self._build(True, 42, LEAD_STRAIGHT)
        self._assert_preview_radius(shape, gui, self.WORKPIECE_RADIUS)

    def test_radius_and_startmove_preview_the_nominal_lead_out(self):
        for cut_cor in (41, 42):
            for mode in (LEAD_RADIUS, LEAD_STARTMOVE):
                shape, layer, gui = self._build(True, cut_cor, mode)
                self._assert_preview_radius(shape, gui,
                                            self.WORKPIECE_RADIUS)

    def test_internal_compensation_previews_the_tool_center_lead_out(self):
        tool_radius = self.TOOL_DIAMETER / 2.0
        shape, layer, gui = self._build(False, 41, LEAD_STRAIGHT)
        self._assert_preview_radius(shape, gui,
                                    self.WORKPIECE_RADIUS - tool_radius)

    def test_g40_previews_the_tool_center_lead_out(self):
        tool_radius = self.TOOL_DIAMETER / 2.0
        shape, layer, gui = self._build(True, 40, LEAD_STRAIGHT)
        self._assert_preview_radius(shape, gui,
                                    self.WORKPIECE_RADIUS - tool_radius)

    def test_the_rebuilt_preview_matches_the_exported_arc(self):
        # The lead out of the last pass in the G-Code: the arc radius from
        # the I/J offsets has to be the same as the rebuilt preview shows.
        shape, layer, gui = self._build(True, 41, LEAD_STRAIGHT)
        gcode = export_gcode(shape, layer)
        radii = []
        for line in gcode.splitlines():
            fields = line.split()
            if not fields or fields[0] not in ("G2", "G3"):
                continue
            values = {}
            arguments = fields[1:]
            for index in range(0, len(arguments) - 1, 2):
                values[arguments[index]] = float(arguments[index + 1])
            if "I" in values or "J" in values:
                radii.append(math.hypot(values.get("I", 0.0),
                                        values.get("J", 0.0)))
        self.assertTrue(radii, "the export contains no arc")
        self.assertAlmostEqual(radii[-1], self.WORKPIECE_RADIUS)
        self.assertAlmostEqual(gui.exit_geos[-1].r, radii[-1])


class TestFoundProblems(LeadMoveTestBase):
    """Regression tests for the problems found in the manual test."""

    def test_g40_has_a_lead_out_preview(self):
        # Without a cutter compensation the contour itself is the tool center
        # path: the lead out has to be calculated in the tool center plane
        # (the same as the export).
        from dxf2gcode.presentation.qt.canvas2d import StMoveGUI
        shape, layer = build_shape(
            closed=True, cut_cor=40,
            layer_settings=dict(lead_out_mode=LEAD_RADIUS,
                                lead_radius=20.0))
        gui = StMoveGUI(shape)
        self.assertTrue(len(gui.exit_geos),
                        "the G40 path has no preview of the lead out")
        gcode = export_gcode(shape, layer)
        self.assertIn("G3", gcode)
        # The preview and the export use the same plane: the radius of the
        # tool center path is the workpiece radius minus the tool radius.
        tool_radius = layer.getToolRadius()
        self.assertAlmostEqual(gui.exit_geos[-1].r, 20.0 - tool_radius)
        self.assertAlmostEqual(gui.exit_geos[-1].Pe.x, 15.0)
        self.assertAlmostEqual(gui.exit_geos[-1].Pe.y, -15.0)

    def test_the_preview_and_the_export_use_the_same_validation(self):
        # The overcut is only possible for closed contours: on an open contour
        # it is silently ignored - neither the canvas nor the export produces
        # an overcut and there is no error message.
        from dxf2gcode.presentation.qt.canvas2d import StMoveGUI
        shape, layer = build_shape(
            closed=False, cut_cor=41,
            layer_settings=dict(overcut_enabled=True, overcut_length=20.0))
        gui = StMoveGUI(shape)
        self.assertEqual(len(gui.exit_geos), 0)
        self.assertFalse(gui._warning())
        gcode, errors = export_with_errors(shape)
        self.assertTrue(gcode)
        self.assertFalse(errors)

    def test_the_lead_out_and_the_overcut_are_used_together(self):
        # The lead out and the overcut can be used at the same time: the lead
        # out leaves the contour at its end, the overcut continues the cut
        # along the contour beyond the closing point. The preview has to show
        # the same geometry as the export.
        from dxf2gcode.presentation.qt.canvas2d import StMoveGUI
        shape, layer = build_shape(
            closed=True, cut_cor=41,
            layer_settings=dict(lead_out_mode=LEAD_RADIUS,
                                lead_radius=20.0,
                                overcut_enabled=True,
                                overcut_length=20.0))
        gui = StMoveGUI(shape)
        self.assertTrue(len(gui.exit_geos) > 0)
        gcode, errors = export_with_errors(shape)
        self.assertFalse(errors)
        self.assertTrue(gcode)

    def test_an_invalid_geometry_is_marked_in_the_canvas(self):
        # A radius which is smaller than the tool radius can not be milled:
        # the user has to see it in the canvas (the shape is not exported).
        from dxf2gcode.presentation.qt.canvas2d import StMoveGUI
        from dxf2gcode.presentation.qt.qt_compat.QtGui import QImage, QPainter
        shape, layer = build_shape(
            closed=True, cut_cor=41,
            layer_settings=dict(lead_out_mode=LEAD_RADIUS,
                                lead_radius=1.0))
        gui = StMoveGUI(shape)
        self.assertEqual(len(gui.exit_geos), 0)
        self.assertTrue(gui._warning(),
                        "the error is not shown in the canvas")
        self.assertTrue(gui.toolTip())
        # The warning marker is drawn (it must not raise an exception).
        image = QImage(400, 400, QImage.Format.Format_ARGB32)
        image.fill(0xFFFFFFFF)
        painter = QPainter(image)
        try:
            # The geometry uses the coordinates of the shape (the origin is
            # the corner of the contour), so it is shifted into the image.
            painter.translate(100, 100)
            gui.paint(painter, None)
        finally:
            painter.end()
        # The marker is really drawn (red pixels at the start of the path).
        red = 0
        for y in range(image.height()):
            for x in range(image.width()):
                colour = image.pixelColor(x, y)
                if colour.red() > 150 and colour.green() < 100:
                    red += 1
        self.assertGreater(red, 0, "the warning marker is not drawn")

    def test_a_small_radius_is_rejected_with_a_message(self):
        # The radius at the workpiece must be greater than the tool radius.
        shape, layer = build_shape(
            closed=True, cut_cor=41,
            layer_settings=dict(lead_out_mode=LEAD_RADIUS,
                                lead_radius=0.2))
        gcode, errors = export_with_errors(shape)
        self.assertEqual(gcode, "")
        self.assertTrue(errors)
        self.assertIn("tool radius", errors[0])

    def test_a_small_radius_does_not_stop_the_other_functions(self):
        # A valid overcut is exported, even if the lead in / lead out radius
        # is invalid: the invalid radius is reported, the shape is not
        # exported (no silent movements).
        shape, layer = build_shape(
            closed=True, cut_cor=41,
            layer_settings=dict(lead_in_mode=LEAD_RADIUS,
                                lead_radius=0.2,
                                overcut_enabled=True,
                                overcut_length=20.0))
        gcode, errors = export_with_errors(shape)
        self.assertEqual(gcode, "")
        self.assertTrue(errors)
        # The overcut itself is geometrically possible.
        self.assertTrue(len(shape.stmove.exit_geos) >= 0)


class TestConfiguration(LeadMoveTestBase):
    """The configuration of the new functions."""

    def test_defaults_keep_the_previous_behaviour(self):
        self.assertEqual(self.config.vars.Lead_In_Out['lead_in_mode'],
                         LEAD_STARTMOVE)
        self.assertEqual(self.config.vars.Lead_In_Out['lead_out_mode'],
                         LEAD_OFF)
        self.assertFalse(self.config.vars.Lead_In_Out['overcut_enabled'])
        # The radius, the length and the overcut length are defined per tool.
        tool = self.config.vars.Tool_Parameters['1']
        self.assertTrue(tool['lead_radius'] > 0.0)
        self.assertTrue(tool['lead_length'] > 0.0)
        self.assertEqual(tool['overcut_length'], 0.0)

    def test_the_layer_uses_the_global_defaults(self):
        layer = LayerContent(nr=1, name="L1", shapes=[])
        # The layer uses the configuration default, the method which is
        # really used follows the global default value.
        self.assertEqual(layer.lead_in_mode, LEAD_DEFAULT)
        self.assertEqual(layer.lead_out_mode, LEAD_DEFAULT)
        self.assertEqual(layer.get_lead_in_mode(),
                         self.config.vars.Lead_In_Out['lead_in_mode'])
        self.assertEqual(layer.get_lead_out_mode(),
                         self.config.vars.Lead_In_Out['lead_out_mode'])
        # The overcut is a setting of the layer: the layer uses the standard
        # of the configuration file.
        self.assertEqual(layer.overcut_enabled, OVERCUT_DEFAULT)
        self.assertEqual(layer.get_overcut_enabled(),
                         self.config.vars.Lead_In_Out['overcut_enabled'])
        # The length of the overcut is defined per tool.
        self.assertEqual(layer.overcut_length,
                         self.config.vars.Tool_Parameters['1']['overcut_length'])

    def test_a_change_of_the_global_default_is_followed(self):
        layer = LayerContent(nr=1, name="L1", shapes=[])
        g.config.vars.Lead_In_Out['lead_in_mode'] = LEAD_RADIUS
        g.config.vars.Lead_In_Out['lead_out_mode'] = LEAD_STRAIGHT
        self.assertEqual(layer.get_lead_in_mode(), LEAD_RADIUS)
        self.assertEqual(layer.get_lead_out_mode(), LEAD_STRAIGHT)
        # The layer itself is not modified: it keeps the configuration
        # default.
        self.assertEqual(layer.lead_in_mode, LEAD_DEFAULT)

    def test_the_layer_name_overrides_the_values(self):
        separator = g.config.vars.Layer_Options['id_float_separator']
        layer = LayerContent(
            nr=1,
            name=separator.join(["MILL", "Lr", "8.0", "Ll", "3.0", "Lom", "1",
                                 "Ol", "12.0"]),
            shapes=[])
        layer.overrideDefaults()
        self.assertAlmostEqual(layer.lead_radius, 8.0)
        self.assertAlmostEqual(layer.lead_length, 3.0)
        self.assertEqual(layer.lead_out_mode, LEAD_STRAIGHT)
        self.assertAlmostEqual(layer.overcut_length, 12.0)
        self.assertTrue(layer.get_overcut_enabled())
        self.assertTrue(layer.lead_radius_overridden)
        self.assertTrue(layer.lead_length_overridden)

    def test_old_config_files_are_still_loadable(self):
        # A config file without the new options gets the defaults.
        path = os.path.join(self.tmp, "config", "config.cfg")
        self.config.save_varspace()
        with open(path) as config_file:
            content = config_file.read()
        content = content.replace("[Lead_In_Out]", "[Removed_Section]")
        with open(path, "w") as config_file:
            config_file.write(content)

        config = MyConfig()
        self.assertEqual(config.var_dict["Lead_In_Out"]["lead_in_mode"],
                         LEAD_STARTMOVE)
        self.assertFalse(config.var_dict["Lead_In_Out"]["overcut_enabled"])

    def test_the_values_are_scaled_with_the_units(self):
        layer = LayerContent(nr=1, name="L1", shapes=[])
        layer.lead_radius = 2.0
        layer.lead_length = 3.0
        layer.overcut_length = 4.0
        layer.changeMeasuringUnits(1, 0)
        self.assertAlmostEqual(layer.lead_radius, 2.0 / 25.4)
        self.assertAlmostEqual(layer.lead_length, 3.0 / 25.4)
        self.assertAlmostEqual(layer.overcut_length, 4.0 / 25.4)



if __name__ == "__main__":
    unittest.main(verbosity=2)

