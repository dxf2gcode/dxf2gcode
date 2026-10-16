# -*- coding: utf-8 -*-
"""
Regression tests for the offset computation status of offShapeClass and the
differentiated messages in StMove.make_start_moves.

The test run needs no GUI: it uses the offscreen Qt platform and a minimal
in-memory configuration. Run from the ``source`` directory:

    python -m unittest dxf2gcode_offset_status_test -v
"""
from __future__ import absolute_import

import os
import tempfile
import logging
import unittest
from unittest import mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def _init_config():
    import dxf2gcode.globals.globals as g
    from dxf2gcode.globals.config import MyConfig

    if getattr(g, "config", None) is None:
        g.folder = tempfile.mkdtemp(prefix="d2g_status_test_")
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
    # The offset is only computed when the compensation is NOT done by the
    # machine (GUI checkbox). Enable the software compensation path.
    try:
        g.config.vars.Cutter_Compensation["done_by_machine"] = False
    except Exception:
        pass
    logging.getLogger("core.shapeoffset").setLevel(logging.CRITICAL)


_init_config()

import dxf2gcode.core.shapeoffset as so
import dxf2gcode.core.stmove as stmove
from dxf2gcode.core.shapeoffset import offShapeClass
from dxf2gcode.core.shape import Shape, Geos
from dxf2gcode.core.linegeo import LineGeo
from dxf2gcode.core.point import Point


def _square(size=10.0, nr=0):
    s = Shape(nr=nr, closed=True, geos=Geos([
        LineGeo(Point(0, 0), Point(size, 0)),
        LineGeo(Point(size, 0), Point(size, size)),
        LineGeo(Point(size, size), Point(0, size)),
        LineGeo(Point(0, size), Point(0, 0))]))
    s.AnalyseAndOptimize()
    return s


def _vanishing_square():
    """A closed contour whose offset fully collapses for a large tool."""
    for size, offs in ((1.0, 5.0), (0.5, 2.0), (2.0, 5.0)):
        o = offShapeClass(parent=_square(size), offset=offs, offtype="in")
        if o.offset_status == "vanished":
            return o
    return None


class TestOffsetStatus(unittest.TestCase):

    def test_ok(self):
        o = offShapeClass(parent=_square(10.0), offset=1.0, offtype="in")
        self.assertEqual(o.offset_status, "ok")
        self.assertTrue(o.rawoff)

    def test_vanished(self):
        o = _vanishing_square()
        self.assertIsNotNone(o, "no vanishing test geometry found")
        self.assertEqual(o.offset_status, "vanished")
        self.assertEqual(len(o.rawoff), 0)

    def test_walk_overflow(self):
        with mock.patch.object(offShapeClass, "PairWiseInterferenceDetection",
                               return_value=(None, None)):
            o = offShapeClass(parent=_square(10.0), offset=1.0, offtype="in")
        self.assertEqual(o.offset_status, "walk_overflow")
        self.assertNotEqual(o.offset_status, "vanished")

    def test_no_intersection(self):
        with mock.patch.object(so.OffLineGeo, "find_inter_point",
                               return_value=None), \
             mock.patch.object(so.OffArcGeo, "find_inter_point",
                               return_value=None):
            o = offShapeClass(parent=_square(10.0), offset=1.0, offtype="in")
        self.assertEqual(o.offset_status, "no_intersection")
        self.assertNotEqual(o.offset_status, "vanished")

    def test_exception(self):
        with mock.patch.object(offShapeClass, "PairWiseInterferenceDetection",
                               side_effect=RuntimeError("boom")):
            o = offShapeClass(parent=_square(10.0), offset=1.0, offtype="in")
        self.assertEqual(o.offset_status, "exception")
        self.assertNotEqual(o.offset_status, "vanished")

    def test_unknown_empty(self):
        with mock.patch.object(offShapeClass, "make_segment_types",
                               lambda self: None):
            o = offShapeClass(parent=_square(10.0), offset=1.0, offtype="in")
        self.assertEqual(o.offset_status, "unknown")
        self.assertEqual(len(o.rawoff), 0)
        self.assertNotEqual(o.offset_status, "vanished")

    def test_multiple_contours_independent(self):
        good = offShapeClass(parent=_square(10.0), offset=1.0, offtype="in")
        bad = _vanishing_square()
        self.assertEqual(good.offset_status, "ok")
        self.assertTrue(good.rawoff)
        self.assertIsNotNone(bad)
        self.assertEqual(bad.offset_status, "vanished")
        self.assertEqual(len(bad.rawoff), 0)


class _FakeLayer(object):
    start_radius = 0.0
    tool_diameter = 3.05

    def getToolRadius(self):
        return self.tool_diameter / 2.0


class _FakeShape(object):
    def __init__(self, pocket=False):
        self.nr = 5
        self.Drill = False
        self.cut_cor = 41
        self.cw = True
        self.Pocket = pocket
        self.parentLayer = _FakeLayer()


class _FakeOff(object):
    def __init__(self, status):
        self.rawoff = []
        self.loops = []
        self.offset_status = status


class _Capture(logging.Handler):
    def __init__(self):
        logging.Handler.__init__(self)
        self.records = []

    def emit(self, record):
        self.records.append((record.levelname, record.getMessage()))


class TestStMoveMessages(unittest.TestCase):

    def _run(self, status):
        capture = _Capture()
        root = logging.getLogger()
        root.addHandler(capture)
        old = stmove.offShapeClass
        stmove.offShapeClass = \
            lambda parent=None, offset=1, offtype='in': _FakeOff(status)
        try:
            m = stmove.StMove.__new__(stmove.StMove)
            m.shape = _FakeShape()
            m.start = Point(0, 0)
            m.angle = 0.0
            m.end = m.start
            m.geos = Geos([])
            m.pocket_geos_start = 0
            m.make_start_moves()
        finally:
            stmove.offShapeClass = old
            root.removeHandler(capture)
        return capture.records

    def _has(self, recs, level, needle):
        return any(lv == level and needle in msg for lv, msg in recs)

    def test_vanished_warns_not_error(self):
        recs = self._run("vanished")
        self.assertTrue(self._has(recs, "WARNING", "cannot be milled"))
        self.assertFalse(any(lv == "ERROR" for lv, _ in recs))

    def test_overflow_error_with_reason(self):
        self.assertTrue(self._has(self._run("walk_overflow"), "ERROR",
                                  "walk_overflow"))

    def test_no_intersection_error_with_reason(self):
        self.assertTrue(self._has(self._run("no_intersection"), "ERROR",
                                  "no_intersection"))

    def test_exception_error_with_reason(self):
        self.assertTrue(self._has(self._run("exception"), "ERROR",
                                  "exception"))

    def test_unknown_keeps_safe_message(self):
        self.assertTrue(self._has(self._run(None), "ERROR",
                                  "will NOT be milled"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
