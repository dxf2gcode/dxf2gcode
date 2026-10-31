# -*- coding: utf-8 -*-
"""
Regression test: the lead in and the lead out have to be at the start point
which the user has set, also with the option "split line segments"
("Linien teilen").

The option cuts every line of the contour in two halves at the import. If the
user sets the start point in the middle of a line, the first and the last
geometry of the closed contour are the two halves of that line - and
therefore colinear.

The cutter compensation (the software compensation of dxf2gcode) used to join
those two colinear geometries: the joined geometry starts at the start point
of the LAST geometry, so the start point of the contour was moved to the end
of the contour. The lead in was then built at the wrong end of the contour
(and the lead out as well).

The test builds two closed contours, sets the start point in the middle of a
line of each of them and checks the toolpath, the lead in, the lead out and
the exported G-Code - with and without the "split line segments" option and
with both contour directions.

Run from the repository root:

    python -m unittest discover -s tests -t tests -p "dxf2gcode_leadmove_startpoint_test.py" -v
"""
from __future__ import absolute_import

import os
import shutil
import sys
import tempfile
import unittest
from copy import deepcopy

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [_TEST_DIR, os.path.join(os.path.dirname(_TEST_DIR), "source")]

import dxf2gcode.bootstrap.runtime_state as g  # noqa: E402
from dxf2gcode.domain.project.layercontent import LayerContent  # noqa: E402
from dxf2gcode.domain.toolpath.leadmove import LEAD_RADIUS  # noqa: E402
from dxf2gcode.domain.geometry.linegeo import LineGeo  # noqa: E402
from dxf2gcode.domain.geometry.point import Point  # noqa: E402
from dxf2gcode.domain.project.shape import Shape, Geos  # noqa: E402
from dxf2gcode.adapters.config.runtime_config import MyConfig  # noqa: E402
from dxf2gcode.presentation.qt.qt_compat.QtWidgets import QApplication  # noqa: E402

from dxf2gcode_leadmove_golden_test import export_gcode  # noqa: E402

_APP = None

TOOL_RADIUS = 1.0     # tool diameter 2.0 mm


def _app():
    global _APP
    if _APP is None:
        _APP = QApplication.instance() or QApplication([])
    return _APP


def split_line_segments(geos):
    """
    Split every line of the contour in two halves - the same as
    MainWindow.append_geo_to_shape does with the option "split line
    segments" enabled.
    @param geos: the geometries of the contour
    @return: the split geometries
    """
    result = []
    for geo in geos:
        if isinstance(geo, LineGeo):
            diff = (geo.Pe - geo.Ps) / 2.0
            geo_b = deepcopy(geo)
            geo_a = deepcopy(geo)
            geo_b.Pe -= diff
            geo_a.Ps += diff
            result.append(geo_b)
            result.append(geo_a)
        else:
            result.append(geo)
    return result


def square_geos(size=10.0):
    """A closed square (counter clockwise)."""
    return [LineGeo(Point(0, 0), Point(size, 0)),
            LineGeo(Point(size, 0), Point(size, size)),
            LineGeo(Point(size, size), Point(0, size)),
            LineGeo(Point(0, size), Point(0, 0))]


def rectangle_geos(width=20.0, height=10.0):
    """A closed rectangle (counter clockwise)."""
    return [LineGeo(Point(0, 0), Point(width, 0)),
            LineGeo(Point(width, 0), Point(width, height)),
            LineGeo(Point(width, height), Point(0, height)),
            LineGeo(Point(0, height), Point(0, 0))]


