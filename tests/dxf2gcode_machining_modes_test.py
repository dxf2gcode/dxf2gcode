"""B1/B2: mode transitions, project conflicts and drilling availability."""

import itertools
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'source'))

from dxf2gcode.domain.project.machining import MachiningState, machining_conflict
from dxf2gcode.application.shapes import SetMachiningMode, AutomaticCutterCompensation
from dxf2gcode_leadmove_golden_test import GoldenTestBase, build_shape
from dxf2gcode_stmove_gcode_test import make_postpro, make_plan_service
from dxf2gcode_leadmove_project_test import _ParentStub, Project
import dxf2gcode.bootstrap.runtime_state as g
from dxf2gcode.domain.geometry.arcgeo import ArcGeo
from dxf2gcode.domain.geometry.point import Point
from dxf2gcode.domain.project.shape import Geos
from dxf2gcode.adapters.toolpath.preparation import prepare_shape
from dxf2gcode.presentation.qt.canvas import MyDropDownMenu
from dxf2gcode.presentation.qt.qt_compat.QtWidgets import QMenu, QMessageBox
from dxf2gcode.presentation.qt.qt_compat.QtCore import QPoint, QTranslator


class TestMachiningRule(unittest.TestCase):
    def test_all_deliberate_transitions(self):
        for drill, pocket, comp in itertools.product((False, True), (False, True), (40, 41, 42)):
            state = MachiningState(drill, pocket, comp)
            with self.subTest(state=state):
                self.assertEqual(machining_conflict(drill, pocket, comp),
                                 drill and (pocket or comp != 40))
                self.assertEqual(state.transition('drill', True), MachiningState(True, False, 40))
                self.assertEqual(state.transition('drill', False), MachiningState(False, pocket, comp))
                self.assertEqual(state.transition('pocket', True), MachiningState(False, True, comp))
                self.assertEqual(state.transition('pocket', False), MachiningState(drill, False, comp))
                for selected_comp in (40, 41, 42):
                    self.assertEqual(state.transition('compensation', selected_comp),
                                     MachiningState(False, pocket, selected_comp))

    def test_group_action_uses_one_target_and_does_not_restore_previous_modes(self):
        shapes = [SimpleNamespace(Drill=False, Pocket=True, cut_cor=41),
                  SimpleNamespace(Drill=True, Pocket=False, cut_cor=40)]
        action = SetMachiningMode()
        action.execute(shapes, 'drill')
        self.assertTrue(all((s.Drill, s.Pocket, s.cut_cor) == (True, False, 40) for s in shapes))
        action.execute(shapes, 'drill')
        self.assertTrue(all((s.Drill, s.Pocket, s.cut_cor) == (False, False, 40) for s in shapes))

    def test_automatic_milling_compensation_preserves_drilling_and_loaded_conflicts(self):
        for pocket, comp in ((False, 40), (True, 41)):
            shape = SimpleNamespace(nr=1, Drill=True, Pocket=pocket, cut_cor=comp)
            layer = SimpleNamespace(shapes=[shape], automaticCutterCompensationEnabled=lambda: True)
            self.assertEqual(AutomaticCutterCompensation().execute([layer], True, 'milling'), ())
            self.assertEqual((shape.Drill, shape.Pocket, shape.cut_cor), (True, pocket, comp))


