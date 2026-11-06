# -*- coding: utf-8 -*-
"""
Regression tests for the software cutter compensation of the closed ellipse
(dxf/test.dxf, entity 2).

The raw offset of the ellipse is complete (71 elements), but the GIR removal
treated the cyclic connection of the closed raw offset as a self-intersection
and deleted almost the whole curve. The result was one single OffArcGeo with
the status "ok". The fix skips only the shared connection point (not a real
crossing) and adds a collapse guard.
"""
from __future__ import absolute_import

import os
import sys
import unittest
from copy import deepcopy

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_DIR = os.path.dirname(_TEST_DIR)
sys.path[:0] = [_TEST_DIR, os.path.join(_REPO_DIR, "source")]
from toolpath_test_support import serialize_gcode, serialize_shape_geometry

from dxf2gcode_stmove_gcode_test import (  # noqa: E402
    corridor_shape, make_postpro)

import dxf2gcode.bootstrap.runtime_state as g  # noqa: E402
from dxf2gcode.domain.geometry.arcgeo import ArcGeo  # noqa: E402
from dxf2gcode.domain.project.layercontent import LayerContent  # noqa: E402
from dxf2gcode.domain.toolpath.leadmove import LEAD_RADIUS, LEAD_STRAIGHT  # noqa: E402
from dxf2gcode.domain.project.shape import Geos, Shape  # noqa: E402
from dxf2gcode.domain.toolpath.shapeoffset import OffArcGeo, offShapeClass  # noqa: E402
from dxf2gcode.adapters.toolpath.preparation import prepare_shape  # noqa: E402
from dxf2gcode.adapters.dxf.parser import ReadDXF  # noqa: E402

DXF = os.path.join(_REPO_DIR, "dxf", "test.dxf")
ELLIPSE_NR = 2          # closed full ellipse (GeoentEllipse)
TOOL_RADIUS = 1.525
DISTANCE_MARGIN = 0.02  # a little more than the 1 % validation tolerance
MIN_ELEMENTS = 60       # the ellipse is converted to 70 arcs


def shape_from(geos, closed):
    shape = Shape(0, closed, geos=Geos([deepcopy(geo) for geo in geos]), config=g.config)
    shape.AnalyseAndOptimize()
    return shape


def offset_distance_range(off, target=TOOL_RADIUS):
    values = []
    for loop in off.loops:
        for geo in loop:
            length = getattr(geo, 'length', 0.0) or 0.0
            n = 8
            if length > 0:
                n = max(n, min(int(length / (0.1 * target)) + 1, 500))
            for k in range(n + 1):
                p = off._sample_offset_point(geo, k / float(n))
                d, _ = off._nearest_source(p)
                values.append(d)
    return min(values), max(values)


def loop_perimeter(loop):
    total = 0.0
    for geo in loop:
        if isinstance(geo, ArcGeo):
            total += abs(geo.ext) * geo.r
        else:
            total += geo.get_start_end_points(True).distance(
                geo.get_start_end_points(False))
    return total


def continuity_gap(loop):
    gaps = []
    for first, second in zip(loop[:-1], loop[1:]):
        gaps.append(first.get_start_end_points(False).distance(
            second.get_start_end_points(True)))
    if len(loop) > 1:
        gaps.append(loop[-1].get_start_end_points(False).distance(
            loop[0].get_start_end_points(True)))
    return max(gaps) if gaps else 0.0


