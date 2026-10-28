# -*- coding: utf-8 -*-
"""
Regression tests for the degenerate end biarc of a spline with a repeated
end control point (dxf/test.dxf, spline 9).

The repeated end control point makes the biarc conversion fit a micro arc at
the open end (r=0.106863 mm, chord=0.007369 mm). The cutter compensation of
that arc collapses on one side and the offset validation rejects the shape
with "offset point is 1.5071 mm from the contour (expected 1.5250 mm)".

The fix drops only this degenerate end element (see
dxfimport.geoent_spline.drop_degenerate_end_geos). A real short element, a
closed spline and a real small radius end arc are not touched.
"""
from __future__ import absolute_import

import math
import os
import sys
import unittest
from copy import deepcopy

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_DIR = os.path.dirname(_TEST_DIR)
sys.path[:0] = [_TEST_DIR, os.path.join(_REPO_DIR, "source")]

from dxf2gcode_stmove_gcode_test import make_postpro  # noqa: F401,E402

import dxf2gcode.bootstrap.runtime_state as g  # noqa: E402
from dxf2gcode.domain.geometry.arcgeo import ArcGeo  # noqa: E402
from dxf2gcode.domain.geometry.linegeo import LineGeo  # noqa: E402
from dxf2gcode.domain.geometry.point import Point  # noqa: E402
from dxf2gcode.domain.project.shape import Geos, Shape  # noqa: E402
from dxf2gcode.domain.toolpath.shapeoffset import offShapeClass  # noqa: E402
from dxf2gcode.adapters.dxf.geoent_spline import (  # noqa: E402
    drop_degenerate_end_geos)
from dxf2gcode.adapters.dxf.parser import ReadDXF  # noqa: E402
from dxf2gcode.adapters.dxf.spline_convert import Spline2Arcs  # noqa: E402

DXF = os.path.join(_REPO_DIR, "dxf", "test.dxf")
SPLINE_NR = 9          # open spline with the repeated end control point
ELLIPSE_NR = 2         # closed full ellipse
TOOL_RADIUS = 1.525
TOL = 0.001
DISTANCE_MARGIN = 0.02  # a little more than the 1 % validation tolerance


def chord(geo):
    return geo.get_start_end_points(True).distance(
        geo.get_start_end_points(False))


def offset_distance_range(off, target=TOOL_RADIUS):
    values = []
    for loop in off.loops:
        for geo in loop:
            length = getattr(geo, 'length', 0.0) or 0.0
            n = 8
            if length > 0:
                n = max(n, min(int(length / (0.1 * target)) + 1, 500))
            for k in range(n + 1):
                p = off._sample_offset_point(geo, k / float(n))
                d, _ = off._nearest_source(p)
                values.append(d)
    return min(values), max(values)


def shape_from(geos, closed):
    shape = Shape(0, closed, geos=Geos([deepcopy(geo) for geo in geos]))
    shape.AnalyseAndOptimize()
    return shape


