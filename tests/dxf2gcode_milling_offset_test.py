# -*- coding: utf-8 -*-
"""
Regression tests for the per-shape additional offset (finishing allowance)
`shape.milling_offset` added to the software cutter compensation.

Semantics under test:
  * the value is added to the tool radius used for the compensated toolpath
    (comp_offset = tool_radius + milling_offset),
  * a positive value moves the toolpath away from the outline on the
    compensated side (outward for outside contours, inward for inside
    contours) and therefore leaves more material,
  * 0.0 (and a missing value in older projects) keeps the previous behaviour.

Run from the repository root:

    python -m unittest discover -s tests -t tests -p "dxf2gcode_milling_offset_test.py" -v
"""
from __future__ import absolute_import

import ast
import contextlib
import io
import os
import re
import tempfile
import logging
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import sys
_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [_TEST_DIR, os.path.join(os.path.dirname(_TEST_DIR), "source")]
from toolpath_test_support import serialize_gcode, serialize_shape_geometry


def _init_config():
    import dxf2gcode.bootstrap.runtime_state as g
    from dxf2gcode.adapters.config.runtime_config import MyConfig

    if getattr(g, "config", None) is None:
        g.folder = tempfile.mkdtemp(prefix="d2g_milling_offset_test_")
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
                 "Core.Project", "Gui.TreeHandling"):
        logging.getLogger(name).setLevel(logging.CRITICAL)


_init_config()

import dxf2gcode.bootstrap.runtime_state as g  # noqa: E402

from dxf2gcode.domain.project.shape import Shape, Geos  # noqa: E402
from dxf2gcode.domain.geometry.linegeo import LineGeo  # noqa: E402
from dxf2gcode.domain.geometry.point import Point  # noqa: E402
from dxf2gcode.domain.project.layercontent import LayerContent, Layers, Shapes  # noqa: E402
from dxf2gcode.domain.toolpath.stmove import StMove  # noqa: E402
from dxf2gcode.domain.toolpath.leadmove import LEAD_OFF  # noqa: E402
from dxf2gcode.domain.project.project import Project  # noqa: E402

from dxf2gcode_stmove_gcode_test import (  # noqa: E402
    make_postpro, make_shape, build_stmove, square_geos, norm)
import dxf2gcode_pocket_edge_clearance_test as pocket  # noqa: E402

from dxf2gcode.presentation.qt.qt_compat.QtWidgets import (  # noqa: E402
    QApplication, QWidget, QLineEdit, QTreeView)
from dxf2gcode.presentation.qt.qt_compat import QtCore  # noqa: E402
from dxf2gcode.presentation.qt.treehandling import TreeHandler  # noqa: E402

_APP = None  # keep the QApplication alive (otherwise widgets are deleted)


def stmove_bbox(st):
    """Bounding box of all start/end points of an StMove geometry."""
    xs, ys = [], []
    for geo in st.geos:
        for point in (getattr(geo, "Ps", None), getattr(geo, "Pe", None)):
            if point is not None:
                xs.append(point.x)
                ys.append(point.y)
    if not xs:
        return None
    return (min(xs), max(xs), min(ys), max(ys))


def stmove_geos_key(st):
    """Canonical string of all points of an StMove geometry."""
    parts = []
    for geo in st.geos:
        p = getattr(geo, "Ps", None)
        e = getattr(geo, "Pe", None)
        parts.append("%s:%s" % (p, e))
    return "|".join(parts)


def software_comp():
    """Enable the software cutter compensation for the test (default is the
    machine compensation, which cannot apply the additional offset)."""
    g.config.vars.Cutter_Compensation["done_by_machine"] = False


def machine_comp():
    g.config.vars.Cutter_Compensation["done_by_machine"] = True


