"""R3/R1b P1--P3: project identities, snapshots, migration and real export."""
import contextlib
from copy import deepcopy
from dataclasses import replace
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'source'), str(ROOT / 'tests')]
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from dxf2gcode_leadmove_golden_test import GoldenTestBase, build_shape
from dxf2gcode_leadmove_project_test import _ParentStub
from dxf2gcode_stmove_gcode_test import make_postpro
import dxf2gcode.bootstrap.runtime_state as g
from dxf2gcode.application.machining import MachiningDrawing, contour_key
from dxf2gcode.domain.project.machining_project import (
    MachiningProject, MachiningOperation, LiteralAction, new_id)
from dxf2gcode.domain.project.layercontent import Layers, Shapes
from dxf2gcode.domain.project.tool_settings import ToolSettings
from dxf2gcode.domain.project.project import Project as LegacyProject
from dxf2gcode.presentation.qt.project_session import Project
from dxf2gcode.adapters.project.machining_d2g import decode_project, encode_project
from dxf2gcode.adapters.project.file_store import LegacyProjectFileStore
from dxf2gcode.adapters.project.legacy_d2g import decode_d2g
from dxf2gcode.adapters.toolpath.preparation import prepare_shape
from dxf2gcode.adapters.toolpath.preview import preview_result
from toolpath_test_support import serialize_gcode


