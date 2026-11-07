"""Presentation precision, independent of stored/input floating-point values."""

from numbers import Real

import dxf2gcode.bootstrap.runtime_state as g
from dxf2gcode.presentation.qt.qt_compat import QtCore


def display_decimals(units=None, kind='length', config=None):
    config = config or getattr(g, 'config', None)
    settings = getattr(config, 'var_dict', {}).get('Display', {})
    if units is None:
        units = 'mm' if getattr(config, 'metric', True) else 'in'
    key, default = ('decimals_angle', 1) if kind == 'angle' else ('decimals_feed', 1) if kind == 'feed' else (
        ('decimals_in', 5) if units == 'in' else ('decimals_mm', 3))
    return int(settings.get(key, default))


def format_number(value, units=None, kind='length', decimals=None):
    if value is None:
        return ''
    if not isinstance(value, Real) or isinstance(value, bool):
        return str(value)
    if kind == 'integer' and float(value).is_integer():
        return str(int(value))
    places = display_decimals(units, kind) if decimals is None else decimals
    text = format(value, '.%df' % places)
    # Avoid a negative zero created only by display rounding.
    return text[1:] if text.startswith('-') and float(text) == 0 else text


class NumericDisplay(QtCore.QObject):
    """Show full precision during input without writing formatted text back."""
    def __init__(self, field):
        super().__init__(field)
        self.field = field
        self.value = None
        self.units = None
        self.kind = 'length'
        self.decimals = None
        self.edited_text = None
        field.textEdited.connect(self.edited)
        field.installEventFilter(self)
        field.editingFinished.connect(self.finished)

    def set_value(self, value, units=None, kind='length', decimals=None):
        self.edited_text = None
        self.value, self.units, self.kind, self.decimals = value, units, kind, decimals
        self.show_value(self.field.hasFocus())

    def show_value(self, editing=False):
        value = self.value
        text = (str(value) if editing and value is not None else
                format_number(value, self.units, self.kind, self.decimals))
        self.field.setText(text)
        self.field.setModified(False)

    def eventFilter(self, watched, event):
        # During native destruction Qt may already expose only QWidget.
        if not hasattr(watched, 'isModified'):
            return False
        if event.type() == QtCore.QEvent.Type.FocusIn and not watched.isReadOnly():
            if not watched.isModified():
                self.show_value(True)
        elif event.type() == QtCore.QEvent.Type.FocusOut and not watched.isModified():
            self.show_value()
        return False

    def edited(self, text):
        self.edited_text = text

    def finished(self):
        if self.field.isModified():
            try:
                self.value = float(self.field.text().replace(',', '.'))
            except ValueError:
                return
        if not self.field.hasFocus():
            self.show_value()


def set_number(field, value, units=None, kind='length', decimals=None):
    if not hasattr(field, '_numeric_display'):
        field._numeric_display = NumericDisplay(field)
    field._numeric_display.set_value(value, units, kind, decimals)
