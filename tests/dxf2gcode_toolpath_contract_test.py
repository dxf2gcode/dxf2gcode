"""Contracts for toolkit-independent toolpath plans and diagnostics."""
from __future__ import absolute_import

import os
import sys
import unittest
from dataclasses import FrozenInstanceError, asdict, replace
from unittest.mock import Mock

_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(_TEST_DIR), "source"))

from dxf2gcode.application.toolpath.planning import PlanToolpath  # noqa: E402
from dxf2gcode.domain.toolpath.plan import (  # noqa: E402
    ToolpathDiagnostic, ToolpathPlan, ToolpathPlanningResult)
from dxf2gcode.domain.toolpath.inputs import (  # noqa: E402
    MachineCapabilities, MachiningSettings, PathGeometry, ToolpathRequest)
from dxf2gcode.domain.toolpath.planner import ToolpathPlanner  # noqa: E402


class TestPureToolpathPlanner(unittest.TestCase):
    @staticmethod
    def request(closed=True):
        points = ((0, 0), (10, 0), (10, 10), (0, 10), (0, 0))
        contour = tuple(PathGeometry("line", a, b, length=10.0)
                        for a, b in zip(points, points[1:]))
        if not closed:
            contour = contour[:1]
        return ToolpathRequest(
            7, MachiningSettings(final_depth=-3), MachineCapabilities(),
            contour=contour, split_contour=contour,
            prepared_path=(PathGeometry("rapid", (0, 0), (0, 0)),),
            closed=closed)

    def test_native_milling_has_complete_actions_and_each_cutting_pass(self):
        result = ToolpathPlanner().plan(self.request())
        self.assertFalse(result.has_errors)
        self.assertEqual([item.depth for item in result.plan.passes], [-1, -2, -3])
        self.assertEqual([action.args[0] for action in result.plan.actions
                          if action.role == "plunge"], [-1, -2, -3])
        self.assertEqual(result.plan.actions[0].kind, "rapid_xy")
        self.assertEqual(result.plan.actions[-1].kind, "post_cut")

    def test_open_contour_reverses_values_without_mutating_the_request(self):
        request = self.request(closed=False)
        before = asdict(request)
        planner = ToolpathPlanner()
        first = planner.plan(request)
        second = planner.plan(request)
        self.assertEqual(first, second)
        self.assertEqual(asdict(request), before)
        self.assertEqual(
            [action.args for action in first.plan.actions
             if action.kind == "linear_xy"],
            [((0, 0), (10, 0)), ((10, 0), (0, 0)), ((0, 0), (10, 0))])

    def test_pocket_depths_are_actions_and_do_not_modify_geometry(self):
        request = self.request()
        body = (request.contour[0],
                PathGeometry("pocket", (10, 0), (0, 10), depth=123),
                request.contour[-1])
        request = replace(
            request, pocket=True, prepared_path=request.prepared_path + body,
            split_contour=body)
        before = asdict(request)
        result = ToolpathPlanner().plan(request)
        self.assertEqual(asdict(request), before)
        self.assertEqual(
            [action.args[0] for action in result.plan.actions
             if action.kind == "linear_z" and action.role == "pocket" and
             action.args[0] < 0], [-1, -2, -3])

    def test_capabilities_are_explicit_and_arc_tessellation_is_planned(self):
        from math import pi
        request = self.request(closed=False)
        arc = PathGeometry(
            "arc", (1, 0), (-1, 0), pi, center=(0, 0), radius=1,
            start_angle=0, end_angle=pi, sweep=pi)
        request = replace(
            request, contour=(arc,), split_contour=(arc,),
            capabilities=replace(request.capabilities, arcs_as_lines=True,
                                 fitting_tolerance=0.01))
        result = ToolpathPlanner().plan(request)
        self.assertFalse(any(action.kind == "arc" for action in result.plan.actions))
        self.assertGreater(sum(action.kind == "linear_xy"
                               for action in result.plan.actions), 3)


class TestToolpathPlanningResult(unittest.TestCase):
    def test_result_can_represent_a_valid_plan_with_a_warning(self):
        plan = ToolpathPlan(
            shape_number=4, approach_xy=(0.0, 0.0), passes=(),
            workpiece_top=0.0, safe_margin=1.0, retract_depth=5.0,
            feed_depth=100.0, feed_xy=500.0)
        warning = ToolpathDiagnostic(
            code="lead.near_limit", severity="warning",
            message="Lead radius is close to the tool radius.",
            shape_number=4)

        result = ToolpathPlanningResult(plan, (warning,))

        self.assertIs(result.plan, plan)
        self.assertEqual(result.diagnostics, (warning,))
        self.assertFalse(result.has_errors)

    def test_result_can_represent_a_failure_without_an_exportable_plan(self):
        error = ToolpathDiagnostic(
            code="lead.invalid_radius", severity="error",
            message="Lead radius is too small.", shape_number=4,
            geometry_index=0)

        result = ToolpathPlanningResult(None, (error,))

        self.assertIsNone(result.plan)
        self.assertTrue(result.has_errors)

    def test_plan_diagnostics_and_result_are_immutable(self):
        warning = ToolpathDiagnostic(
            code="plan.warning", severity="warning", message="Review plan.")
        result = ToolpathPlanningResult(None, (warning,))

        with self.assertRaises(FrozenInstanceError):
            warning.message = "changed"
        with self.assertRaises(FrozenInstanceError):
            result.diagnostics = ()

    def test_use_case_passes_only_an_explicit_request_to_the_planner(self):
        plan = ToolpathPlan(
            shape_number=1, approach_xy=(0.0, 0.0), passes=(),
            workpiece_top=0.0, safe_margin=0.0, retract_depth=0.0,
            feed_depth=0.0, feed_xy=0.0)
        planner = Mock()
        planner.plan.return_value = ToolpathPlanningResult(plan)
        request = object()
        request_factory = Mock(return_value=request)
        use_case = PlanToolpath(planner, request_factory)

        result = use_case.execute_result("shape", "postprocessor")

        self.assertEqual(result, ToolpathPlanningResult(plan))
        planner.plan.assert_called_once_with(request)
        request_factory.assert_called_once_with("shape", "postprocessor")
        self.assertIs(use_case.execute("shape", "postprocessor"), plan)

    def test_use_case_preserves_planner_diagnostics(self):
        result = ToolpathPlanningResult(None, (ToolpathDiagnostic(
            code="shape.unsupported", severity="error",
            message="This shape is unsupported."),))
        planner = Mock()
        planner.plan.return_value = result

        actual = PlanToolpath(planner, Mock()).execute_result("shape", "postprocessor")

        self.assertIs(actual, result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
