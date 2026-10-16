# -*- coding: utf-8 -*-
"""
Regression tests for ticket #150: the BREAKS (tab) contour is only split for
the milling passes selected with the "Process breaks from" setting
(shape.break_pass: -1 = last pass, 0 = never, 1..n = pass number).

They check the actual emitted movements (pass plunges, XY blocks, tab lift /
dip Z lines) instead of only counting geometry objects. The GUI part uses the
real TreeHandler with a real QComboBox/QTreeView headless (offscreen); the
full MainWindow cannot be instantiated offscreen (it crashes, like the other
existing GUI tests) so the widget position is verified against the generated
UI module and the layout collapse is verified with a plain QGridLayout.

Run from the ``source`` directory:

    python -m unittest dxf2gcode_breaks_pass_test -v
"""
from __future__ import absolute_import

import ast
import os
import re
import tempfile
import logging
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def _init_config():
    import dxf2gcode.globals.globals as g
    from dxf2gcode.globals.config import MyConfig

    if getattr(g, "config", None) is None:
        g.folder = tempfile.mkdtemp(prefix="d2g_breaks_test_")
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
    logging.getLogger("PostPro.PostProcessor").setLevel(logging.CRITICAL)
    logging.getLogger("core.shapeoffset").setLevel(logging.CRITICAL)
    logging.getLogger("core.stmove").setLevel(logging.CRITICAL)
    logging.getLogger("Core.Project").setLevel(logging.CRITICAL)
    logging.getLogger("Gui.TreeHandling").setLevel(logging.CRITICAL)


_init_config()

import dxf2gcode.globals.globals as g  # noqa: E402

from dxf2gcode.postpro.breaks import Breaks  # noqa: E402
from dxf2gcode.core.shape import Shape, Geos  # noqa: E402
from dxf2gcode.core.linegeo import LineGeo  # noqa: E402
from dxf2gcode.core.arcgeo import ArcGeo  # noqa: E402
from dxf2gcode.core.point import Point  # noqa: E402
from dxf2gcode.core.layercontent import LayerContent, Layers  # noqa: E402
from dxf2gcode.core.project import Project  # noqa: E402

from dxf2gcode_stmove_gcode_test import (  # noqa: E402
    make_postpro, make_shape, build_stmove, square_geos, norm)

from dxf2gcode.Qt.QtWidgets import (  # noqa: E402
    QApplication, QComboBox, QLabel, QTreeView, QWidget, QGridLayout, QLineEdit)
from dxf2gcode.Qt import QtCore  # noqa: E402
from dxf2gcode.gui.treehandling import TreeHandler  # noqa: E402

_APP = None  # keep the QApplication alive (otherwise all widgets are deleted)


# ---------------------------------------------------------------------------
# Fixtures

def tab_rect(x0, x1, y0, y1):
    """Closed rectangle built from its two corner coordinates."""
    return [LineGeo(Point(x0, y0), Point(x1, y0)),
            LineGeo(Point(x1, y0), Point(x1, y1)),
            LineGeo(Point(x1, y1), Point(x0, y1)),
            LineGeo(Point(x0, y1), Point(x0, y0))]


def make_break_layer(name, crossing="bottom", a=4.9, b=5.1, enabled=True):
    """A BREAKS layer holding one tab shape.

    The tab crosses exactly ONE side of the 10 mm square contour:
    - "bottom": rectangle between y=-1 and y=4, spanning x=a..b
    - "right":  rectangle between x=4.9 and x=11, spanning y=a..b
    """
    if crossing == "bottom":
        tab = tab_rect(a, b, -1.0, 4.0)
    else:  # crossing the right side
        tab = tab_rect(4.9, 11.0, a, b)
    break_shape = Shape(nr=100, closed=True, geos=Geos(tab))
    break_shape.setDisable(not enabled)
    layer = LayerContent(1, name, [break_shape])
    layer.overrideDefaults()
    return layer


def export_shape(break_pass=-1, depths=(0.0, -8.0, -1.0), cut_cor=40,
                 closed=True, machine=False, break_layers=None, geos=None):
    """Builds a shape + postpro with break layers and returns (shape, code)."""
    g.config.vars.Cutter_Compensation["done_by_machine"] = bool(machine)
    if geos is None:
        geos = square_geos()
    sh = make_shape(geos, cut_cor=cut_cor, closed=closed, cw=True, nr=0)
    build_stmove(sh)
    sh.axis3_start_mill_depth, sh.axis3_mill_depth, sh.axis3_slice_depth = depths
    sh.break_pass = break_pass

    pp = make_postpro()
    if break_layers:
        layers = [sh.parentLayer] + list(break_layers)
        pp.breaks = Breaks(Layers(layers))
    code = sh.Write_GCode(pp)
    return sh, code


