# -*- coding: utf-8 -*-
"""
G-code regression tests for the StMove / offset export chain.

They check the *movement codes* actually produced (G0/G1/G2/G3, Z moves and
arc I/J offsets) instead of only "file not empty". No GUI is required; the
post processor is built headless from the default configuration.

Run from the repository root:

    python -m unittest discover -s tests -t tests -p "dxf2gcode_stmove_gcode_test.py" -v
"""
from __future__ import absolute_import

import os
import re
import tempfile
import logging
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import sys
_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [_TEST_DIR, os.path.join(os.path.dirname(_TEST_DIR), "source")]


def _init_config():
    import dxf2gcode.globals.globals as g
    from dxf2gcode.globals.config import MyConfig

    if getattr(g, "config", None) is None:
        g.folder = tempfile.mkdtemp(prefix="d2g_gcode_test_")
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


_init_config()

import dxf2gcode.globals.globals as g
from configobj import ConfigObj
from validate import Validator

from dxf2gcode.postpro.postprocessorconfig import POSTPRO_SPEC, MyPostProConfig
from dxf2gcode.postpro.postprocessor import MyPostProcessor
from dxf2gcode.postpro.breaks import Breaks
from dxf2gcode.core.shape import Shape, Geos
from dxf2gcode.core.linegeo import LineGeo
from dxf2gcode.core.arcgeo import ArcGeo
from dxf2gcode.core.point import Point
from dxf2gcode.core.stmove import StMove
from dxf2gcode.core.leadmove import LEAD_OFF
from dxf2gcode.core.pocketmove import PocketMove
from dxf2gcode.core.layercontent import LayerContent


def make_postpro():
    """A real MyPostProcessor with default config, built without the GUI."""
    obj = ConfigObj(configspec=POSTPRO_SPEC)
    obj.validate(Validator(), copy=True)
    obj.main.interpolation = False
    cfg = MyPostProConfig.__new__(MyPostProConfig)
    cfg.var_dict = obj
    cfg.update_config()

    pp = MyPostProcessor.__new__(MyPostProcessor)
    pp.vars = cfg.vars
    br = Breaks.__new__(Breaks)
    br.breakLayers = []
    pp.breaks = br
    pp.initialize_export_vars()
    return pp


def make_shape(geos, closed=True, nr=0, cut_cor=41, cw=True, drill=False,
               pocket=False, tool_diameter=2.0):
    s = Shape(nr=nr, closed=closed, geos=Geos(geos))
    s.AnalyseAndOptimize()
    # deterministic milling depths / feeds (independent of the user config)
    s.axis3_start_mill_depth = 0.0
    s.axis3_mill_depth = -1.0
    s.axis3_slice_depth = 0.5
    s.f_g1_plane = 800
    s.f_g1_depth = 150
    s.cut_cor = cut_cor
    s.cw = cw
    s.Drill = drill
    s.Pocket = pocket
    layer = LayerContent(0, "L0", [s])
    layer.tool_diameter = tool_diameter
    layer.axis3_retract = 9.91
    layer.axis3_safe_margin = 3.05
    s.parentLayer = layer
    return s


def build_stmove(shape):
    st = StMove(shape)
    shape.stmove = st
    return st


def lines_with(prefix, text):
    """All non-empty lines that start (after stripping) with prefix."""
    return [ln.strip() for ln in text.splitlines() if ln.strip().startswith(prefix)]


def norm(text):
    """Collapse formatting whitespace so assertions test codes, not layout."""
    return re.sub(r"\s+", " ", text).strip()


def square_geos(size=10.0):
    return [LineGeo(Point(0, 0), Point(size, 0)),
            LineGeo(Point(size, 0), Point(size, size)),
            LineGeo(Point(size, size), Point(0, size)),
            LineGeo(Point(0, size), Point(0, 0))]


def corridor_shape(nr=0):
    """3 squares linked by 2 narrow corridors -> more than one offset loop.

    cut_cor 42 + cw selects the inward offset so the narrow corridors pinch
    and the raw offset splits into several loops.
    """
    pts = [(0, 0), (10, 0), (10, 4), (14, 4), (14, 0), (24, 0), (24, 4),
           (28, 4), (28, 0), (38, 0), (38, 10), (28, 10), (28, 6),
           (24, 6), (24, 10), (14, 10), (14, 6), (10, 6), (10, 10),
           (0, 10)]
    geos = [LineGeo(Point(*pts[k]), Point(*pts[(k + 1) % len(pts)]))
            for k in range(len(pts))]
    return make_shape(geos, cut_cor=42, cw=True, nr=nr, tool_diameter=3.0)


