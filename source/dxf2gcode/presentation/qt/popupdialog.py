# -*- coding: utf-8 -*-

############################################################################
#
#   Copyright (C) 2010-2014
#    Christian Kohlöffel
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

from __future__ import absolute_import

import logging
from math import isfinite

import dxf2gcode.domain.constants as c
from dxf2gcode.presentation.qt.qt_compat.QtWidgets import QDialog, QVBoxLayout, QFrame, QGridLayout, QLabel, QLineEdit, QPushButton, QCheckBox
from dxf2gcode.presentation.qt.qt_compat.QtGui import QIcon
from dxf2gcode.presentation.qt.qt_compat import QtCore


logger = logging.getLogger("Gui.PopUpDialog")


class PopUpDialog(QDialog):

    def __init__(self, title="Test", label='Value1', value=1.0, wtype="lineEdit", haveAuto=False,
                 decimals=None, snap=None):
        super(PopUpDialog, self).__init__()

        logger.debug(title)
        logger.debug(label)
        logger.debug(value)
        logger.debug(wtype)

        self.title = title
        self.wtype = wtype
        self.label = label
        self.value = value
        self.decimals = decimals
        self.snap = snap

        self.result = None

        if not(len(label) == len(value)):
            raise Exception("Number of labels different to number of values")

        self.initUI(haveAuto)

    def tr(self, string_to_translate):
        """
        Translate a string using the QCoreApplication translation framework
        @param: string_to_translate: a unicode string
        @return: the translated unicode string if it was possible to translate
        """
        return str(QtCore.QCoreApplication.translate('PopUpDialog',
                                                           string_to_translate))

    def initUI(self, haveAuto):

        vbox = QVBoxLayout(self)

        top = QFrame(self)
        top.setFrameShape(QFrame.Shape.StyledPanel)

        bottom = QFrame(self)
        bottom.setFrameShape(QFrame.Shape.StyledPanel)

        grid1 = QGridLayout()
        grid1.setSpacing(10)
        self.lineLabel = []
        self.lineElement = []

        for i in range(len(self.label)):
            self.lineLabel.append(QLabel(self.label[i]))

            grid1.addWidget(self.lineLabel[i], i, 0)
            if self.wtype[i]=="lineEdit":
                text = self._display_value(self.value[i])
                self.lineElement.append(QLineEdit(text))
                self.lineElement[-1]._original_popup_text = text
                self.lineElement[-1]._original_popup_value = self.value[i]
                grid1.addWidget(self.lineElement[-1], i, 1)
            elif self.wtype[i]=="checkBox":
                self.lineElement.append(QCheckBox())
                self.lineElement[-1].setChecked(self.value[i])
                #self.lineElement[-1].stateChanged.connect(lambda:self.btnstate(self.lineElement[-1]))
                grid1.addWidget(self.lineElement[-1], i, 1)




        if self.snap is not None:
            self.snapButton = QPushButton(self.tr("Snap to nearest contour point"))
            self.snapButton.setToolTip(self.tr("Use a start-point candidate of the selected contour without changing its start point or direction."))
            self.snapButton.setAutoDefault(False)
            self.snapButton.clicked.connect(self.cbSnap)
            grid1.addWidget(self.snapButton, len(self.label), 0, 1, 2)
            for element in self.lineElement:
                if isinstance(element, QLineEdit):
                    element.textChanged.connect(self._update_snap_enabled)
            self._update_snap_enabled()
        top.setLayout(grid1)

        grid2 = QGridLayout()
        grid2.setSpacing(5)

        autoButton = QPushButton(self.tr("Auto"))
        okButton = QPushButton(self.tr("OK"))
        cancelButton = QPushButton(self.tr("Cancel"))
        self.autoButton, self.okButton, self.cancelButton = autoButton, okButton, cancelButton
        autoButton.setAutoDefault(False)
        cancelButton.setAutoDefault(False)
        okButton.setDefault(True)

        autoButton.clicked.connect(self.cbAuto)
        okButton.clicked.connect(self.cbOK)
        cancelButton.clicked.connect(self.cbCancel)

        grid2.addWidget(okButton, 0, 0)
        if haveAuto:
            grid2.addWidget(autoButton, 0, 1)
        grid2.addWidget(cancelButton, 0, 2 if haveAuto else 1)

        bottom.setLayout(grid2)

        vbox.addWidget(top)
        vbox.addWidget(bottom)

        self.setLayout(vbox)

        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowType.WindowContextHelpButtonHint)
        self.setWindowTitle(self.title)
        self.setWindowIcon(QIcon(":images/dxf2gcode.ico"))

        self.exec()

    def _display_value(self, value):
        if self.decimals is None:
            return str(value)
        text = format(float(value), '.%df' % self.decimals).rstrip('0').rstrip('.')
        return '0' if text == '-0' else text

    def cbAuto(self):
        """
        Determine WP zero automatically by finding the left/bottom-most shape
        """
        self.result = 'Auto'
        self.close()

    def cbOK(self):
        self.result = self._current_values()
        self.close()

    def _current_values(self):
        values = []
        for lineElement in self.lineElement:
            if isinstance(lineElement,QLineEdit):
                if (self.decimals is not None and not lineElement.isModified() and
                        lineElement.text() == lineElement._original_popup_text):
                    values.append(lineElement._original_popup_value)
                else:
                    values.append(lineElement.text())
            elif isinstance(lineElement,QCheckBox):
                values.append(lineElement.isChecked())
        return values

    def _update_snap_enabled(self):
        try:
            valid = all(isfinite(float(value)) for value in self._current_values())
        except (TypeError, ValueError):
            valid = False
        self.snapButton.setEnabled(valid)

    def cbSnap(self):
        if self.snap is None or not self.snapButton.isEnabled():
            return
        values = self.snap(self._current_values())
        for element, value in zip(self.lineElement, values):
            text = self._display_value(value)
            element.setText(text)
            element._original_popup_text = text
            element._original_popup_value = value

    def cbCancel(self):
        logger.debug('Cancel')
        self.close()

