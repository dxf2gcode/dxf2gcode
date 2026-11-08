"""D41 nominal tab boundaries, normal transfer and emitted movements."""
from dataclasses import replace
from math import cos, sin, pi, hypot
import unittest

from dxf2gcode.domain.toolpath.inputs import PathGeometry, ToolpathRequest, MachiningSettings, MachineCapabilities
from dxf2gcode.domain.toolpath.tabs import TabRegion, map_tabs
from dxf2gcode.domain.toolpath.planner import ToolpathPlanner


def line(start, end):
    return PathGeometry('line', start, end, hypot(end[0]-start[0], end[1]-start[1]))


def arc(center, radius, first, sweep):
    return PathGeometry('arc', (center[0]+radius*cos(first), center[1]+radius*sin(first)),
        (center[0]+radius*cos(first+sweep), center[1]+radius*sin(first+sweep)),
        abs(radius*sweep), center=center, radius=radius, start_angle=first,
        end_angle=first+sweep, sweep=sweep)


def region(x0, x1, y0, y1, identity='region'):
    return TabRegion(((x0, y0), (x1, y0), (x1, y1), (x0, y1)), -1., 200., 100., identity)


def planned(contour, path, split, skipped=0, closed=False, **settings):
    request = ToolpathRequest(7,
        MachiningSettings(final_depth=-3, slice_depth=-3, feed_xy=500, **settings),
        MachineCapabilities(), contour=contour,
        prepared_path=(PathGeometry('rapid', path[0].start, path[0].start),)+path,
        split_contour=split, closed=closed, compensation=41,
        has_break_layers=True, skipped_tabs=skipped)
    return ToolpathPlanner().plan(request)


