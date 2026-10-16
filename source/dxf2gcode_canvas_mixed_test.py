# -*- coding: utf-8 -*-
"""
Regression tests for the mixed-state display of the canvas context-menu
actions (gui/canvas.py :: MyDropDownMenu).

QAction has no native PartiallyChecked display, so a mixed selection is shown
by an extended label ("(mixed selection)"); the action is then not checked.
Uses real Qt objects (QMenu / QAction) headless.

Run from the ``source`` directory:

    python -m unittest dxf2gcode_canvas_mixed_test -v
"""
from __future__ import absolute_import

import os
import tempfile
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def _init_config():
    import dxf2gcode.globals.globals as g
    from dxf2gcode.globals.config import MyConfig

    if getattr(g, "config", None) is None:
        g.folder = tempfile.mkdtemp(prefix="d2g_canvas_test_")
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
from dxf2gcode.Qt.QtWidgets import QApplication, QMenu  # noqa: E402
from dxf2gcode.Qt.QtGui import QAction  # noqa: E402
from dxf2gcode.gui.canvas import MyDropDownMenu  # noqa: E402
from dxf2gcode.core.shape import Shape, Geos  # noqa: E402
from dxf2gcode.core.linegeo import LineGeo  # noqa: E402
from dxf2gcode.core.point import Point  # noqa: E402

_APP = None


class _Scene(object):
    def repaint_shape(self, shape):
        pass

    def update(self):
        pass


class _TreeHandler(object):
    def __init__(self):
        self.calls = []

    def updateDrill(self, shape, enable):
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
        LineGeo(Point(0, 10), Point(0, 0))]))
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
    menu.PocketAction = QAction("Pocket Mill")
    menu.PocketAction.setCheckable(True)
    menu.DrillAction = QAction("Drill Bore")
    menu.DrillAction.setCheckable(True)
    menu.noCompAction = QAction("G40 No Compensation")
    menu.noCompAction.setCheckable(True)
    menu.leCompAction = QAction("G41 Left Compensation")
    menu.leCompAction.setCheckable(True)
    menu.reCompAction = QAction("G42 Right Compensation")
    menu.reCompAction.setCheckable(True)
    menu.compMenuAction = QAction("Cutter Compensation")
    return menu, th


class TestSelectionBoolState(unittest.TestCase):

    def test_all_off(self):
        m, _ = _make_menu([_mk_shape(0), _mk_shape(1)])
        self.assertEqual(m._selectionBoolState("Pocket"), "off")

    def test_all_on(self):
        s0, s1 = _mk_shape(0), _mk_shape(1)
        s0.Pocket = True
        s1.Pocket = True
        m, _ = _make_menu([s0, s1])
        self.assertEqual(m._selectionBoolState("Pocket"), "on")

    def test_mixed(self):
        s0, s1 = _mk_shape(0), _mk_shape(1)
        s0.Pocket = True
        m, _ = _make_menu([s0, s1])
        self.assertEqual(m._selectionBoolState("Pocket"), "mixed")


class TestActionLabel(unittest.TestCase):
    """Mixed state must be shown by an icon, never by extra text."""

    def test_uniform_on_checked_no_icon(self):
        s0, s1 = _mk_shape(0), _mk_shape(1)
        s0.Pocket = True
        s1.Pocket = True
        m, _ = _make_menu([s0, s1])
        m._updateBoolActionState(m.PocketAction, "Pocket")
        self.assertTrue(m.PocketAction.isChecked())
        self.assertEqual(m.PocketAction.text(), "Pocket Mill")   # unchanged
        self.assertTrue(m.PocketAction.icon().isNull())          # no mixed icon

    def test_uniform_off_unchecked_no_icon(self):
        m, _ = _make_menu([_mk_shape(0), _mk_shape(1)])
        m._updateBoolActionState(m.PocketAction, "Pocket")
        self.assertFalse(m.PocketAction.isChecked())
        self.assertEqual(m.PocketAction.text(), "Pocket Mill")
        self.assertTrue(m.PocketAction.icon().isNull())

    def test_mixed_has_icon_and_unchanged_text(self):
        s0, s1 = _mk_shape(0), _mk_shape(1)
        s0.Pocket = True
        m, _ = _make_menu([s0, s1])
        m._updateBoolActionState(m.PocketAction, "Pocket")
        self.assertFalse(m.PocketAction.isChecked())
        self.assertEqual(m.PocketAction.text(), "Pocket Mill")   # unchanged
        self.assertNotIn("mixed", m.PocketAction.text().lower())
        self.assertFalse(m.PocketAction.icon().isNull())         # mixed icon

    def test_drill_mixed_icon_and_text(self):
        s0, s1 = _mk_shape(0), _mk_shape(1)
        s1.Drill = True
        m, _ = _make_menu([s0, s1])
        m._updateBoolActionState(m.DrillAction, "Drill")
        self.assertFalse(m.DrillAction.isChecked())
        self.assertEqual(m.DrillAction.text(), "Drill Bore")
        self.assertNotIn("mixed", m.DrillAction.text().lower())
        self.assertFalse(m.DrillAction.icon().isNull())

    def test_switching_back_clears_mixed_icon(self):
        s0, s1 = _mk_shape(0), _mk_shape(1)
        s0.Pocket = True                              # mixed
        m, _ = _make_menu([s0, s1])
        m._updateBoolActionState(m.PocketAction, "Pocket")
        self.assertFalse(m.PocketAction.icon().isNull())
        s1.Pocket = True                              # now uniform on
        m._updateBoolActionState(m.PocketAction, "Pocket")
        self.assertTrue(m.PocketAction.icon().isNull())   # stale icon cleared


