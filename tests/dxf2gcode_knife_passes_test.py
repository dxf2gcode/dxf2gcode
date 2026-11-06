"""D1/D2: actual tip coverage, depth transitions, orientation and XYZ output."""

from dataclasses import replace
from math import atan2, cos, hypot, pi, sin
from pathlib import Path
import re
import sys
import unittest

sys.path[:0] = [str(Path(__file__).parent), str(Path(__file__).resolve().parents[1] / 'source')]

from dxf2gcode.domain.toolpath.inputs import PathGeometry, MachiningSettings, MachineCapabilities, ToolpathRequest
from dxf2gcode.domain.toolpath.planner import ToolpathPlanner
from dxf2gcode.domain.toolpath.strategies.drag_knife import DragKnifeStrategy
from dxf2gcode.application.toolpath.projections import plan_preview_segments, plan_xyz_segments
from dxf2gcode.adapters.toolpath.gcode_exporter import ToolpathGCodeExporter
from dxf2gcode.adapters.postprocessor.dialect import ProfileDialect


def line(a, b):
    return PathGeometry('line', a, b, hypot(b[0]-a[0], b[1]-a[1]))


def request(closed=True, **options):
    points = [(0, 0), (10, 0), (10, 10)]
    if closed:
        points += [(0, 10), (0, 0)]
    settings = MachiningSettings(machine_type='drag_knife',
                                tool_radius=.25, slice_depth=-.1, final_depth=-.3,
                                lead_in_mode='straight', lead_length=3,
                                lead_out_mode='straight', drag_exit_length=4)
    return ToolpathRequest(1, replace(settings, **options), MachineCapabilities(),
                           contour=tuple(line(a, b) for a,b in zip(points, points[1:])), closed=closed)