class StartPointTestBase(unittest.TestCase):

    def setUp(self):
        _app()
        self.tmp = tempfile.mkdtemp(prefix="d2g_startpoint_")
        self._old_folder = getattr(g, "folder", None)
        self._old_config = getattr(g, "config", None)
        g.folder = self.tmp
        os.makedirs(os.path.join(self.tmp, "config"))
        self.config = MyConfig()
        g.config = self.config
        self._old_done_by_machine = g.config.vars.Cutter_Compensation[
            "done_by_machine"]

    def tearDown(self):
        g.config.vars.Cutter_Compensation["done_by_machine"] = \
            self._old_done_by_machine
        g.folder = self._old_folder
        g.config = self._old_config
        shutil.rmtree(self.tmp, ignore_errors=True)

    def make_shape(self, geos, nr=1, cut_cor=41, cw=True, tool_diameter=2.0):
        """
        A shape with a layer, the lead in and the lead out are set to
        "radius".
        """
        shape = Shape(nr=nr, closed=True, geos=Geos(geos))
        shape.AnalyseAndOptimize()
        shape.axis3_start_mill_depth = 0.0
        shape.axis3_mill_depth = -1.0
        shape.axis3_slice_depth = 0.5
        shape.f_g1_plane = 800
        shape.f_g1_depth = 150
        shape.cut_cor = cut_cor
        shape.cw = cw
        shape.Drill = False
        shape.Pocket = False
        layer = LayerContent(nr, "L%i" % nr, [shape])
        layer.tool_diameter = tool_diameter
        layer.axis3_retract = 9.91
        layer.axis3_safe_margin = 3.05
        layer.lead_in_mode = LEAD_RADIUS
        layer.lead_out_mode = LEAD_RADIUS
        layer.lead_radius = 5.0
        layer.lead_length = 2.0
        shape.parentLayer = layer
        return shape, layer

    def stmove_of(self, shape):
        from dxf2gcode.adapters.toolpath.preparation import prepare_shape
        stmove = prepare_shape(shape)
        shape.stmove = stmove
        return stmove

    def assertPointAlmostEqual(self, first, second, msg=None):
        self.assertAlmostEqual(first.x, second.x, 6, msg)
        self.assertAlmostEqual(first.y, second.y, 6, msg)

    def hasPosition(self, positions, point):
        """Whether the point is one of the positions of the G-Code."""
        for position in positions:
            if (abs(position.x - point.x) < 1e-6 and
                    abs(position.y - point.y) < 1e-6):
                return True
        return False


class TestStartPointWithoutSplit(StartPointTestBase):
    """Without the "split line segments" option everything stays as it is."""

    def test_the_lead_in_is_at_the_start_point(self):
        # The lead in is programmed in the nominal plane: with the machine
        # compensation the nominal arc ends exactly at the (nominal) start
        # point, because the machine offsets the whole lead in by the tool
        # radius while it is cut.
        g.config.vars.Cutter_Compensation["done_by_machine"] = True
        shape, layer = self.make_shape(square_geos(10.0))
        shape.setNearestStPoint(Point(10.0, 5.0))
        start = shape.get_start_end_points(True, True)[0]
        stmove = self.stmove_of(shape)
        # The lead in ends at the start point (nominal).
        self.assertAlmostEqual(stmove.lead_in_geos[-1].Pe.distance(start),
                               0.0, 6)
        # The lead out starts at the end of the (nominal) toolpath.
        end = shape.get_start_end_points(False, True)[0]
        self.assertPointAlmostEqual(stmove.exit_geos[0].Ps, end)

    def test_the_lead_in_is_at_the_offset_of_the_start_point(self):
        # The software cutter compensation mills the offset contour: the lead
        # in is at the offset of the start point, i.e. at the distance of the
        # tool radius from it.
        g.config.vars.Cutter_Compensation["done_by_machine"] = False
        shape, layer = self.make_shape(square_geos(10.0))
        shape.setNearestStPoint(Point(10.0, 5.0))
        start = shape.get_start_end_points(True, True)[0]
        stmove = self.stmove_of(shape)
        toolpath_start = stmove.lead_in_geos[-1].Pe
        self.assertAlmostEqual(toolpath_start.distance(start), TOOL_RADIUS,
                               6)
        # The lead out starts at the end of the toolpath, which is the start
        # point again (the contour is closed).
        self.assertPointAlmostEqual(stmove.exit_geos[0].Ps, toolpath_start)


