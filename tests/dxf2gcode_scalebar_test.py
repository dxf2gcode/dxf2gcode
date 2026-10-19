# -*- coding: utf-8 -*-
"""
Tests for the scale bar of the 2D canvas (gui/scalebar.py).

They cover the unit handling (mm/cm/in), the selection of the scale length
at different zoom levels, the stable position inside the viewport, the
configuration option and the backwards compatibility of the configuration
file.

Run from the repository root:

    python -m unittest discover -s tests -t tests -p "dxf2gcode_scalebar_test.py" -v
"""
from __future__ import absolute_import

import os
import shutil
import tempfile
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import sys
_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [_TEST_DIR, os.path.join(os.path.dirname(_TEST_DIR), "source")]

import dxf2gcode.globals.globals as g  # noqa: E402
from dxf2gcode.globals.config import (  # noqa: E402
    MyConfig, CONFIG_SPEC, CONFIG_VERSION)
from dxf2gcode.Qt import QtCore  # noqa: E402
from dxf2gcode.Qt.QtGui import QImage, QPainter  # noqa: E402
from dxf2gcode.Qt.QtWidgets import QApplication, QGraphicsScene  # noqa: E402
from dxf2gcode.gui.scalebar import (  # noqa: E402
    CM, IN, MM, ScaleBar, ScaleBarState, convert_length, drawing_unit,
    format_length, format_number, nice_lengths, scale_bar_enabled,
    select_scale_length)

_APP = None


def _app():
    global _APP
    if _APP is None:
        _APP = QApplication.instance() or QApplication([])
    return _APP


class _ConfigBase(unittest.TestCase):
    """Base class for the tests that need a configuration."""

    def setUp(self):
        self._old_folder = getattr(g, "folder", None)
        self._old_config = getattr(g, "config", None)
        self.tmp = tempfile.mkdtemp(prefix="d2g_scalebar_test_")
        g.folder = self.tmp
        os.makedirs(os.path.join(self.tmp, "config"))

    def tearDown(self):
        g.folder = self._old_folder
        g.config = self._old_config
        shutil.rmtree(self.tmp, ignore_errors=True)

    @property
    def _cfg_path(self):
        return os.path.join(self.tmp, "config", "config.cfg")

    def _load(self):
        cfg = MyConfig()
        g.config = cfg
        return cfg


class TestUnitConversion(unittest.TestCase):
    """The conversion between the screen length and the real length."""

    def test_mm_to_cm(self):
        self.assertAlmostEqual(convert_length(50, MM, CM), 5.0)

    def test_cm_to_mm(self):
        self.assertAlmostEqual(convert_length(2, CM, MM), 20.0)

    def test_inch_to_mm(self):
        self.assertAlmostEqual(convert_length(1, IN, MM), 25.4)

    def test_mm_to_inch(self):
        self.assertAlmostEqual(convert_length(25.4, MM, IN), 1.0)

    def test_same_unit_is_unchanged(self):
        for unit in (MM, CM, IN):
            self.assertAlmostEqual(convert_length(7.5, unit, unit), 7.5)

    def test_drawing_unit_follows_the_metric_flag(self):
        # the same convention as g.config.metric: 1 == mm, 0 == inch
        self.assertEqual(drawing_unit(1), MM)
        self.assertEqual(drawing_unit(0), IN)

    def test_drawing_unit_accepts_a_unit_name(self):
        self.assertEqual(drawing_unit("mm"), MM)
        self.assertEqual(drawing_unit("cm"), CM)
        self.assertEqual(drawing_unit("in"), IN)