class TestKnifePasses(unittest.TestCase):
    def plan(self, req):
        result = ToolpathPlanner().plan(req)
        self.assertFalse(result.has_errors, result.diagnostics)
        self.assertIsNotNone(result.plan)
        self.assertEqual(result, ToolpathPlanner().plan(req))
        # Verify the emitted sequence has no hidden XY or Z jumps.
        xy, z = result.plan.approach_xy, req.settings.workpiece_top
        for action in result.plan.actions:
            kind, args = action.kind, action.args
            if kind == 'rapid_xy':
                xy = args[0]
            elif kind in ('linear_z', 'rapid_z'):
                z = args[0]
            elif kind in ('linear_xy', 'linear_xyz', 'arc'):
                start, end = (args[1], args[2]) if kind == 'arc' else args[:2]
                self.assertLess(hypot(xy[0]-start[0], xy[1]-start[1]), 1e-7, action)
                if kind == 'linear_xyz':
                    self.assertAlmostEqual(z, args[2])
                    z = args[3]
                xy = end
        return result.plan

    def test_closed_depths_and_single_initial_external_entry(self):
        plan = self.plan(request(drag_swivel_depth=-.01))
        plunges = [a.args[0] for a in plan.actions if a.role == 'plunge']
        self.assertEqual([round(z, 5) for z in plunges], [-.1, -.2, -.3])
        self.assertEqual(sum(a.kind == 'rapid_xy' for a in plan.actions), 1)
        self.assertEqual(sum(a.kind == 'rapid_z' and a.role == 'retract' for a in plan.actions), 1)
        self.assertLess(plan.approach_xy[0], 0)

    def test_optional_return_happens_once_at_external_exit_and_at_contact_depth(self):
        req = request(drag_return=True, drag_start_angle=90, drag_swivel_depth=-.02)
        plan = self.plan(req)
        self.assertAlmostEqual(plan.knife_heading, pi/2)
        self.assertEqual(plan.knife_tool, (0,.25))
        markers = [i for i,a in enumerate(plan.actions) if a.role == 'return_alignment']
        self.assertEqual(len(markers), 1)
        after = plan.actions[markers[0]:]
        self.assertFalse(any(a.role == 'cut' and a.kind in ('linear_xy','linear_xyz','arc') for a in after))
        self.assertTrue(any(a.kind == 'arc' for a in after))
        self.assertTrue(all(a.args[0] >= -.02-1e-9 for a in after if a.kind == 'linear_z'))
        blocked = ToolpathPlanner().plan(request(drag_return=True,lead_out_mode='off'))
        self.assertTrue(blocked.has_errors)

    def test_previous_heading_is_used_only_when_selected(self):
        base = request(drag_entry_mode='previous')
        req = replace(base, initial_state=replace(base.initial_state,knife_heading=pi/2))
        carried = self.plan(req)
        fixed = self.plan(replace(req,settings=replace(req.settings,drag_entry_mode='fixed')))
        self.assertNotEqual(carried.approach_xy, fixed.approach_xy)
        self.assertEqual(carried.knife_heading, fixed.knife_heading)

    def test_short_initial_segments_close_in_both_directions_with_and_without_overlap(self):
        from dxf2gcode.domain.toolpath.inputs import reverse_chain
        points = [(0,0),(.1,0),(10,0),(10,10),(0,10),(0,.1),(0,0)]
        chain = tuple(line(a,b) for a,b in zip(points,points[1:]))
        for geos in (chain, reverse_chain(chain)):
            for overlap in (0,.3):
                req = request(drag_ramp_length=2, overcut_enabled=bool(overlap),overcut_length=overlap)
                plan = self.plan(replace(req,contour=geos))
                finishing = [a for a in plan.actions if a.role == 'ramp_finish' and a.kind == 'linear_xy']
                self.assertAlmostEqual(sum(hypot(b[0]-a[0],b[1]-a[1]) for a,b in (m.args for m in finishing)),2)

    def test_unknown_orientation_uses_external_stroke_after_every_lift(self):
        for closed in (False,True):
            req = request(closed, drag_entry_mode='unknown',drag_alignment_length=2)
            plan = self.plan(req)
            strokes = [a for a in plan.actions if a.role == 'knife_alignment']
            self.assertEqual(len(strokes), 1 if closed else 3)
            for a in strokes:
                self.assertAlmostEqual(hypot(a.args[1][0]-a.args[0][0],a.args[1][1]-a.args[0][1]),2)
                self.assertLess(max(a.args[0][0],a.args[1][0]), 0)
            before = plan.actions[:plan.actions.index(strokes[0])]
            self.assertFalse(any(a.kind == 'arc' for a in before))
            other = replace(req, settings=replace(req.settings, drag_start_angle=173))
            self.assertEqual(plan, self.plan(other))
        for req in (request(drag_entry_mode='unknown'),
                    request(drag_entry_mode='unknown',drag_alignment_length=2,lead_in_mode='off')):
            self.assertTrue(ToolpathPlanner().plan(req).has_errors)

    def test_closed_ramp_coverage_and_additional_pass_are_separate(self):
        base = self.plan(request(drag_ramp_length=2, overcut_enabled=True, overcut_length=.5))
        extra = self.plan(request(drag_ramp_length=2, overcut_enabled=True, overcut_length=.5, drag_extra_pass=True))
        for plan in (base, extra):
            finishing = [a for a in plan.actions if a.role == 'ramp_finish' and a.kind == 'linear_xy']
            self.assertEqual(len(finishing), 1)
            self.assertAlmostEqual(hypot(*(b-a for a,b in zip(*finishing[0].args))), 2)
            overlaps = [a for a in plan.actions if a.role == 'overcut' and a.kind == 'linear_xy']
            self.assertAlmostEqual(hypot(*(b-a for a,b in zip(*overlaps[0].args))), .5)
        self.assertFalse(any(a.role == 'extra_cut' for a in base.actions))
        # Full 40 mm tip contour, without the separate swivel arcs.
        full = [a for a in extra.actions if a.role == 'extra_cut' and a.kind == 'linear_xy']
        self.assertAlmostEqual(sum(hypot(*(b-a for a,b in zip(*a.args))) for a in full), 40)

    def test_ramp_crosses_segment_and_swivel_without_reset_or_missing_tail(self):
        req = request(lead_in_mode='off', drag_ramp_length=15)
        plan = self.plan(req)
        ramps = [a for a in plan.actions if a.kind == 'linear_xyz']
        self.assertGreater(len(ramps), 3)
        for a in ramps:
            self.assertLessEqual(a.args[3], a.args[2])
        cuts = [a for a in plan.actions if a.kind == 'linear_xy' and a.role == 'cut']
        self.assertTrue(any(hypot(a.args[1][0], a.args[1][1]+.25) < 1e-8 for a in cuts))
        self.assertTrue(any(s.start[2] != s.end[2] and s.start[:2] != s.end[:2]
                            for s in plan_preview_segments(plan)))
        self.assertTrue(any(a[2] != b[2] and a[:2] != b[:2] for a,b in plan_xyz_segments(plan)))

    def test_open_alternating_turns_outside_and_recomputes_offset(self):
        plan = self.plan(request(False, drag_alternate=True, drag_ramp_length=2, drag_extra_pass=True))
        self.assertEqual(sum(a.kind == 'rapid_xy' for a in plan.actions), 1)
        turns = [a for a in plan.actions if a.kind == 'arc' and abs(abs(a.args[8])-pi) < 1e-7]
        self.assertEqual(len(turns), 3)
        for a in turns:
            tip = a.args[6]
            self.assertTrue(tip[0] < 0 or tip[1] > 10)
        # Reverse vertical cut: holder trails below the nominal top endpoint.
        cuts = [a for a in plan.actions if a.kind == 'linear_xy' and a.role == 'cut']
        self.assertIn(((10, 9.75), (10, -.25)), [a.args for a in cuts])

    def test_open_internal_ramp_gets_mandatory_finish_plus_optional_cut(self):
        base = self.plan(request(False, lead_in_mode='off', drag_ramp_length=2))
        extra = self.plan(request(False, lead_in_mode='off', drag_ramp_length=2, drag_extra_pass=True))
        self.assertEqual(sum(a.kind == 'rapid_xy' for a in base.actions), 4)
        self.assertEqual(sum(a.kind == 'rapid_xy' for a in extra.actions), 5)

    def test_swivels_never_plunge_below_current_shallow_cut(self):
        plan = self.plan(request(slice_depth=-.05, final_depth=-.1, drag_swivel_depth=-.2, drag_start_angle=90))
        depth = 0
        for a in plan.actions:
            if a.kind == 'linear_z':
                if a.role == 'drag_swivel':
                    self.assertGreaterEqual(a.args[0], depth - 1e-10)
                depth = a.args[0]

    def test_arc_tip_offset_and_reverse_are_exact_in_both_directions(self):
        for direction in (1, -1):
            geo = PathGeometry('arc', (5, 0), (0, direction*5), 5*pi/2,
                               center=(0, 0), radius=5, start_angle=0,
                               end_angle=direction*pi/2, sweep=direction*pi/2)
            req = request(False, drag_alternate=True, drag_ramp_length=2)
            plan = self.plan(replace(req, contour=(geo,)))
            arcs = [a for a in plan.actions if a.kind == 'arc' and a.role == 'cut']
            for a in arcs:
                self.assertAlmostEqual(a.args[5]**2, 25 + .25**2)

    def test_invalid_geometry_and_external_turn_settings_block_plan(self):
        for req in (request(slice_depth=0), request(drag_ramp_length=41),
                    request(lead_length=.1), request(False, drag_alternate=True, lead_out_mode='off')):
            result = ToolpathPlanner().plan(req)
            self.assertIsNone(result.plan)
            self.assertTrue(result.has_errors)

    def test_lead_modes_and_circle_winding_remain_continuous(self):
        for mode in ('off','straight','radius','startmove'):
            for direction in (-1,1):
                circle = PathGeometry('arc', (5,0), (5,0), 10*pi, center=(0,0),
                                      radius=5, start_angle=0, end_angle=direction*2*pi,
                                      sweep=direction*2*pi)
                req = request(lead_in_mode=mode, lead_out_mode=mode, lead_radius=2,
                              drag_ramp_length=2, drag_extra_pass=True)
                self.plan(replace(req, contour=(circle,)))

    def test_each_lead_choice_changes_preview_without_an_enable_switch(self):
        previews = []
        for mode in ('off', 'straight', 'radius', 'startmove'):
            plan = self.plan(request(lead_in_mode=mode, lead_out_mode=mode, lead_radius=2))
            incoming = [a for a in plan.actions if a.role == 'lead_in']
            outgoing = [a for a in plan.actions if a.role == 'lead_out']
            self.assertEqual(bool(incoming), mode != 'off')
            self.assertEqual(bool(outgoing), mode != 'off')
            previews.append(repr(plan_preview_segments(plan)))
        self.assertEqual(len(set(previews)), 4)

    def test_clockwise_output_restriction_preserves_direction_by_tessellation(self):
        req = request(drag_ramp_length=2)
        self.plan(replace(req, capabilities=replace(req.capabilities, counterclockwise_arcs_only=True)))

    def test_legacy_ramp_retains_line_tail_and_accumulates_depth(self):
        for points in (((0,0),(100,0)), ((0,0),(10,0),(100,0))):
            path = (PathGeometry('rapid', points[0], points[0]),) + tuple(line(a,b) for a,b in zip(points,points[1:]))
            req = replace(request(False, drag_ramp_length=20), prepared_path=path)
            plan = DragKnifeStrategy().plan(req)
            xy = [a for a in plan.actions if a.kind in ('linear_xy', 'linear_xyz')]
            self.assertEqual(xy[-1].args[1], (100,0))
            ramps = [a for a in xy if a.kind == 'linear_xyz']
            self.assertAlmostEqual(ramps[-1].args[3], -.3)
            self.assertTrue(all(a.args[3] <= a.args[2] for a in ramps))

    def test_xyz_g90_g91_and_preview_share_endpoints(self):
        from configobj import ConfigObj
        from validate import Validator
        from dxf2gcode.adapters.postprocessor.postprocessorconfig import POSTPRO_SPEC
        profile = ConfigObj(configspec=POSTPRO_SPEC, interpolation=False)
        self.assertIs(profile.validate(Validator(), copy=True), True)
        plan = self.plan(request(drag_ramp_length=2, drag_swivel_depth=-.01))
        for absolute in (True, False):
            profile['General']['abs_export'] = absolute
            from dxf2gcode.adapters.config.runtime_config import DictDotLookup
            dialect = ProfileDialect(DictDotLookup(profile), start_xy=(0,0), start_z=0)
            code = ToolpathGCodeExporter().export(plan, dialect)
            self.assertIn(' Z', code)
            xyz = [line for line in code.splitlines() if line.startswith('G1 X') and ' Z' in line]
            self.assertEqual(len(xyz), sum(a.kind == 'linear_xyz' for a in plan.actions))
            actual, position = [], [0.0, 0.0, 0.0]
            for row in code.splitlines():
                if not re.match(r'G[0123]\s', row):
                    continue
                words = re.findall(r'([XYZ])\s*(-?\d+(?:\.\d+)?)', row)
                for axis, value in words:
                    i = 'XYZ'.index(axis)
                    position[i] = float(value) if absolute else position[i] + float(value)
                actual.append(tuple(position))
            expected, position = [], [0.0, 0.0, 0.0]
            for a in plan.actions:
                if a.kind == 'rapid_xy':
                    position[:2] = a.args[0]
                elif a.kind in ('rapid_z','linear_z'):
                    position[2] = a.args[0]
                elif a.kind in ('linear_xy','linear_xyz'):
                    position[:2] = a.args[1]
                    if a.kind == 'linear_xyz':
                        position[2] = a.args[3]
                elif a.kind == 'arc':
                    position[:2] = a.args[2]
                else:
                    continue
                expected.append(tuple(position))
            self.assertEqual(len(actual), len(expected))
            for got, wanted in zip(actual, expected):
                for a,b in zip(got,wanted):
                    self.assertAlmostEqual(a,b,delta=.002)
            # Modal state follows the final planned retract even in G91.
            if not absolute:
                self.assertAlmostEqual(dialect.lz, plan.retract_depth)

    def test_every_square_edge_is_cut_at_final_depth_with_and_without_extra_pass(self):
        for extra in (False, True):
            for ramp in (0, 2, 15):
                req = request(lead_in_mode='off', drag_ramp_length=ramp,
                              drag_extra_pass=extra, drag_swivel_depth=-.01)
                plan = self.plan(req)
                final_segments, z = [], 0
                for a in plan.actions:
                    if a.kind in ('linear_z', 'rapid_z'):
                        z = a.args[0]
                    elif a.kind == 'linear_xyz':
                        z = a.args[3]
                    elif a.kind == 'linear_xy' and a.role in ('cut','extra_cut','ramp_finish','overcut'):
                        if abs(z-req.settings.final_depth) > 1e-8:
                            continue
                        start, end = a.args
                        angle = atan2(end[1]-start[1], end[0]-start[0])
                        # Independent inverse of the holder offset for straight cuts.
                        delta = (.25*cos(angle), .25*sin(angle))
                        final_segments.append(tuple(tuple(p[i]-delta[i] for i in (0,1)) for p in (start,end)))
                for geo in req.contour:
                    for i in range(100):
                        f = (i+.5)/100
                        point = tuple(a+(b-a)*f for a,b in zip(geo.start,geo.end))
                        def covers(segment):
                            a,b = segment
                            length = hypot(b[0]-a[0], b[1]-a[1])
                            distance = abs((b[0]-a[0])*(point[1]-a[1])-(b[1]-a[1])*(point[0]-a[0]))/length
                            dot = sum((point[j]-a[j])*(b[j]-a[j]) for j in (0,1))
                            return distance < 1e-8 and -1e-8 <= dot <= length*length+1e-8
                        self.assertTrue(any(covers(s) for s in final_segments), (extra,ramp,point))


