# -*- coding: utf-8 -*-
"""
Regression tests for two GIR/export risks:

1. Loop winding filter: offShapeClass._loop_signed_area / _loop_area_sign_ok
   used by split_into_loops (relative to Shape.isDirectionOfGeosCCW).
2. Short segment filter: Shape.Write_GCode_for_geo dropping geometries whose
   endpoints round to the same value at the post processor's post_decimals.

Only tests are added; no production code is changed. The helpers of
dxf2gcode_stmove_gcode_test are reused. Run from the ``source`` directory:

    python -m unittest dxf2gcode_gir_loop_test -v
"""
from __future__ import absolute_import

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from dxf2gcode_stmove_gcode_test import (  # noqa: E402  (config is initialised there)
    make_postpro, make_shape, build_stmove, lines_with, norm,
    square_geos, corridor_shape)

from dxf2gcode.core.shape import Shape, Geos
from dxf2gcode.core.shapeoffset import offShapeClass
from dxf2gcode.core.linegeo import LineGeo
from dxf2gcode.core.arcgeo import ArcGeo
from dxf2gcode.core.point import Point

DXF_1997 = r"D:\GIT\dxf2gcode-sourcecode\dxf\1997.DXF"


def ccw_square(size=10.0):
    return [LineGeo(Point(0, 0), Point(size, 0)),
            LineGeo(Point(size, 0), Point(size, size)),
            LineGeo(Point(size, size), Point(0, size)),
            LineGeo(Point(0, size), Point(0, 0))]


def cw_square(size=10.0):
    return list(reversed([LineGeo(Point(g.Pe.x, g.Pe.y), Point(g.Ps.x, g.Ps.y))
                          for g in ccw_square(size)]))


def make_off(shape, offset=1.0, offtype="in"):
    return offShapeClass(parent=shape, offset=offset, offtype=offtype)


# ---------------------------------------------------------------------------
class TestLoopWinding(unittest.TestCase):

    def setUp(self):
        self.off = make_off(make_shape(square_geos(10.0)), offset=1.0,
                            offtype="in")

    def test_signed_area_sign_ccw_positive(self):
        self.assertGreater(self.off._loop_signed_area(ccw_square()), 0.0)

    def test_signed_area_sign_cw_negative(self):
        self.assertLess(self.off._loop_signed_area(cw_square()), 0.0)

    def test_area_sign_ok_matches_reference(self):
        self.assertTrue(self.off._loop_area_sign_ok(ccw_square(), 1.0))
        self.assertFalse(self.off._loop_area_sign_ok(ccw_square(), -1.0))
        self.assertTrue(self.off._loop_area_sign_ok(cw_square(), -1.0))

    def test_big_enough_threshold(self):
        # min_length = 0.01 -> threshold area = 1e-4
        self.assertTrue(self.off._loop_big_enough(ccw_square(10.0)))
        tiny = 0.005                 # area 2.5e-5 < 1e-4
        self.assertFalse(self.off._loop_big_enough(ccw_square(tiny)))

    def test_non_crossing_loop_kept_regardless_of_winding(self):
        # Documented contract: a closed chain WITHOUT self-intersections is
        # kept when it is big enough - the winding check is reserved for the
        # actual split decision (offsets are assumed to preserve winding).
        res = self.off._split_loops_recursive(cw_square(10.0), 1.0)
        self.assertEqual(len(res), 1)

    def test_corridor_yields_three_valid_closed_loops(self):
        off = make_off(corridor_shape(), offset=1.5, offtype="in")
        self.assertEqual(len(off.loops), 3)
        ref_sign = 1.0 if off._loop_signed_area(off.geos) >= 0.0 else -1.0
        for loop in off.loops:
            # closed
            self.assertLessEqual(loop[0].Ps.distance(loop[-1].Pe), 1e-6)
            # correct winding (not discarded as gouging island)
            self.assertTrue(off._loop_area_sign_ok(loop, ref_sign))
            self.assertTrue(off._loop_big_enough(loop))