# ---------------------------------------------------------------------------
# G-code parsing helpers

_PASS_PLUNGE = re.compile(r"^G1 Z\s+(-?\d+\.\d+)$")


def split_passes(code):
    """Splits the exported code into the milling passes.

    A pass starts at a plunge to a new deepest Z; tab lifts (to the tab top)
    and re-entry dips (back to the pass depth) do not start a pass. Leading
    start moves are skipped.
    """
    lines = [ln.strip() for ln in code.splitlines() if ln.strip()]
    groups = []
    cur = []
    started = False
    minz = None
    for ln in lines:
        m = _PASS_PLUNGE.match(ln)
        if m:
            z = float(m.group(1))
            if minz is None or z < minz - 1e-9:
                minz = z
                if started or cur:
                    groups.append(cur)
                cur = []
                started = True
        if started:
            cur.append(ln)
    if cur:
        groups.append(cur)
    return [grp for grp in groups if grp]


def xy_blocks(pass_lines):
    """Cutting XY moves of one pass (G1 lines, arcs) without rapids."""
    return [ln for ln in pass_lines if ln.startswith(("G1 X", "G2", "G3"))]


def tab_lifts(pass_lines, tab_top):
    """Z moves of one pass that lift the cutter up to the tab top.

    The first G1 Z line of a pass is its plunge and never counted, so a
    tab top that coincides with a pass depth is not confused with it.
    """
    lifts = []
    for ln in pass_lines[1:]:
        if ln.startswith("G1 Z"):
            z = float(ln.split()[2])
            if abs(z - tab_top) < 1e-6:
                lifts.append(ln)
    return lifts


def geo_snapshot(geos):
    """Orientation snapshot (Ps/Pe order) of a geometry list."""
    return [(g_.Ps.x, g_.Ps.y, g_.Pe.x, g_.Pe.y) for g_ in geos]


