"""K3: retain input precision through settings, planning and export."""

import os
import re
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'source'))

import dxf2gcode.bootstrap.runtime_state as g
from dxf2gcode.adapters.config.runtime_config import MyConfig
from dxf2gcode.presentation.qt.configwindow import CfgDoubleSpinBox, ConfigWindow
from dxf2gcode.presentation.qt.qt_compat.QtCore import QLocale
from dxf2gcode.presentation.qt.qt_compat.QtWidgets import QApplication, QMessageBox
from dxf2gcode.presentation.qt.qt_compat import PYQT_VERSION

if PYQT_VERSION == 6:
    from PyQt6.QtTest import QTest
else:
    from PyQt5.QtTest import QTest

_APP = QApplication.instance() or QApplication([])


class TestNumericPrecision(unittest.TestCase):
    def setUp(self):
        self.old_folder, self.old_config = g.folder, g.config
        self.old_window = g.window
        g.window = None
        self.directory = tempfile.TemporaryDirectory(prefix='d2g_precision_')
        g.folder = self.directory.name
        g.config = MyConfig()

    def tearDown(self):
        g.folder, g.config = self.old_folder, self.old_config
        g.window = self.old_window
        self.directory.cleanup()

    def test_invalid_configuration_shows_error_without_applying_changes(self):
        config = g.config
        dialog = ConfigWindow(config.makeConfigWidgets(), config.var_dict,
                              config.var_dict.configspec)
        messages = []

        def close_message(box):
            messages.append((box.icon(), box.text()))
            return 0

        with patch.object(dialog, 'validateConfiguration',
                          return_value=(False, 'invalid depth')), \
                patch.object(dialog, 'updateConfiguration') as update, \
                patch.object(QMessageBox, 'exec', new=close_message):
            dialog.applyChanges()
            dialog.accept()
            update.assert_not_called()
        self.assertEqual(len(messages), 2)
        for icon, text in messages:
            self.assertEqual(icon, QMessageBox.Icon.Critical)
            self.assertIn('invalid depth', text)
        dialog.close()

    def test_display_precision_does_not_limit_real_widget_values(self):
        widget = CfgDoubleSpinBox('Depth')
        self.assertGreaterEqual(widget.spinbox.decimals(), 17)
        for value in (.015, .005, .0005, -.015, -.005, -.0005, 25.4005):
            with self.subTest(value=value):
                widget.setValue(value)
                self.assertEqual(widget.getValue(), value)
                self.assertEqual(widget.spinbox.cleanText().replace(',', '.'), format(value, '.3f'))

    def test_display_rounding_preserves_original_until_edit_or_step(self):
        widget = CfgDoubleSpinBox('Depth')
        widget.spinbox.setLocale(QLocale('en_US'))
        widget.setValue(-.01234567)
        self.assertEqual(widget.spinbox.cleanText(), '-0.012')
        self.assertEqual(widget.getValue(), -.01234567)
        widget.spinbox.lineEdit().selectAll()
        QTest.keyClicks(widget.spinbox.lineEdit(), '-0.0005')
        widget.spinbox.interpretText()
        self.assertEqual(widget.getValue(), -.0005)
        widget.setValue(-.01234567)
        widget.spinbox.stepBy(1)
        self.assertAlmostEqual(widget.getValue(), 1-.01234567, places=14)

    def test_comma_and_dot_work_in_both_locales(self):
        for locale_name in ('de_DE', 'en_US'):
            widget = CfgDoubleSpinBox('Depth', ' in')
            widget.spinbox.setLocale(QLocale(locale_name))
            for entry in ('-0,0005 in', '-0.0005 in'):
                with self.subTest(locale=locale_name, entry=entry):
                    widget.spinbox.lineEdit().selectAll()
                    QTest.keyClicks(widget.spinbox.lineEdit(), entry.removesuffix(' in'))
                    widget.spinbox.interpretText()
                    self.assertEqual(widget.getValue(), -.0005)

    def test_unchanged_dialog_and_profile_reload_preserve_precise_values(self):
        for units in ('mm', 'in'):
            with self.subTest(units=units):
                config = g.config
                config.var_dict['General']['tool_units'] = units
                config.var_dict['Depth_Coordinates']['axis3_mill_depth'] = -.0156789
                config.var_dict['Depth_Coordinates']['axis3_slice_depth'] = -.0005
                config.var_dict['Plane_Coordinates']['axis1_start_end'] = .01234567
                config.var_dict['Tool_Parameters']['1']['diameter'] = .0156789
                config.var_dict['Tool_Parameters']['1']['lead_length'] = .0056789
                config.var_dict['Tool_Parameters']['1']['milling_offset'] = -.00056789
                config.var_dict['Drag_Knife_Options']['ramp_in_length'] = .0005
                config.save_varspace()
                config = g.config = MyConfig()
                before = config.var_dict.dict()
                widgets = config.makeConfigWidgets()
                dialog = ConfigWindow(widgets, config.var_dict,
                                      config.var_dict.configspec)
                dialog.accept()
                self.assertEqual(dialog.result(), 1)
                sections = ('Depth_Coordinates', 'Plane_Coordinates',
                            'Tool_Parameters', 'Drag_Knife_Options')
                for section in sections:
                    self.assertEqual(config.var_dict[section].dict(), before[section])
                config.save_varspace()
                reloaded = MyConfig()
                for section in sections:
                    self.assertEqual(reloaded.var_dict[section].dict(), before[section])
                dialog.close()

    def test_unit_switch_and_dialog_preserve_physical_depth_and_tool_values(self):
        config = g.config
        config.var_dict['Depth_Coordinates']['axis3_mill_depth'] = -.0156789
        config.var_dict['Tool_Parameters']['1']['diameter'] = .0056789
        config.update_config()
        for units, scale in (('in', 1 / 25.4), ('mm', 1)):
            config.var_dict['General']['tool_units'] = units
            config.update_config()
            widgets = config.makeConfigWidgets()
            dialog = ConfigWindow(widgets, config.var_dict, config.var_dict.configspec)
            dialog.accept()
            self.assertEqual(dialog.result(), 1)
            self.assertAlmostEqual(config.var_dict['Depth_Coordinates']['axis3_mill_depth'],
                                   -.0156789 * scale, places=14)
            self.assertAlmostEqual(config.var_dict['Tool_Parameters']['1']['diameter'],
                                   .0056789 * scale, places=14)
            dialog.close()

    def test_config_project_knife_plan_and_export_keep_depths(self):
        from dxf2gcode_leadmove_project_test import _ParentStub, Project
        from dxf2gcode_stmove_gcode_test import (
            build_stmove, make_plan_service, make_postpro, make_shape, square_geos)
        from toolpath_test_support import serialize_gcode

        config = g.config
        config.var_dict['General']['tool_units'] = 'in'
        config.var_dict['General']['machine_type'] = 'drag_knife'
        config.var_dict['Depth_Coordinates']['axis3_mill_depth'] = -.015
        config.var_dict['Depth_Coordinates']['axis3_slice_depth'] = -.005
        config.var_dict['Tool_Parameters']['1']['diameter'] = .0005
        config.save_varspace()
        config = g.config = MyConfig()
        config.metric = 0
        config.update_config()
        config.vars.Drag_Knife_Options['ramp_in_length'] = 0
        shape = make_shape(square_geos(1), cut_cor=40,
                           tool_diameter=config.vars.Tool_Parameters['1']['diameter'])
        shape.axis3_mill_depth = config.vars.Depth_Coordinates['axis3_mill_depth']
        shape.axis3_slice_depth = config.vars.Depth_Coordinates['axis3_slice_depth']
        shape.parentLayer.lead_length = .0056789
        shape.parentLayer.exp_order_complete = [0]
        parent = _ParentStub([shape.parentLayer])
        content = Project(parent).export(compleet=False)
        shape.axis3_mill_depth = -1
        shape.axis3_slice_depth = -1
        shape.parentLayer.lead_length = 1
        Project(parent).load(content, compleet=False)
        self.assertEqual(shape.axis3_mill_depth, -.015)
        self.assertEqual(shape.axis3_slice_depth, -.005)
        self.assertEqual(shape.parentLayer.lead_length, .0056789)
        build_stmove(shape)
        post = make_postpro()
        self.assertEqual(post.vars.Number_Format['post_decimals'], 3)
        for decimals, final, swivel in ((3, -.015, -.005), (4, -.0005, -.0001)):
            with self.subTest(decimals=decimals):
                shape.axis3_mill_depth, shape.axis3_slice_depth = final, swivel
                post.vars.Number_Format.post_decimals = decimals
                plan = make_plan_service().execute(shape, post)
                depths = [action.args[0] for action in plan.actions
                          if action.kind == 'linear_z']
                self.assertIn(final, depths)
                self.assertIn(swivel, depths)
                code = serialize_gcode(shape, post)
                z_values = [float(value) for value in
                            re.findall(r'Z\s*([+-]?[0-9]+(?:\.[0-9]+)?)', code)]
                self.assertIn(final, z_values)
                self.assertIn(swivel, z_values)


if __name__ == '__main__':
    unittest.main()
