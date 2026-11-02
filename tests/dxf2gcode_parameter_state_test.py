# -*- coding: utf-8 -*-
"""
Tests for the unified numeric parameter fields of the mill settings frame.

Covers the state logic (standard / individual / mixed / unavailable) and the
multi selection display: equal values, different values, different tool
defaults, the "Different" placeholder (which must never become a parameter
value) and the behaviour when a field is focused/left without a new value.

Run from the repository root:

    python -m unittest discover -s tests -t tests -p "dxf2gcode_parameter_state_test.py" -v
"""
from __future__ import absolute_import

import os
import tempfile
import logging
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import sys
_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [_TEST_DIR, os.path.join(os.path.dirname(_TEST_DIR), "source")]


def _init_config():
    import dxf2gcode.bootstrap.runtime_state as g
    from dxf2gcode.adapters.config.runtime_config import MyConfig

    if getattr(g, "config", None) is None:
        g.folder = tempfile.mkdtemp(prefix="d2g_param_state_test_")
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
    for name in ("PostPro.PostProcessor", "core.shapeoffset", "core.stmove",
                 "Core.Project", "Gui.TreeHandling", "core.pocketmill"):
        logging.getLogger(name).setLevel(logging.CRITICAL)


_init_config()

import dxf2gcode.bootstrap.runtime_state as g  # noqa: E402
from dxf2gcode.presentation.qt import shapeparameterstate as sps  # noqa: E402
from dxf2gcode.domain.project.shape import Shape, Geos  # noqa: E402
from dxf2gcode.domain.project.layercontent import LayerContent, Layers  # noqa: E402

import dxf2gcode_stmove_gcode_test as stmove_test  # noqa: E402

from dxf2gcode.presentation.qt.qt_compat.QtWidgets import (  # noqa: E402
    QApplication, QWidget, QLineEdit, QLabel, QComboBox, QTreeView)
from dxf2gcode.presentation.qt.qt_compat import QtCore  # noqa: E402
from dxf2gcode.presentation.qt.treehandling import TreeHandler  # noqa: E402

_APP = None  # keep the QApplication alive


class _Shape(object):
    """Minimal stand-in for a shape with configurable parameter values."""

    def __init__(self, **values):
        self.__dict__.update(values)


def _shape(**values):
    return _Shape(**values)


class TestParameterState(unittest.TestCase):
    """Pure state logic (no GUI)."""

    def test_empty_selection(self):
        self.assertEqual(sps.parameter_state([], "f_g1_plane"), (sps.EMPTY, None))

    def test_single_standard_value(self):
        shape = _shape(f_g1_plane=100.0)
        self.assertEqual(sps.parameter_state([shape], "f_g1_plane"),
                         (sps.SAME, 100.0))
        self.assertTrue(sps.is_standard_value([shape], "f_g1_plane",
                                              lambda item: 100.0))
        self.assertFalse(sps.is_standard_value([shape], "f_g1_plane",
                                               lambda item: 200.0))

    def test_single_individual_value(self):
        shape = _shape(f_g1_plane=42.0)
        state, value = sps.parameter_state([shape], "f_g1_plane")
        self.assertEqual((state, value), (sps.SAME, 42.0))
        self.assertFalse(sps.is_standard_value([shape], "f_g1_plane",
                                               lambda item: 100.0))

    def test_several_equal_values(self):
        shapes = [_shape(milling_offset=0.2), _shape(milling_offset=0.2)]
        self.assertEqual(sps.parameter_state(shapes, "milling_offset"),
                         (sps.SAME, 0.2))

    def test_several_different_values(self):
        shapes = [_shape(milling_offset=0.0), _shape(milling_offset=0.2),
                  _shape(milling_offset=0.6)]
        state, value = sps.parameter_state(shapes, "milling_offset")
        self.assertEqual(state, sps.MIXED)
        self.assertIsNone(value)

    def test_missing_parameter_is_never_a_standard_value(self):
        shapes = [_shape(axis3_mill_depth=-1.0), _Shape()]  # second has none
        self.assertEqual(sps.parameter_state(shapes, "axis3_mill_depth"),
                         (sps.UNAVAILABLE, None))
        self.assertFalse(sps.is_standard_value(shapes, "axis3_mill_depth",
                                               lambda item: -1.0))

    def test_different_tool_defaults(self):
        # two shapes use different tools: each one uses its own default
        class _Layer(object):
            def __init__(self, tool_nr):
                self.tool_nr = tool_nr

        a = _shape(milling_offset=0.1, parentLayer=_Layer(1))
        b = _shape(milling_offset=0.7, parentLayer=_Layer(2))

        def default_of(shape):
            return {1: 0.1, 2: 0.7}[shape.parentLayer.tool_nr]

        state, _value = sps.parameter_state([a, b], "milling_offset")
        self.assertEqual(state, sps.MIXED)          # different numbers ...
        self.assertTrue(sps.is_standard_value([a, b], "milling_offset",
                                              default_of))  # ... own defaults

    def test_placeholder_is_not_a_number(self):
        # the mixed placeholder must never be usable as a parameter value
        mixed_text = "Different / Unterschiedlich"
        for candidate in (mixed_text, "Different", "Unterschiedlich"):
            try:
                float(candidate)
                self.fail("%r parsed as a number" % candidate)
            except ValueError:
                pass