# ---------------------------------------------------------------------------
class TestBreakPassGCode(unittest.TestCase):

    def test_auto_processes_tabs_in_last_pass_only(self):
        """Ticket #150 example: 8 mm depth, 1 mm slice, tab top at -6.5."""
        layer = make_break_layer("BREAKS: 1 MillDepth: -6.5")
        _, code = export_shape(break_pass=-1, break_layers=[layer])
        passes = split_passes(code)
        self.assertEqual(len(passes), 8)
        for k, pass_lines in enumerate(passes[:-1]):
            self.assertEqual(len(xy_blocks(pass_lines)), 4,
                             "pass %d must use the unbroken contour" % (k + 1))
            self.assertEqual(len(tab_lifts(pass_lines, -6.5)), 0,
                             "pass %d must not touch the tabs" % (k + 1))
        self.assertEqual(len(xy_blocks(passes[-1])), 6,
                         "last pass must use the broken contour")
        self.assertEqual(len(tab_lifts(passes[-1], -6.5)), 1,
                         "last pass must lift the cutter to the tab top")

    def test_get_pass_depths_mirrors_write_gcode(self):
        from dxf2gcode.core.shape import Shape as _S
        sh = make_shape(square_geos())
        sh.axis3_start_mill_depth = 0.0
        sh.axis3_mill_depth = -8.0
        sh.axis3_slice_depth = -1.0
        self.assertEqual(len(sh.get_pass_depths()), 8)
        self.assertEqual(sh.get_pass_depths()[-1], -8.0)
        sh.axis3_slice_depth = -3.0
        self.assertEqual([round(d, 6) for d in sh.get_pass_depths()],
                         [-3.0, -6.0, -8.0])
        self.assertEqual(sh.get_pass_depths(single_pass=True), [-8.0])
        sh.axis3_slice_depth = 0.0
        self.assertEqual(sh.get_pass_depths(), [0.0])

    def test_explicit_first_pass(self):
        layer = make_break_layer("BREAKS: 1 MillDepth: -6.5")
        _, code = export_shape(break_pass=1, break_layers=[layer])
        passes = split_passes(code)
        self.assertEqual(len(passes), 8)
        for k, pass_lines in enumerate(passes):
            self.assertEqual(len(xy_blocks(pass_lines)), 6,
                             "pass %d must use the broken contour" % (k + 1))
            expected_lifts = 1 if k >= 6 else 0
            self.assertEqual(len(tab_lifts(pass_lines, -6.5)), expected_lifts)

    def test_explicit_middle_pass(self):
        layer = make_break_layer("BREAKS: 1 MillDepth: -6.5")
        _, code = export_shape(break_pass=4, break_layers=[layer])
        passes = split_passes(code)
        self.assertEqual(len(passes), 8)
        for k, pass_lines in enumerate(passes):
            expected_blocks = 6 if k >= 3 else 4
            self.assertEqual(len(xy_blocks(pass_lines)), expected_blocks,
                             "pass %d has wrong contour variant" % (k + 1))
            expected_lifts = 1 if k >= 6 else 0
            self.assertEqual(len(tab_lifts(pass_lines, -6.5)), expected_lifts)

    def test_explicit_last_pass_equals_auto(self):
        layer = make_break_layer("BREAKS: 1 MillDepth: -6.5")
        _, code_auto = export_shape(break_pass=-1, break_layers=[layer])
        _, code_last = export_shape(break_pass=8, break_layers=[layer])
        self.assertEqual(code_auto, code_last)

    def test_pass_zero_never_processes_tabs(self):
        layer = make_break_layer("BREAKS: 1 MillDepth: -6.5")
        _, code = export_shape(break_pass=0, break_layers=[layer])
        passes = split_passes(code)
        self.assertEqual(len(passes), 8)
        for k, pass_lines in enumerate(passes):
            self.assertEqual(len(xy_blocks(pass_lines)), 4,
                             "pass %d must use the unbroken contour" % (k + 1))
        self.assertNotIn("Z -6.500", code)

    def test_variable_last_slice(self):
        # slices of 3 mm give passes at -3, -6 and the clamped -8
        layer = make_break_layer("BREAKS: 1 MillDepth: -6.5")
        _, code = export_shape(break_pass=-1, depths=(0.0, -8.0, -3.0),
                               break_layers=[layer])
        passes = split_passes(code)
        self.assertEqual(len(passes), 3)
        self.assertEqual(len(xy_blocks(passes[0])), 4)
        self.assertEqual(len(xy_blocks(passes[1])), 4)
        self.assertEqual(len(xy_blocks(passes[2])), 6)
        self.assertEqual(len(tab_lifts(passes[2], -6.5)), 1)

        # explicit pass 2: passes 1 plain, passes 2-3 split
        _, code = export_shape(break_pass=2, depths=(0.0, -8.0, -3.0),
                               break_layers=[layer])
        passes = split_passes(code)
        self.assertEqual(len(passes), 3)
        self.assertEqual(len(xy_blocks(passes[0])), 4)
        self.assertEqual(len(xy_blocks(passes[1])), 6)
        self.assertEqual(len(xy_blocks(passes[2])), 6)
        self.assertEqual(len(tab_lifts(passes[1], -6.5)), 0)
        self.assertEqual(len(tab_lifts(passes[2], -6.5)), 1)

    def test_tab_top_on_pass_depth(self):
        # tab top exactly at the 7th pass depth: the 7th pass must not lift
        # (existing Z height semantics) but the 8th must.
        layer = make_break_layer("BREAKS: 1 MillDepth: -7.0")
        _, code = export_shape(break_pass=-1, break_layers=[layer])
        passes = split_passes(code)
        self.assertEqual(len(passes), 8)
        self.assertEqual(len(xy_blocks(passes[6])), 4)
        self.assertEqual(len(tab_lifts(passes[6], -7.0)), 0)
        self.assertEqual(len(xy_blocks(passes[7])), 6)
        self.assertEqual(len(tab_lifts(passes[7], -7.0)), 1)

    def test_multiple_tab_heights(self):
        # two tabs with different heights on different sides
        layer1 = make_break_layer("BREAKS: 1 MillDepth: -2.5",
                                  crossing="bottom")
        layer2 = make_break_layer("BREAKS: 2 MillDepth: -6.5",
                                  crossing="right")
        _, code = export_shape(break_pass=-1,
                               break_layers=[layer1, layer2])
        passes = split_passes(code)
        self.assertEqual(len(passes), 8)
        for k, pass_lines in enumerate(passes[:-1]):
            self.assertEqual(len(xy_blocks(pass_lines)), 4)
            self.assertEqual(len(tab_lifts(pass_lines, -2.5)), 0)
            self.assertEqual(len(tab_lifts(pass_lines, -6.5)), 0)
        self.assertEqual(len(xy_blocks(passes[-1])), 8)
        self.assertEqual(len(tab_lifts(passes[-1], -2.5)), 1)
        self.assertEqual(len(tab_lifts(passes[-1], -6.5)), 1)

        # explicit pass 4: passes 4-8 split; the -2.5 tab lifts from pass 4
        # on (Z semantics unchanged), the -6.5 tab only in the deep passes
        _, code = export_shape(break_pass=4,
                               break_layers=[layer1, layer2])
        passes = split_passes(code)
        self.assertEqual(len(xy_blocks(passes[3])), 8)
        self.assertEqual(len(tab_lifts(passes[3], -2.5)), 1)
        self.assertEqual(len(tab_lifts(passes[3], -6.5)), 0)
        self.assertEqual(len(tab_lifts(passes[7], -2.5)), 1)
        self.assertEqual(len(tab_lifts(passes[7], -6.5)), 1)

    def test_tab_top_between_pass_depths(self):
        # tab top -6.5 lies between pass 6 (-6.0) and pass 7 (-7.0)
        layer = make_break_layer("BREAKS: 1 MillDepth: -6.5")
        _, code = export_shape(break_pass=7, break_layers=[layer])
        passes = split_passes(code)
        self.assertEqual(len(passes), 8)
        self.assertEqual(len(xy_blocks(passes[5])), 4)
        self.assertEqual(len(xy_blocks(passes[6])), 6)
        self.assertEqual(len(tab_lifts(passes[6], -6.5)), 1)
        self.assertEqual(len(tab_lifts(passes[6], -7.0)), 1)  # re-entry dip

    def test_closed_contour_geometry_unchanged(self):
        layer = make_break_layer("BREAKS: 1 MillDepth: -6.5")
        sh, _ = export_shape(break_pass=2, break_layers=[layer])
        before = geo_snapshot(sh.geos)
        pp = make_postpro()
        pp.breaks = Breaks(Layers([sh.parentLayer, layer]))
        sh.Write_GCode(pp)
        self.assertEqual(geo_snapshot(sh.geos), before)

    def test_no_breaks_gcode_identical(self):
        """Without break layers the selection must not change anything."""
        codes = [export_shape(break_pass=bp)[1] for bp in (-1, 0, 3)]
        self.assertEqual(codes[0], codes[1])
        self.assertEqual(codes[1], codes[2])
        passes = split_passes(codes[0])
        self.assertEqual(len(passes), 8)
        for pass_lines in passes:
            self.assertEqual(len(xy_blocks(pass_lines)), 4)

    def test_machine_tool_compensation(self):
        layer = make_break_layer("BREAKS: 1 MillDepth: -6.5")
        _, code = export_shape(break_pass=-1, cut_cor=41, machine=True,
                               break_layers=[layer])
        self.assertIn("G41", code)
        passes = split_passes(code)
        self.assertEqual(len(passes), 8)
        for k, pass_lines in enumerate(passes[:-1]):
            self.assertEqual(len(xy_blocks(pass_lines)), 4)
        self.assertEqual(len(xy_blocks(passes[-1])), 6)
        self.assertEqual(len(tab_lifts(passes[-1], -6.5)), 1)

    def test_software_tool_compensation(self):
        layer = make_break_layer("BREAKS: 1 MillDepth: -6.5")
        _, code = export_shape(break_pass=-1, cut_cor=41, machine=False,
                               break_layers=[layer])
        self.assertNotIn("G41", code)
        self.assertNotIn("G42", code)
        passes = split_passes(code)
        self.assertEqual(len(passes), 8)
        for k, pass_lines in enumerate(passes[:-1]):
            # the inward offset of the square has rounded corners:
            # 4 lines + 4 arcs = 8 blocks
            self.assertEqual(len(xy_blocks(pass_lines)), 8)
        self.assertEqual(len(xy_blocks(passes[-1])), 10)
        self.assertEqual(len(tab_lifts(passes[-1], -6.5)), 1)

    def test_open_contour_alternates_direction(self):
        # open contour of 2 lines; the tab crosses the second (vertical) line
        geos = [LineGeo(Point(0, 0), Point(10, 0)),
                LineGeo(Point(10, 0), Point(10, 10))]
        layer = make_break_layer("BREAKS: 1 MillDepth: -6.5",
                                 crossing="right")
        sh, code = export_shape(break_pass=2, depths=(0.0, -8.0, -1.0),
                                cut_cor=40, closed=False,
                                break_layers=[layer], geos=geos)
        passes = split_passes(code)
        self.assertEqual(len(passes), 8)
        # plain pass: 2 blocks; split pass: 4 blocks (line 2 broken in 3)
        for k, pass_lines in enumerate(passes):
            expected_blocks = 4 if k >= 1 else 2
            self.assertEqual(len(xy_blocks(pass_lines)), expected_blocks)

        # direction alternates: pass 1 ends at the contour end, pass 2 (the
        # first split pass) runs backwards and ends at the contour start
        last_xy_1 = norm(xy_blocks(passes[0])[-1])
        last_xy_2 = norm(xy_blocks(passes[1])[-1])
        self.assertIn("X 0.000 Y 0.000", last_xy_1)
        self.assertIn("X 10.000 Y 10.000", last_xy_2)

        # the original geometry must be restored after the export
        before = geo_snapshot(sh.geos)
        from dxf2gcode.postpro.breaks import Breaks as _B
        pp = make_postpro()
        pp.breaks = _B(Layers([sh.parentLayer, layer]))
        sh.Write_GCode(pp)
        self.assertEqual(geo_snapshot(sh.geos), before)

    def test_arcs_are_split_at_tabs(self):
        # "D" contour: line + half circle; the tab crosses the line
        geos = [LineGeo(Point(0, 0), Point(10, 0)),
                ArcGeo(Ps=Point(10, 0), Pe=Point(0, 0), O=Point(5, 0),
                       r=5.0, direction=1)]
        layer = make_break_layer("BREAKS: 1 MillDepth: -6.5")
        _, code = export_shape(break_pass=1, depths=(0.0, -8.0, -1.0),
                               cut_cor=40, closed=True,
                               break_layers=[layer], geos=geos)
        passes = split_passes(code)
        self.assertEqual(len(passes), 8)
        for pass_lines in passes:
            blocks = xy_blocks(pass_lines)
            # plain contour: 2 blocks (line + arc); broken: 4 (2 lines,
            # BreakGeo, arc) and the arc move (G2/G3) must still be an arc
            self.assertEqual(len(blocks), 4)
            self.assertTrue(any(ln.startswith(("G2", "G3")) for ln in blocks),
                            "arc must stay an arc in the broken contour")

        _, code_plain = export_shape(break_pass=0, depths=(0.0, -8.0, -1.0),
                                     cut_cor=40, closed=True, geos=geos)
        passes = split_passes(code_plain)
        for pass_lines in passes:
            self.assertEqual(len(xy_blocks(pass_lines)), 2)
            self.assertTrue(any(ln.startswith(("G2", "G3")) for ln in
                                xy_blocks(pass_lines)))