class TestCutterCompDirection(unittest.TestCase):

    def test_uniform_no_comp(self):
        s0, s1 = _mk_shape(0), _mk_shape(1)
        s0.cut_cor = 40
        s1.cut_cor = 40
        m, _ = _make_menu([s0, s1])
        self.assertEqual(m.calcMenuDir(), 0)

    def test_uniform_left(self):
        s0, s1 = _mk_shape(0), _mk_shape(1)
        s0.cut_cor = 41
        s1.cut_cor = 41
        m, _ = _make_menu([s0, s1])
        self.assertEqual(m.calcMenuDir(), 1)

    def test_uniform_right(self):
        s0, s1 = _mk_shape(0), _mk_shape(1)
        s0.cut_cor = 42
        s1.cut_cor = 42
        m, _ = _make_menu([s0, s1])
        self.assertEqual(m.calcMenuDir(), 2)

    def test_mixed_returns_minus_one(self):
        s0, s1 = _mk_shape(0), _mk_shape(1)
        s0.cut_cor = 41
        s1.cut_cor = 42
        m, _ = _make_menu([s0, s1])
        self.assertEqual(m.calcMenuDir(), -1)


class TestDrillGroupAction(unittest.TestCase):

    def test_group_sets_all_on(self):
        s0, s1, s2 = _mk_shape(0), _mk_shape(1), _mk_shape(2)
        m, th = _make_menu([s0, s1, s2])
        m.setDrill()
        self.assertEqual([s0.Drill, s1.Drill, s2.Drill], [True, True, True])
        self.assertTrue(m.DrillAction.isChecked())
        self.assertEqual(sorted(th.calls), [(0, True), (1, True), (2, True)])

    def test_mixed_becomes_all_on(self):
        s0, s1 = _mk_shape(0), _mk_shape(1)
        s0.Drill = True                              # mixed
        m, th = _make_menu([s0, s1])
        m.setDrill()
        self.assertTrue(s0.Drill)                    # not disabled
        self.assertTrue(s1.Drill)
        self.assertTrue(m.DrillAction.isChecked())

    def test_all_on_becomes_all_off(self):
        s0, s1 = _mk_shape(0), _mk_shape(1)
        s0.Drill = True
        s1.Drill = True
        m, th = _make_menu([s0, s1])
        m.setDrill()
        self.assertEqual([s0.Drill, s1.Drill], [False, False])
        self.assertFalse(m.DrillAction.isChecked())


class TestCutterCompIcon(unittest.TestCase):
    """Mixed cutter compensation is shown by the submenu icon, text unchanged."""

    def _menu(self, cut_cors):
        shapes = [_mk_shape(i) for i in range(len(cut_cors))]
        for s, cc in zip(shapes, cut_cors):
            s.cut_cor = cc
        return _make_menu(shapes)[0]

    def test_uniform_no_checked_no_icon(self):
        m = self._menu([40, 40])
        m.checkMenuDir(m.calcMenuDir())
        self.assertTrue(m.compMenuAction.icon().isNull())
        self.assertTrue(m.noCompAction.isChecked())
        self.assertFalse(m.leCompAction.isChecked())
        self.assertFalse(m.reCompAction.isChecked())

    def test_uniform_left_no_icon(self):
        m = self._menu([41, 41])
        m.checkMenuDir(m.calcMenuDir())
        self.assertTrue(m.compMenuAction.icon().isNull())
        self.assertTrue(m.leCompAction.isChecked())

    def test_uniform_right_no_icon(self):
        m = self._menu([42, 42])
        m.checkMenuDir(m.calcMenuDir())
        self.assertTrue(m.compMenuAction.icon().isNull())
        self.assertTrue(m.reCompAction.isChecked())

    def test_mixed_shows_icon_and_none_checked(self):
        m = self._menu([41, 42])
        m.checkMenuDir(m.calcMenuDir())
        self.assertFalse(m.compMenuAction.icon().isNull())     # mixed icon
        self.assertFalse(m.noCompAction.isChecked())           # NOT shown as No
        self.assertFalse(m.leCompAction.isChecked())
        self.assertFalse(m.reCompAction.isChecked())
        self.assertEqual(m.compMenuAction.text(), "Cutter Compensation")
        self.assertNotIn("mixed", m.compMenuAction.text().lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)
