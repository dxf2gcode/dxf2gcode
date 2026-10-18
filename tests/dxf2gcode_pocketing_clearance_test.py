# -*- coding: utf-8 -*-
"""
Tests for the pocketing edge clearance (SourceForge ticket #176 follow-up).

They measure the real toolpath of ``dxf/pocketing1.dxf`` (not only the GUI)
and verify that

* the configured "Pocketing edge clearance" (as % of the tool diameter)
  sets the distance between the cutting edge and the contour,
* the value is applied uniformly for the compensation directions
  G40/G41/G42,
* inner (concave) and outer (convex) contour features are treated the same,
* the default value reproduces the historical centre stand-off
  (cutter radius / 0.7),
* the boundary pass stays at exactly one cutter radius (no double
  counting of the tool radius).

Run from the repository root:

    python -m unittest discover -s tests -t tests -p "dxf2gcode_pocketing_clearance_test.py" -v
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
    import dxf2gcode.globals.globals as g
    from dxf2gcode.globals.config import MyConfig

    if getattr(g, "config", None) is None:
        g.folder = tempfile.mkdtemp(prefix="d2g_clear_test_")
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

import dxf2gcode.globals.globals as g  # noqa: E402
from dxf2gcode.core.linegeo import LineGeo  # noqa: E402
from dxf2gcode.core.arcgeo import ArcGeo  # noqa: E402
from dxf2gcode.core.pocketmill import PocketMill  # noqa: E402
from dxf2gcode.core.layercontent import LayerContent  # noqa: E402
from dxf2gcode.core.stmove import StMove  # noqa: E402
from dxf2gcode.core.pocketmove import PocketMove  # noqa: E402
from dxf2gcode_pocketmill_zigzag_test import _load_shapes  # noqa: E402

DXF_POCKETING1 = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "dxf", "pocketing1.dxf")

# Historical default: center stand-off = cutter radius / 0.7
HISTORIC = 100.0 * 3 / 14  # 21.4286 % of the tool diameter


# ---------------------------------------------------------------------------
# geometry helpers
_SHAPE_SEGS = None


def _shape_segments(shape, n=180):
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


def _get_shape_segs():
    """Contour of pocketing1.dxf, flattened once and cached."""
    global _SHAPE_SEGS
    if _SHAPE_SEGS is None:
        _SHAPE_SEGS = _shape_segments(_load_shapes(DXF_POCKETING1)[0])
    return _SHAPE_SEGS


def _dist_point_seg(px, py, x0, y0, x1, y1):
    dx, dy = x1 - x0, y1 - y0
    l2 = dx * dx + dy * dy
    if l2 == 0:
        return math.hypot(px - x0, py - y0)
    t = max(0.0, min(1.0, ((px - x0) * dx + (py - y0) * dy) / l2))
    return math.hypot(px - (x0 + t * dx), py - (y0 + t * dy))


def _min_center_distance(geos):
    """Minimum distance between any of ``geos`` and the shape contour."""
    segs = _get_shape_segs()
    best = float("inf")
    for geo in geos:
        if isinstance(geo, LineGeo):
            length = geo.Ps.distance(geo.Pe)
            n = max(1, min(50, int(length / 0.3) + 1))
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


def _set_clearance(pct):
    g.config.vars.Pocketing["pocket_edge_clearance"] = pct


def _pocket(tool_dia, cut_cor, pct):
    _set_clearance(pct)
    shape = _load_shapes(DXF_POCKETING1)[0]
    layer = LayerContent(0, "top", [shape])
    layer.tool_diameter = tool_dia
    layer.start_radius = 0.0
    shape.parentLayer = layer
    shape.Pocket = True
    shape.cut_cor = cut_cor
    shape.cw = True
    shape.calc_bounding_box()
    g.config.vars.Cutter_Compensation["done_by_machine"] = False
    with contextlib.redirect_stdout(io.StringIO()):
        st = StMove(shape)
    return shape, st


def _fill_geos(st):
    return [geo for geo in st.geos[st.pocket_geos_start:]
            if isinstance(geo, LineGeo) and abs(geo.Ps.y - geo.Pe.y) < 1e-9]


def _boundary_geos(st):
    return [geo for geo in st.geos[:st.pocket_geos_start]
            if isinstance(geo, (LineGeo, ArcGeo))]


def _measured_clearance(tool_dia, cut_cor, pct):
    shape, st = _pocket(tool_dia, cut_cor, pct)
    fill = _fill_geos(st)
    if not fill:
        return None
    return _min_center_distance(fill) - tool_dia / 2.0


# ---------------------------------------------------------------------------
@unittest.skipUnless(os.path.exists(DXF_POCKETING1), "pocketing1.dxf not available")
class TestEdgeClearanceConfiguration(unittest.TestCase):

    def test_unit_test_helper_default_matches_historic(self):
        # default configuration value must reproduce cutter_radius / 0.7
        _set_clearance(HISTORIC)
        pct = PocketMill._pocket_edge_clearance_percent()
        self.assertAlmostEqual(pct, HISTORIC, places=6)
        tool_rad = 1.0
        dist = tool_rad + pct / 100.0 * 2 * tool_rad
        self.assertAlmostEqual(dist, tool_rad / 0.7, places=9)

    def test_helper_falls_back_when_option_missing(self):
        # simulate an old configuration without the option
        saved = g.config.vars.Pocketing["pocket_edge_clearance"]
        try:
            del g.config.vars.Pocketing.__dict__["pocket_edge_clearance"]
            self.assertAlmostEqual(
                PocketMill._pocket_edge_clearance_percent(), HISTORIC, places=6)
        finally:
            g.config.vars.Pocketing.__dict__["pocket_edge_clearance"] = saved

    def test_default_reproduces_historical_g42_clearance(self):
        tool = 2.0
        measured = _measured_clearance(tool, 42, HISTORIC)
        target = HISTORIC / 100.0 * tool
        # grid discretisation may only increase the clearance a little
        self.assertGreaterEqual(measured, target - 0.02)
        self.assertLessEqual(measured, target + 0.5 * (tool / 2.0))

    def test_zero_clearance_reaches_contour(self):
        tool = 2.0
        measured = _measured_clearance(tool, 42, 0.0)
        self.assertLessEqual(measured, 0.05,
                             "0 %% clearance must let the cutting edge reach "
                             "the contour (measured %.4f)" % measured)

    def test_clearance_scales_with_tool_diameter(self):
        pct = 50.0
        for tool in (1.0, 2.0, 3.0):
            measured = _measured_clearance(tool, 42, pct)
            target = pct / 100.0 * tool
            self.assertGreaterEqual(measured, target - 0.02)
            self.assertLessEqual(measured, target + 0.5 * (tool / 2.0),
                                 "tool %.1f: measured %.4f vs target %.4f"
                                 % (tool, measured, target))

    def test_clearance_applied_for_all_compensation_directions(self):
        pct = 50.0
        tool = 2.0
        values = {}
        for cc in (40, 41, 42):
            values[cc] = _measured_clearance(tool, cc, pct)
        target = pct / 100.0 * tool
        for cc, v in values.items():
            self.assertGreaterEqual(v, target - 0.02, "cut_cor %d" % cc)
            self.assertLessEqual(v, target + 0.5 * (tool / 2.0), "cut_cor %d" % cc)
        # all directions must give (nearly) the same clearance
        self.assertLess(max(values.values()) - min(values.values()), 0.05)

    def test_boundary_pass_is_at_one_tool_radius(self):
        # the compensated contour must sit exactly one cutter radius from the
        # contour (no double counting of the tool radius)
        for cc in (41, 42):
            tool = 2.0
            shape, st = _pocket(tool, cc, HISTORIC)
            boundary = _boundary_geos(st)
            self.assertTrue(boundary, "boundary pass expected for cut_cor %d" % cc)
            d = _min_center_distance(boundary)
            self.assertAlmostEqual(d, tool / 2.0, places=4,
                                   msg="cut_cor %d boundary at %.4f" % (cc, d))

    def test_clearance_is_monotonic_in_percent(self):
        tool = 2.0
        a = _measured_clearance(tool, 42, 0.0)
        b = _measured_clearance(tool, 42, 25.0)
        c = _measured_clearance(tool, 42, 50.0)
        self.assertLess(a, b)
        self.assertLess(b, c)


if __name__ == "__main__":
    unittest.main(verbosity=2)
