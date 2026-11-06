# -*- coding: utf-8 -*-
"""
Edge clearance tests for the pocket compensation modes.

Focus (ticket #176 follow-up): in ``selected_direction`` the pocket fill must
keep the configured edge clearance ``c`` relative to the *offset contour*
selected by G40/G41/G42 (not relative to the original contour), and the offset
side must follow the actual contour direction (so the canvas "switch direction"
flips G41/G42).

A rectangular pocket with a known tool diameter and a known clearance is used
and the actual geometry of the produced toolpath is measured.

Run from the repository root:

    python -m unittest discover -s tests -t tests -p "dxf2gcode_pocket_edge_clearance_test.py" -v
"""
from __future__ import absolute_import

import contextlib
import io
import math
import os
import re
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
        g.folder = tempfile.mkdtemp(prefix="d2g_edge_test_")
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
from dxf2gcode.domain.project.shape import Shape, Geos  # noqa: E402
from dxf2gcode.domain.project.layercontent import LayerContent  # noqa: E402
from dxf2gcode.adapters.toolpath.preparation import prepare_shape  # noqa: E402
from dxf2gcode.domain.toolpath.leadmove import LEAD_OFF  # noqa: E402
from dxf2gcode_stmove_gcode_test import make_postpro, norm  # noqa: E402

RECT_W, RECT_H = 40.0, 30.0
TOOL_DIA = 2.0
TOOL_RAD = TOOL_DIA / 2.0
HISTORIC = 100.0 * 3 / 14  # 21.4286 %


# ---------------------------------------------------------------------------
# rectangular pocket (5 edges, so it uses the general fill, not the 4-line
# special case) 
def rect_geos(w=RECT_W, h=RECT_H):
    return [LineGeo(Point(0, 0), Point(w / 2, 0)),
            LineGeo(Point(w / 2, 0), Point(w, 0)),
            LineGeo(Point(w, 0), Point(w, h)),
            LineGeo(Point(w, h), Point(0, h)),
            LineGeo(Point(0, h), Point(0, 0))]


def make_shape(geos, nr=0):
    s = Shape(nr=nr, closed=True, geos=Geos(geos), config=g.config)
    s.AnalyseAndOptimize()
    return s


def build(mode, cut_cor, pct, reversed_dir=False, geos=None):
    g.config.vars.Pocketing["pocket_compensation_mode"] = mode
    g.config.vars.Pocketing["pocket_edge_clearance"] = pct
    s = make_shape(geos if geos is not None else rect_geos())
    if reversed_dir:
        s.reverse()   # the canvas "switch direction" action
    s.axis3_start_mill_depth = 0.0
    s.axis3_mill_depth = -1.0
    s.axis3_slice_depth = 0.5
    s.f_g1_plane = 800
    s.f_g1_depth = 150
    s.cut_cor = cut_cor
    s.Drill = False
    s.Pocket = True
    layer = LayerContent(0, "L", [s], config=g.config)
    layer.tool_diameter = TOOL_DIA
    layer.axis3_retract = 9.91
    layer.axis3_safe_margin = 3.05
    # The test checks the compensated pocket toolpath, not the lead in.
    layer.lead_in_mode = LEAD_OFF
    s.parentLayer = layer
    s.calc_bounding_box()
    g.config.vars.Cutter_Compensation["done_by_machine"] = False
    with contextlib.redirect_stdout(io.StringIO()):
        st = prepare_shape(s)
    s.stmove = st
    return s, st


def _flatten(geos, n=120):
    out = []
    for geo in geos:
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


def _dist_point_seg(px, py, x0, y0, x1, y1):
    dx, dy = x1 - x0, y1 - y0
    l2 = dx * dx + dy * dy
    if l2 == 0:
        return math.hypot(px - x0, py - y0)
    t = max(0.0, min(1.0, ((px - x0) * dx + (py - y0) * dy) / l2))
    return math.hypot(px - (x0 + t * dx), py - (y0 + t * dy))


