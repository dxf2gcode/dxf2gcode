# -*- coding: utf-8 -*-

############################################################################
#
#   Copyright (C) 2010-2014
#    Christian Kohl�ffel
#    Jean-Paul Schouwstra
#
#   This file is part of DXF2GCODE.
#
#   DXF2GCODE is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   DXF2GCODE is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with DXF2GCODE.  If not, see <http://www.gnu.org/licenses/>.
#
############################################################################

from dxf2gcode.presentation.qt.qt_compat.QtWidgets import QDialog, QVBoxLayout, QTextBrowser, QWidget
from dxf2gcode.presentation.qt.qt_compat.QtGui import QIcon, QPainter, QPixmap, QTextCursor
from dxf2gcode.presentation.qt.qt_compat import QtCore

import logging

logger = logging.getLogger("Gui.AboutDialog")


class AboutLogo(QWidget):
    """Draw the original image smoothly at the current screen's pixel density."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(320, 116)
        self.pixmap = QPixmap(":images/dxf2gcode-logo-1024.png")

    def paintEvent(self, event):
        size = self.pixmap.size().scaled(
            self.size(), QtCore.Qt.AspectRatioMode.KeepAspectRatio)
        target = QtCore.QRect(QtCore.QPoint(), size)
        target.moveCenter(self.rect().center())
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.drawPixmap(target, self.pixmap)


class AboutDialog(QDialog):
    def __init__(self, title="Test", message="Test Text"):
        super(AboutDialog, self).__init__()

        self.title = title
        self.message = message

        self.initUI()

    def initUI(self):
        """
        initUI()
        """

        vbox = QVBoxLayout(self)
        self.logo = AboutLogo(self)
        vbox.addWidget(self.logo, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter)
        vbox.addSpacing(12)

        self.text = QTextBrowser()
        self.text.setReadOnly(True)
        self.text.setOpenExternalLinks(True)
        self.text.append(self.message)
        self.text.moveCursor(QTextCursor.MoveOperation.Start)
        self.text.ensureCursorVisible()

        vbox.addWidget(self.text)

        self.setLayout(vbox)
        self.setMinimumSize(550, 450)
        self.resize(550, 600)
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowType.WindowContextHelpButtonHint)
        self.setWindowTitle(self.title)
        self.setWindowIcon(QIcon(":images/dxf2gcode.ico"))

        self.exec()