class _Scene(object):
    def update(self):
        pass

    def repaint_shape(self, shape):
        pass


class _FakeWin(object):
    canvas_scene = _Scene()


class _FakeUI(object):
    pass


class _Harness(object):
    """Real TreeHandler with the mill settings widgets and a tree."""

    def __init__(self, layers):
        global _APP
        _APP = QApplication.instance() or QApplication([])
        g.window = _FakeWin()
        self.th = TreeHandler.__new__(TreeHandler)
        QWidget.__init__(self.th)
        self.th.ui = _FakeUI()
        self.th.auto_update_export_order = False
        self.th.ui.toolDiameterComboBox = QComboBox(self.th)
        self.th.ui.toolDiameterLabel = QLabel(self.th)
        self.th.ui.toolSpeedLabel = QLabel(self.th)
        self.th.ui.startRadiusLabel = QLabel(self.th)
        self.th.ui.leadRadiusLabel = QLabel(self.th)
        self.th.ui.leadLengthLabel = QLabel(self.th)
        self.th.ui.overcutLengthLabel = QLabel(self.th)
        self.th.ui.leadInComboBox = QComboBox(self.th)
        self.th.ui.leadOutComboBox = QComboBox(self.th)
        self.th.ui.overcutComboBox = QComboBox(self.th)
        self.line_edits = {}
        for name in ("zRetractionArealLineEdit", "zSafetyMarginLineEdit",
                     "zInfeedDepthLineEdit", "g1FeedXYLineEdit",
                     "g1FeedZLineEdit", "zInitialMillDepthLineEdit",
                     "zFinalMillDepthLineEdit", "millingOffsetLineEdit"):
            widget = QLineEdit(self.th)
            setattr(self.th.ui, name, widget)
            self.line_edits[name] = widget
        self.th.palette = self.th.ui.millingOffsetLineEdit.palette()
        self.th.display_tool_layer = None
        self.th.display_tool_shape = None
        self.th.display_tool_layers = []
        self.th.display_tool_shapes = []
        self.th.tool_nr = None
        for name in ("tool_diameter", "speed", "lead_radius", "lead_length",
                     "axis3_retract", "axis3_safe_margin",
                     "axis3_slice_depth", "axis3_start_mill_depth",
                     "axis3_mill_depth", "milling_offset", "f_g1_plane",
                     "f_g1_depth"):
            setattr(self.th, name, None)
        from dxf2gcode.presentation.qt.qt_compat.QtGui import QStandardItemModel
        self.th.layer_item_model = None
        self.th.entity_item_model = QStandardItemModel(self.th)
        self.view = QTreeView()
        self.th.ui.layersShapesTreeView = self.view
        self.th.ui.entitiesTreeView = QTreeView()
        from dxf2gcode.presentation.qt.qt_compat.QtGui import QStandardItemModel
        self.th.ui.entitiesTreeView.setModel(QStandardItemModel(self.th))
        self.th.ui.millSettingsFrame = QWidget(self.th)
        self.th.layers_list = list(layers)
        self.th.buildLayerTree(list(layers))
        self.model = self.th.layer_item_model
        self.all_shapes = []
        for layer in layers:
            for shape in getattr(layer, 'shapes', None) or []:
                self.all_shapes.append(shape)

    def select(self, shapes, order=None):
        """
        Select the given shapes in the tree and refresh the display.

        This drives the REAL widget update path (tree selection ->
        updateToolParameters) instead of calling the display directly.
        @param order: optional selection order (defaults to shapes)
        """
        wanted = list(order if order is not None else shapes)
        # keep the shape selection flags in sync (the application does this
        # through the canvas/tree synchronisation)
        deselected = QtCore.QItemSelection()
        selected = QtCore.QItemSelection()
        for shape in self.all_shapes:
            index = self.th.findLayerItemIndexFromShape(shape)
            if shape in wanted:
                shape.setSelected(True)
                selected.select(index, index)
            else:
                shape.setSelected(False)
                deselected.select(index, index)
        sel = self.view.selectionModel()
        sel.clearSelection()
        sel.select(selected,
                   QtCore.QItemSelectionModel.SelectionFlag.Select |
                   QtCore.QItemSelectionModel.SelectionFlag.Rows)
        # fire the REAL selection callback (the application connects it via
        # setSelectionCallback) - this is the path that had the bug
        self.th.actionOnSelectionChange(None, selected, deselected)

    def canvasSelect(self, shape):
        """
        Mimic a selection made on the canvas (graphic view): the shape
        toggles its selection and the tree is told about it
        (see canvas.py: shape.setSelected(...) + updateShapeSelection).
        """
        shape.setSelected(not shape.isSelected())
        self.th.updateShapeSelection(shape, shape.isSelected())
    def display(self, layers, shapes):
        self.th.displayToolParametersForSelection(layers, shapes)

    def text(self, name):
        return getattr(self.th.ui, name).text()

    def enabled(self, name):
        return getattr(self.th.ui, name).isEnabled()


