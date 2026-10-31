# -*- coding: utf-8 -*-
"""Tests for TreeView selection callbacks and internal row reordering."""
from __future__ import absolute_import

import os
import subprocess
import sys
import unittest
from unittest import mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_DIR = os.path.dirname(_TEST_DIR)
sys.path.insert(0, os.path.join(_REPO_DIR, "source"))

from dxf2gcode.presentation.qt.qt_compat import QtCore  # noqa: E402
from dxf2gcode.presentation.qt.qt_compat.QtGui import QDropEvent, QKeyEvent, QStandardItem, QStandardItemModel  # noqa: E402
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
        mime = QtCore.QMimeData()
        event = QDropEvent(QtCore.QPointF(0, 0), QtCore.Qt.DropAction.MoveAction,
                           mime, QtCore.Qt.MouseButton.LeftButton,
                           QtCore.Qt.KeyboardModifier.NoModifier)

        with mock.patch.object(TreeView, "indexAt", return_value=target), \
                mock.patch.object(TreeView, "dropIndicatorPosition",
                                  return_value=TreeView.DropIndicatorPosition.BelowItem):
            self.view.dropEvent(event)

        self.assertTrue(event.isAccepted())
        self.assertEqual(event.dropAction(), QtCore.Qt.DropAction.IgnoreAction)
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
                                  return_value=TreeView.DropIndicatorPosition.OnViewport):
            self.view.dropEvent(event)
        self.assertTrue(event.ignored)
        self.assertEqual(self._names(), ["A", "B", "C"])

    def test_rejected_drops_preserve_tree_and_finish_drag(self):
        shape = QStandardItem("shape")
        self.model.item(0).appendRow(shape)
        updates = []
        self.view.setExportOrderUpdateCallback(lambda: updates.append(True))
        positions = TreeView.DropIndicatorPosition
        mime = QtCore.QMimeData()
        cases = (
            (shape.index(), self.model.index(2, 0), positions.OnItem),
            (shape.index(), self.model.index(1, 0), positions.BelowItem),
            (self.model.index(1, 0), shape.index(), positions.OnItem),
            (shape.index(), QtCore.QModelIndex(), positions.OnViewport),
            (QtCore.QModelIndex(), shape.index(), positions.OnItem),
        )
        for source, target, position in cases:
            with self.subTest(source=source.row(), target=target.row(),
                              position=position):
                self.view.dragged_element = True
                self.view.dragged_element_model_index = source
                event = QDropEvent(
                    QtCore.QPointF(0, 0), QtCore.Qt.DropAction.MoveAction,
                    mime, QtCore.Qt.MouseButton.LeftButton,
                    QtCore.Qt.KeyboardModifier.NoModifier)
                with mock.patch.object(TreeView, "indexAt", return_value=target), \
                        mock.patch.object(TreeView, "dropIndicatorPosition",
                                          return_value=position):
                    self.view.dropEvent(event)
                self.assertFalse(event.isAccepted())
                self.assertFalse(self.view.dragged_element)
                self.assertEqual(self._names(), ["A", "B", "C"])
                self.assertIs(self.model.item(0).child(0), shape)
                self.assertEqual(self.model.item(0).rowCount(), 1)
                self.assertEqual(self.model.item(1).rowCount(), 0)
                self.assertEqual(self.model.item(2).rowCount(), 0)
                self.assertEqual(updates, [])

    def test_custom_model_returns_empty_qt_drag_mime_payload(self):
        model = MyStandardItemModel()
        model.appendRow(QStandardItem("shape"))
        payload = model.mimeData([model.index(0, 0)])

        self.assertTrue(payload.hasFormat(
            "application/x-qstandarditemmodeldatalist"))
        self.assertEqual(bytes(payload.data(
            "application/x-qstandarditemmodeldatalist")), b"")