class TestMillingOffsetGeometry(unittest.TestCase):
    """The additional offset shifts the compensated toolpath."""

    def setUp(self):
        software_comp()

    def _bbox(self, extra, cut_cor=41, cw=True, tool_diameter=2.0,
              size=10.0):
        shape = make_shape(square_geos(size), cut_cor=cut_cor, cw=cw,
                           tool_diameter=tool_diameter)
        shape.milling_offset = extra
        # The test checks the compensated toolpath, not the lead in.
        shape.parentLayer.lead_in_mode = LEAD_OFF
        build_stmove(shape)
        return stmove_bbox(shape.stmove)

    def test_zero_offset_keeps_previous_behaviour(self):
        # 0.0 and a shape without the attribute (e.g. an object created
        # before this feature) must produce exactly the same toolpath
        shape_a = make_shape(square_geos(10.0), cut_cor=41, cw=True,
                             tool_diameter=2.0)
        shape_a.milling_offset = 0.0
        shape_b = make_shape(square_geos(10.0), cut_cor=41, cw=True,
                             tool_diameter=2.0)
        del shape_b.milling_offset
        build_stmove(shape_a)
        build_stmove(shape_b)
        self.assertEqual(stmove_geos_key(shape_a.stmove),
                         stmove_geos_key(shape_b.stmove))
        # the plain cutter compensation (radius 1.0) is unchanged
        self.assertEqual(self._bbox(0.0), (-1.0, 11.0, -1.0, 11.0))

    def test_positive_offset_outside_contour(self):
        # outside contour (G41 + cw): positive offset leaves more material,
        # i.e. the toolpath moves further outward
        self.assertEqual(self._bbox(0.0), (-1.0, 11.0, -1.0, 11.0))
        self.assertEqual(self._bbox(0.5), (-1.5, 11.5, -1.5, 11.5))

    def test_negative_offset_outside_contour(self):
        self.assertEqual(self._bbox(-0.3), (-0.7, 10.7, -0.7, 10.7))

    def test_positive_offset_inside_contour(self):
        # inside contour (G42 + cw): positive offset moves further inward,
        # which also leaves more material at the wall
        self.assertEqual(self._bbox(0.0, cut_cor=42), (1.0, 9.0, 1.0, 9.0))
        self.assertEqual(self._bbox(0.5, cut_cor=42), (1.5, 8.5, 1.5, 8.5))

    def test_offset_sign_is_independent_of_contour_direction(self):
        # the same physical behaviour for the opposite contour direction
        self.assertEqual(self._bbox(0.0, cut_cor=41, cw=False),
                         (1.0, 9.0, 1.0, 9.0))
        self.assertEqual(self._bbox(0.5, cut_cor=41, cw=False),
                         (1.5, 8.5, 1.5, 8.5))
        self.assertEqual(self._bbox(0.0, cut_cor=42, cw=False),
                         (-1.0, 11.0, -1.0, 11.0))
        self.assertEqual(self._bbox(0.5, cut_cor=42, cw=False),
                         (-1.5, 11.5, -1.5, 11.5))

    def test_two_shapes_do_not_influence_each_other(self):
        shape_a = make_shape(square_geos(10.0), cut_cor=41, cw=True,
                             tool_diameter=2.0, nr=0)
        shape_b = make_shape(square_geos(10.0), cut_cor=41, cw=True,
                             tool_diameter=2.0, nr=1)
        shape_a.milling_offset = 0.5
        shape_b.milling_offset = -0.3
        # The test checks the compensated toolpath, not the lead in.
        shape_a.parentLayer.lead_in_mode = LEAD_OFF
        shape_b.parentLayer.lead_in_mode = LEAD_OFF
        build_stmove(shape_a)
        build_stmove(shape_b)
        self.assertEqual(stmove_bbox(shape_a.stmove),
                         (-1.5, 11.5, -1.5, 11.5))
        self.assertEqual(stmove_bbox(shape_b.stmove),
                         (-0.7, 10.7, -0.7, 10.7))
        # changing one shape must not touch the other
        shape_a.milling_offset = 0.0
        build_stmove(shape_a)
        self.assertEqual(stmove_bbox(shape_a.stmove),
                         (-1.0, 11.0, -1.0, 11.0))
        self.assertEqual(stmove_bbox(shape_b.stmove),
                         (-0.7, 10.7, -0.7, 10.7))

    def test_zero_offset_gcode_is_unchanged(self):
        shape_a = make_shape(square_geos(10.0), cut_cor=41, cw=True,
                             tool_diameter=2.0)
        shape_a.milling_offset = 0.0
        shape_b = make_shape(square_geos(10.0), cut_cor=41, cw=True,
                             tool_diameter=2.0)
        del shape_b.milling_offset
        build_stmove(shape_a)
        build_stmove(shape_b)
        self.assertEqual(norm(serialize_gcode(shape_a, make_postpro())),
                         norm(serialize_gcode(shape_b, make_postpro())))

    def test_offset_cannot_cancel_the_cutter_compensation(self):
        # a negative offset larger than the tool radius would be meaningless;
        # the shape is skipped instead of producing a mirrored toolpath
        shape = make_shape(square_geos(10.0), cut_cor=41, cw=True,
                           tool_diameter=2.0)
        shape.milling_offset = -2.0  # tool radius is 1.0
        build_stmove(shape)
        self.assertEqual(len(shape.stmove.geos), 0)