# ---------------------------------------------------------------------------
class _Scene(object):
    def update(self):
        pass


class _FakeWin(object):
    canvas_scene = _Scene()
    layerContents = None


class _FakeUI(object):
    pass


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


class _Harness(object):
    """Real TreeHandler with a fake UI holding the new combobox."""

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
        self.th.ui.breaksPassLabel = QLabel(self.th)
        self.th.ui.breaksPassComboBox = QComboBox(self.th)
        self.view = QTreeView()
        self.th.ui.layersShapesTreeView = self.view
        self.th.layers_list = list(layers)
        self.th.buildLayerTree(list(layers))
        self.model = self.th.layer_item_model

    def select_shape(self, shape):
        sel = self.view.selectionModel()
        sel.clearSelection()
        idx = self.th.findLayerItemIndexFromShape(shape)
        sel.select(idx, QtCore.QItemSelectionModel.SelectionFlag.Select |
                   QtCore.QItemSelectionModel.SelectionFlag.Rows)
        self.th.display_tool_layer = shape.parentLayer
        self.th.display_tool_shape = shape


def _mill_shape(depths=(0.0, -8.0, -1.0), nr=0):
    sh = make_shape(square_geos(), cut_cor=40, cw=True, nr=nr)
    build_stmove(sh)
    sh.axis3_start_mill_depth, sh.axis3_mill_depth, sh.axis3_slice_depth = depths
    return sh


