"""Show derived tree references without changing the editable selection."""
from dxf2gcode.presentation.qt.qt_compat import QtCore
from dxf2gcode.presentation.qt.qt_compat.QtGui import QPalette
from dxf2gcode.presentation.qt.qt_compat.QtWidgets import QStyledItemDelegate, QStyle

REFERENCE_ROLE = int(QtCore.Qt.ItemDataRole.UserRole)+18


class ReferenceDelegate(QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        reference = index.data(REFERENCE_ROLE)
        if reference:
            option.state |= QStyle.StateFlag.State_Selected
            if reference == 1:
                option.palette.setColor(QPalette.ColorRole.Highlight,
                    option.palette.color(QPalette.ColorRole.Highlight).lighter(160))
                option.palette.setColor(QPalette.ColorRole.HighlightedText,
                    option.palette.color(QPalette.ColorRole.Text))
