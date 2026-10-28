# -*- coding: utf-8 -*-
"""
Test of the warning marker in the canvas.

The marker (a red circle with a cross) shows that the geometry of a shape is
not complete. It must always have the same size in pixels, it must not scale
with the zoom level of the canvas.

Run from the repository root:

    python -m unittest discover -s tests -t tests -p "dxf2gcode_canvas_warning_marker_test.py" -v
"""
from __future__ import absolute_import

import os
import shutil
import sys
import tempfile
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [_TEST_DIR, os.path.join(os.path.dirname(_TEST_DIR), "source")]

import dxf2gcode.bootstrap.runtime_state as g  # noqa: E402
from dxf2gcode.domain.toolpath.leadmove import LEAD_RADIUS  # noqa: E402
from dxf2gcode.adapters.config.runtime_config import MyConfig  # noqa: E402
from dxf2gcode.presentation.qt.qt_compat.QtCore import QPointF, QRectF  # noqa: E402
from dxf2gcode.presentation.qt.qt_compat.QtGui import QImage, QPainter  # noqa: E402
from dxf2gcode.presentation.qt.qt_compat.QtWidgets import (QApplication, QGraphicsScene,  # noqa: E402
                                    QGraphicsView)

from dxf2gcode_leadmove_golden_test import build_shape  # noqa: E402

_APP = None


def _app():
    global _APP
    if _APP is None:
        _APP = QApplication.instance() or QApplication([])
    return _APP


class TestWarningMarker(unittest.TestCase):

    def setUp(self):
        _app()
        self.tmp = tempfile.mkdtemp(prefix="d2g_marker_")
        self._old_folder = getattr(g, "folder", None)
        self._old_config = getattr(g, "config", None)
        g.folder = self.tmp
        os.makedirs(os.path.join(self.tmp, "config"))
        self.config = MyConfig()
        g.config = self.config

    def tearDown(self):
        g.folder = self._old_folder
        g.config = self._old_config
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _marker_image(self, zoom):
        """
        Render a shape with an invalid geometry (the radius at the workpiece
        is smaller than the tool radius) and return the image.
        @param zoom: the zoom level of the view
        @return: the rendered image
        """
        from dxf2gcode.presentation.qt.canvas2d import StMoveGUI
        shape, layer = build_shape(
            closed=True, cut_cor=41,
            layer_settings=dict(lead_in_mode=LEAD_RADIUS, lead_radius=1.0))
        self.assertTrue(shape.stmove.start_move_error)

        scene = QGraphicsScene()
        item = StMoveGUI(shape)
        scene.addItem(item)
        view = QGraphicsView(scene)
        view.resize(400, 400)
        view.scale(zoom, zoom)
        view.setSceneRect(-50, -50, 100, 100)

        image = QImage(400, 400, QImage.Format.Format_ARGB32)
        image.fill(0xFFFFFFFF)
        painter = QPainter(image)
        view.render(painter)
        painter.end()
        return image

    def _red_pixels(self, image):
        """The bounding rect of the red (warning) pixels of the image."""
        rect = None
        for y in range(image.height()):
            for x in range(image.width()):
                pixel = image.pixelColor(x, y)
                if (pixel.red() > 150 and pixel.green() < 80 and
                        pixel.blue() < 80):
                    point = QRectF(x, y, 1, 1)
                    rect = point if rect is None else rect.united(point)
        return rect

    def test_the_marker_has_the_same_size_at_every_zoom_level(self):
        sizes = []
        for zoom in (1.0, 0.25, 4.0):
            image = self._marker_image(zoom)
            rect = self._red_pixels(image)
            self.assertIsNotNone(rect, "no warning marker found (zoom %s)"
                                 % zoom)
            sizes.append((rect.width(), rect.height()))
        for width, height in sizes:
            # The diameter of the marker is 20 pixels (the cross has the same
            # extent as the circle). The pen is 2 pixels wide, so the marker
            # is a little bit bigger.
            self.assertGreaterEqual(width, 20)
            self.assertLessEqual(width, 24)
            self.assertGreaterEqual(height, 20)
            self.assertLessEqual(height, 24)
        # All the zoom levels give the same size.
        self.assertEqual(len(set(sizes)), 1, sizes)


