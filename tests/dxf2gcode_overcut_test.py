# -*- coding: utf-8 -*-
"""
Tests of the overcut.

The overcut is a setting of the shape (like the method of the lead in and of
the lead out): it either uses the standard of the configuration file, it is
switched off or it is active. The length of the overcut is defined per tool
(see the tools table).

The tests check the storage of the values, the precedence of the global
standard and of the own value of a shape, the tool change, the unit
conversion, the toolpath of closed and open contours, the preview in the
canvas and the backwards compatibility.

Run from the repository root:

    python -m unittest discover -s tests -t tests -p "dxf2gcode_overcut_test.py" -v
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
from dxf2gcode.core.leadmove import (OVERCUT_DEFAULT, OVERCUT_OFF,  # noqa: E402
                                     OVERCUT_ON, resolve_overcut)
from dxf2gcode.globals.config import MyConfig  # noqa: E402
from dxf2gcode.Qt.QtWidgets import QApplication  # noqa: E402

from dxf2gcode_leadmove_golden_test import (GoldenTestBase, build_shape,  # noqa: E402
                                           export_gcode)
from dxf2gcode_leadmove_function_test import export_with_errors  # noqa: E402

_APP = None


def _app():
    global _APP
    if _APP is None:
        _APP = QApplication.instance() or QApplication([])
    return _APP


class OvercutTestBase(GoldenTestBase):

    def setUp(self):
        GoldenTestBase.setUp(self)
        _app()
        from dxf2gcode.gui.treehandling import update_lead_move_values
        self.update = update_lead_move_values

    def tearDown(self):
        GoldenTestBase.tearDown(self)

    def set_config_value(self, section, key, value):
        """
        Change a value of the configuration file. The values of the
        configuration file are only read when the configuration is updated.
        @param section: the name of the section
        @param key: the name of the value
        @param value: the new value
        """
        g.config.var_dict[section][key] = value
        g.config.update_config()

    def set_tool_value(self, tool, key, value):
        """
        Change a value of the tools table.
        @param tool: the number of the tool
        @param key: the name of the value
        @param value: the new value
        """
        g.config.var_dict['Tool_Parameters'][str(tool)][key] = value
        g.config.update_config()

    def shape_with(self, overcut_enabled=None, overcut_length=None,
                   closed=True, tool_nr=None):
        """
        A closed contour with the given overcut settings.
        """
        settings = {}
        if overcut_enabled is not None:
            settings['overcut_enabled'] = overcut_enabled
        if overcut_length is not None:
            settings['overcut_length'] = overcut_length
        shape, layer = build_shape(closed=closed, cut_cor=41,
                                   layer_settings=settings)
        if tool_nr is not None:
            layer.tool_nr = tool_nr
        return shape, layer

class TestOvercutValues(OvercutTestBase):
    """The storage of the overcut values."""

    def test_the_length_is_stored_per_tool(self):
        tool = g.config.vars.Tool_Parameters['1']
        self.assertIn('overcut_length', tool)
        self.set_tool_value(1, 'overcut_length', 12.5)
        self.config.save_varspace()
        config = MyConfig()
        self.assertAlmostEqual(
            config.vars.Tool_Parameters['1']['overcut_length'], 12.5)

    def test_the_activation_is_a_setting_of_the_shape(self):
        layer = LayerContent(nr=1, name="L1", shapes=[])
        # The shape uses the standard of the configuration file.
        self.assertEqual(layer.overcut_enabled, OVERCUT_DEFAULT)
        # The standard of the configuration file is used.
        self.set_config_value('Lead_In_Out', 'overcut_enabled', True)
        self.assertTrue(layer.get_overcut_enabled())
        self.set_config_value('Lead_In_Out', 'overcut_enabled', False)
        self.assertFalse(layer.get_overcut_enabled())
        # An own value of the shape is not overwritten by the standard.
        layer.overcut_enabled = OVERCUT_ON
        self.set_config_value('Lead_In_Out', 'overcut_enabled', False)
        self.assertTrue(layer.get_overcut_enabled())
        layer.overcut_enabled = OVERCUT_OFF
        self.set_config_value('Lead_In_Out', 'overcut_enabled', True)
        self.assertFalse(layer.get_overcut_enabled())

    def test_the_shape_has_its_own_overcut_setting(self):
        self.set_config_value('Lead_In_Out', 'overcut_enabled', False)
        shape, layer = self.shape_with(overcut_length=50.0)
        # The standard of the configuration file is off.
        self.assertFalse(shape.get_overcut_enabled())
        # The own value wins over the standard of the configuration file.
        shape.overcut_enabled = OVERCUT_ON
        self.assertTrue(shape.get_overcut_enabled())
        # The shape follows the layer if it has no own value.
        shape.overcut_enabled = OVERCUT_DEFAULT
        layer.overcut_enabled = OVERCUT_ON
        self.assertTrue(shape.get_overcut_enabled())

    def test_a_closed_and_an_open_contour_of_one_layer_are_separated(self):
        # Two contours in one layer: the overcut can be switched on for the
        # closed contour only. The open contour ignores it (no error) and is
        # milled without an overcut.
        self.set_config_value('Lead_In_Out', 'overcut_enabled', False)
        closed, layer = self.shape_with(overcut_length=50.0)
        open_shape, _ = build_shape(
            closed=False, cut_cor=41,
            layer_settings=dict(overcut_length=50.0))
        open_shape.parentLayer = layer
        layer.shapes.append(open_shape)
        closed.overcut_enabled = OVERCUT_ON
        self.assertTrue(closed.get_overcut_enabled())
        self.assertFalse(open_shape.get_overcut_enabled())
        self.assertEqual(
            export_gcode(closed, layer).count("G1 X  50.000 Y   0.000"), 1)
        open_gcode, errors = export_with_errors(open_shape)
        self.assertFalse(errors)
        self.assertEqual(open_gcode.count("G1 X  50.000 Y   0.000"), 0)

    def test_the_length_comes_from_the_tool(self):
        self.set_tool_value(1, 'overcut_length', 7.0)
        layer = LayerContent(nr=1, name="L1", shapes=[])
        self.assertAlmostEqual(layer.overcut_length, 7.0)
        self.update(layer)
        self.assertAlmostEqual(layer.overcut_length, 7.0)
        # A length which was set by a layer name is not overwritten.
        layer.overcut_length = 3.0
        layer.overcut_length_overridden = True
        self.update(layer)
        self.assertAlmostEqual(layer.overcut_length, 3.0)

    def test_the_tool_change_uses_the_new_length(self):
        self.set_tool_value(1, 'overcut_length', 7.0)
        self.set_tool_value(2, 'overcut_length', 20.0)
        layer = LayerContent(nr=1, name="L1", shapes=[])
        self.assertAlmostEqual(layer.overcut_length, 7.0)
        layer.tool_nr = 2
        self.update(layer)
        self.assertAlmostEqual(layer.overcut_length, 20.0)

    def test_the_units_are_converted_without_a_double_conversion(self):
        # The values of the tools table are converted with the unit of the
        # drawing (see MyConfig.update_tool_values).
        self.set_tool_value(1, 'overcut_length', 25.4)
        g.config.tool_units_metric = 1
        g.config.metric = 0
        g.config.update_tool_values()
        self.assertAlmostEqual(
            g.config.vars.Tool_Parameters['1']['overcut_length'], 1.0)
        layer = LayerContent(nr=1, name="L1", shapes=[])
        self.update(layer)
        self.assertAlmostEqual(layer.overcut_length, 1.0)
        # A second update must not convert the value again.
        self.update(layer)
        self.assertAlmostEqual(layer.overcut_length, 1.0)


class TestOvercutResolution(unittest.TestCase):
    """The resolution of the overcut of a shape."""

    def test_the_standard_is_used(self):
        self.assertTrue(resolve_overcut(OVERCUT_DEFAULT, True))
        self.assertFalse(resolve_overcut(OVERCUT_DEFAULT, False))

    def test_the_own_value_wins(self):
        self.assertTrue(resolve_overcut(OVERCUT_ON, False))
        self.assertFalse(resolve_overcut(OVERCUT_OFF, True))

    def test_the_old_project_files_are_accepted(self):
        # The project files of the previous versions stored a bool.
        self.assertTrue(resolve_overcut(True, False))
        self.assertFalse(resolve_overcut(False, True))


class TestOvercutToolpath(OvercutTestBase):
    """The toolpath with and without the overcut."""

    def test_a_closed_contour_with_the_overcut(self):
        self.set_config_value('Lead_In_Out', 'overcut_enabled', True)
        shape, layer = self.shape_with(overcut_length=50.0)
        self.assertTrue(shape.stmove.exit_geos)
        gcode = export_gcode(shape, layer)
        # The overcut continues the cut along the contour.
        self.assertEqual(gcode.count("G1 X  50.000 Y   0.000"), 1)

    def test_a_closed_contour_with_the_overcut_and_the_lead_out(self):
        # The overcut continues the cut along the contour and the lead out
        # starts at the end of the overcut - both in the same tool path.
        shape, layer = build_shape(
            closed=True, cut_cor=41,
            layer_settings=dict(lead_out_mode='radius', lead_radius=20.0,
                                overcut_enabled=True, overcut_length=50.0))
        self.assertTrue(shape.stmove.exit_geos)
        gcode = export_gcode(shape, layer)
        # The overcut continues the cut along the contour and the lead out
        # starts at its end.
        self.assertEqual(gcode.count("G1 X  50.000 Y   0.000"), 1)

    def test_a_closed_contour_without_the_overcut(self):
        self.set_config_value('Lead_In_Out', 'overcut_enabled', False)
        shape, layer = self.shape_with(overcut_length=50.0)
        self.assertFalse(shape.stmove.exit_geos)
        gcode = export_gcode(shape, layer)
        self.assertEqual(gcode.count("G1 X  50.000 Y   0.000"), 0)

    def test_the_shape_can_switch_the_overcut_off(self):
        self.set_config_value('Lead_In_Out', 'overcut_enabled', True)
        shape, layer = self.shape_with(overcut_enabled=OVERCUT_OFF,
                                      overcut_length=50.0)
        self.assertFalse(shape.stmove.exit_geos)
        gcode = export_gcode(shape, layer)
        self.assertEqual(gcode.count("G1 X  50.000 Y   0.000"), 0)

    def test_the_shape_can_switch_the_overcut_on(self):
        self.set_config_value('Lead_In_Out', 'overcut_enabled', False)
        shape, layer = self.shape_with(overcut_enabled=OVERCUT_ON,
                                      overcut_length=50.0)
        self.assertTrue(shape.stmove.exit_geos)
        gcode = export_gcode(shape, layer)
        self.assertEqual(gcode.count("G1 X  50.000 Y   0.000"), 1)

    def test_an_open_contour_ignores_the_overcut(self):
        # The overcut is only possible for closed contours: on an open contour
        # it is silently ignored (no error), the contour is milled normally.
        self.set_config_value('Lead_In_Out', 'overcut_enabled', True)
        shape, layer = self.shape_with(closed=False, overcut_length=50.0)
        gcode, errors = export_with_errors(shape)
        self.assertTrue(gcode)
        self.assertFalse(errors)
        self.assertEqual(gcode.count("G1 X  50.000 Y   0.000"), 0)

    def test_the_preview_matches_the_export(self):
        self.set_config_value('Lead_In_Out', 'overcut_enabled', True)
        shape, layer = self.shape_with(overcut_length=50.0)
        exit_geos = list(shape.stmove.exit_geos)
        self.assertTrue(exit_geos)
        gcode = export_gcode(shape, layer)
        # The last position of the G-Code is the end of the overcut.
        positions = []
        for line in gcode.splitlines():
            fields = line.split()
            if not fields or fields[0] not in ("G0", "G1", "G2", "G3"):
                continue
            values = {}
            for index in range(1, len(fields) - 1, 2):
                try:
                    values[fields[index]] = float(fields[index + 1])
                except ValueError:
                    pass
            if "X" in values and "Y" in values:
                positions.append((values["X"], values["Y"]))
        self.assertAlmostEqual(positions[-1][0], exit_geos[-1].Pe.x, 6)
        self.assertAlmostEqual(positions[-1][1], exit_geos[-1].Pe.y, 6)


class TestOvercutMigration(OvercutTestBase):
    """The configuration files of the previous versions."""

    def test_the_global_length_is_moved_to_the_tools(self):
        path = os.path.join(self.tmp, "config", "config.cfg")
        self.config.save_varspace()
        with open(path) as config_file:
            content = config_file.read()
        # A configuration file of the previous version: the length of the
        # overcut was a global value and the tools did not have one.
        content = content.replace(
            "[Lead_In_Out]",
            "[Lead_In_Out]\novercut_length = 12.0")
        content = "\n".join(
            [line for line in content.splitlines()
             if line.strip() != "overcut_length = 0.0"]) + "\n"
        with open(path, "w") as config_file:
            config_file.write(content)

        config = MyConfig()
        # The global value is removed.
        self.assertNotIn('overcut_length', config.vars.Lead_In_Out)
        # The tools take it over: the behaviour does not change.
        for tool in config.vars.Tool_Parameters:
            self.assertAlmostEqual(config.vars.Tool_Parameters[tool]
                                  ['overcut_length'], 12.0)

    def test_the_tools_keep_their_own_length(self):
        path = os.path.join(self.tmp, "config", "config.cfg")
        self.config.save_varspace()
        with open(path) as config_file:
            content = config_file.read()
        content = content.replace(
            "[Lead_In_Out]",
            "[Lead_In_Out]\novercut_length = 12.0")
        # The first tool has its own length, the other tools do not have one
        # (a configuration file of the previous version).
        lines = content.splitlines()
        result = []
        in_tool_1 = False
        for line in lines:
            if line.strip().startswith('[['):
                in_tool_1 = line.strip() == '[[1]]'
            if in_tool_1 and line.strip() == 'overcut_length = 0.0':
                result.append('overcut_length = 5.0')
                continue
            if not in_tool_1 and line.strip() == 'overcut_length = 0.0':
                continue
            result.append(line)
        with open(path, "w") as config_file:
            config_file.write("\n".join(result) + "\n")

        config = MyConfig()
        # The tool which has its own value keeps it.
        self.assertAlmostEqual(config.vars.Tool_Parameters['1']
                              ['overcut_length'], 5.0)
        # The other tools take over the global value.
        self.assertAlmostEqual(config.vars.Tool_Parameters['2']
                              ['overcut_length'], 12.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
