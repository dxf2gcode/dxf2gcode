# -*- coding: utf-8 -*-
"""
Regression tests for the multi-selection handling of the "Optimal path"
(TSP) checkbox column in the layer/shape tree.

The decision logic is factored into the pure helper
``treehandling.next_group_check_state`` so it can be tested without a running
GUI. A Qt-model level test additionally verifies the uniform application on
real QStandardItems. The remaining GUI wiring (``TreeHandler.actionOnKeyPress``)
still needs a full application and is documented as a test gap.

Run from the repository root:

    python -m unittest discover -s tests -t tests -p "dxf2gcode_tree_group_state_test.py" -v
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
        g.folder = tempfile.mkdtemp(prefix="d2g_tree_test_")
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

from dxf2gcode.gui.treehandling import next_group_check_state  # noqa: E402


class TestNextGroupCheckState(unittest.TestCase):
    """Pure decision logic: uniform target state for a group toggle."""

    def test_single_off_to_on(self):
        self.assertTrue(next_group_check_state([False]))

    def test_single_on_to_off(self):
        self.assertFalse(next_group_check_state([True]))

    def test_mixed_multi_selection_turns_all_on(self):
        # scenario 2: mixed start states -> all selected set to ON
        self.assertTrue(next_group_check_state([True, False, False]))

    def test_all_on_multi_selection_turns_all_off(self):
        # scenario 3: everything already on -> all selected set to OFF
        self.assertFalse(next_group_check_state([True, True, True]))

    def test_extend_selection_does_not_disable_enabled_shape(self):
        # scenario 4: one shape already enabled, then more (disabled) shapes
        # are added to the selection -> target must be ON, the enabled shape
        # kept enabled
        self.assertTrue(next_group_check_state([True, False]))
        self.assertTrue(next_group_check_state([True, False, False, False]))

    def test_uniform_application_sets_each_item_once(self):
        # scenario 5: the target is computed ONCE from the pre-change states
        # and applied to every item (no per-item toggle, no double toggle)
        states = [True, False, False]
        target = next_group_check_state(states)
        applied = []
        for _ in states:
            applied.append(target)          # one setCheckState per item
        self.assertEqual(applied, [True, True, True])
        # a naive per-item invert (the old buggy behaviour) differs
        self.assertNotEqual(applied, [not s for s in states])

    def test_empty_selection_is_harmless(self):
        # no selected item -> the returned state is never applied
        self.assertTrue(next_group_check_state([]))


class TestGroupCheckStateQtModel(unittest.TestCase):
    """Application on real QStandardItems (headless Qt)."""

    def setUp(self):
        try:
            from dxf2gcode.Qt.QtGui import QStandardItem
            from dxf2gcode.Qt import QtCore
        except Exception as exc:                       # pragma: no cover
            self.skipTest("Qt not available: %s" % exc)
        self.QStandardItem = QStandardItem
        self.QtCore = QtCore

    def _make(self, states):
        items = []
        for s in states:
            it = self.QStandardItem()
            it.setCheckState(self.QtCore.Qt.CheckState.Checked if s
                             else self.QtCore.Qt.CheckState.Unchecked)
            items.append(it)
        return items

    def _apply(self, items):
        target = next_group_check_state(
            [it.checkState() == self.QtCore.Qt.CheckState.Checked
             for it in items])
        new_state = (self.QtCore.Qt.CheckState.Checked if target
                     else self.QtCore.Qt.CheckState.Unchecked)
        for it in items:
            it.setCheckState(new_state)

    def test_mixed_becomes_all_checked(self):
        items = self._make([True, False, False])
        self._apply(items)
        self.assertTrue(all(it.checkState() == self.QtCore.Qt.CheckState.Checked
                            for it in items))

    def test_all_checked_becomes_all_unchecked(self):
        items = self._make([True, True])
        self._apply(items)
        self.assertTrue(all(it.checkState() == self.QtCore.Qt.CheckState.Unchecked
                            for it in items))

    def test_partially_checked_counts_as_on(self):
        # a mixed item (PartiallyChecked) is not "Checked", so the group is
        # switched ON - deterministic behaviour for mixed selections
        items = self._make([True, False])
        items[1].setCheckState(self.QtCore.Qt.CheckState.PartiallyChecked)
        self._apply(items)
        self.assertTrue(all(it.checkState() == self.QtCore.Qt.CheckState.Checked
                            for it in items))

    def test_single_item_toggles(self):
        items = self._make([False])
        self._apply(items)
        self.assertEqual(items[0].checkState(), self.QtCore.Qt.CheckState.Checked)
        self._apply(items)
        self.assertEqual(items[0].checkState(), self.QtCore.Qt.CheckState.Unchecked)


if __name__ == "__main__":
    unittest.main(verbosity=2)