from dxf2gcode_leadmove_golden_test import GoldenTestBase


class TestKnifeIntegration(GoldenTestBase):
    def test_tool_table_validates_offset_and_survives_machine_switches(self):
        import dxf2gcode.bootstrap.runtime_state as g
        from dxf2gcode.presentation.qt.qt_compat.QtCore import QTranslator
        from dxf2gcode.presentation.qt.qt_compat.QtWidgets import QApplication
        from dxf2gcode.presentation.qt.configwindow import ConfigWindow
        app = QApplication.instance()
        for language in ('en', 'de', 'fr', 'ru'):
            translator = QTranslator()
            if language != 'en':
                self.assertTrue(translator.load(str(Path(__file__).resolve().parents[1] / ('source/i18n/dxf2gcode_'+language+'.qm'))))
                app.installTranslator(translator)
            g.config.machine_type = 'drag_knife'
            definitions = g.config.makeConfigWidgets()
            form = ConfigWindow(definitions, g.config.var_dict, g.config.var_dict.configspec)
            table = definitions['Tool_Parameters']
            try:
                form.show()
                app.processEvents()
                for index in range(form.tab_window.count()):
                    if form.tab_window.widget(index).isAncestorOf(table):
                        form.tab_window.setCurrentIndex(index)
                app.processEvents()
                self.assertTrue(table.isVisible())
                before = table.getValue()
                self.assertTrue(table.validateValue()[0], table.validateValue()[1])
                diameter = table.keys.index('diameter')
                for mode in ('milling', 'drag_knife', 'milling', 'drag_knife'):
                    form.hide()
                    g.config.machine_type = mode
                    form.show()
                    app.processEvents()
                    self.assertEqual(table.getValue(), before)
                    self.assertTrue(table.validateValue()[0], table.validateValue()[1])
                    expected = before['1']['diameter'] / (2 if mode == 'drag_knife' else 1)
                    self.assertAlmostEqual(table.tablewidget.cellWidget(0, diameter).value(), expected,
                                           (mode, table.knife_offset, table.isVisible()))
                # A small positive radius is valid for the tip path even when
                # it is smaller than the offset, but cannot contain a cutter.
                radius = table.keys.index('lead_radius')
                table.tablewidget.cellWidget(0, radius).setValue(.1)
                self.assertTrue(table.validateValue()[0])
                form.hide()
                g.config.machine_type = 'milling'
                # Validation also follows the active machine before the
                # hidden tool page has received its next show event.
                self.assertFalse(table.validateValue()[0])
                form.show()
                app.processEvents()
                valid, errors = table.validateValue()
                self.assertFalse(valid)
                self.assertIn('lead_radius', errors)
                self.assertNotIn('tool_diameter', errors)
                # Real invalid values must still produce separate, localized
                # lines, including a correctly encoded German sharp s.
                form.hide()
                g.config.machine_type = 'drag_knife'
                form.show()
                app.processEvents()
                for row in (0, 1):
                    table.tablewidget.cellWidget(row, diameter).setValue(0)
                valid, errors = table.validateValue()
                self.assertFalse(valid)
                lines = [line for line in errors.splitlines() if line.strip()]
                self.assertEqual(len(lines), 2)
                self.assertTrue(all('tool_diameter' in line for line in lines))
                self.assertNotIn('\u00c3', errors)
                if language == 'de':
                    self.assertTrue(all('gr\u00f6\u00dfer als null' in line for line in lines))
            finally:
                form.close()
                if language != 'en':
                    app.removeTranslator(translator)

    def test_old_project_preserves_each_contour_swivel_depth_and_single_cut(self):
        from dxf2gcode_leadmove_project_test import _ParentStub, build_layer
        from dxf2gcode.presentation.qt.project_session import Project
        from dxf2gcode.adapters.project.legacy_d2g import decode_d2g, D2G_HEADER
        from dxf2gcode.adapters.toolpath.preparation import prepare_shape
        from dxf2gcode_stmove_gcode_test import make_plan_service, make_postpro
        import dxf2gcode.bootstrap.runtime_state as g
        g.config.machine_type = 'drag_knife'
        parent = _ParentStub([build_layer('A'), build_layer('B')])
        for layer, depth in zip(parent.layerContents, (-.04, -.08)):
            shape = layer.shapes[0]
            shape.parentLayer = layer
            shape.axis3_start_mill_depth = .1
            shape.axis3_mill_depth = -.3
            shape.axis3_slice_depth = depth
            layer.tool_diameter = .5
            shape.overcut_enabled = True
            layer.overcut_length = .4
        snapshot = decode_d2g(Project(parent).export(compleet=False)).values
        for version in (1.3, 1.4):
            old = dict(snapshot)
            if version == 1.3:
                old.pop('drag_knife')
            else:
                old['drag_knife'] = dict(snapshot['drag_knife'], planned_passes=False)
            content = D2G_HEADER % version + '\n' + '\n'.join('d2g.%s = %r' % item for item in old.items())
            Project(parent).load(content, compleet=False)
            for layer, depth in zip(parent.layerContents, (-.04, -.08)):
                shape = layer.shapes[0]
                self.assertEqual(shape.drag_swivel_depth, depth)
                self.assertAlmostEqual(shape.axis3_slice_depth, -.4)
                self.assertEqual(shape.get_lead_in_mode(), 'off')
                self.assertEqual(shape.get_lead_out_mode(), 'off')
                self.assertTrue(shape.get_overcut_enabled())
                prepare_shape(shape)
                result = make_plan_service().execute_result(shape, make_postpro())
                self.assertFalse(result.has_errors, result.diagnostics)
                self.assertFalse(any(a.role in ('lead_in', 'lead_out') for a in result.plan.actions))
                self.assertTrue(any(a.kind == 'linear_z' and a.role == 'drag_swivel'
                                    and abs(a.args[0] - depth) < 1e-9 for a in result.plan.actions))
                self.assertEqual(len([a for a in result.plan.actions if a.role == 'plunge']), 1)
            saved = Project(parent).export(compleet=False)
            Project(parent).load(saved, compleet=False)
            self.assertEqual([l.shapes[0].drag_swivel_depth for l in parent.layerContents], [-.04, -.08])
        shape = parent.layerContents[0].shapes[0]
        parent.layerContents[0].changeMeasuringUnits(1, 0)
        self.assertAlmostEqual(shape.drag_swivel_depth, -.04 / 25.4)

    def test_carry_state_preview_export_tool_change_and_literal_boundary(self):
        from dxf2gcode_leadmove_golden_test import build_shape
        from dxf2gcode.adapters.toolpath.preparation import prepare_shape
        from dxf2gcode.adapters.toolpath.planning import ShapePlanningInputs
        from dxf2gcode.adapters.toolpath.preview import preview_result
        from dxf2gcode_stmove_gcode_test import make_postpro, make_plan_service
        from dxf2gcode.domain.project.layercontent import Layers
        from dxf2gcode.domain.toolpath.movements import MovementPlan
        import dxf2gcode.bootstrap.runtime_state as g
        options = g.config.var_dict['Drag_Knife_Options']
        options['entry_mode'] = 'previous'
        g.config.update_config()
        first, one = build_shape(closed=False,cut_cor=40,machine_type='drag_knife',tool_diameter=.5,
                                 layer_settings=dict(lead_in_mode='straight',lead_length=3))
        second, two = build_shape(closed=True,cut_cor=40,machine_type='drag_knife',tool_diameter=.5,
                                  layer_settings=dict(lead_in_mode='straight',lead_length=3))
        one.shapes, two.shapes = [first], [second]
        one.exp_order_complete = two.exp_order_complete = [0]
        layers = Layers([one,two])
        pp = make_postpro()
        pp.chg_tool(1,1000)
        initial = make_plan_service().execute_result(first,pp)
        self.assertFalse(initial.has_errors)
        ToolpathGCodeExporter().export(initial.plan, pp)
        self.assertAlmostEqual(pp.knife_heading, pi/2)
        carried = make_plan_service().execute_result(second,pp)
        self.assertFalse(carried.has_errors)
        preview = preview_result(second,pp,layers)
        self.assertEqual(preview.plan, carried.plan)
        factory = ShapePlanningInputs(lambda: g.config)
        self.assertAlmostEqual(factory.request(second,pp).initial_state.knife_heading, pi/2)
        pp.chg_tool(2,1000)
        self.assertIsNone(factory.request(second,pp).initial_state.knife_heading)
        ToolpathGCodeExporter().export(initial.plan,pp)
        literal = MovementPlan(ToolpathRequest(9,MachiningSettings(),MachineCapabilities(),literal='M0\n'))
        literal.add('literal','M0\n')
        ToolpathGCodeExporter().export(literal.finish(),pp)
        self.assertIsNone(pp.knife_heading)

    def test_forum_fixture_final_swivel_lifts_before_arc_and_exports(self):
        from dxf2gcode.adapters.dxf.parser import ReadDXF
        from dxf2gcode.application.drawings import BuildDrawingModel
        from dxf2gcode.domain.project.shape import Shape
        from dxf2gcode.adapters.toolpath.preparation import prepare_shape
        from dxf2gcode_stmove_gcode_test import make_plan_service, make_postpro
        import dxf2gcode.bootstrap.runtime_state as g
        path = Path(__file__).resolve().parents[1] / 'dxf/drag_knive_test.dxf'
        drawing = ReadDXF(filename=str(path))
        g.config.machine_type = 'drag_knife'
        model = BuildDrawingModel(drawing, g.config, Shape, False).execute()
        self.assertEqual(len(model.shapes), 5)
        for mode in ('off', 'straight'):
            g.config.update_config()
            for shape in model.shapes:
                shape.parentLayer.tool_diameter = .5
                shape.parentLayer.lead_in_mode = mode
                shape.parentLayer.lead_length = 3
                shape.axis3_mill_depth = -.3
                shape.axis3_slice_depth = -.1
                shape.stmove = prepare_shape(shape)
                pp = make_postpro()
                result = make_plan_service().execute_result(shape, pp)
                self.assertFalse(result.has_errors, result.diagnostics)
                self.assertTrue(ToolpathGCodeExporter().export(result.plan, pp))
                arcs = [(i,a) for i,a in enumerate(result.plan.actions) if a.kind == 'arc' and a.role == 'drag_swivel']
                self.assertTrue(arcs)
                for index, arc in arcs:
                    before = result.plan.actions[:index]
                    z = next(a.args[0] for a in reversed(before) if a.kind == 'linear_z')
                    self.assertGreaterEqual(z, -.1-1e-9)
                    self.assertEqual(before[-1].kind, 'feed')

    def test_project_roundtrip_restores_knife_options_including_units(self):
        from dxf2gcode_leadmove_project_test import _ParentStub, build_layer
        from dxf2gcode.presentation.qt.project_session import Project
        from dxf2gcode.adapters.project.legacy_d2g import decode_d2g
        import dxf2gcode.bootstrap.runtime_state as g
        parent = _ParentStub([build_layer()])
        parent.load = lambda *args: True
        parent.connectToolbarToConfig = lambda *args: None
        g.config.machine_type = 'drag_knife'
        g.config.var_dict['Drag_Knife_Options'].update(dict(extra_pass=True,
            alternate=True, swivel_depth=-.02, ramp_in_length=2.5, lead_out_length=3,
            entry_mode='unknown', alignment_length=6.35, return_to_start=True))
        g.config.update_config()
        content = Project(parent).export(compleet=False)
        payload = decode_d2g(content).values['drag_knife']
        self.assertNotIn('planned_passes', payload)
        g.config.var_dict['Drag_Knife_Options'].update(dict(extra_pass=False))
        Project(parent).load(content)
        self.assertNotIn('planned_passes', g.config.var_dict['Drag_Knife_Options'])
        self.assertTrue(g.config.vars.Drag_Knife_Options.extra_pass)
        self.assertEqual(g.config.vars.Drag_Knife_Options.entry_mode, 'unknown')
        self.assertTrue(g.config.vars.Drag_Knife_Options.return_to_start)
        self.assertAlmostEqual(g.config.vars.Drag_Knife_Options.alignment_length, 6.35)
        self.assertAlmostEqual(g.config.vars.Drag_Knife_Options.ramp_in_length, 2.5)
        g.config.var_dict['General']['tool_units'] = 'in'
        g.config.update_config()
        Project(parent).load(content)
        self.assertAlmostEqual(g.config.var_dict['Drag_Knife_Options']['ramp_in_length'], 2.5/25.4)
        self.assertAlmostEqual(g.config.var_dict['Drag_Knife_Options']['alignment_length'], .25)
        self.assertAlmostEqual(g.config.vars.Drag_Knife_Options.ramp_in_length, 2.5)
        legacy = '\n'.join(l for l in content.splitlines() if not l.startswith('d2g.drag_knife'))
        Project(parent).load(legacy)
        self.assertFalse(g.config.vars.Drag_Knife_Options.extra_pass)
        old = dict(payload)
        old['planned_passes'] = True
        for key in ('entry_mode','alignment_length','return_to_start'):
            old.pop(key)
        old_content = re.sub(r'^d2g.drag_knife = .*$', lambda match: 'd2g.drag_knife = '+repr(old), content.replace('V1.5', 'V1.4'), flags=re.M)
        self.assertEqual(decode_d2g(old_content).values['drag_knife']['entry_mode'], 'fixed')
        with self.assertRaises(ValueError):
            decode_d2g(old_content.replace("'planned_passes': True", "'planned_passes': 'yes'"))

    def test_knife_lengths_convert_with_configuration_and_drawing_units(self):
        import dxf2gcode.bootstrap.runtime_state as g
        options = g.config.var_dict['Drag_Knife_Options']
        options['ramp_in_length'], options['swivel_depth'], options['lead_out_length'] = 2.54, -.254, 5.08
        g.config.update_config()
        g.config.var_dict['General']['tool_units'] = 'in'
        g.config.update_config()
        self.assertAlmostEqual(options['ramp_in_length'], .1)
        self.assertAlmostEqual(g.config.vars.Drag_Knife_Options.ramp_in_length, 2.54)
        g.config.metric = 0
        g.config.update_tool_values()
        self.assertAlmostEqual(g.config.vars.Drag_Knife_Options.swivel_depth, -.01)
        self.assertAlmostEqual(g.config.vars.Drag_Knife_Options.lead_out_length, .2)

    def test_offset_editor_roundtrip_and_new_translations(self):
        import dxf2gcode.bootstrap.runtime_state as g
        from dxf2gcode.presentation.qt.qt_compat.QtCore import QTranslator
        from dxf2gcode.presentation.qt.qt_compat.QtWidgets import QApplication
        from dxf2gcode.presentation.qt.configwindow import ConfigWindow
        for language in ('de','fr','ru'):
            translator = QTranslator()
            self.assertTrue(translator.load(str(Path(__file__).resolve().parents[1] / ('source/i18n/dxf2gcode_'+language+'.qm'))))
            app = QApplication.instance()
            app.installTranslator(translator)
            g.config.machine_type = 'drag_knife'
            definitions = g.config.makeConfigWidgets()
            form = ConfigWindow(definitions, g.config.var_dict, g.config.var_dict.configspec)
            try:
                table = definitions['Tool_Parameters']
                column = table.keys.index('diameter')
                stored = float(g.config.var_dict['Tool_Parameters']['1']['diameter'])
                self.assertAlmostEqual(table.tablewidget.cellWidget(0,column).value(), stored/2)
                self.assertAlmostEqual(table.getValue()['1']['diameter'], stored)
                self.assertEqual(table.tablewidget.horizontalHeaderItem(column).text(), translator.translate('CfgTableToolParameters','Knife offset'))
                table.tablewidget.cellWidget(0,column).setValue(.25)
                self.assertAlmostEqual(table.getValue()['1']['diameter'], .5)
                self.assertNotIn('planned_passes', definitions['Drag_Knife_Options'])
                self.assertTrue(translator.translate('TreeHandler', 'Swivel contact Z'))
                self.assertNotEqual(translator.translate('TreeHandler', 'Swivel contact Z'), 'Swivel contact Z')
                modes = definitions['Drag_Knife_Options']['entry_mode']
                modes.setValue('unknown')
                self.assertEqual(modes.getValue(),'unknown')
                form.resize(900,600)
                form.show()
                app.processEvents()
                for index in range(form.tab_window.count()):
                    page = form.tab_window.widget(index)
                    if page.isAncestorOf(modes):
                        form.tab_window.setCurrentIndex(index)
                        app.processEvents()
                        self.assertGreater(page.verticalScrollBar().maximum(),0)
                self.assertLessEqual(form.height(),600)
            finally:
                form.close()
                app.removeTranslator(translator)


if __name__ == '__main__':
    unittest.main()
