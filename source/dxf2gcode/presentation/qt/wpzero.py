# -*- coding: utf-8 -*-

############################################################################
#
#   Copyright (C) 2008-2015
#    Christian Kohlöffel
#    Vinzenz Schulz
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
from __future__ import division

import dxf2gcode.domain.constants as c
from dxf2gcode.presentation.qt.qt_compat.QtWidgets import QGraphicsItem
from dxf2gcode.presentation.qt.qt_compat.QtGui import QPen
from dxf2gcode.presentation.qt.qt_compat import QtCore

class WpZero(QGraphicsItem):
    """
    class WpZero
    """
    def __init__(self, center, color=QtCore.Qt.GlobalColor.gray):
        self.sc = None
        super(WpZero, self).__init__()

        self.center = center
        self.allwaysshow = False
        self.color = color
        self.diameter = 23.0

    def contains_point(self, point):
        """
        WpZero cannot be selected. Return maximal distance
        """
        return float(0x7fffffff)

    def setSelected(self, *args):
        """
        Override inherited function - with possibility to be called with multiple arguments
        """
        pass

    def paint(self, painter, option, widget=None):
        """
        paint()
        """
        demat = painter.deviceTransform()
        self.sc = demat.m11()

        paint_workpiece_zero(painter, QtCore.QPointF(0, 0), 1 / self.sc, self.diameter, self.color)


    def boundingRect(self):
        """
        Override inherited function to enlarge selection of Arrow to include all
        @param flag: The flag to enable or disable Selection
        """
        if not self.sc:  # since this function is called before paint; and scale is unknown
            return QtCore.QRectF(0, 0, 1e-9, 1e-9)

        diameter = self.diameter / self.sc
        return QtCore.QRectF(-diameter / 2, -diameter / 2, diameter, diameter)


def paint_workpiece_zero(painter, center, unit=1., diameter=23., color=QtCore.Qt.GlobalColor.gray):
    outer = diameter * unit / 2
    inner = (diameter - 4) * unit / 2
    rectangle = QtCore.QRectF(center.x() - inner, center.y() - inner, 2 * inner, 2 * inner)
    pen = QPen(QtCore.Qt.GlobalColor.darkGray, 1)
    pen.setCosmetic(True)
    painter.save()
    painter.setPen(pen)
    painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
    painter.drawEllipse(center, outer, outer)
    painter.drawEllipse(rectangle)
    painter.drawPie(rectangle, 90 * 16, 90 * 16)
    painter.setBrush(color)
    painter.drawPie(rectangle, 270 * 16, 90 * 16)
    painter.restore()