class TestMillingOffsetDefaultFlow(unittest.TestCase):
    """The tool table provides the default value for the individual offset."""

    def setUp(self):
        self._saved = g.config.vars.Tool_Parameters['2']['milling_offset']

    def tearDown(self):
        g.config.vars.Tool_Parameters['2']['milling_offset'] = self._saved

    def test_layer_uses_tool_default(self):
        g.config.vars.Tool_Parameters['2']['milling_offset'] = 0.7
        shape = make_shape(square_geos(10.0), nr=0)
        layer = LayerContent(0, "MILL:ToolNr:2", [shape])
        shape.parentLayer = layer
        layer.overrideDefaults()
        self.assertEqual(layer.tool_nr, 2)
        self.assertAlmostEqual(layer.milling_offset, 0.7)
        self.assertAlmostEqual(shape.milling_offset, 0.7)

    def test_layer_identifier_overrides_the_tool_default(self):
        g.config.vars.Tool_Parameters['2']['milling_offset'] = 0.7
        shape = make_shape(square_geos(10.0), nr=0)
        layer = LayerContent(0, "MILL:ToolNr:2 MillingOffset:0.25", [shape])
        shape.parentLayer = layer
        layer.overrideDefaults()
        self.assertAlmostEqual(shape.milling_offset, 0.25)

    def test_default_is_zero_without_any_setting(self):
        shape = make_shape(square_geos(10.0), nr=0)
        layer = LayerContent(0, "MILL:ToolNr:1", [shape])
        shape.parentLayer = layer
        layer.overrideDefaults()
        self.assertAlmostEqual(shape.milling_offset, 0.0)
        self.assertAlmostEqual(layer.milling_offset, 0.0)

    def test_measuring_unit_change_scales_the_offset(self):
        shape = make_shape(square_geos(10.0), nr=0)
        layer = LayerContent(0, "L0", [shape])
        layer.milling_offset = 1.0
        shape.milling_offset = 1.0
        layer.changeMeasuringUnits(1, 0)  # mm -> inch
        self.assertAlmostEqual(shape.milling_offset, 1.0 / 25.4)
        self.assertAlmostEqual(layer.milling_offset, 1.0 / 25.4)


