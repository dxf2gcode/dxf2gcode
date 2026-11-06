# -*- coding: utf-8 -*-
"""
Regression tests for SourceForge ticket #176 (pocketing).

Two defects are covered:

* missed pocket toolpaths (an unstable horizontal intersection test dropped
  whole grid rows because a near-vertical segment produced a bogus crossing
  and flipped the even-odd parity), and
* crashes for large cutter diameters / small circles (empty fill grid and a
  division by zero in the circle branch).

The tests check the produced geometry (not just "no exception was raised").

Run from the repository root:

    python -m unittest discover -s tests -t tests -p "dxf2gcode_pocketing_ticket176_test.py" -v
"""
from __future__ import absolute_import

import contextlib
import io
import math
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
        g.folder = tempfile.mkdtemp(prefix="d2g_ticket176_test_")
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
from dxf2gcode.domain.geometry.point import Point  # noqa: E402
from dxf2gcode.domain.geometry.linegeo import LineGeo  # noqa: E402
from dxf2gcode.domain.geometry.arcgeo import ArcGeo  # noqa: E402
from dxf2gcode.domain.toolpath.pocketmove import PocketMove  # noqa: E402
from dxf2gcode.domain.toolpath.pocketmill import PocketMill, BBArray  # noqa: E402
from dxf2gcode.domain.project.layercontent import LayerContent  # noqa: E402
from dxf2gcode.adapters.toolpath.preparation import prepare_shape  # noqa: E402
from dxf2gcode.domain.toolpath.leadmove import LEAD_OFF  # noqa: E402

# Reuse the existing test helpers instead of duplicating them.
from dxf2gcode_stmove_gcode_test import square_geos, corridor_shape  # noqa: E402
from dxf2gcode_pocketmill_zigzag_test import _load_shapes  # noqa: E402

DXF_POCKETING1 = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "dxf", "pocketing1.dxf")

# The grid row that was wrongly dropped for the ticket file (tool 2.0 mm).
MISSING_ROW_Y = 32.32873281583571
# Reachable x-span of the central "bridge" at that row (pocket interior).
BRIDGE_X0, BRIDGE_X1 = 35.0, 47.2


# ---------------------------------------------------------------------------
# helpers
def pocket_stmove(shape, tool_diameter, cut_cor, cw=True):
    """Build an StMove for ``shape`` with pocket milling enabled."""
    layer = LayerContent(0, "top", [shape], config=g.config)
    layer.tool_diameter = tool_diameter
    layer.start_radius = 0.0
    # The test checks the compensated pocket toolpath, not the lead in.
    layer.lead_in_mode = LEAD_OFF
    shape.parentLayer = layer
    shape.calc_bounding_box()
    shape.Pocket = True
    shape.cut_cor = cut_cor
    shape.cw = cw
    prev = g.config.vars.Cutter_Compensation["done_by_machine"]
    g.config.vars.Cutter_Compensation["done_by_machine"] = False
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            st = prepare_shape(shape)
    finally:
        g.config.vars.Cutter_Compensation["done_by_machine"] = prev
    return st


def pocket_geos(st):
    return st.geos[st.pocket_geos_start:]


def horizontal_mill_rows(st):
    """Map y -> list of (x0, x1) horizontal milling segments."""
    rows = {}
    for geo in pocket_geos(st):
        if isinstance(geo, LineGeo) and abs(geo.Ps.y - geo.Pe.y) < 1e-9:
            y = round(geo.Ps.y, 6)
            rows.setdefault(y, []).append(
                (min(geo.Ps.x, geo.Pe.x), max(geo.Ps.x, geo.Pe.x)))
    return rows


def x_coverage(segments, x0, x1):
    covered = 0.0
    for a, b in segments:
        lo, hi = max(a, x0), min(b, x1)
        if hi > lo:
            covered += hi - lo
    return covered


def degenerate_pocketmoves(st):
    bad = []
    for geo in pocket_geos(st):
        if isinstance(geo, PocketMove) and geo.length < 1e-9:
            bad.append(geo)
    return bad


def circle_geos(radius):
    """Two half circles exactly like dxfimport/geoent_circle.py produces."""
    p1 = Point(radius, 0)
    p2 = Point(-radius, 0)
    return [ArcGeo(Ps=p1, Pe=p2, O=Point(0, 0), r=radius, direction=-1),
            ArcGeo(Ps=p2, Pe=p1, O=Point(0, 0), r=radius, direction=-1)]


def make_circle_shape(radius, nr=0):
    from dxf2gcode.domain.project.shape import Shape, Geos
    s = Shape(nr=nr, closed=True, geos=Geos(circle_geos(radius)), config=g.config)
    s.AnalyseAndOptimize()
    return s