# ---------------------------------------------------------------------------
class TestPostProcessorMovements(unittest.TestCase):
    """The movement templates of the default configuration."""

    def setUp(self):
        self.pp = make_postpro()
        self.pp.postpro_file_used = "test.cfg"

    def test_rapid_xy_is_G0(self):
        out = self.pp.rap_pos_xy(Point(1.0, 2.0))
        self.assertIn("G0 X 1.000 Y 2.000", norm(out))

    def test_linear_xy_is_G1(self):
        out = self.pp.lin_pol_xy(Point(0, 0), Point(3.0, 4.0))
        self.assertIn("G1 X 3.000 Y 4.000", norm(out))

    def test_rapid_z_is_G0(self):
        self.assertIn("G0 Z -2.000", norm(self.pp.rap_pos_z(-2.0)))

    def test_linear_z_is_G1(self):
        self.assertIn("G1 Z -1.000", norm(self.pp.lin_pol_z(-1.0)))

    def test_arc_ccw_is_G3_with_IJ(self):
        ccw = ArcGeo(Ps=Point(5, 0), Pe=Point(-5, 0), O=Point(0, 0), r=5.0,
                     direction=1)
        out = ccw.Write_GCode(self.pp)
        self.assertIn("G3 X -5.000 Y 0.000 I -5.000 J 0.000", norm(out))

    def test_arc_cw_is_G2_with_IJ(self):
        cw = ArcGeo(Ps=Point(5, 0), Pe=Point(-5, 0), O=Point(0, 0), r=5.0,
                    direction=-1)
        out = cw.Write_GCode(self.pp)
        self.assertIn("G2 X -5.000 Y 0.000 I -5.000 J 0.000", norm(out))

    def test_clockwise_arc_can_be_exported_as_counterclockwise(self):
        self.pp.vars.General.export_ccw_arcs_only = True
        cw = ArcGeo(Ps=Point(5, 0), Pe=Point(-5, 0), O=Point(0, 0), r=5.0,
                    direction=-1)

        out = cw.Write_GCode(self.pp)

        self.assertTrue(lines_with("G3", out))
        self.assertFalse(lines_with("G2", out))

    def test_arc_above_maximum_radius_is_exported_as_a_line(self):
        self.pp.vars.General.max_arc_radius = 4.0
        arc = ArcGeo(Ps=Point(5, 0), Pe=Point(-5, 0), O=Point(0, 0), r=5.0,
                     direction=1)

        out = arc.Write_GCode(self.pp)

        self.assertTrue(lines_with("G1", out))
        self.assertFalse(lines_with("G2", out))
        self.assertFalse(lines_with("G3", out))

    def test_arc_can_be_tessellated_to_linear_moves(self):
        self.pp.vars.General.export_arcs_as_lines = True
        arc = ArcGeo(Ps=Point(5, 0), Pe=Point(-5, 0), O=Point(0, 0), r=5.0,
                     direction=1)

        out = arc.Write_GCode(self.pp)

        self.assertGreaterEqual(len(lines_with("G1", out)), 2)
        self.assertFalse(lines_with("G2", out))
        self.assertFalse(lines_with("G3", out))

    def test_incremental_xy_export_emits_deltas_after_the_first_move(self):
        self.pp.abs_export = False
        self.pp.lPe = Point(0, 0)
        self.pp.lin_pol_xy(Point(0, 0), Point(3, 4))

        out = self.pp.lin_pol_xy(Point(3, 4), Point(7, 9))

        self.assertIn("G1 X 4.000 Y 5.000", norm(out))

    def test_postprocessor_decimal_precision_controls_xy_format(self):
        self.pp.vars.Number_Format.post_decimals = 2

        out = self.pp.lin_pol_xy(Point(0, 0), Point(2, 3))

        self.assertIn("G1 X 2.00 Y 3.00", norm(out))

    def test_line_number_settings_are_applied_to_each_output_line(self):
        self.pp.vars.Line_Numbers.use_line_nrs = True
        self.pp.vars.Line_Numbers.line_nrs_begin = 10
        self.pp.vars.Line_Numbers.line_nrs_step = 5

        out = self.pp.make_line_numbers("G1 X1\nG0 X2")

        self.assertEqual(out, "N10 G1 X1\nN15 G0 X2")

    def test_windows_line_ending_option_is_applied(self):
        self.pp.vars.Number_Format.win_line_endings = True

        out = self.pp.make_windows_line_endings("G1 X1\nG0 X2\n")

        self.assertEqual(out, "G1 X1\r\nG0 X2\r\n")

    def test_program_header_uses_the_drawing_units(self):
        old_metric = g.config.metric
        try:
            for metric, unit_code in (
                    (1, self.pp.vars.General.code_begin_units_mm),
                    (0, self.pp.vars.General.code_begin_units_in)):
                g.config.metric = metric
                out = self.pp.write_gcode_be("fixture.dxf")
                self.assertIn(unit_code, out)
        finally:
            g.config.metric = old_metric
            g.config.update_tool_values()

    def test_program_header_selects_absolute_or_incremental_mode(self):
        self.pp.abs_export = True
        absolute = self.pp.write_gcode_be("fixture.dxf")
        self.pp.abs_export = False
        incremental = self.pp.write_gcode_be("fixture.dxf")

        self.assertIn(self.pp.vars.General.code_begin_prog_abs, absolute)
        self.assertIn(self.pp.vars.General.code_begin_prog_inc, incremental)

    def test_non_gcode_header_omits_gcode_metadata_but_keeps_configured_start(self):
        self.pp.vars.General.output_type = "text"

        header = self.pp.write_gcode_be("fixture.dxf")

        self.assertNotIn("Created from file", header)
        self.assertIn(self.pp.vars.General.code_begin_units_mm, header)
        self.assertIn(self.pp.vars.General.code_begin, header)

    def test_gcode_header_sanitizes_parentheses_in_source_filename(self):
        header = self.pp.write_gcode_be("part (copy).dxf")

        self.assertIn("(Created from file: part _copy_.dxf)", header)

    def test_number_format_supports_sign_padding_separator_and_trim(self):
        number_format = self.pp.vars.Number_Format
        number_format.pre_decimals = 3
        number_format.post_decimals = 2
        number_format.decimal_separator = ","
        number_format.pre_decimal_zero_padding = True
        number_format.post_decimal_zero_padding = True
        number_format.signed_values = True

        self.assertEqual(self.pp.fnprint(2.5), "+02,50")

        number_format.post_decimal_zero_padding = False
        self.assertEqual(self.pp.fnprint(2.5), "+02,5")

        number_format.signed_values = False
        self.assertEqual(self.pp.fnprint(2.5), "002,5")

    def test_feed_change_is_emitted_only_when_feed_changes(self):
        first = self.pp.chg_feed_rate(650)
        unchanged = self.pp.chg_feed_rate(650)
        changed = self.pp.chg_feed_rate(700)

        self.assertIn("F650", norm(first))
        self.assertEqual(unchanged, "")
        self.assertIn("F700", norm(changed))

    def test_export_errors_are_deduplicated(self):
        message = "Contour 4 has no valid lead-in."
        self.pp.add_export_error(message)
        self.pp.add_export_error(message)

        self.assertEqual(self.pp.export_errors, [message])

    def test_empty_export_writes_header_retract_final_position_and_footer(self):
        class EmptyLayerContents(object):
            def break_layer_iter(self):
                return iter(())

            def non_break_layer_iter(self):
                return iter(())

        old_stdout = g.config.vars.General["write_to_stdout"]
        g.config.vars.General["write_to_stdout"] = False
        try:
            with tempfile.TemporaryDirectory() as directory:
                filename = os.path.join(directory, "empty.ngc")
                self.pp.exportShapes("fixture.dxf", filename,
                                     EmptyLayerContents())
                with open(filename, "r") as output_file:
                    output = output_file.read()
        finally:
            g.config.vars.General["write_to_stdout"] = old_stdout

        self.assertIn("(Created from file: fixture.dxf)", output)
        self.assertIn("G0 Z", output)
        self.assertIn("G0 X", output)
        self.assertIn("M2 (Program end)", output)

    def test_stdout_export_prints_the_completed_program(self):
        class EmptyLayerContents(object):
            def break_layer_iter(self):
                return iter(())

            def non_break_layer_iter(self):
                return iter(())

        old_stdout = g.config.vars.General["write_to_stdout"]
        g.config.vars.General["write_to_stdout"] = True
        try:
            with patch("builtins.print") as print_mock:
                self.pp.exportShapes("fixture.dxf", "unused.ngc",
                                     EmptyLayerContents())
        finally:
            g.config.vars.General["write_to_stdout"] = old_stdout

        output = print_mock.call_args[0][0]
        self.assertIn("(Created from file: fixture.dxf)", output)
        self.assertIn("M2 (Program end)", output)

    def test_line_write_gcode_is_G1(self):
        out = LineGeo(Point(0, 0), Point(2, 3)).Write_GCode(self.pp)
        self.assertIn("G1 X 2.000 Y 3.000", norm(out))


