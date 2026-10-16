# -*- coding: utf-8 -*-
"""
Regression tests for the multi-selection handling of the "Optimal path"
(TSP) checkbox column, using the REAL TreeHandler and a real Qt item model /
QTreeView (headless, offscreen platform).

They cover the actual GUI paths that change the checkbox:
- a direct checkbox click (the path that previously only changed one row),
- the "O" shortcut and the context menu actions,
for single and mixed multi-selections, and verify the consistency between the
visible checkbox state and shape.send_to_TSP.

Run from the ``source`` directory:

    python -m unittest dxf2gcode_tree_multiselect_test -v
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
        g.folder = tempfile.mkdtemp(prefix="d2g_ms_test_")
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
from dxf2gcode.Qt.QtWidgets import QApplication, QTreeView, QWidget  # noqa: E402
from dxf2gcode.Qt import QtCore  # noqa: E402
from dxf2gcode.gui.treehandling import TreeHandler  # noqa: E402
from dxf2gcode.core.shape import Shape, Geos  # noqa: E402
from dxf2gcode.core.linegeo import LineGeo  # noqa: E402
from dxf2gcode.core.point import Point  # noqa: E402
from dxf2gcode.core.layercontent import LayerContent  # noqa: E402

_CHECKED = QtCore.Qt.CheckState.Checked
_UNCHECKED = QtCore.Qt.CheckState.Unchecked

_APP = None  # keep the QApplication alive (otherwise all widgets are deleted)


class _Scene(object):
    def update(self):
        pass


class _Win(object):
    canvas_scene = _Scene()


def _mk_shape(nr, size=10.0):
    s = Shape(nr=nr, closed=True, geos=Geos([
        LineGeo(Point(0, 0), Point(size, 0)),
        LineGeo(Point(size, 0), Point(size, size)),
        LineGeo(Point(size, size), Point(0, size)),
        LineGeo(Point(0, size), Point(0, 0))]))
    s.AnalyseAndOptimize()
    return s


class _FakeUI(object):
    pass


class MultiSelectHarness(object):
    """Builds a real TreeHandler with a real QTreeView and 3 shapes."""

    def __init__(self, n=3):
        global _APP
        _APP = QApplication.instance() or QApplication([])
        g.window = _Win()
        self.shapes = [_mk_shape(i) for i in range(n)]
        self.layer = LayerContent(0, "L", self.shapes)
        for s in self.shapes:
            s.parentLayer = self.layer

        self.th = TreeHandler.__new__(TreeHandler)
        QWidget.__init__(self.th)
        self.th.auto_update_export_order = False
        self.th.layer_item_model = None
        self.th.entity_item_model = None
        self.view = QTreeView()
        self.th.ui = _FakeUI()
        self.th.ui.layersShapesTreeView = self.view
        self.th.layers_list = [self.layer]
        self.th.buildLayerTree([self.layer])
        self.model = self.th.layer_item_model

    def col3(self, shape):
        idx = self.th.findLayerItemIndexFromShape(shape)
        return self.model.itemFromIndex(idx.sibling(idx.row(), 3))

    def state(self):
        return [(s.send_to_TSP,
                 self.col3(s).checkState() == _CHECKED) for s in self.shapes]

    def select_all(self):
        sel = self.view.selectionModel()
        sel.clearSelection()
        for s in self.shapes:
            s.setSelected(True)
            idx = self.th.findLayerItemIndexFromShape(s)
            sel.select(idx, QtCore.QItemSelectionModel.SelectionFlag.Select |
                       QtCore.QItemSelectionModel.SelectionFlag.Rows)

    def clear_selection(self):
        self.view.selectionModel().clearSelection()
        for s in self.shapes:
            s.setSelected(False)

    def set_mixed_state(self, enabled_nrs):
        """Mixed state without a selection, then select all."""
        self.clear_selection()
        for s in self.shapes:
            s.setToolPathOptimized(s.nr in enabled_nrs)
            self.col3(s).setCheckState(_CHECKED if s.nr in enabled_nrs
                                       else _UNCHECKED)
        self.select_all()


class TestOptimalPathMultiSelection(unittest.TestCase):

    def setUp(self):
        self.h = MultiSelectHarness(3)

    # ---- single selection ------------------------------------------------
    def test_single_selection_checkbox_click_toggles_only_that_shape(self):
        self.h.clear_selection()
        s1 = self.h.shapes[1]
        idx = self.h.th.findLayerItemIndexFromShape(s1)
        self.h.view.selectionModel().select(
            idx, QtCore.QItemSelectionModel.SelectionFlag.Select |
            QtCore.QItemSelectionModel.SelectionFlag.Rows)
        self.h.col3(s1).setCheckState(_CHECKED)
        self.assertEqual(self.h.state(),
                         [(False, False), (True, True), (False, False)])
        self.h.col3(s1).setCheckState(_UNCHECKED)
        self.assertEqual(self.h.state(),
                         [(False, False), (False, False), (False, False)])

    # ---- mixed multi-selection: checkbox click ---------------------------
    def test_checkbox_click_sets_all_selected_on(self):
        self.h.set_mixed_state({0})                    # shape 0 already on
        self.h.col3(self.h.shapes[1]).setCheckState(_CHECKED)
        self.assertEqual(self.h.state(),
                         [(True, True), (True, True), (True, True)])

    def test_checkbox_click_sets_all_selected_off(self):
        self.h.set_mixed_state({0, 1})
        self.h.col3(self.h.shapes[1]).setCheckState(_UNCHECKED)
        self.assertEqual(self.h.state(),
                         [(False, False), (False, False), (False, False)])

    def test_extending_selection_does_not_disable_enabled_shape(self):
        # enable shape 0 (single selection), then select all, then switch the
        # group on: shape 0 must stay enabled
        self.h.clear_selection()
        self.h.col3(self.h.shapes[0]).setCheckState(_CHECKED)
        self.h.select_all()
        self.h.col3(self.h.shapes[2]).setCheckState(_CHECKED)
        self.assertEqual(self.h.state(),
                         [(True, True), (True, True), (True, True)])

    # ---- "O" shortcut and context menu -----------------------------------
    def test_key_o_sets_all_selected_on(self):
        self.h.set_mixed_state({0})

        class Ev(object):
            def key(self):
                return QtCore.Qt.Key.Key_O
        self.h.th.actionOnKeyPress(Ev())
        self.assertEqual(self.h.state(),
                         [(True, True), (True, True), (True, True)])

    def test_context_menu_sets_all_selected_on_and_off(self):
        self.h.set_mixed_state({0})
        self.h.th.optimizeRouteForSelectedItems()
        self.assertEqual(self.h.state(),
                         [(True, True), (True, True), (True, True)])
        self.h.th.doNotOptimizeRouteForSelectedItems()
        self.assertEqual(self.h.state(),
                         [(False, False), (False, False), (False, False)])

    # ---- consistency + no unexpected toggles -----------------------------
    def test_checkbox_state_matches_shape_send_to_tsp(self):
        self.h.set_mixed_state({0})
        self.h.col3(self.h.shapes[1]).setCheckState(_CHECKED)
        for s in self.h.shapes:
            self.assertEqual(s.send_to_TSP,
                             self.h.col3(s).checkState() == _CHECKED)

    def test_single_click_emits_no_extra_item_changed(self):
        # the fix applies the other checkboxes with blocked signals -> a single
        # click must not produce a cascade of itemChanged emissions
        self.h.set_mixed_state({0})
        counter = {"n": 0}

        def _count(*a):
            counter["n"] += 1
        self.h.model.itemChanged.connect(_count)
        try:
            self.h.col3(self.h.shapes[1]).setCheckState(_CHECKED)
        finally:
            self.h.model.itemChanged.disconnect(_count)
        self.assertLessEqual(counter["n"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
