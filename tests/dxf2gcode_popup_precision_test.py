"""Coordinate display precision must not round untouched machining values."""

from importlib import import_module
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'source'))
from dxf2gcode.presentation.qt.popupdialog import PopUpDialog
from dxf2gcode.presentation.qt.qt_compat import QtCore, PYQT_VERSION
from dxf2gcode.presentation.qt.qt_compat.QtWidgets import QApplication

QTest = import_module('PyQt%d.QtTest' % PYQT_VERSION).QTest


class TestPopupPrecision(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def dialog(self, digits, snap=None):
        values = [15.7414481404958, -6.42960557851239]
        with patch.object(PopUpDialog, 'exec', return_value=0):
            dialog = PopUpDialog('Zero', ['X', 'Y'], values, ['lineEdit']*2, True, decimals=digits, snap=snap)
        dialog.show()
        self.app.processEvents()
        self.addCleanup(dialog.close)
        return dialog, values

    def test_mm_and_inch_display_and_unchanged_enter_keep_exact_values(self):
        for digits, expected in ((3, ['15.741', '-6.43']), (5, ['15.74145', '-6.42961'])):
            with self.subTest(digits=digits):
                dialog, original = self.dialog(digits)
                self.assertEqual([field.text() for field in dialog.lineElement], expected)
                self.assertLess(dialog.okButton.x(), dialog.autoButton.x())
                self.assertLess(dialog.autoButton.x(), dialog.cancelButton.x())
                self.assertTrue(dialog.okButton.isDefault())
                self.assertFalse(dialog.autoButton.isDefault())
                dialog.lineElement[0].setFocus()
                QTest.keyClick(dialog.lineElement[0], QtCore.Qt.Key.Key_Tab)
                QTest.keyClick(dialog.lineElement[1], QtCore.Qt.Key.Key_Return)
                self.assertEqual(dialog.result, original)
                self.assertTrue(all(isinstance(value, float) for value in dialog.result))

    def test_only_edited_coordinate_is_replaced(self):
        dialog, original = self.dialog(3)
        field = dialog.lineElement[0]
        field.setFocus()
        field.selectAll()
        QTest.keyClicks(field, '2.125')
        dialog.okButton.click()
        self.assertEqual(dialog.result, ['2.125', original[1]])

    def test_cancel_keeps_original_values(self):
        dialog, original = self.dialog(5)
        dialog.lineElement[0].setText('99')
        dialog.cancelButton.click()
        self.assertIsNone(dialog.result)
        self.assertEqual(dialog.value, original)

    def test_optional_snap_accepts_exact_values_and_closes_immediately(self):
        from unittest.mock import Mock
        snapped = [1.234567891234, -3.456789123456]
        callback = Mock(return_value=snapped)
        dialog, original = self.dialog(3, callback)
        dialog.snapButton.click()
        callback.assert_called_once_with(original)
        self.assertFalse(dialog.isVisible())
        self.assertEqual(dialog.value, original)
        self.assertEqual(dialog.result, snapped)

    def test_invalid_input_disables_snap_and_cancel_does_not_apply(self):
        from unittest.mock import Mock
        callback = Mock(return_value=[1.234567, 3.456789])
        dialog, original = self.dialog(5, callback)
        dialog.lineElement[0].clear()
        self.assertFalse(dialog.snapButton.isEnabled())
        dialog.snapButton.click()
        callback.assert_not_called()
        dialog.lineElement[0].setText('1.25')
        self.assertTrue(dialog.snapButton.isEnabled())
        dialog.cancelButton.click()
        self.assertIsNone(dialog.result)
        self.assertEqual(dialog.value, original)


if __name__ == '__main__':
    unittest.main()