class TestBreakPassGUI(unittest.TestCase):

    def setUp(self):
        self.mill = _mill_shape()

    def _layers(self, with_breaks=True, enabled=True):
        if with_breaks:
            return Layers([self.mill.parentLayer,
                           make_break_layer("BREAKS: 1 MillDepth: -6.5",
                                            enabled=enabled)])
        return Layers([self.mill.parentLayer])

    def test_hidden_without_breaks(self):
        h = _Harness(self._layers(with_breaks=False))
        self.assertFalse(h.th.ui.breaksPassComboBox.isVisibleTo(h.th))
        self.assertFalse(h.th.ui.breaksPassLabel.isVisibleTo(h.th))

    def test_shown_with_breaks_and_hidden_when_disabled(self):
        h = _Harness(self._layers())
        self.assertTrue(h.th.ui.breaksPassComboBox.isVisibleTo(h.th))
        # disable the only break shape -> no break geometries -> hidden
        h.th.layers_list[1].shapes[0].setDisable(True)
        h.th.updateBreaksPassWidget()
        self.assertFalse(h.th.ui.breaksPassComboBox.isVisibleTo(h.th))
        # re-enable -> visible again
        h.th.layers_list[1].shapes[0].setDisable(False)
        h.th.updateBreaksPassWidget()
        self.assertTrue(h.th.ui.breaksPassComboBox.isVisibleTo(h.th))

    def test_items_follow_shape_passes_and_selection(self):
        h = _Harness(self._layers())
        h.select_shape(self.mill)
        h.th.updateBreaksPassWidget()
        combo = h.th.ui.breaksPassComboBox
        # 2 fixed entries + 8 passes
        self.assertEqual(combo.count(), 10)
        self.assertEqual(combo.currentData(), -1)

        self.mill.break_pass = 3
        h.th.updateBreaksPassWidget()
        self.assertEqual(combo.currentData(), 3)

        # out of range selection is reset visibly to the default
        self.mill.break_pass = 20
        h.th.updateBreaksPassWidget()
        self.assertEqual(self.mill.break_pass, -1)
        self.assertEqual(combo.currentData(), -1)

        # shorter depths reduce the number of entries
        self.mill.axis3_mill_depth = -4.0
        h.th.updateBreaksPassWidget()
        self.assertEqual(combo.count(), 6)

    def test_no_shape_selected_leaves_combo_disabled(self):
        h = _Harness(self._layers())
        h.th.display_tool_shape = None
        h.th.updateBreaksPassWidget()
        self.assertTrue(h.th.ui.breaksPassComboBox.isVisibleTo(h.th))
        self.assertFalse(h.th.ui.breaksPassComboBox.isEnabled())

    def test_slot_applies_selection_to_selected_shapes(self):
        sh2 = _mill_shape(nr=1)
        self.mill.parentLayer.shapes.append(sh2)
        sh2.parentLayer = self.mill.parentLayer
        layers = Layers([self.mill.parentLayer,
                         make_break_layer("BREAKS: 1 MillDepth: -6.5")])
        h = _Harness(layers)
        h.select_shape(self.mill)
        h.th.updateBreaksPassWidget()
        combo = h.th.ui.breaksPassComboBox
        idx = combo.findData(5)
        self.assertGreaterEqual(idx, 0)
        h.th.breaksPassUpdate(idx)
        self.assertEqual(self.mill.break_pass, 5)
        self.assertEqual(sh2.break_pass, -1)  # unselected shape untouched

        idx0 = combo.findData(0)
        h.th.breaksPassUpdate(idx0)
        self.assertEqual(self.mill.break_pass, 0)