class TestNominalTabs(unittest.TestCase):
    def test_region_only_reaches_nominal_line_for_both_offset_sides_and_radii(self):
        contour = (line((0, 0), (10, 0)),)
        for offset in (-3, -1, 0, 1, 3):
            with self.subTest(offset=offset):
                path = (line((0, offset), (10, offset)),)
                split, skipped = map_tabs(contour, path, (region(4, 6, -.1, .1),), abs(offset), False)
                tabs = [g for g in split if g.kind == 'break']
                self.assertFalse(skipped)
                self.assertEqual(len(tabs), 1)
                for actual, expected in zip(tabs[0].start+tabs[0].end, (4, offset, 6, offset)):
                    self.assertAlmostEqual(actual, expected)

    def test_oblique_region_uses_nominal_contacts_not_offset_intersections(self):
        contour = (line((0, 0), (10, 0)),)
        path = (line((0, 2), (10, 2)),)
        oblique = TabRegion(((3, -2), (5, -2), (9, 2), (7, 2)), -1, 200, 100)
        split, skipped = map_tabs(contour, path, (oblique,), 2, False)
        self.assertFalse(skipped)
        self.assertEqual([(g.start, g.end) for g in split if g.kind == 'break'], [((5., 2.), (7., 2.))])

    def test_arc_boundaries_keep_contact_angles_and_arc_movements(self):
        contour = (arc((0, 0), 10, 0, pi/2),)
        for radius in (8, 10, 12):
            path = (arc((0, 0), radius, 0, pi/2),)
            split, skipped = map_tabs(contour, path, (region(4, 6, 7, 10),), abs(radius-10), False)
            tab = next(g for g in split if g.kind == 'break')
            self.assertFalse(skipped)
            self.assertEqual(tab.tab_geometry.kind, 'arc')
            self.assertAlmostEqual(tab.start[0], 6*radius/10)
            self.assertAlmostEqual(tab.end[0], 4*radius/10)
            result = planned(contour, path, split)
            self.assertFalse(result.has_errors)
            self.assertTrue(any(a.kind == 'arc' and a.modifier_id == 'region' for a in result.plan.actions))

    def test_corner_join_stays_raised_without_intermediate_plunge(self):
        contour = (line((0, 0), (10, 0)), line((10, 0), (10, 10)))
        path = (line((0, -2), (10, -2)), arc((10, 0), 2, -pi/2, pi/2), line((12, 0), (12, 10)))
        split, skipped = map_tabs(contour, path, (region(8, 11, -1, 3),), 2, False)
        self.assertFalse(skipped)
        self.assertEqual([g.tab_geometry.kind for g in split if g.kind == 'break'], ['line', 'arc', 'line'])
        actions = planned(contour, path, split).plan.actions
        indexes = [i for i, action in enumerate(actions) if action.modifier_id == 'region']
        self.assertEqual(len(indexes), 3)
        self.assertFalse(any(a.kind == 'linear_z' for a in actions[indexes[0]:indexes[-1]+1]))

    def test_missing_boundary_skips_whole_tab_and_warns_without_blocking_plan(self):
        contour = (line((0, 0), (10, 0)),)
        path = (line((0, 2), (5, 2)),)
        split, skipped = map_tabs(contour, path, (region(4, 6, -.1, .1),), 2, False)
        self.assertEqual(len(skipped), 1)
        self.assertFalse(any(g.kind == 'break' for g in split))
        result = planned(contour, path, split, len(skipped))
        self.assertIsNotNone(result.plan)
        self.assertFalse(result.has_errors)
        self.assertEqual([(d.code, d.severity) for d in result.diagnostics], [('tabs.unmapped', 'warning')])

    def test_boundary_exactly_at_round_join_is_ambiguous_and_skipped(self):
        contour = (line((0, 0), (10, 0)), line((10, 0), (10, 10)))
        path = (line((0, -2), (10, -2)), arc((10, 0), 2, -pi/2, pi/2), line((12, 0), (12, 10)))
        split, skipped = map_tabs(contour, path, (region(8, 11, -1, 0),), 2, False)
        self.assertEqual(len(skipped), 1)
        self.assertFalse(any(g.kind == 'break' for g in split))

    def test_disconnected_offset_parts_do_not_receive_a_partial_tab(self):
        contour = (line((0, 0), (5, 0)), line((5, 0), (10, 0)))
        path = (line((0, 2), (4.5, 2)),
                PathGeometry('pocket', (4.5, 2), (5.5, 2)), line((5.5, 2), (10, 2)))
        split, skipped = map_tabs(contour, path, (region(4, 6, -.1, .1),), 2, False)
        self.assertEqual(len(skipped), 1)
        self.assertFalse(any(g.kind == 'break' for g in split))

    def test_two_distinct_counterparts_are_not_chosen_arbitrarily(self):
        contour = (line((0, 0), (10, 0)),)
        path = (line((0, 2), (10, 2)), line((0, -2), (10, -2)))
        split, skipped = map_tabs(contour, path, (region(4, 6, -.1, .1),), 2, False)
        self.assertEqual(len(skipped), 1)
        self.assertFalse(any(g.kind == 'break' for g in split))

    def test_missing_tab_does_not_remove_another_tab_from_the_same_region(self):
        contour = (line((0, 0), (10, 0)), line((10, 0), (10, 10)), line((10, 10), (0, 10)))
        path = (line((0, -2), (5, -2)), line((10, 12), (0, 12)))
        split, skipped = map_tabs(contour, path, (region(4, 6, -1, 11),), 2, False)
        self.assertEqual(len(skipped), 1)
        tabs = [g for g in split if g.kind == 'break']
        self.assertEqual(len(tabs), 1)
        self.assertAlmostEqual(tabs[0].start[1], 12)

    def test_arc_tab_survives_legacy_exit_adapter_and_reversal(self):
        from copy import deepcopy
        from dxf2gcode.adapters.toolpath.planning import _existing_geometry, snapshot_geometry
        contour = (arc((0, 0), 10, 0, pi/2),)
        split, _ = map_tabs(contour, contour, (region(4, 6, 7, 10),), 0, False)
        tab = next(g for g in split if g.kind == 'break')
        legacy = deepcopy(_existing_geometry(tab))
        legacy.reverse()
        legacy.make_abs_geo()
        restored = snapshot_geometry(legacy).resolved
        self.assertEqual(restored.kind, 'break')
        self.assertEqual(restored.tab_geometry, tab.tab_geometry.reversed())
        self.assertEqual(restored.modifier_id, tab.modifier_id)
        self.assertAlmostEqual(restored.length, tab.length)

    def test_merged_collinear_sources_and_reverse_direction(self):
        contour = (line((0, 0), (5, 0)), line((5, 0), (10, 0)))
        path = (line((10, 2), (0, 2)),)
        split, skipped = map_tabs(contour, path, (region(4, 6, -.1, .1),), 2, False)
        self.assertFalse(skipped)
        tabs = [g for g in split if g.kind == 'break']
        self.assertEqual((tabs[0].start, tabs[-1].end), ((6., 2.), (4., 2.)))
        reversed_tab = tabs[0].reversed()
        self.assertEqual(reversed_tab.tab_geometry.start, tabs[0].tab_geometry.end)

    def test_tangent_contact_creates_no_tab(self):
        contour = (line((0, 0), (10, 0)),)
        triangle = TabRegion(((5, 0), (6, 1), (4, 1)), -1, 200, 100)
        split, skipped = map_tabs(contour, contour, (triangle,), 0, False)
        self.assertEqual(split, contour)
        self.assertFalse(skipped)

    def test_closed_seam_is_not_plunged_through_on_deep_passes(self):
        contour = (line((0, 0), (10, 0)), line((10, 0), (10, 10)),
                   line((10, 10), (0, 10)), line((0, 10), (0, 0)))
        split, skipped = map_tabs(contour, contour, (region(-1, 2, -1, 2),), 0, True)
        self.assertFalse(skipped)
        result = planned(contour, contour, split, closed=True)
        plunges = [a.args[0] for a in result.plan.actions if a.role == 'plunge']
        self.assertEqual(plunges, [-1.])


