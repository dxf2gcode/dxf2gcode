# -*- coding: utf-8 -*-
"""Contracts for DXF entity import and nested block transforms."""
from __future__ import absolute_import

import os
import sys
import tempfile
import unittest
from math import pi

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_DIR = os.path.dirname(_TEST_DIR)
sys.path[:0] = [_TEST_DIR, os.path.join(_REPO_DIR, "source")]

import dxf2gcode.globals.globals as g  # noqa: E402
from dxf2gcode.core.entitycontent import EntityContent  # noqa: E402
from dxf2gcode.core.linegeo import LineGeo  # noqa: E402
from dxf2gcode.core.point import Point  # noqa: E402
from dxf2gcode.dxfimport.importer import ReadDXF  # noqa: E402
from dxf2gcode.dxfimport.importer import (  # noqa: E402
    dxflinepairClass, dxflinepairsClass)
from dxf2gcode.dxfimport.geoent_circle import GeoentCircle  # noqa: E402
from dxf2gcode.dxfimport.geoent_point import GeoentPoint  # noqa: E402

if g.config is None:
    from dxf2gcode.globals.config import MyConfig  # noqa: E402
    g.folder = tempfile.mkdtemp(prefix="d2g_import_contract_")
    g.config = MyConfig()


def read_dxf(name):
    """Read a fixture without leaking the drawing's unit setting."""
    filename = os.path.join(_REPO_DIR, "dxf", name)
    old_metric = g.config.metric
    old_quiet = g.quiet
    g.quiet = True
    try:
        return ReadDXF(filename=filename)
    finally:
        g.config.metric = old_metric
        g.config.update_tool_values()
        g.quiet = old_quiet


class EntityCaller(object):
    """Small importer context for exercising individual DXF entities."""

    def __init__(self, pairs):
        self.line_pairs = dxflinepairsClass([
            dxflinepairClass(code, value) for code, value in pairs])
        self.start = 0

    def Get_Layer_Nr(self, name):
        self.layer_name = name
        return 7


def entity_caller(entity_type, data, extrusion=None):
    pairs = [(0, entity_type), (8, "drill-layer")]
    pairs.extend(data)
    if extrusion is not None:
        pairs.append((230, str(extrusion)))
    pairs.append((0, "ENDSEC"))
    return EntityCaller(pairs)


class TestDXFEntityImport(unittest.TestCase):

    def test_circle_import_makes_two_connected_arcs_with_full_circumference(self):
        caller = entity_caller(
            "CIRCLE", [(10, "12"), (20, "-4"), (40, "3.5")])

        circle = GeoentCircle(Nr=3, caller=caller)

        self.assertEqual(circle.Typ, "Circle")
        self.assertEqual(circle.Nr, 3)
        self.assertEqual(circle.Layer_Nr, 7)
        self.assertEqual(len(circle.geo), 2)
        self.assertAlmostEqual(circle.length, 2 * pi * 3.5)
        first_start = circle.geo[0].get_start_end_points(True)
        first_end = circle.geo[0].get_start_end_points(False)
        second_start = circle.geo[1].get_start_end_points(True)
        second_end = circle.geo[1].get_start_end_points(False)
        self.assertAlmostEqual(first_start.distance(second_end), 0.0)
        self.assertAlmostEqual(first_end.distance(second_start), 0.0)

    def test_circle_import_flips_center_for_negative_extrusion(self):
        caller = entity_caller(
            "CIRCLE", [(10, "12"), (20, "-4"), (40, "3.5")],
            extrusion=-1)

        circle = GeoentCircle(caller=caller)

        self.assertAlmostEqual(circle.geo[0].O.x, -12.0)
        self.assertAlmostEqual(circle.geo[0].O.y, -4.0)

    def test_point_import_creates_a_zero_length_hole_on_its_layer(self):
        caller = entity_caller("POINT", [(10, "8.25"), (20, "-2.5")])

        point = GeoentPoint(Nr=4, caller=caller)

        self.assertEqual(point.Typ, "Point")
        self.assertEqual(point.Nr, 4)
        self.assertEqual(point.Layer_Nr, 7)
        self.assertEqual(point.length, 0)
        self.assertEqual(len(point.geo), 1)
        self.assertAlmostEqual(point.geo[0].Ps.x, 8.25)
        self.assertAlmostEqual(point.geo[0].Ps.y, -2.5)
        self.assertEqual(point.geo[0].length, -1)

    def test_spline_ellipse_and_lwpolyline_entities_become_contours(self):
        dxf = read_dxf("test.dxf")
        types = [entity.Typ for entity in dxf.entities.geo]

        self.assertIn("Spline", types)
        self.assertIn("Ellipse", types)
        self.assertIn("LWPolyline", types)
        self.assertEqual(len(dxf.entities.cont), len(dxf.entities.geo))
        for entity in dxf.entities.geo:
            self.assertTrue(entity.geo, entity.Typ)
        for contour in dxf.entities.cont:
            self.assertTrue(contour.order)
            for entity_nr, direction in contour.order:
                self.assertGreaterEqual(entity_nr, 0)
                self.assertLess(entity_nr, len(dxf.entities.geo))
                self.assertIn(direction, (0, 1))

    def test_insert_fixture_keeps_nested_block_entity_types(self):
        dxf = read_dxf("Bogen_Ellipsen_Polylinien_Block.dxf")
        self.assertTrue(dxf.blocks.Entities)
        self.assertTrue(dxf.entities.geo)
        self.assertTrue(all(entity.Typ == "Insert"
                            for entity in dxf.entities.geo))

        block_types = [entity.Typ for block in dxf.blocks.Entities
                       for entity in block.geo]
        for entity_type in ("Insert", "Line", "Arc", "Ellipse",
                            "LWPolyline"):
            self.assertIn(entity_type, block_types)


class TestNestedBlockTransform(unittest.TestCase):

    def test_line_geometry_applies_nested_scale_rotation_and_translation(self):
        root = EntityContent(
            nr=0, name="root", parent=None, p0=Point(10, 20),
            pb=Point(0, 0), sca=[1, 1, 1], rot=pi / 2)
        insert = EntityContent(
            nr=1, name="block", parent=root, p0=Point(5, 0),
            pb=Point(1, 0), sca=[2, 2, 1], rot=0)
        line = LineGeo(Point(2, 1), Point(3, 1))

        line.make_abs_geo(parent=insert)

        self.assertAlmostEqual(line.abs_geo.Ps.x, 8.0)
        self.assertAlmostEqual(line.abs_geo.Ps.y, 27.0)
        self.assertAlmostEqual(line.abs_geo.Pe.x, 8.0)
        self.assertAlmostEqual(line.abs_geo.Pe.y, 29.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
