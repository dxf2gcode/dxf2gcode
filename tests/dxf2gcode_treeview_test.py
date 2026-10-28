# -*- coding: utf-8 -*-
"""Tests for TreeView selection callbacks and internal row reordering."""
from __future__ import absolute_import

import os
import sys
import unittest
from unittest import mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_DIR = os.path.dirname(_TEST_DIR)
sys.path.insert(0, os.path.join(_REPO_DIR, "source"))

from dxf2gcode.presentation.qt.qt_compat import QtCore  # noqa: E402
from dxf2gcode.presentation.qt.qt_compat.QtGui import QKeyEvent, QStandardItem, QStandardItemModel  # noqa: E402
from dxf2gcode.presentation.qt.qt_compat.QtWidgets import QApplication  # noqa: E402
from dxf2gcode.presentation.qt.treeview import MyStandardItemModel, TreeView  # noqa: E402

_APP = None


class _DropEvent(object):
    def __init__(self):
        self.accepted = False
        self.ignored = False
        self.drop_action = None

    def pos(self):
        return QtCore.QPoint(0, 0)

    def proposedAction(self):
        return QtCore.Qt.DropAction.MoveAction

    def setDropAction(self, action):
        self.drop_action = action

    def acceptProposedAction(self):
        self.accepted = True

    def accept(self):
        self.accepted = True

    def ignore(self):
        self.ignored = True


class TestTreeView(unittest.TestCase):

    def setUp(self):
        global _APP
        _APP = QApplication.instance() or QApplication([])
        self.view = TreeView()
        self.model = QStandardItemModel()
        self.model.appendColumn([QStandardItem(name) for name in "ABC"])
        self.view.setModel(self.model)

    def _names(self):
        return [self.model.item(row).text()
                for row in range(self.model.rowCount())]

    def test_selection_callback_receives_real_qt_selection_changes(self):
        calls = []
        self.view.setSelectionCallback(
            lambda parent, selected, deselected:
            calls.append((selected.count(), deselected.count())))
        selection = self.view.selectionModel()
        selection.select(
            self.model.index(1, 0),
            QtCore.QItemSelectionModel.SelectionFlag.Select |
            QtCore.QItemSelectionModel.SelectionFlag.Rows)

        self.assertEqual(calls, [(1, 0)])

    def test_block_signals_suppresses_callback_until_reenabled(self):
        calls = []
        self.view.setSelectionCallback(lambda *args: calls.append(args))
        self.view.blockSignals(True)
        self.view.selectionModel().select(
            self.model.index(0, 0),
            QtCore.QItemSelectionModel.SelectionFlag.Select |
            QtCore.QItemSelectionModel.SelectionFlag.Rows)
        self.assertEqual(calls, [])

        self.view.blockSignals(False)
        self.view.selectionModel().select(
            self.model.index(2, 0),
            QtCore.QItemSelectionModel.SelectionFlag.Select |
            QtCore.QItemSelectionModel.SelectionFlag.Rows)
        self.assertEqual(len(calls), 1)

    def test_key_callback_can_handle_or_delegate_key_events(self):
        handled = mock.Mock(return_value=True)
        self.view.setKeyPressEventCallback(handled)
        event = QKeyEvent(QtCore.QEvent.Type.KeyPress,
                          QtCore.Qt.Key.Key_Escape,
                          QtCore.Qt.KeyboardModifier.NoModifier)
        self.view.keyPressEvent(event)
        handled.assert_called_once_with(event)

        delegated = mock.Mock(return_value=False)
        self.view.setKeyPressEventCallback(delegated)
        event = QKeyEvent(QtCore.QEvent.Type.KeyPress,
                          QtCore.Qt.Key.Key_Down,
                          QtCore.Qt.KeyboardModifier.NoModifier)
        self.view.keyPressEvent(event)
        delegated.assert_called_once_with(event)

    def test_move_up_and_down_reorder_rows_and_notify_export_callback(self):
        updates = []
        self.view.setExportOrderUpdateCallback(
            lambda: updates.append(self._names()))

        self.view.setCurrentIndex(self.model.index(1, 0))
        self.view.moveUpCurrentItem()
        self.assertEqual(self._names(), ["B", "A", "C"])
        self.assertEqual(len(updates), 1)

        self.view.moveDownCurrentItem()
        self.assertEqual(self._names(), ["A", "B", "C"])
        self.assertEqual(len(updates), 2)

    def test_move_at_first_or_last_row_is_a_noop(self):
        updates = []
        self.view.setExportOrderUpdateCallback(lambda: updates.append(True))

        self.view.setCurrentIndex(self.model.index(0, 0))
        self.view.moveUpCurrentItem()
        self.view.setCurrentIndex(self.model.index(2, 0))
        self.view.moveDownCurrentItem()

        self.assertEqual(self._names(), ["A", "B", "C"])
        self.assertEqual(updates, [])

    def test_drop_reorders_siblings_and_calls_export_callback(self):
        updates = []
        self.view.setExportOrderUpdateCallback(lambda: updates.append(True))
        self.view.dragged_element = True
        self.view.dragged_element_model_index = self.model.index(0, 0)
        target = self.model.index(1, 0)
        event = _DropEvent()

        with mock.patch.object(TreeView, "indexAt", return_value=target), \
                mock.patch.object(TreeView, "dropIndicatorPosition",
                                  return_value=TreeView.BelowItem):
            self.view.dropEvent(event)

        self.assertTrue(event.accepted)
        self.assertEqual(event.drop_action, QtCore.Qt.DropAction.IgnoreAction)
        self.assertEqual(self._names(), ["B", "A", "C"])
        self.assertEqual(updates, [True])
        self.assertFalse(self.view.dragged_element)

    def test_drop_without_drag_or_onto_viewport_is_ignored(self):
        event = _DropEvent()
        self.view.dropEvent(event)
        self.assertTrue(event.ignored)

        self.view.dragged_element = True
        self.view.dragged_element_model_index = self.model.index(0, 0)
        event = _DropEvent()
        with mock.patch.object(TreeView, "indexAt",
                               return_value=QtCore.QModelIndex()), \
                mock.patch.object(TreeView, "dropIndicatorPosition",
                                  return_value=TreeView.OnViewport):
            self.view.dropEvent(event)
        self.assertTrue(event.ignored)
        self.assertEqual(self._names(), ["A", "B", "C"])

    def test_custom_model_returns_empty_qt_drag_mime_payload(self):
        model = MyStandardItemModel()
        model.appendRow(QStandardItem("shape"))
        payload = model.mimeData([model.index(0, 0)])

        self.assertTrue(payload.hasFormat(
            "application/x-qstandarditemmodeldatalist"))
        self.assertEqual(bytes(payload.data(
            "application/x-qstandarditemmodeldatalist")), b"")


if __name__ == "__main__":
    unittest.main()