class TestLabelFormatting(unittest.TestCase):
    """The label of the scale bar."""

    def test_millimeter_label(self):
        self.assertEqual(format_length(50, MM), "50 mm")

    def test_centimeter_label(self):
        self.assertEqual(format_length(2, CM), "2 cm")

    def test_inch_label(self):
        self.assertEqual(format_length(1, IN), "1 in")

    def test_no_unnecessary_decimals(self):
        self.assertEqual(format_length(50.0, MM), "50 mm")
        self.assertEqual(format_length(2.50, CM), "2.5 cm")
        self.assertEqual(format_length(0.25, IN), "0.25 in")

    def test_number_formatting(self):
        self.assertEqual(format_number(50.0), "50")
        self.assertEqual(format_number(0.5), "0.5")
        self.assertEqual(format_number(0.0), "0")


class TestNiceLengths(unittest.TestCase):
    """The selection of a readable scale length."""

    def test_nice_lengths_are_the_expected_series(self):
        lengths = nice_lengths(500)
        for expected in (0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50, 100, 200, 500):
            self.assertIn(expected, lengths)

    def test_nice_lengths_are_sorted_and_bounded(self):
        lengths = nice_lengths(37)
        self.assertEqual(lengths, sorted(lengths))
        self.assertTrue(all(length <= 37 for length in lengths))
        self.assertEqual(lengths[-1], 20)

    def test_selected_length_is_nice(self):
        for px_per_unit in (0.01, 0.1, 1.0, 3.7, 12.5, 100.0, 1000.0):
            length, pixels = select_scale_length(px_per_unit)
            self.assertIn(length, nice_lengths(1e9))
            self.assertTrue(60 <= pixels <= 150,
                            "%s px for %s px/unit" % (pixels, px_per_unit))

    def test_selected_length_grows_with_the_zoom(self):
        # zooming in shows a smaller real length on the same screen distance
        length_far, _ = select_scale_length(1.0)
        length_near, _ = select_scale_length(10.0)
        self.assertLess(length_near, length_far)

    def test_zooming_in_halves_the_real_length(self):
        # 10 px per unit -> 100 px are 10 units, 100 px per unit -> 1 unit
        length, pixels = select_scale_length(10.0)
        self.assertAlmostEqual(length * 10.0, pixels)
        length2, pixels2 = select_scale_length(100.0)
        self.assertAlmostEqual(length2 * 100.0, pixels2)
        self.assertAlmostEqual(length * 10.0, length2 * 100.0)

    def test_zooming_out_doubles_the_real_length(self):
        length, _ = select_scale_length(10.0)
        length2, _ = select_scale_length(1.0)
        self.assertAlmostEqual(length * 10.0, length2 * 1.0)

    def test_invalid_zoom_is_handled(self):
        self.assertEqual(select_scale_length(0), (None, 0.0))
        self.assertEqual(select_scale_length(-1), (None, 0.0))


class TestScaleBarState(unittest.TestCase):
    """The state keeps the length stable while zooming."""

    def test_length_is_kept_while_it_is_readable(self):
        state = ScaleBarState()
        length, pixels = state.update(10.0, MM)
        self.assertTrue(60 <= pixels <= 150)
        # a small zoom step must not change the label
        length2, pixels2 = state.update(11.0, MM)
        self.assertEqual(length2, length)
        self.assertAlmostEqual(pixels2, length2 * 11.0)

    def test_length_changes_when_it_does_not_fit_anymore(self):
        state = ScaleBarState()
        length, _ = state.update(10.0, MM)
        length2, pixels2 = state.update(1000.0, MM)
        self.assertNotEqual(length2, length)
        self.assertTrue(60 <= pixels2 <= 150)

    def test_length_changes_when_zoomed_far_out(self):
        state = ScaleBarState()
        length, _ = state.update(10.0, MM)
        length2, pixels2 = state.update(0.01, MM)
        self.assertNotEqual(length2, length)
        self.assertTrue(60 <= pixels2 <= 150)

    def test_unit_change_resets_the_length(self):
        state = ScaleBarState()
        state.update(10.0, MM)
        length, pixels = state.update(10.0, IN)
        # the old length is not reused for the new unit
        self.assertAlmostEqual(length * 10.0, pixels)
        self.assertNotEqual(length, 100.0)

    def test_reset_forgets_the_length(self):
        state = ScaleBarState()
        state.update(10.0, MM)
        state.reset()
        self.assertIsNone(state.length)


