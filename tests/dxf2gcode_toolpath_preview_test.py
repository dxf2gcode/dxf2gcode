"""Shared preview actions, settings refresh and pure preparation contracts."""

from dataclasses import asdict
from copy import deepcopy

from dxf2gcode_leadmove_golden_test import GoldenTestBase, build_shape
import dxf2gcode.bootstrap.runtime_state as g
from dxf2gcode.adapters.toolpath.preparation import prepare_shape
from dxf2gcode.adapters.toolpath.preview import preview_result
from dxf2gcode.application.toolpath.projections import plan_preview_segments
from dxf2gcode.domain.toolpath.pocketmill import PocketMill
from pathlib import Path


class TestSharedPreview(GoldenTestBase):
    def setUp(self):
        super().setUp()
        self.old_window = getattr(g, 'window', None)
        g.window = None

    def tearDown(self):
        g.window = self.old_window
        super().tearDown()

    def test_leads_and_all_depths_come_from_current_export_actions(self):
        shape, _ = build_shape(layer_settings=dict(lead_out_mode='straight'))
        first = preview_result(shape).plan
        self.assertEqual(first, preview_result(shape).plan)
        for dimensions in (2, 3):
            projected = plan_preview_segments(first, dimensions)
            self.assertTrue(any(s.role == 'lead_in' for s in projected))
            self.assertTrue(any(s.role == 'lead_out' for s in projected))
            self.assertTrue(all(s.space == 'programmed' for s in projected))
        shape.axis3_mill_depth = -7
        second = preview_result(shape).plan
        self.assertNotEqual(first, second)
        self.assertIn(-7, {s.end[2] for s in plan_preview_segments(second)})
        self.assertEqual(plan_preview_segments(first, 2), plan_preview_segments(second, 2))

    def test_original_geometry_and_hit_area_remain_when_overlay_is_selected(self):
        from dxf2gcode.presentation.qt.canvas2d import MyGraphicsScene, ShapeGUI
        from dxf2gcode.presentation.qt.qt_compat.QtCore import QPointF
        shape, _ = build_shape(done_by_machine=False)
        shape.calc_bounding_box()
        scene, item = MyGraphicsScene(), ShapeGUI(shape)
        scene.paint_shape(item)
        original = item.path
        self.assertEqual((original.boundingRect().left(), original.boundingRect().width()), (0, 100))
        self.assertLess(item.stmove_item._comp_path.boundingRect().left(), 0)
        self.assertTrue(item.isVisible())
        self.assertFalse(item.stmove_item.isVisible())
        self.assertLess(item.contains_point(QPointF(40, 0)), 0.1)
        self.assertGreater(item.contains_point(QPointF(40, 5)), 4.5)
        item.setSelected(True)
        self.assertTrue(item.stmove_item.isVisible())
        self.assertTrue(item.isVisible())
        self.assertEqual(item.path, original)
        item.setSelected(False)
        self.assertFalse(item.stmove_item.isVisible())
        self.assertTrue(item.isVisible())
        self.assertEqual(item.path, original)

    def test_selection_overlay_retains_toolpath_lead_and_tool_colors(self):
        from unittest.mock import Mock
        from dxf2gcode.presentation.qt.canvas2d import StMoveGUI
        shape, _ = build_shape(layer_settings=dict(lead_out_mode='straight'))
        item = StMoveGUI(shape)
        painter = Mock()
        item.paint(painter, None)
        pens = [call.args[0] for call in painter.setPen.call_args_list]
        self.assertEqual(pens[0], StMoveGUI.PEN_COMP_LINE)
        self.assertIn(StMoveGUI.PEN_LEAD_IN_LINE, pens)
        self.assertIn(StMoveGUI.PEN_LEAD_IN_TOOL, pens)
        self.assertIn(StMoveGUI.PEN_EXIT_LINE, pens)
        painter.drawEllipse.assert_called_once()

    def test_tool_compensation_and_lead_edits_refresh_both_projections(self):
        shape, layer = build_shape(done_by_machine=False)
        previous = preview_result(shape).plan
        changes = ((layer, 'tool_diameter', 6), (shape, 'cut_cor', 42),
                   (layer, 'lead_out_mode', 'straight'))
        for target, attribute, value in changes:
            with self.subTest(attribute=attribute):
                setattr(target, attribute, value)
                prepare_shape(shape)
                current = preview_result(shape).plan
                self.assertNotEqual(plan_preview_segments(previous, 2),
                                    plan_preview_segments(current, 2))
                self.assertNotEqual(plan_preview_segments(previous),
                                    plan_preview_segments(current))
                previous = current

    def test_pocket_generation_returns_values_without_mutating_input(self):
        shape, _ = build_shape(cut_cor=40, done_by_machine=False,
                               tool_diameter=20, layer_settings=dict(lead_in_mode='off'))
        prepared = shape.stmove
        before = deepcopy(prepared.geos)
        pocket = PocketMill(prepared, edge_clearance_percent=0)
        result = pocket.generate()
        self.assertTrue(result)
        self.assertEqual(repr(prepared.geos), repr(before))
        self.assertIsNot(pocket.stmove.geos, prepared.geos)
        shape.Pocket = True
        prepare_shape(shape)
        segments = plan_preview_segments(preview_result(shape).plan, 2)
        self.assertTrue(any(s.role == 'pocket' for s in segments))

    def test_counterclockwise_only_profile_projects_the_formatted_arc_direction(self):
        from dataclasses import replace
        from math import pi
        from dxf2gcode.domain.toolpath.inputs import PathGeometry, ToolpathRequest, MachiningSettings, MachineCapabilities
        from dxf2gcode.domain.toolpath.planner import ToolpathPlanner
        arc = PathGeometry('arc', (1, 0), (0, -1), pi / 2,
                           center=(0, 0), radius=1, sweep=-pi / 2,
                           start_angle=0, end_angle=-pi / 2)
        request = ToolpathRequest(1, MachiningSettings(),
                                 MachineCapabilities(counterclockwise_arcs_only=True),
                                 contour=(arc,), split_contour=(arc,), closed=False,
                                 prepared_path=(PathGeometry('rapid', (1, 0), (1, 0)),))
        plan = ToolpathPlanner().plan(request).plan
        segments = [s for s in plan_preview_segments(plan) if s.role == 'cut']
        self.assertEqual(segments[0].start[:2], (0, -1))
        self.assertEqual(segments[-1].end[:2], (1, 0))
        self.assertTrue(all(s.start[0] >= -1e-9 and s.start[1] <= 1e-9 for s in segments))

    def test_preparation_settings_are_snapshots_of_resolved_values(self):
        shape, layer = build_shape()
        settings = shape.stmove.settings
        before = asdict(settings)
        layer.tool_diameter = 3
        g.config.machine_type = 'drag_knife'
        self.assertEqual(asdict(settings), before)
        prepare_shape(shape)
        self.assertEqual(shape.stmove.settings.machine_type, 'drag_knife')
        self.assertEqual(shape.stmove.settings.tool.tool_diameter, 3)

    def test_compensation_descriptions_load_from_all_compiled_catalogs(self):
        from dxf2gcode.presentation.qt.qt_compat.QtCore import QTranslator
        catalogs = Path(__file__).resolve().parents[1] / 'source/i18n'
        expected = {
            'de': ('Programmierte Kontur (G41/G42)', 'Werkzeugmittelpunktbahn (G40)'),
            'fr': ('Contour programmé (G41/G42)', 'Trajectoire du centre de l’outil (G40)'),
            'ru': ('Запрограммированный контур (G41/G42)', 'Траектория центра инструмента (G40)')}
        for language, labels in expected.items():
            with self.subTest(language=language):
                translator = QTranslator()
                self.assertTrue(translator.load(str(catalogs / ('dxf2gcode_' + language + '.qm'))))
                for source, target in zip(('Programmed contour (G41/G42)',
                                           'Tool center path (G40)'), labels):
                    self.assertEqual(translator.translate('ToolpathPreview', source), target)