class TestErrorMessageAggregation(unittest.TestCase):
    """The error message of the shapes is shown only once.

    Changing a setting of a layer (e.g. the overcut) repaints every shape of
    the layer one after the other. A shape whose geometry can not be calculated
    reports an error: showing the message box inside repaint_shape would pop it
    up once per affected shape. The messages are collected and shown in a
    single box.
    """

    def setUp(self):
        _app()
        self.tmp = tempfile.mkdtemp(prefix="d2g_messages_")
        self._old_folder = getattr(g, "folder", None)
        self._old_config = getattr(g, "config", None)
        self._old_window = getattr(g, "window", None)
        g.folder = self.tmp
        os.makedirs(os.path.join(self.tmp, "config"))
        self.config = MyConfig()
        g.config = self.config

        class _Window(object):
            def tr(self, text):
                return text

        g.window = _Window()

    def tearDown(self):
        g.folder = self._old_folder
        g.config = self._old_config
        g.window = self._old_window
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _new_scene(self):
        from dxf2gcode.presentation.qt.canvas2d import MyGraphicsScene
        return MyGraphicsScene()

    def test_duplicate_messages_are_collected_and_shown_once(self):
        from dxf2gcode.presentation.qt import canvas2d
        scene = self._new_scene()
        calls = []
        old_critical = canvas2d.QMessageBox.critical
        canvas2d.QMessageBox.critical = staticmethod(
            lambda *args: calls.append(args))
        try:
            # The same error of three shapes and a different one.
            scene.queue_error_message("overcut error")
            scene.queue_error_message("overcut error")
            scene.queue_error_message("overcut error")
            scene.queue_error_message("other error")
            # Nothing is shown while the shapes are repainted.
            self.assertEqual(calls, [])
            scene._show_pending_error_messages()
            # A single message box with the unique messages.
            self.assertEqual(len(calls), 1)
            message = calls[0][2]
            self.assertEqual(message.count("overcut error"), 1)
            self.assertEqual(message.count("other error"), 1)
            # The collection is reset: nothing is shown a second time.
            scene._show_pending_error_messages()
            self.assertEqual(len(calls), 1)
        finally:
            canvas2d.QMessageBox.critical = old_critical
            scene._pending_error_messages = []

    def test_repaint_shape_collects_instead_of_showing_the_message(self):
        from dxf2gcode.presentation.qt import canvas2d
        scene = self._new_scene()
        calls = []
        old_critical = canvas2d.QMessageBox.critical
        canvas2d.QMessageBox.critical = staticmethod(
            lambda *args: calls.append(args))
        try:
            class _Item(object):
                def hide(self):
                    pass

            class _StMove(_Item):
                def _warning(self):
                    return "the overcut is only possible for closed contours."

            def fake_paint_shape(s):
                # Simulate the items the paint_shape of the scene creates.
                s.stmove = _StMove()
                s.starrow = _Item()
                s.enarrow = _Item()

            shape = type("ShapeStub", (), {})()
            shape.stmove = _StMove()
            shape.starrow = _Item()
            shape.enarrow = _Item()
            shape.isSelected = lambda: False
            scene.paint_shape = fake_paint_shape

            scene.repaint_shape(shape)
            # The message is not shown during the repaint, it is collected.
            self.assertEqual(calls, [])
            self.assertIn(
                "the overcut is only possible for closed contours.",
                scene._pending_error_messages)
        finally:
            canvas2d.QMessageBox.critical = old_critical
            scene._pending_error_messages = []


if __name__ == "__main__":
    unittest.main(verbosity=2)
