"""Vertical contracts: project input -> native plan -> preview and G-Code."""

import os
import re
import sys
from dataclasses import asdict
from unittest.mock import patch

_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [_TEST_DIR, os.path.join(os.path.dirname(_TEST_DIR), "source")]

from dxf2gcode_leadmove_golden_test import GoldenTestBase, build_shape
from dxf2gcode_stmove_gcode_test import make_postpro, make_plan_service
import dxf2gcode.bootstrap.runtime_state as g
from dxf2gcode.adapters.toolpath.planning import ShapePlanningInputs
from dxf2gcode.adapters.toolpath.gcode_exporter import ToolpathGCodeExporter
from dxf2gcode.adapters.postprocessor.breaks import Breaks
from dxf2gcode.adapters.postprocessor.dialect import ProfileDialect
from dxf2gcode.application.toolpath.projections import plan_xy_segments, plan_xyz_segments
from dxf2gcode.domain.geometry.arcgeo import ArcGeo
from dxf2gcode.domain.geometry.holegeo import HoleGeo
from dxf2gcode.domain.geometry.point import Point
from dxf2gcode.domain.project.layercontent import Layers
from dxf2gcode.domain.project.shape import Geos
from dxf2gcode.adapters.toolpath.preparation import prepare_shape


class TestToolpathSlices(GoldenTestBase):
    def test_entry_circle_renders_without_a_lead_and_scales_with_the_scene(self):
        from dxf2gcode.presentation.qt.canvas2d import MyGraphicsScene, StMoveGUI
        from dxf2gcode.presentation.qt.qt_compat.QtCore import QRectF
        from dxf2gcode.presentation.qt.qt_compat.QtGui import QImage, QPainter
        shape, _ = build_shape(cut_cor=40, layer_settings=dict(lead_in_mode='off', lead_out_mode='off'))
        overlay = StMoveGUI(shape)
        scene = MyGraphicsScene()
        scene.addItem(overlay)
        center = overlay._lead_in_dive_point()
        radius = overlay._tool_radius()
        source = QRectF(center.x-1.2*radius, -center.y-1.2*radius, 2.4*radius, 2.4*radius)
        g.config.vars.General['show_tool_circle'] = True
        for size in (120, 240):
            image = QImage(size, size, QImage.Format.Format_ARGB32)
            image.fill(0xffffffff)
            painter = QPainter(image)
            try:
                scene.render(painter, QRectF(0, 0, size, size), source)
            finally:
                painter.end()
            xs = [x for x in range(size) for y in range(size)
                  if image.pixelColor(x, y) == overlay.PEN_LEAD_IN_TOOL.color()]
            self.assertTrue(xs)
            self.assertAlmostEqual(max(xs)-min(xs), size/1.2, delta=4)
        g.config.vars.General['show_tool_circle'] = False
        scene.updateToolCircleVisibility()
        image.fill(0xffffffff)
        painter = QPainter(image)
        try:
            scene.render(painter, QRectF(0, 0, size, size), source)
        finally:
            painter.end()
        self.assertFalse(any(image.pixelColor(x, y) == overlay.PEN_LEAD_IN_TOOL.color()
                             for x in range(size) for y in range(size)))

    def test_entry_circle_uses_plan_with_and_without_leads_and_never_changes_export(self):
        from unittest.mock import Mock
        from dxf2gcode.presentation.qt.canvas2d import StMoveGUI
        from dxf2gcode.domain.project.tool_settings import ToolSettings
        from dxf2gcode.domain.project.entitycontent import EntityContent
        for machine in (False, True):
            for side in (40, 41, 42):
                for lead in ('off', 'startmove'):
                    with self.subTest(machine=machine, side=side, lead=lead):
                        shape, _ = build_shape(cut_cor=side, done_by_machine=machine,
                            layer_settings=dict(lead_in_mode=lead, lead_out_mode='off'))
                        shape.tool_override = ToolSettings(1, 6, 1000, 1, 20, 3, 0)
                        root = EntityContent(nr=0, name='Root', parent=None,
                            p0=Point(7, 11), pb=Point(), sca=[1.5]*3, rot=.3)
                        shape.parentEntity = root
                        for geo in shape.geos:
                            geo.make_abs_geo(root)
                        shape.stmove = prepare_shape(shape)
                        if machine and side != 40 and lead == 'off':
                            result = make_plan_service().execute_result(shape, make_postpro())
                            self.assertTrue(result.has_errors)
                            self.assertIsNone(StMoveGUI(shape)._lead_in_dive_point())
                            continue
                        plan, code = self.plan_and_export(shape)
                        g.config.vars.General['show_tool_circle'] = True
                        gui = StMoveGUI(shape, plan=plan)
                        painter = Mock()
                        gui.paint_details(painter)
                        painter.drawEllipse.assert_called_once()
                        center, rx, ry = painter.drawEllipse.call_args.args
                        self.assertEqual((center.x(), -center.y()), plan.approach_xy)
                        self.assertEqual((rx, ry), (3, 3))
                        br = gui.boundingRect()
                        self.assertLessEqual(br.left(), center.x()-rx+1e-9)
                        self.assertGreaterEqual(br.right(), center.x()+rx-1e-9)
                        self.assertLessEqual(br.top(), center.y()-ry+1e-9)
                        self.assertGreaterEqual(br.bottom(), center.y()+ry-1e-9)
                        g.config.vars.General['show_tool_circle'] = False
                        painter = Mock()
                        gui.paint_details(painter)
                        painter.drawEllipse.assert_not_called()
                        after, after_code = self.plan_and_export(shape)
                        self.assertEqual(plan, after)
                        self.assertEqual(code, after_code)

    def test_knife_overcut_uses_exit_overlay_even_without_a_lead_out(self):
        from dxf2gcode.presentation.qt.canvas2d import StMoveGUI
        shape, _ = build_shape(cut_cor=40, machine_type='drag_knife', layer_settings=dict(
            lead_in_mode='off', lead_out_mode='off', overcut_enabled=True, overcut_length=5))
        plan, _ = self.plan_and_export(shape)
        self.assertTrue(any(a.role == 'overcut' for a in plan.actions))
        overlay = StMoveGUI(shape, plan=plan)
        self.assertFalse(overlay._exit_path.isEmpty())
        self.assertTrue(shape.stmove.exit_geos)

    def test_leads_render_above_other_contours_and_follow_visibility(self):
        from dxf2gcode.presentation.qt.canvas2d import MyGraphicsScene, StMoveGUI
        from dxf2gcode.presentation.qt.qt_compat.QtGui import QImage, QPainter, QPainterPath
        from dxf2gcode.presentation.qt.qt_compat.QtCore import QRectF
        shape, _ = build_shape(cut_cor=40, layer_settings=dict(lead_in_mode='off', lead_out_mode='off'))
        for field, pen in (('_lead_in_path', StMoveGUI.PEN_LEAD_IN_LINE),
                           ('_exit_path', StMoveGUI.PEN_EXIT_LINE)):
            for reversed_order in (False, True):
                scene = MyGraphicsScene()
                detail, contour = StMoveGUI(shape), StMoveGUI(shape)
                for item in (detail, contour):
                    item._comp_path = QPainterPath()
                    item._lead_in_path = QPainterPath()
                    item._exit_path = QPainterPath()
                    item._rapid_paths = []
                path = QPainterPath()
                path.moveTo(10, 20)
                path.lineTo(90, 20)
                setattr(detail, field, path)
                contour._comp_path = path
                for item in ((contour, detail) if reversed_order else (detail, contour)):
                    scene.addItem(item)
                def colors():
                    image = QImage(100, 40, QImage.Format.Format_ARGB32)
                    image.fill(0xffffffff)
                    painter = QPainter(image)
                    try:
                        scene.render(painter, QRectF(0, 0, 100, 40), QRectF(0, 0, 100, 40))
                    finally:
                        painter.end()
                    return [image.pixelColor(x, 20).getRgb() for x in range(15, 85)]
                self.assertIn(pen.color().getRgb(), colors())
                detail.hide()
                self.assertNotIn(pen.color().getRgb(), colors())
                self.assertIn(StMoveGUI.PEN_COMP_LINE.color().getRgb(), colors())

    def plan_and_export(self, shape, pp=None):
        pp = pp or make_postpro()
        inputs = ShapePlanningInputs(lambda: g.config)
        before = asdict(inputs.request(shape, pp))
        service = make_plan_service()
        result = service.execute_result(shape, pp)
        self.assertFalse(result.has_errors, result.diagnostics)
        self.assertIsNotNone(result.plan)
        self.assertEqual(result, service.execute_result(shape, pp))
        self.assertEqual(before, asdict(inputs.request(shape, pp)))
        self.assertEqual(result.plan, pp.plan_shape_toolpath(shape))
        dialect = ProfileDialect(
            pp.vars, start_xy=(pp.lPe.x, pp.lPe.y), start_z=pp.lz,
            diameter_factor=2 if g.config.machine_type == "lathe" else 1)
        code = ToolpathGCodeExporter().export(result.plan, pp)
        self.assertEqual(code, ToolpathGCodeExporter().export(result.plan, dialect))
        pp.initialize_export_vars()
        self.assertEqual(code, pp.write_shape_gcode(shape))
        pp.initialize_export_vars()
        self.assertEqual(before, asdict(inputs.request(shape, pp)))
        # Compare real formatted endpoints with the native actions, including
        # the historical lathe diameter factor. No exporter mock is involved.
        endpoints = [tuple(map(float, match)) for match in re.findall(
            r"G[123] X\s*([-\d.]+) Y\s*([-\d.]+)", code)]
        planned = [action.args[1] if action.kind in ("linear_xy", "linear_xyz") else action.args[2]
                   for action in result.plan.actions
                   if action.kind in ("linear_xy", "linear_xyz", "arc")]
        factor = 2 if g.config.machine_type == "lathe" else 1
        self.assertEqual(endpoints, [(round(x, 3), round(y * factor, 3))
                                     for x, y in planned])
        return result.plan, code

    def assert_unique_xy(self, plan):
        segments = plan_xy_segments(plan)
        keys = [tuple(sorted(tuple(round(v, 9) for v in point)
                             for point in segment)) for segment in segments]
        self.assertEqual(len(keys), len(set(keys)))

    def test_software_compensation_closed_and_alternating_open_passes(self):
        for closed in (True, False):
            with self.subTest(closed=closed):
                shape, _ = build_shape(closed=closed, done_by_machine=False)
                plan, code = self.plan_and_export(shape)
                self.check_golden("software_closed" if closed else "software_open", code)
                self.assertEqual([a.args[0] for a in plan.actions
                                  if a.role == "plunge"], [-2, -4, -5])
                self.assertFalse(any(a.kind.startswith("compensation_")
                                     for a in plan.actions))
                self.assert_unique_xy(plan)
                self.assertEqual({p[2] for segment in plan_xyz_segments(plan)
                                  for p in segment}, {0, -2, -4, -5})
                if not closed:
                    # Ignore lead actions: the next pass starts at the last
                    # pass's end and returns to its start, without a rapid.
                    cuts = [p for p in plan.passes if p.depth < 0]
                    self.assertEqual(cuts[1].moves[-1].end_xy,
                                     cuts[2].moves[0].start_xy)

    def test_machine_compensation_sides_and_depth_cancellation(self):
        for side in (41, 42):
            for closed in (True, False):
                for cancel in (False, True):
                    with self.subTest(side=side, closed=closed, cancel=cancel):
                        shape, _ = build_shape(closed=closed, cut_cor=side)
                        pp = make_postpro()
                        pp.vars.General.cancel_cc_for_depth = cancel
                        plan, code = self.plan_and_export(shape, pp)
                        ons = [a.args[0] for a in plan.actions
                               if a.kind == "compensation_on"]
                        self.assertEqual(ons, [side] * (3 if cancel else 1)
                                         if closed else [side, 83 - side, side])
                        self.assertEqual(re.findall(r"\bG4[12]\b", code),
                                         ["G%d" % value for value in ons])
                        self.assertIn("compensation_off", [a.kind for a in plan.actions])
                        if not cancel and (closed or side == 41):
                            name = "g%d_closed" % side if closed else "g41_open"
                            self.check_golden(name, code)

    def test_leads_overcut_and_failed_geometry(self):
        shape, _ = build_shape(layer_settings=dict(
            lead_in_mode="radius", lead_radius=20,
            lead_out_mode="straight", overcut_enabled=True, overcut_length=50))
        plan, _ = self.plan_and_export(shape)
        self.assertTrue(any(a.role == "lead_in" for a in plan.actions))
        self.assertTrue(any(a.role == "lead_out" for a in plan.actions))
        plunges = [i for i, a in enumerate(plan.actions) if a.role == "plunge"]
        self.assertTrue(all(i < plunges[1] for i, a in enumerate(plan.actions)
                            if a.role == "lead_in"))
        self.assertTrue(all(i > plunges[-1] for i, a in enumerate(plan.actions)
                            if a.role == "lead_out"))
        shape.parentLayer.lead_out_mode = "radius"
        shape.parentLayer.lead_radius = 1
        result = make_plan_service().execute_result(shape, make_postpro())
        self.assertIsNone(result.plan)
        self.assertEqual(result.diagnostics[-1].code, "lead.invalid_exit")

    def test_tabs_are_projected_only_at_the_selected_depths(self):
        from dxf2gcode_breaks_pass_test import make_break_layer
        for first_pass, expected in ((-1, [-5]), (0, []), (1, [-2, -4, -5]),
                                     (2, [-4, -5])):
            with self.subTest(first_pass=first_pass):
                shape, _ = build_shape(cut_cor=40, layer_settings=dict(
                    lead_in_mode="off", lead_out_mode="off"))
                shape.break_pass = first_pass
                pp = make_postpro()
                pp.breaks = Breaks(Layers([
                    shape.parentLayer, make_break_layer("BREAKS: 1 MillDepth: -1.5")]))
                plan, code = self.plan_and_export(shape, pp)
                depth, selected = None, []
                for action in plan.actions:
                    if action.role == "plunge":
                        depth = action.args[0]
                    if action.role == "tab" and action.kind == "linear_z":
                        if depth not in selected:
                            selected.append(depth)
                self.assertEqual(selected, expected)
                xyz = plan_xyz_segments(plan)
                self.assertEqual(any(p[2] == -1.5 for s in xyz for p in s), bool(expected))
                if first_pass == 2:
                    self.check_golden("slices_tabs_from_second_pass", code)

    def test_pocket_directions_keep_initial_approach_and_safe_connections(self):
        for side in (40, 41, 42):
            with self.subTest(side=side):
                shape, _ = build_shape(cut_cor=side, done_by_machine=False,
                                       tool_diameter=20, layer_settings=dict(
                                           lead_in_mode="off", lead_out_mode="off"))
                shape.Pocket = True
                shape.stmove = prepare_shape(shape)
                plan, code = self.plan_and_export(shape)
                rapids = [a for a in plan.actions if a.kind == "rapid_xy"]
                self.assertGreater(len(rapids), 1)
                self.assertEqual(plan.approach_xy, rapids[0].args[0])
                self.assertTrue(any(a.role == "pocket" for a in plan.actions))
                self.assertFalse(any(a.kind == "compensation_on" for a in plan.actions))
                self.assertEqual([a.args[0] for a in plan.actions
                                  if a.role == "plunge"], [-2, -4, -5])
                self.check_golden("slices_pocket_g%d" % side, code)

    def test_drilling_circle_and_hole_keep_position_and_peck_depths(self):
        for hole in (False, True):
            for repeat in (False, True):
                with self.subTest(hole=hole, repeat=repeat):
                    shape, _ = build_shape(cut_cor=40, layer_settings=dict(
                        lead_in_mode="off", lead_out_mode="off"))
                    shape.geos = Geos([HoleGeo(Point(7, 9))] if hole else [ArcGeo(
                        Ps=Point(9, 9), Pe=Point(9, 9), O=Point(7, 9),
                        r=2, direction=1)])
                    for geo in shape.geos:
                        geo.make_abs_geo()
                    shape.Drill = True
                    shape.stmove = prepare_shape(shape)
                    pp = make_postpro()
                    pp.vars.General.repeat_drill_move = repeat
                    plan, code = self.plan_and_export(shape, pp)
                    self.assertEqual(plan.approach_xy, (7, 9))
                    depths = [-2, -4, -5] if repeat else [-5]
                    self.assertEqual([a.args[0] for a in plan.actions
                                      if a.kind == "drill"], depths)
                    self.assertEqual(sum(a.kind == "drill_retract" for a in plan.actions),
                                     len(depths) - 1)
                    self.assertFalse(any(a.kind in ("linear_xy", "arc", "compensation_on")
                                         for a in plan.actions))
                    xyz = plan_xyz_segments(plan)
                    self.assertTrue(xyz, "drilling must be visible in 3D")
                    self.assertEqual({p[:2] for s in xyz for p in s}, {(7, 9)})
                    self.assertTrue(set(depths).issubset({p[2] for s in xyz for p in s}))
                    xy = plan_xy_segments(plan)
                    self.assertTrue(xy, "keep the 2D hole marker")
                    for start, end in xy:
                        for x, y in (start, end):
                            self.assertAlmostEqual((x - 7) ** 2 + (y - 9) ** 2, 25)
                    self.check_golden("slices_drill_peck" if repeat else "slices_drill", code)

    def test_2d_painter_keeps_disconnected_plan_segments_separate(self):
        from dataclasses import replace
        from dxf2gcode.domain.toolpath.plan import ToolpathAction
        from dxf2gcode.presentation.qt.canvas2d import MyGraphicsScene, ShapeGUI
        shape, _ = build_shape(cut_cor=40, layer_settings=dict(
            lead_in_mode="off", lead_out_mode="off"))
        shape.calc_bounding_box()
        plan, _ = self.plan_and_export(shape)
        plan = replace(plan, actions=(
            ToolpathAction("linear_xy", ((0, 0), (1, 0))),
            ToolpathAction("linear_xy", ((4, 0), (5, 0)))))
        scene = MyGraphicsScene()
        item = ShapeGUI(shape)
        with patch.object(MyGraphicsScene, "_shape_toolpath_plan", return_value=plan):
            scene.paint_shape(item)
        path = item.stmove_item._comp_path
        elements = [path.elementAt(i) for i in range(path.elementCount())]
        self.assertEqual([(e.x, e.y, e.isMoveTo()) for e in elements],
                         [(0, 0, True), (1, 0, False), (4, 0, True), (5, 0, False)])
        self.assertEqual(item.path.boundingRect().width(), 100)

    def test_drag_knife_tip_offset_swivels_and_ramp(self):
        for ramp, name in ((0, "drag_knife_closed"), (20, "drag_knife_ramp_in")):
            with self.subTest(ramp=ramp):
                g.config.var_dict["Drag_Knife_Options"]["ramp_in_length"] = ramp
                g.config.update_config()
                shape, _ = build_shape(cut_cor=40, machine_type="drag_knife")
                plan, code = self.plan_and_export(shape)
                self.check_golden(name, code)
                swivels = [a for a in plan.actions if a.role == "drag_swivel"]
                self.assertTrue(any(a.kind == "arc" for a in swivels))
                self.assertTrue(any(a.kind == "linear_z" and a.args[0] == -.1
                                    for a in swivels))
                cuts = [a for a in plan.actions if a.kind in ("linear_xy", "linear_xyz") and a.role == 'cut']
                # The holder is ahead of the original tip path by the tool
                # radius (5 mm), so the prepared first side ends at x=105.
                self.assertEqual(cuts[0].args[0], (5, 0))
                if not ramp:
                    self.assertIn((105, 0), [a.args[1] for a in cuts])
                self.assertEqual(any(a.role == "ramp" for a in plan.actions), bool(ramp))
                self.assertTrue(plan_xy_segments(plan))
                self.assertTrue(plan_xyz_segments(plan))

    def test_lathe_lines_arcs_and_existing_lead_restrictions(self):
        for closed in (True, False):
            with self.subTest(closed=closed):
                shape, _ = build_shape(closed=closed, cut_cor=40, machine_type="lathe",
                                       layer_settings=dict(
                                           lead_in_mode="radius", lead_radius=20,
                                           lead_out_mode="straight", overcut_enabled=True,
                                           overcut_length=50))
                if not closed:
                    shape.geos = Geos([ArcGeo(Ps=Point(10, 0), Pe=Point(0, 10),
                                             O=Point(0, 0), r=10, direction=1)])
                    shape.geos[0].make_abs_geo()
                    shape.stmove = prepare_shape(shape)
                plan, code = self.plan_and_export(shape)
                self.assertFalse(any(a.role in ("lead_in", "lead_out") for a in plan.actions))
                self.assertEqual([a.args[0] for a in plan.actions
                                  if a.role == "plunge"], [-2, -4, -5])
                self.assertTrue(plan_xy_segments(plan))
                self.assertTrue(plan_xyz_segments(plan))
                self.check_golden("slices_lathe_closed" if closed else "slices_lathe_arc_open", code)