class TestMillingOffsetPocketFill(unittest.TestCase):
    """Pocket fill follows the additional offset (finishing allowance).

    The additional offset shifts the contour the tool really mills, so the
    pocket that has to be cleared GROWS (outside contour / G41, the fill clears
    beyond the outline up to the shifted contour) or SHRINKS (inside contour /
    pocket / G42, the fill retreats and leaves material). The fill is derived
    from that shifted contour ("wall"), so it follows the offset.
    ``milling_offset = 0.0`` keeps the historical geometry exactly.
    """

    TOOL_DIA = 2.0
    TOOL_RAD = TOOL_DIA / 2.0
    PCT = 20.0
    CLEARANCE = TOOL_DIA * PCT / 100.0      # 0.4 mm

    def setUp(self):
        self._saved = (
            g.config.vars.Pocketing["pocket_compensation_mode"],
            g.config.vars.Pocketing["pocket_edge_clearance"],
            g.config.vars.Cutter_Compensation["done_by_machine"],
        )

    def tearDown(self):
        (g.config.vars.Pocketing["pocket_compensation_mode"],
         g.config.vars.Pocketing["pocket_edge_clearance"],
         g.config.vars.Cutter_Compensation["done_by_machine"]) = self._saved

    def _build(self, cut_cor, extra, cw=True, mode="selected_direction",
               machine=False, tool_dia=None, pct=None):
        g.config.vars.Pocketing["pocket_compensation_mode"] = mode
        g.config.vars.Pocketing["pocket_edge_clearance"] = (
            self.PCT if pct is None else pct)
        g.config.vars.Cutter_Compensation["done_by_machine"] = machine
        shape = pocket.make_shape(pocket.rect_geos())
        if not cw:
            shape.reverse()
        shape.axis3_start_mill_depth = 0.0
        shape.axis3_mill_depth = -1.0
        shape.axis3_slice_depth = 0.5
        shape.f_g1_plane = 800
        shape.f_g1_depth = 150
        shape.cut_cor = cut_cor
        shape.Drill = False
        shape.Pocket = True
        if extra is None:
            del shape.milling_offset          # pre-feature object
        else:
            shape.milling_offset = extra
        layer = LayerContent(0, "L", [shape])
        layer.tool_diameter = self.TOOL_DIA if tool_dia is None else tool_dia
        layer.axis3_retract = 9.91
        layer.axis3_safe_margin = 3.05
        shape.parentLayer = layer
        shape.calc_bounding_box()
        with contextlib.redirect_stdout(io.StringIO()):
            st = StMove(shape)
        shape.stmove = st
        return shape, st

    @staticmethod
    def _bbox(geos):
        xs = [q.x for gg in geos for q in (gg.Ps, gg.Pe)]
        ys = [q.y for gg in geos for q in (gg.Ps, gg.Pe)]
        return (min(xs), max(xs), min(ys), max(ys))

    def _measure(self, cut_cor, extra, **kwargs):
        shape, st = self._build(cut_cor, extra, **kwargs)
        boundary, fill = pocket.split(st)
        reference = st.pocket_wall_reference
        return {
            "shape": shape, "st": st, "boundary": boundary, "fill": fill,
            "fill_bbox": self._bbox(fill) if fill else None,
            "ref_bbox": self._bbox(reference) if reference else None,
            "side": pocket.boundary_side(
                pocket._flatten(shape.geos), boundary),
            "fill_dist": pocket.min_dist(fill, shape.geos) if fill else 0.0,
        }

    # -- no offset: historical behaviour ----------------------------------
    def test_zero_offset_is_exactly_the_historical_behaviour(self):
        with_offset, _ = self._build(41, 0.0)
        without_attr, _ = self._build(41, None)
        self.assertEqual(norm(serialize_gcode(with_offset, make_postpro())),
                         norm(serialize_gcode(without_attr, make_postpro())))
        m0 = self._measure(41, 0.0)
        self.assertIsNone(m0["ref_bbox"])            # no shifted contour
        self.assertAlmostEqual(m0["fill_dist"], self.CLEARANCE, delta=0.10)

    def test_zero_offset_gcode_identical_in_all_modes(self):
        for mode in ("selected_direction", "always_inward"):
            for cut_cor in (40, 41, 42):
                with_off, _ = self._build(cut_cor, 0.0, mode=mode)
                without, _ = self._build(cut_cor, None, mode=mode)
                self.assertEqual(
                    norm(serialize_gcode(with_off, make_postpro())),
                    norm(serialize_gcode(without, make_postpro())),
                    "%s cc=%d" % (mode, cut_cor))

    # -- outside contour (G41): the pocket grows ---------------------------
    def test_outside_contour_pocket_grows_by_the_offset(self):
        grid = 0.5      # fill grid resolution of the 2 mm tool
        for e in (0.2, 0.6):
            m0 = self._measure(41, 0.0)
            m1 = self._measure(41, e)
            self.assertEqual(m0["side"], "out")
            x0, x1, y0, y1 = m0["fill_bbox"]
            ex0, ex1, ey0, ey1 = m1["fill_bbox"]
            # the pocket grows outward on every side by the offset
            self.assertLess(ex0, x0 - e + grid, "left  e=%.1f" % e)
            self.assertGreater(ex1, x1 + e - grid, "right e=%.1f" % e)
            self.assertLess(ey0, y0 - e + grid, "bottom e=%.1f" % e)
            self.assertGreater(ey1, y1 + e - grid, "top    e=%.1f" % e)
            # the shifted contour the fill is derived from is that much larger
            rx0, rx1, ry0, ry1 = m1["ref_bbox"]
            self.assertAlmostEqual(rx0, x0 - e - 0.5, delta=0.6)

    def test_small_tool_outside_contour_clears_beyond_the_outline(self):
        # outline is x[0..40], y[0..30]: with tool dia 0.5 and a 0.6 allowance
        # the pocket must be cleared beyond the outline (as reported)
        m0 = self._measure(41, 0.0, tool_dia=0.5)
        m1 = self._measure(41, 0.6, tool_dia=0.5)
        x0, x1, y0, y1 = m0["fill_bbox"]
        ex0, ex1, ey0, ey1 = m1["fill_bbox"]
        self.assertLess(ex0, x0)             # grew (starts further outside)...
        self.assertLess(ex0, 0.0)            # ... up to beyond the outline
        self.assertLess(ey0, 0.0)
        self.assertGreater(ex1, 40.0)
        self.assertGreater(ey1, 30.0)

    # -- inside contour / pocket: it shrinks -------------------------------
    def test_inside_contour_pocket_shrinks_by_the_offset(self):
        grid = 0.5
        m0 = self._measure(42, 0.0)
        m1 = self._measure(42, 0.6)
        self.assertEqual(m0["side"], "in")
        x0, x1, y0, y1 = m0["fill_bbox"]
        ex0, ex1, ey0, ey1 = m1["fill_bbox"]
        self.assertGreater(ex0, x0 + 0.6 - grid)
        self.assertLess(ex1, x1 - 0.6 + grid)
        self.assertGreater(ey0, y0 + 0.6 - grid)
        self.assertLess(ey1, y1 - 0.6 + grid)
        # the shifted contour is the outline inset by the offset
        rx0, rx1, ry0, ry1 = m1["ref_bbox"]
        self.assertAlmostEqual(rx0, 0.6, delta=0.05)
        self.assertAlmostEqual(rx1, 39.4, delta=0.05)

    def test_inside_contour_negative_offset_grows_the_pocket(self):
        # a negative offset removes material at the outline: the shifted
        # contour grows and the fill clears more
        m0 = self._measure(42, 0.0)
        mneg = self._measure(42, -0.3)
        x0, x1, y0, y1 = m0["fill_bbox"]
        ex0, ex1, ey0, ey1 = mneg["fill_bbox"]
        self.assertLess(ex0, x0)
        self.assertGreater(ex1, x1)
        self.assertLess(mneg["ref_bbox"][0], 0.0)

    def test_all_modes_follow_the_offset(self):
        # every pocket mode with a positive allowance derives the fill from the
        # shifted contour (only plain G40 without cutter compensation cannot,
        # because there is no compensation side to shift to)
        for mode in ("selected_direction", "always_inward"):
            for cut_cor in (41, 42):
                m = self._measure(cut_cor, 0.6, mode=mode, tool_dia=0.5)
                self.assertIsNotNone(m["ref_bbox"],
                                     "%s cc=%d" % (mode, cut_cor))
                self.assertTrue(m["fill"], "%s cc=%d" % (mode, cut_cor))
                ex0, ex1, ey0, ey1 = m["fill_bbox"]
                rx0, rx1, ry0, ry1 = m["ref_bbox"]
                self.assertGreaterEqual(ex0, rx0 - 1e-6, mode)
                self.assertLessEqual(ex1, rx1 + 1e-6, mode)
        # G40 + selected_direction keeps the original contour
        m40 = self._measure(40, 0.6, mode="selected_direction")
        self.assertIsNone(m40["ref_bbox"])

    def test_machine_compensation_ignores_the_offset(self):
        m0 = self._measure(41, 0.0, machine=True)
        m1 = self._measure(41, 0.6, machine=True)
        self.assertIsNone(m1["ref_bbox"])
        self.assertEqual(m0["fill_bbox"], m1["fill_bbox"])
        self.assertEqual(norm(serialize_gcode(m0["shape"], make_postpro())),
                         norm(serialize_gcode(m1["shape"], make_postpro())))

    def test_offset_cancelling_the_compensation_skips_the_shape(self):
        shape, st = self._build(41, -self.TOOL_RAD)
        self.assertEqual(len(st.geos), 0)