# ---------------------------------------------------------------------------
class TestRobustHorizontalIntersection(unittest.TestCase):
    """Unit tests for the new crossing helpers (ticket #176 core fix)."""

    def test_near_vertical_segment_outside_y_extent_has_no_crossing(self):
        # dx ~ 1e-13 must not be treated as a vertical line that crosses
        # everywhere; the real Y extent is [0, 10].
        geo = LineGeo(Point(5.0, 0.0), Point(5.0 + 1.9e-13, 10.0))
        self.assertIsNone(PocketMill._line_horizontal_intersection(geo, 20.0))
        self.assertIsNone(PocketMill._line_horizontal_intersection(geo, -1.0))

    def test_near_vertical_segment_inside_extent_crosses_once(self):
        geo = LineGeo(Point(5.0, 0.0), Point(5.0 + 1.9e-13, 10.0))
        x = PocketMill._line_horizontal_intersection(geo, 5.0)
        self.assertIsNotNone(x)
        self.assertAlmostEqual(x, 5.0, places=6)

    def test_vertical_segment_half_open_endpoints(self):
        geo = LineGeo(Point(5.0, 0.0), Point(5.0, 10.0))
        self.assertIsNotNone(PocketMill._line_horizontal_intersection(geo, 0.0))
        self.assertIsNotNone(PocketMill._line_horizontal_intersection(geo, 9.999))
        # upper endpoint is exclusive (half-open rule)
        self.assertIsNone(PocketMill._line_horizontal_intersection(geo, 10.0))
        # outside the extent
        self.assertIsNone(PocketMill._line_horizontal_intersection(geo, 11.0))

    def test_horizontal_segment_never_crosses(self):
        geo = LineGeo(Point(0.0, 3.0), Point(10.0, 3.0))
        self.assertIsNone(PocketMill._line_horizontal_intersection(geo, 3.0))

    def test_slanted_segment_crossing(self):
        geo = LineGeo(Point(0.0, 0.0), Point(10.0, 10.0))
        self.assertAlmostEqual(
            PocketMill._line_horizontal_intersection(geo, 4.0), 4.0, places=9)

    def test_arc_quarter_crossing_and_half_open_endpoints(self):
        # quarter arc O=(0,0) r=1 from (1,0) to (0,1), ccw
        arc = ArcGeo(Ps=Point(1, 0), Pe=Point(0, 1), O=Point(0, 0), r=1.0,
                     direction=1)
        inside = PocketMill._arc_horizontal_intersections(arc, 0.5)
        self.assertEqual(len(inside), 1)
        self.assertAlmostEqual(inside[0], math.sqrt(0.75), places=9)
        self.assertEqual(
            PocketMill._arc_horizontal_intersections(arc, 2.0), [])
        # lower endpoint (y=0) included, upper endpoint (y=1) excluded
        self.assertEqual(len(PocketMill._arc_horizontal_intersections(arc, 0.0)), 1)
        self.assertEqual(len(PocketMill._arc_horizontal_intersections(arc, 1.0)), 0)


# ---------------------------------------------------------------------------
@unittest.skipUnless(os.path.exists(DXF_POCKETING1), "pocketing1.dxf not available")
class TestPocketing1MissingLines(unittest.TestCase):
    """The row that vanished for dxf/pocketing1.dxf must be milled again."""

    def _rows(self):
        shape = _load_shapes(DXF_POCKETING1)[0]
        st = pocket_stmove(shape, tool_diameter=2.0, cut_cor=42)
        return st, horizontal_mill_rows(st)

    def test_pocket_is_not_empty(self):
        st, rows = self._rows()
        self.assertTrue(rows, "pocket produced no horizontal milling lines")

    def test_central_bridge_row_is_milled(self):
        st, rows = self._rows()
        self.assertTrue(rows)
        # grid row nearest to the previously dropped one
        row_y = min(rows.keys(), key=lambda y: abs(y - MISSING_ROW_Y))
        self.assertLessEqual(abs(row_y - MISSING_ROW_Y), 1e-6,
                             "expected the grid row at ~32.329 to exist")
        covered = x_coverage(rows[row_y], BRIDGE_X0, BRIDGE_X1)
        self.assertGreater(
            covered, 5.0,
            "the central bridge at y=%.3f must be milled (covered=%.2f mm)"
            % (row_y, covered))

    def test_no_spurious_crossing_from_near_vertical_edge(self):
        # At the problematic row the near-vertical edge at x~53.399 ends at
        # y=32.219 and must NOT contribute a crossing; only the round corner
        # arc crosses there -> exactly one crossing in that small x window.
        shape = _load_shapes(DXF_POCKETING1)[0]
        layer = LayerContent(0, "top", [shape], config=g.config)
        layer.tool_diameter = 2.0
        layer.start_radius = 0.0
        shape.parentLayer = layer
        shape.Pocket = False
        shape.cut_cor = 42
        shape.cw = True
        shape.calc_bounding_box()
        with contextlib.redirect_stdout(io.StringIO()):
            st = prepare_shape(shape)

        pm = PocketMill(st)
        pm.diff = pm.tool_rad * 2 * 0.7
        pm.bbarray = BBArray(shape.BB.Ps, shape.BB.Pe, pm.diff)
        pm.dist = pm.tool_rad / 0.7
        pm.bbarray.create()
        pm.createInterList()

        row = MISSING_ROW_Y
        near = [p for p in pm.inters
                if abs(p.y - row) < 1e-6 and 53.30 <= p.x <= 53.45]
        self.assertEqual(len(near), 1,
                         "expected exactly one genuine crossing near "
                         "x=53.39, got %s" % [round(p.x, 4) for p in near])


