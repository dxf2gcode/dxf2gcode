# -*- coding: utf-8 -*-
"""
Configuration tests for the pocketing edge clearance option.

They cover the configuration architecture (versioning, defaults, migrations,
forward/backward compatibility, save/reload and invalid values) for the new
``[Pocketing] pocket_edge_clearance`` setting.

Run from the repository root:

    python -m unittest discover -s tests -t tests -p "dxf2gcode_config_pocketing_test.py" -v
"""
from __future__ import absolute_import

import os
import shutil
import tempfile
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import sys
_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [_TEST_DIR, os.path.join(os.path.dirname(_TEST_DIR), "source")]

import dxf2gcode.bootstrap.runtime_state as g  # noqa: E402
from dxf2gcode.adapters.config.runtime_config import (  # noqa: E402
    MyConfig, CONFIG_SPEC, CONFIG_VERSION, SUPPORTED_CONFIGS)
from configobj import ConfigObj  # noqa: E402
from validate import Validator  # noqa: E402

HISTORIC = 100.0 * 3 / 14  # 21.4286

_APP = None  # kept alive so widgets created by the tests are not deleted


class ConfigTestBase(unittest.TestCase):
    def setUp(self):
        self._old_folder = getattr(g, "folder", None)
        self._old_config = getattr(g, "config", None)
        self.tmp = tempfile.mkdtemp(prefix="d2g_cfg_test_")
        g.folder = self.tmp
        os.makedirs(os.path.join(self.tmp, "config"))

    def tearDown(self):
        g.folder = self._old_folder
        g.config = self._old_config
        shutil.rmtree(self.tmp, ignore_errors=True)

    @property
    def _cfg_path(self):
        return os.path.join(self.tmp, "config", "config.cfg")

    def _write_config(self, version, clearance="__keep__", drop_section=False,
                      raw_value=None, mode="__keep__", drop_mode=False):
        for p in (self._cfg_path, self._cfg_path + ".bad"):
            if os.path.exists(p):
                os.remove(p)
        obj = ConfigObj(configspec=CONFIG_SPEC, interpolation=False,
                        list_values=False, _inspec=True)
        obj.validate(Validator(), copy=True)
        obj["Version"]["config_version"] = version
        if drop_section:
            del obj["Pocketing"]
        else:
            if raw_value is not None:
                obj["Pocketing"]["pocket_edge_clearance"] = raw_value
            elif clearance != "__keep__":
                obj["Pocketing"]["pocket_edge_clearance"] = clearance
            if drop_mode:
                del obj["Pocketing"]["pocket_compensation_mode"]
            elif mode != "__keep__":
                obj["Pocketing"]["pocket_compensation_mode"] = mode
        obj.filename = self._cfg_path
        obj.write()

    def _load(self):
        cfg = MyConfig()
        g.config = cfg
        return cfg


