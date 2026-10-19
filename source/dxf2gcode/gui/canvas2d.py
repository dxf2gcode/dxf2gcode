# -*- coding: utf-8 -*-

############################################################################
#
#   Copyright (C) 2011-2015
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

"""
Special purpose canvas including all required plotting function etc.

@purpose:  Plotting all
"""

from __future__ import absolute_import
from __future__ import division

import logging
import math

from dxf2gcode.core.point import Point
from dxf2gcode.core.shape import Shape
from dxf2gcode.core.boundingbox import BoundingBox
from dxf2gcode.core.stmove import StMove
#TODO: check if can be removed:
#from dxf2gcode.core.arcgeo import ArcGeo
from dxf2gcode.gui.wpzero import WpZero
from dxf2gcode.gui.arrow import Arrow
from dxf2gcode.gui.routetext import RouteText
from dxf2gcode.gui.canvas import CanvasBase, MyDropDownMenu
from dxf2gcode.gui.scalebar import (ScaleBar, drawing_unit, scale_bar_enabled)

import dxf2gcode.globals.globals as g

import dxf2gcode.globals.constants as c
from dxf2gcode.Qt.QtWidgets import QGraphicsItem, QGraphicsView, QRubberBand, QGraphicsScene, QGraphicsLineItem
from dxf2gcode.Qt.QtGui import QPainterPath, QPen, QColor, QPainterPathStroker
from dxf2gcode.Qt import QtCore


logger = logging.getLogger("DxfImport.myCanvasClass")


