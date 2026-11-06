# -*- coding: utf-8 -*-
"""
Golden tests of the G-Code of the lead in, the lead out and the overcut.

The reference files contain the G-Code of the different combinations of
cutter compensation, contour type and lead in / lead out / overcut settings.
They protect the existing behaviour (the default settings have to produce
exactly the same G-Code as before) and they document the new geometry.

The radius at the workpiece and the length of the straight part are common to
the lead in and the lead out: they are defined per tool. The start move of
the program ('startmove') uses the radius at the workpiece, so the radius of
the tool is added to the old start radius (the radius of the tool center
path) - the geometry of the start move does not change.

Two reference files changed with the common radius: g41_lead_out_radius and
g41_lead_out_radius_open. The radius of the lead out is now the common
radius, so the start move of the lead in uses it as well (10.0 -> 20.0). The
geometry of the lead out itself is unchanged.

Run from the repository root:

    python -m unittest discover -s tests -t tests -p "dxf2gcode_leadmove_golden_test.py" -v
"""
from __future__ import absolute_import

import os
import sys
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [_TEST_DIR, os.path.join(os.path.dirname(_TEST_DIR), "source")]
from toolpath_test_support import serialize_gcode, serialize_shape_geometry

_GOLDEN_DIR = os.path.join(_TEST_DIR, "golden")

import dxf2gcode.bootstrap.runtime_state as g  # noqa: E402
from dxf2gcode.domain.geometry.arcgeo import ArcGeo  # noqa: E402
from dxf2gcode.domain.project.layercontent import LayerContent  # noqa: E402
from dxf2gcode.domain.geometry.linegeo import LineGeo  # noqa: E402
from dxf2gcode.domain.geometry.point import Point  # noqa: E402
from dxf2gcode.domain.project.shape import Shape, Geos  # noqa: E402
from dxf2gcode.adapters.toolpath.preparation import prepare_shape  # noqa: E402
from dxf2gcode.adapters.config.runtime_config import MyConfig  # noqa: E402
from dxf2gcode.adapters.postprocessor.breaks import Breaks  # noqa: E402
from dxf2gcode.adapters.postprocessor.postprocessor import MyPostProcessor  # noqa: E402
from dxf2gcode.adapters.postprocessor.postprocessorconfig import MyPostProConfig  # noqa: E402
from dxf2gcode.presentation.qt.qt_compat.QtWidgets import QApplication  # noqa: E402

import shutil
import tempfile

_APP = None


def _app():
    global _APP
    if _APP is None:
        _APP = QApplication.instance() or QApplication([])
    return _APP


class _LayerContentsStub(object):
    """The break layers are needed by the post processor."""

    def break_layer_iter(self):
        return []


def build_shape(closed=True, cut_cor=41, done_by_machine=True,
                tool_diameter=10.0, start_radius=5.0, slice_depth=-2.0,
                mill_depth=-5.0, layer_settings=None, machine_type='milling'):
    """
    Build a simple contour and its layer content.

    The start_radius is the radius of the tool center path of the start move
    of the program: the common radius at the workpiece is the start radius
    plus the radius of the tool. The common length of the straight lead in /
    lead out is the radius of the tool (the length of the straight part of
    the start move).

    @return: (shape, layer)
    """

    if closed:
        geos = Geos([LineGeo(Point(0, 0), Point(100, 0)),
                     LineGeo(Point(100, 0), Point(100, 100)),
                     LineGeo(Point(100, 100), Point(0, 100)),
                     LineGeo(Point(0, 100), Point(0, 0))])
    else:
        geos = Geos([LineGeo(Point(0, 0), Point(100, 0)),
                     LineGeo(Point(100, 0), Point(100, 100))])

    # The cutter compensation method is a global setting.
    g.config.var_dict['Cutter_Compensation']['done_by_machine'] = \
        done_by_machine
    g.config.update_config()
    g.config.machine_type = machine_type

    shape = Shape(nr=1, closed=closed, geos=geos, config=g.config)
    layer = LayerContent(nr=1, name="L1", shapes=[], config=g.config)
    layer.tool_diameter = tool_diameter
    # The common radius at the workpiece of the lead in / lead out: with the
    # start radius of the program it reproduces the start move of the
    # previous version.
    layer.lead_radius = start_radius + tool_diameter / 2.0
    # The common length of the straight lead in / lead out: the radius of the
    # tool (the length of the straight part of the start move).
    layer.lead_length = tool_diameter / 2.0
    shape.parentLayer = layer

    shape.parentEntity = None
    shape.cw = True
    shape.cut_cor = cut_cor
    for geo in shape.geos:
        geo.make_abs_geo()

    if layer_settings:
        for name, value in layer_settings.items():
            setattr(layer, name, value)

    shape.axis3_mill_depth = mill_depth
    shape.axis3_start_mill_depth = 0.0
    shape.axis3_slice_depth = slice_depth
    shape.stmove = prepare_shape(shape)
    return shape, layer