class TestPocketClearanceConfig(ConfigTestBase):

    def test_default_config_has_option_and_current_version(self):
        cfg = self._load()
        self.assertEqual(cfg.var_dict["Version"]["config_version"], CONFIG_VERSION)
        self.assertAlmostEqual(
            float(cfg.var_dict["Pocketing"]["pocket_edge_clearance"]),
            HISTORIC, places=4)

    def test_option_present_in_config_spec(self):
        spec_text = "\n".join(CONFIG_SPEC)
        self.assertIn("[Pocketing]", spec_text)
        self.assertIn("pocket_edge_clearance", spec_text)
        self.assertNotIn("pocket_compensation_mode", spec_text)

    def test_config_widget_exists_for_option(self):
        # the option must be reachable in the existing configuration window
        from dxf2gcode.presentation.qt.qt_compat import QtWidgets
        global _APP
        _APP = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        cfg = self._load()
        widgets = cfg.makeConfigWidgets()
        self.assertIn("Pocketing", widgets)
        self.assertIn("pocket_edge_clearance", widgets["Pocketing"])
        self.assertNotIn("pocket_compensation_mode", widgets["Pocketing"])

    def test_new_config_has_no_pocket_direction_override(self):
        cfg = self._load()
        self.assertNotIn("pocket_compensation_mode", cfg.var_dict["Pocketing"])

    def test_old_modes_are_removed_without_losing_clearance(self):
        for mode in ("always_inward", "selected_direction"):
            with self.subTest(mode=mode):
                self._write_config(CONFIG_VERSION, mode=mode, clearance=37.5)
                cfg = self._load()
                self.assertEqual(cfg.version_mismatch, "")
                self.assertNotIn("pocket_compensation_mode", cfg.var_dict["Pocketing"])
                self.assertAlmostEqual(cfg.var_dict["Pocketing"]["pocket_edge_clearance"], 37.5)
                cfg.save_varspace()
                again = self._load()
                self.assertNotIn("pocket_compensation_mode", again.var_dict["Pocketing"])
                self.assertAlmostEqual(again.var_dict["Pocketing"]["pocket_edge_clearance"], 37.5)

    def test_old_config_without_option_loads_with_default(self):
        # a config file that predates the option (no [Pocketing] section)
        self._write_config(CONFIG_VERSION, drop_section=True)
        cfg = self._load()
        self.assertEqual(cfg.version_mismatch, "")
        self.assertFalse(cfg.default_config)
        self.assertAlmostEqual(
            float(cfg.var_dict["Pocketing"]["pocket_edge_clearance"]),
            HISTORIC, places=4)
        # file must not have been discarded
        self.assertFalse(os.path.exists(self._cfg_path + ".bad"))

    def test_old_912_is_migrated_to_current_version(self):
        self._write_config(9.12, drop_section=True)
        cfg = self._load()
        self.assertEqual(cfg.version_mismatch, "")
        self.assertEqual(cfg.var_dict["Version"]["config_version"], CONFIG_VERSION)
        self.assertIn(9.12, SUPPORTED_CONFIGS)
        self.assertAlmostEqual(
            float(cfg.var_dict["Pocketing"]["pocket_edge_clearance"]),
            HISTORIC, places=4)

    def test_old_911_is_migrated_to_current_version(self):
        self._write_config(9.11, drop_section=True)
        cfg = self._load()
        self.assertEqual(cfg.version_mismatch, "")
        self.assertEqual(cfg.var_dict["Version"]["config_version"], CONFIG_VERSION)

    def test_explicit_clearance_is_preserved(self):
        self._write_config(CONFIG_VERSION, clearance=0.0)
        cfg = self._load()
        self.assertEqual(float(cfg.var_dict["Pocketing"]["pocket_edge_clearance"]), 0.0)

        self._write_config(CONFIG_VERSION, clearance=50.0)
        cfg = self._load()
        self.assertEqual(float(cfg.var_dict["Pocketing"]["pocket_edge_clearance"]), 50.0)

    def test_save_and_reload_preserves_other_settings(self):
        cfg = self._load()
        cfg.var_dict["Paths"]["import_dir"] = "C:/my/custom/dxf"
        cfg.var_dict["Pocketing"]["pocket_edge_clearance"] = 12.5
        cfg.save_varspace()

        cfg2 = self._load()
        self.assertEqual(cfg2.var_dict["Paths"]["import_dir"], "C:/my/custom/dxf")
        self.assertEqual(float(cfg2.var_dict["Pocketing"]["pocket_edge_clearance"]), 12.5)

    def test_out_of_range_value_is_neutralised(self):
        # An explicitly invalid value must never crash the loader; the
        # resulting value has to be inside the allowed range again.
        for bad in (150.0, -5.0):
            self._write_config(CONFIG_VERSION, raw_value=bad)
            cfg = self._load()  # must not raise
            self.assertEqual(cfg.version_mismatch, "")
            value = float(cfg.var_dict["Pocketing"]["pocket_edge_clearance"])
            self.assertGreaterEqual(value, 0.0)
            self.assertLessEqual(value, 100.0)

    def test_non_numeric_value_does_not_crash(self):
        self._write_config(CONFIG_VERSION, raw_value="not_a_number")
        cfg = self._load()  # must not raise
        self.assertEqual(cfg.version_mismatch, "")
        value = float(cfg.var_dict["Pocketing"]["pocket_edge_clearance"])
        self.assertGreaterEqual(value, 0.0)
        self.assertLessEqual(value, 100.0)

    def test_unsupported_version_reports_mismatch_without_crashing(self):
        self._write_config(9.10, clearance=5.0)
        cfg = self._load()
        self.assertNotEqual(cfg.version_mismatch, "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
