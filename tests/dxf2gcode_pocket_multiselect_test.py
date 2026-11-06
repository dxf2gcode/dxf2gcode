# -*- coding: utf-8 -*-
"""
Regression tests for the pocket-milling toggle of the canvas context menu
(gui/canvas.py :: MyDropDownMenu.setPocket).

A multi-selection must receive ONE uniform state (all on / all off); the old
implementation inverted each selected shape individually, leaving a mixed
selection inconsistent. Uses real Qt objects (QMenu / QAction) headless.

Run from the repository root:

    python -m unittest discover -s tests -t tests -p "dxf2gcode_pocket_multiselect_test.py" -v
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
        g.folder = tempfile.mkdtemp(prefix="d2g_pocket_test_")
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
from dxf2gcode.presentation.qt.qt_compat.QtWidgets import QApplication, QMenu  # noqa: E402
from dxf2gcode.presentation.qt.qt_compat.QtGui import QAction  # noqa: E402
from dxf2gcode.presentation.qt.canvas import MyDropDownMenu  # noqa: E402
from dxf2gcode.domain.project.shape import Shape, Geos  # noqa: E402
from dxf2gcode.domain.geometry.linegeo import LineGeo  # noqa: E402
from dxf2gcode.domain.geometry.point import Point  # noqa: E402

_APP = None


class _Scene(object):
    def repaint_shape(self, shape):
        pass

    def update(self):
        pass


class _TreeHandler(object):
    def __init__(self):
        self.calls = []

    def updatePocketMill(self, shape, enable):
        self.calls.append((shape.nr, enable))


class _Win(object):
    def __init__(self, th):
        self.TreeHandler = th
        self.canvas_scene = _Scene()


def _mk_shape(nr):
    s = Shape(nr=nr, closed=True, geos=Geos([
        LineGeo(Point(0, 0), Point(10, 0)),
        LineGeo(Point(10, 0), Point(10, 10)),
        LineGeo(Point(10, 10), Point(0, 10)),
        LineGeo(Point(0, 10), Point(0, 0))]), config=g.config)
    return s


def _make_menu(shapes):
    global _APP
    _APP = QApplication.instance() or QApplication([])
    th = _TreeHandler()
    g.window = _Win(th)
    menu = MyDropDownMenu.__new__(MyDropDownMenu)
    QMenu.__init__(menu)
    menu.selectedItems = shapes
    menu.canvas_scene = _Scene()
    menu.PocketAction = QAction()
    menu.PocketAction.setCheckable(True)
    return menu, th


class TestPocketMultiSelection(unittest.TestCase):

    def test_single_selection_toggles_on_and_off(self):
        s0 = _mk_shape(0)
        menu, th = _make_menu([s0])
        menu.setPocket()
        self.assertTrue(s0.Pocket)
        self.assertTrue(menu.PocketAction.isChecked())
        menu.setPocket()
        self.assertFalse(s0.Pocket)
        self.assertFalse(menu.PocketAction.isChecked())

    def test_mixed_multi_selection_sets_all_on(self):
        s0, s1, s2 = _mk_shape(0), _mk_shape(1), _mk_shape(2)
        s0.Pocket = True                      # already enabled
        menu, th = _make_menu([s0, s1, s2])
        menu.setPocket()
        self.assertEqual([s0.Pocket, s1.Pocket, s2.Pocket], [True, True, True])
        self.assertTrue(menu.PocketAction.isChecked())
        # every selected shape got the same target state
        self.assertEqual(sorted(th.calls), [(0, True), (1, True), (2, True)])

    def test_all_on_multi_selection_sets_all_off(self):
        s0, s1 = _mk_shape(0), _mk_shape(1)
        s0.Pocket = True
        s1.Pocket = True
        menu, th = _make_menu([s0, s1])
        menu.setPocket()
        self.assertEqual([s0.Pocket, s1.Pocket], [False, False])
        self.assertFalse(menu.PocketAction.isChecked())

    def test_extending_selection_does_not_disable_enabled_shape(self):
        s0, s1 = _mk_shape(0), _mk_shape(1)
        s0.Pocket = True                      # enabled first, then s1 added
        menu, th = _make_menu([s0, s1])
        menu.setPocket()
        self.assertTrue(s0.Pocket)            # NOT disabled
        self.assertTrue(s1.Pocket)
        self.assertTrue(menu.PocketAction.isChecked())

    def test_updatePocketMill_called_once_per_shape(self):
        s0, s1, s2 = _mk_shape(0), _mk_shape(1), _mk_shape(2)
        menu, th = _make_menu([s0, s1, s2])
        menu.setPocket()
        self.assertEqual(len(th.calls), 3)    # no duplicate / per-item toggling

    def test_empty_selection_is_harmless(self):
        menu, th = _make_menu([])
        menu.setPocket()                      # must not raise
        self.assertEqual(th.calls, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
