"""BREAKS corner contacts must not recursively subdivide unchanged geometry."""
from math import pi
from pathlib import Path

from dxf2gcode_leadmove_golden_test import GoldenTestBase
from dxf2gcode.adapters.postprocessor.breaks import Breaks
from dxf2gcode.domain.geometry.linegeo import LineGeo
from dxf2gcode.domain.geometry.arcgeo import ArcGeo
from dxf2gcode.domain.geometry.breakgeo import BreakGeo
from dxf2gcode.domain.geometry.point import Point
from dxf2gcode.domain.project.shape import Shape, Geos
from dxf2gcode.domain.project.layercontent import LayerContent, Layers
import dxf2gcode.bootstrap.runtime_state as g


class TestBreakIntersections(GoldenTestBase):
    def splitter(self, x0=0, x1=1, y0=0, y1=1):
        points = [Point(x0, y0), Point(x1, y0), Point(x1, y1), Point(x0, y1)]
        geos = Geos(LineGeo(a, b) for a, b in zip(points, points[1:]+points[:1]))
        shape = Shape(1, True, geos=geos, config=g.config)
        shape.axis3_mill_depth, shape.f_g1_plane, shape.f_g1_depth = -1, 500, 300
        layer = LayerContent(1, 'BREAKS:', [shape], config=g.config)
        shape.parentLayer = layer
        return Breaks(Layers([layer]))

    def assert_chain(self, parts, start, end):
        self.assertEqual(parts[0].Ps, start)
        self.assertEqual(parts[-1].Pe, end)
        self.assertTrue(all(part.length > 1e-9 for part in parts))
        for first, second in zip(parts, parts[1:]):
            self.assertEqual(first.Pe, second.Ps)

    def test_single_corner_touch_does_not_create_zero_width_tab(self):
        line = LineGeo(Point(-1, 1), Point(1, -1))
        parts = self.splitter().breakLineGeo(line)
        self.assertEqual(parts, [line])

    def test_opposite_corner_hits_are_counted_once_and_form_one_tab(self):
        for reverse in (False, True):
            line = LineGeo(Point(-1, -1), Point(2, 2))
            if reverse:
                line.reverse()
            parts = self.splitter().breakLineGeo(line)
            self.assertEqual(len(parts), 3)
            self.assert_chain(parts, line.Ps, line.Pe)
            self.assertIsInstance(parts[1], BreakGeo)
            self.assertEqual((parts[1].height, parts[1].xyfeed, parts[1].zfeed), (-1, 500, 300))

    def test_split_at_original_endpoints_emits_no_empty_fragments(self):
        line = LineGeo(Point(0, .5), Point(1, .5))
        parts = self.splitter().breakLineGeo(line)
        self.assertEqual(len(parts), 1)
        self.assertIsInstance(parts[0], BreakGeo)
        self.assert_chain(parts, line.Ps, line.Pe)

    def test_arc_exit_at_endpoint_does_not_create_a_full_circle_tail(self):
        arc = ArcGeo(Ps=Point(1, 0), Pe=Point(0, 1), O=Point(), r=1, direction=1)
        parts = self.splitter(0, .5, 0, 2).breakArcGeo(arc)
        self.assertEqual(len(parts), 2)
        self.assert_chain(parts, arc.Ps, arc.Pe)
        self.assertIsInstance(parts[-1], BreakGeo)
        self.assertLess(parts[0].ext, pi/2)

    def test_break_example_import_preview_keeps_real_tabs(self):
        from dxf2gcode.adapters.dxf.parser import ReadDXF
        from dxf2gcode.application.drawings import BuildDrawingModel
        from dxf2gcode.adapters.toolpath.preparation import prepare_shape
        from dxf2gcode.adapters.toolpath.preview import preview_result
        path = Path(__file__).resolve().parents[1] / 'dxf/BreakExample.dxf'
        model = BuildDrawingModel(ReadDXF(filename=str(path)), g.config, Shape, False).execute()
        splitter = Breaks(model.layers)
        self.assertEqual(len(model.shapes), 5)
        found = []
        for shape in model.shapes:
            parts = splitter.getNewGeos(shape.geos)
            if not shape.parentLayer.isBreakLayer():
                found.extend(part for part in parts if isinstance(part, BreakGeo))
            prepare_shape(shape, build_preview=False)
            result = preview_result(shape, layers=model.layers)
            self.assertFalse(result.has_errors)
        self.assertTrue(found)
