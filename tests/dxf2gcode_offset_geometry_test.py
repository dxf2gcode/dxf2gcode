# -*- coding: utf-8 -*-
"""
Geometric correctness tests for the cutter compensation (offset) of open
contours.

Unlike the crash-regression tests these tests check the geometric invariants of
the produced raw offset:

* every point of the offset is at the tool radius from the source contour,
* the offset chain is continuous (no gaps between neighbouring segments),
* non-adjacent offset segments do not cross.

The cut_cor software compensation is an outward offset by the tool radius, so
the offset must stay at exactly `offset` from the source for every point.

Run from the repository root:

    python -m unittest discover -s tests -t tests -p "dxf2gcode_offset_geometry_test.py" -v
"""
from __future__ import absolute_import

import os
import copy
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import sys
_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [_TEST_DIR, os.path.join(os.path.dirname(_TEST_DIR), "source")]


def _init_config():
    import tempfile
    import dxf2gcode.bootstrap.runtime_state as g
    from dxf2gcode.adapters.config.runtime_config import MyConfig

    if getattr(g, "config", None) is None:
        g.folder = tempfile.mkdtemp(prefix="d2g_offset_geom_")
        g.config = MyConfig()


_init_config()

from dxf2gcode.presentation.qt.qt_compat.QtWidgets import QApplication, QWidget  # noqa: E402
import dxf2gcode.bootstrap.runtime_state as g  # noqa: E402
from dxf2gcode.domain.project.shape import Shape, Geos  # noqa: E402
from dxf2gcode.domain.toolpath.shapeoffset import offShapeClass  # noqa: E402
from dxf2gcode.domain.geometry.linegeo import LineGeo  # noqa: E402
from dxf2gcode.domain.geometry.arcgeo import ArcGeo  # noqa: E402
from dxf2gcode.domain.geometry.point import Point  # noqa: E402

_APP = None


def _app():
    global _APP
    _APP = QApplication.instance() or QApplication([])


def _mk_shape(geos, closed):
    shape = Shape(0, closed, geos=Geos(geos), config=g.config)
    shape.AnalyseAndOptimize()
    return shape


def _sample_geo(geo, n=16):
    pts = []
    if isinstance(geo, ArcGeo):
        for i in range(n + 1):
            t = i / n
            pts.append(geo.O.get_arc_point(geo.s_ang + geo.ext * t, geo.r))
    elif isinstance(geo, LineGeo):
        for i in range(n + 1):
            t = i / n
            pts.append(Point(geo.Ps.x + (geo.Pe.x - geo.Ps.x) * t,
                             geo.Ps.y + (geo.Pe.y - geo.Ps.y) * t))
    else:
        pts = [geo.Ps, geo.Pe]
    return pts


def _dist_to_contour(p, geos, n=48):
    best = 1e18
    for geo in geos:
        for q in _sample_geo(geo, n):
            d = p.distance(q)
            if d < best:
                best = d
    return best


def _offset_distance_range(off, n=16):
    src = list(off.geos)
    ds = [_dist_to_contour(p, src) for r in off.rawoff
          for p in _sample_geo(r, n)]
    return (min(ds), max(ds)) if ds else (float('nan'), float('nan'))


def _max_adjacent_gap(off):
    rawoff = off.rawoff
    gaps = [rawoff[k].Pe.distance(rawoff[k + 1].Ps)
            for k in range(len(rawoff) - 1)]
    return max(gaps) if gaps else 0.0


def _nonadjacent_intersections(chain):
    """Number of intersections between non-adjacent geos of a chain."""
    count = 0
    n = len(chain)
    for i in range(n):
        for j in range(i + 2, n):
            if i == 0 and j == n - 1:
                continue
            try:
                if chain[i].find_inter_point(chain[j]) is not None:
                    count += 1
            except Exception:
                pass
    return count


def _open_corner():
    # open contour without collapsed arcs: line, line
    return [LineGeo(Point(0, 0), Point(10, 0)),
            LineGeo(Point(10, 0), Point(10, 10))]


def _one_collapsed_bump_open():
    return [LineGeo(Point(0, 0), Point(10, 0)),
            ArcGeo(Ps=Point(10, 0), Pe=Point(10.5, 0.5), O=Point(10, 0.5),
                   r=0.5, direction=1),
            LineGeo(Point(10.5, 0.5), Point(20, 0.5))]


