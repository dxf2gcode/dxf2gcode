# -*- coding: utf-8 -*-
"""
Tests of the common geometric parameters of the lead in and the lead out:
the radius at the workpiece and the length of the straight part are defined
per tool and they are used by both directions. The methods (none, straight,
circle, straight with circle) are selected independently for the lead in and
for the lead out.

Run from the repository root:

    python -m unittest discover -s tests -t tests -p "dxf2gcode_leadmove_common_test.py" -v
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
from dxf2gcode.core.leadmove import (LEAD_DEFAULT, LEAD_OFF, LEAD_RADIUS,  # noqa: E402
                                     LEAD_STARTMOVE, LEAD_STRAIGHT,
                                     validate_lead_move)
from dxf2gcode.globals.config import MyConfig  # noqa: E402
from dxf2gcode.Qt.QtWidgets import QApplication  # noqa: E402

from dxf2gcode_leadmove_golden_test import build_shape, export_gcode  # noqa: E402
from dxf2gcode_leadmove_function_test import (  # noqa: E402
    LeadMoveTestBase, export_with_errors)

_APP = None


def _app():
    global _APP
    if _APP is None:
        _APP = QApplication.instance() or QApplication([])
    return _APP


class TestCommonParameters(LeadMoveTestBase):
    """The radius and the length are common to both directions."""

    def test_the_layer_has_only_one_radius_and_one_length(self):
        layer = LayerContent(nr=1, name="L1", shapes=[])
        # The values come from the tool of the layer.
        tool = g.config.vars.Tool_Parameters['1']
        self.assertAlmostEqual(layer.lead_radius, tool['lead_radius'])
        self.assertAlmostEqual(layer.lead_length, tool['lead_length'])
        # There is no separate value for the lead in and for the lead out.
        self.assertFalse(hasattr(layer, 'lead_in_radius'))
        self.assertFalse(hasattr(layer, 'lead_out_radius'))
        self.assertFalse(hasattr(layer, 'lead_in_length'))
        self.assertFalse(hasattr(layer, 'lead_out_length'))

    def test_the_tool_table_has_only_one_radius_and_one_length(self):
        tool = g.config.vars.Tool_Parameters['1']
        self.assertIn('lead_radius', tool)
        self.assertIn('lead_length', tool)
        self.assertNotIn('lead_in_radius', tool)
        self.assertNotIn('lead_out_radius', tool)

    def test_the_values_do_not_change_with_the_method(self):
        layer = LayerContent(nr=1, name="L1", shapes=[])
        radius = layer.lead_radius
        length = layer.lead_length
        for mode in (LEAD_OFF, LEAD_STRAIGHT, LEAD_RADIUS, LEAD_STARTMOVE):
            layer.lead_in_mode = mode
            layer.lead_out_mode = mode
            self.assertAlmostEqual(layer.lead_radius, radius)
            self.assertAlmostEqual(layer.lead_length, length)

    def test_a_change_of_the_tool_diameter_is_validated_again(self):
        # The radius at the workpiece has to be greater than the radius of
        # the tool: a bigger tool makes the radius invalid.
        layer = LayerContent(nr=1, name="L1", shapes=[])
        layer.tool_diameter = 10.0
        layer.lead_radius = 10.0
        layer.lead_in_mode = LEAD_RADIUS
        ok, errors, warnings = validate_lead_move(layer.tool_diameter,
                                                   layer.lead_radius,
                                                   layer.lead_length,
                                                   layer.lead_in_mode,
                                                   layer.lead_out_mode)
        self.assertTrue(ok)
        self.assertEqual(errors, [])

        layer.tool_diameter = 30.0
        ok, errors, warnings = validate_lead_move(layer.tool_diameter,
                                                   layer.lead_radius,
                                                   layer.lead_length,
                                                   layer.lead_in_mode,
                                                   layer.lead_out_mode)
        self.assertFalse(ok)
        self.assertEqual(errors[0][0], 'lead_radius')

    def test_the_units_are_converted(self):
        layer = LayerContent(nr=1, name="L1", shapes=[])
        layer.lead_radius = 2.0
        layer.lead_length = 3.0
        layer.changeMeasuringUnits(1, 0)
        self.assertAlmostEqual(layer.lead_radius, 2.0 / 25.4)
        self.assertAlmostEqual(layer.lead_length, 3.0 / 25.4)


class TestMethodSelection(LeadMoveTestBase):
    """The methods of the lead in and of the lead out are independent."""

    def test_all_the_methods_can_be_selected_for_both_directions(self):
        layer = LayerContent(nr=1, name="L1", shapes=[])
        for mode in (LEAD_OFF, LEAD_STRAIGHT, LEAD_RADIUS, LEAD_STARTMOVE):
            layer.lead_in_mode = mode
            layer.lead_out_mode = LEAD_OFF
            self.assertEqual(layer.get_lead_in_mode(), mode)
            self.assertEqual(layer.get_lead_out_mode(), LEAD_OFF)
            layer.lead_out_mode = mode
            layer.lead_in_mode = LEAD_OFF
            self.assertEqual(layer.get_lead_in_mode(), LEAD_OFF)
            self.assertEqual(layer.get_lead_out_mode(), mode)

    def test_the_configuration_default_is_used_for_each_direction(self):
        layer = LayerContent(nr=1, name="L1", shapes=[])
        g.config.vars.Lead_In_Out['lead_in_mode'] = LEAD_RADIUS
        g.config.vars.Lead_In_Out['lead_out_mode'] = LEAD_STRAIGHT
        self.assertEqual(layer.get_lead_in_mode(), LEAD_RADIUS)
        self.assertEqual(layer.get_lead_out_mode(), LEAD_STRAIGHT)

    def test_a_change_of_the_global_default_is_followed(self):
        layer = LayerContent(nr=1, name="L1", shapes=[])
        self.assertEqual(layer.lead_in_mode, LEAD_DEFAULT)
        g.config.vars.Lead_In_Out['lead_in_mode'] = LEAD_STRAIGHT
        self.assertEqual(layer.get_lead_in_mode(), LEAD_STRAIGHT)
        # An explicit value of the layer is not affected.
        layer.lead_in_mode = LEAD_RADIUS
        g.config.vars.Lead_In_Out['lead_in_mode'] = LEAD_STRAIGHT
        self.assertEqual(layer.get_lead_in_mode(), LEAD_RADIUS)

    def test_the_export_of_all_the_method_combinations(self):
        # Every combination of the methods has to be exportable (as long as
        # the geometry is valid).
        for lead_in in (LEAD_OFF, LEAD_STRAIGHT, LEAD_RADIUS,
                        LEAD_STARTMOVE):
            for lead_out in (LEAD_OFF, LEAD_STRAIGHT, LEAD_RADIUS,
                             LEAD_STARTMOVE):
                shape, layer = build_shape(
                    closed=True, cut_cor=41,
                    layer_settings=dict(lead_in_mode=lead_in,
                                        lead_out_mode=lead_out,
                                        lead_radius=20.0,
                                        lead_length=5.0))
                gcode, errors = export_with_errors(shape)
                if lead_in == LEAD_OFF:
                    # The lead in 'off' is not possible with G41/G42: the
                    # machine can only build the compensation with a
                    # movement in the XY plane.
                    self.assertEqual(gcode, "")
                    self.assertTrue(errors)
                else:
                    self.assertTrue(gcode, (lead_in, lead_out, errors))
                    self.assertFalse(errors, (lead_in, lead_out, errors))

    def test_an_invalid_geometry_is_reported_and_not_exported(self):
        # The radius at the workpiece is smaller than the tool radius.
        shape, layer = build_shape(
            closed=True, cut_cor=41,
            layer_settings=dict(lead_in_mode=LEAD_RADIUS, lead_radius=1.0))
        gcode, errors = export_with_errors(shape)
        self.assertEqual(gcode, "")
        self.assertTrue(errors)
        self.assertIn("tool radius", errors[0])

    def test_the_preview_matches_the_export(self):
        for lead_out in (LEAD_STRAIGHT, LEAD_RADIUS, LEAD_STARTMOVE):
            shape, layer = build_shape(
                closed=True, cut_cor=41,
                layer_settings=dict(lead_out_mode=lead_out,
                                    lead_radius=20.0,
                                    lead_length=5.0))
            geos = list(getattr(shape.stmove, 'exit_geos', []))
            self.assertTrue(geos, lead_out)
            gcode = export_gcode(shape, layer)
            exported = None
            for line in gcode.splitlines():
                fields = line.split()
                if not fields or fields[0] not in ("G0", "G1", "G2", "G3"):
                    continue
                arguments = fields[1:]
                values = {}
                for index in range(0, len(arguments) - 1, 2):
                    values[arguments[index]] = float(arguments[index + 1])
                if "X" in values and "Y" in values:
                    exported = (values["X"], values["Y"])
            self.assertIsNotNone(exported)
            self.assertAlmostEqual(round(geos[-1].Pe.x, 3), exported[0], 3)
            self.assertAlmostEqual(round(geos[-1].Pe.y, 3), exported[1], 3)


class TestConfigurationMigration(LeadMoveTestBase):
    """The configuration files of the previous versions are still loadable."""

    def _write_config(self, content):
        path = os.path.join(self.tmp, "config", "config.cfg")
        with open(path, "w") as config_file:
            config_file.write(content)
        return path

    def test_the_old_start_radius_is_migrated(self):
        # The old start_radius was the radius of the tool center path of the
        # start move: the new lead_radius is the radius at the workpiece, so
        # the radius of the tool is added to it. The geometry does not change.
        self.config.save_varspace()
        path = os.path.join(self.tmp, "config", "config.cfg")
        with open(path) as config_file:
            content = config_file.read()
        content = content.replace("lead_radius = 1.2", "start_radius = 0.2")
        content = content.replace("lead_length = 1.0", "")
        with open(path, "w") as config_file:
            config_file.write(content)

        config = MyConfig()
        tool = config.vars.Tool_Parameters['1']
        # 0.2 (the tool center path) + 1.0 (the radius of the tool)
        self.assertAlmostEqual(tool['lead_radius'], 1.2)
        # The length of the straight part was the radius of the tool.
        self.assertAlmostEqual(tool['lead_length'], 1.0)
        # The old value is not used any more.
        self.assertNotIn('start_radius', tool)

    def test_the_old_lead_in_out_options_are_removed(self):
        self.config.save_varspace()
        path = os.path.join(self.tmp, "config", "config.cfg")
        with open(path) as config_file:
            content = config_file.read()
        content = content.replace(
            "overcut_length = 0.0",
            "overcut_length = 0.0\nlead_in_radius = 12.0\n"
            "lead_out_radius = 13.0")
        with open(path, "w") as config_file:
            config_file.write(content)

        config = MyConfig()
        self.assertNotIn('lead_in_radius', config.vars.Lead_In_Out)
        self.assertNotIn('lead_out_radius', config.vars.Lead_In_Out)

    def test_an_old_config_file_is_loadable(self):
        path = self._write_config(
            "[General]\n"
            "tool_units_metric = 0\n"
            "\n"
            "[Tool_Parameters]\n"
            "[[1]]\n"
            "diameter = 2.0\n"
            "speed = 6000\n"
            "start_radius = 0.2\n"
            "milling_offset = 0.0\n"
            "\n"
            "[Lead_In_Out]\n"
            "lead_in_mode = startmove\n"
            "lead_in_radius = 12.0\n"
            "lead_out_mode = off\n"
            "lead_out_radius = 13.0\n"
            "overcut_enabled = False\n"
            "overcut_length = 0.0\n")
        config = MyConfig()
        self.assertEqual(config.vars.Lead_In_Out['lead_in_mode'],
                         LEAD_STARTMOVE)
        self.assertEqual(config.vars.Lead_In_Out['lead_out_mode'], LEAD_OFF)
        self.assertFalse(config.vars.Lead_In_Out['overcut_enabled'])
        tool = config.vars.Tool_Parameters['1']
        self.assertAlmostEqual(tool['lead_radius'], 1.2)
        self.assertAlmostEqual(tool['lead_length'], 1.0)

    def test_an_old_config_file_without_a_diameter_is_migrated(self):
        # The diameter is missing: it is filled with the default of the
        # configuration file before the start radius is converted.
        path = self._write_config(
            "[General]\n"
            "tool_units_metric = 0\n"
            "\n"
            "[Tool_Parameters]\n"
            "[[1]]\n"
            "start_radius = 0.2\n"
            "\n"
            "[Lead_In_Out]\n"
            "lead_in_mode = startmove\n")
        config = MyConfig()
        tool = config.vars.Tool_Parameters['1']
        # The default diameter of the tool is 2.0 (the radius of the tool is
        # 1.0): 0.2 + 1.0
        self.assertAlmostEqual(tool['diameter'], 2.0)
        self.assertAlmostEqual(tool['lead_radius'], 1.2)
        self.assertAlmostEqual(tool['lead_length'], 1.0)


class TestToolTableValidation(LeadMoveTestBase):
    """The validation of the tools table of the configuration window."""

    def setUp(self):
        LeadMoveTestBase.setUp(self)
        _app()
        from dxf2gcode.gui.configwindow import CfgTableToolParameters
        self.table = CfgTableToolParameters("tools")
        self.table.setSpec({'string_list': ['', 'diameter', 'speed',
                                            'lead_radius', 'lead_length',
                                            'milling_offset'],
                            'comment': ''})
        self.table.appendLine(["1", "10.0", "6000", "20.0", "5.0", "0.0"])
        self.table.appendLine(["2", "10.0", "6000", "3.0", "5.0", "0.0"])

    def tearDown(self):
        LeadMoveTestBase.tearDown(self)

    def test_a_valid_table_is_accepted(self):
        g.config.vars.Lead_In_Out['lead_in_mode'] = LEAD_RADIUS
        g.config.vars.Lead_In_Out['lead_out_mode'] = LEAD_STRAIGHT
        # The radius of the second tool is valid.
        self.table.setCellValue(1, 3, 6.0)
        ok, message = self.table.validateValue()
        self.assertTrue(ok, message)

    def test_a_radius_which_is_too_small_is_rejected(self):
        g.config.vars.Lead_In_Out['lead_in_mode'] = LEAD_RADIUS
        g.config.vars.Lead_In_Out['lead_out_mode'] = LEAD_OFF
        ok, message = self.table.validateValue()
        self.assertFalse(ok)
        self.assertIn("radius of the tool", message)
        # The tool with the invalid radius is named in the message.
        self.assertIn("2", message)

    def test_an_unused_radius_does_not_prevent_the_table(self):
        # Neither the lead in nor the lead out uses a circle: the radius is
        # not needed, so it must not be validated.
        g.config.vars.Lead_In_Out['lead_in_mode'] = LEAD_STRAIGHT
        g.config.vars.Lead_In_Out['lead_out_mode'] = LEAD_OFF
        ok, message = self.table.validateValue()
        self.assertTrue(ok, message)


class TestTreeGui(LeadMoveTestBase):
    """The two dropdowns of the mill settings (lead in / lead out)."""

    def setUp(self):
        LeadMoveTestBase.setUp(self)
        from dxf2gcode_parameter_state_test import _Harness, _make_shape
        self.shape = _make_shape(0)
        self.layer = self.shape.parentLayer
        self.harness = _Harness([self.layer])
        self.harness.select([self.shape])
        self.th = self.harness.th

    def tearDown(self):
        LeadMoveTestBase.tearDown(self)

    def _index_of(self, combo, mode):
        index = combo.findData(mode)
        self.assertGreaterEqual(index, 0, mode)
        return index

def test_the_combo_boxes_offer_all_the_methods(self):
        # The configuration default is not an entry of the comboboxes: the
        # method which is really used is shown. The 'radius' method is not
        # selectable for the lead in (it is merged into the 'startmove'), it
        # is only selectable for the lead out.
        lead_in_data = [self.th.ui.leadInComboBox.itemData(i)
                        for i in range(self.th.ui.leadInComboBox.count())]
        self.assertEqual(lead_in_data, [LEAD_OFF, LEAD_STRAIGHT,
                                        LEAD_STARTMOVE])
        lead_out_data = [self.th.ui.leadOutComboBox.itemData(i)
                         for i in range(self.th.ui.leadOutComboBox.count())]
        self.assertEqual(lead_out_data, [LEAD_OFF, LEAD_STRAIGHT,
                                          LEAD_RADIUS, LEAD_STARTMOVE])

    def test_the_configuration_default_is_used(self):
        # The layer uses the configuration default: the global default is
        # shown and it is used by the export. The 'radius' method of the lead
        # in is not selectable any more: it is mapped to the 'startmove'.
        g.config.vars.Lead_In_Out['lead_in_mode'] = LEAD_RADIUS
        g.config.vars.Lead_In_Out['lead_out_mode'] = LEAD_STRAIGHT
        self.harness.select([self.shape])
        self.assertEqual(self.layer.get_lead_in_mode(), LEAD_RADIUS)
        self.assertEqual(self.layer.get_lead_out_mode(), LEAD_STRAIGHT)
        # The combobox shows the method which is really used.
        self.assertEqual(self.th.ui.leadInComboBox.currentData(),
                         LEAD_STARTMOVE)
        self.assertEqual(self.th.ui.leadOutComboBox.currentData(),
                         LEAD_STRAIGHT)

    def test_the_directions_are_independent(self):
        # The lead in is set to a circle, the lead out keeps its value. The
        # 'radius' method of the lead in is not selectable any more: it is
        # mapped to the 'startmove'.
        self.shape.lead_out_mode = LEAD_STRAIGHT
        self.harness.select([self.shape])
        index = self._index_of(self.th.ui.leadInComboBox,
                               LEAD_STARTMOVE)
        self.th.ui.leadInComboBox.setCurrentIndex(index)
        self.th.leadInUpdate(index)
        self.assertEqual(self.shape.lead_in_mode, LEAD_STARTMOVE)
        self.assertEqual(self.shape.lead_out_mode, LEAD_STRAIGHT)

        index = self._index_of(self.th.ui.leadOutComboBox, LEAD_OFF)
        self.th.ui.leadOutComboBox.setCurrentIndex(index)
        self.th.leadOutUpdate(index)
        self.assertEqual(self.shape.lead_in_mode, LEAD_STARTMOVE)
        # The lead out of the configuration file is 'off': the shape follows
        # the standard again.
        self.assertEqual(self.shape.lead_out_mode, LEAD_DEFAULT)
        self.assertEqual(self.shape.get_lead_out_mode(), LEAD_OFF)

    def test_the_common_values_are_not_changed(self):
        radius = self.layer.lead_radius
        length = self.layer.lead_length
        for mode in (LEAD_OFF, LEAD_STRAIGHT, LEAD_STARTMOVE):
            index = self._index_of(self.th.ui.leadInComboBox, mode)
            self.th.ui.leadInComboBox.setCurrentIndex(index)
            self.th.leadInUpdate(index)
            # The value of the configuration file is not an own value of the
            # shape: it follows the standard.
            if mode == g.config.vars.Lead_In_Out['lead_in_mode']:
                self.assertEqual(self.shape.lead_in_mode, LEAD_DEFAULT)
            else:
                self.assertEqual(self.shape.lead_in_mode, mode)
            self.assertAlmostEqual(self.layer.lead_radius, radius)
            self.assertAlmostEqual(self.layer.lead_length, length)

    def test_selecting_the_standard_value_follows_the_standard_again(self):
        # The configuration default is not an entry of the combobox: if the
        # value of the configuration file is selected, the shape follows the
        # standard again (like the milling depth). The 'radius' method of the
        # lead in is not selectable any more: it is mapped to the 'startmove'.
        g.config.vars.Lead_In_Out['lead_in_mode'] = LEAD_STRAIGHT
        self.shape.lead_in_mode = LEAD_RADIUS
        self.harness.select([self.shape])
        index = self._index_of(self.th.ui.leadInComboBox, LEAD_STRAIGHT)
        self.th.ui.leadInComboBox.setCurrentIndex(index)
        self.th.leadInUpdate(index)
        self.assertEqual(self.shape.lead_in_mode, LEAD_DEFAULT)
        self.assertFalse(self.shape.lead_in_mode_overridden)
        # The global default is used.
        g.config.vars.Lead_In_Out['lead_in_mode'] = LEAD_RADIUS
        self.assertEqual(self.shape.get_lead_in_mode(), LEAD_RADIUS)

    def test_only_the_changed_shape_gets_its_own_value(self):
        # The value is only changed for the selected shape, the other shapes
        # keep the standard of the configuration file.
        from dxf2gcode_parameter_state_test import _make_shape
        g.config.vars.Lead_In_Out['lead_in_mode'] = LEAD_STARTMOVE
        other_shape = _make_shape(1)
        self.harness.select([self.shape])
        index = self._index_of(self.th.ui.leadInComboBox,
                               LEAD_STARTMOVE)
        self.th.ui.leadInComboBox.setCurrentIndex(index)
        self.th.leadInUpdate(index)
        self.assertEqual(self.shape.lead_in_mode, LEAD_STARTMOVE)
        # The other shape is not touched.
        self.assertEqual(other_shape.lead_in_mode, LEAD_DEFAULT)
        self.assertEqual(other_shape.get_lead_in_mode(), LEAD_STARTMOVE)

    def test_two_shapes_of_one_layer_have_separate_lead_modes(self):
        # Two contours in one layer: the lead in of one contour can be
        # changed without touching the other contour.
        from dxf2gcode_parameter_state_test import _Harness, _make_shape
        from dxf2gcode.core.layercontent import LayerContent
        g.config.vars.Lead_In_Out['lead_in_mode'] = LEAD_OFF
        first = _make_shape(0)
        second = _make_shape(1)
        layer = LayerContent(0, "L", [first, second])
        first.parentLayer = layer
        second.parentLayer = layer
        harness = _Harness([layer])
        harness.select([first])
        index = self._index_of(harness.th.ui.leadInComboBox,
                               LEAD_STARTMOVE)
        harness.th.ui.leadInComboBox.setCurrentIndex(index)
        harness.th.leadInUpdate(index)
        self.assertEqual(first.lead_in_mode, LEAD_STARTMOVE)
        # The other contour of the same layer is not touched.
        self.assertEqual(second.lead_in_mode, LEAD_DEFAULT)
        self.assertEqual(second.get_lead_in_mode(), LEAD_OFF)


if __name__ == "__main__":
    unittest.main(verbosity=2)
