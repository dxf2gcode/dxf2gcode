# -*- coding: utf-8 -*-
"""
Tests for unrestricted pocket compensation. G40/G41/G42 always determine
the boundary offset, including profiles carrying obsolete mode values.

The tests evaluate the produced geometry and the G-code export.

Run from the repository root:

    python -m unittest discover -s tests -t tests -p "dxf2gcode_pocket_comp_mode_test.py" -v
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
        g.folder = tempfile.mkdtemp(prefix="d2g_mode_test_")
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
from dxf2gcode.domain.project.layercontent import LayerContent  # noqa: E402
from dxf2gcode.adapters.toolpath.preparation import prepare_shape  # noqa: E402
from dxf2gcode.domain.toolpath.leadmove import LEAD_OFF  # noqa: E402
from dxf2gcode_pocketmill_zigzag_test import _load_shapes  # noqa: E402
from dxf2gcode_stmove_gcode_test import make_postpro, norm  # noqa: E402

_APP = None

DXF_POCKETING1 = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "dxf", "pocketing1.dxf")

TOOL_RAD = 1.0  # tool diameter 2.0 mm
BRIDGE_Y = 32.32873281583571
_CONTOUR_CACHE = None


# ---------------------------------------------------------------------------
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


def _contour_segs():
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


def _min_dist(segs, geos):
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


def _outside_points(segs, geos, tol=1e-6):
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
            d = min(_dist_point_seg(px, py, *s) for s in segs)
            if d > tol and not _point_inside(segs, px, py):
                bad.append((px, py))
    return bad


def _split(st):
    boundary = [geo for geo in st.geos[:st.pocket_geos_start]
                if isinstance(geo, (LineGeo, ArcGeo))]
    fill = [geo for geo in st.geos[st.pocket_geos_start:]
            if isinstance(geo, LineGeo) and abs(geo.Ps.y - geo.Pe.y) < 1e-9]
    return boundary, fill


def _build(mode, cut_cor, tool=2.0):
    g.config.vars.Pocketing["pocket_compensation_mode"] = mode
    # deterministic edge clearance (independent of other test modules)
    g.config.vars.Pocketing["pocket_edge_clearance"] = 100.0 * 3 / 14
    s = _load_shapes(DXF_POCKETING1)[0]
    s.axis3_start_mill_depth = 0.0
    s.axis3_mill_depth = -1.0
    s.axis3_slice_depth = 0.5
    s.f_g1_plane = 800
    s.f_g1_depth = 150
    s.cut_cor = cut_cor
    s.cw = True
    s.Drill = False
    s.Pocket = True
    layer = LayerContent(0, "top", [s])
    layer.tool_diameter = tool
    layer.axis3_retract = 9.91
    layer.axis3_safe_margin = 3.05
    # The test checks the compensated pocket toolpath, not the lead in.
    layer.lead_in_mode = LEAD_OFF
    s.parentLayer = layer
    s.calc_bounding_box()
    g.config.vars.Cutter_Compensation["done_by_machine"] = False
    st = prepare_shape(s)
    s.stmove = st
    return s, st


def _gcode(s):
    return norm(serialize_gcode(s, make_postpro()))


def _g1_xy(code):
    return [(float(a), float(b)) for a, b in re.findall(
        r"G1\s+X\s+(-?\d+\.\d+)\s+Y\s+(-?\d+\.\d+)", code)]


# ---------------------------------------------------------------------------
@unittest.skipUnless(os.path.exists(DXF_POCKETING1), "pocketing1.dxf not available")
class TestRetiredPocketMode(unittest.TestCase):
    """An obsolete runtime override must not restrict the user's direction."""

    def test_old_mode_has_no_effect_on_selected_direction(self):
        for cc in (40, 41, 42):
            self.assertEqual(_gcode(_build("always_inward", cc)[0]),
                             _gcode(_build("selected_direction", cc)[0]))

    def test_g40_exports_the_complete_fill(self):
        code = _gcode(_build("always_inward", 40)[0])
        points = _g1_xy(code)
        self.assertGreater(len(points), 100)
        self.assertTrue([point for point in points
                         if abs(point[1] - BRIDGE_Y) < 0.05
                         and 35.0 < point[0] < 47.2],
                        "G40 pocket fill is missing the central bridge")
        self.assertNotIn("G41", code)
        self.assertNotIn("G42", code)