def _make_shape(nr, tool_nr=1, **values):
    shape = stmove_test.make_shape(stmove_test.square_geos(), nr=nr, cut_cor=40)
    shape.parentLayer = LayerContent(nr, "L%d" % nr, [shape])
    shape.parentLayer.shapes = [shape]
    shape.parentLayer.tool_nr = tool_nr
    for name, value in values.items():
        setattr(shape, name, value)
    return shape


class TestParameterDisplay(unittest.TestCase):
    """Display of standard, individual and mixed values (real path)."""

    def test_knife_swivel_edit_mixed_selection_and_return_to_profile_default(self):
        original_mode = g.config.machine_type
        original_depth = g.config.vars.Drag_Knife_Options.swivel_depth
        try:
            g.config.machine_type = 'drag_knife'
            g.config.vars.Drag_Knife_Options.swivel_depth = -.03
            self.a.drag_swivel_depth = -.04
            self.b.drag_swivel_depth = -.08
            self.harness.select([self.a, self.b])
            widget = self.harness.th.ui.knifeSwivelLineEdit
            self.assertEqual(widget.text(), self.harness.th.tr('Different'))
            self.assertFalse(widget.isHidden())
            widget.setText('-.06')
            widget.setModified(True)
            widget.editingFinished.emit()
            self.assertEqual((self.a.drag_swivel_depth, self.b.drag_swivel_depth), (-.06, -.06))
            self.harness.select([self.a])
            widget.clear()
            widget.setModified(True)
            widget.editingFinished.emit()
            self.assertIsNone(self.a._drag_swivel_depth)
            self.assertEqual(self.a.drag_swivel_depth, -.03)
            self.assertEqual(self.b.drag_swivel_depth, -.06)
            self.assertEqual(widget.text(), '-0.03')
            g.config.machine_type = 'milling'
            self.harness.th.updateToolParameters()
            self.assertTrue(widget.isHidden())
        finally:
            g.config.machine_type = original_mode
            g.config.vars.Drag_Knife_Options.swivel_depth = original_depth

    @staticmethod
    def _text_color(widget):
        from dxf2gcode.presentation.qt.qt_compat.QtGui import QPalette
        return widget.palette().color(QPalette.ColorRole.WindowText).name()

    @staticmethod
    def _gray_name():
        from dxf2gcode.presentation.qt.qt_compat.QtGui import QColor
        return QColor(QtCore.Qt.GlobalColor.gray).name()

    def setUp(self):
        self.a = _make_shape(0, milling_offset=0.0)
        self.b = _make_shape(1, milling_offset=0.2)
        self.c = _make_shape(2, milling_offset=0.6)
        for shape in (self.a, self.b, self.c):
            shape.f_g1_plane = 100.0
            shape.f_g1_depth = 50.0
        self.layers = [shape.parentLayer for shape in (self.a, self.b, self.c)]
        self.harness = _Harness(self.layers)

    def test_different_values_show_the_placeholder(self):
        self.harness.select([self.a, self.b, self.c])
        self.assertEqual(self.harness.text("millingOffsetLineEdit"),
                         self.harness.th.tr("Different"))
        self.assertEqual((self.a.milling_offset, self.b.milling_offset,
                          self.c.milling_offset), (0.0, 0.2, 0.6))

    def test_two_shapes_with_different_values_show_the_placeholder(self):
        self.harness.select([self.a, self.b])
        self.assertEqual(self.harness.text("millingOffsetLineEdit"),
                         self.harness.th.tr("Different"))

    def test_selection_order_does_not_matter(self):
        self.harness.select([self.a, self.b, self.c])
        first = self.harness.text("millingOffsetLineEdit")
        self.harness.select([self.a, self.b, self.c],
                            order=[self.c, self.b, self.a])
        self.assertEqual(self.harness.text("millingOffsetLineEdit"), first)
        self.assertEqual(first, self.harness.th.tr("Different"))

    def test_repeated_refresh_keeps_the_placeholder(self):
        self.harness.select([self.a, self.b])
        expected = self.harness.th.tr("Different")
        self.assertEqual(self.harness.text("millingOffsetLineEdit"), expected)
        # a refresh (eg. after a configuration change) must not fall back to
        # the value of the first shape
        self.harness.th.updateToolParameters()
        self.harness.th.updateToolParameters()
        self.assertEqual(self.harness.text("millingOffsetLineEdit"), expected)

    def test_equal_values_show_the_common_value(self):
        self.harness.select([self.a, self.b, self.c])
        self.assertEqual(self.harness.text("g1FeedXYLineEdit"), "100.0")
        self.assertEqual(self.harness.text("g1FeedZLineEdit"), "50.0")

    def test_all_parameter_fields_follow_the_selection(self):
        for shape, factor in ((self.a, 1.0), (self.b, 2.0), (self.c, 3.0)):
            shape.axis3_start_mill_depth = -1.0 * factor
            shape.axis3_slice_depth = -2.0 * factor
            shape.axis3_mill_depth = -3.0 * factor
            shape.f_g1_plane = 100.0 * factor
            shape.f_g1_depth = 50.0 * factor
            shape.milling_offset = 0.1 * factor
        self.harness.select([self.a, self.b, self.c])
        for name in ("zInitialMillDepthLineEdit", "zInfeedDepthLineEdit",
                     "zFinalMillDepthLineEdit", "g1FeedXYLineEdit",
                     "g1FeedZLineEdit", "millingOffsetLineEdit"):
            self.assertEqual(self.harness.text(name),
                             self.harness.th.tr("Different"), name)
        # the parameters that stay equal keep showing the common value
        for shape in (self.a, self.b, self.c):
            shape.f_g1_plane = 321.0
        self.harness.th.updateToolParameters()
        self.assertEqual(self.harness.text("g1FeedXYLineEdit"), "321.0")

    def test_standard_value_is_de_emphasized_but_enabled(self):
        default = float(g.config.vars.Depth_Coordinates["axis3_mill_depth"])
        for shape in (self.a, self.b, self.c):
            shape.axis3_mill_depth = default
        self.harness.select([self.a, self.b, self.c])
        widget = self.harness.line_edits["zFinalMillDepthLineEdit"]
        self.assertTrue(widget.isEnabled())
        self.assertEqual(self.harness.text("zFinalMillDepthLineEdit"),
                         str(round(default, 4)))
        self.assertEqual(self._text_color(widget), self._gray_name())

    def test_individual_value_is_not_de_emphasized(self):
        for shape in (self.a, self.b, self.c):
            shape.axis3_mill_depth = -7.5
        self.harness.select([self.a, self.b, self.c])
        widget = self.harness.line_edits["zFinalMillDepthLineEdit"]
        self.assertEqual(self.harness.text("zFinalMillDepthLineEdit"), "-7.5")
        self.assertNotEqual(self._text_color(widget), self._gray_name())

    def test_nothing_selected_shows_no_values(self):
        # Unified behaviour: without a selection (and after startup) no values
        # at all are shown - for the tool and for the shape fields.
        self.harness.select([self.a])          # first show some values ...
        self.harness.select([])                # ... then clear the selection
        for widget in self.harness.th._mill_parameter_widgets():
            self.assertEqual(widget.text(), "",
                             "field %s is not empty" % widget.objectName())
        self.assertFalse(self.harness.th.ui.millSettingsFrame.isEnabled())

    def test_tool_values_are_always_shown_de_emphasized(self):
        # The tool values can only be changed through the tool selection, so
        # they are always grey (they are the tool default by definition).
        self.harness.select([self.a])
        gray = self._gray_name()
        for name in ("toolDiameterLabel", "toolSpeedLabel", "leadRadiusLabel",
                     "leadLengthLabel", "overcutLengthLabel"):
            widget = getattr(self.harness.th.ui, name)
            self.assertNotEqual(widget.text(), "")
            self.assertEqual(self._text_color(widget), gray)

    def test_refresh_without_selection_shows_no_values(self):
        # A refresh (e.g. after a configuration change) must not bring the
        # values of a previously selected shape back when nothing is selected.
        self.harness.select([self.a])
        self.harness.select([])
        self.harness.th.updateToolParameters()
        for widget in self.harness.th._mill_parameter_widgets():
            self.assertEqual(widget.text(), "")

    def test_tool_update_without_selection_shows_no_values(self):
        # The tool dropdown is also set up at startup (with no selection); it
        # must not fill the tool values then.
        self.harness.th.toolUpdate()
        for name in ("toolDiameterLabel", "toolSpeedLabel", "leadRadiusLabel",
                     "leadLengthLabel", "overcutLengthLabel"):
            self.assertEqual(getattr(self.harness.th.ui, name).text(), "")

    def test_canvas_deselection_clears_the_fields(self):
        # Deselecting the last shape on the canvas must clear all fields (not
        # keep showing the values of the deselected shape).
        self.harness.canvasSelect(self.a)
        self.assertNotEqual(self.harness.text("millingOffsetLineEdit"), "")
        self.harness.canvasSelect(self.a)      # deselect again
        for widget in self.harness.th._mill_parameter_widgets():
            self.assertEqual(widget.text(), "")

    def test_switching_the_selection_updates_the_display(self):
        self.harness.select([self.a])
        self.assertEqual(self.harness.text("millingOffsetLineEdit"), "0.0")
        self.harness.select([self.a, self.b])
        self.assertEqual(self.harness.text("millingOffsetLineEdit"),
                         self.harness.th.tr("Different"))
        self.harness.select([self.b])
        self.assertEqual(self.harness.text("millingOffsetLineEdit"), "0.2")

    def test_canvas_selection_shows_the_placeholder(self):
        # selecting two shapes with different values on the canvas must
        # also show "Different" (the canvas path uses updateShapeSelection)
        self.harness.canvasSelect(self.a)
        self.assertEqual(self.harness.text("millingOffsetLineEdit"), "0.0")
        self.harness.canvasSelect(self.b)
        self.assertEqual(self.harness.text("millingOffsetLineEdit"),
                         self.harness.th.tr("Different"))
        self.harness.canvasSelect(self.a)      # deselect a again
        self.assertEqual(self.harness.text("millingOffsetLineEdit"), "0.2")
    def test_no_shapes_disables_the_shape_parameters(self):
        self.harness.display(self.layers, [])
        self.assertEqual(self.harness.text("millingOffsetLineEdit"), "")
        self.assertFalse(self.harness.enabled("millingOffsetLineEdit"))
        self.assertTrue(self.harness.enabled("zRetractionArealLineEdit"))