def _two_collapsed_bumps_open():
    # Two consecutive convex arcs with radius 0.5 < tool radius 5: both
    # collapse into ConvexPoint placeholders.
    return [LineGeo(Point(0, 0), Point(10, 0)),
            ArcGeo(Ps=Point(10, 0), Pe=Point(10.5, 0.5), O=Point(10, 0.5),
                   r=0.5, direction=1),
            ArcGeo(Ps=Point(10.5, 0.5), Pe=Point(11, 0), O=Point(11, 0.5),
                   r=0.5, direction=1),
            LineGeo(Point(11, 0), Point(20, 0))]


def _two_collapsed_bumps_at_end():
    return _two_collapsed_bumps_open()[:-1]


def _two_collapsed_bumps_at_start():
    return _two_collapsed_bumps_open()[1:]


def _reversed(geos):
    result = [copy.deepcopy(g) for g in geos]
    result.reverse()
    for geo in result:
        geo.reverse()
    return result


def _degenerate_no_normals():
    # A degenerate open contour (arc and line do not join); its offset needs a
    # vertex placeholder whose incident normals can not be derived reliably.
    return [LineGeo(Point(0, 0), Point(1, 0)),
            ArcGeo(Ps=Point(1, 0), Pe=Point(1.3, 0.3), O=Point(1, 0.3),
                   r=0.3, direction=1)]


def _closed_two_bumps():
    return _two_collapsed_bumps_open() + [
        LineGeo(Point(20, 0), Point(20, 10)),
        LineGeo(Point(20, 10), Point(0, 10)),
        LineGeo(Point(0, 10), Point(0, 0))]


def _square(size):
    return [LineGeo(Point(0, 0), Point(size, 0)),
            LineGeo(Point(size, 0), Point(size, size)),
            LineGeo(Point(size, size), Point(0, size)),
            LineGeo(Point(0, size), Point(0, 0))]


def _sliver_arc_open():
    # A thin V-sliver with an arc. Offsetting it outward by 1.0 leaves a
    # localized gouge: the offset of the second line passes within ~0.884 of
    # the source arc over a ~0.93 long region (a concrete counterexample that
    # a fixed 9-sample check missed).
    return [LineGeo(Point(-15.963098, -6.718193), Point(-10.957375, -16.028963)),
            LineGeo(Point(-10.957375, -16.028963), Point(-19.474119, -8.104467)),
            ArcGeo(Ps=Point(-19.474119, -8.104467),
                   Pe=Point(-18.682356, -11.414810),
                   O=Point(-19.078238, -9.759638), r=1.701856, direction=1)]