from dxf2gcode_leadmove_golden_test import GoldenTestBase


class TestNominalTabIntegration(GoldenTestBase):
    def case(self, machine=False, compensation=41, radius=2, extra=0, curved=False):
        import dxf2gcode.bootstrap.runtime_state as g
        from dxf2gcode_stmove_gcode_test import make_shape, build_stmove, make_postpro
        from dxf2gcode.domain.project.shape import Shape, Geos
        from dxf2gcode.domain.project.layercontent import LayerContent, Layers
        from dxf2gcode.domain.geometry.linegeo import LineGeo
        from dxf2gcode.domain.geometry.arcgeo import ArcGeo
        from dxf2gcode.domain.geometry.point import Point
        from dxf2gcode.adapters.postprocessor.breaks import Breaks
        from dxf2gcode.adapters.toolpath.planning import ShapePlanningInputs
        g.config.vars.Cutter_Compensation['done_by_machine'] = machine
        geos = ([ArcGeo(Ps=Point(10, 0), Pe=Point(0, 10), O=Point(0, 0), r=10, direction=1)]
                if curved else [LineGeo(Point(0, 0), Point(10, 0))])
        shape = make_shape(geos, closed=False,
                           cut_cor=compensation, tool_diameter=2*radius)
        shape.axis3_mill_depth, shape.axis3_slice_depth = -3, -3
        shape.milling_offset = extra
        shape.parentLayer.lead_in_mode = 'straight'
        shape.parentLayer.lead_length = 1
        build_stmove(shape)
        vertices = (region(4, 6, 7, 10) if curved else region(4, 6, -.1, .1)).vertices
        tab = Shape(99, True, geos=Geos(LineGeo(Point(*a), Point(*b))
                    for a, b in zip(vertices, vertices[1:]+vertices[:1])), config=g.config)
        tab.axis3_mill_depth, tab.f_g1_plane, tab.f_g1_depth = -1, 200, 100
        tab.operation_id = 'region'
        layer = LayerContent(1, 'BREAKS:', [tab], config=g.config)
        tab.parentLayer = layer
        layers = Layers([shape.parentLayer, layer])
        pp = make_postpro()
        pp.breaks = Breaks(layers)
        request = ShapePlanningInputs(lambda: g.config).request(shape, pp)
        return shape, pp, layers, request

    def test_real_offset_and_machine_compensation_share_nominal_boundaries(self):
        from dxf2gcode.adapters.toolpath.preview import preview_result
        from dxf2gcode_stmove_gcode_test import make_plan_service
        from toolpath_test_support import serialize_gcode
        for machine in (False, True):
            for compensation in (40, 41, 42):
                for radius in (1, 2):
                    with self.subTest(machine=machine, compensation=compensation, radius=radius):
                        shape, pp, layers, request = self.case(machine, compensation, radius)
                        tabs = [geo for geo in request.split_contour if geo.kind == 'break']
                        self.assertEqual(len(tabs), 1)
                        self.assertAlmostEqual(tabs[0].start[0], 4)
                        self.assertAlmostEqual(tabs[0].end[0], 6)
                        self.assertAlmostEqual(abs(tabs[0].start[1]), 0 if machine or compensation == 40 else radius)
                        result = make_plan_service().execute_result(shape, pp)
                        self.assertFalse(result.has_errors)
                        preview = preview_result(shape, pp, layers)
                        self.assertEqual(preview.plan, result.plan)
                        code = serialize_gcode(shape, pp)
                        self.assertRegex(code, r'Z\s+-1\.000')
                        self.assertRegex(code, r'X\s+6\.000')

    def test_finishing_allowance_does_not_move_nominal_tab_boundaries(self):
        _, _, _, request = self.case(extra=.5)
        tab = next(g for g in request.split_contour if g.kind == 'break')
        self.assertAlmostEqual(tab.start[0], 4)
        self.assertAlmostEqual(tab.end[0], 6)
        self.assertAlmostEqual(abs(tab.start[1]), 2.5)

    def test_real_compensated_arc_preview_and_export_keep_the_tab_arc(self):
        from dxf2gcode_stmove_gcode_test import make_plan_service
        from toolpath_test_support import serialize_gcode
        for machine in (False, True):
            for compensation in (41, 42):
                with self.subTest(machine=machine, compensation=compensation):
                    shape, pp, _, request = self.case(machine, compensation, curved=True)
                    tabs = [g for g in request.split_contour if g.kind == 'break']
                    self.assertEqual(len(tabs), 1)
                    contacts = sorted(p[0]/hypot(*p) for p in (tabs[0].start, tabs[0].end))
                    self.assertAlmostEqual(contacts[0], .4)
                    self.assertAlmostEqual(contacts[1], .6)
                    result = make_plan_service().execute_result(shape, pp)
                    self.assertFalse(result.has_errors)
                    self.assertTrue(any(a.kind == 'arc' and a.modifier_id == 'region' for a in result.plan.actions))
                    code = serialize_gcode(shape, pp)
                    self.assertRegex(code, r'G[23] X\s+')
                    self.assertRegex(code, r'Z\s+-1\.000')

    def test_omitted_tab_warning_has_translations_and_compiled_catalogs(self):
        from pathlib import Path
        import xml.etree.ElementTree as ET
        from dxf2gcode.domain.toolpath.diagnostics import TAB_UNMAPPED
        from dxf2gcode.presentation.qt.qt_compat import QtCore
        root = Path(__file__).resolve().parents[1] / 'source/i18n'
        for language in ('de', 'fr', 'ru'):
            context = next(c for c in ET.parse(root / ('dxf2gcode_'+language+'.ts')).findall('context')
                           if c.findtext('name') == 'Shape')
            message = next(m for m in context.findall('message') if m.findtext('source') == TAB_UNMAPPED)
            translation = message.findtext('translation')
            self.assertTrue(translation)
            self.assertEqual(translation.count('%i'), 2)
            translator = QtCore.QTranslator()
            self.assertTrue(translator.load(str(root / ('dxf2gcode_'+language+'.qm'))))
            self.assertEqual(translator.translate('Shape', TAB_UNMAPPED), translation)