class MyGraphicsView(CanvasBase):
    """
    This is the used Canvas to print the graphical interface of dxf2gcode.
    All GUI things should be performed in the View and plotting functions in
    the scene
    """

    def __init__(self, parent=None):
        """
        Initialisation of the View Object. This is called by the gui created
        with the QTDesigner.
        @param parent: Main is passed as a pointer for reference.
        """
        super(MyGraphicsView, self).__init__(parent)
        self.currentItem = None

        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)

        # self.setDragMode(QGraphicsView.RubberBandDrag )
        self.setDragMode(QGraphicsView.DragMode.NoDrag)

        self.parent = parent
        self.mppos = None

        # The scale bar is a viewport overlay (see drawForeground), it is not
        # part of the scene and therefore never part of the exported geometry.
        self.scaleBar = ScaleBar()

        self.rubberBand = QRubberBand(QRubberBand.Shape.Rectangle, self)
        self.prvRectRubberBand = QtCore.QRect()

    def tr(self, string_to_translate):
        """
        Translate a string using the QCoreApplication translation framework
        @param string_to_translate: a unicode string
        @return: the translated unicode string if it was possible to translate
        """
        return str(QtCore.QCoreApplication.translate('MyGraphicsView',
                                                           string_to_translate))

    def contextMenuEvent(self, event):
        """
        Create the contextmenu.
        @purpose: Links the new Class of ContextMenu to Graphicsview.
        """
        position = self.mapToGlobal(event.pos())
        GVPos = self.mapToScene(event.pos())
        real_pos = Point(GVPos.x(), -GVPos.y())

        menu = MyDropDownMenu(self.scene(), position, real_pos)

    def wheelEvent(self, event):
        """
        With Mouse Wheel the object is scaled
        @purpose: Scale by mouse wheel
        @param event: Event Parameters passed to function
        """
        delta = event.angleDelta().y()
        scale = (1000 + delta) / 1000.0
        self.scale(scale, scale)

    def mousePressEvent(self, event):
        """
        Right Mouse click shall have no function, Therefore pass only left
        click event
        @purpose: Change inherited mousePressEvent
        @param event: Event Parameters passed to function
        """

        if self.dragMode() == 1:
            super(MyGraphicsView, self).mousePressEvent(event)
        elif event.button() == QtCore.Qt.LeftButton:
            self.mppos = event.pos()
        else:
            pass

    def mouseReleaseEvent(self, event):
        """
        Right Mouse click shall have no function, Therefore pass only left
        click event
        @purpose: Change inherited mousePressEvent
        @param event: Event Parameters passed to function
        """
        delta = 2

        if self.dragMode() == 1:
            # if (event.key() == QtCore.Qt.Key_Shift):
            # self.setDragMode(QGraphicsView.NoDrag)
            super(MyGraphicsView, self).mouseReleaseEvent(event)

        # Selection only enabled for left Button
        elif event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.currentItems = []
            scene = self.scene()
            if scene and not self.isMultiSelect:
                for item in scene.selectedItems():
                    item.setSelected(False, False)
            # If the mouse button is pressed without movement of rubberband
            if self.rubberBand.isHidden():
                rect = QtCore.QRect(event.pos().x()-delta,
                                    event.pos().y() - delta,
                                    2 * delta, 2*delta)
                # logger.debug(rect)

                point = self.mapToScene(event.pos())
                min_distance = float(0x7fffffff)
                for item in self.items(rect):
                    itemDistance = item.contains_point(point)
                    if itemDistance < min_distance:
                        min_distance = itemDistance
                        self.currentItems = item
                if self.currentItems:
                    if self.currentItems.isSelected():
                        self.currentItems.setSelected(False, False)
                    else:
                        self.currentItems.setSelected(True, False)
            else:
                rect = self.rubberBand.geometry()
                self.currentItems = self.items(rect)
                self.rubberBand.hide()
                # logger.debug("Rubberband Selection")

                # All items in the selection
                # self.currentItems = self.items(rect)
                # print self.currentItems
                # logger.debug(rect)

                for item in self.currentItems:
                    if item.isSelected():
                        item.setSelected(False, False)
                    else:
                        # print (item.flags())
                        item.setSelected(True, False)

        else:
            pass

        self.mppos = None
        # super(MyGraphicsView, self).mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        """
        MouseMoveEvent of the Graphiscview. May also be used for the Statusbar.
        @purpose: Get the MouseMoveEvent and use it for the Rubberband Selection
        @param event: Event Parameters passed to function
        """
        if self.mppos is not None:
            Point = event.pos() - self.mppos
            if Point.manhattanLength() > 3:
                # print 'the mouse has moved more than 3 pixels since the oldPosition'
                # print "Mouse Pointer is currently hovering at: ", event.pos()
                rect = QtCore.QRect(self.mppos, event.pos())
                '''
                The following is needed because of PyQt5 doesn't like to switch from sign
                 it will keep displaying last rectangle, i.e. you can end up will multiple rectangles
                '''
                if self.prvRectRubberBand.width() > 0 and not rect.width() > 0 or rect.width() == 0 or\
                   self.prvRectRubberBand.height() > 0 and not rect.height() > 0 or rect.height() == 0:
                    self.rubberBand.hide()
                self.rubberBand.setGeometry(rect.normalized())
                self.rubberBand.show()
                self.prvRectRubberBand = rect

        scpoint = self.mapToScene(event.pos())

        # self.setStatusTip('X: %3.1f; Y: %3.1f' % (scpoint.x(), -scpoint.y()))
        # works not as supposed to
        self.setToolTip('X: %3.1f; Y: %3.1f' %(scpoint.x(), -scpoint.y()))

        super(MyGraphicsView, self).mouseMoveEvent(event)

    def autoscale(self):
        """
        Automatically zooms to the full extend of the current GraphicsScene
        """
        scene = self.scene()
        width = scene.BB.Pe.x - scene.BB.Ps.x
        height = scene.BB.Pe.y - scene.BB.Ps.y
        scext = QtCore.QRectF(scene.BB.Ps.x, -scene.BB.Pe.y, width * 1.05, height * 1.05)
        self.fitInView(scext, QtCore.Qt.AspectRatioMode.KeepAspectRatio)
        logger.debug(self.tr("Autoscaling to extend: %s") % scext)

    def scaleBarPixelsPerUnit(self):
        """
        The number of viewport pixels per drawing unit of the current drawing.
        The value is measured with the real view transformation (the same one
        that is used to draw the geometry), so it follows every zoom, pan and
        resize of the canvas.
        @return: the pixels per drawing unit or None if it cannot be measured
        """
        origin = self.mapToScene(QtCore.QPoint(0, 0))
        right = self.mapToScene(QtCore.QPoint(1, 0))
        scene_per_pixel = math.hypot(right.x() - origin.x(),
                                     right.y() - origin.y())
        if scene_per_pixel <= 0:
            return None
        # One scene unit is one drawing unit (millimetre or inch).
        return 1.0 / scene_per_pixel

    def updateScaleBar(self):
        """
        Recalculate the scale bar and repaint the canvas. This is called when
        the configuration (e.g. the 'show_scale_bar' option) or the
        measurement units changed.
        """
        self.scaleBar.state.reset()
        self.viewport().update()

    def drawForeground(self, painter, rect):
        """
        Draw the scale bar on top of the geometry.
        The scale bar is a viewport overlay: it is not an item of the scene,
        so it can never become part of the contour processing or of the
        exported G-Code.
        @param painter: the painter of the viewport
        @param rect: the exposed area of the scene
        """
        super(MyGraphicsView, self).drawForeground(painter, rect)

        if not scale_bar_enabled():
            return

        pixels_per_unit = self.scaleBarPixelsPerUnit()
        if not pixels_per_unit:
            return

        self.scaleBar.update(pixels_per_unit, drawing_unit())

        viewport_rect = self.viewport().rect()

        painter.save()
        try:
            # Draw in viewport coordinates: the zoom of the canvas is
            # compensated, so the scale bar always stays at the same place in
            # the visible area. The transformation of the canvas itself is
            # not modified, the drawing of the geometry is not influenced.
            origin = self.mapToScene(QtCore.QPoint(0, 0))
            painter.translate(origin)
            painter.scale(1.0 / pixels_per_unit, 1.0 / pixels_per_unit)
            self.scaleBar.paint(painter, viewport_rect)
        finally:
            painter.restore()

    def setShowPathDirections(self, flag):
        """
        This function is called by the Main Window from the Menubar.
        @param flag: This flag is true if all Path Direction shall be shown
        """
        scene = self.scene()
        for shape in scene.shapes:
            shape.starrow.setallwaysshow(flag)
            shape.enarrow.setallwaysshow(flag)
            shape.stmove.setallwaysshow(flag)

            if shape.Drill:
                shape.starrow.setallwaysshow(False)
                shape.enarrow.setallwaysshow(False)

    def resetAll(self):
        """
        Deletes the existing GraphicsScene.
        """
        scene = self.scene()
        del scene

class MyGraphicsScene(QGraphicsScene):
    """
    This is the Canvas used to print the graphical interface of dxf2gcode.
    The Scene is rendered into the previously defined mygraphicsView class.
    All performed plotting functions should be defined here.
    @sideeffect: None
    """
    def __init__(self):
        QGraphicsScene.__init__(self)

        self.shapes = []
        self.wpzero = None
        self.routearrows = []
        self.routetext = []
        self.expprv = None
        self.expcol = None
        self.expnr = 0

        self.showDisabledPaths = False

        self.BB = BoundingBox()

    def tr(self, string_to_translate):
        """
        Translate a string using the QCoreApplication translation framework
        @param string_to_translate: a unicode string
        @return: the translated unicode string if it was possible to translate
        """
        return str(QtCore.QCoreApplication.translate('MyGraphicsScene',
                                                           string_to_translate))

    def plotAll(self, shapes):
        """
        Instance is called by the Main Window after the defined file is loaded.
        It generates all ploting functionality. The parameters are generally
        used to scale or offset the base geometry (by Menu in GUI).
        """
        for shape in shapes:
            self.paint_shape(shape)
            self.addItem(shape)
            self.shapes.append(shape)
        self.draw_wp_zero()
        self.update()

    def repaint_shape(self, shape):
        # setParentItem(None) might let it crash, hence we rely on the garbage collector
        shape.stmove.hide()
        shape.starrow.hide()
        shape.enarrow.hide()
        del shape.stmove
        del shape.starrow
        del shape.enarrow
        self.paint_shape(shape)
        if not shape.isSelected():
            shape.stmove.hide()
            shape.starrow.hide()
            shape.enarrow.hide()

    def paint_shape(self, shape):
        """
        Create all plotting related parts of one shape.
        @param shape: The shape to be plotted.
        """
        start, start_ang = shape.get_start_end_points(True, True)
        shape.path = QPainterPath()
        shape.path.moveTo(start.x, -start.y)
        drawHorLine = lambda caller, start, end: shape.path.lineTo(end.x, -end.y)
        drawVerLine = lambda caller, start: None  # Not used in 2D mode
        shape.make_path(drawHorLine, drawVerLine)

        self.BB = self.BB.joinBB(shape.BB)

        shape.stmove = self.createstmove(shape)
        shape.starrow = self.createstarrow(shape)
        shape.enarrow = self.createenarrow(shape)
        shape.stmove.setParentItem(shape)
        shape.starrow.setParentItem(shape)
        shape.enarrow.setParentItem(shape)

    def draw_wp_zero(self):
        """
        This function is called while the drawing of all items is done. It plots
        the WPZero to the Point x=0 and y=0. This item will be enabled or
        disabled to be shown or not.
        """
        self.wpzero = WpZero(QtCore.QPointF(0, 0))
        self.addItem(self.wpzero)

    def createstarrow(self, shape):
        """
        This function creates the Arrows at the end point of a shape when the
        shape is selected.
        @param shape: The shape for which the Arrow shall be created.
        """

        length = 20
        start, start_ang = shape.get_start_end_points_physical(True, True, PPocket=True)
        
        arrow = Arrow(startp=start,
                      length=length,
                      angle=start_ang,
                      color=QColor(50, 200, 255),
                      pencolor=QColor(50, 100, 255))
        return arrow

    def createenarrow(self, shape):
        """
        This function creates the Arrows at the end point of a shape when the
        shape is selected.
        @param shape: The shape for which the Arrow shall be created.
        """
        length = 20
        end, end_ang = shape.get_start_end_points_physical(False, True, PPocket=shape.Pocket)
            
        arrow = Arrow(startp=end,
                      length=length,
                      angle=end_ang,
                      color=QColor(0, 245, 100),
                      pencolor=QColor(0, 180, 50),
                      startarrow=False)
        return arrow

    def createstmove(self, shape):
        """
        This function creates the Additional Start and End Moves in the plot
        window when the shape is selected
        @param shape: The shape for which the Move shall be created.
        """
        stmove = StMoveGUI(shape)
        return stmove

    def delete_opt_paths(self):
        """
        This function deletes all the plotted export routes.
        """
        # removeItem might let it crash, hence we rely on the garbage collector
        while self.routearrows:
            item = self.routearrows.pop()
            item.hide()
            del item

        while self.routetext:
            item = self.routetext.pop()
            item.hide()
            del item

    def addexproutest(self):
        self.expprv = Point(g.config.vars.Plane_Coordinates['axis1_start_end'],
                            g.config.vars.Plane_Coordinates['axis2_start_end'])
        self.expcol = QtCore.Qt.GlobalColor.darkRed

    def addexproute(self, exp_order, layer_nr):
        """
        This function initialises the Arrows of the export route order and its numbers.
        """
        for shape_nr in range(len(exp_order)):
            shape = self.shapes[exp_order[shape_nr]]
            st = self.expprv
            if shape.Pocket == True:
                start_en_points = shape.get_start_end_points(PPocket=True)
                en = start_en_points[0]
                self.expprv = start_en_points[1]

            else:
                en, self.expprv = shape.get_start_end_points_physical()
            self.routearrows.append(Arrow(startp=en,
                                          endp=st,
                                          color=self.expcol,
                                          pencolor=self.expcol))

            self.expcol = QtCore.Qt.GlobalColor.darkGray

            self.routetext.append(RouteText(text=("%s,%s" % (layer_nr, shape_nr+1)),
                                            startp=en))
            # self.routetext[-1].ItemIgnoresTransformations

            self.addItem(self.routearrows[-1])
            self.addItem(self.routetext[-1])

    def addexprouteen(self):
        st = self.expprv
        en = Point(g.config.vars.Plane_Coordinates['axis1_start_end'],
                   g.config.vars.Plane_Coordinates['axis2_start_end'])
        self.expcol = QtCore.Qt.GlobalColor.darkRed

        self.routearrows.append(Arrow(startp=en,
                                      endp=st,
                                      color=self.expcol,
                                      pencolor=self.expcol))

        self.addItem(self.routearrows[-1])

    def setShowDisabledPaths(self, flag):
        """
        This function is called by the Main Menu and is passed from Main to
        MyGraphicsView to the Scene. It performs the showing or hiding
        of enabled/disabled shapes.

        @param flag: This flag is true if hidden paths shall be shown
        """
        self.showDisabledPaths = flag

        for shape in self.shapes:
            if flag and shape.isDisabled():
                shape.show()
            elif not flag and shape.isDisabled():
                shape.hide()

class ShapeGUI(QGraphicsItem, Shape):
    PEN_NORMAL = QPen(QtCore.Qt.GlobalColor.black, 1, QtCore.Qt.PenStyle.SolidLine)
    PEN_NORMAL.setCosmetic(True)
    PEN_SELECT = QPen(QtCore.Qt.GlobalColor.red, 2, QtCore.Qt.PenStyle.SolidLine,
                      QtCore.Qt.PenCapStyle.RoundCap, QtCore.Qt.PenJoinStyle.RoundJoin)
    PEN_SELECT.setCosmetic(True)
    PEN_NORMAL_DISABLED = QPen(QtCore.Qt.GlobalColor.gray, 1, QtCore.Qt.PenStyle.DotLine)
    PEN_NORMAL_DISABLED.setCosmetic(True)
    PEN_SELECT_DISABLED = QPen(QtCore.Qt.GlobalColor.blue, 1, QtCore.Qt.PenStyle.DashLine)
    PEN_SELECT_DISABLED.setCosmetic(True)
    PEN_BREAK = QPen(QtCore.Qt.GlobalColor.magenta, 1, QtCore.Qt.PenStyle.SolidLine)
    PEN_BREAK.setCosmetic(True)
    PEN_LEFT = QPen(QtCore.Qt.GlobalColor.darkCyan, 1, QtCore.Qt.PenStyle.SolidLine)
    PEN_LEFT.setCosmetic(True)
    PEN_RIGHT = QPen(QtCore.Qt.GlobalColor.darkMagenta, 1, QtCore.Qt.PenStyle.SolidLine)
    PEN_RIGHT.setCosmetic(True)

    def __init__(self, nr, closed, parentEntity):
        QGraphicsItem.__init__(self)
        Shape.__init__(self, nr, closed, parentEntity)

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setAcceptedMouseButtons(QtCore.Qt.MouseButton.NoButton)

        self.selectionChangedCallback = None
        self.enableDisableCallback = None

        self.starrow = None
        self.enarrow = None

    def __str__(self):
        return super(ShapeGUI, self).__str__()

    def tr(self, string_to_translate):
        return super(ShapeGUI, self).tr(string_to_translate)

    def contains_point(self, point):
        """
        Method to determine the minimal distance from the point to the shape
        @param point: a QPointF
        @return: minimal distance
        """
        min_distance = float(0x7fffffff)
        ref_point = Point(point.x(), point.y())
        t = 0.0
        while t < 1.0:
            per_point = self.path.pointAtPercent(t)
            spline_point = Point(per_point.x(), per_point.y())
            distance = ref_point.distance(spline_point)
            if distance < min_distance:
                min_distance = distance
            t += 0.01
        return min_distance

    def setSelectionChangedCallback(self, callback):
        """
        Register a callback function in order to inform parents when the selection has changed.
        Note: we can't use QT signals here because ShapeClass doesn't inherits from a QObject
        @param callback: the function to be called, with the prototype callbackFunction(shape, select)
        """
        self.selectionChangedCallback = callback

    def setEnableDisableCallback(self, callback):
        """
        Register a callback function in order to inform parents when a shape has been enabled or disabled.
        Note: we can't use QT signals here because ShapeClass doesn't inherits from a QObject
        @param callback: the function to be called, with the prototype callbackFunction(shape, enabled)
        """
        self.enableDisableCallback = callback

    def setPen(self, pen):
        """
        Method to change the Pen of the outline of the object and update the
        drawing
        """
        self.pen = pen

    def paint(self, painter, option, widget):
        """
        Method will be triggered with each paint event. Possible to give options
        @param painter: Reference to std. painter
        @param option: Possible options here
        @param widget: The widget which is painted on.
        """
        if self.isSelected() and not self.isDisabled():
            painter.setPen(ShapeGUI.PEN_SELECT)
        elif not self.isDisabled():
            if self.parentLayer.isBreakLayer():
                painter.setPen(ShapeGUI.PEN_BREAK)
            elif self.cut_cor == 41:
                painter.setPen(ShapeGUI.PEN_LEFT)
            elif self.cut_cor == 42:
                painter.setPen(ShapeGUI.PEN_RIGHT)
            else:
                painter.setPen(ShapeGUI.PEN_NORMAL)
        elif self.isSelected():
            painter.setPen(ShapeGUI.PEN_SELECT_DISABLED)
        else:
            painter.setPen(ShapeGUI.PEN_NORMAL_DISABLED)

        painter.drawPath(self.path)

    def boundingRect(self):
        """
        Required method for painting. Inherited by Painterpath
        @return: Gives the Bounding Box
        """
        return self.path.boundingRect()

    def shape(self):
        """
        Reimplemented function to select outline only.
        @return: Returns the Outline only
        """
        painterStrock = QPainterPathStroker()
        painterStrock.setCurveThreshold(0.01)
        painterStrock.setWidth(0)

        stroke = painterStrock.createStroke(self.path)
        return stroke

    def setSelected(self, flag=True, blockSignals=True):
        """
        Override inherited function to turn off selection of Arrows.
        @param flag: The flag to enable or disable Selection
        """


        if Shape.isDrill(self):
            self.starrow.setSelected(False)
            self.enarrow.setSelected(False)
        else:
            self.starrow.setSelected(flag)
            self.enarrow.setSelected(flag)

        self.stmove.setSelected(flag)

        QGraphicsItem.setSelected(self, flag)
        Shape.setSelected(self, flag)

        if self.selectionChangedCallback and not blockSignals:
            self.selectionChangedCallback(self, flag)

    def setDisable(self, flag=False, blockSignals=True):
        """
        New implemented function which is in parallel to show and hide.
        @param flag: The flag to enable or disable Selection
        """
        # QGraphicsItem.setDisable(self, flag)
        Shape.setDisable(self, flag)
        scene = self.scene()

        if scene is not None:
            if not scene.showDisabledPaths and flag:
                self.hide()
                self.starrow.setSelected(False)
                self.enarrow.setSelected(False)
                self.stmove.setSelected(False)
            else:
                self.show()

        if self.enableDisableCallback and not blockSignals:
            self.enableDisableCallback(self, not flag)


class StMoveGUI(QGraphicsItem, StMove):

    # G41/G42 compensation contour and start moves (thicker solid line)
    PEN_COMP_LINE = QPen(QColor(50, 100, 255), 2, QtCore.Qt.PenStyle.SolidLine,
                         QtCore.Qt.PenCapStyle.RoundCap, QtCore.Qt.PenJoinStyle.RoundJoin)
    PEN_COMP_LINE.setCosmetic(True)
    # Pocket milling zig-zag lines (thinner solid line)
    PEN_POCKET_LINE = QPen(QColor(120, 170, 255), 1, QtCore.Qt.PenStyle.SolidLine,
                           QtCore.Qt.PenCapStyle.RoundCap, QtCore.Qt.PenJoinStyle.RoundJoin)
    PEN_POCKET_LINE.setCosmetic(True)
    # Rapid / positioning moves (dotted line)
    PEN_RAPID_MOVE = QPen(QColor(30, 60, 120), 1, QtCore.Qt.PenStyle.DotLine,
                          QtCore.Qt.PenCapStyle.RoundCap, QtCore.Qt.PenJoinStyle.RoundJoin)
    PEN_RAPID_MOVE.setCosmetic(True)

    def __init__(self, shape):
        QGraphicsItem.__init__(self)
        StMove.__init__(self, shape)

        self.allwaysshow = False
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        self.setAcceptHoverEvents(False)

        # Store paths permanently for repaint (zoom, drag, etc.)
        self._comp_path = QPainterPath()    # G41/G42 compensation contour
        self._pocket_path = QPainterPath()  # pocket milling zig-zag
        self._rapid_paths = []
        
        self._rebuild_paths_from_geos()

    def contains_point(self, point):
        """
        StMove cannot be selected. Return maximal distance
        """
        return float(0x7fffffff)

    def _rebuild_paths_from_geos(self):
        """Rebuild _comp_path, _pocket_path and _rapid_paths from current geos."""
        self._comp_path = QPainterPath()
        self._pocket_path = QPainterPath()
        self._rapid_paths = []
        
        try:
            first_geo = self.geos.abs_el(0)
            start = first_geo.get_start_end_points(True)
            prev_pe = Point(start.x, start.y)
        except Exception:
            return
        
        # Index where the pocket mill geometries start (set by
        # StMove.make_start_moves); everything before belongs to the
        # G41/G42 compensation contour / start moves.
        pocket_start = getattr(self, 'pocket_geos_start', None)
        
        comp_pos = None    # current end position of _comp_path
        pocket_pos = None  # current end position of _pocket_path
        force_break = False  # set after a PocketMove (retract/plunge)
        
        n = len(self.geos)
        for i in range(n):
            geo = self.geos[i]
            
            ps, pe = None, None
            
            # Detect RapidPos early before calling get_start_end_points
            geo_type_name = type(geo).__name__
            if 'Rapid' in geo_type_name and 'PocketMove' not in geo_type_name:
                # RapidPos has x,y coords directly since it inherits from Point
                ps, pe = geo, geo
            
            if ps is None or pe is None:
                if hasattr(geo, 'abs_geo') and geo.abs_geo is not None:
                    ag = geo.abs_geo
                    if hasattr(ag, 'Ps') and hasattr(ag, 'Pe'):
                        ps, pe = ag.Ps, ag.Pe
                    elif hasattr(ag, 'x') and hasattr(ag, 'y'):
                        ps = Point(ag.x, ag.y)
                        pe = Point(ag.x, ag.y)
                
                if ps is None or pe is None:
                    try:
                        ps = geo.get_start_end_points(True)
                        pe = geo.get_start_end_points(False)
                    except Exception:
                        continue
            
            is_rapid = ('Rapid' in geo_type_name or 
                       'PocketMove' in geo_type_name)
            
            eps = 1e-9
            dx = abs(pe.x - ps.x)
            dy = abs(pe.y - ps.y)
            if dx < eps and dy < eps:
                if 'PocketMove' in geo_type_name:
                    # Zero-length rapid between separate loops (retract and
                    # plunge at the same point): start a new subpath for the
                    # next loop so the loops stay visually separated.
                    force_break = True
                prev_pe = Point(pe.x, pe.y)
                continue
            
            # Draw connection gap from previous geo end to current geo start
            dx_gap = abs(ps.x - prev_pe.x)
            dy_gap = abs(ps.y - prev_pe.y)
            if dx_gap > 1e-6 or dy_gap > 1e-6:
                gap_rp = QPainterPath()
                gap_rp.moveTo(prev_pe.x, -prev_pe.y)
                gap_rp.lineTo(ps.x, -ps.y)
                self._rapid_paths.append(gap_rp)
            
            in_pocket = (pocket_start is not None and i >= pocket_start)
            
            if is_rapid:
                rp = QPainterPath()
                rp.moveTo(ps.x, -ps.y)
                rp.lineTo(pe.x, -pe.y)
                self._rapid_paths.append(rp)
            else:
                if in_pocket:
                    target = self._pocket_path
                    pos = pocket_pos
                else:
                    target = self._comp_path
                    pos = comp_pos
                
                # Start a new subpath if the target path is not at this geo's
                # start point, otherwise lineTo draws a phantom diagonal
                # across the pocket after a rapid move
                if (force_break or pos is None or
                        abs(ps.x - pos.x) > 1e-6 or
                        abs(ps.y - pos.y) > 1e-6):
                    target.moveTo(ps.x, -ps.y)
                drawHorLine = lambda caller, s, e: target.lineTo(e.x, -e.y)
                try:
                    geo.make_path(None, drawHorLine)
                except Exception:
                    pass
                force_break = False
                
                if in_pocket:
                    pocket_pos = Point(pe.x, pe.y)
                else:
                    comp_pos = Point(pe.x, pe.y)
            
            prev_pe = Point(pe.x, pe.y)
    
    def setSelected(self, flag=True, blockSignals=True):
        """
        Override inherited function to turn off selection of Arrows.
        @param flag: The flag to enable or disable Selection
        """
        if self.allwaysshow:
            pass
        elif flag is True:
            self.show()
        else:
            self.hide()

    def setallwaysshow(self, flag=False):
        """
        If the directions shall be allwaysshown the parameter will be set and
        all paths will be shown.
        @param flag: The flag to enable or disable Selection
        """
        self.allwaysshow = flag
        if flag is True:
            self.show()
        elif flag is True and self.isSelected():
            self.show()
        else:
            self.hide()

    def paint(self, painter, option, widget=None):
        """
        Method triggered on every paint event (including zoom/drag).
        Draw G41/G42 compensation lines (thick solid), pocket milling
        lines (thin solid) and rapid moves (dotted).
        """
        if (self._comp_path.isEmpty() and self._pocket_path.isEmpty()
                and not self._rapid_paths):
            return
        
        painter.setPen(self.PEN_COMP_LINE)
        painter.drawPath(self._comp_path)
        
        painter.setPen(self.PEN_POCKET_LINE)
        painter.drawPath(self._pocket_path)
        
        # Draw rapid/positioning paths as dotted lines
        for rp in self._rapid_paths:
            painter.setPen(self.PEN_RAPID_MOVE)
            painter.drawPath(rp)

    def boundingRect(self):
        """
        Required method for painting. Returns combined bounding box of
        compensation path, pocket path and all rapid move paths.
        """
        br = self._comp_path.boundingRect()
        br = br.united(self._pocket_path.boundingRect())
        for rp in self._rapid_paths:
            br = br.united(rp.boundingRect())
        return br

    def updateGeometry(self):
        """Rebuild paths when underlying geos change."""
        self._rebuild_paths_from_geos()
        self.prepareGeometryChange()
        self.update()
