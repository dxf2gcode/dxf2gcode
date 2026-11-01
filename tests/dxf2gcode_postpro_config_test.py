# -*- coding: utf-8 -*-
"""File-based regression tests for postprocessor configuration handling."""
from __future__ import absolute_import

import os
import shutil
import sys
import tempfile
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_DIR = os.path.dirname(_TEST_DIR)
sys.path[:0] = [_TEST_DIR, os.path.join(_REPO_DIR, "source")]

import dxf2gcode.bootstrap.runtime_state as g  # noqa: E402
import dxf2gcode.domain.constants as c  # noqa: E402
from configobj import ConfigObj  # noqa: E402
from validate import Validator  # noqa: E402
from dxf2gcode.adapters.postprocessor.postprocessorconfig import (  # noqa: E402
    CONFIG_VERSION, POSTPRO_SPEC, MyPostProConfig)


class PostProConfigTestCase(unittest.TestCase):

    def setUp(self):
        self._old_folder = getattr(g, "folder", None)
        self.tmp = tempfile.mkdtemp(prefix="d2g_postpro_cfg_test_")
        g.folder = self.tmp
        os.makedirs(os.path.join(self.tmp, c.DEFAULT_POSTPRO_DIR))
        self.config = MyPostProConfig(filename="machine.cfg")

    def tearDown(self):
        g.folder = self._old_folder
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write_valid_config(self, version=CONFIG_VERSION):
        values = ConfigObj(configspec=POSTPRO_SPEC, interpolation=False,
                           list_values=False, _inspec=True)
        values.validate(Validator(), copy=True)
        values["Version"]["config_version"] = version
        values.filename = self.config.filename
        values.write()
        return values


class TestPostProConfigDefaultsAndRoundTrip(PostProConfigTestCase):

    def test_default_config_is_written_and_loads_with_current_version(self):
        self.config.create_default_config()

        self.assertTrue(os.path.isfile(self.config.filename))
        loaded = MyPostProConfig(filename="machine.cfg")
        loaded.load_config()

        self.assertEqual(loaded.var_dict["Version"]["config_version"],
                         CONFIG_VERSION)
        self.assertEqual(loaded.vars.General.output_type, "g-code")
        self.assertEqual(loaded.vars.General.abs_export, True)
        self.assertFalse(loaded.default_config)

    def test_custom_export_settings_survive_save_and_reload(self):
        self.config.create_default_config()
        self.config.var_dict["General"]["output_format"] = ".tap"
        self.config.var_dict["General"]["output_text"] = "Shop controller"
        self.config.var_dict["Number_Format"]["decimal_separator"] = ","
        self.config.var_dict["Program"]["code_end"] = "M30 (Done)"
        self.config.save_varspace()

        loaded = MyPostProConfig(filename="machine.cfg")
        loaded.load_config()

        self.assertEqual(loaded.vars.General.output_format, ".tap")
        self.assertEqual(loaded.vars.General.output_text, "Shop controller")
        self.assertEqual(loaded.vars.Number_Format.decimal_separator, ",")
        self.assertEqual(loaded.vars.Program.code_end, "M30 (Done)")

    def test_managed_macro_settings_survive_save_and_reload(self):
        self.config.create_default_config()
        self.config.var_dict['Tool_Change'].update(dict(
            return_state='next_start_at_retract', end_distance_mode='G91',
            work_offset='G55', length_offset_mode='mapping',
            length_offset_mapping='1:4,2:8'))
        self.config.var_dict['Program']['tool_change'] = 'M0%nlG43 H%length_offset_nr'
        self.config.save_varspace()
        loaded = MyPostProConfig(filename='machine.cfg')
        loaded.load_config()
        self.assertEqual(dict(loaded.var_dict['Tool_Change']),
                         dict(self.config.var_dict['Tool_Change']))
        self.assertEqual(loaded.vars.Program.tool_change, 'M0%nlG43 H%length_offset_nr')


class TestPostProConfigVersions(PostProConfigTestCase):

    def test_81_profile_without_macro_contract_keeps_legacy_output(self):
        values = self._write_valid_config(version=8.1)
        del values['Tool_Change']
        values['Program']['tool_change'] = 'T%tool_nr M6%nlS%speed%nl'
        values.write()
        self.config.load_config()
        self.assertFalse(self.config.version_mismatch)
        self.assertEqual(self.config.vars.Tool_Change.return_state, 'legacy')
        self.assertEqual(self.config.vars.Program.tool_change, 'T%tool_nr M6%nlS%speed%nl')

    def test_supported_older_version_is_upgraded_without_losing_settings(self):
        self._write_valid_config(version=8.0)
        values = ConfigObj(self.config.filename)
        values["General"]["output_format"] = ".cnc"
        values.write()

        self.config.load_config()

        self.assertEqual(self.config.version_mismatch, "")
        self.assertEqual(self.config.var_dict["Version"]["config_version"],
                         CONFIG_VERSION)
        self.assertEqual(self.config.vars.General.output_format, ".cnc")
        self.assertFalse(self.config.default_config)
        self.assertTrue(os.path.isfile(self.config.filename))
        self.assertFalse(os.path.exists(
            os.path.splitext(self.config.filename)[0] + c.BAD_CONFIG_EXTENSION))

    def test_unsupported_version_is_reported_and_original_file_is_preserved(self):
        self._write_valid_config(version=99.0)

        self.config.load_config()

        self.assertTrue(self.config.version_mismatch)
        self.assertTrue(os.path.isfile(self.config.filename))
        self.assertFalse(self.config.default_config)
        self.assertFalse(os.path.exists(
            os.path.splitext(self.config.filename)[0] + c.BAD_CONFIG_EXTENSION))


class TestPostProConfigRecovery(PostProConfigTestCase):

    def test_invalid_value_is_backed_up_and_replaced_with_defaults(self):
        values = self._write_valid_config()
        values["Number_Format"]["post_decimals"] = "not_an_integer"
        values.write()
        backup = os.path.splitext(self.config.filename)[0] + c.BAD_CONFIG_EXTENSION

        self.config.load_config()

        self.assertTrue(self.config.default_config)
        self.assertTrue(os.path.isfile(self.config.filename))
        self.assertTrue(os.path.isfile(backup))
        self.assertEqual(self.config.var_dict["Version"]["config_version"],
                         CONFIG_VERSION)
        self.assertEqual(self.config.vars.Number_Format.post_decimals, 3)

    def test_malformed_file_is_kept_as_backup_after_default_recovery(self):
        with open(self.config.filename, "w") as config_file:
            config_file.write("[Version\nconfig_version = ???\n")
        backup = os.path.splitext(self.config.filename)[0] + c.BAD_CONFIG_EXTENSION

        self.config.load_config()

        self.assertTrue(self.config.default_config)
        self.assertTrue(os.path.isfile(self.config.filename))
        self.assertTrue(os.path.isfile(backup))
        self.assertEqual(self.config.var_dict["Version"]["config_version"],
                         CONFIG_VERSION)


if __name__ == "__main__":
    unittest.main(verbosity=2)