class TestFullEllipseOffset(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.dxf = ReadDXF(filename=DXF)
        cls.entity = cls.dxf.entities.geo[ELLIPSE_NR]

    def _offset(self, offtype):
        shape = shape_from(self.entity.geo, closed=True)
        return offShapeClass(parent=shape, offset=TOOL_RADIUS,
                             offtype=offtype)

    def _assert_complete(self, offtype):
        off = self._offset(offtype)
        self.assertEqual(off.offset_status, "ok", offtype)
        self.assertEqual(len(off.loops), 1, offtype)
        loop = off.loops[0]
        self.assertGreaterEqual(len(loop), MIN_ELEMENTS, offtype)
        self.assertGreater(loop_perimeter(loop), 100.0, offtype)
        self.assertLess(continuity_gap(loop), 1e-6, offtype)
        self.assertEqual(len(off._find_crossings(loop)), 0, offtype)
        low, high = offset_distance_range(off)
        self.assertGreaterEqual(low, TOOL_RADIUS - DISTANCE_MARGIN, offtype)
        self.assertLessEqual(high, TOOL_RADIUS + DISTANCE_MARGIN, offtype)

    def test_out_is_a_complete_closed_offset(self):
        self._assert_complete("out")

    def test_in_is_a_complete_closed_offset(self):
        self._assert_complete("in")

    def test_the_offset_does_not_collapse_to_one_element(self):
        for offtype in ("out", "in"):
            off = self._offset(offtype)
            total = sum(len(loop) for loop in off.loops)
            self.assertGreater(total, MIN_ELEMENTS, offtype)

    def test_the_complete_toolpath_is_built(self):
        # Exact layer parameters from the reported case: tool 3.05 mm,
        # lead radius 1.6 mm, lead length 1.52 mm, straight lead in, circle
        # lead out, software compensation.
        g.config.machine_type = 'milling'
        g.config.var_dict['Cutter_Compensation']['done_by_machine'] = False
        g.config.update_config()
        for cut_cor in (41, 42):
            shape = shape_from(self.entity.geo, closed=True)
            layer = LayerContent(nr=3, name='Ebene 1', shapes=[], config=g.config)
            layer.tool_diameter = 3.05
            layer.lead_radius = 1.6
            layer.lead_length = 1.52
            layer.lead_in_mode = LEAD_STRAIGHT
            layer.lead_out_mode = LEAD_RADIUS
            layer.overcut_enabled = False
            layer.overcut_length = 2.0
            layer.milling_offset = 0.0
            shape.parentLayer = layer
            shape.cut_cor = cut_cor
            shape.axis3_mill_depth = -12.45
            shape.axis3_start_mill_depth = 0.0
            shape.axis3_slice_depth = -4.06
            shape.stmove = prepare_shape(shape)

            offset_geos = [geo for geo in shape.stmove.geos
                           if isinstance(geo, OffArcGeo)]
            self.assertGreaterEqual(len(offset_geos), MIN_ELEMENTS,
                                    cut_cor)
            gcode = serialize_gcode(shape, make_postpro())
            arcs = sum(1 for line in gcode.splitlines()
                       if line.split()[:1] in (["G2"], ["G3"]))
            self.assertGreaterEqual(arcs, 100, cut_cor)


class TestRealGlobalInterference(unittest.TestCase):
    """The closure guard must not disable genuine GIR handling."""

    def test_a_corridor_is_still_trimmed_into_three_loops(self):
        off = offShapeClass(parent=corridor_shape(), offset=1.5,
                            offtype="in")
        self.assertEqual(off.offset_status, "ok")
        self.assertEqual(len(off.loops), 3)
        for loop in off.loops:
            self.assertLess(continuity_gap(loop), 1e-6)
            self.assertGreater(loop_perimeter(loop), 1.0)


class TestCollapseGuard(unittest.TestCase):
    """A nearly deleted offset must not be reported as "ok"."""

    def test_a_collapsed_offset_is_not_ok(self):
        dxf = ReadDXF(filename=DXF)
        entity = dxf.entities.geo[ELLIPSE_NR]
        shape = shape_from(entity.geo, closed=True)

        class Collapse(offShapeClass):
            def remove_global_interferences(self):
                # Simulate the former GIR bug: only one raw element survives.
                if len(self.rawoff) >= 3:
                    self.rawoff = Geos([self.rawoff[0]])

        off = Collapse(parent=shape, offset=TOOL_RADIUS, offtype="out")
        self.assertNotEqual(off.offset_status, "ok")
        self.assertEqual(len(off.rawoff), 0)
        self.assertEqual(len(off.loops), 0)


if __name__ == "__main__":
    unittest.main()