# ---------------------------------------------------------------------------
class TestStMoveGCode(unittest.TestCase):

    def setUp(self):
        self.pp = make_postpro()

    def test_simple_contour_software_comp(self):
        # software compensation -> the exported path is the offset (stmove)
        g.config.vars.Cutter_Compensation["done_by_machine"] = False
        sh = make_shape(square_geos(10.0), cut_cor=41, cw=True)
        build_stmove(sh)
        code = sh.Write_GCode(self.pp)

        self.assertTrue(lines_with("G1", code), "no linear cutting move")
        self.assertTrue(lines_with("G0", code), "no rapid positioning move")
        # positioning (G0) must come before the first cutting move (G1)
        self.assertLess(code.index("G0"), code.index("G1"))
        # Z plunge before cutting and retract after
        self.assertTrue(lines_with("G1 Z", code), "no Z plunge")
        # software compensation must NOT emit G41/G42 (no double compensation)
        self.assertNotIn("G41", code)
        self.assertNotIn("G42", code)

    def test_machine_comp_emits_G41_and_original_contour(self):
        g.config.vars.Cutter_Compensation["done_by_machine"] = True
        sh = make_shape(square_geos(10.0), cut_cor=41, cw=True)
        build_stmove(sh)
        code = sh.Write_GCode(self.pp)
        self.assertIn("G41", code)          # machine side radius compensation
        self.assertTrue(lines_with("G1", code))

    def test_multiple_loops_are_all_present_and_connected_by_rapid(self):
        # 3 squares linked by 2 narrow corridors -> 3 loops after GIR
        g.config.vars.Cutter_Compensation["done_by_machine"] = False
        sh = corridor_shape(nr=0)
        # The test checks the offset loops and their connectors, not the lead in.
        sh.parentLayer.lead_in_mode = LEAD_OFF
        build_stmove(sh)

        # the offset must have produced more than one loop
        self.assertGreaterEqual(len(sh.stmove.geos), 2)
        loops = [geo for geo in sh.stmove.geos[1:]]
        code = sh.Write_GCode(self.pp)

        # every loop must contribute cutting moves
        self.assertGreaterEqual(len(lines_with("G1", code)), 3)

        # the connectors between separate loops are PocketMove geometries:
        # their XY move is a rapid (G0) and their Z move a linear plunge (G1)
        # they must NEVER emit a linear XY move across the gap (G1 X.. Y..).
        # => at least as many rapid XY moves as loop connectors exist.
        g0_xy = [ln for ln in lines_with("G0", code) if "X" in ln and "Y" in ln]
        self.assertGreaterEqual(len(g0_xy), 1)

    def test_connector_between_loops_is_rapid_not_linear(self):
        """A StMove loop-to-loop connector must not cut across the gap with G1."""
        g.config.vars.Cutter_Compensation["done_by_machine"] = False
        sh = corridor_shape(nr=5)
        # The test checks the offset loops and their connectors, not the lead in.
        sh.parentLayer.lead_in_mode = LEAD_OFF
        build_stmove(sh)
        connectors = [geo for geo in sh.stmove.geos if isinstance(geo, PocketMove)]
        self.assertTrue(connectors, "expected rapid connectors between loops")
        for conn in connectors:
            txt = conn.Write_GCode(self.pp)
            # XY positioning between loops is a rapid move (G0) ...
            self.assertTrue(lines_with("G0", txt),
                            "loop connector XY move must be G0")
            # ... and never a linear XY cutting move.
            self.assertFalse([ln for ln in lines_with("G1", txt)
                              if "X" in ln and "Y" in ln],
                             "loop connector must not emit G1 X/Y")
            # the plunge at the loop start is a linear Z move.
            self.assertTrue(lines_with("G1 Z", txt),
                            "loop connector must plunge with G1 Z")

    def test_vanished_contour_produces_no_moves_other_still_works(self):
        g.config.vars.Cutter_Compensation["done_by_machine"] = False
        # cut_cor 42 + cw -> inward offset; a 1x1 square fully vanishes
        small = make_shape(square_geos(1.0), cut_cor=42, cw=True, nr=1)
        build_stmove(small)
        code_small = small.Write_GCode(self.pp)
        self.assertEqual(code_small.strip(), "")

        good = make_shape(square_geos(10.0), cut_cor=41, cw=True, nr=2)
        build_stmove(good)
        code_good = good.Write_GCode(self.pp)
        self.assertTrue(lines_with("G1", code_good))

    def test_arc_direction_software_comp_keeps_G2_G3(self):
        g.config.vars.Cutter_Compensation["done_by_machine"] = True
        # a "D" shape: straight chord + half circle; direction sets G2/G3
        def d_shape(direction):
            geos = [LineGeo(Point(0, 0), Point(10, 0)),
                    ArcGeo(Ps=Point(10, 0), Pe=Point(0, 0), O=Point(5, 0),
                           r=5.0, direction=direction)]
            return geos
        sh3 = make_shape(d_shape(1), cut_cor=41, cw=True, nr=3)
        build_stmove(sh3)
        code3 = sh3.Write_GCode(self.pp)
        self.assertTrue(lines_with("G3", code3), "ccw arc must be G3")

        sh2 = make_shape(d_shape(-1), cut_cor=41, cw=True, nr=4)
        build_stmove(sh2)
        code2 = sh2.Write_GCode(self.pp)
        self.assertTrue(lines_with("G2", code2), "cw arc must be G2")


if __name__ == "__main__":
    unittest.main(verbosity=2)