class TestTreeExpansionAvailability(unittest.TestCase):
    """Only offer folding actions that change visible tree branches."""

    def setUp(self):
        global _APP
        _APP = QApplication.instance() or QApplication([])
        self.view = TreeView()
        self.states = []
        self.view.expansionAvailabilityChanged.connect(
            lambda collapse, expand: self.states.append((collapse, expand)))
        self.model = QStandardItemModel()
        self.view.setModel(self.model)

    def tearDown(self):
        self.view.close()
        self.view.deleteLater()
        _APP.processEvents()

    def assert_actions(self, collapse, expand):
        _APP.processEvents()
        self.assertEqual(self.states[-1], (collapse, expand))

    def add_branches(self):
        outer = QStandardItem("entity")
        inner = QStandardItem("block")
        inner.appendRow(QStandardItem("shape"))
        outer.appendRow(inner)
        other = QStandardItem("other layer")
        other.appendRow(QStandardItem("other shape"))
        self.model.appendRow(outer)
        self.model.appendRow(other)
        return outer, inner, other

    def test_no_model_empty_model_and_leaves_disable_both_actions(self):
        self.assert_actions(False, False)
        self.model.appendRow(QStandardItem("leaf"))
        self.assert_actions(False, False)
        self.view.setModel(None)
        self.assert_actions(False, False)

    def test_manual_folding_and_bulk_actions_update_availability(self):
        outer, inner, other = self.add_branches()
        self.assert_actions(False, True)
        self.view.expand(outer.index())
        self.assert_actions(True, True)
        self.view.expand(inner.index())
        self.assert_actions(True, True)
        self.view.expand(other.index())
        self.assert_actions(True, False)
        self.view.collapse(inner.index())
        self.assert_actions(True, True)
        self.view.expandAll()
        self.assert_actions(True, False)
        self.view.collapseAll()
        self.assert_actions(False, True)

    def test_hidden_expanded_descendants_do_not_enable_collapse(self):
        outer, inner, other = self.add_branches()
        self.view.expandAll()
        self.view.collapse(other.index())
        self.view.collapse(outer.index())
        self.assertTrue(self.view.isExpanded(inner.index()))
        self.assert_actions(False, True)
        self.view.expand(outer.index())
        self.assert_actions(True, True)
        self.view.expand(other.index())
        self.assert_actions(True, False)

    def test_inserting_and_removing_branches_refreshes_actions(self):
        outer, inner, other = self.add_branches()
        self.view.expandAll()
        branch = QStandardItem("new block")
        branch.appendRow(QStandardItem("new shape"))
        outer.appendRow(branch)
        self.assert_actions(True, True)
        outer.removeRow(branch.row())
        self.assert_actions(True, False)
        self.model.clear()
        self.assert_actions(False, False)

    def test_model_replacement_disconnects_old_model(self):
        self.add_branches()
        old_model = self.model
        self.model = QStandardItemModel()
        self.model.appendRow(QStandardItem("leaf"))
        self.view.setModel(self.model)
        self.assert_actions(False, False)
        notifications = len(self.states)
        old_model.clear()
        self.assertEqual(len(self.states), notifications)
        self.model.item(0).appendRow(QStandardItem("child"))
        self.assert_actions(False, True)

    def test_reordering_rows_keeps_actions_current(self):
        self.add_branches()
        self.view.expandAll()
        moved = self.model.takeRow(0)
        self.model.appendRow(moved)
        self.assert_actions(True, True)
        self.view.expandAll()
        self.assert_actions(True, False)

    def test_unblocking_signals_refreshes_after_silent_expansion(self):
        self.add_branches()
        self.view.blockSignals(True)
        self.view.expandAll()
        self.view.blockSignals(False)
        self.assert_actions(True, False)
        self.view.expandToDepth(0)
        self.assert_actions(True, True)

    def test_two_views_manage_their_states_independently(self):
        self.add_branches()
        other_view = TreeView()
        other_states = []
        other_view.expansionAvailabilityChanged.connect(
            lambda collapse, expand: other_states.append((collapse, expand)))
        other_view.setModel(self.model)
        self.view.expandAll()
        self.assert_actions(True, False)
        self.assertEqual(other_states[-1], (False, True))
        other_view.close()
        other_view.deleteLater()

    def test_manual_fold_notifications_wait_until_qt_finishes(self):
        outer, inner, other = self.add_branches()
        _APP.processEvents()
        self.states.clear()
        self.view.expand(outer.index())
        self.assertEqual(self.states, [], "Do not query/update buttons inside Qt's expand signal")
        self.assert_actions(True, True)
        self.states.clear()
        self.view.collapse(outer.index())
        self.assertEqual(self.states, [], "Do not query/update buttons inside Qt's collapse signal")
        self.assert_actions(False, True)

    def test_bulk_folding_reports_only_the_completed_state(self):
        self.add_branches()
        _APP.processEvents()
        self.states.clear()
        self.view.expandAll()
        self.assertEqual(self.states, [(True, False)])
        _APP.processEvents()
        self.assertEqual(self.states, [(True, False)])
        self.states.clear()
        self.view.collapseAll()
        self.assertEqual(self.states, [(False, True)])
        _APP.processEvents()
        self.assertEqual(self.states, [(False, True)])

    def test_reentrant_consumer_does_not_repeat_state_notifications(self):
        self.add_branches()
        _APP.processEvents()
        self.states.clear()

        def refresh_again(*unused):
            self.view.updateExpansionAvailability()
            _APP.processEvents()

        self.view.expansionAvailabilityChanged.connect(refresh_again)
        self.view.expandAll()
        _APP.processEvents()
        self.assertEqual(self.states, [(True, False)])

    def test_shown_tree_bulk_buttons_finish_after_manual_collapse(self):
        result = subprocess.run(
            [sys.executable, __file__, "--expansion-worker"],
            capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


def _run_expansion_worker():
    """Exercise Qt's visible-tree layout; a hang must not stall the suite."""
    import faulthandler
    from dxf2gcode.presentation.qt.qt_compat.QtWidgets import QPushButton

    faulthandler.dump_traceback_later(3)
    app = QApplication([])
    view = TreeView()
    model = QStandardItemModel()
    for name in ("Platte", "Durchbrueche", "0"):
        parent = QStandardItem(name)
        for number in range(30):
            parent.appendRow(QStandardItem("Shape %d" % number))
        model.appendRow(parent)
    view.setModel(model)
    collapse, expand = QPushButton(), QPushButton()

    def update_buttons(can_collapse, can_expand):
        collapse.setEnabled(can_collapse)
        expand.setEnabled(can_expand)

    view.expansionAvailabilityChanged.connect(update_buttons)
    collapse.clicked.connect(view.collapseAll)
    expand.clicked.connect(view.expandAll)
    view.expandAll()
    view.resize(500, 350)
    view.show()
    app.processEvents()
    for row in (1, 0, 2):
        view.collapse(model.index(row, 0))
        app.processEvents()
        assert collapse.isEnabled() and expand.isEnabled()
        expand.click()
        app.processEvents()
        assert collapse.isEnabled() and not expand.isEnabled()
        view.collapse(model.index(row, 0))
        app.processEvents()
        collapse.click()
        app.processEvents()
        assert not collapse.isEnabled() and expand.isEnabled()
        expand.click()
        app.processEvents()
    view.close()
    faulthandler.cancel_dump_traceback_later()


if __name__ == "__main__":
    if "--expansion-worker" in sys.argv:
        _run_expansion_worker()
    else:
        unittest.main()