class TestScaleBarLayout(unittest.TestCase):
    """The position of the scale bar inside the viewport."""

    def setUp(self):
        _app()
        self.bar = ScaleBar()
        self.bar.update(10.0, MM)

    def test_bar_is_in_the_bottom_right_corner(self):
        viewport = QtCore.QRect(0, 0, 800, 600)
        bar_rect, text_rect = self.bar.layout(viewport)
        self.assertAlmostEqual(bar_rect.right(),
                               viewport.right() - ScaleBar.MARGIN)
        self.assertAlmostEqual(text_rect.right(),
                               viewport.right() - ScaleBar.MARGIN)
        self.assertLess(text_rect.bottom(), viewport.bottom())
        self.assertGreater(bar_rect.left(), viewport.left())

    def test_position_is_the_same_for_other_viewport_sizes(self):
        # the position only depends on the viewport, not on the geometry
        viewport = QtCore.QRect(0, 0, 800, 600)
        bar_rect, text_rect = self.bar.layout(viewport)
        offset = viewport.right() - bar_rect.right()
        for size in ((320, 240), (1024, 768), (1920, 1080)):
            other = QtCore.QRect(0, 0, size[0], size[1])
            bar2, text2 = self.bar.layout(other)
            self.assertAlmostEqual(other.right() - bar2.right(), offset)
            self.assertAlmostEqual(other.bottom() - text2.bottom(),
                                   viewport.bottom() - text_rect.bottom())

    def test_label_is_below_the_bar(self):
        viewport = QtCore.QRect(0, 0, 800, 600)
        bar_rect, text_rect = self.bar.layout(viewport)
        self.assertLessEqual(bar_rect.bottom(), text_rect.top())

    def test_bar_width_matches_the_length(self):
        viewport = QtCore.QRect(0, 0, 800, 600)
        bar_rect, _ = self.bar.layout(viewport)
        self.assertAlmostEqual(bar_rect.width(), self.bar.pixels)
        self.assertAlmostEqual(self.bar.pixels, self.bar.length * 10.0)

    def test_label_contains_the_length_and_the_unit(self):
        # 10 px per unit: the bar is 100 px wide and shows 10 mm
        self.assertEqual(self.bar.label, "10 mm")
        self.bar.update(10.0, IN)
        self.assertTrue(self.bar.label.endswith(" in"))