class _Scene(object):
    def update(self):
        pass

    def repaint_shape(self, shape):
        pass


class _FakeWin(object):
    canvas_scene = _Scene()
    layerContents = None


class _FakeUI(object):
    pass


class _Harness(object):
    """Real TreeHandler with a fake UI holding the offset line edit."""

    def __init__(self, layers):
        global _APP
        _APP = QApplication.instance() or QApplication([])
        g.window = _FakeWin()
        g.window.layerContents = layers
        self.th = TreeHandler.__new__(TreeHandler)
        QWidget.__init__(self.th)
        self.th.auto_update_export_order = False
        self.th.layer_item_model = None
        self.th.entity_item_model = None
        self.th.ui = _FakeUI()
        self.th.ui.millingOffsetLineEdit = QLineEdit(self.th)
        self.th.palette = self.th.ui.millingOffsetLineEdit.palette()
        self.view = QTreeView()
        self.th.ui.layersShapesTreeView = self.view
        self.th.layers_list = list(layers)
        self.th.buildLayerTree(list(layers))
        self.model = self.th.layer_item_model

    def select(self, shape):
        sel = self.view.selectionModel()
        sel.clearSelection()
        index = self.th.findLayerItemIndexFromShape(shape)
        sel.select(index, QtCore.QItemSelectionModel.SelectionFlag.Select |
                   QtCore.QItemSelectionModel.SelectionFlag.Rows)
        self.th.display_tool_layer = shape.parentLayer
        self.th.display_tool_shape = shape