class TestStartPointWithSplit(StartPointTestBase):
    """With the "split line segments" option the start point must be kept."""

    def _check_shape(self, shape, layer, start, done_by_machine,
                     expected_offset):
        g.config.vars.Cutter_Compensation["done_by_machine"] = done_by_machine
        stmove = self.stmove_of(shape)
        # The start point of the shape is the start point the user has set.
        self.assertPointAlmostEqual(shape.get_start_end_points(True, True)[0],
                                    start)
        if done_by_machine:
            # The lead in is nominal (the machine offsets it by the tool
            # radius while it is cut), so it ends exactly at the start point.
            self.assertPointAlmostEqual(stmove.lead_in_geos[-1].Pe, start)
            self.assertPointAlmostEqual(stmove.geos[-1].Pe, start)
        else:
            # The lead in is the offset tool center path (cut by dxf2gcode).
            self.assertPointAlmostEqual(stmove.lead_in_geos[-1].Pe,
                                        expected_offset)
            self.assertPointAlmostEqual(stmove.geos[-1].Pe, expected_offset)
        # The lead out starts at the end of the toolpath. With the internal
        # compensation the toolpath is the offset contour; with the machine
        # compensation the contour itself is milled, so the lead out is
        # nominal and starts at the (nominal) contour end.
        if done_by_machine:
            self.assertPointAlmostEqual(stmove.exit_geos[0].Ps, start)
        else:
            self.assertPointAlmostEqual(stmove.exit_geos[0].Ps,
                                        expected_offset)

    def test_two_contours_with_the_start_point_in_the_middle_of_a_line(self):
        # The first contour: a square, the start point in the middle of the
        # right line.
        shape, layer = self.make_shape(split_line_segments(square_geos(10.0)),
                                       nr=1)
        shape.setNearestStPoint(Point(10.0, 5.0))
        self.assertPointAlmostEqual(shape.get_start_end_points(True, True)[0],
                                    Point(10.0, 5.0))
        for done_by_machine in (True, False):
            self._check_shape(shape, layer, Point(10.0, 5.0), done_by_machine,
                              Point(11.0, 5.0))

        # The second contour: a rectangle, the start point in the middle of
        # the bottom line.
        shape2, layer2 = self.make_shape(
            split_line_segments(rectangle_geos(20.0, 10.0)), nr=2)
        shape2.setNearestStPoint(Point(10.0, 0.0))
        self.assertPointAlmostEqual(
            shape2.get_start_end_points(True, True)[0], Point(10.0, 0.0))
        for done_by_machine in (True, False):
            self._check_shape(shape2, layer2, Point(10.0, 0.0),
                              done_by_machine, Point(10.0, -1.0))

    def test_the_order_of_the_contour_geometries_is_kept(self):
        shape, layer = self.make_shape(split_line_segments(square_geos(10.0)),
                                       nr=1)
        shape.setNearestStPoint(Point(10.0, 5.0))
        # The contour starts in the middle of the right line and ends there
        # again (the contour is closed).
        geos = list(shape.geos)
        self.assertPointAlmostEqual(geos[0].Ps, Point(10.0, 5.0))
        self.assertPointAlmostEqual(geos[-1].Pe, Point(10.0, 5.0))
        # The geometries are connected one after the other.
        for index in range(len(geos) - 1):
            self.assertPointAlmostEqual(geos[index].Pe, geos[index + 1].Ps)

    def test_both_contour_directions(self):
        # The lead in is built on the free side of the contour: with the
        # opposite contour direction it is mirrored.
        g.config.vars.Cutter_Compensation["done_by_machine"] = False
        ends = []
        for cw in (True, False):
            shape, layer = self.make_shape(
                split_line_segments(square_geos(10.0)), nr=1, cw=cw)
            shape.setNearestStPoint(Point(10.0, 5.0))
            stmove = self.stmove_of(shape)
            ends.append(stmove.lead_in_geos[-1].Pe)
            # In both cases the lead in ends at the start point (or at its
            # offset).
            self.assertAlmostEqual(stmove.lead_in_geos[-1].Pe.distance(
                Point(10.0, 5.0)), TOOL_RADIUS, 6)
        # The two lead ins are on different sides of the contour.
        self.assertNotAlmostEqual(ends[0].x, ends[1].x)

    def test_the_preview_matches_the_exported_gcode(self):
        for done_by_machine in (True, False):
            g.config.vars.Cutter_Compensation["done_by_machine"] = \
                done_by_machine
            shape, layer = self.make_shape(
                split_line_segments(square_geos(10.0)), nr=1)
            shape.setNearestStPoint(Point(10.0, 5.0))
            stmove = self.stmove_of(shape)
            gcode = export_gcode(shape, layer)
            positions = []
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
                    positions.append(Point(values["X"], values["Y"]))
            self.assertTrue(positions, gcode)
            # The lead in of the preview ends at the start of the contour:
            # the position is part of the G-Code.
            self.assertTrue(
                self.hasPosition(positions, stmove.lead_in_geos[-1].Pe),
                gcode)
            # The lead out of the preview is the last movement.
            self.assertPointAlmostEqual(positions[-1],
                                        stmove.exit_geos[-1].Pe)

    def test_the_lead_in_is_at_the_offset_of_the_start_point(self):
        # The general invariant: the toolpath starts at the offset of the
        # start point of the contour (the distance of the tool radius from
        # it) - with and without the split option.
        g.config.vars.Cutter_Compensation["done_by_machine"] = False
        for split in (False, True):
            geos = square_geos(10.0)
            if split:
                geos = split_line_segments(geos)
            shape, layer = self.make_shape(geos, nr=1)
            shape.setNearestStPoint(Point(10.0, 5.0))
            start = shape.get_start_end_points(True, True)[0]
            stmove = self.stmove_of(shape)
            self.assertAlmostEqual(
                stmove.lead_in_geos[-1].Pe.distance(start), TOOL_RADIUS, 6)


if __name__ == "__main__":
    unittest.main(verbosity=2)