def export_gcode(shape, layer):
    """
    Export the G-Code of a shape.
    @return: the G-Code
    """
    postpro = MyPostProcessor()
    postpro.breaks = Breaks(_LayerContentsStub())
    postpro_config = MyPostProConfig()
    postpro_config.load_config()
    postpro.vars = postpro_config.vars
    postpro.initialize_export_vars()
    return serialize_gcode(shape, postpro)


class GoldenTestBase(unittest.TestCase):

    def setUp(self):
        _app()
        self.tmp = tempfile.mkdtemp(prefix="d2g_golden_")
        self._old_folder = getattr(g, "folder", None)
        self._old_config = getattr(g, "config", None)
        self._old_machine_type = getattr(g.config, "machine_type", 'milling')
        g.folder = self.tmp
        os.makedirs(os.path.join(self.tmp, "config"))
        self.config = MyConfig()
        g.config = self.config

    def tearDown(self):
        g.folder = self._old_folder
        g.config = self._old_config
        shutil.rmtree(self.tmp, ignore_errors=True)

    def check_golden(self, name, gcode):
        """
        Compare the G-Code with the reference file. If the reference does not
        exist, it is created (the test then fails, so that the new file is
        reviewed before it is used).
        """
        path = os.path.join(_GOLDEN_DIR, name + ".gcode")
        if not os.path.exists(path):
            if not os.path.exists(_GOLDEN_DIR):
                os.makedirs(_GOLDEN_DIR)
            with open(path, "w") as golden:
                golden.write(gcode)
            self.fail("The reference file %s was created - please check it."
                      % path)
        with open(path) as golden:
            expected = golden.read()
        if expected != gcode:
            self.fail("The G-Code differs from the reference %s:\n%s"
                      % (path, gcode))
        self.assertTrue(gcode)


class TestGoldenG41(GoldenTestBase):
    """The G-Code of the machine cutter compensation."""

    def test_closed_contour(self):
        shape, layer = build_shape(closed=True, cut_cor=41)
        self.check_golden("g41_closed", export_gcode(shape, layer))

    def test_open_contour(self):
        shape, layer = build_shape(closed=False, cut_cor=41)
        self.check_golden("g41_open", export_gcode(shape, layer))

    def test_closed_contour_g42(self):
        shape, layer = build_shape(closed=True, cut_cor=42)
        self.check_golden("g42_closed", export_gcode(shape, layer))


class TestGoldenSoftwareCompensation(GoldenTestBase):
    """The G-Code of the internal cutter compensation."""

    def test_closed_contour(self):
        shape, layer = build_shape(closed=True, cut_cor=41,
                                   done_by_machine=False)
        self.check_golden("software_closed", export_gcode(shape, layer))

    def test_open_contour(self):
        shape, layer = build_shape(closed=False, cut_cor=41,
                                   done_by_machine=False)
        self.check_golden("software_open", export_gcode(shape, layer))


