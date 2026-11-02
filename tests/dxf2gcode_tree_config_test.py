"""Tree startup/import preferences, old profiles and translated controls."""

import os
from pathlib import Path
import sys
import tempfile
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
SOURCE = Path(__file__).resolve().parents[1] / "source"
sys.path.insert(0, str(SOURCE))

from configobj import ConfigObj
from validate import Validator

import dxf2gcode.bootstrap.runtime_state as g
from dxf2gcode.adapters.config.runtime_config import (
    CONFIG_SPEC, CONFIG_VERSION, SUPPORTED_CONFIGS, MyConfig)
from dxf2gcode.presentation.qt.qt_compat.QtCore import QTranslator
from dxf2gcode.presentation.qt.qt_compat.QtWidgets import QApplication

_APP = None


class TestLayerTreeStartupConfig(unittest.TestCase):
    def setUp(self):
        global _APP
        _APP = QApplication.instance() or QApplication([])
        self.previous_folder = g.folder
        self.previous_config = g.config
        self.directory = tempfile.TemporaryDirectory(prefix="d2g_tree_config_")
        g.folder = self.directory.name

    def tearDown(self):
        g.folder = self.previous_folder
        g.config = self.previous_config
        self.directory.cleanup()

    def test_new_profiles_expand_layers_by_default(self):
        config = MyConfig()
        self.assertIs(config.vars.General.expand_layers_on_load, True)
        self.assertIs(config.vars.General.show_tool_circle, True)
        self.assertIs(config.vars.Import_Parameters.exclude_ignore_layers, False)
        self.assertIs(config.vars.Import_Parameters.exclude_layer_zero, False)

    def test_old_profiles_receive_default_without_losing_values(self):
        MyConfig()  # Create only the isolated profile directory.
        for version in SUPPORTED_CONFIGS[:-1]:
            with self.subTest(version=version):
                values = ConfigObj(configspec=CONFIG_SPEC,
                                   interpolation=False, _inspec=True)
                values.validate(Validator(), copy=True)
                del values["General"]["expand_layers_on_load"]
                del values["General"]["show_tool_circle"]
                del values["Import_Parameters"]["exclude_ignore_layers"]
                del values["Import_Parameters"]["exclude_layer_zero"]
                values["General"]["live_update_export_route"] = True
                values["Version"]["config_version"] = version
                values.filename = str(Path(g.folder) / "config/config.cfg")
                values.write()
                loaded = MyConfig()
                self.assertIs(loaded.vars.General.expand_layers_on_load, True)
                self.assertIs(loaded.vars.General.show_tool_circle, True)
                self.assertTrue(loaded.vars.General.live_update_export_route)
                self.assertIs(loaded.vars.Import_Parameters.exclude_ignore_layers, False)
                self.assertIs(loaded.vars.Import_Parameters.exclude_layer_zero, False)
                self.assertEqual(loaded.var_dict["Version"]["config_version"],
                                 CONFIG_VERSION)
                self.assertFalse(Path(values.filename).with_suffix(".bad").exists())

    def test_both_preferences_survive_save_reload(self):
        config = MyConfig()
        for expand in (False, True):
            with self.subTest(expand=expand):
                config.var_dict["General"]["expand_layers_on_load"] = expand
                config.var_dict["General"]["show_tool_circle"] = not expand
                config.save_varspace()
                config = MyConfig()
                self.assertIs(config.vars.General.expand_layers_on_load, expand)
                self.assertIs(config.vars.General.show_tool_circle, not expand)

    def test_import_filters_survive_save_reload_independently(self):
        config = MyConfig()
        for ignore, zero in ((False, False), (True, False), (False, True), (True, True)):
            with self.subTest(ignore=ignore, zero=zero):
                config.var_dict["Import_Parameters"]["exclude_ignore_layers"] = ignore
                config.var_dict["Import_Parameters"]["exclude_layer_zero"] = zero
                config.save_varspace()
                config = MyConfig()
                self.assertIs(config.vars.Import_Parameters.exclude_ignore_layers, ignore)
                self.assertIs(config.vars.Import_Parameters.exclude_layer_zero, zero)

    def test_translated_checkbox_preserves_values_in_all_languages(self):
        expected = {
            "de": "Layer beim Laden einer Zeichnung ausklappen",
            "fr": "Développer les calques lors du chargement d’un dessin",
            "ru": "Разворачивать слои при загрузке чертежа",
        }
        config = MyConfig()
        for language, label in expected.items():
            with self.subTest(language=language):
                translator = QTranslator()
                self.assertTrue(translator.load(str(
                    SOURCE / "i18n" / ("dxf2gcode_" + language + ".qm"))))
                _APP.installTranslator(translator)
                try:
                    widgets = config.makeConfigWidgets()
                    control = widgets["General"]["expand_layers_on_load"]
                    self.assertEqual(control.checkbox.text(), label)
                    for value in (True, False):
                        control.setValue(value)
                        self.assertIs(control.getValue(), value)
                finally:
                    _APP.removeTranslator(translator)

    def test_import_filter_labels_are_translated_in_all_languages(self):
        expected = {
            "de": ("IGNORE-Layer nicht importieren", "Layer 0 nicht importieren"),
            "fr": ("Ne pas importer les calques IGNORE", "Ne pas importer le calque 0"),
            "ru": ("Не импортировать слои IGNORE", "Не импортировать слой 0"),
        }
        config = MyConfig()
        for language, labels in expected.items():
            with self.subTest(language=language):
                translator = QTranslator()
                self.assertTrue(translator.load(str(
                    SOURCE / "i18n" / ("dxf2gcode_" + language + ".qm"))))
                _APP.installTranslator(translator)
                try:
                    widgets = config.makeConfigWidgets()["Import_Parameters"]
                    for key, label in zip(("exclude_ignore_layers", "exclude_layer_zero"), labels):
                        self.assertEqual(widgets[key].checkbox.text(), label)
                        for value in (False, True):
                            widgets[key].setValue(value)
                            self.assertIs(widgets[key].getValue(), value)
                    self.assertTrue(translator.translate(
                        "ImportFilters", "Layers excluded from import: %s"))
                finally:
                    _APP.removeTranslator(translator)


if __name__ == "__main__":
    unittest.main()
