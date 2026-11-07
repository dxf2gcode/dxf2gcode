"""R3/R1b atomic commands, inheritance, history and optimizer barriers."""
from copy import deepcopy
from dataclasses import replace
import unittest

from dxf2gcode_leadmove_golden_test import GoldenTestBase, build_shape
from dxf2gcode.application.machining import MachiningDrawing
from dxf2gcode.application.machining_actions import MachiningCommands
from dxf2gcode.domain.project.machining_project import LiteralAction, new_id
from dxf2gcode.domain.project.layercontent import Layers, Shapes
import dxf2gcode.bootstrap.runtime_state as g


class TestMachiningActions(GoldenTestBase):
    def setup_commands(self, count=1, circle=False):
        shape, layer = build_shape(cut_cor=40, done_by_machine=False, tool_diameter=2,
                                  layer_settings=dict(lead_in_mode='off', lead_out_mode='off'))
        if circle:
            from dxf2gcode.domain.geometry.arcgeo import ArcGeo
            from dxf2gcode.domain.geometry.point import Point
            shape.geos[:] = [ArcGeo(Ps=Point(5, 0), Pe=Point(5, 0), O=Point(0, 0), r=5, direction=1)]
            shape.geos[0].make_abs_geo()
        layer.shapes = Shapes([shape])
        for index in range(1, count):
            other = deepcopy(shape)
            other.parentLayer = layer
            other.nr = index
            for geo in other.geos:
                geo.Ps.x += 100 * index
                geo.Pe.x += 100 * index
                geo.make_abs_geo()
            layer.shapes.append(other)
        layer.exp_order_complete = list(range(count))
        binding = MachiningDrawing.capture(Layers([layer]), g.config)
        binding.bind_legacy_editor()
        return MachiningCommands(binding)

    def test_selected_kind_change_splits_step_preserving_ids_defaults_and_undo(self):
        commands = self.setup_commands(2)
        original = deepcopy(commands.binding.project.to_dict())
        source = commands.binding.project.steps[0]
        entry = source.entries[0]
        commands.set_operation_mode([entry.id], 'pocket', names={'pocket': 'Pocket'})
        first, target = commands.binding.project.steps
        self.assertEqual(first.kind, 'contour')
        self.assertEqual([e.id for e in first.entries], [source.entries[1].id])
        self.assertEqual(target.kind, 'pocket')
        self.assertEqual(target.tool_id, source.tool_id)
        self.assertEqual(target.defaults, source.defaults)
        self.assertEqual(target.entries[0], entry)
        self.assertEqual(len(commands.undo_stack), 1)
        target_id = target.id
        commands.undo()
        self.assertEqual(commands.binding.project.to_dict(), original)
        commands.redo()
        self.assertEqual(commands.binding.project.steps[1].id, target_id)
        self.assertEqual(commands.binding.project.steps[1].entries[0].id, entry.id)

    def test_mode_split_keeps_distinct_source_tools_in_one_history_action(self):
        commands = self.setup_commands(2)
        source = commands.binding.project.steps[0]
        first, second = [e.id for e in source.entries]
        tool = replace(commands.binding.project.tools[source.tool_id], tool_nr=2)
        commands.create_step('Second tool', 'contour', tool)
        target = commands.binding.project.steps[-1]
        commands.transfer([second], target.id)
        before = commands.binding.project.to_dict()
        count = len(commands.undo_stack)
        commands.set_operation_mode([first, second], 'pocket')
        pockets = [step for step in commands.binding.project.steps if step.kind == 'pocket']
        self.assertEqual([step.tool_id for step in pockets], [source.tool_id, target.tool_id])
        self.assertEqual([step.entries[0].id for step in pockets], [first, second])
        self.assertEqual(len(commands.undo_stack), count+1)
        commands.undo()
        self.assertEqual(commands.binding.project.to_dict(), before)

    def test_mode_change_rejects_entire_invalid_selection_without_history(self):
        commands = self.setup_commands(2)
        step = commands.binding.project.steps[0]
        commands.binding.sources[step.entries[1].geometry_id].closed = False
        before = commands.binding.project.to_dict()
        with self.assertRaisesRegex(ValueError, 'pocketing requires'):
            commands.set_operation_mode([entry.id for entry in step.entries], 'pocket')
        self.assertEqual(commands.binding.project.to_dict(), before)
        self.assertFalse(commands.undo_stack)
        commands.binding.project.configuration['Cutter_Compensation']['done_by_machine'] = True
        with self.assertRaisesRegex(ValueError, 'pocketing requires'):
            commands.set_operation_mode([step.entries[0].id], 'pocket')
        self.assertFalse(commands.undo_stack)
        commands.binding.project.configuration['General']['machine_type'] = 'lathe'
        commands.binding.project.configuration['Cutter_Compensation']['done_by_machine'] = False
        with self.assertRaisesRegex(ValueError, 'pocketing requires'):
            commands.set_operation_mode([step.entries[0].id], 'pocket')

    def test_drilling_selects_g40_and_compensation_returns_only_that_circle_to_contour(self):
        commands = self.setup_commands(2, circle=True)
        source = commands.binding.project.steps[0]
        entry = source.entries[0]
        commands.update_entries([entry.id], {'cut_cor': 41})
        commands.set_operation_mode([entry.id], 'drill')
        target = commands.binding.project.steps[1]
        self.assertEqual(target.kind, 'drill')
        self.assertEqual(target.entries[0].overrides['cut_cor'], 40)
        self.assertTrue(commands.binding.materialize()[1].shapes[0].Drill)
        commands.set_operation_mode([entry.id], compensation=42)
        target = commands.binding.project.steps[2]
        self.assertEqual(target.kind, 'contour')
        self.assertEqual(target.entries[0].id, entry.id)
        self.assertEqual(target.entries[0].overrides['cut_cor'], 42)
        view = commands.binding.materialize()[2].shapes[0]
        self.assertFalse(view.Drill or view.Pocket)
        self.assertEqual(view.cut_cor, 42)
        self.assertEqual(len(commands.binding.project.steps[0].entries), 1)

    def test_copy_move_own_values_target_inheritance_and_stable_history(self):
        commands = self.setup_commands()
        project = commands.binding.project
        first = project.steps[0]
        entry = first.entries[0]
        commands.update_entries([entry.id], {'axis3_slice_depth': None})
        tool = replace(next(iter(project.tools.values())), tool_nr=2, tool_diameter=3)
        commands.create_step('Finish', 'contour', tool)
        target = commands.binding.project.steps[-1]
        target.defaults['axis3_slice_depth'] = -.2
        commands.selection = (entry.id,)
        result = commands.transfer([entry.id], target.id, copy=True)
        copied_id = result.selection[0]
        self.assertNotEqual(copied_id, entry.id)
        copied = commands.binding.project.steps[-1].entries[0]
        values, origins, tool = commands.binding.project.resolve(commands.binding.project.steps[-1], copied)
        self.assertEqual(values['axis3_slice_depth'], -.2)
        self.assertEqual(origins['axis3_slice_depth'], 'step')
        self.assertEqual(values['axis3_mill_depth'], entry.overrides['axis3_mill_depth'])
        self.assertEqual(tool.tool_nr, 2)
        self.assertEqual(copied.geometry_id, entry.geometry_id)
        commands.undo()
        self.assertFalse(commands.binding.project.steps[-1].entries)
        self.assertEqual(commands.selection, (entry.id,))
        commands.redo()
        self.assertEqual(commands.binding.project.steps[-1].entries[0].id, copied_id)
        commands.transfer([entry.id], target.id)
        self.assertFalse(commands.binding.project.steps[0].entries)
        self.assertEqual(len(commands.binding.project.geometries), 1)
        self.assertEqual(len(commands.binding.project.steps[-1].entries), 2)

    def test_invalid_mixed_target_is_atomic_and_does_not_create_undo(self):
        commands = self.setup_commands(2)
        project = commands.binding.project
        entries = project.steps[0].entries
        commands.create_step('Pocket', 'pocket', project.steps[0].tool_id)
        commands.binding.sources[entries[1].geometry_id].closed = False
        before = commands.binding.project.to_dict()
        history = len(commands.undo_stack)
        with self.assertRaisesRegex(ValueError, 'closed contour'):
            commands.transfer([entry.id for entry in entries], commands.binding.project.steps[-1].id)
        self.assertEqual(commands.binding.project.to_dict(), before)
        self.assertEqual(len(commands.undo_stack), history)

    def test_special_layers_and_unknown_ids_reject_without_mutation(self):
        commands = self.setup_commands()
        step = commands.binding.project.steps[0]
        commands.create_step('Tabs', 'break', step.tool_id)
        before = commands.binding.project.to_dict()
        with self.assertRaises(ValueError):
            commands.transfer([step.entries[0].id], commands.binding.project.steps[-1].id)
        with self.assertRaises(ValueError):
            commands.transfer(['foreign'], step.id)
        self.assertEqual(commands.binding.project.to_dict(), before)

    def test_remove_step_move_or_remove_never_deletes_geometry_and_undo_restores_ids(self):
        commands = self.setup_commands()
        first = commands.binding.project.steps[0]
        commands.create_step('Finish', 'contour', first.tool_id)
        target = commands.binding.project.steps[-1]
        commands.delete_step(first.id, target.id)
        self.assertEqual(commands.binding.project.steps[0].entries[0].id, first.entries[0].id)
        self.assertEqual(len(commands.binding.project.geometries), 1)
        commands.undo()
        self.assertEqual(commands.binding.project.steps[0].id, first.id)
        commands.delete_step(first.id)
        self.assertEqual(len(commands.binding.project.geometries), 1)
        self.assertTrue(commands.binding.sources)

    def test_assign_unassigned_is_transactional_and_uses_target_defaults(self):
        commands = self.setup_commands()
        step = commands.binding.project.steps[0]
        source = next(iter(commands.binding.sources.values()))
        commands.remove([step.entries[0].id])
        result = commands.assign([source], step.id)
        entry = commands.binding.project.steps[0].entries[0]
        self.assertEqual(entry.id, result.selection[0])
        self.assertFalse(entry.overrides)
        commands.undo()
        self.assertFalse(commands.binding.project.steps[0].entries)
        commands.redo()
        self.assertEqual(commands.binding.project.steps[0].entries[0].id, entry.id)

    def test_edit_step_kind_and_tool_profile_update_have_atomic_undo(self):
        commands = self.setup_commands()
        step = commands.binding.project.steps[0]
        before = commands.binding.project.to_dict()
        with self.assertRaises(ValueError):
            commands.edit_step(step.id, 'Bore', 'drill', step.tool_id)
        self.assertEqual(commands.binding.project.to_dict(), before)
        tool = commands.binding.project.tools[step.tool_id]
        commands.refresh_tool(step.tool_id, replace(tool, speed=1234))
        self.assertEqual(commands.binding.materialize()[0].shapes[0].tool_override.speed, 1234)
        commands.undo()
        self.assertEqual(commands.binding.project.to_dict(), before)

    def test_optimizer_keeps_literal_barriers_and_both_relative_modes(self):
        class ReverseOptimizer:
            def __init__(self, endpoints, fixed, settings):
                self.opt_route = [len(endpoints)-1] + list(reversed(range(len(endpoints)-1)))
            def calc_next_iteration(self):
                pass
        for mode in ('CONSTRAIN_ORDER_ONLY', 'CONSTRAIN_PLACE_AFTER'):
            with self.subTest(mode=mode):
                commands = self.setup_commands(4)
                step = commands.binding.project.steps[0]
                original = [e.id for e in step.entries]
                for entry in step.entries:
                    entry.optimize = True
                literal = LiteralAction(new_id(), 'Pause', 'M0')
                step.entries.insert(2, literal)
                commands.binding.project.configuration['Route_Optimisation']['TSP_shape_order'] = mode
                commands.optimize(ReverseOptimizer)
                ids = [e.id for e in commands.binding.project.steps[0].entries]
                self.assertEqual(ids, [original[1], original[0], literal.id, original[3], original[2]])
                commands.undo()
                self.assertEqual([e.id for e in commands.binding.project.steps[0].entries],
                                 original[:2] + [literal.id] + original[2:])

    def test_unit_override_converts_values_once_and_preserves_local_geometry(self):
        commands = self.setup_commands()
        before = commands.binding.project.to_dict()
        entry = commands.binding.project.steps[0].entries[0]
        start = entry.start
        depth = entry.overrides['axis3_mill_depth']
        commands.change_units('in')
        project = commands.binding.project
        self.assertAlmostEqual(project.steps[0].entries[0].overrides['axis3_mill_depth'], depth/25.4)
        self.assertEqual(project.steps[0].entries[0].start, start)
        from dxf2gcode.application.machining import ProjectConfiguration
        config = ProjectConfiguration(project)
        config.metric = 1  # a DXF still declaring mm is explicitly reinterpreted
        config.update_tool_values()
        self.assertEqual(config.metric, 0)
        commands.undo()
        self.assertEqual(commands.binding.project.to_dict(), before)

    def test_foreign_source_selection_cannot_create_partial_assignments(self):
        commands = self.setup_commands()
        before = commands.binding.project.to_dict()
        source = next(iter(commands.binding.sources.values()))
        with self.assertRaises(ValueError):
            commands.assign([source, deepcopy(source)], commands.binding.project.steps[0].id)
        self.assertEqual(commands.binding.project.to_dict(), before)

    def test_route_endpoint_matches_emitted_lead_out_instead_of_original_contour(self):
        import re
        from dxf2gcode.application.toolpath.projections import plan_route_endpoints
        from dxf2gcode.adapters.toolpath.preparation import prepare_shape
        from dxf2gcode.adapters.toolpath.preview import preview_result
        from dxf2gcode_stmove_gcode_test import make_postpro
        from toolpath_test_support import serialize_gcode
        commands = self.setup_commands()
        entry = commands.binding.project.steps[0].entries[0]
        commands.update_entries([entry.id], {'lead_out_mode': 'straight', 'lead_length': 5})
        shape = commands.binding.materialize()[0].shapes[0]
        prepare_shape(shape, build_preview=False)
        plan = preview_result(shape).plan
        start, end, retract = plan_route_endpoints(plan)
        output = serialize_gcode(shape, make_postpro())
        xy = re.findall(r'G[0123] X\s*(-?[\d.]+) Y\s*(-?[\d.]+)', output)
        self.assertTrue(xy, output)
        self.assertAlmostEqual(float(xy[-1][0]), end[0], places=3)
        self.assertAlmostEqual(float(xy[-1][1]), end[1], places=3)
        original_end = shape.get_start_end_points(False)
        self.assertNotEqual(end, (original_end.x, original_end.y))

    def test_tool_change_depends_only_on_output_number_even_with_distinct_definitions(self):
        import re
        from dxf2gcode.adapters.toolpath.preparation import prepare_shape
        from dxf2gcode_stmove_gcode_test import make_postpro
        from dxf2gcode_tool_change_test import ATC
        commands = self.setup_commands()
        step = commands.binding.project.steps[0]
        tool = commands.binding.project.tools[step.tool_id]
        commands.refresh_tool(step.tool_id, replace(tool, speed=1111))
        commands.create_step('Finish', 'contour', replace(tool, speed=2222, tool_diameter=3))
        commands.transfer([step.entries[0].id], commands.binding.project.steps[-1].id, copy=True)
        layers = commands.binding.materialize()
        for layer in layers:
            for shape in layer.shapes:
                prepare_shape(shape, build_preview=False)
        for managed in (False, True):
            with self.subTest(managed=managed):
                pp = make_postpro()
                pp.project_config = layers.machining_config
                pp.initialize_export_vars()
                if managed:
                    pp.vars.Tool_Change.return_state = 'next_start_at_retract'
                    pp.vars.Tool_Change.length_offset_mode = 'tool_number'
                    pp.vars.Program.tool_change = ATC
                body = pp._managed_tool_changes(layers) if managed else pp._legacy_tool_changes(layers)
                self.assertEqual(body.count('T1 M6'), 1)
                self.assertIsNotNone(re.search(r'S\s*1111', body))
                self.assertIsNone(re.search(r'S\s*2222', body))

    def test_compensation_edit_and_rename_preserve_loaded_mode_conflict(self):
        commands = self.setup_commands()
        step = commands.binding.project.steps[0]
        step.kind = 'drill'
        entry = step.entries[0]
        entry.legacy_conflict = (True, True, 41)
        entry.overrides['cut_cor'] = 41
        commands.binding.bind_legacy_editor()
        commands.update_entries([entry.id], {'cut_cor': 40})
        self.assertEqual(commands.binding.project.steps[0].entries[0].legacy_conflict, (True, True, 40))
        commands.edit_step(step.id, 'Rename only', 'drill', step.tool_id)
        self.assertEqual(commands.binding.project.steps[0].entries[0].legacy_conflict, (True, True, 40))
        commands.edit_step(step.id, 'Contour', 'contour', step.tool_id)
        view = commands.binding.materialize()[0].shapes[0]
        self.assertFalse(view.Drill or view.Pocket)
        self.assertEqual(view.cut_cor, 40)


if __name__ == '__main__':
    unittest.main()