class TestMillingOffsetShapeWindow(unittest.TestCase):
    """Editing the value in the contour (shape) window."""

    def test_line_edit_applies_the_value_to_the_selected_shape(self):
        software_comp()
        shape = make_shape(square_geos(10.0), cut_cor=41, cw=True,
                           tool_diameter=2.0, nr=0)
        build_stmove(shape)
        harness = _Harness([shape.parentLayer])
        harness.select(shape)
        self.assertEqual(shape.milling_offset, 0.0)

        harness.th.ui.millingOffsetLineEdit.setText("0.5")
        harness.th.toolParameterMillingOffsetUpdate()
        self.assertAlmostEqual(shape.milling_offset, 0.5)

        harness.th.ui.millingOffsetLineEdit.setText("-0.25")
        harness.th.toolParameterMillingOffsetUpdate()
        self.assertAlmostEqual(shape.milling_offset, -0.25)

    def test_only_selected_shapes_are_changed(self):
        software_comp()
        shape_a = make_shape(square_geos(10.0), nr=0)
        shape_b = make_shape(square_geos(10.0), nr=1)
        shape_a.parentLayer.shapes = Shapes([shape_a, shape_b])
        shape_b.parentLayer = shape_a.parentLayer
        harness = _Harness([shape_a.parentLayer])
        harness.select(shape_a)
        harness.th.ui.millingOffsetLineEdit.setText("0.4")
        harness.th.toolParameterMillingOffsetUpdate()
        self.assertAlmostEqual(shape_a.milling_offset, 0.4)
        self.assertAlmostEqual(shape_b.milling_offset, 0.0)