class TestBreakPassGUILayout(unittest.TestCase):
    """Widget position and layout collapse.

    The full MainWindow crashes offscreen (as in the other existing GUI
    tests), so the position is verified against the generated UI module and
    the collapse behaviour of the used QGridLayout with plain widgets.
    """

    def _ui5_add_items(self):
        base = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base, "dxf2gcode_ui5.py")
        if not os.path.isfile(path):  # source tree variant
            path = os.path.join(base, "source", "dxf2gcode_ui5.py")
        with open(path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
        rows = {}
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "addWidget"
                    and len(node.args) >= 2
                    and isinstance(node.args[0], ast.Attribute)
                    and isinstance(node.args[1], ast.Constant)):
                rows[node.args[0].attr] = node.args[1].value
        return rows

    def test_combobox_is_below_infeed_and_final_depth(self):
        rows = self._ui5_add_items()
        self.assertEqual(rows["zInfeedDepthLineEdit"], 5)
        self.assertEqual(rows["zFinalMillDepthLineEdit"], 6)
        self.assertEqual(rows["breaksPassComboBox"], 7)
        self.assertEqual(rows["g1FeedXYLineEdit"], 8)
        self.assertEqual(rows["g1FeedZLineEdit"], 9)

    def test_combobox_is_child_of_mill_settings_frame(self):
        base = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base, "dxf2gcode_ui5.py")
        if not os.path.isfile(path):
            path = os.path.join(base, "source", "dxf2gcode_ui5.py")
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn(
            "self.breaksPassComboBox = QtWidgets.QComboBox(self.millSettingsFrame)",
            content)

    def test_hidden_widget_collapses_in_grid_layout(self):
        global _APP
        _APP = QApplication.instance() or QApplication([])
        frame = QWidget()
        grid = QGridLayout(frame)
        top = QLineEdit()
        middle = QLineEdit()
        bottom = QLineEdit()
        grid.addWidget(top, 0, 1)
        grid.addWidget(middle, 1, 1)
        grid.addWidget(bottom, 2, 1)
        frame.show()
        _APP.processEvents()
        y_before = bottom.mapTo(frame, QtCore.QPoint(0, 0)).y()
        middle.hide()
        _APP.processEvents()
        y_after = bottom.mapTo(frame, QtCore.QPoint(0, 0)).y()
        self.assertLess(y_after, y_before)