class TestOpenOffsetGeometry(unittest.TestCase):
    """Geometric invariants of the offset of open contours."""

    def setUp(self):
        _app()

    def _assert_valid_or_rejected(self, geos, offset=5.0):
        """The result must either be a geometrically valid offset (tool
        distance everywhere, continuous) or be rejected in a controlled way.
        An invalid toolpath must never be returned."""
        shape = _mk_shape(geos, closed=False)
        off = offShapeClass(parent=shape, offset=offset, offtype="out")
        if off.offset_status == "ok":
            lo, hi = _offset_distance_range(off)
            self.assertGreaterEqual(lo, offset - 0.05)
            self.assertLessEqual(hi, offset + 0.05)
            self.assertLess(_max_adjacent_gap(off), 1e-6)
            for loop in off.loops:
                self.assertEqual(_nonadjacent_intersections(loop), 0,
                                 "the offset must not cross itself")
        else:
            self.assertNotEqual(off.offset_status, "exception")
            self.assertEqual(len(off.rawoff), 0)
            self.assertEqual(len(off.loops), 0)

    def test_open_offset_stays_at_the_tool_radius_and_is_continuous(self):
        shape = _mk_shape(_open_corner(), closed=False)
        off = offShapeClass(parent=shape, offset=5.0, offtype="out")
        self.assertEqual(off.offset_status, "ok")
        lo, hi = _offset_distance_range(off)
        self.assertAlmostEqual(lo, 5.0, places=3)
        self.assertAlmostEqual(hi, 5.0, places=3)
        self.assertLess(_max_adjacent_gap(off), 1e-6)
        for loop in off.loops:
            self.assertEqual(_nonadjacent_intersections(loop), 0)

    def test_single_collapsed_convex_arc_is_mitred(self):
        # A single collapsed convex arc is resolved by the LIR removal -> the
        # offset keeps the tool radius (this worked before the fix as well).
        shape = _mk_shape(_one_collapsed_bump_open(), closed=False)
        off = offShapeClass(parent=shape, offset=5.0, offtype="out")
        self.assertEqual(off.offset_status, "ok")
        lo, hi = _offset_distance_range(off)
        self.assertAlmostEqual(lo, 5.0, places=2)
        self.assertAlmostEqual(hi, 5.0, places=2)
        for loop in off.loops:
            self.assertEqual(_nonadjacent_intersections(loop), 0)

    def test_consecutive_collapsed_convex_arcs_are_resolved_or_rejected(self):
        # Two consecutive collapsed convex arcs: their neighbouring offset
        # lines are collinear, so a local miter is not possible. The contour
        # must not produce an invalid toolpath (no gouging).
        self._assert_valid_or_rejected(_two_collapsed_bumps_open())

    def test_collapsed_convex_arcs_at_the_open_end(self):
        self._assert_valid_or_rejected(_two_collapsed_bumps_at_end())

    def test_collapsed_convex_arcs_at_the_open_start(self):
        self._assert_valid_or_rejected(_two_collapsed_bumps_at_start())

    def test_reversed_direction_is_handled(self):
        self._assert_valid_or_rejected(_reversed(_two_collapsed_bumps_open()))

    def test_degenerate_contour_is_rejected_not_crashing(self):
        # A degenerate contour must never crash (no AttributeError/TypeError)
        # and must not return an invalid toolpath.
        self._assert_valid_or_rejected(_degenerate_no_normals())
        self._assert_valid_or_rejected(_reversed(_degenerate_no_normals()))

    def test_validate_offset_rejects_a_gouging_toolpath(self):
        shape = _mk_shape(_open_corner(), closed=False)
        off = offShapeClass(parent=shape, offset=5.0, offtype="out")
        self.assertTrue(off._validate_offset()[0])
        # A toolpath segment lying ON the contour (distance 0 instead of the
        # tool radius) must be detected.
        off.loops = [[LineGeo(Point(0, 0), Point(10, 0))]]
        ok, reason = off._validate_offset()
        self.assertFalse(ok)
        self.assertTrue(reason)

    def test_localized_gouge_is_detected(self):
        # The offset of the sliver has a localized gouge (a real counter
        # example). The validation must not accept it; an independent dense
        # scan confirms the rejection is justified.
        shape = _mk_shape(_sliver_arc_open(), closed=False)
        off = offShapeClass(parent=shape, offset=1.0, offtype="out")
        if off.offset_status == "ok":
            lo, hi = _offset_distance_range(off, n=400)
            self.assertGreaterEqual(lo, 1.0 - 0.01)
            self.assertLessEqual(hi, 1.0 + 0.01)
        else:
            self.assertNotEqual(off.offset_status, "exception")
            self.assertEqual(len(off.rawoff), 0)
            self.assertEqual(len(off.loops), 0)

    def test_validate_offset_rejects_the_wrong_side(self):
        # An outward toolpath replaced by the inward one keeps the same
        # absolute distance to the contour; the side check must still reject
        # it.
        big = _mk_shape(_square(40.0), closed=True)
        out_off = offShapeClass(parent=copy.deepcopy(big), offset=5.0,
                                offtype="out")
        in_off = offShapeClass(parent=copy.deepcopy(big), offset=5.0,
                               offtype="in")
        self.assertEqual(out_off.offset_status, "ok")
        self.assertEqual(in_off.offset_status, "ok")
        # sanity: the outward toolpath is valid
        self.assertTrue(out_off._validate_offset()[0])
        # wrong side (inward loops on the outward offset)
        out_off.loops = copy.deepcopy(in_off.loops)
        ok, reason = out_off._validate_offset()
        self.assertFalse(ok)
        self.assertIn("side", reason)


class TestClosedOffsetUnchanged(unittest.TestCase):
    """The fix must not change closed contours."""

    def setUp(self):
        _app()

    def test_closed_contour_with_consecutive_convex_arcs_is_unchanged(self):
        shape = _mk_shape(_closed_two_bumps(), closed=True)
        off = offShapeClass(parent=shape, offset=5.0, offtype="out")
        self.assertEqual(off.offset_status, "ok")
        # The closed contour is handled by the cyclic walk (it does not hit
        # the open-end path), so the outcome is the pre-fix one.
        self.assertEqual(len(off.rawoff), 11)

    def test_closed_square_offset_keeps_distance_and_closure(self):
        shape = _mk_shape(_square(40.0), closed=True)
        off = offShapeClass(parent=shape, offset=5.0, offtype="out")

        self.assertEqual(off.offset_status, "ok")
        self.assertEqual(len(off.loops), 1)
        lo, hi = _offset_distance_range(off)
        self.assertGreaterEqual(lo, 4.95)
        self.assertLessEqual(hi, 5.05)
        loop = off.loops[0]
        self.assertLess(loop[-1].Pe.distance(loop[0].Ps), 1e-6)
        self.assertEqual(_nonadjacent_intersections(loop), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