class TestGoldenDragKnife(GoldenTestBase):
    """The G-Code of the drag knife."""

    def test_closed_contour(self):
        g.config.machine_type = 'drag_knife'
        shape, layer = build_shape(closed=True, cut_cor=40, machine_type='drag_knife')
        self.check_golden("drag_knife_closed", export_gcode(shape, layer))

    def test_open_contour(self):
        g.config.machine_type = 'drag_knife'
        shape, layer = build_shape(closed=False, cut_cor=40, machine_type='drag_knife')
        self.check_golden("drag_knife_open", export_gcode(shape, layer))

    def test_overcut(self):
        g.config.machine_type = 'drag_knife'
        shape, layer = build_shape(
            closed=True, cut_cor=40, machine_type='drag_knife',
            layer_settings=dict(overcut_enabled=True, overcut_length=50.0))
        self.check_golden("drag_knife_overcut", export_gcode(shape, layer))

    def test_ramp_in(self):
        g.config.machine_type = 'drag_knife'
        g.config.var_dict['Drag_Knife_Options']['ramp_in_length'] = 20.0
        g.config.update_config()
        shape, layer = build_shape(closed=True, cut_cor=40, machine_type='drag_knife')
        self.check_golden("drag_knife_ramp_in", export_gcode(shape, layer))


class TestGoldenLeadIn(GoldenTestBase):
    """The G-Code of the new lead in modes."""

    def test_lead_in_with_radius(self):
        shape, layer = build_shape(
            closed=True, cut_cor=41,
            layer_settings=dict(lead_in_mode='radius', lead_radius=20.0))
        self.check_golden("g41_lead_in_radius", export_gcode(shape, layer))

    def test_lead_in_straight(self):
        shape, layer = build_shape(
            closed=True, cut_cor=41,
            layer_settings=dict(lead_in_mode='straight'))
        self.check_golden("g41_lead_in_straight", export_gcode(shape, layer))

    def test_lead_in_with_radius_software_compensation(self):
        shape, layer = build_shape(
            closed=True, cut_cor=41, done_by_machine=False,
            layer_settings=dict(lead_in_mode='radius', lead_radius=20.0))
        self.check_golden("software_lead_in_radius",
                          export_gcode(shape, layer))


class TestGoldenLeadOutAndOvercut(GoldenTestBase):
    """The G-Code of the lead out and the overcut."""

    def test_lead_out_straight_closed(self):
        shape, layer = build_shape(
            closed=True, cut_cor=41,
            layer_settings=dict(lead_out_mode='straight'))
        self.check_golden("g41_lead_out_straight",
                          export_gcode(shape, layer))

    def test_lead_out_straight_open(self):
        shape, layer = build_shape(
            closed=False, cut_cor=41,
            layer_settings=dict(lead_out_mode='straight'))
        self.check_golden("g41_lead_out_straight_open",
                          export_gcode(shape, layer))

    def test_lead_out_with_radius(self):
        shape, layer = build_shape(
            closed=True, cut_cor=41,
            layer_settings=dict(lead_out_mode='radius',
                                lead_radius=20.0))
        self.check_golden("g41_lead_out_radius", export_gcode(shape, layer))

    def test_lead_out_with_radius_open_contour(self):
        # The open contour is milled in alternating directions: the second
        # pass is milled backwards and the compensation is switched to G42.
        # The lead out has to follow the compensation of the pass.
        shape, layer = build_shape(
            closed=False, cut_cor=41, slice_depth=-2.0, mill_depth=-4.0,
            layer_settings=dict(lead_out_mode='radius',
                                lead_radius=20.0))
        self.check_golden("g41_lead_out_radius_open",
                          export_gcode(shape, layer))


    def test_overcut(self):
        shape, layer = build_shape(
            closed=True, cut_cor=41,
            layer_settings=dict(overcut_enabled=True, overcut_length=50.0))
        self.check_golden("g41_overcut", export_gcode(shape, layer))

    def test_overcut_software_compensation(self):
        shape, layer = build_shape(
            closed=True, cut_cor=41, done_by_machine=False,
            layer_settings=dict(overcut_enabled=True, overcut_length=50.0))
        self.check_golden("software_overcut", export_gcode(shape, layer))


if __name__ == "__main__":
    unittest.main(verbosity=2)
