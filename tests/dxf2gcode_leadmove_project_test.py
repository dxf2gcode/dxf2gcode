# -*- coding: utf-8 -*-
"""
Tests of the persistence of the lead in / lead out / overcut values of the
layers in the project file (.d2g).

Run from the repository root:

    python -m unittest discover -s tests -t tests -p "dxf2gcode_leadmove_project_test.py" -v
"""
from __future__ import absolute_import

import os
import shutil
import sys
import tempfile
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [_TEST_DIR, os.path.join(os.path.dirname(_TEST_DIR), "source")]

import dxf2gcode.globals.globals as g  # noqa: E402
from dxf2gcode.core.layercontent import LayerContent  # noqa: E402
from dxf2gcode.core.project import Project  # noqa: E402
from dxf2gcode.core.shape import Shape, Geos  # noqa: E402
from dxf2gcode.core.linegeo import LineGeo  # noqa: E402
from dxf2gcode.core.point import Point  # noqa: E402
from dxf2gcode.globals.config import MyConfig  # noqa: E402
from dxf2gcode.Qt.QtWidgets import QApplication  # noqa: E402

_APP = None


def _app():
    global _APP
    if _APP is None:
        _APP = QApplication.instance() or QApplication([])
    return _APP


class _ActionStub(object):
    def isChecked(self):
        return False


class _UiStub(object):
    actionSplitLineSegments = _ActionStub()
    actionAutomaticCutterCompensation = _ActionStub()


class _TreeHandlerStub(object):
    def updateExportOrder(self, *args):
        pass


class _ParentStub(object):
    """The minimum the project export / load needs."""

    def __init__(self, layers):
        self.TreeHandler = _TreeHandlerStub()
        self.layerContents = layers
        self.ui = _UiStub()
        self.filename = "test.d2g"
        self.cont_scale = 1.0
        self.cont_rotate = 0.0
        self.cont_dx = 0.0
        self.cont_dy = 0.0
        self.cont_mirrorx = False
        self.cont_mirrory = False
        self.newNumber = 0

    def plot(self):
        pass


def build_layer(name="L1", with_shape=True):
    layer = LayerContent(nr=1, name=name, shapes=[])
    layer.tool_nr = 1
    layer.tool_diameter = 10.0
    layer.speed = 1000.0
    layer.lead_radius = 10.0
    layer.lead_length = 5.0
    layer.axis3_retract = 10.0
    layer.axis3_safe_margin = 3.0
    if with_shape:
        shape = Shape(nr=1, closed=True,
                      geos=Geos([LineGeo(Point(0, 0), Point(100, 0)),
                                 LineGeo(Point(100, 0), Point(100, 100)),
                                 LineGeo(Point(100, 100), Point(0, 100)),
                                 LineGeo(Point(0, 100), Point(0, 0))]))
        layer.shapes = [shape]
        layer.exp_order_complete = [0]
    return layer


class ProjectRoundtripBase(unittest.TestCase):

    def setUp(self):
        _app()
        self.tmp = tempfile.mkdtemp(prefix="d2g_project_")
        self._old_folder = getattr(g, "folder", None)
        self._old_config = getattr(g, "config", None)
        g.folder = self.tmp
        os.makedirs(os.path.join(self.tmp, "config"))
        self.config = MyConfig()
        g.config = self.config

    def tearDown(self):
        g.folder = self._old_folder
        g.config = self._old_config
        shutil.rmtree(self.tmp, ignore_errors=True)