def _sample(geos):
    pts = []
    for geo in geos:
        if isinstance(geo, LineGeo):
            length = geo.Ps.distance(geo.Pe)
            n = max(1, min(120, int(length / 0.1) + 1))
            pts += [(geo.Ps.x + (geo.Pe.x - geo.Ps.x) * i / n,
                     geo.Ps.y + (geo.Pe.y - geo.Ps.y) * i / n)
                    for i in range(n + 1)]
        else:
            pts += [(geo.Ps.x, geo.Ps.y), (geo.Pe.x, geo.Pe.y)]
    return pts


def min_dist(geos_a, geos_b):
    """Minimum distance between the sampled geometry A and the segments of B."""
    segs = _flatten(geos_b)
    best = float("inf")
    for px, py in _sample(geos_a):
        for s in segs:
            d = _dist_point_seg(px, py, *s)
            if d < best:
                best = d
    return best


def point_inside(segs, x, y):
    c = 0
    for x0, y0, x1, y1 in segs:
        if (y0 <= y < y1) or (y1 <= y < y0):
            t = (y - y0) / (y1 - y0)
            if x0 + t * (x1 - x0) > x:
                c += 1
    return c % 2 == 1


def split(st):
    boundary = [geo for geo in st.geos[:st.pocket_geos_start]
                if isinstance(geo, (LineGeo, ArcGeo))]
    fill = [geo for geo in st.geos[st.pocket_geos_start:]
            if isinstance(geo, LineGeo) and abs(geo.Ps.y - geo.Pe.y) < 1e-9]
    return boundary, fill


def boundary_side(orig_segs, boundary):
    b0 = boundary[0]
    mx, my = (b0.Ps.x + b0.Pe.x) / 2, (b0.Ps.y + b0.Pe.y) / 2
    return "in" if point_inside(orig_segs, mx, my) else "out"


def edge_clearance(fill, reference_geos):
    """Cutting-edge distance to the reference contour (= centre dist - radius)."""
    return min_dist(fill, reference_geos) - TOOL_RAD


# ---------------------------------------------------------------------------
class TestSelectedDirectionCW(unittest.TestCase):
    """Test A: selected_direction, contour CW."""

    def test_offset_contour_positions(self):
        orig = _flatten(make_shape(rect_geos()).geos)
        for cc in (40, 41, 42):
            s, st = build("selected_direction", cc, 20.0)
            boundary, _ = split(st)
            self.assertTrue(boundary, "no boundary for cc=%d" % cc)
            d = min_dist(boundary, make_shape(rect_geos()).geos)
            if cc == 40:
                self.assertLess(d, 0.01, "G40 offset contour must equal original")
            else:
                self.assertAlmostEqual(d, TOOL_RAD, delta=0.02,
                                       msg="cc=%d offset %.4f" % (cc, d))
                side = boundary_side(orig, boundary)
                self.assertEqual(side, "out" if cc == 41 else "in",
                                 "cc=%d offset side" % cc)

    def test_clearance_relative_to_offset_contour(self):
        c = TOOL_DIA * 20.0 / 100.0
        for cc in (40, 41, 42):
            s, st = build("selected_direction", cc, 20.0)
            boundary, fill = split(st)
            self.assertTrue(fill)
            measured = edge_clearance(fill, boundary)
            self.assertGreaterEqual(measured, c - 0.02,
                                    "cc=%d measured %.4f" % (cc, measured))
            self.assertLessEqual(measured, c + 0.5 * TOOL_RAD + 0.02,
                                 "cc=%d measured %.4f" % (cc, measured))

    def test_zero_clearance_touches_offset_contour(self):
        for cc in (40, 41, 42):
            s, st = build("selected_direction", cc, 0.0)
            boundary, fill = split(st)
            measured = edge_clearance(fill, boundary)
            self.assertLessEqual(measured, 0.5 * TOOL_RAD + 0.02,
                                 "cc=%d measured %.4f" % (cc, measured))

    def test_no_double_radius_offset(self):
        for cc in (41, 42):
            s, st = build("selected_direction", cc, 20.0)
            boundary, _ = split(st)
            d = min_dist(boundary, make_shape(rect_geos()).geos)
            self.assertGreater(d, 0.5 * TOOL_RAD)
            self.assertLess(abs(d - TOOL_RAD), 0.02)


