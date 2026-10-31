"""Reversed compound DXF entities must retain a connected geometry chain."""

from pathlib import Path
import unittest

from dxf2gcode_leadmove_golden_test import GoldenTestBase
from dxf2gcode_stmove_gcode_test import make_plan_service, make_postpro
from dxf2gcode.adapters.dxf.parser import ReadDXF
from dxf2gcode.adapters.toolpath.preparation import prepare_shape
from dxf2gcode.application.drawings import BuildDrawingModel
from dxf2gcode.domain.project.shape import Shape
import dxf2gcode.bootstrap.runtime_state as g


class TestReversedImportChain(GoldenTestBase):
    def fixtures(self):
        directory = Path(__file__).resolve().parents[1] / 'dxf'
        return (next(directory.glob('*2004.dxf')), directory / 'ATT00079.dxf')

    @staticmethod
    def imported_endpoints(drawing):
        return tuple((geo.get_start_end_points(True).x,
                      geo.get_start_end_points(True).y,
                      geo.get_start_end_points(False).x,
                      geo.get_start_end_points(False).y)
                     for entity in drawing.entities.geo for geo in entity.geo)

    def build(self, path, split=False):
        drawing = ReadDXF(filename=str(path))
        # Confirm these fixtures exercise the formerly broken branch.
        self.assertTrue(any(reverse and len(drawing.entities.geo[index].geo) > 1
                            for contour in drawing.entities.cont
                            for index, reverse in contour.order))
        before = self.imported_endpoints(drawing)
        model = BuildDrawingModel(drawing, g.config, Shape, split).execute()
        self.assertEqual(self.imported_endpoints(drawing), before)
        return model

    def test_both_drawings_have_connected_original_geometry(self):
        for path in self.fixtures():
            for split in (False, True):
                with self.subTest(file=path.name, split_lines=split):
                    model = self.build(path, split)
                    for shape in model.shapes:
                        geos = list(shape.geos.abs_iter())
                        pairs = list(zip(geos, geos[1:]))
                        if shape.closed:
                            pairs.append((geos[-1], geos[0]))
                        for first, second in pairs:
                            gap = first.get_start_end_points(False).distance(
                                second.get_start_end_points(True))
                            self.assertLessEqual(gap, g.config.point_tolerance + 1e-8,
                                                 (path.name, shape.nr, gap))

    def test_g40_plans_do_not_jump_between_compound_entity_pieces(self):
        previous_window = g.window
        g.window = None
        try:
            for path in self.fixtures():
                model = self.build(path)
                for shape in model.shapes:
                    shape.cut_cor = 40
                    shape.lead_in_mode = shape.lead_out_mode = 'off'
                    shape.overcut_enabled = False
                    prepare_shape(shape, build_preview=False)
                    result = make_plan_service().execute_result(shape, make_postpro())
                    self.assertFalse(result.has_errors, (path.name, shape.nr, result.diagnostics))
                    self.assertIsNotNone(result.plan)
                    for toolpass in result.plan.passes:
                        for first, second in zip(toolpass.moves, toolpass.moves[1:]):
                            gap = sum((a-b)**2 for a, b in
                                      zip(first.end_xy, second.start_xy)) ** .5
                            self.assertLessEqual(gap, g.config.point_tolerance + 1e-8,
                                                 (path.name, shape.nr, toolpass.number, gap))
        finally:
            g.window = previous_window


if __name__ == '__main__':
    unittest.main()
