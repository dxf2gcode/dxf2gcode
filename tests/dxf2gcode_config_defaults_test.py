"""K2: schema defaults, persisted profile values and new-contour defaults."""

import copy
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path[:0] = [str(Path(__file__).parent), str(Path(__file__).resolve().parents[1]/'source')]
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from dxf2gcode.adapters.config.runtime_config import MyConfig
from dxf2gcode.presentation.qt.configwindow import ConfigWindow
from dxf2gcode.presentation.qt.qt_compat.QtCore import QTranslator, QCoreApplication
from dxf2gcode.domain.project.shape import Shape
import dxf2gcode.bootstrap.runtime_state as g

ROOT = Path(__file__).resolve().parents[1]
DEFAULTS = dict(show_disabled_paths=True, live_update_export_route=False,
                split_line_segments=False, automatic_cutter_compensation=False,
                machine_type='milling')


class TestConfigDefaults(unittest.TestCase):
    def test_legacy_knife_profile_migration_is_persisted_once(self):
        for version, planned, machine in ((9.16, False, 'drag_knife'),
                                           (9.17, False, 'drag_knife'),
                                           (9.17, True, 'drag_knife'),
                                           (9.17, False, 'milling')):
            with self.subTest(version=version, planned=planned, machine=machine), tempfile.TemporaryDirectory() as folder:
                with patch.object(g, 'folder', folder):
                    config = MyConfig()
                    values = config.var_dict
                    values['Version']['config_version'] = version
                    values['General']['machine_type'] = machine
                    values['Depth_Coordinates'].update(dict(axis3_start_mill_depth=2,
                        axis3_mill_depth=-.3, axis3_slice_depth=-.07))
                    values['Drag_Knife_Options']['swivel_depth'] = -.02
                    if version >= 9.17:
                        values['Drag_Knife_Options']['planned_passes'] = planned
                        values['Drag_Knife_Options'].update(dict(extra_pass=True,
                            alternate=True, entry_mode='unknown', return_to_start=True))
                    values['Lead_In_Out'].update(dict(lead_in_mode='straight', lead_out_mode='radius', overcut_enabled=True))
                    config.save_varspace()
                    loaded = MyConfig()
                    migrated = machine == 'drag_knife' and not planned
                    self.assertAlmostEqual(loaded.vars.Drag_Knife_Options.swivel_depth, -.07 if migrated else -.02)
                    self.assertAlmostEqual(loaded.vars.Depth_Coordinates.axis3_slice_depth, -2.3 if migrated else -.07)
                    self.assertEqual(loaded.vars.Lead_In_Out.lead_in_mode, 'off' if migrated else 'straight')
                    self.assertEqual(loaded.vars.Lead_In_Out.lead_out_mode, 'off' if migrated else 'radius')
                    self.assertTrue(loaded.vars.Lead_In_Out.overcut_enabled)
                    self.assertEqual(loaded.vars.Drag_Knife_Options.extra_pass, version >= 9.17 and not migrated)
                    self.assertEqual(loaded.vars.Drag_Knife_Options.entry_mode, 'fixed' if migrated or version < 9.17 else 'unknown')
                    self.assertNotIn('planned_passes', loaded.var_dict['Drag_Knife_Options'])
                    first = loaded.var_dict.dict()
                    self.assertEqual(MyConfig().var_dict.dict(), first)
                    self.assertNotIn('planned_passes', loaded.makeConfigWidgets()['Drag_Knife_Options'])

    @classmethod
    def setUpClass(cls):
        from dxf2gcode.presentation.qt.qt_compat.QtWidgets import QApplication
        cls.app=QApplication.instance() or QApplication([])

    def test_factory_file_profile_roundtrip_and_localized_default_hints(self):
        for language in ('en','de','fr','ru'):
            with self.subTest(language=language), tempfile.TemporaryDirectory() as folder:
                tr=QTranslator()
                if language != 'en':
                    self.assertTrue(tr.load(str(ROOT/'source/i18n'/('dxf2gcode_'+language+'.qm'))))
                    self.app.installTranslator(tr)
                form=None
                try:
                    with patch.object(g,'folder',folder):
                        config=MyConfig()
                        self.assertTrue(Path(config.filename).is_file())
                        fresh=MyConfig()
                        for key,value in DEFAULTS.items():
                            self.assertEqual(fresh.var_dict['General'][key],value)
                        individual={key:(not value if isinstance(value,bool) else 'lathe') for key,value in DEFAULTS.items()}
                        config.var_dict['General'].update(individual)
                        config.update_config()
                        config.save_varspace()
                        loaded=MyConfig()
                        before=copy.deepcopy(loaded.var_dict.dict())
                        file_before=Path(loaded.filename).read_bytes()
                        definitions=loaded.makeConfigWidgets()
                        form=ConfigWindow(definitions,loaded.var_dict,loaded.var_dict.configspec)
                        form.show()
                        self.app.processEvents()
                        for key,default in DEFAULTS.items():
                            control=definitions['General'][key]
                            self.assertEqual(control.getValue(),individual[key])
                            if isinstance(default,bool):
                                label=QCoreApplication.translate('MyConfig','On' if default else 'Off')
                                tooltip=control.checkbox.toolTip()
                                self.assertNotIn('(default)',control.checkbox.text())
                            else:
                                label=QCoreApplication.translate('MyConfig','Milling')
                                tooltip=control.combobox.toolTip()
                                self.assertEqual(loaded.machine_type,'lathe')
                                self.assertNotIn('(default)',control.label.text())
                            expected=QCoreApplication.translate('MyConfig','Default for new profiles: %s') % label
                            self.assertIn(expected,tooltip)
                        for key,control in definitions['Layer_Options'].items():
                            if key.endswith('_identifiers'):
                                self.assertIn('https://dxf2gcode.github.io/dxf2gcode/',control.lineedit.toolTip())
                                self.assertNotIn('wiki',control.lineedit.toolTip().lower())
                        self.assertEqual(loaded.var_dict.dict(),before)
                        self.assertEqual(Path(loaded.filename).read_bytes(),file_before)
                        again=MyConfig()
                        for key,value in individual.items():
                            self.assertEqual(again.var_dict['General'][key],value)
                finally:
                    if form is not None:
                        form.close()
                    self.app.removeTranslator(tr)

    def test_optimization_default_applies_only_to_new_contours(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(g,'folder',folder):
            config=MyConfig()
            with patch.object(g,'config',config):
                config.var_dict['Route_Optimisation']['default_TSP']=False
                config.update_config()
                existing=Shape(nr=1,closed=True,geos=[], config=g.config)
                self.assertFalse(existing.send_to_TSP)
                config.var_dict['Route_Optimisation']['default_TSP']=True
                config.update_config()
                new=Shape(nr=2,closed=True,geos=[], config=g.config)
                self.assertTrue(new.send_to_TSP)
                self.assertFalse(existing.send_to_TSP)


if __name__=='__main__':
    unittest.main()