class TestBreakPassProject(unittest.TestCase):

    def _shape_with_break_pass(self, value):
        sh = _mill_shape(nr=0)
        sh.break_pass = value
        return sh

    def _project_string(self, shape_dict):
        header = Project.header % Project.version
        layers = [{
            'name': 'L0', 'tool_nr': 1, 'diameter': 2.0, 'speed': 1000.0,
            'start_radius': 0.0, 'retract': 9.91, 'safe_margin': 3.05,
            'shapes': [shape_dict]}]
        return "%s\nd2g.layers = %s\n" % (header, str(layers))

    def _real_shape_dict(self, sh):
        parent = _FakeParent(Layers([sh.parentLayer]))
        py_code = Project(parent).export(compleet=False)
        match = re.search(r"d2g\.layers = (.*)", py_code)
        layers = ast.literal_eval(match.group(1))
        return dict(layers[0]['shapes'][0])

    def test_export_contains_break_pass(self):
        sh = self._shape_with_break_pass(4)
        parent = _FakeParent(Layers([sh.parentLayer]))
        py_code = Project(parent).export()
        match = re.search(r"d2g\.layers = (.*)", py_code)
        layers = ast.literal_eval(match.group(1))
        shape_entry = layers[0]['shapes'][0]
        self.assertIn('break_pass', shape_entry)
        self.assertEqual(shape_entry['break_pass'], 4)

    def test_load_old_project_defaults_to_last_pass(self):
        # a project file from a version without break_pass: same geometry,
        # no break_pass key in the shape dict
        sh = _mill_shape()
        shape_dict = self._real_shape_dict(_mill_shape())
        shape_dict.pop('break_pass')
        parent = _FakeParent(Layers([sh.parentLayer]))
        Project(parent).load(self._project_string(shape_dict),
                             compleet=False)
        self.assertEqual(sh.break_pass, -1)

    def test_roundtrip_restores_break_pass(self):
        sh = self._shape_with_break_pass(4)
        content = Project(
            _FakeParent(Layers([sh.parentLayer]))).export(compleet=False)
        # fresh shape with default setting, same number -> same reload hash
        sh2 = _mill_shape()
        self.assertEqual(sh2.break_pass, -1)
        parent2 = _FakeParent(Layers([sh2.parentLayer]))
        Project(parent2).load(content, compleet=False)
        self.assertEqual(sh2.break_pass, 4)


if __name__ == "__main__":
    unittest.main(verbosity=2)