class TestParameterEditing(unittest.TestCase):
    """Editing a field only changes values on a confirmed new value."""

    def setUp(self):
        self.a = _make_shape(0, milling_offset=0.0)
        self.b = _make_shape(1, milling_offset=0.2)
        self.layers = [self.a.parentLayer, self.b.parentLayer]
        self.harness = _Harness(self.layers)
        self.harness.select([self.a, self.b])

    def _widget(self):
        return self.harness.line_edits["millingOffsetLineEdit"]

    def test_placeholder_is_not_applied(self):
        widget = self._widget()
        self.assertEqual(widget.text(), self.harness.th.tr("Different"))
        widget.setFocus()
        self.harness.th.toolParameterMillingOffsetUpdate()
        self.harness.th.updateToolParameters()
        self.assertEqual(self.a.milling_offset, 0.0)
        self.assertEqual(self.b.milling_offset, 0.2)
        self.assertEqual(widget.text(), self.harness.th.tr("Different"))

    def test_focus_and_leave_change_nothing(self):
        widget = self._widget()
        widget.setFocus()
        widget.clearFocus()
        widget.setFocus()
        self.harness.th.toolParameterMillingOffsetUpdate()
        self.assertEqual((self.a.milling_offset, self.b.milling_offset),
                         (0.0, 0.2))

    def test_confirmed_value_applies_to_all_and_is_shown(self):
        widget = self._widget()
        widget.setText("0.35")
        self.harness.th.toolParameterMillingOffsetUpdate()
        self.harness.th.updateToolParameters()
        self.assertEqual(self.a.milling_offset, 0.35)
        self.assertEqual(self.b.milling_offset, 0.35)
        self.assertEqual(widget.text(), "0.35")

    def test_value_is_applied_to_the_canvas_selection(self):
        # shapes selected on the canvas: an entered value must be applied
        # to ALL of them (not only to the last one)
        h = self.harness
        h.select([])                      # clear the tree selection
        h.canvasSelect(self.a)
        h.canvasSelect(self.b)
        widget = h.line_edits["millingOffsetLineEdit"]
        self.assertEqual(widget.text(), h.th.tr("Different"))
        widget.setText("0.45")
        h.th.toolParameterMillingOffsetUpdate()
        self.assertEqual(self.a.milling_offset, 0.45)
        self.assertEqual(self.b.milling_offset, 0.45)
        h.th.updateToolParameters()
        self.assertEqual(widget.text(), "0.45")
    def test_other_parameters_keep_their_values(self):
        self.a.axis3_mill_depth = -2.0
        self.b.axis3_mill_depth = -5.0
        widget = self._widget()
        widget.setText("0.4")
        self.harness.th.toolParameterMillingOffsetUpdate()
        self.harness.th.updateToolParameters()
        self.assertEqual(self.a.axis3_mill_depth, -2.0)
        self.assertEqual(self.b.axis3_mill_depth, -5.0)

    def test_single_selection_value_still_works(self):
        self.harness.select([self.a])
        widget = self._widget()
        self.assertEqual(widget.text(), "0.0")
        widget.setText("-0.15")
        self.harness.th.toolParameterMillingOffsetUpdate()
        self.harness.th.updateToolParameters()
        self.assertEqual(self.a.milling_offset, -0.15)
        self.assertEqual(self.b.milling_offset, 0.2)

    def test_rounded_display_preserves_original_until_explicit_edit(self):
        self.a.milling_offset = -.01234567
        self.harness.select([self.a])
        widget = self._widget()
        self.assertEqual(widget.text(), '-0.0123')
        self.harness.th.toolParameterMillingOffsetUpdate()
        self.assertEqual(self.a.milling_offset, -.01234567)
        # Retyping the displayed value deliberately accepts its rounding.
        widget.setModified(True)
        self.harness.th.toolParameterMillingOffsetUpdate()
        self.assertEqual(self.a.milling_offset, -.0123)
        widget.setText('-0,0005')
        self.harness.th.toolParameterMillingOffsetUpdate()
        self.assertEqual(self.a.milling_offset, -.0005)


if __name__ == "__main__":
    unittest.main(verbosity=2)