class _FakeAction(object):
    def isChecked(self):
        return False


class _FakeUIActions(object):
    def __init__(self):
        self.actionSplitLineSegments = _FakeAction()
        self.actionAutomaticCutterCompensation = _FakeAction()


class _FakeParent(object):
    """Minimal mainwindow stand-in for Project export/load."""

    def __init__(self, layers):
        self.layerContents = layers
        self.TreeHandler = self
        self.filename = ""
        self.cont_scale = 1
        self.cont_rotate = 0
        self.cont_dx = 0
        self.cont_dy = 0
        self.cont_mirrorx = False
        self.cont_mirrory = False
        self.ui = _FakeUIActions()
        self.newNumber = 1000

    def updateExportOrder(self, flag=True):
        for layer in self.layerContents:
            layer.exp_order_complete = list(range(len(layer.shapes)))

    def connectToolbarToConfig(self, flag):
        pass

    def load(self, flag):
        return True

    def plot(self):
        pass


def _mill_shape(nr=0):
    shape = make_shape(square_geos(), cut_cor=40, cw=True, nr=nr)
    build_stmove(shape)
    return shape


class TestMillingOffsetProject(unittest.TestCase):

    def _project_string(self, shape_dict, layer_extra=None):
        header = Project.header % Project.version
        layer = {
            'name': 'L0', 'tool_nr': 1, 'diameter': 2.0, 'speed': 1000.0,
            'start_radius': 0.0, 'retract': 9.91, 'safe_margin': 3.05,
            'shapes': [shape_dict]}
        if layer_extra is not None:
            layer.update(layer_extra)
        return "%s\nd2g.layers = %s\n" % (header, str([layer]))

    def _layers_of(self, parent):
        return ast.literal_eval(
            re.search(r"d2g\.layers = (.*)",
                      Project(parent).export(compleet=False)).group(1))

    def _real_shape_dict(self, shape):
        layers = self._layers_of(_FakeParent(Layers([shape.parentLayer])))
        return dict(layers[0]['shapes'][0]), dict(layers[0])

    def test_export_contains_the_offset(self):
        shape = _mill_shape()
        shape.milling_offset = 0.35
        shape.parentLayer.milling_offset = 0.35
        _, layer = self._real_shape_dict(shape)
        self.assertEqual(layer['shapes'][0]['milling_offset'], 0.35)
        self.assertEqual(layer['milling_offset'], 0.35)

    def test_load_old_project_defaults_to_zero(self):
        shape = _mill_shape()
        shape_dict, _ = self._real_shape_dict(_mill_shape())
        shape_dict.pop('milling_offset')
        parent = _FakeParent(Layers([shape.parentLayer]))
        Project(parent).load(self._project_string(shape_dict),
                             compleet=False)
        self.assertAlmostEqual(shape.milling_offset, 0.0)
        self.assertAlmostEqual(shape.parentLayer.milling_offset, 0.0)

    def test_roundtrip_restores_the_offset(self):
        shape = _mill_shape()
        shape.milling_offset = 0.6
        content = Project(
            _FakeParent(Layers([shape.parentLayer]))).export(compleet=False)
        shape2 = _mill_shape()
        self.assertAlmostEqual(shape2.milling_offset, 0.0)
        parent2 = _FakeParent(Layers([shape2.parentLayer]))
        Project(parent2).load(content, compleet=False)
        self.assertAlmostEqual(shape2.milling_offset, 0.6)


if __name__ == "__main__":
    unittest.main(verbosity=2)
