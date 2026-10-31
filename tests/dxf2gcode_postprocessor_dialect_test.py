"""Exercise semantic serialization with a profile, without a GUI or project."""

import os
import sys
import unittest
from types import SimpleNamespace

_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(_TEST_DIR), "source"))

from dxf2gcode.adapters.postprocessor.dialect import ProfileDialect
from dxf2gcode.adapters.toolpath.gcode_exporter import ToolpathGCodeExporter
from dxf2gcode.domain.toolpath.plan import ToolpathAction, ToolpathPlan


def profile(absolute=True):
    return SimpleNamespace(
        General={"abs_export": absolute, "code_end": "M2%nl"},
        Number_Format={"pre_decimals": 0, "post_decimals": 3,
                       "decimal_separator": ".", "pre_decimal_zero_padding": False,
                       "post_decimal_zero_padding": True, "signed_values": False,
                       "win_line_endings": False},
        Program={"rap_pos_plane": "G0 X%XE Y%YE%nl",
                 "rap_pos_depth": "G0 Z%ZE%nl",
                 "lin_mov_plane": "G1 X%XE Y%YE%nl",
                 "lin_mov_depth": "G1 Z%ZE%nl",
                 "arc_int_cw": "G2 X%XE Y%YE I%I J%J%nl",
                 "arc_int_ccw": "G3 X%XE Y%YE I%I J%J%nl",
                 "lin_mov_drill": "G1 Z%ZE%nl",
                 "lin_ret_drill": "G0 Z%ZE%nl",
                 "feed_change": "F%feed%nl", "tool_change": "T%tool_nr S%speed%nl",
                 "cutter_comp_left": "G41%nl", "cutter_comp_right": "G42%nl",
                 "cutter_comp_off": "G40%nl", "pre_shape_cut": "%start%nl",
                 "post_shape_cut": "M5%nl", "comment": "(%comment)%nl"},
        Custom_GCode={"%start": {"gcode": "M3"}},
        Line_Numbers={"use_line_nrs": False, "line_nrs_begin": 10, "line_nrs_step": 5})


def plan(*actions):
    return ToolpathPlan(1, (0, 0), (), 0, 1, 5, 100, 400,
                        actions=tuple(ToolpathAction(kind, args) for kind, args in actions))


class TestProfileDialect(unittest.TestCase):
    def test_modal_state_continues_across_plans_and_is_local_to_the_dialect(self):
        first = plan(("rapid_xy", ((3, 4),)), ("rapid_z", (2,)),
                     ("feed", (100,)), ("linear_z", (-1,)))
        second = plan(("feed", (100,)), ("linear_xy", ((3, 4), (7, 9))),
                      ("linear_z", (-3,)))
        exporter = ToolpathGCodeExporter()
        absolute = ProfileDialect(profile(), start_xy=(1, 2), start_z=5)
        incremental = ProfileDialect(profile(False), start_xy=(1, 2), start_z=5)
        self.assertEqual(exporter.export(first, absolute),
                         "G0 X3.000 Y4.000\nG0 Z2.000\nF100\nG1 Z-1.000\n")
        self.assertEqual(exporter.export(first, incremental),
                         "G0 X2.000 Y2.000\nG0 Z-3.000\nF100\nG1 Z-3.000\n")
        self.assertEqual(exporter.export(second, absolute), "G1 X7.000 Y9.000\nG1 Z-3.000\n")
        self.assertEqual(exporter.export(second, incremental), "G1 X4.000 Y5.000\nG1 Z-2.000\n")
        fresh = ProfileDialect(profile())
        self.assertEqual(exporter.export(plan(("feed", (100,))), fresh), "F100\n")

    def test_diameter_scaling_is_explicit_and_applies_to_arc_words(self):
        arc = plan(("arc", ("ccw", (1, 2), (3, 4), 0, 1, 5, (0, 0), (-1, -2), 1)))
        exporter = ToolpathGCodeExporter()
        milling = ProfileDialect(profile())
        lathe = ProfileDialect(profile(), diameter_factor=2)
        self.assertEqual(exporter.export(arc, milling), "G3 X3.000 Y4.000 I-1.000 J-2.000\n")
        self.assertEqual(exporter.export(arc, lathe), "G3 X3.000 Y8.000 I-1.000 J-4.000\n")
        self.assertEqual(exporter.export(arc, milling), "G3 X3.000 Y4.000 I-1.000 J-2.000\n")

    def test_profile_actions_custom_code_and_literal_keep_their_order(self):
        actions = plan(("literal", (";literal\n",)), ("pre_cut", ()),
                       ("compensation_on", (41,)), ("drill", (-2,)),
                       ("drill_retract", (1,)), ("compensation_off", ()),
                       ("compensation_on", (42,)), ("compensation_off", ()),
                       ("hole_marker", ()), ("post_cut", ()))
        self.assertEqual(ToolpathGCodeExporter().export(actions, ProfileDialect(profile())),
                         ";literal\nM3\nG41\nG1 Z-2.000\nG0 Z1.000\nG40\n"
                         "G42\nG40\n(Drilled hole)\nM5\n")


if __name__ == "__main__":
    unittest.main()