class TestMachiningWorkflow(GoldenTestBase):
    def setUp(self):
        super().setUp()
        self.old_window = g.window
        self.tree = Mock()
        g.window = SimpleNamespace(TreeHandler=self.tree)

    def tearDown(self):
        g.window = self.old_window
        super().tearDown()

    def circle(self, machine_comp=False):
        shape, layer = build_shape(cut_cor=40, done_by_machine=machine_comp)
        shape.geos = Geos([ArcGeo(Ps=Point(9, 9), Pe=Point(9, 9),
                                 O=Point(7, 9), r=2, direction=1)])
        for geo in shape.geos:
            geo.make_abs_geo()
        shape.setSelected(True)
        return shape

    def menu(self, shapes):
        scene = SimpleNamespace(shapes=shapes, repaint_shape=Mock(), update=Mock())
        with patch.object(QMenu, 'exec', new=lambda self, position: None):
            return MyDropDownMenu(scene, QPoint(), Point(0, 0))

    def test_menu_actions_refresh_related_flags_and_reopened_menu(self):
        shape = self.circle()
        shape.Pocket, shape.cut_cor = True, 41
        menu = self.menu([shape])
        menu.DrillAction.trigger()
        self.assertEqual((shape.Drill, shape.Pocket, shape.cut_cor), (True, False, 40))
        self.assertFalse(menu.PocketAction.isChecked())
        self.assertTrue(menu.noCompAction.isChecked())
        self.tree.updatePocketMill.assert_called_once_with(shape, False)
        reopened = self.menu([shape])
        self.assertTrue(reopened.DrillAction.isChecked())
        reopened.leCompAction.trigger()
        self.assertFalse(shape.Drill)
        self.assertFalse(reopened.DrillAction.isChecked())
        self.assertEqual(shape.cut_cor, 41)
        reopened.PocketAction.trigger()
        self.assertTrue(shape.Pocket)
        self.assertEqual(shape.cut_cor, 41)

    def test_drilling_geometry_availability_in_both_compensation_configurations(self):
        for machine_comp in (False, True):
            shape = self.circle(machine_comp)
            self.assertTrue(hasattr(self.menu([shape]), 'DrillAction'))
            self.assertEqual(hasattr(self.menu([shape]), 'PocketAction'), not machine_comp)
            shape.closed = False
            menu = self.menu([shape])
            self.assertFalse(hasattr(menu, 'DrillAction'))
            self.assertFalse(hasattr(menu, 'PocketAction'))
            closed = self.circle(machine_comp)
            self.assertFalse(hasattr(self.menu([closed, shape]), 'DrillAction'))
            rectangle, _ = build_shape(cut_cor=40, done_by_machine=machine_comp)
            rectangle.setSelected(True)
            self.assertFalse(hasattr(self.menu([closed, rectangle]), 'DrillAction'))

    def test_mixed_menu_selection_receives_one_consistent_target(self):
        first, second = self.circle(), self.circle()
        first.Pocket, first.cut_cor = True, 42
        second.Drill = True
        menu = self.menu([first, second])
        menu.DrillAction.trigger()
        self.assertTrue(all((s.Drill, s.Pocket, s.cut_cor) == (True, False, 40)
                            for s in (first, second)))
        menu.PocketAction.trigger()
        self.assertTrue(all((s.Drill, s.Pocket, s.cut_cor) == (False, True, 40)
                            for s in (first, second)))
        self.assertTrue(menu.PocketAction.isChecked())
        self.assertFalse(menu.DrillAction.isChecked())

    def test_planner_rejects_each_drilling_conflict(self):
        for pocket, comp in itertools.product((False, True), (40, 41, 42)):
            shape = self.circle()
            shape.Drill, shape.Pocket, shape.cut_cor = True, pocket, comp
            prepare_shape(shape)
            result = make_plan_service().execute_result(shape, make_postpro())
            with self.subTest(pocket=pocket, compensation=comp):
                self.assertEqual(result.has_errors, pocket or comp != 40)
                if result.has_errors:
                    self.assertEqual(shape.stmove.geos, [])
                    self.assertIsNone(shape.toolpath_plan)
                    self.assertEqual(result.diagnostics[0].code, 'machining.conflict')

    def test_conflicting_preview_has_warning_instead_of_machining_overlay(self):
        from dxf2gcode.presentation.qt.canvas2d import StMoveGUI
        shape = self.circle()
        shape.Drill, shape.Pocket = True, True
        item = StMoveGUI(shape)
        self.assertIsNone(item.plan)
        self.assertTrue(item._comp_path.isEmpty())
        self.assertTrue(item._pocket_path.isEmpty())
        self.assertIn('Select a machining mode', item._warning())
        self.assertIsNotNone(item._warning_point())

    def test_drilling_plan_and_export_are_uncompensated_and_have_no_pocket_moves(self):
        for machine_comp in (False, True):
            shape = self.circle(machine_comp)
            shape.Pocket, shape.cut_cor = True, 42
            menu = self.menu([shape])
            menu.DrillAction.trigger()
            prepare_shape(shape)
            post = make_postpro()
            result = make_plan_service().execute_result(shape, post)
            self.assertFalse(result.has_errors, result.diagnostics)
            self.assertTrue(any(a.kind == 'drill' for a in result.plan.actions))
            self.assertFalse(any(a.kind == 'compensation_on' or a.role == 'pocket'
                                 for a in result.plan.actions))
            code = post.write_shape_gcode(shape)
            self.assertRegex(code, r'G1 Z\s+-5\.000')
            self.assertNotIn('G41', code)
            self.assertNotIn('G42', code)

    def test_conflicting_project_preserves_values_warns_and_requires_explicit_resolution(self):
        from dxf2gcode.presentation.qt.application import MainWindow
        shape = self.circle()
        shape.Drill, shape.Pocket, shape.cut_cor = True, True, 41
        layer = shape.parentLayer
        layer.shapes = [shape]
        layer.exp_order_complete = [0]
        parent = _ParentStub([layer])
        content = Project(parent).export(compleet=False)
        shape.Drill, shape.Pocket, shape.cut_cor = False, False, 40
        harness = SimpleNamespace(
            project_repository=SimpleNamespace(load=lambda filename: content),
            d2g=SimpleNamespace(load=lambda document: Project(parent).load(document, compleet=False)),
            tr=lambda text: text)
        with patch.object(QMessageBox, 'warning', return_value=QMessageBox.StandardButton.Ok) as warning:
            MainWindow.loadProject(harness, 'test.d2g')
        warning.assert_called_once()
        self.assertIn(str(shape.nr), warning.call_args.args[2])
        self.assertEqual((shape.Drill, shape.Pocket, shape.cut_cor), (True, True, 41))
        prepare_shape(shape)
        post = make_postpro()
        result = make_plan_service().execute_result(shape, post)
        self.assertTrue(result.has_errors)
        self.assertIsNone(result.plan)
        self.assertEqual(result.diagnostics[0].code, 'machining.conflict')
        self.assertEqual(post.write_shape_gcode(shape), '')
        menu = self.menu([shape])
        menu.noCompAction.trigger()
        self.assertFalse(machining_conflict(shape.Drill, shape.Pocket, shape.cut_cor))
        menu.DrillAction.trigger()
        prepare_shape(shape)
        self.assertFalse(make_plan_service().execute_result(shape, make_postpro()).has_errors)

    def test_conflict_translations_are_available(self):
        from dxf2gcode.domain.toolpath.diagnostics import MODE_CONFLICT
        source = Path(__file__).resolve().parents[1] / 'source/i18n'
        for language in ('de', 'fr', 'ru'):
            translator = QTranslator()
            self.assertTrue(translator.load(str(source / ('dxf2gcode_' + language + '.qm'))))
            for context, text in (('Shape', MODE_CONFLICT),
                                  ('MainWindow', 'Conflicting machining settings'),
                                  ('MainWindow', 'Shapes %s combine drilling with pocket milling or G41/G42. '
                                   'Their settings were preserved. Select drilling, pocket milling '
                                   'or cutter compensation in the context menu to resolve each '
                                   'conflict. Affected shapes cannot be exported until then.')):
                translated = translator.translate(context, text)
                self.assertTrue(translated)
                self.assertNotEqual(translated, text)