class TestCanvasIntegration(unittest.TestCase):
    """The scale bar on the real canvas."""

    def setUp(self):
        _app()
        self._old_folder = getattr(g, "folder", None)
        self._old_config = getattr(g, "config", None)
        self.tmp = tempfile.mkdtemp(prefix="d2g_scalebar_canvas_")
        g.folder = self.tmp
        os.makedirs(os.path.join(self.tmp, "config"))
        self.cfg = MyConfig()
        g.config = self.cfg
        self.cfg.metric = 1
        self.cfg.var_dict["General"]["show_scale_bar"] = True
        self.cfg.update_config()

        from dxf2gcode.gui.canvas2d import MyGraphicsView
        self.view = MyGraphicsView()
        self.view.resize(800, 600)
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(0, 0, 400, 300)
        self.view.setScene(self.scene)
        self.view.show()
        _app().processEvents()

    def tearDown(self):
        self.view.close()
        g.folder = self._old_folder
        g.config = self._old_config
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_pixels_per_unit_follow_the_zoom(self):
        before = self.view.scaleBarPixelsPerUnit()
        self.view.scale(2.0, 2.0)
        _app().processEvents()
        after = self.view.scaleBarPixelsPerUnit()
        self.assertAlmostEqual(before * 2.0, after, places=5)

    def test_pixels_per_unit_follow_the_pan(self):
        # panning does not change the scale of the drawing
        before = self.view.scaleBarPixelsPerUnit()
        self.view.horizontalScrollBar().setValue(50)
        self.view.verticalScrollBar().setValue(20)
        _app().processEvents()
        self.assertAlmostEqual(before, self.view.scaleBarPixelsPerUnit())

    def test_label_follows_the_zoom(self):
        self.view.scaleBar.update(self.view.scaleBarPixelsPerUnit(), MM)
        length_before = self.view.scaleBar.length
        pixels_before = self.view.scaleBar.pixels
        self.view.scale(4.0, 4.0)
        _app().processEvents()
        self.view.scaleBar.update(self.view.scaleBarPixelsPerUnit(), MM)
        length_after = self.view.scaleBar.length
        pixels_after = self.view.scaleBar.pixels

        # four times the zoom: the same screen distance shows a quarter of
        # the real length (the length is a nice number, so it may differ a
        # bit from the exact factor)
        self.assertLess(length_after, length_before)
        self.assertGreaterEqual(length_before / length_after, 2.0)
        self.assertLessEqual(length_before / length_after, 5.0)
        # the bar stays readable on the screen
        self.assertTrue(60 <= pixels_after <= 150)
        self.assertTrue(60 <= pixels_before <= 150)

    def test_scale_bar_is_drawn_at_the_bottom_right(self):
        image = QImage(self.view.size(), QImage.Format.Format_ARGB32)
        image.fill(0xFFFFFFFF)
        painter = QPainter(image)
        self.view.render(painter)
        painter.end()

        bar_rect, text_rect = self.view.scaleBar.layout(
            self.view.viewport().rect())

        painted = 0
        for y in range(int(bar_rect.top()), int(bar_rect.bottom()) + 1):
            for x in range(int(bar_rect.left()), int(bar_rect.right()) + 1):
                if image.pixelColor(x, y).value() < 128:
                    painted += 1
        self.assertGreater(painted, 10,
                           "the scale bar is not drawn")
        # the bar is in the bottom right corner of the viewport
        self.assertGreater(bar_rect.left(), self.view.viewport().width() / 2)
        self.assertGreater(bar_rect.top(), self.view.viewport().height() / 2)

    def test_nothing_is_drawn_when_the_option_is_disabled(self):
        self.cfg.var_dict["General"]["show_scale_bar"] = False
        self.cfg.update_config()
        self.view.updateScaleBar()
        _app().processEvents()

        image = QImage(self.view.size(), QImage.Format.Format_ARGB32)
        image.fill(0xFFFFFFFF)
        painter = QPainter(image)
        self.view.render(painter)
        painter.end()

        bar_rect, _ = self.view.scaleBar.layout(self.view.viewport().rect())
        for y in range(int(bar_rect.top()), int(bar_rect.bottom()) + 1):
            for x in range(int(bar_rect.left()), int(bar_rect.right()) + 1):
                self.assertGreaterEqual(image.pixelColor(x, y).value(), 128)

    def test_the_scale_bar_is_no_item_of_the_scene(self):
        # the overlay must not become part of the geometry
        before = len(self.scene.items())
        self.view.scaleBar.update(self.view.scaleBarPixelsPerUnit(), MM)
        _app().processEvents()
        self.assertEqual(len(self.scene.items()), before)

    def test_the_unit_of_the_drawing_is_used(self):
        self.cfg.metric = 0
        self.view.scaleBar.update(self.view.scaleBarPixelsPerUnit(),
                                  drawing_unit())
        self.assertTrue(self.view.scaleBar.label.endswith(" in"))
        self.cfg.metric = 1
        self.view.scaleBar.update(self.view.scaleBarPixelsPerUnit(),
                                  drawing_unit())
        self.assertTrue(self.view.scaleBar.label.endswith(" mm"))