class TestMachiningProject(GoldenTestBase):
    def test_load_unifies_only_complete_equal_tool_definitions(self):
        _, binding = self.captured()
        project = binding.project
        tool_id = project.steps[0].tool_id
        tool = project.tools[tool_id]
        duplicate = new_id()
        project.tools[duplicate] = tool
        step = deepcopy(project.steps[0])
        step.id = new_id()
        step.entries = []
        step.tool_id = duplicate
        project.steps.append(step)
        different = new_id()
        project.tools[different] = replace(tool, lead_length=tool.lead_length + 1e-9)
        loaded = MachiningProject.from_dict(project.to_dict())
        self.assertEqual(loaded.steps[0].tool_id, loaded.steps[-1].tool_id)
        self.assertNotIn(duplicate, loaded.tools)
        self.assertIn(different, loaded.tools)

    def drawing(self):
        shape, layer = build_shape(cut_cor=40, done_by_machine=False,
            tool_diameter=2, layer_settings=dict(lead_in_mode='off', lead_out_mode='off'))
        layer.shapes = Shapes([shape])
        layer.exp_order_complete = [0]
        layer.exp_order = [shape.nr]
        return shape, Layers([layer])

    def captured(self):
        shape, layers = self.drawing()
        return shape, MachiningDrawing.capture(layers, g.config)

    def test_capture_preserves_identity_and_explicit_numeric_values(self):
        shape, binding = self.captured()
        step = binding.project.steps[0]
        operation = step.entries[0]
        self.assertEqual(operation.geometry_id, shape.geometry_id)
        self.assertEqual(operation.id, shape.operation_id)
        self.assertEqual(operation.overrides['axis3_mill_depth'], shape.axis3_mill_depth)
        self.assertNotIn('lead_in_mode', operation.overrides)
        self.assertIn('axis3_mill_depth', operation.overrides)
        values, origins, tool = binding.project.resolve(step, operation)
        self.assertEqual(origins['lead_in_mode'], 'step')
        self.assertEqual(origins['axis3_mill_depth'], 'operation')
        self.assertEqual(tool.tool_diameter, 2)

    def test_snapshot_does_not_follow_profile_mutation(self):
        shape, binding = self.captured()
        before = binding.project.to_dict()
        g.config.vars.Tool_Parameters['1']['diameter'] = 99
        g.config.vars.Depth_Coordinates['axis3_mill_depth'] = -99
        self.assertEqual(binding.project.to_dict(), before)
        self.assertEqual(binding.materialize()[0].shapes[0].tool_override.tool_diameter, 2)

    def test_materialized_plan_matches_old_serialization_and_preserves_geometry(self):
        shape, binding = self.captured()
        before = [(geo.Ps.x, geo.Ps.y, geo.Pe.x, geo.Pe.y) for geo in shape.geos]
        expected = serialize_gcode(shape, make_postpro())
        view = binding.materialize()[0].shapes[0]
        prepare_shape(view, build_preview=False)
        actual = serialize_gcode(view, make_postpro())
        self.assertEqual(actual, expected)
        self.assertIsNot(view.geos[0], shape.geos[0])
        self.assertEqual([(geo.Ps.x, geo.Ps.y, geo.Pe.x, geo.Pe.y) for geo in shape.geos], before)

    def test_two_operations_share_reference_but_not_direction_or_parameters(self):
        shape, binding = self.captured()
        project = binding.project
        first = project.steps[0].entries[0]
        second = replace(deepcopy(first), id=new_id(), clockwise=not first.clockwise,
                         overrides=dict(first.overrides, axis3_mill_depth=-7))
        project.steps.append(replace(deepcopy(project.steps[0]), id=new_id(),
                                     name='Finish', entries=[second]))
        views = binding.materialize()
        self.assertEqual(len(project.geometries), 1)
        self.assertEqual(views[0].shapes[0].geometry_id, views[1].shapes[0].geometry_id)
        self.assertNotEqual(views[0].shapes[0].cw, views[1].shapes[0].cw)
        self.assertNotEqual(views[0].shapes[0].axis3_mill_depth, views[1].shapes[0].axis3_mill_depth)
        self.assertEqual(shape.axis3_mill_depth, first.overrides['axis3_mill_depth'])

    def test_roundtrip_keeps_ids_order_provenance_and_literals(self):
        _, binding = self.captured()
        binding.project.steps[0].entries.insert(0, LiteralAction(new_id(), 'Pause', 'M0', False))
        data = binding.project.to_dict()
        restored = MachiningProject.from_dict(json.loads(json.dumps(data)))
        self.assertEqual(restored.to_dict(), data)

    def test_explicit_tool_update_is_atomic_and_shared(self):
        _, binding = self.captured()
        project = binding.project
        identity, tool = next(iter(project.tools.items()))
        with self.assertRaises(ValueError):
            project.update_tool(identity, replace(tool, tool_diameter=-1))
        self.assertEqual(project.tools[identity], tool)
        project.update_tool(identity, replace(tool, tool_diameter=3))
        self.assertEqual(binding.materialize()[0].shapes[0].tool_override.tool_diameter, 3)
        project.update_tool(identity, replace(tool, speed=1234, lead_length=4))
        view = binding.materialize()[0].shapes[0]
        self.assertEqual((view.tool_override.speed, view.tool_override.lead_length), (1234, 4))
        self.assertEqual(view.parameter_origins['speed'], 'tool')

    def test_new_source_geometry_is_unassigned_and_missing_reference_blocks(self):
        _, binding = self.captured()
        original_id = next(iter(binding.project.geometries))
        new_shape, layers = self.drawing()
        new_shape.geos[0].Ps.x += .00001
        restored = MachiningDrawing(binding.project, layers)
        self.assertEqual(restored.project.unresolved[original_id], 'missing')
        self.assertEqual(restored.unassigned, (new_shape,))
        with self.assertRaisesRegex(ValueError, 'Unresolved'):
            restored.materialize()
        restored.project.steps[0].entries[0].enabled = False
        restored.materialize()

    def test_identical_candidates_are_not_silently_matched(self):
        shape, binding = self.captured()
        duplicate = deepcopy(shape)
        duplicate.parentLayer = binding.source_layers[0]
        binding.source_layers[0].shapes.append(duplicate)
        binding.bind()
        self.assertEqual(set(binding.project.unresolved.values()), {'ambiguous'})
        with self.assertRaises(ValueError):
            binding.materialize()

    def test_geometry_key_ignores_direction_and_preserves_submillimetre_differences(self):
        shape, _ = self.drawing()
        key = contour_key(shape)
        shape.reverse()
        self.assertEqual(contour_key(shape), key)
        shape.geos[0].Ps.x += .00001
        self.assertNotEqual(contour_key(shape), key)

    def test_saved_project_codec_is_strict_and_does_not_execute_text(self):
        _, layers = self.drawing()
        parent = _ParentStub(layers)
        text = Project(parent).export_current()
        restored = decode_project(text)
        self.assertEqual(restored.version, 2.0)
        malformed = json.loads(text)
        malformed['machining']['steps'][0]['entries'][0]['geometry_id'] = 'unknown'
        with self.assertRaises(ValueError):
            decode_project(json.dumps(malformed))
        with self.assertRaises(ValueError):
            decode_project(text.replace('"version": 2.0', '"version": 2.0, "version": 2.0'))
        with self.assertRaises(ValueError):
            decode_project(text.replace('"version": 2.0', '"version": NaN'))
        with self.assertRaises(Exception):
            decode_project('__import__("os").system("echo unsafe")')

    def test_gui_facade_load_save_and_single_operation_edit_keep_ids(self):
        _, layers = self.drawing()
        parent = _ParentStub(layers)
        session = Project(parent)
        first = decode_project(session.export_current())
        session.load(first, compleet=False)
        shape = parent.layerContents[0].shapes[0]
        shape.axis3_mill_depth = -8
        second = decode_project(session.export_current())
        self.assertEqual(first.machining.steps[0].id, second.machining.steps[0].id)
        self.assertEqual(first.machining.steps[0].entries[0].id, second.machining.steps[0].entries[0].id)
        self.assertEqual(second.machining.steps[0].entries[0].overrides['axis3_mill_depth'], -8)

    def test_legacy_versions_migrate_effective_values_without_changing_output(self):
        for version in (1.1, 1.2, 1.3, 1.4, 1.5):
            with self.subTest(version=version):
                _, layers = self.drawing()
                parent = _ParentStub(layers)
                legacy = LegacyProject(parent, g.config, decode=decode_d2g)
                text = legacy.export().replace('1.5', str(version), 1)
                if version < 1.5:
                    # Pre-1.5 files without a knife-settings snapshot are a
                    # supported historical representation.
                    text = '\n'.join(line for line in text.splitlines()
                                     if not line.startswith('d2g.drag_knife ='))
                session = Project(parent)
                session.load(text, compleet=False)
                expected = serialize_gcode(parent.layerContents[0].shapes[0], make_postpro())
                document = decode_project(session.export_current())
                self.assertEqual(document.version, 2.0)
                view = session.machining_drawing.materialize()[0].shapes[0]
                prepare_shape(view, build_preview=False)
                self.assertEqual(serialize_gcode(view, make_postpro()), expected)

    def test_invalid_snapshot_is_rejected_before_gui_state_changes(self):
        _, layers = self.drawing()
        parent = _ParentStub(layers)
        session = Project(parent)
        data = json.loads(session.export_current())
        data['machining']['configuration']['Depth_Coordinates'].pop('axis3_retract')
        with self.assertRaises(ValueError):
            session.load(json.dumps(data))
        self.assertIs(parent.layerContents[0], layers[0])
        data = json.loads(session.export_current())
        data['source']['layers'][0]['shapes'] = [{}]
        with self.assertRaises(ValueError):
            decode_project(json.dumps(data))

    def test_explicit_active_operation_edits_only_that_assignment(self):
        shape, binding = self.captured()
        first = binding.project.steps[0].entries[0]
        second = replace(deepcopy(first), id=new_id(), overrides=dict(first.overrides, axis3_mill_depth=-6))
        binding.project.steps.append(replace(deepcopy(binding.project.steps[0]), id=new_id(), entries=[second]))
        binding.bind_legacy_editor()
        binding.activate_operation(second.id)
        shape.axis3_mill_depth = -8
        binding.synchronize_editor()
        self.assertEqual(binding.project.steps[0].entries[0].overrides['axis3_mill_depth'], first.overrides['axis3_mill_depth'])
        self.assertEqual(binding.project.steps[1].entries[0].overrides['axis3_mill_depth'], -8)

    def test_shared_geometry_requires_active_editor_context(self):
        shape, binding = self.captured()
        first = binding.project.steps[0].entries[0]
        binding.project.steps.append(replace(deepcopy(binding.project.steps[0]), id=new_id(),
            entries=[replace(deepcopy(first), id=new_id())]))
        binding.bind_legacy_editor()
        shape.axis3_mill_depth = -8
        with self.assertRaisesRegex(ValueError, 'explicit machining operation'):
            binding.synchronize_editor()

    def test_preview_and_export_use_the_same_saved_settings(self):
        shape, binding = self.captured()
        binding.bind_legacy_editor()
        g.config.vars.Tool_Parameters['1']['diameter'] = 80
        prepare_shape(shape, build_preview=False)
        preview = preview_result(shape).plan
        view = binding.materialize()[0].shapes[0]
        prepare_shape(view, build_preview=False)
        self.assertEqual(preview.actions, preview_result(view).plan.actions)

    def test_atomic_file_store_keeps_legacy_file_and_writes_utf8(self):
        _, layers = self.drawing()
        text = Project(_ParentStub(layers)).export_current()
        store = LegacyProjectFileStore()
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'old.d2g'
            path.write_text('old legacy file')
            with self.assertRaises(IOError):
                store.write_text(path, text)
            self.assertEqual(path.read_text(), 'old legacy file')
            target = Path(folder) / 'new.d2g'
            store.write_text(target, text)
            self.assertEqual(store.read_text(target), text)
            with patch('dxf2gcode.adapters.project.file_store.os.replace', side_effect=OSError):
                with self.assertRaises(OSError):
                    store.write_text(target, text)
            self.assertEqual(store.read_text(target), text)
            self.assertEqual(len(list(Path(folder).iterdir())), 2)

    def test_real_new_project_roundtrip_and_cli_export(self):
        from dxf2gcode.bootstrap.composition import create_drawing_session
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'new.d2g'
            state = create_drawing_session(g.config, str(path))
            state.filename = str(ROOT / 'docs/assets/examples/first-dxf/rectangle-20x10-mm.dxf')
            self.assertTrue(state.load())
            state.layerContents[0].exp_order_complete = [0]
            parent = Project(state)
            text = parent.export_current()
            path.write_text(text, encoding='utf-8')
            document = decode_project(text)
            self.assertEqual(len(document.machining.geometries), 1)
            env = dict(os.environ, HOME=folder, USERPROFILE=folder, QT_QPA_PLATFORM='offscreen')
            output = Path(folder) / 'output.ngc'
            result = subprocess.run([sys.executable, str(ROOT / 'source/dxf2gcode.py'),
                '--cfg', 'r3', '--quiet', '--export', str(output), str(path)],
                env=env, cwd=folder, capture_output=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr.decode(errors='replace'))
            self.assertTrue(output.exists())
            self.assertIn('G', output.read_text())
            # Missing current-table tools block the complete headless export.
            tool_id = document.machining.steps[0].tool_id
            document.machining.tools[tool_id] = replace(document.machining.tools[tool_id], tool_nr=99)
            path.write_text(encode_project(document.values, document.machining), encoding='utf-8')
            output.write_text('original program')
            rejected = subprocess.run([sys.executable, str(ROOT / 'source/dxf2gcode.py'),
                '--cfg', 'r3', '--quiet', '--export', str(output), str(path)],
                env=env, cwd=folder, capture_output=True, timeout=30)
            self.assertEqual(rejected.returncode, 2)
            self.assertEqual(rejected.stdout, b'')
            self.assertEqual(output.read_text(), 'original program')
            self.assertIn('T99', rejected.stderr.decode(errors='replace'))
            # Historical project files must not bypass the same export gate.
            legacy_parent = _ParentStub(state.layerContents)
            legacy_parent.filename = state.filename
            state.layerContents[0].shapes[0].tool_override = document.machining.tools[tool_id]
            path.write_text(LegacyProject(legacy_parent, g.config, decode=decode_d2g).export(), encoding='utf-8')
            legacy_rejected = subprocess.run([sys.executable, str(ROOT / 'source/dxf2gcode.py'),
                '--cfg', 'r3', '--quiet', '--export', str(output), str(path)],
                env=env, cwd=folder, capture_output=True, timeout=30)
            self.assertEqual(legacy_rejected.returncode, 2)
            self.assertEqual(legacy_rejected.stdout, b'')
            self.assertEqual(output.read_text(), 'original program')
            self.assertIn('T99', legacy_rejected.stderr.decode(errors='replace'))

    def test_same_tool_number_can_keep_distinct_diameters(self):
        shape, layers = self.drawing()
        second = deepcopy(shape)
        second.parentLayer = layers[0]
        second.nr = 2
        for geo in second.geos:
            geo.Ps.x += 200
            geo.Pe.x += 200
            geo.make_abs_geo()
        second.tool_override = replace(ToolSettings(**{key: getattr(layers[0], key)
            for key in ToolSettings.__dataclass_fields__}), tool_diameter=3)
        layers[0].shapes.append(second)
        layers[0].exp_order_complete = [0, 1]
        binding = MachiningDrawing.capture(layers, g.config)
        self.assertEqual(len(binding.project.tools), 2)
        self.assertEqual([tool.tool_nr for tool in binding.project.tools.values()], [1, 1])
        self.assertEqual([view.shapes[0].tool_override.tool_diameter for view in binding.materialize()], [2, 3])
        self.assertEqual(MachiningProject.from_dict(binding.project.to_dict()).to_dict(), binding.project.to_dict())

    def test_interleaved_tools_and_literal_keep_original_order(self):
        from dxf2gcode.domain.toolpath.customgcode import CustomGCode
        shape, layers = self.drawing()
        shapes = [shape]
        for nr in (2, 3):
            other = deepcopy(shape)
            other.parentLayer = layers[0]
            other.nr = nr
            for geo in other.geos:
                geo.Ps.x += nr * 200
                geo.Pe.x += nr * 200
                geo.make_abs_geo()
            shapes.append(other)
        tool = ToolSettings(**{key: getattr(layers[0], key) for key in ToolSettings.__dataclass_fields__})
        shapes[1].tool_override = replace(tool, tool_nr=2)
        pause = CustomGCode('Pause', 4, 'M0', layers[0])
        layers[0].shapes = Shapes([shapes[0], pause, shapes[1], shapes[2]])
        layers[0].exp_order_complete = [0, 1, 2, 3]
        binding = MachiningDrawing.capture(layers, g.config)
        self.assertEqual([binding.project.tools[s.tool_id].tool_nr for s in binding.project.steps], [1, 2, 1])
        entries = [entry for step in binding.project.steps for entry in step.entries]
        self.assertIsInstance(entries[1], LiteralAction)
        self.assertEqual(entries[1].gcode, 'M0')
        self.assertEqual([getattr(s, 'geometry_id', None) for l in binding.materialize() for s in l.shapes],
                         [shapes[0].geometry_id, None, shapes[1].geometry_id, shapes[2].geometry_id])

    def test_explicit_first_lead_does_not_become_default_for_second_contour(self):
        shape, layers = self.drawing()
        shape.lead_in_mode = 'radius'
        second = deepcopy(shape)
        second.parentLayer = layers[0]
        second.lead_in_mode = 'default'
        for geo in second.geos:
            geo.Ps.x += 200
            geo.Pe.x += 200
            geo.make_abs_geo()
        layers[0].shapes.append(second)
        layers[0].exp_order_complete = [0, 1]
        binding = MachiningDrawing.capture(layers, g.config)
        first, second = binding.materialize()[0].shapes
        self.assertEqual(first.lead_in_mode, 'radius')
        self.assertEqual(second.lead_in_mode, 'off')

    def test_legacy_conflict_is_preserved_and_planning_is_blocked(self):
        shape, layers = self.drawing()
        shape.Drill, shape.Pocket, shape.cut_cor = True, True, 41
        binding = MachiningDrawing.capture(layers, g.config)
        view = binding.materialize()[0].shapes[0]
        self.assertEqual((view.Drill, view.Pocket, view.cut_cor), (True, True, 41))
        prepare_shape(view, build_preview=False)
        self.assertEqual(preview_result(view).diagnostics[0].code, 'machining.conflict')

    def test_new_drawing_and_migration_reload_preserve_block_transform(self):
        from dxf2gcode.bootstrap.composition import create_drawing_session
        source = str(ROOT / 'docs/assets/examples/first-dxf/rectangle-20x10-mm.dxf')
        first = create_drawing_session(g.config, source + '.d2g')
        first.filename = source
        self.assertTrue(first.load())
        binding = MachiningDrawing.capture(first.layerContents, g.config)
        identity = next(iter(binding.project.geometries))
        transformed = create_drawing_session(g.config, source + '.d2g')
        transformed.filename = source
        transformed.cont_dx, transformed.cont_scale = 10, 2
        self.assertTrue(transformed.load())
        rebound = MachiningDrawing(binding.project, transformed.layerContents)
        self.assertEqual(rebound.project.unresolved, {})
        self.assertEqual(rebound.materialize()[0].shapes[0].geometry_id, identity)
        view = rebound.materialize()[0].shapes[0]
        self.assertGreaterEqual(min(g.Ps.x for g in view.geos.abs_iter()), 10)

    def test_newly_imported_additional_contour_is_not_exported_automatically(self):
        shape, binding = self.captured()
        additional = deepcopy(shape)
        additional.parentLayer = binding.source_layers[0]
        for geo in additional.geos:
            geo.Ps.x += 200
            geo.Pe.x += 200
            geo.make_abs_geo()
        binding.source_layers[0].shapes.append(additional)
        rebound = MachiningDrawing(binding.project, binding.source_layers)
        self.assertEqual(rebound.unassigned, (additional,))
        self.assertEqual(sum(len(l.shapes) for l in rebound.materialize()), 1)

    def test_unresolved_new_project_preserves_output_and_returns_failure(self):
        from dxf2gcode.bootstrap.composition import create_drawing_session
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'new.d2g'
            state = create_drawing_session(g.config, str(path))
            state.filename = str(ROOT / 'docs/assets/examples/first-dxf/rectangle-20x10-mm.dxf')
            self.assertTrue(state.load())
            state.layerContents[0].exp_order_complete = [0]
            text = Project(state).export_current()
            document = decode_project(text)
            identity, geometry = next(iter(document.machining.geometries.items()))
            document.machining.geometries[identity] = replace(geometry, fingerprint='missing')
            path.write_text(encode_project(document.values, document.machining), encoding='utf-8')
            output = Path(folder) / 'output.ngc'
            output.write_text('original program')
            env = dict(os.environ, HOME=folder, USERPROFILE=folder, QT_QPA_PLATFORM='offscreen')
            result = subprocess.run([sys.executable, str(ROOT / 'source/dxf2gcode.py'),
                '--cfg', 'r3', '--quiet', '--export', str(output), str(path)],
                env=env, cwd=folder, capture_output=True, timeout=30)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stdout, b'')
            self.assertEqual(output.read_text(), 'original program')


if __name__ == '__main__':
    unittest.main()
