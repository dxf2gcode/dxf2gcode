"""Project-owned tab regions: scopes, geometry, migration and history."""
from copy import deepcopy
from dataclasses import replace
from math import pi
from pathlib import Path

from dxf2gcode_leadmove_golden_test import GoldenTestBase, build_shape
from dxf2gcode_stmove_gcode_test import make_postpro
from dxf2gcode.domain.project.machining_project import StegRegion, MachiningProject, MachiningStep, MachiningOperation, new_id
from dxf2gcode.domain.project.layercontent import Layers, Shapes
from dxf2gcode.domain.geometry.point import Point
from dxf2gcode.application.machining import MachiningDrawing
from dxf2gcode.application.machining_actions import MachiningCommands
from dxf2gcode.application.tab_regions import to_drawing, world_vertices
from dxf2gcode.adapters.toolpath.preparation import prepare_shape
from dxf2gcode.adapters.toolpath.preview import preview_result
import dxf2gcode.bootstrap.runtime_state as g


class TestTabRegions(GoldenTestBase):
    def test_selected_region_batch_is_atomic_and_has_one_undo_entry(self):
        binding, commands = self.case()
        first, second = self.region(binding), self.region(binding)
        before = binding.project.to_dict()
        history = len(commands.undo_stack)
        commands.create_regions([first, second])
        self.assertEqual(len(commands.undo_stack), history+1)
        after = binding.project.to_dict()
        commands.undo()
        self.assertEqual(binding.project.to_dict(), before)
        commands.redo()
        self.assertEqual(binding.project.to_dict(), after)
        with self.assertRaises(ValueError):
            commands.create_regions([self.region(binding), first])
        self.assertEqual(binding.project.to_dict(), after)
        self.assertEqual(len(commands.undo_stack), history+1)

    def test_tool_change_resizes_auto_region_and_undo_restores_tool_and_vertices(self):
        from dxf2gcode.application.tab_regions import rectangle_size
        for refresh in (False, True):
            with self.subTest(refresh=refresh):
                binding, commands = self.case()
                step = binding.project.steps[0]
                entry = step.entries[0]
                auto = self.region(binding, scope='operations', targets=[entry.id], placement_mode='snap')
                manual = self.region(binding, scope='operations', targets=[entry.id])
                commands.create_region(auto)
                commands.create_region(manual)
                before = binding.project.to_dict()
                count = len(commands.undo_stack)
                tool = replace(binding.project.tools[step.tool_id], tool_nr=4, tool_diameter=4)
                if refresh:
                    commands.refresh_tool(step.tool_id, tool)
                else:
                    commands.set_operation_tool([entry.id], tool)
                region = binding.project.regions[auto.id]
                self.assertEqual(rectangle_size(world_vertices(binding, region)), (6, 6))
                self.assertEqual(binding.project.regions[manual.id].vertices, manual.vertices)
                self.assertEqual(len(commands.undo_stack), count+1)
                after = binding.project.to_dict()
                commands.undo()
                self.assertEqual(binding.project.to_dict(), before)
                commands.redo()
                self.assertEqual(binding.project.to_dict(), after)

    def test_shared_auto_region_splits_only_affected_tool_use(self):
        from dxf2gcode.application.tab_regions import rectangle_size
        binding, commands = self.case()
        first, second = binding.project.steps
        region = self.region(binding, placement_mode='snap')
        commands.create_region(region)
        before = binding.project.to_dict()
        tool = replace(binding.project.tools[first.tool_id], tool_nr=4, tool_diameter=4)
        commands.set_operation_tool([first.entries[0].id], tool)
        self.assertEqual(len(binding.project.regions), 2)
        by_operation = {r.targets[0]: r for r in binding.project.regions.values()}
        self.assertEqual(by_operation[second.entries[0].id].vertices, region.vertices)
        changed = by_operation[first.entries[0].id]
        self.assertEqual(rectangle_size(world_vertices(binding, changed)), (6, 6))
        self.assertTrue(all(r.placement_mode == 'snap' and r.scope == 'operations' for r in by_operation.values()))
        commands.undo()
        self.assertEqual(binding.project.to_dict(), before)

    def test_each_region_retains_placement_mode_and_legacy_defaults_to_manual(self):
        binding, commands = self.case()
        first, second = self.region(binding), self.region(binding)
        commands.create_region(first)
        commands.create_region(second)
        commands.update_region(first.id, placement_mode='snap')
        data = binding.project.to_dict()
        restored = MachiningProject.from_dict(data)
        self.assertEqual(restored.regions[first.id].placement_mode, 'snap')
        self.assertEqual(restored.regions[second.id].placement_mode, 'manual')
        commands.undo()
        self.assertEqual(binding.project.regions[first.id].placement_mode, 'manual')
        for value in data['regions']:
            value.pop('placement_mode')
        self.assertTrue(all(r.placement_mode == 'manual' for r in MachiningProject.from_dict(data).regions.values()))
        with self.assertRaises(ValueError):
            commands.update_region(first.id, placement_mode='invalid')

    def test_click_square_has_diameter_plus_length_and_follows_nominal_line(self):
        from dxf2gcode.application.tab_regions import square_on_contour, nominal_contour, rectangle_size
        binding, _ = self.case()
        source = next(iter(binding.sources.values()))
        vertices = square_on_contour(nominal_contour(source), (50, .1), 4+2)
        self.assertEqual(rectangle_size(vertices), (6, 6))
        self.assertEqual(tuple(sum(v[j] for v in vertices)/4 for j in (0, 1)), (50, 0))
        with self.assertRaises(ValueError):
            square_on_contour((), (0, 0), 6)

    def test_dimension_edit_preserves_centre_other_edge_and_precision(self):
        from math import hypot
        from dxf2gcode.application.tab_regions import resize_rectangle, rectangle_size
        vertices = ((0, 0), (3, 4), (-5, 10), (-8, 6))
        value = 7.1234567890123
        changed = resize_rectangle(vertices, 0, value)
        self.assertAlmostEqual(rectangle_size(changed)[0], value, places=12)
        self.assertAlmostEqual(rectangle_size(changed)[1], 10)
        self.assertEqual(tuple(sum(p[j] for p in changed)/4 for j in (0, 1)), (-2.5, 5))
        self.assertAlmostEqual(hypot(changed[2][0]-changed[1][0], changed[2][1]-changed[1][1]), 10)
        for invalid in (0, -1, float('nan'), float('inf')):
            with self.assertRaises(ValueError):
                resize_rectangle(vertices, 1, invalid)

    def test_snap_deduplicates_repeated_uses_and_preserves_dimensions(self):
        from dxf2gcode.application.tab_regions import alignment_candidates, align_rectangle, rectangle_size
        binding, _ = self.case()
        vertices = self.region(binding).vertices
        candidates = alignment_candidates(binding, vertices)
        self.assertEqual(len(candidates), 1)
        contacts = next(iter(candidates.values()))
        changed = align_rectangle(vertices, contacts)
        self.assertEqual(rectangle_size(changed), rectangle_size(vertices))
        self.assertEqual(tuple(sum(p[j] for p in changed)/4 for j in (0, 1)),
                         tuple(sum(p[j] for p in contacts)/2 for j in (0, 1)))
        self.assertFalse(alignment_candidates(binding, ((40, 0), (60, 0), (60, 2), (40, 2))))

    def test_arc_snap_uses_original_circle_contacts(self):
        from math import sqrt
        from dxf2gcode.domain.toolpath.tabs import region_crossings
        from dxf2gcode.domain.toolpath.inputs import PathGeometry
        arc = PathGeometry('arc', (10, 0), (-10, 0), 10*pi,
                           center=(0, 0), radius=10, start_angle=0, end_angle=pi, sweep=pi)
        vertices = ((-2, 9), (2, 9), (2, 11), (-2, 11))
        contacts = region_crossings((arc,), vertices)
        self.assertEqual(len(contacts), 2)
        for x, y in contacts:
            self.assertAlmostEqual(abs(x), 2)
            self.assertAlmostEqual(y, sqrt(96))

    def test_assignment_candidates_use_nominal_geometry_and_keep_repeated_operations(self):
        from dxf2gcode.application.tab_regions import overlapping_operations
        binding, _ = self.case()
        region = self.region(binding)
        expected = {(s.id, s.entries[0].id) for s in binding.project.steps}
        self.assertEqual(set(overlapping_operations(binding, region)), expected)
        # Eligibility is geometric, even when an operation/region is disabled,
        # excluded or not currently selected for processing tabs.
        binding.project.steps[0].entries[0].enabled = False
        region.enabled, region.scope, region.targets = False, 'operations', []
        self.assertEqual(set(overlapping_operations(binding, region)), expected)
        region.vertices = ((40, 0), (60, 0), (60, 2), (40, 2))
        self.assertFalse(overlapping_operations(binding, region))
        region.vertices = ((400, 400), (600, 400), (600, 600), (400, 600))
        self.assertFalse(overlapping_operations(binding, region))

    def case(self):
        shape, layer = build_shape(cut_cor=40, done_by_machine=False, tool_diameter=2,
                                  layer_settings=dict(lead_in_mode='off', lead_out_mode='off'))
        layer.shapes = Shapes([shape])
        binding = MachiningDrawing.capture(Layers([layer]), g.config)
        commands = MachiningCommands(binding)
        step = binding.project.steps[0]
        commands.create_step('Finish', 'contour', step.tool_id)
        other = binding.project.steps[-1]
        commands.transfer([step.entries[0].id], other.id, copy=True)
        return binding, commands

    def region(self, binding, **kwargs):
        return StegRegion(new_id(), vertices=((40, -1), (60, -1), (60, 1), (40, 1)),
                          height=-1, xy_feed=200, z_feed=100, **kwargs)

    def effective(self, binding):
        layers = binding.materialize()
        result = {}
        for layer in layers.non_break_layer_iter():
            for shape in layer.shapes:
                prepare_shape(shape, build_preview=False)
                plan = preview_result(shape, make_postpro(), layers).plan
                result[shape.operation_id] = {a.modifier_id for a in plan.actions if a.modifier_id}
        return result

    def test_scope_exclusion_changes_only_the_target_operation_and_undo_restores(self):
        binding, commands = self.case()
        region = self.region(binding)
        commands.create_region(region)
        ids = [s.entries[0].id for s in binding.project.steps]
        self.assertTrue(all(region.id in ids for ids in self.effective(binding).values()))
        commands.update_region(region.id, excluded=[ids[0]])
        self.assertNotIn(region.id, self.effective(binding)[ids[0]])
        self.assertIn(region.id, self.effective(binding)[ids[1]])
        commands.undo()
        self.assertTrue(all(region.id in ids for ids in self.effective(binding).values()))
        commands.update_region(region.id, scope='operations', targets=[ids[1]])
        self.assertNotIn(region.id, self.effective(binding)[ids[0]])
        self.assertIn(region.id, self.effective(binding)[ids[1]])

    def test_step_scope_includes_new_operations_copied_into_the_step(self):
        binding, commands = self.case()
        step = binding.project.steps[0]
        region = self.region(binding, scope='steps', targets=[step.id])
        commands.create_region(region)
        commands.transfer([binding.project.steps[-1].entries[0].id], step.id, copy=True)
        result = self.effective(binding)
        self.assertTrue(all(region.id in result[e.id] for e in binding.project.steps[0].entries))
        self.assertNotIn(region.id, result[binding.project.steps[-1].entries[0].id])

    def test_region_values_and_geometry_survive_history_and_json_roundtrip(self):
        binding, commands = self.case()
        original = binding.project.to_dict()
        region = self.region(binding)
        commands.create_region(region)
        commands.update_region(region.id, vertices=((42, -1), (62, -1), (62, 1), (42, 1)), height=-.7)
        restored = MachiningProject.from_dict(binding.project.to_dict())
        self.assertEqual(restored.to_dict(), binding.project.to_dict())
        commands.remove_region(region.id)
        self.assertNotIn(region.id, binding.project.regions)
        commands.undo()
        self.assertEqual(binding.project.regions[region.id].height, -.7)
        commands.undo()
        commands.undo()
        self.assertEqual(binding.project.to_dict(), original)
        commands.redo()
        self.assertIn(region.id, binding.project.regions)

    def test_manual_regions_follow_root_rotation_scale_translation_and_inverse(self):
        from dxf2gcode.domain.project.entitycontent import EntityContent
        binding, commands = self.case()
        root = EntityContent(0, '', None, Point(5, 7), Point(), [2, 2, 1], pi/2)
        for source in binding.sources.values():
            source.parentEntity = root
        region = self.region(binding)
        commands.create_region(region)
        world = world_vertices(binding, region)
        self.assertAlmostEqual(world[0][0], 7)
        self.assertAlmostEqual(world[0][1], 87)
        for actual, expected in zip(to_drawing(binding, world), region.vertices):
            self.assertAlmostEqual(actual[0], expected[0])
            self.assertAlmostEqual(actual[1], expected[1])
        root.p0.x += 10
        self.assertAlmostEqual(world_vertices(binding, region)[0][0], world[0][0]+10)

    def test_legacy_hidden_break_step_is_migrated_without_losing_values_or_identity(self):
        binding, _ = self.case()
        project = binding.project
        original = project.steps[0]
        entry = replace(deepcopy(original.entries[0]), id=new_id(), overrides=dict(axis3_mill_depth=-.7, f_g1_plane=123, f_g1_depth=99))
        project.steps.append(MachiningStep(new_id(), 'BREAKS:', 'break', original.tool_id, entries=[entry]))
        data = project.to_dict()
        del data['regions']  # Actual 2.0 payload.
        restored = MachiningProject.from_dict(data)
        self.assertFalse(any(s.kind == 'break' for s in restored.steps))
        region = restored.regions[entry.id]
        self.assertEqual((region.height, region.xy_feed, region.z_feed), (-.7, 123, 99))
        self.assertEqual(region.geometry_id, entry.geometry_id)

    def test_circle_example_captures_imported_regions_as_modifiers_and_plans_arcs(self):
        from dxf2gcode.adapters.dxf.parser import ReadDXF
        from dxf2gcode.application.drawings import BuildDrawingModel
        path = Path(__file__).resolve().parents[1] / 'dxf/BreakExample_Circle.dxf'
        model = BuildDrawingModel(ReadDXF(filename=str(path)), g.config, type(build_shape()[0]), False).execute()
        binding = MachiningDrawing.capture(model.layers, g.config)
        self.assertTrue(binding.project.regions)
        self.assertFalse(any(s.kind == 'break' for s in binding.project.steps))
        self.assertTrue(any(self.effective(binding).values()))
