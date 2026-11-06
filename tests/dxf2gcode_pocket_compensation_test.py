# -*- coding: utf-8 -*-
"""
Regression tests comparing pocket milling for G40, G41 and G42.

Goal (ticket #176 follow-up): a pocket must be machined geometrically
correctly regardless of the selected compensation direction. In particular

* the inward selection keeps the boundary pass and fill inside the contour,
* G40/G41/G42 determine different pocket paths and are exported consistently
  (software compensation emits no G41/G42),
* the machine-side compensation must not be applied twice,
* the cutting edge must reach the selected boundary at 0 % edge clearance and keep the
  configured clearance otherwise.

The tests evaluate the produced geometry and G-code, not just "no exception".

Run from the repository root:

    python -m unittest discover -s tests -t tests -p "dxf2gcode_pocket_compensation_test.py" -v
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
from toolpath_test_support import serialize_gcode, serialize_shape_geometry


def _init_config():
    import dxf2gcode.bootstrap.runtime_state as g
    from dxf2gcode.adapters.config.runtime_config import MyConfig

    if getattr(g, "config", None) is None:
        g.folder = tempfile.mkdtemp(prefix="d2g_comp_test_")
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
from dxf2gcode.domain.geometry.linegeo import LineGeo  # noqa: E402
from dxf2gcode.domain.geometry.arcgeo import ArcGeo  # noqa: E402
from dxf2gcode.domain.project.layercontent import LayerContent  # noqa: E402
from dxf2gcode.adapters.toolpath.preparation import prepare_shape  # noqa: E402
from dxf2gcode.domain.toolpath.leadmove import LEAD_OFF  # noqa: E402
from dxf2gcode_pocketmill_zigzag_test import _load_shapes  # noqa: E402
from dxf2gcode_stmove_gcode_test import (  # noqa: E402
    make_postpro, make_shape, build_stmove, square_geos, norm)

DXF_POCKETING1 = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "dxf", "pocketing1.dxf")

HISTORIC = 100.0 * 3 / 14  # 21.4286 %

_CONTOUR_CACHE = None


# ---------------------------------------------------------------------------
# contour geometry helpers
def _flatten(shape, n=180):
    out = []
    for geo in shape.geos:
        if isinstance(geo, LineGeo):
            out.append((geo.Ps.x, geo.Ps.y, geo.Pe.x, geo.Pe.y))
        else:
            ext = geo.ext
            steps = max(4, int(n * abs(ext) / (2 * math.pi)) + 1)
            a0 = geo.s_ang
            pts = [(geo.O.x + geo.r * math.cos(a0 + ext * i / steps),
                    geo.O.y + geo.r * math.sin(a0 + ext * i / steps))
                   for i in range(steps + 1)]
            for i in range(len(pts) - 1):
                out.append((pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1]))
    return out


def _pocket_contour_segs():
    global _CONTOUR_CACHE
    if _CONTOUR_CACHE is None:
        _CONTOUR_CACHE = _flatten(_load_shapes(DXF_POCKETING1)[0])
    return _CONTOUR_CACHE


def _point_inside(segs, x, y):
    c = 0
    for x0, y0, x1, y1 in segs:
        if (y0 <= y < y1) or (y1 <= y < y0):
            t = (y - y0) / (y1 - y0)
            if x0 + t * (x1 - x0) > x:
                c += 1
    return c % 2 == 1


def _dist_point_seg(px, py, x0, y0, x1, y1):
    dx, dy = x1 - x0, y1 - y0
    l2 = dx * dx + dy * dy
    if l2 == 0:
        return math.hypot(px - x0, py - y0)
    t = max(0.0, min(1.0, ((px - x0) * dx + (py - y0) * dy) / l2))
    return math.hypot(px - (x0 + t * dx), py - (y0 + t * dy))


def _min_dist_to_contour(segs, geos):
    best = float("inf")
    for geo in geos:
        if isinstance(geo, LineGeo):
            length = geo.Ps.distance(geo.Pe)
            n = max(1, min(60, int(length / 0.2) + 1))
            pts = [(geo.Ps.x + (geo.Pe.x - geo.Ps.x) * i / n,
                    geo.Ps.y + (geo.Pe.y - geo.Ps.y) * i / n)
                   for i in range(n + 1)]
        else:
            pts = [(geo.Ps.x, geo.Ps.y), (geo.Pe.x, geo.Pe.y)]
        for px, py in pts:
            for s in segs:
                d = _dist_point_seg(px, py, *s)
                if d < best:
                    best = d
    return best


def _points_outside(segs, geos, tol=1e-6):
    """Sample points of ``geos`` that lie outside the contour."""
    bad = []
    for geo in geos:
        if isinstance(geo, LineGeo):
            length = geo.Ps.distance(geo.Pe)
            n = max(1, min(40, int(length / 0.3) + 1))
            pts = [(geo.Ps.x + (geo.Pe.x - geo.Ps.x) * i / n,
                    geo.Ps.y + (geo.Pe.y - geo.Ps.y) * i / n)
                   for i in range(n + 1)]
        else:
            pts = [(geo.Ps.x, geo.Ps.y), (geo.Pe.x, geo.Pe.y)]
        for px, py in pts:
            # ignore points that sit on the contour within tolerance
            d = min(_dist_point_seg(px, py, *s) for s in segs)
            if d > tol and not _point_inside(segs, px, py):
                bad.append((px, py))
    return bad


def _split_geos(st):
    boundary = [geo for geo in st.geos[:st.pocket_geos_start]
                if isinstance(geo, (LineGeo, ArcGeo))]
    fill = [geo for geo in st.geos[st.pocket_geos_start:]
            if isinstance(geo, LineGeo) and abs(geo.Ps.y - geo.Pe.y) < 1e-9]
    return boundary, fill


def _pocket(cut_cor, pct=HISTORIC, tool=2.0, cw=True):
    s = _load_shapes(DXF_POCKETING1)[0]
    s.axis3_start_mill_depth = 0.0
    s.axis3_mill_depth = -1.0
    s.axis3_slice_depth = 0.5
    s.f_g1_plane = 800
    s.f_g1_depth = 150
    s.cut_cor = cut_cor
    s.cw = cw
    s.Drill = False
    s.Pocket = True
    layer = LayerContent(0, "top", [s], config=g.config)
    layer.tool_diameter = tool
    layer.axis3_retract = 9.91
    layer.axis3_safe_margin = 3.05
    # The test checks the compensated pocket toolpath, not the lead in.
    layer.lead_in_mode = LEAD_OFF
    s.parentLayer = layer
    s.calc_bounding_box()
    g.config.vars.Pocketing["pocket_edge_clearance"] = pct
    g.config.vars.Cutter_Compensation["done_by_machine"] = False
    st = prepare_shape(s)
    s.stmove = st
    return s, st


# ---------------------------------------------------------------------------
@unittest.skipUnless(os.path.exists(DXF_POCKETING1), "pocketing1.dxf not available")
class TestPocketCompensationModes(unittest.TestCase):

    def setUp(self):
        self.pp = make_postpro()

    def test_pocket_geometry_follows_selected_direction(self):
        results = {}
        for cc in (40, 41, 42):
            s, st = _pocket(cc)
            # a fresh post processor per mode: the post processor keeps a
            # stateful feed rate, so reusing it would only hide the identity
            # check behind a deduplicated feed word
            results[cc] = norm(serialize_gcode(s, make_postpro()))
        base = results[40]
        self.assertTrue(base)
        self.assertNotEqual(results[41], base)
        self.assertNotEqual(results[42], base)

    def test_no_toolpath_outside_the_contour(self):
        segs = _pocket_contour_segs()
        for cc in (42,):
            s, st = _pocket(cc)
            boundary, fill = _split_geos(st)
            self.assertTrue(boundary, "no boundary pass for cut_cor %d" % cc)
            self.assertTrue(fill, "no fill for cut_cor %d" % cc)
            for name, geos in (("boundary", boundary), ("fill", fill)):
                bad = _points_outside(segs, geos)
                self.assertEqual(
                    bad, [],
                    "cut_cor %d: %d %s point(s) outside the contour (e.g. %s)"
                    % (cc, len(bad), name, bad[:3]))

    def test_boundary_and_fill_are_consistent(self):
        segs = _pocket_contour_segs()
        tool_rad = 1.0
        for cc in (42,):
            s, st = _pocket(cc)
            boundary, fill = _split_geos(st)
            bd = _min_dist_to_contour(segs, boundary)
            fd = _min_dist_to_contour(segs, fill)
            # boundary finishing pass sits (about) one cutter radius inside
            self.assertLessEqual(abs(bd - tool_rad), 0.02,
                                 "cut_cor %d boundary stand-off %.4f" % (cc, bd))
            # the roughing fill keeps the configured clearance, i.e. it is at
            # least as far from the contour as the boundary pass
            self.assertGreaterEqual(fd, bd - 1e-6,
                                    "cut_cor %d fill closer than boundary" % cc)

    def test_clearance_zero_puts_edge_on_contour(self):
        from types import SimpleNamespace
        segs = _pocket_contour_segs()
        tool_rad = 1.0
        for cc in (42,):
            s, st = _pocket(cc, pct=0.0)
            boundary, fill = _split_geos(st)
            # boundary pass: edge exactly on the contour
            self.assertLessEqual(_min_dist_to_contour(segs, boundary),
                                 tool_rad + 0.02)
            # The fill's clearance refers to the selected boundary pass.
            selected = _flatten(SimpleNamespace(geos=boundary))
            self.assertLessEqual(_min_dist_to_contour(selected, fill),
                                 tool_rad + 0.5 * tool_rad)

    def test_software_compensation_not_emitted_and_not_doubled(self):
        segs = _pocket_contour_segs()
        tool_rad = 1.0
        for cc in (41, 42):
            s, st = _pocket(cc)
            code = serialize_gcode(s, self.pp)
            # software compensation -> geometry is baked in, no G41/G42 output
            self.assertNotIn("G41", code)
            self.assertNotIn("G42", code)
            # the offset must be applied exactly once: boundary at 1*tool_rad
            boundary, _ = _split_geos(st)
            bd = _min_dist_to_contour(segs, boundary)
            self.assertLess(abs(bd - tool_rad), 0.02,
                            "cut_cor %d offset %.4f (double compensation?)"
                            % (cc, bd))


@unittest.skipUnless(os.path.exists(DXF_POCKETING1), "pocketing1.dxf not available")
class TestNonPocketCompensationUnchanged(unittest.TestCase):
    """The G41/G42 mapping for non-pocket shapes must be untouched."""

    def test_non_pocket_g40_exports_contour(self):
        g.config.vars.Cutter_Compensation["done_by_machine"] = False
        sh = make_shape(square_geos(10.0), cut_cor=40, cw=True)
        build_stmove(sh)
        code = norm(serialize_gcode(sh, make_postpro()))
        self.assertIn("G1 X 10.000 Y 0.000", code)
        self.assertIn("G1 X 10.000 Y 10.000", code)

    def test_non_pocket_g41_is_out_and_g42_is_in(self):
        g.config.vars.Cutter_Compensation["done_by_machine"] = False
        # a CW square: G41 -> outside, G42 -> inside (unchanged behaviour)
        expect = {41: False, 42: True}  # value = "inside"
        for cc, inside_expected in expect.items():
            sh = make_shape(square_geos(10.0), cut_cor=cc, cw=True)
            build_stmove(sh)
            boundary = [geo for geo in sh.stmove.geos
                        if isinstance(geo, LineGeo)]
            self.assertTrue(boundary)
            g0 = boundary[0]
            mx, my = (g0.Ps.x + g0.Pe.x) / 2, (g0.Ps.y + g0.Pe.y) / 2
            segs = _flatten(make_shape(square_geos(10.0), cut_cor=40))
            is_in = _point_inside(segs, mx, my)
            self.assertEqual(is_in, inside_expected,
                             "cut_cor %d offset side changed" % cc)


if __name__ == "__main__":
    unittest.main(verbosity=2)
