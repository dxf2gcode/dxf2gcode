# -*- coding: utf-8 -*-
"""
Regression tests for the PocketMill zig-zag start (BBArray.findClosestEnd).

A G40 pocket uses the first contour vertex as its start point. That point can
be farther than overDistance from all four extreme pocket-grid ends, which
previously aborted the zig-zag (empty pocket). findClosestEnd must fall back to
the nearest valid grid end instead of returning None.

Run from the repository root:

    python -m unittest discover -s tests -t tests -p "dxf2gcode_pocketmill_zigzag_test.py" -v
"""
from __future__ import absolute_import

import os
import tempfile
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import sys
_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [_TEST_DIR, os.path.join(os.path.dirname(_TEST_DIR), "source")]


def _init_config():
    import dxf2gcode.bootstrap.runtime_state as g
    from dxf2gcode.adapters.config.runtime_config import MyConfig

    if getattr(g, "config", None) is None:
        g.folder = tempfile.mkdtemp(prefix="d2g_zigzag_test_")
        cfg = MyConfig()
        cfg.metric = 1
        try:
            cfg.mode3d = False
        except Exception:
            pass
        try:
            cfg.update_tool_values()
        except Exception:
            pass
        g.config = cfg


_init_config()

import dxf2gcode.bootstrap.runtime_state as g  # noqa: E402
from dxf2gcode.domain.toolpath.pocketmill import BBArray  # noqa: E402
from dxf2gcode.domain.geometry.point import Point  # noqa: E402

DXF_1997 = os.path.join(os.path.dirname(_TEST_DIR), "dxf", "1997.DXF")


class TestFindClosestEndFallback(unittest.TestCase):

    def _array(self):
        # overDistance = distance((1,1),(9,9)) ~ 11.31
        b = BBArray(Point(0, 0), Point(10, 10), 1.0)
        b.points_by_y = {10.0: [3.0, 7.0], 0.0: [2.0, 8.0]}
        return b

    def test_empty_grid_returns_none(self):
        b = BBArray(Point(0, 0), Point(10, 10), 1.0)
        b.points_by_y = {}
        self.assertIsNone(b.findClosestEnd(Point(5, 5)))

    def test_candidate_within_overdistance_unchanged(self):
        b = self._array()
        # all candidates are within overDistance -> nearest one, unchanged
        res = b.findClosestEnd(Point(5, 5))
        self.assertEqual(res, Point(3, 10))

    def test_far_point_falls_back_to_nearest_grid_end(self):
        b = self._array()
        # (100, 100) is farther than overDistance from every candidate; the
        # fix must still return the nearest valid grid end (was None before)
        res = b.findClosestEnd(Point(100, 100))
        self.assertIsNotNone(res)
        self.assertEqual(res, Point(7, 10))       # nearest of the four
        self.assertIn((res.x, res.y),
                      [(3.0, 10.0), (7.0, 10.0), (2.0, 0.0), (8.0, 0.0)])


def _load_shapes(path):
    from dxf2gcode.adapters.dxf.parser import ReadDXF
    from dxf2gcode.domain.project.shape import Shape, Geos
    from copy import copy

    dxf = ReadDXF(filename=path)
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
    return shapes


@unittest.skipUnless(os.path.exists(DXF_1997), "1997.DXF not available")
class TestG40PocketStart1997(unittest.TestCase):

    def _pocket_added(self, shape, cut_cor=40, cw=True):
        from dxf2gcode.domain.project.layercontent import LayerContent
        from dxf2gcode.adapters.toolpath.preparation import prepare_shape

        layer = LayerContent(0, "L", [shape])
        shape.parentLayer = layer
        shape.calc_bounding_box()
        shape.Pocket = True
        shape.cut_cor = cut_cor
        shape.cw = cw
        prev = g.config.vars.Cutter_Compensation["done_by_machine"]
        g.config.vars.Cutter_Compensation["done_by_machine"] = False
        try:
            st = prepare_shape(shape)
        finally:
            g.config.vars.Cutter_Compensation["done_by_machine"] = prev
        return len(st.geos) - st.pocket_geos_start

    def test_left_inner_g40_now_produces_a_real_path(self):
        shapes = _load_shapes(DXF_1997)
        added = self._pocket_added(shapes[2], cut_cor=40)   # left inner (9)
        self.assertGreater(added, 1, "pocket toolpath must not be empty")

    def test_left_and_right_inner_produce_equal_paths(self):
        shapes = _load_shapes(DXF_1997)
        left = self._pocket_added(shapes[2], cut_cor=40)
        right = self._pocket_added(shapes[4], cut_cor=40)
        # congruent geometry -> identical pocket path length (invariance)
        self.assertEqual(left, right)
        self.assertGreater(left, 5)


if __name__ == "__main__":
    unittest.main(verbosity=2)