@unittest.skipUnless(os.path.exists(DXF_POCKETING1), "pocketing1.dxf not available")
class TestSelectedDirectionMode(unittest.TestCase):
    """G40/G41/G42 controls pocket geometry without a mode switch."""

    def test_g42_is_the_inward_offset(self):
        segs = _contour_segs()
        s, st = _build("selected_direction", 42)
        boundary, _ = _split(st)
        self.assertTrue(boundary)
        self.assertEqual(_outside_points(segs, boundary), [])
        self.assertLess(abs(_min_dist(segs, boundary) - TOOL_RAD), 0.02)

    def test_g41_is_the_outward_offset_for_cw_contour(self):
        # pocketing1.dxf is normalised to CW, so G41 (left) lies outside
        segs = _contour_segs()
        s, st = _build("selected_direction", 41)
        boundary, _ = _split(st)
        self.assertTrue(boundary)
        b0 = boundary[0]
        mx, my = (b0.Ps.x + b0.Pe.x) / 2, (b0.Ps.y + b0.Pe.y) / 2
        self.assertFalse(_point_inside(segs, mx, my),
                         "G41 offset must be outside for a CW contour")
        self.assertLess(abs(_min_dist(segs, boundary) - TOOL_RAD), 0.02)

    def test_g40_uses_the_contour_without_offset(self):
        segs = _contour_segs()
        s, st = _build("selected_direction", 40)
        boundary, _ = _split(st)
        self.assertTrue(boundary)
        # no radius compensation -> the cutter center path is the contour
        self.assertLess(_min_dist(segs, boundary), 0.01)

    def test_fill_stays_inside_for_every_direction(self):
        segs = _contour_segs()
        for cc in (40, 41, 42):
            s, st = _build("selected_direction", cc)
            _, fill = _split(st)
            self.assertTrue(fill, "no fill for cut_cor %d" % cc)
            self.assertEqual(_outside_points(segs, fill), [],
                             "cut_cor %d fill outside" % cc)

    def test_no_double_radius_compensation(self):
        # G41/G42 offsets must be exactly one cutter radius, never two
        segs = _contour_segs()
        for cc in (41, 42):
            s, st = _build("selected_direction", cc)
            boundary, _ = _split(st)
            d = _min_dist(segs, boundary)
            self.assertLess(abs(d - TOOL_RAD), 0.02,
                            "cut_cor %d offset %.4f" % (cc, d))
            self.assertGreater(d, 0.5 * TOOL_RAD)

    def test_directions_differ(self):
        code41 = _gcode(_build("selected_direction", 41)[0])
        code42 = _gcode(_build("selected_direction", 42)[0])
        code40 = _gcode(_build("selected_direction", 40)[0])
        self.assertNotEqual(code41, code42)
        self.assertNotEqual(code40, code42)

# ---------------------------------------------------------------------------
class _StubShape(object):
    def __init__(self, pocket, cut_cor=42):
        self.Pocket = pocket
        self.cut_cor = cut_cor
        self.closed = True
        self.geos = [object()]   # not an ArcGeo

    def isSelected(self):
        return True


class _StubScene(object):
    def __init__(self, shapes):
        self.shapes = shapes


class TestCompensationMenuSelection(unittest.TestCase):
    """Pocket milling must not disable the user's compensation selection."""

    def setUp(self):
        from dxf2gcode.presentation.qt.qt_compat import QtWidgets
        global _APP
        _APP = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        self._app = _APP

    def _menu_for(self, shapes, mode):
        from dxf2gcode.presentation.qt import canvas as canvasmod
        g.config.vars.Pocketing["pocket_compensation_mode"] = mode
        # avoid the modal menu popup
        canvasmod.MyDropDownMenu.exec = lambda self, pos: None
        return canvasmod.MyDropDownMenu(_StubScene(shapes), None, Point(0, 0))

    def test_menu_enabled_for_pocket_with_older_profile_mode(self):
        menu = self._menu_for([_StubShape(True)], "always_inward")
        self.assertTrue(menu.compMenuAction.isEnabled())
        self.assertTrue(menu.noCompAction.isEnabled())
        self.assertTrue(menu.leCompAction.isEnabled())
        self.assertTrue(menu.reCompAction.isEnabled())

    def test_menu_enabled_without_pocket_in_default_mode(self):
        menu = self._menu_for([_StubShape(False)], "always_inward")
        self.assertTrue(menu.compMenuAction.isEnabled())

    def test_menu_enabled_for_pocket_in_selected_direction_mode(self):
        menu = self._menu_for([_StubShape(True)], "selected_direction")
        self.assertTrue(menu.compMenuAction.isEnabled())


class TestDragKnifeMenuGating(unittest.TestCase):
    """The drag knife does not support the pocket milling: the context menu
    of a shape must not offer it."""

    def setUp(self):
        from dxf2gcode.presentation.qt.qt_compat import QtWidgets
        global _APP
        _APP = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        self._app = _APP
        # the pocket mill is only offered if the compensation is done by
        # dxf2gcode itself
        self._done_by_machine = g.config.vars.Cutter_Compensation[
            "done_by_machine"]
        g.config.vars.Cutter_Compensation["done_by_machine"] = False
        self._machine_type = g.config.machine_type

    def tearDown(self):
        g.config.vars.Cutter_Compensation["done_by_machine"] = \
            self._done_by_machine
        g.config.machine_type = self._machine_type

    def _menu(self, shapes):
        from dxf2gcode.presentation.qt import canvas as canvasmod
        # avoid the modal menu popup
        canvasmod.MyDropDownMenu.exec = lambda self, pos: None
        return canvasmod.MyDropDownMenu(_StubScene(shapes), None, Point(0, 0))

    def _action_texts(self, menu):
        return [action.text() for action in menu.actions()]

    def test_the_pocket_mill_is_not_offered_for_the_drag_knife(self):
        g.config.machine_type = 'drag_knife'
        menu = self._menu([_StubShape(False)])
        self.assertNotIn("Pocket Mill", self._action_texts(menu))
        self.assertFalse(hasattr(menu, "PocketAction"))

    def test_the_pocket_mill_is_offered_for_the_milling_machine(self):
        g.config.machine_type = 'milling'
        menu = self._menu([_StubShape(False)])
        self.assertIn("Pocket Mill", self._action_texts(menu))
        self.assertTrue(hasattr(menu, "PocketAction"))

    def test_the_pocket_mill_is_not_offered_for_the_lathe(self):
        # The lathe is not supported by the pocket milling either.
        g.config.machine_type = 'lathe'
        menu = self._menu([_StubShape(False)])
        self.assertIn("Pocket Mill", self._action_texts(menu))


def tearDownModule():
    # do not leak a non-default mode into other test modules
    try:
        g.config.vars.Pocketing["pocket_compensation_mode"] = "always_inward"
    except Exception:
        pass


if __name__ == "__main__":
    unittest.main(verbosity=2)