class TestSelectedDirectionReversed(unittest.TestCase):
    """Test B: the canvas "switch direction" flips the offset sides."""

    def test_offset_sides_flip(self):
        orig = _flatten(make_shape(rect_geos()).geos)
        normal = {}
        reversedd = {}
        for cc in (41, 42):
            _, st = build("selected_direction", cc, 20.0, reversed_dir=False)
            b, _ = split(st)
            normal[cc] = boundary_side(orig, b)
            _, st2 = build("selected_direction", cc, 20.0, reversed_dir=True)
            b2, _ = split(st2)
            reversedd[cc] = boundary_side(orig, b2)
        # reversing the contour must swap which side G41/G42 use ...
        self.assertEqual(normal[41], "out")
        self.assertEqual(normal[42], "in")
        self.assertEqual(reversedd[41], "in")
        self.assertEqual(reversedd[42], "out")
        # ... and G41/G42 must never end up on the same side
        self.assertNotEqual(reversedd[41], reversedd[42])

    def test_clearance_constant_after_reversal(self):
        c = TOOL_DIA * 20.0 / 100.0
        for cc in (40, 41, 42):
            s, st = build("selected_direction", cc, 20.0, reversed_dir=True)
            boundary, fill = split(st)
            self.assertTrue(fill, "cc=%d no fill" % cc)
            measured = edge_clearance(fill, boundary)
            self.assertGreaterEqual(measured, c - 0.02)
            self.assertLessEqual(measured, c + 0.5 * TOOL_RAD + 0.02)


class TestClearanceValues(unittest.TestCase):
    """Test C: different clearance percentages."""

    def test_clearance_scales_with_percentage(self):
        for cc in (40, 41, 42):
            _, st0 = build("selected_direction", cc, 0.0)
            _, st20 = build("selected_direction", cc, 20.0)
            m0 = edge_clearance(split(st0)[1], split(st0)[0])
            m20 = edge_clearance(split(st20)[1], split(st20)[0])
            self.assertLess(m0, 0.5 * TOOL_RAD + 0.02)
            self.assertAlmostEqual(m20 - m0, TOOL_DIA * 20.0 / 100.0, delta=0.5 * TOOL_RAD)

    def test_radius_offset_independent_of_clearance(self):
        # the offset contour stays one radius away, for any clearance value
        for pct in (0.0, 5.0, 20.0, 50.0):
            _, st = build("selected_direction", 42, pct)
            boundary, _ = split(st)
            d = min_dist(boundary, make_shape(rect_geos()).geos)
            self.assertAlmostEqual(d, TOOL_RAD, delta=0.02,
                                   msg="pct=%s offset %.4f" % (pct, d))


class TestRetiredPocketOverride(unittest.TestCase):
    def test_obsolete_mode_cannot_override_selected_direction(self):
        for cc in (40, 41, 42):
            old, _ = build("always_inward", cc, 20.0)
            selected, _ = build("selected_direction", cc, 20.0)
            self.assertEqual(norm(serialize_gcode(old, make_postpro())),
                             norm(serialize_gcode(selected, make_postpro())))


def tearDownModule():
    # do not leak a non-default pocket compensation mode into other tests
    try:
        g.config.vars.Pocketing["pocket_compensation_mode"] = "always_inward"
    except Exception:
        pass


if __name__ == "__main__":
    unittest.main(verbosity=2)
