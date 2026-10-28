"""Tests for application actions that change shape machining state."""
from __future__ import absolute_import

import os
import sys
import unittest

_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_DIR = os.path.dirname(_TEST_DIR)
sys.path.insert(0, os.path.join(_REPO_DIR, "source"))

from dxf2gcode.application.shapes import (
    ApplyLayerOvercutDefaults, AutomaticCutterCompensation,
    SetShapeBreakPass, SetShapeLeadMode, SetShapeOvercut,
    UpdateLayerParameters, UpdateShapeParameters)
from dxf2gcode.domain.toolpath.leadmove import (
    LEAD_DEFAULT, LEAD_OFF, OVERCUT_DEFAULT, OVERCUT_ON)


class Shape(object):
    def __init__(self, closed=True):
        self.closed = closed
        self.overcut_enabled = OVERCUT_DEFAULT
        self.overcut_enabled_overridden = False
        self.break_pass = -1
        self.lead_in_mode = LEAD_DEFAULT
        self.lead_in_mode_overridden = False
        self.axis3_mill_depth = -1.0


class TestShapeActions(unittest.TestCase):
    def test_overcut_action_only_updates_closed_shapes_and_default_override(self):
        closed, opened = Shape(), Shape(closed=False)

        updated = SetShapeOvercut().execute([closed, opened], OVERCUT_ON)
        self.assertEqual(updated, (closed,))
        self.assertEqual(closed.overcut_enabled, OVERCUT_ON)
        self.assertTrue(closed.overcut_enabled_overridden)
        self.assertEqual(opened.overcut_enabled, OVERCUT_DEFAULT)

        SetShapeOvercut().execute([closed], OVERCUT_DEFAULT, use_default=True)
        self.assertFalse(closed.overcut_enabled_overridden)

    def test_break_pass_action_updates_shapes_and_rejects_invalid_values(self):
        first, second = Shape(), Shape()
        updated = SetShapeBreakPass().execute([first, second], 2)

        self.assertEqual(updated, (first, second))
        self.assertEqual((first.break_pass, second.break_pass), (2, 2))
        with self.assertRaises(ValueError):
            SetShapeBreakPass().execute([first], -2)
        self.assertEqual(first.break_pass, 2)

    def test_lead_mode_action_sets_or_clears_shape_override(self):
        shape = Shape()

        SetShapeLeadMode().execute([shape], "lead_in_mode", LEAD_OFF)
        self.assertEqual(shape.lead_in_mode, LEAD_OFF)
        self.assertTrue(shape.lead_in_mode_overridden)

        SetShapeLeadMode().execute(
            [shape], "lead_in_mode", LEAD_DEFAULT, use_default=True)
        self.assertFalse(shape.lead_in_mode_overridden)

    def test_shape_and_layer_parameter_actions_validate_and_apply_values(self):
        shape = Shape()
        layer = type("Layer", (), {"axis3_retract": 1.0})()

        self.assertEqual(UpdateShapeParameters().execute(
            [shape], "axis3_mill_depth", -4.0), (shape,))
        self.assertEqual(shape.axis3_mill_depth, -4.0)
        self.assertEqual(UpdateLayerParameters().execute(
            [layer], axis3_retract=7.0), (layer,))
        self.assertEqual(layer.axis3_retract, 7.0)
        with self.assertRaises(ValueError):
            UpdateShapeParameters().execute([shape], "name", "invalid")

    def test_layer_overcut_defaults_follow_tool_unless_overridden(self):
        tool_config = type("Config", (), {
            "vars": type("Vars", (), {
                "Tool_Parameters": {"1": {"overcut_length": 2.5}}
            })()
        })()
        layer = type("Layer", (), {
            "tool_nr": 1, "overcut_length": 0.0,
            "overcut_length_overridden": False,
            "overcut_enabled": OVERCUT_ON,
        })()

        self.assertTrue(ApplyLayerOvercutDefaults().execute(layer, tool_config))
        self.assertEqual(layer.overcut_length, 2.5)
        self.assertEqual(layer.overcut_enabled, OVERCUT_DEFAULT)

        layer.overcut_length_overridden = True
        layer.overcut_length = 4.0
        self.assertFalse(ApplyLayerOvercutDefaults().execute(layer, tool_config))
        self.assertEqual(layer.overcut_length, 4.0)

    def test_automatic_compensation_orders_nested_contours(self):
        class Bounds(object):
            def __init__(self, depth):
                self.depth = depth

            def iscontained(self, other):
                return self.depth > other.depth

        outer = type("Shape", (), {
            "nr": 0, "cw": True, "cut_cor": 40,
            "BB": Bounds(0),
        })()
        inner = type("Shape", (), {
            "nr": 1, "cw": True, "cut_cor": 40,
            "BB": Bounds(1),
        })()
        layer = type("Layer", (), {
            "shapes": [outer, inner], "exp_order": [],
            "automaticCutterCompensationEnabled": lambda self: True,
        })()

        changed = AutomaticCutterCompensation().execute(
            [layer], enabled=True, machine_type="milling")

        self.assertEqual(changed, (outer, inner))
        self.assertEqual((outer.cut_cor, inner.cut_cor), (41, 42))
        self.assertEqual(layer.exp_order, [1, 0])


if __name__ == "__main__":
    unittest.main()