# ---------------------------------------------------------------------------
@unittest.skipUnless(os.path.exists(DXF_POCKETING1), "pocketing1.dxf not available")
class TestLargeToolDiameter(unittest.TestCase):
    """Large cutters must never crash; controlled handling instead."""

    def test_large_diameters_do_not_crash(self):
        for dia in (39.5, 40.0, 50.0):
            shape = _load_shapes(DXF_POCKETING1)[0]
            st = pocket_stmove(shape, tool_diameter=dia, cut_cor=42)
            # never a degenerate "milled" pocket move
            self.assertEqual(degenerate_pocketmoves(st), [],
                             "degenerate PocketMove for tool %.1f mm" % dia)

    def test_too_large_tool_is_reported_and_skipped(self):
        for dia in (40.0, 50.0):
            shape = _load_shapes(DXF_POCKETING1)[0]
            layer = LayerContent(0, "top", [shape], config=g.config)
            layer.tool_diameter = dia
            layer.start_radius = 0.0
            # The test checks the pocket toolpath, not the lead in.
            layer.lead_in_mode = LEAD_OFF
            shape.parentLayer = layer
            shape.Pocket = True
            shape.cut_cor = 42
            shape.cw = True
            shape.calc_bounding_box()
            g.config.vars.Cutter_Compensation["done_by_machine"] = False
            with self.assertLogs("core.pocketmill", level="WARNING"):
                with contextlib.redirect_stdout(io.StringIO()):
                    shape.stmove = prepare_shape(shape)
            # no fill lines at all for a grid that cannot be built
            self.assertEqual(horizontal_mill_rows(shape.stmove), {})


# ---------------------------------------------------------------------------
class TestCirclePocket(unittest.TestCase):
    """Small circles with too large cutters must not divide by zero."""

    def test_small_circle_with_large_tool_is_handled(self):
        # r=1.65 mm (3.3 mm dia) with a 2 mm cutter: previously ZeroDivisionError
        for cut_cor in (40, 41, 42):
            shape = make_circle_shape(1.65)
            layer = LayerContent(0, "top", [shape], config=g.config)
            layer.tool_diameter = 2.0
            layer.start_radius = 0.0
            shape.parentLayer = layer
            shape.Pocket = True
            shape.cut_cor = cut_cor
            shape.cw = True
            shape.calc_bounding_box()
            g.config.vars.Cutter_Compensation["done_by_machine"] = False
            with self.assertLogs("core.pocketmill", level="WARNING"):
                with contextlib.redirect_stdout(io.StringIO()):
                    st = prepare_shape(shape)
            self.assertEqual(degenerate_pocketmoves(st), [],
                             "degenerate PocketMove for cut_cor %d" % cut_cor)

    def test_millable_circle_still_produces_a_path(self):
        for cut_cor in (40, 41, 42):
            shape = make_circle_shape(5.0)
            st = pocket_stmove(shape, tool_diameter=2.0, cut_cor=cut_cor)
            added = len(pocket_geos(st))
            self.assertGreater(added, 1,
                               "circle pocket empty for cut_cor %d" % cut_cor)
            self.assertTrue(any(isinstance(geo, ArcGeo)
                                for geo in pocket_geos(st)),
                            "circle pocket must contain arc moves")
            self.assertEqual(degenerate_pocketmoves(st), [])


# ---------------------------------------------------------------------------
class TestValidPocketsStillWork(unittest.TestCase):
    """Existing (previously working) pocketing cases must keep working."""

    def test_square_pocket_rectangle_branch(self):
        from dxf2gcode.domain.project.shape import Shape, Geos
        s = Shape(nr=0, closed=True, geos=Geos(square_geos(20.0)), config=g.config)
        s.AnalyseAndOptimize()
        st = pocket_stmove(s, tool_diameter=2.0, cut_cor=42)
        self.assertGreater(len(pocket_geos(st)), 1,
                           "square pocket must not be empty")

    def test_corridor_pocket_not_empty(self):
        s = corridor_shape(nr=0)
        st = pocket_stmove(s, tool_diameter=3.0, cut_cor=42)
        self.assertGreater(len(pocket_geos(st)), 1,
                           "corridor pocket must not be empty")

    def test_pocketing1_normal_tool_has_many_rows(self):
        if not os.path.exists(DXF_POCKETING1):
            self.skipTest("pocketing1.dxf not available")
        shape = _load_shapes(DXF_POCKETING1)[0]
        st = pocket_stmove(shape, tool_diameter=2.0, cut_cor=42)
        rows = horizontal_mill_rows(st)
        # a 2 mm cutter must fill the pocket with many zig-zag rows
        self.assertGreater(len(rows), 5)
        self.assertEqual(degenerate_pocketmoves(st), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
