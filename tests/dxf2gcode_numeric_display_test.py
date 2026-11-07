"""GUI display rounding must never limit loaded or entered precision."""
from importlib import import_module
import os
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'source'))
import dxf2gcode.bootstrap.runtime_state as g
from dxf2gcode.presentation.qt.numeric_display import display_decimals, format_number, set_number
from dxf2gcode.presentation.qt.configwindow import CorrectedDoubleSpinBox, CfgDoubleSpinBox
from dxf2gcode.presentation.qt.qt_compat import QtCore, PYQT_VERSION
from dxf2gcode.presentation.qt.qt_compat.QtWidgets import QApplication, QWidget, QVBoxLayout, QLineEdit

QTest = import_module('PyQt%d.QtTest' % PYQT_VERSION).QTest


class TestNumericDisplay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.config = SimpleNamespace(metric=True, var_dict={'Display': dict(
            decimals_mm=3, decimals_in=5, decimals_angle=1, decimals_feed=1)})
        mock = patch.object(g, 'config', self.config)
        mock.start()
        self.addCleanup(mock.stop)

    def form(self, field):
        form = QWidget()
        layout = QVBoxLayout(form)
        layout.addWidget(field)
        other = QLineEdit(form)
        layout.addWidget(other)
        form.show()
        other.setFocus()
        self.app.processEvents()
        self.addCleanup(form.close)
        return form, other

    def test_fixed_places_units_angles_and_integers(self):
        self.assertEqual(format_number(1.2, 'mm'), '1.200')
        self.assertEqual(format_number(1.2, 'in'), '1.20000')
        self.assertEqual(format_number(12.34567, 'in', 'angle'), '12.3')
        self.assertEqual(format_number(12.34567, 'mm', 'feed'), '12.3')
        self.assertEqual(format_number(12.34567, 'in', 'feed'), '12.3')
        self.assertEqual(format_number(5000, kind='integer'), '5000')
        self.assertEqual(format_number(-1e-15, 'mm'), '0.000')
        self.config.var_dict['Display'].update(decimals_mm=1, decimals_in=7, decimals_angle=4, decimals_feed=2)
        self.assertEqual(format_number(12.34567, 'in', 'feed'), '12.35')
        self.assertEqual(display_decimals('in'), 7)
        self.assertEqual(format_number(1.234, 'mm'), '1.2')
        self.assertEqual(format_number(12.34567, kind='angle'), '12.3457')

    def test_config_feed_and_angle_fields_use_independent_precision(self):
        for unit, kind in ((' mm/min', 'feed'), (' IPS', 'feed'), ('°', 'angle')):
            field = CfgDoubleSpinBox('Value', unit)
            field.setValue(12.3456789)
            self.assertEqual(field.spinbox.number_kind, kind)
            self.assertEqual(field.spinbox.cleanText(), '12.3')
            self.assertEqual(field.getValue(), 12.3456789)
            self.config.var_dict['Display']['decimals_' + kind] = 2
            field.spinbox.update_display()
            self.assertEqual(field.spinbox.cleanText(), '12.35')
            self.assertEqual(field.getValue(), 12.3456789)
            self.config.var_dict['Display']['decimals_' + kind] = 1
            field.close()

    def test_new_display_preferences_are_available_in_compiled_languages(self):
        messages = {
            'MyConfig': ('Number display', 'Display rounding does not change stored values. Editing uses the full precision.',
                         'Decimal places for millimeters:', 'Decimal places for inches:', 'Decimal places for angles:', 'Decimal places for feed rates:'),
            'ConfigurationHelp': ('Decimal places used only for GUI display; stored values retain full precision.',),
        }
        for language in ('de', 'fr', 'ru'):
            translator = QtCore.QTranslator()
            self.assertTrue(translator.load(str(Path(__file__).resolve().parents[1] /
                                               ('source/i18n/dxf2gcode_' + language + '.qm'))))
            for context, sources in messages.items():
                for source in sources:
                    self.assertTrue(translator.translate(context, source), (language, source))

    def test_line_edit_focus_and_input_retain_full_precision(self):
        field = QLineEdit()
        form, other = self.form(field)
        exact = 1.234567891234567
        set_number(field, exact, 'mm')
        self.assertEqual(field.text(), '1.235')
        field.setFocus()
        self.app.processEvents()
        self.assertEqual(field.text(), str(exact))
        self.assertFalse(field.isModified())
        other.setFocus()
        self.assertEqual(field._numeric_display.value, exact)
        field.setFocus()
        field.selectAll()
        QTest.keyClicks(field, '2.987654321987654')
        other.setFocus()
        self.assertEqual(field.text(), '2.988')
        self.assertEqual(field._numeric_display.value, 2.987654321987654)

    def test_spinbox_stores_loaded_and_edited_values_beyond_display_precision(self):
        for units, places in (('mm', 3), ('in', 5)):
            field = CorrectedDoubleSpinBox()
            field.number_units = units
            field.setRange(-1e9, 1e9)
            form, other = self.form(field)
            exact = 0.12345678912345678
            field.setValue(exact)
            self.assertEqual(field.text(), format(exact, '.%df' % places))
            field.setFocus()
            self.assertEqual(field.lineEdit().text(), repr(exact))
            other.setFocus()
            self.assertEqual(field.value(), exact)
            field.setFocus()
            field.lineEdit().selectAll()
            QTest.keyClicks(field.lineEdit(), '0.987654321987654')
            other.setFocus()
            self.assertEqual(field.value(), 0.987654321987654)
            self.assertEqual(field.text(), format(0.987654321987654, '.%df' % places))
            field.setValue(1e-20)
            field.setFocus()
            other.setFocus()
            self.assertEqual(field.value(), 1e-20)
            form.close()


if __name__ == '__main__':
    unittest.main()