class TestSplineEndBiarc(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.dxf = ReadDXF(filename=DXF)
        cls.spline = cls.dxf.entities.geo[SPLINE_NR]
        cls.raw = Spline2Arcs(
            degree=cls.spline.degree, Knots=cls.spline.Knots,
            Weights=cls.spline.Weights, CPoints=cls.spline.CPoints,
            tol=g.config.fitting_tolerance,
            check=g.config.vars.Import_Parameters['spline_check']).Curve

    def test_the_spline_has_a_repeated_end_control_point(self):
        cpoints = self.spline.CPoints
        self.assertTrue(cpoints[-1].within_tol(cpoints[-2],
                                               g.config.fitting_tolerance))

    def test_the_raw_conversion_creates_the_micro_end_arc(self):
        last = self.raw[-1]
        self.assertIsInstance(last, ArcGeo)
        self.assertAlmostEqual(last.r, 0.106863, places=5)
        self.assertAlmostEqual(chord(last), 0.007369, places=5)

    def test_only_the_micro_end_arc_is_dropped(self):
        cleaned = self.spline.geo
        # The raw conversion had 228 elements, the cleaned one has 227.
        self.assertEqual(len(cleaned), len(self.raw) - 1)
        # The new end element is the element before the dropped micro arc.
        self.assertAlmostEqual(chord(cleaned[-1]), chord(self.raw[-2]),
                               places=9)
        self.assertGreater(chord(cleaned[-1]), 0.01)
        # The end point only moves by the negligible chord of the micro arc.
        moved = cleaned[-1].get_start_end_points(False).distance(
            self.raw[-1].get_start_end_points(False))
        self.assertAlmostEqual(moved, 0.007367, places=5)
        self.assertLess(moved, 0.01)
        # All other elements are unchanged.
        for old, new in zip(self.raw[:-1], cleaned):
            self.assertAlmostEqual(
                old.get_start_end_points(True).distance(
                    new.get_start_end_points(True)), 0.0, places=9)
            self.assertAlmostEqual(
                old.get_start_end_points(False).distance(
                    new.get_start_end_points(False)), 0.0, places=9)
        # The length is recomputed after the drop.
        self.assertAlmostEqual(
            self.spline.length,
            sum(geo.length for geo in self.spline.geo), places=9)

    def test_the_cleaned_spline_is_contiguous(self):
        cleaned = self.spline.geo
        for first, second in zip(cleaned[:-1], cleaned[1:]):
            gap = first.get_start_end_points(False).distance(
                second.get_start_end_points(True))
            self.assertLess(gap, 1e-6)

    def test_the_cleaned_spline_offsets_on_both_sides(self):
        shape = shape_from(self.spline.geo, closed=False)
        self.assertFalse(shape.closed)
        for offtype in ("out", "in"):
            off = offShapeClass(parent=shape, offset=TOOL_RADIUS,
                                offtype=offtype)
            self.assertEqual(off.offset_status, "ok", offtype)
            self.assertTrue(off.loops, offtype)
            self.assertTrue(off._validate_offset()[0], offtype)
            low, high = offset_distance_range(off)
            self.assertGreaterEqual(low, TOOL_RADIUS - DISTANCE_MARGIN,
                                    offtype)
            self.assertLessEqual(high, TOOL_RADIUS + DISTANCE_MARGIN,
                                 offtype)


class TestDegenerateEndGuard(unittest.TestCase):

    def test_a_short_end_element_without_duplicate_points_is_kept(self):
        geos = [LineGeo(Point(0, 0), Point(10, 0)),
                LineGeo(Point(10, 0), Point(10.005, 0))]
        cpoints = [Point(0, 0), Point(5, 0), Point(10, 0)]
        drop_degenerate_end_geos(geos, cpoints, TOL)
        self.assertEqual(len(geos), 2)
        self.assertAlmostEqual(geos[-1].get_start_end_points(False).x,
                               10.005)

    def test_a_uniformly_short_end_is_kept_with_duplicate_points(self):
        # The end element is short, but the neighbour is not much longer:
        # this is not an isolated micro arc, so it must stay.
        geos = [LineGeo(Point(0, 0), Point(0.01, 0)),
                LineGeo(Point(0.01, 0), Point(0.015, 0))]
        cpoints = [Point(0, 0), Point(0.015, 0), Point(0.015, 0)]
        drop_degenerate_end_geos(geos, cpoints, TOL)
        self.assertEqual(len(geos), 2)

    def test_a_closed_spline_is_not_opened(self):
        geos = [LineGeo(Point(0, 0), Point(10, 0)),
                LineGeo(Point(10, 0), Point(0, 0))]
        cpoints = [Point(0, 0), Point(10, 0), Point(0, 0)]
        drop_degenerate_end_geos(geos, cpoints, TOL)
        self.assertEqual(len(geos), 2)

    def test_a_negligible_isolated_end_with_duplicate_points_is_dropped(self):
        geos = [LineGeo(Point(0, 0), Point(10, 0)),
                LineGeo(Point(10, 0), Point(10.005, 0))]
        cpoints = [Point(0, 0), Point(10.005, 0), Point(10.005, 0)]
        drop_degenerate_end_geos(geos, cpoints, TOL)
        self.assertEqual(len(geos), 1)
        self.assertAlmostEqual(geos[-1].get_start_end_points(False).x, 10.0)


class TestRealSmallRadiusEnd(unittest.TestCase):

    def test_a_real_small_end_arc_is_not_removed_and_its_offset_is_rejected(self):
        # A genuine end arc with r=0.5 mm and a length of 0.5 mm (chord
        # 0.479 mm). It is not a degenerate micro arc and must not be
        # removed by the cleanup. Its left offset at r=1.525 is geometrically
        # impossible and must still be rejected.
        center = Point(10, 0.5)
        radius = 0.5
        ext = 1.0
        start = Point(10, 0)
        end = Point(center.x + (start.x - center.x) * math.cos(ext) -
                    (start.y - center.y) * math.sin(ext),
                    center.y + (start.x - center.x) * math.sin(ext) +
                    (start.y - center.y) * math.cos(ext))
        arc = ArcGeo(Ps=start, Pe=end, O=center, r=radius, direction=1)
        line = LineGeo(end, Point(20, end.y))
        geos = [arc, line]
        self.assertAlmostEqual(chord(arc), 0.4794, places=3)
        self.assertGreater(chord(arc), 10.0 * TOL)

        # The cleanup does not remove the arc (no repeated end point at the
        # arc and the chord is far above the negligible threshold).
        cpoints = [start, end, Point(20, end.y)]
        drop_degenerate_end_geos(geos, cpoints, TOL)
        self.assertEqual(len(geos), 2)
        self.assertIsInstance(geos[0], ArcGeo)

        shape = shape_from(geos, closed=False)
        off = offShapeClass(parent=shape, offset=TOOL_RADIUS, offtype="out")
        self.assertNotEqual(off.offset_status, "ok")


class TestFullEllipseUnaffected(unittest.TestCase):

    def test_the_closed_full_ellipse_still_offsets_on_both_sides(self):
        dxf = ReadDXF(filename=DXF)
        ellipse = dxf.entities.geo[ELLIPSE_NR]
        shape = shape_from(ellipse.geo, closed=True)
        self.assertTrue(shape.closed)
        for offtype in ("out", "in"):
            off = offShapeClass(parent=shape, offset=TOOL_RADIUS,
                                offtype=offtype)
            self.assertEqual(off.offset_status, "ok", offtype)
            low, high = offset_distance_range(off)
            self.assertGreaterEqual(low, TOOL_RADIUS - DISTANCE_MARGIN)
            self.assertLessEqual(high, TOOL_RADIUS + DISTANCE_MARGIN)


if __name__ == "__main__":
    unittest.main()
