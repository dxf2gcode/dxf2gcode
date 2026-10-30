"""Shape tool selection must stay local through preview, save and export."""

import os
import sys
import tempfile
import unittest
from dataclasses import asdict
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [_TEST_DIR, os.path.join(os.path.dirname(_TEST_DIR), "source")]

import dxf2gcode_parameter_state_test as gui
import dxf2gcode_stmove_gcode_test as machining
from dxf2gcode_leadmove_project_test import _ParentStub
import dxf2gcode.bootstrap.runtime_state as g
from dxf2gcode.application.shapes import AssignTool
from dxf2gcode.domain.project.layercontent import Layers, Shapes
from dxf2gcode.domain.project.project import Project
from dxf2gcode.domain.project.tool_settings import ToolSettings, effective_tool


class TestShapeToolAssignment(unittest.TestCase):
    def setUp(self):
        self.old_window = getattr(g, "window", None)
        self.shapes = [
            machining.make_shape(machining.square_geos(10 + nr * 2),
                                 nr=nr, cut_cor=40)
            for nr in range(3)]
        self.layer = self.shapes[0].parentLayer
        self.layer.shapes = Shapes(self.shapes)
        self.layer.exp_order_complete = [0, 1, 2]
        for shape in self.shapes:
            shape.parentLayer = self.layer
            shape.parentLayer.lead_in_mode = "off"
            shape.parentLayer.lead_out_mode = "off"
            shape.overcut_enabled = False
        self.profile = dict(
            diameter=4.0, speed=12345.0, start_radius=1.0,
            lead_radius=3.0, lead_length=2.0, overcut_length=0.0,
            milling_offset=0.25)
        self.tool = ToolSettings.from_profile(99, self.profile)
        self.tool_profiles = g.config.vars.Tool_Parameters
        self.tool_profiles.__dict__["99"] = self.profile

    def tearDown(self):
        del self.tool_profiles.__dict__["99"]
        g.window = self.old_window

    def harness(self):
        harness = gui._Harness([self.layer])
        harness.th.ui.toolDiameterComboBox.addItems(["1", "99"])
        g.window.canvas_scene = Mock()
        return harness

    def select_tool(self, harness, shapes):
        harness.select(shapes)
        harness.th.ui.toolDiameterComboBox.setCurrentText("99")
        harness.th.toolUpdate()

    def test_gui_changes_one_shape_without_touching_siblings_or_layer(self):
        harness = self.harness()
        old_layer = (self.layer.tool_nr, self.layer.tool_diameter,
                     self.layer.speed, self.layer.lead_radius)
        old_sibling = self.shapes[1].milling_offset
        self.select_tool(harness, [self.shapes[0]])
        self.assertEqual(effective_tool(self.shapes[0]), self.tool)
        self.assertEqual((self.layer.tool_nr, self.layer.tool_diameter,
                          self.layer.speed, self.layer.lead_radius), old_layer)
        self.assertIsNone(self.shapes[1].tool_override)
        self.assertIsNone(self.shapes[2].tool_override)
        self.assertEqual(self.shapes[1].milling_offset, old_sibling)
        g.window.canvas_scene.repaint_shape.assert_called_once_with(self.shapes[0])
        harness.select([self.shapes[1]])
        self.assertEqual(harness.th.ui.toolDiameterComboBox.currentText(), "1")
        harness.select([self.shapes[0]])
        self.assertEqual(harness.th.ui.toolDiameterComboBox.currentText(), "99")
        self.assertEqual(harness.th.ui.toolDiameterLabel.text(), "4.0")

    def test_multi_selection_changes_only_selected_shapes(self):
        harness = self.harness()
        self.select_tool(harness, self.shapes[:2])
        self.assertEqual([effective_tool(shape).tool_nr for shape in self.shapes],
                         [99, 99, 1])
        self.assertEqual(g.window.canvas_scene.repaint_shape.call_count, 2)

    def test_mixed_tools_show_placeholder_and_no_arbitrary_tool_values(self):
        AssignTool().execute([self.shapes[0]], [], 99, self.profile)
        harness = self.harness()
        combo = harness.th.ui.toolDiameterComboBox
        for order in (self.shapes[:2], list(reversed(self.shapes[:2]))):
            harness.select(order)
            harness.th.updateToolParameters()
            self.assertEqual(combo.currentIndex(), -1)
            self.assertEqual(combo.currentText(), "")
            self.assertEqual(combo.placeholderText(), harness.th.tr("Different tools"))
            self.assertEqual(combo.count(), 2)
            self.assertIsNone(harness.th.tool_nr)
            for name in ("toolDiameterLabel", "toolSpeedLabel", "leadRadiusLabel",
                         "leadLengthLabel", "overcutLengthLabel"):
                self.assertEqual(getattr(harness.th.ui, name).text(), "\u2014")
            harness.th.toolUpdate()
            self.assertEqual([effective_tool(shape).tool_nr for shape in self.shapes],
                             [99, 1, 1])
        g.window.canvas_scene.repaint_shape.assert_not_called()

    def test_choosing_tool_from_mixed_selection_assigns_all_selected_shapes(self):
        AssignTool().execute([self.shapes[0]], [], 99, self.profile)
        harness = self.harness()
        harness.select(self.shapes[:2])
        combo = harness.th.ui.toolDiameterComboBox
        combo.textActivated[str].connect(harness.th.toolUpdate)
        combo.setCurrentIndex(combo.findText("99"))
        combo.textActivated[str].emit("99")
        self.assertEqual([effective_tool(shape).tool_nr for shape in self.shapes],
                         [99, 99, 1])
        self.assertEqual(combo.currentText(), "99")
        self.assertEqual(combo.placeholderText(), "")
        self.assertEqual(harness.th.ui.toolDiameterLabel.text(), "4.0")

    def test_common_tool_selection_restores_number_and_values(self):
        AssignTool().execute([self.shapes[0]], [], 99, self.profile)
        harness = self.harness()
        harness.select(self.shapes[:2])
        harness.select(self.shapes[1:])
        combo = harness.th.ui.toolDiameterComboBox
        self.assertEqual(combo.currentText(), "1")
        self.assertEqual(combo.placeholderText(), "")
        self.assertNotEqual(harness.th.ui.toolDiameterLabel.text(), "\u2014")

    def test_deselection_clears_mixed_tool_placeholder(self):
        AssignTool().execute([self.shapes[0]], [], 99, self.profile)
        harness = self.harness()
        harness.select(self.shapes[:2])
        harness.select([])
        combo = harness.th.ui.toolDiameterComboBox
        self.assertEqual(combo.placeholderText(), "")
        self.assertEqual(combo.currentIndex(), -1)
        self.assertEqual(harness.th.ui.toolDiameterLabel.text(), "")

    def test_explicit_layer_assignment_applies_to_all_and_clears_overrides(self):
        AssignTool().execute([self.shapes[0]], [], 99, self.profile)
        harness = self.harness()
        for shape in self.shapes:
            shape.setSelected(False)
        selection = harness.view.selectionModel()
        selection.clearSelection()
        selection.select(harness.model.index(0, 0),
                         gui.QtCore.QItemSelectionModel.SelectionFlag.Select |
                         gui.QtCore.QItemSelectionModel.SelectionFlag.Rows)
        harness.th.ui.toolDiameterComboBox.setCurrentText("99")
        harness.th.toolUpdate()
        self.assertEqual(self.layer.tool_nr, 99)
        self.assertTrue(all(shape.tool_override is None for shape in self.shapes))

    def test_compensated_plan_and_output_use_the_individual_tool_radius(self):
        shape = self.shapes[0]
        AssignTool().execute([shape], [], 99, self.profile)
        shape.cut_cor = 41
        reference = machining.make_shape(machining.square_geos(), cut_cor=41)
        reference.milling_offset = shape.milling_offset
        reference.overcut_enabled = False
        for name, value in asdict(self.tool).items():
            setattr(reference.parentLayer, name, value)
        reference.parentLayer.lead_in_mode = "off"
        reference.parentLayer.lead_out_mode = "off"
        with patch.object(g.config, "machine_type", "milling"), patch.dict(
                g.config.vars.Cutter_Compensation.__dict__, done_by_machine=False):
            for item in (shape, reference):
                machining.build_stmove(item)
            pp = machining.make_postpro()
            actual_plan = pp.plan_shape_toolpath(shape)
            expected_plan = machining.make_postpro().plan_shape_toolpath(reference)
            self.assertEqual(actual_plan.passes, expected_plan.passes)
            self.assertEqual(pp.write_shape_gcode(shape),
                             machining.make_postpro().write_shape_gcode(reference))
        self.assertNotEqual(effective_tool(shape).getToolRadius(),
                            effective_tool(self.shapes[1]).getToolRadius())

    def test_full_export_switches_tools_for_each_shape_in_existing_order(self):
        AssignTool().execute([self.shapes[1]], [], 99, self.profile)
        for shape in self.shapes:
            machining.build_stmove(shape)
        pp = machining.make_postpro()
        pp.postpro_file_used = "test.cfg"
        with tempfile.TemporaryDirectory() as directory, patch.object(
                pp, "chg_tool", wraps=pp.chg_tool) as changes, patch.dict(
                    g.config.vars.General.__dict__, write_to_stdout=False):
            pp.exportShapes("tools.dxf", os.path.join(directory, "tools.ngc"),
                            Layers([self.layer]))
        self.assertEqual([call.args[0] for call in changes.call_args_list],
                         [1, 99, 1])

    def test_project_roundtrip_preserves_individual_tool_and_old_files_inherit(self):
        AssignTool().execute([self.shapes[0]], [], 99, self.profile)
        project = Project(_ParentStub([self.layer]))
        content = project.export(compleet=False)
        self.shapes[0].tool_override = None
        project.load(content, compleet=False)
        self.assertEqual(self.shapes[0].tool_override, self.tool)
        self.assertIsNone(self.shapes[1].tool_override)
        self.shapes[0].tool_override = None
        old_content = project.export(compleet=False)
        self.shapes[0].tool_override = self.tool
        project.load(old_content, compleet=False)
        self.assertIsNone(self.shapes[0].tool_override)

    def test_unit_change_scales_shape_tool_without_changing_its_speed_or_number(self):
        AssignTool().execute([self.shapes[0]], [], 99, self.profile)
        self.layer.changeMeasuringUnits(1, 0)
        self.assertAlmostEqual(self.shapes[0].tool_override.tool_diameter, 4 / 25.4)
        self.assertEqual(self.shapes[0].tool_override.tool_nr, 99)
        self.assertEqual(self.shapes[0].tool_override.speed, self.tool.speed)

    def test_hole_preview_and_hit_testing_use_the_individual_tool(self):
        from dxf2gcode.domain.geometry.holegeo import HoleGeo
        from dxf2gcode.domain.geometry.point import Point
        AssignTool().execute([self.shapes[0]], [], 99, self.profile)
        hole = HoleGeo(Point(0, 0))
        lines = []
        hole.make_path(self.shapes[0], lambda caller, start, end:
                       lines.append((start, end)))
        self.assertEqual(lines[0][0], Point(2, 0))
        self.assertTrue(hole.isHit(self.shapes[0], Point(2, 0), 0.01))
        self.assertFalse(hole.isHit(self.shapes[0], Point(1, 0), 0.01))


if __name__ == "__main__":
    unittest.main(verbosity=2)
