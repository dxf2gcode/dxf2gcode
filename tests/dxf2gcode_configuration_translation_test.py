"""Real configuration dialogs and stable Qt extraction contexts (K1)."""

import copy
import importlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'source'))
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from configobj import ConfigObj
from validate import Validator
import dxf2gcode.bootstrap.runtime_state as g
from dxf2gcode.adapters.config.runtime_config import MyConfig
from dxf2gcode.adapters.postprocessor.postprocessorconfig import (
    MyPostProConfig, POSTPRO_SPEC)
from dxf2gcode.presentation.qt.qt_compat import PYQT_VERSION, QtCore
from dxf2gcode.presentation.qt.qt_compat.QtWidgets import QApplication, QDialogButtonBox
from dxf2gcode.presentation.qt.configwindow import ConfigWindow
from dxf2gcode.presentation.qt.configuration_help import HELP_SOURCES


class TestConfigurationTranslations(unittest.TestCase):
    def test_usability_controls_and_help_are_translated(self):
        entries = {
            'MyConfig': ('Show tool circle at entry (2D)',),
            'MyDropDownMenu': ('Move workpiece zero here ...',
                'Open the workpiece zero dialog for this point. Snapping is optional in the dialog.'),
            'PopUpDialog': ('Snap to nearest contour point',
                'Use a start-point candidate of the selected contour without changing its start point or direction.'),
            'TreeHandler': ('Expand the active tree (Ctrl+Shift+Right when the tree has focus)',
                'Collapse the active tree (Ctrl+Shift+Left when the tree has focus)'),
            'ToolpathPreview': ('The entry circle approximates the cutter position with machine compensation.',),
        }
        for language in ('de', 'fr', 'ru'):
            translator = QtCore.QTranslator()
            self.assertTrue(translator.load(str(ROOT / 'source/i18n' / ('dxf2gcode_'+language+'.qm'))))
            for context, sources in entries.items():
                for source in sources:
                    result = translator.translate(context, source)
                    self.assertTrue(result, (language, context, source))
                    self.assertNotEqual(result, source)
            self.app.installTranslator(translator)
            try:
                with tempfile.TemporaryDirectory() as folder, patch.object(g, 'folder', folder):
                    config = MyConfig()
                    definitions = config.makeConfigWidgets()
                    form = ConfigWindow(definitions, config.var_dict, config.var_dict.configspec)
                    option = definitions['General']['show_tool_circle']
                    self.assertTrue(option.getValue())
                    self.assertEqual(option.checkbox.text(), translator.translate('MyConfig', entries['MyConfig'][0]))
                    self.assertTrue(option.checkbox.toolTip())
                    self.assertNotIn('Show the tool circle', option.checkbox.toolTip())
                    option.setValue(False)
                    self.assertFalse(option.getValue())
                    form.close()
            finally:
                self.app.removeTranslator(translator)

    def test_restart_notices_and_unit_label_are_translated(self):
        notice = ('These saved changes require a restart:\n{0}\n\n'
                  'After you close the configuration window, DXF2GCODE will restart '
                  'with an empty window. The current drawing and unsaved machining '
                  'changes will not be restored.')
        failure = ('DXF2GCODE could not be restarted. The current window remains open. '
                   'You can restart the application manually.')
        for language in ('de', 'fr', 'ru'):
            translator = QtCore.QTranslator()
            self.assertTrue(translator.load(str(ROOT / 'source/i18n' / ('dxf2gcode_'+language+'.qm'))))
            for source in ('Restart required', 'Restart failed', '3D display',
                           'Logging', notice, failure):
                text = translator.translate('MainWindow', source)
                self.assertTrue(text)
                self.assertNotEqual(text, source)
                if source == notice:
                    self.assertIn('\n{0}\n\n', text)
            label = translator.translate('MyConfig', 'Configuration values use the unit:')
            self.assertTrue(label)
            self.assertNotEqual(label, 'Configuration values use the unit:')

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        importlib.import_module(
            'dxf2gcode.presentation.qt.generated.dxf2gcode_images%d_rc' % PYQT_VERSION)

    def test_real_forms_translate_labels_help_and_choices_without_changing_values(self):
        for language in ('de', 'fr', 'ru'):
            with self.subTest(language=language), tempfile.TemporaryDirectory() as folder:
                translator = QtCore.QTranslator()
                self.assertTrue(translator.load(str(
                    ROOT / 'source/i18n' / ('dxf2gcode_' + language + '.qm'))))
                self.app.installTranslator(translator)
                forms = []
                try:
                    with patch.object(g, 'folder', folder):
                        config = MyConfig()
                    original = copy.deepcopy(config.var_dict.dict())
                    values = ConfigObj(configspec=POSTPRO_SPEC, interpolation=False)
                    self.assertIs(values.validate(Validator(), copy=True), True)
                    original_post = copy.deepcopy(values.dict())
                    application = ConfigWindow(config.makeConfigWidgets(),
                                               config.var_dict, config.var_dict.configspec)
                    postprocessor = ConfigWindow(MyPostProConfig.makeConfigWidgets(),
                                                 values, values.configspec)
                    forms.extend((application, postprocessor))
                    for form in forms:
                        form.show()
                        self.assertEqual(form.windowTitle(),
                                         translator.translate('ConfigWindow', 'Configuration'))
                        for name in ('Discard', 'Apply', 'Close'):
                            button = form.button_box.button(getattr(QDialogButtonBox.StandardButton, name))
                            self.assertEqual(button.text(), translator.translate('ConfigWindow', name))
                    self.app.processEvents()
                    for form, context, section, key, source in (
                        (application, 'MyConfig', 'General', 'mode3d',
                         '3D mode (requires OpenGL - restart needed)'),
                        (postprocessor, 'MyPostProConfig', 'General', 'abs_export',
                         'Export absolute coordinates'),
                    ):
                        widget = form.cfg_window_def[section][key]
                        expected = translator.translate(context, source)
                        self.assertTrue(expected)
                        self.assertEqual(widget.checkbox.text(), expected)
                        self.assertTrue(widget.whatsThis())
                        self.assertNotIn('When enabled', widget.whatsThis())
                    for source in HELP_SOURCES:
                        self.assertTrue(translator.translate('ConfigurationHelp', source), source)
                    machines = application.cfg_window_def['General']['machine_type']
                    for value, source in (('milling', 'Milling'), ('lathe', 'Lathe'),
                                          ('drag_knife', 'Drag knife')):
                        machines.setValue(value)
                        self.assertEqual(machines.getValue(), value)
                        self.assertEqual(machines.combobox.currentText(),
                                         translator.translate('MyConfig', source))
                    macro = postprocessor.cfg_window_def['Tool_Change']['return_state']
                    macro.setValue('next_start_at_retract')
                    self.assertEqual(macro.getValue(), 'next_start_at_retract')
                    self.assertEqual(macro.combobox.currentText(), translator.translate(
                        'MyPostProConfig', 'Next start at retract height'))
                    # Opening the dialogs and choosing translated entries do not
                    # apply or rewrite the user's persisted values.
                    self.assertEqual(config.var_dict.dict(), original)
                    self.assertEqual(values.dict(), original_post)
                    expected_lathe = {'de': '&Drehmaschine', 'fr': '&Tour',
                                      'ru': '&Токарная'}[language]
                    self.assertEqual(translator.translate('MainWindow', '&Lathe'),
                                     expected_lathe)
                finally:
                    for form in forms:
                        form.close()
                    self.app.removeTranslator(translator)

    def test_compact_pages_resize_and_keep_full_help_on_controls(self):
        from dxf2gcode.presentation.qt.qt_compat.QtGui import QFont, QFontDatabase
        original = self.app.font()
        font = QFont('Sans Serif',9)
        # Windows offscreen Qt may otherwise have no font and use square
        # fallback glyphs with unrelated metrics. Exercise the real UI font.
        path = Path('C:/Windows/Fonts/segoeui.ttf')
        if sys.platform == 'win32' and path.exists():
            identifier = QFontDatabase.addApplicationFont(str(path))
            if identifier >= 0:
                font.setFamily(QFontDatabase.applicationFontFamilies(identifier)[0])
        self.app.setFont(font)
        try:
            self._check_compact_pages()
        finally:
            self.app.setFont(original)

    def _check_compact_pages(self):
        for language in ('en','de','fr','ru'):
            with self.subTest(language=language), tempfile.TemporaryDirectory() as folder:
                translator = QtCore.QTranslator()
                if language != 'en':
                    self.assertTrue(translator.load(str(ROOT / 'source/i18n' / ('dxf2gcode_'+language+'.qm'))))
                    self.app.installTranslator(translator)
                with patch.object(g, 'folder', folder):
                    config = MyConfig()
                original = copy.deepcopy(config.var_dict.dict())
                definitions = config.makeConfigWidgets()
                form = ConfigWindow(definitions,config.var_dict,config.var_dict.configspec)
                try:
                    form.show()
                    self.app.processEvents()
                    for width in (1000,780):
                        form.resize(width,600)
                        for section in ('Cutter_Compensation','Layer_Options'):
                            target = definitions[section]
                            control = target['done_by_machine'] if section == 'Cutter_Compensation' else target['start_radius_identifiers']
                            for index in range(form.tab_window.count()):
                                page = form.tab_window.widget(index)
                                if page.isAncestorOf(control):
                                    form.tab_window.setCurrentIndex(index)
                                    self.app.processEvents()
                                    self.assertEqual(page.horizontalScrollBar().maximum(),0,(language,width,section))
                                    if section == 'Cutter_Compensation':
                                        editor = definitions['Drag_Knife_Options']['entry_mode'].combobox
                                        self.assertLessEqual(editor.mapTo(page.viewport(),editor.rect().topRight()).x(),page.viewport().width())
                    cutter = definitions['Cutter_Compensation']['done_by_machine']
                    self.assertIn('G41',cutter.checkbox.toolTip())
                    overcut = definitions['Lead_In_Out']['overcut_enabled']
                    self.assertGreater(len(overcut.checkbox.toolTip()),len(overcut.checkbox.text()))
                    parameters = definitions['Layer_Options']
                    self.assertTrue(parameters['__intro__'].label.isVisible())
                    self.assertEqual(parameters['__section_title__'],QtCore.QCoreApplication.translate('MyConfig','Parameter names'))
                    for key,field in parameters.items():
                        if key.endswith('_identifiers'):
                            self.assertNotIn('separator)',field.label.text())
                            self.assertTrue(field.lineedit.toolTip())
                            before = field.getValue()
                            field.setValue(before)
                            self.assertEqual(field.getValue(),before)
                    old_label = QtCore.QCoreApplication.translate('MyConfig','Start radius (cutter compensation, deprecated - use the lead radius instead):')
                    self.assertIn(old_label,parameters['start_radius_identifiers'].lineedit.toolTip())
                    self.assertEqual(config.var_dict.dict(),original)
                finally:
                    form.close()
                    self.app.removeTranslator(translator)

    def test_reextraction_keeps_finished_messages_in_the_runtime_contexts(self):
        sources = [str(ROOT / 'source/dxf2gcode/presentation/qt' / name)
                   for name in ('configuration_widgets.py', 'configuration_help.py', 'configwindow.py')]
        sources.append(str(ROOT / 'source/dxf2gcode/presentation/qt/resources/dxf2gcode.ui'))
        for language in ('de', 'fr', 'ru'):
            with self.subTest(language=language), tempfile.TemporaryDirectory() as folder:
                original = ROOT / 'source/i18n' / ('dxf2gcode_' + language + '.ts')
                catalog = Path(folder) / original.name
                catalog.write_bytes(original.read_bytes())
                relocated_sources = []
                for source in sources:
                    target = Path(folder) / Path(source).name
                    target.write_bytes(Path(source).read_bytes())
                    relocated_sources.append(str(target))
                if PYQT_VERSION == 5:
                    command = [sys.executable, '-m', 'PyQt5.pylupdate_main'] + relocated_sources + ['-ts', str(catalog)]
                else:
                    command = [sys.executable, '-m', 'PyQt6.lupdate.pylupdate',
                               '--ts', str(catalog)] + relocated_sources
                result = subprocess.run(command, capture_output=True, text=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                contexts = {c.findtext('name'): c for c in ET.parse(catalog).getroot().findall('context')}
                for context in ('MyConfig', 'MyPostProConfig', 'ConfigurationHelp'):
                    messages = [m for m in contexts[context].findall('message')
                                if m.find('translation').get('type') not in ('obsolete', 'vanished')]
                    self.assertTrue(messages)
                    for message in messages:
                        self.assertTrue(message.findtext('translation'), message.findtext('source'))
                        self.assertIsNone(message.find('translation').get('type'), message.findtext('source'))
                menu = {m.findtext('source'): m for m in contexts['MainWindow'].findall('message')}
                for source in ('&Milling', '&Lathe', '&Drag Knife'):
                    self.assertTrue(menu[source].findtext('translation'))
                    self.assertIsNone(menu[source].find('translation').get('type'))
                buttons = {m.findtext('source'): m for m in contexts['ConfigWindow'].findall('message')}
                for source in ('Configuration', 'Discard', 'Apply', 'Close'):
                    self.assertTrue(buttons[source].findtext('translation'))
                    self.assertIsNone(buttons[source].find('translation').get('type'))

    def test_schema_help_remains_covered_by_extractable_sources(self):
        from dxf2gcode.adapters.config.runtime_config import CONFIG_SPEC
        sources = set()
        for spec in (CONFIG_SPEC, POSTPRO_SPEC):
            schema = ConfigObj(configspec=spec, interpolation=False).configspec
            for section in schema.sections:
                for key in schema[section].scalars:
                    text = ''.join(line.strip() for line in schema[section].comments[key])
                    text = text.strip(' #').replace('#', '\n')
                    if text and key != 'config_version':
                        sources.add(text)
        self.assertEqual(set(HELP_SOURCES), sources)


if __name__ == '__main__':
    unittest.main()