class TestLoopWindingExport(unittest.TestCase):

    def test_all_corridor_loops_reach_the_gcode(self):
        import dxf2gcode.globals.globals as g
        g.config.vars.Cutter_Compensation["done_by_machine"] = False
        pp = make_postpro()
        sh = corridor_shape(nr=7)
        build_stmove(sh)
        code = sh.Write_GCode(pp)
        # every loop must contribute linear cutting moves
        self.assertGreaterEqual(len(lines_with("G1", code)), 3)

    @unittest.skipUnless(os.path.exists(DXF_1997),
                         "1997.DXF not available")
    def test_nines_out_loops_are_valid_and_closed(self):
        from dxf2gcode.dxfimport.importer import ReadDXF
        from copy import copy

        dxf = ReadDXF(filename=DXF_1997)
        ent_geos = dxf.entities.geo
        shapes = []
        for cont in dxf.entities.cont:
            tmp = Shape(len(shapes), True if cont.closed else False, geos=Geos([]))
            for k in range(len(cont.order)):
                eg = ent_geos[cont.order[k][0]]
                if cont.order[k][1]:
                    eg.geo.reverse()
                    for geo in eg.geo:
                        geo = copy(geo); geo.reverse(); tmp.append(geo)
                    eg.geo.reverse()
                else:
                    for geo in eg.geo:
                        tmp.append(copy(geo))
            tmp.AnalyseAndOptimize()
            shapes.append(tmp)

        off = offShapeClass(parent=shapes[3], offset=1.525, offtype="out")
        self.assertTrue(off.loops)
        ref_sign = 1.0 if off._loop_signed_area(off.geos) >= 0.0 else -1.0
        # The MAIN (largest) loop keeps the original contour orientation.
        main = max(off.loops, key=lambda l: abs(off._loop_signed_area(l)))
        self.assertTrue(off._loop_area_sign_ok(main, ref_sign))
        # Every loop must be closed and non-degenerate. NOTE: a small,
        # non-crossing offset loop may legitimately have the opposite
        # winding (the production code only applies the winding check at
        # the split decision); it is still a valid path at distance=offset.
        for loop in off.loops:
            self.assertLessEqual(loop[0].Ps.distance(loop[-1].Pe), 1e-6)
            self.assertTrue(off._loop_big_enough(loop))


# ---------------------------------------------------------------------------
class TestShortSegmentFilter(unittest.TestCase):

    def setUp(self):
        self.pp = make_postpro()
        self.post_dec = self.pp.vars.Number_Format["post_decimals"]
        self.sh = make_shape(square_geos(10.0))

    def _kept(self, geo):
        return self.sh.Write_GCode_for_geo(geo, self.pp) != ""

    def test_normal_line_kept(self):
        self.assertTrue(self._kept(LineGeo(Point(0, 0), Point(10, 0))))

    def test_sub_rounding_line_dropped(self):
        # both deltas below 0.5 * 10^-post_dec -> endpoints round equal
        half = 0.5 * 10.0 ** (-self.post_dec)
        short = LineGeo(Point(0, 0), Point(half * 0.8, half * 0.8))
        self.assertFalse(self._kept(short))

    def test_line_above_rounding_kept(self):
        step = 2.0 * 10.0 ** (-self.post_dec)
        self.assertTrue(self._kept(LineGeo(Point(0, 0), Point(step, 0))))

    def test_full_circle_arc_kept(self):
        # a full circle has Ps == Pe - it must still be exported (G2/G3)
        circle = ArcGeo(Ps=Point(1, 0), Pe=Point(1, 0), O=Point(0, 0), r=1.0,
                        direction=1)
        self.assertTrue(self._kept(circle))

    def test_dropping_short_segment_keeps_contiguity(self):
        # a path with one sub-micron middle segment: dropping it must not
        # introduce a gap larger than the rounding resolution
        half = 0.5 * 10.0 ** (-self.post_dec)
        geos = [LineGeo(Point(0, 0), Point(10, 0)),
                LineGeo(Point(10, 0), Point(10, half * 0.8)),
                LineGeo(Point(10, half * 0.8), Point(20, 0))]
        kept = [g for g in geos if self._kept(g)]
        self.assertEqual(len(kept), 2)
        # the gap left by the dropped segment is within the rounding step
        gap = kept[0].Pe.distance(kept[1].Ps)
        self.assertLessEqual(gap, 2.0 * 10.0 ** (-self.post_dec))


if __name__ == "__main__":
    unittest.main(verbosity=2)
