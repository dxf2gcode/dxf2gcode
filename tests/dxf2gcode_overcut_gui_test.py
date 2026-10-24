# -*- coding: utf-8 -*-
"""
Tests of the overcut handling in the GUI (the "Overcut" combobox).

The overcut is only possible for closed contours:
* the combobox is disabled (greyed) if the selection holds open contours only,
* in a mixed selection (open and closed contours) the setting is applied to the
  closed contours only.

Run from the repository root:

    python -m unittest discover -s tests -t tests -p "dxf2gcode_overcut_gui_test.py" -v
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
    import dxf2gcode.globals.globals as g
    from dxf2gcode.globals.config import MyConfig

    if getattr(g, "config", None) is None:
        g.folder = tempfile.mkdtemp(prefix="d2g_overcut_gui_")
        cfg = MyConfig()
        cfg.metric = 1
        g.config = cfg


_init_config()

import dxf2gcode.globals.globals as g  # noqa: E402
from dxf2gcode.Qt.QtWidgets import QApplication, QComboBox, QWidget  # noqa: E402
from dxf2gcode.gui.treehandling import TreeHandler  # noqa: E402
from dxf2gcode.core.leadmove import (OVERCUT_DEFAULT, OVERCUT_OFF,  # noqa: E402
                                     OVERCUT_ON)
from dxf2gcode.core.shape import Shape, Geos  # noqa: E402
from dxf2gcode.core.linegeo import LineGeo  # noqa: E402
from dxf2gcode.core.point import Point  # noqa: E402
from dxf2gcode.core.layercontent import LayerContent  # noqa: E402

_APP = None  # keep the QApplication alive (otherwise all widgets are deleted)


class _Scene(object):
    def __init__(self):
        self.repainted = []

    def repaint_shape(self, shape):
        self.repainted.append(shape)

    def update(self):
        pass


class _Win(object):
    def __init__(self):
        self.canvas_scene = _Scene()


class _FakeUI(object):
    pass


def _closed_shape(nr):
    shape = Shape(nr=nr, closed=True, geos=Geos([
        LineGeo(Point(0, 0), Point(10, 0)),
        LineGeo(Point(10, 0), Point(10, 10)),
        LineGeo(Point(10, 10), Point(0, 10)),
        LineGeo(Point(0, 10), Point(0, 0))]))
    shape.AnalyseAndOptimize()
    return shape


def _open_shape(nr):
    shape = Shape(nr=nr, closed=False, geos=Geos([
        LineGeo(Point(0, 0), Point(10, 0)),
        LineGeo(Point(10, 0), Point(10, 10))]))
    shape.AnalyseAndOptimize()
    return shape


class OvercutGuiTestBase(unittest.TestCase):

    def setUp(self):
        global _APP
        _APP = QApplication.instance() or QApplication([])
        g.window = _Win()
        self.th = TreeHandler.__new__(TreeHandler)
        QWidget.__init__(self.th)
        self.th.ui = _FakeUI()
        self.combo = QComboBox()
        self.combo.addItem("None", OVERCUT_OFF)
        self.combo.addItem("Overcut", OVERCUT_ON)
        self.th.ui.overcutComboBox = self.combo

        self.closed = _closed_shape(1)
        self.open = _open_shape(2)
        self.layer_closed = LayerContent(1, "CLOSED", [self.closed])
        self.layer_open = LayerContent(2, "OPEN", [self.open])
        self.closed.parentLayer = self.layer_closed
        self.open.parentLayer = self.layer_open

    def _select(self, layers, shapes):
        self.th._selectedShapesAndLayers = lambda: (list(layers), list(shapes))


class TestOvercutComboboxEnable(OvercutGuiTestBase):
    """The combobox is disabled if the selection has no closed contour."""

    def test_open_contour_only_is_not_selectable(self):
        self.assertFalse(self.th._selection_has_closed_contour(
            [self.open], [self.layer_open]))

    def test_closed_contour_is_selectable(self):
        self.assertTrue(self.th._selection_has_closed_contour(
            [self.closed], [self.layer_closed]))

    def test_a_mixed_selection_is_selectable(self):
        self.assertTrue(self.th._selection_has_closed_contour(
            [self.open, self.closed], [self.layer_open, self.layer_closed]))

    def test_layer_rows_only_use_the_shapes_of_the_layer(self):
        self.assertTrue(self.th._selection_has_closed_contour(
            [], [self.layer_closed]))
        self.assertFalse(self.th._selection_has_closed_contour(
            [], [self.layer_open]))


class TestOvercutApply(OvercutGuiTestBase):
    """In a mixed selection the overcut is applied to the closed contours."""

    def test_only_the_closed_contour_is_changed(self):
        self._select([self.layer_open, self.layer_closed],
                     [self.open, self.closed])
        self.combo.setCurrentIndex(self.combo.findData(OVERCUT_ON))
        self.th.overcutUpdate()
        self.assertEqual(self.closed.overcut_enabled, OVERCUT_ON)
        # The open contour is not touched (it stays on the standard).
        self.assertEqual(self.open.overcut_enabled, OVERCUT_DEFAULT)

    def test_the_contours_of_the_same_layer_are_separated(self):
        # An open and a closed contour in the SAME layer: enabling the
        # overcut changes only the closed contour.
        closed = _closed_shape(3)
        closed.parentLayer = self.layer_open
        self.layer_open.shapes.append(closed)
        self._select([self.layer_open], [self.open, closed])
        self.combo.setCurrentIndex(self.combo.findData(OVERCUT_ON))
        self.th.overcutUpdate()
        self.assertEqual(closed.overcut_enabled, OVERCUT_ON)
        self.assertEqual(self.open.overcut_enabled, OVERCUT_DEFAULT)
        # The layer itself is not changed.
        self.assertEqual(self.layer_open.overcut_enabled, OVERCUT_DEFAULT)

    def test_an_open_contour_only_selection_changes_nothing(self):
        self._select([self.layer_open], [self.open])
        self.combo.setCurrentIndex(self.combo.findData(OVERCUT_ON))
        self.th.overcutUpdate()
        self.assertEqual(self.open.overcut_enabled, OVERCUT_DEFAULT)

    def test_the_layer_of_the_closed_contour_is_repainted(self):
        self._select([self.layer_open, self.layer_closed],
                     [self.open, self.closed])
        self.combo.setCurrentIndex(self.combo.findData(OVERCUT_ON))
        self.th.overcutUpdate()
        self.assertIn(self.closed, g.window.canvas_scene.repainted)

    def test_the_closed_contours_of_the_selection_are_found(self):
        self._select([self.layer_open, self.layer_closed],
                     [self.open, self.closed])
        self.assertEqual(self.th._closed_contours_of_selection(), [self.closed])
        self._select([self.layer_open], [self.open])
        self.assertEqual(self.th._closed_contours_of_selection(), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