class TestProjectRoundtrip(ProjectRoundtripBase):
    """Save and load the project file with the new values."""

    def test_the_values_are_saved_and_restored(self):
        layer = build_layer()
        layer.lead_in_mode = 'radius'
        layer.lead_radius = 12.5
        layer.lead_length = 4.0
        layer.lead_out_mode = 'straight'
        layer.overcut_enabled = True
        layer.overcut_length = 3.5
        parent = _ParentStub([layer])

        project = Project(parent)
        content = project.export(compleet=False)
        self.assertIn("'lead_in_mode': 'radius'", content)
        self.assertIn("'lead_radius': 12.5", content)
        self.assertIn("'lead_length': 4.0", content)
        self.assertIn("'lead_out_mode': 'straight'", content)
        self.assertIn("'overcut_enabled': True", content)
        self.assertIn("'overcut_length': 3.5", content)

        # Change the values and load the project again.
        layer.lead_in_mode = 'off'
        layer.lead_radius = 0.0
        layer.lead_length = 0.0
        layer.lead_out_mode = 'off'
        layer.overcut_enabled = False
        layer.overcut_length = 0.0

        project2 = Project(parent)
        project2.load(content, compleet=False)
        self.assertEqual(layer.lead_in_mode, 'radius')
        self.assertAlmostEqual(layer.lead_radius, 12.5)
        self.assertAlmostEqual(layer.lead_length, 4.0)
        self.assertEqual(layer.lead_out_mode, 'straight')
        self.assertTrue(layer.overcut_enabled)
        self.assertAlmostEqual(layer.overcut_length, 3.5)

    def test_the_override_flags_are_saved_and_restored(self):
        separator = g.config.vars.Layer_Options['id_float_separator']
        layer = build_layer(name=separator.join(["MILL", "Lim", "2"]))
        layer.overrideDefaults()
        layer.lead_in_mode_overridden = True
        layer.lead_radius_overridden = True
        layer.lead_length_overridden = True
        layer.lead_out_mode_overridden = True
        layer.overcut_length_overridden = True
        parent = _ParentStub([layer])

        project = Project(parent)
        content = project.export(compleet=False)
        self.assertIn("'lead_in_mode_overridden': True", content)
        self.assertIn("'lead_radius_overridden': True", content)
        self.assertIn("'lead_length_overridden': True", content)
        self.assertIn("'overcut_length_overridden': True", content)

        layer.lead_in_mode_overridden = False
        layer.lead_radius_overridden = False
        layer.lead_length_overridden = False
        layer.lead_out_mode_overridden = False
        layer.overcut_length_overridden = False

        project2 = Project(parent)
        project2.load(content, compleet=False)
        self.assertTrue(layer.lead_in_mode_overridden)
        self.assertTrue(layer.lead_radius_overridden)
        self.assertTrue(layer.lead_length_overridden)
        self.assertTrue(layer.lead_out_mode_overridden)
        self.assertTrue(layer.overcut_length_overridden)

    def test_an_old_project_file_is_loaded_with_the_defaults(self):
        layer = build_layer()
        parent = _ParentStub([layer])
        project = Project(parent)
        content = project.export(compleet=False)

        # Remove the new fields: this is a project file of an older version.
        for key in ("'lead_in_mode':", "'lead_radius':", "'lead_length':",
                    "'lead_out_mode':",
                    "'overcut_enabled':", "'overcut_length':",
                    "'lead_in_mode_overridden':",
                    "'lead_radius_overridden':",
                    "'lead_length_overridden':",
                    "'lead_out_mode_overridden':",
                    "'overcut_length_overridden':"):
            index = content.find(key)
            self.assertTrue(index > 0, key)
            end = content.find(",", index) + 1
            content = content[:index] + content[end:]

        project2 = Project(parent)
        project2.load(content, compleet=False)
        # The defaults of the program are used, not an invalid mode.
        self.assertEqual(layer.lead_in_mode, 'default')
        self.assertEqual(layer.get_lead_in_mode(),
                         g.config.vars.Lead_In_Out['lead_in_mode'])
        # The radius and the length are the values of the tool of the layer.
        tool = g.config.vars.Tool_Parameters[str(layer.tool_nr)]
        self.assertAlmostEqual(layer.lead_radius, tool['lead_radius'])
        self.assertAlmostEqual(layer.lead_length, tool['lead_length'])
        self.assertEqual(layer.lead_out_mode, 'default')
        # The overcut is a setting of the layer: the layer uses the standard
        # of the configuration file.
        self.assertEqual(layer.overcut_enabled, 'default')
        self.assertEqual(layer.get_overcut_enabled(),
                         g.config.vars.Lead_In_Out['overcut_enabled'])
        # The length of the overcut is the value of the tool of the layer.
        self.assertAlmostEqual(layer.overcut_length, tool['overcut_length'])
        self.assertFalse(layer.lead_in_mode_overridden)
        self.assertFalse(layer.overcut_length_overridden)


class TestGlobalValuesAndOverrides(ProjectRoundtripBase):
    """The global values and the overrides of the layers."""

    def setUp(self):
        ProjectRoundtripBase.setUp(self)
        from dxf2gcode.gui.treehandling import update_lead_move_values
        self.update = update_lead_move_values

    def test_the_overrides_survive_a_config_change(self):
        separator = g.config.vars.Layer_Options['id_float_separator']
        layer = build_layer(name=separator.join(["MILL", "Lim", "2", "Lr",
                                                 "8.0"]))
        layer.overrideDefaults()
        self.assertEqual(layer.lead_in_mode, 'straight')
        self.assertAlmostEqual(layer.lead_radius, 8.0)

        g.config.vars.Lead_In_Out['lead_in_mode'] = 'radius'
        self.update(layer)
        # The layer keeps its own method and its own radius.
        self.assertEqual(layer.lead_in_mode, 'straight')
        self.assertAlmostEqual(layer.lead_radius, 8.0)

    def test_the_values_are_not_converted_twice(self):
        # The length of the overcut is defined per tool: the values of the
        # tools table are in the unit of the drawing (they are converted with
        # the unit of the configuration file).
        g.config.tool_units_metric = 1
        g.config.metric = 0
        g.config.vars.Tool_Parameters['1']['overcut_length'] = 25.4
        layer = build_layer()
        self.update(layer)
        self.assertAlmostEqual(layer.overcut_length, 25.4)
        # A second update must not convert the value again.
        self.update(layer)
        self.assertAlmostEqual(layer.overcut_length, 25.4)


if __name__ == "__main__":
    unittest.main(verbosity=2)
