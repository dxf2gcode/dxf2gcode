"""Exercise canvas mouse events with the active Qt binding."""

import os
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "source"))

from dxf2gcode.presentation.qt.qt_compat import QtCore
from dxf2gcode.presentation.qt.qt_compat.QtGui import QMouseEvent
from dxf2gcode.presentation.qt.qt_compat.QtWidgets import (
    QApplication, QGraphicsScene, QGraphicsView, QGraphicsRectItem, QGraphicsItem)
import dxf2gcode.bootstrap.runtime_state as g

with patch.object(g, "config", SimpleNamespace(mode3d=False)):
    from dxf2gcode.presentation.qt.canvas2d import MyGraphicsView
    from dxf2gcode.presentation.qt.canvas import mixedSelectionIcon

_APP = None


class TestCanvasMouseEvents(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        global _APP
        _APP = QApplication.instance() or QApplication([])

    def setUp(self):
        self.view = MyGraphicsView()
        self.view.setScene(QGraphicsScene(self.view))
        self.addCleanup(self.view.close)

    def event(self, kind, position, button, buttons):
        return QMouseEvent(kind, QtCore.QPointF(*position), button, buttons,
                           QtCore.Qt.KeyboardModifier.NoModifier)

    def press(self, position=(10, 10)):
        self.view.mousePressEvent(self.event(
            QtCore.QEvent.Type.MouseButtonPress, position,
            QtCore.Qt.MouseButton.LeftButton, QtCore.Qt.MouseButton.LeftButton))

    def release(self, position=(10, 10)):
        self.view.mouseReleaseEvent(self.event(
            QtCore.QEvent.Type.MouseButtonRelease, position,
            QtCore.Qt.MouseButton.LeftButton, QtCore.Qt.MouseButton.NoButton))

    def test_left_click_records_and_clears_selection_origin(self):
        self.press()
        self.assertEqual(self.view.mppos, QtCore.QPoint(10, 10))
        self.release()
        self.assertIsNone(self.view.mppos)

    def test_drag_selects_using_the_rubber_band(self):
        self.press()
        self.view.mouseMoveEvent(self.event(
            QtCore.QEvent.Type.MouseMove, (40, 30),
            QtCore.Qt.MouseButton.NoButton, QtCore.Qt.MouseButton.LeftButton))
        self.assertFalse(self.view.rubberBand.isHidden())
        self.assertEqual(self.view.rubberBand.geometry(),
                         QtCore.QRect(QtCore.QPoint(10, 10), QtCore.QPoint(40, 30)))
        self.release((40, 30))
        self.assertTrue(self.view.rubberBand.isHidden())
        self.assertIsNone(self.view.mppos)

    def test_hand_drag_does_not_start_shape_selection(self):
        self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.press()
        self.assertIsNone(self.view.mppos)
        self.release()
        self.assertTrue(self.view.rubberBand.isHidden())

    def test_multi_selection_notifies_once_with_the_complete_final_state(self):
        notifications = []
        items = []

        class Contour(QGraphicsRectItem):
            def __init__(self, x):
                super().__init__(x, 0, 10, 10)
                self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
                self.model = SimpleNamespace(selectionChangedCallback=lambda model, selected:
                    notifications.append(tuple(item.isSelected() for item in items)))

            def setSelected(self, selected, blockSignals=True):
                super().setSelected(selected)
                if not blockSignals:
                    self.model.selectionChangedCallback(self.model, selected)

            def contains_point(self, point):
                return 0 if self.rect().contains(point) else 1000

        for x in (0, 30, 60):
            item = Contour(x)
            items.append(item)
            self.view.scene().addItem(item)
        self.view.resize(300, 200)
        self.view.show()
        self.view.fitInView(QtCore.QRectF(-10, -10, 100, 50))
        _APP.processEvents()
        self.press()
        self.view.rubberBand.setGeometry(self.view.viewport().rect())
        self.view.rubberBand.show()
        self.release((290, 190))
        self.assertEqual(notifications, [(True, True, True)])
        # Clearing the previous selection also emits one complete state,
        # rather than replanning after each of the three deselections.
        notifications.clear()
        point = self.view.mapFromScene(QtCore.QPointF(90, 30))
        self.press((point.x(), point.y()))
        self.release((point.x(), point.y()))
        self.assertEqual(notifications, [(False, False, False)])

    def test_mixed_selection_icon_is_available(self):
        self.assertFalse(mixedSelectionIcon().isNull())


if __name__ == "__main__":
    unittest.main()