class TestScaleBarOption(unittest.TestCase):
    """The configuration option of the scale bar."""

    def setUp(self):
        self._old_folder = getattr(g, "folder", None)
        self._old_config = getattr(g, "config", None)
        self.tmp = tempfile.mkdtemp(prefix="d2g_scalebar_cfg_")
        g.folder = self.tmp
        os.makedirs(os.path.join(self.tmp, "config"))

    def tearDown(self):
        g.folder = self._old_folder
        g.config = self._old_config
        shutil.rmtree(self.tmp, ignore_errors=True)

    @property
    def _cfg_path(self):
        return os.path.join(self.tmp, "config", "config.cfg")

    def _load(self):
        cfg = MyConfig()
        g.config = cfg
        return cfg

    def _write_config_without_option(self):
        """Write a config file of an older version (without the option)."""
        from configobj import ConfigObj
        from validate import Validator
        obj = ConfigObj(configspec=CONFIG_SPEC, interpolation=False,
                        list_values=False, _inspec=True)
        obj.validate(Validator(), copy=True)
        del obj["General"]["show_scale_bar"]
        obj.filename = self._cfg_path
        obj.write()

    def test_option_is_part_of_the_config_spec(self):
        spec_text = "\n".join(CONFIG_SPEC)
        self.assertIn("show_scale_bar", spec_text)

    def test_default_is_disabled(self):
        # the default keeps the behaviour of the program before the scale bar
        cfg = self._load()
        self.assertFalse(cfg.var_dict["General"]["show_scale_bar"])
        self.assertFalse(scale_bar_enabled(cfg))

    def test_option_is_available_in_the_config_window(self):
        _app()
        cfg = self._load()
        widgets = cfg.makeConfigWidgets()
        self.assertIn("General", widgets)
        self.assertIn("show_scale_bar", widgets["General"])

    def test_the_config_window_stores_the_option(self):
        _app()
        from dxf2gcode.gui.configwindow import ConfigWindow
        cfg = self._load()
        window = ConfigWindow(cfg.makeConfigWidgets(), cfg.var_dict,
                              cfg.var_dict.configspec)
        try:
            # the checkbox shows the value of the config file
            checkbox = window.cfg_window_def["General"]["show_scale_bar"]
            self.assertFalse(checkbox.getValue())

            # the user enables the scale bar and applies the changes
            checkbox.checkbox.setChecked(True)
            window.applyChanges()

            self.assertTrue(cfg.var_dict["General"]["show_scale_bar"])
            self.assertTrue(scale_bar_enabled(cfg))

            # the same way the main window applies the configuration
            cfg.update_config()
            self.assertTrue(scale_bar_enabled(cfg))
        finally:
            window.close()

    def test_old_config_file_gets_the_default(self):
        self._write_config_without_option()
        cfg = self._load()
        self.assertEqual(cfg.version_mismatch, "")
        self.assertFalse(cfg.default_config)
        self.assertFalse(cfg.var_dict["General"]["show_scale_bar"])
        # the file must not have been discarded
        self.assertFalse(os.path.exists(self._cfg_path + ".bad"))

    def test_option_survives_save_and_reload(self):
        cfg = self._load()
        cfg.var_dict["General"]["show_scale_bar"] = True
        cfg.save_varspace()

        cfg2 = self._load()
        self.assertTrue(cfg2.var_dict["General"]["show_scale_bar"])
        self.assertTrue(scale_bar_enabled(cfg2))

    def test_other_options_are_not_lost(self):
        cfg = self._load()
        cfg.var_dict["Paths"]["import_dir"] = "C:/my/custom/dxf"
        cfg.var_dict["General"]["show_scale_bar"] = True
        cfg.save_varspace()

        cfg2 = self._load()
        self.assertEqual(cfg2.var_dict["Paths"]["import_dir"],
                         "C:/my/custom/dxf")
        self.assertTrue(cfg2.var_dict["General"]["show_scale_bar"])

    def test_the_config_version_is_not_changed(self):
        # the format of the config file stays the same, so old files remain
        # valid and no migration is needed
        cfg = self._load()
        self.assertEqual(cfg.var_dict["Version"]["config_version"],
                         CONFIG_VERSION)


if __name__ == "__main__":
    unittest.main(verbosity=2)
