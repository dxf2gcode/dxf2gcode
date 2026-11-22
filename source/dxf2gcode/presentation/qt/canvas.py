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

from __future__ import absolute_import

import logging

import dxf2gcode.bootstrap.runtime_state as g
#TODO: check if can be removed:
#from dxf2gcode.domain.geometry.linegeo import LineGeo
#from dxf2gcode.domain.geometry.point import Point
from dxf2gcode.domain.geometry.arcgeo import ArcGeo
#from dxf2gcode.domain.geometry.holegeo import HoleGeo

from dxf2gcode.application.shapes import SetMachiningMode
from dxf2gcode.domain.project.machining import pocket_supported

import dxf2gcode.domain.constants as c
from dxf2gcode.presentation.qt.qt_compat.QtWidgets import QGraphicsView, QMenu
from dxf2gcode.presentation.qt.qt_compat import QtCore
from dxf2gcode.presentation.qt.qt_compat.QtGui import QMouseEvent, QKeyEvent, QIcon, QPixmap, QPainter, QPen
from dxf2gcode.presentation.qt.qt_compat.QtWidgets import QApplication
from dxf2gcode.presentation.qt.qt_compat.QtCore import Qt


logger = logging.getLogger("Gui.Canvas")

_MIXED_SELECTION_ICON = None


def mixedSelectionIcon():
    """
    A small "partially checked" icon (a boxed minus), drawn programmatically so
    no resource file is needed. It is shown to the left of a context menu entry
    to indicate a mixed selection state (QAction has no native
    Qt.PartiallyChecked display).
    """
    global _MIXED_SELECTION_ICON
    if _MIXED_SELECTION_ICON is None:
        size = 14
        pixmap = QPixmap(size, size)
        pixmap.fill(QtCore.Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        pen = QPen(QtCore.Qt.GlobalColor.black)
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawRect(1, 1, size - 3, size - 3)              # box frame
        painter.drawLine(4, size // 2, size - 5, size // 2)     # "minus"
        painter.end()
        _MIXED_SELECTION_ICON = QIcon(pixmap)
    return _MIXED_SELECTION_ICON


def Canvas(parent=None):
    from dxf2gcode.presentation.qt.canvas2d import MyGraphicsView
    return MyGraphicsView(parent)


class CanvasBase(QGraphicsView):
    def __init__(self, parent=None):
        super(CanvasBase, self).__init__(parent)

        self.isMultiSelect = False

        self.setMouseTracking (True)

    def update(self, *args):
        super().update(*args)
        preview = getattr(self, 'machining_preview', None)
        if preview is not None:
            preview.overlay.update()


class MyDropDownMenu(QMenu):
    def __init__(self, canvas_scene, position, clicked):
        QMenu.__init__(self)

        self.clicked = clicked

        self.canvas_scene = canvas_scene

        self.selectedItems = [shape for shape in canvas_scene.shapes if shape.isSelected()]

        zero_action = self.addAction(self.tr("Move workpiece zero here ..."))
        zero_action.setToolTip(self.tr("Open the workpiece zero dialog for this point. Snapping is optional in the dialog."))
        zero_action.setEnabled(bool(canvas_scene.shapes))
        zero_action.triggered.connect(self.moveWorkpieceZeroHere)
        if clicked is None:
            self.setToolTipsVisible(True)
        self.requireDrawingPoint(zero_action)

        panel = getattr(getattr(g, 'window', None), 'machining_panel', None)
        if panel is not None and panel.binding is not None:
            if panel.modifiers.mode:
                self.clear()
                return
            if self.selectedItems:
                identities = panel.canvas_operation_ids(self.selectedItems)
                enabled = bool(identities)
                self.addSeparator()
                self.addAction(self.tr('Invert Selection'), self.invertSelection)
                for text, value in (('Disable Selection', False), ('Enable Selection', True)):
                    action = self.addAction(self.tr(text))
                    action.setEnabled(enabled)
                    action.triggered.connect(lambda checked=False, value=value:
                                             panel.execute(lambda: panel.commands.update_entries(identities, enabled=value)))
                self.addSeparator()
                for text, operation in (('Switch Direction', 'reverse'), ('Set Nearest StartPoint', 'nearest'),
                                        ('Set Sharpest StartPoint', 'sharpest')):
                    action = self.addAction(self.tr(text))
                    action.setEnabled(enabled)
                    if operation == 'nearest':
                        self.requireDrawingPoint(action)
                    action.triggered.connect(lambda checked=False, operation=operation:
                                             self.editMachiningPaths(panel, identities, operation))
                self.addSeparator()
                panel.add_machining_actions(self, identities, canvas_style=True)
                self.addSeparator()
                self.addAction(panel.tr('Assign machining…'), lambda checked=False:
                               panel.assign_machining(shapes=self.selectedItems, global_position=position))
            self.addSeparator()
            draw_action = self.addAction(panel.modifiers.tr('Draw new tab region…'), panel.modifiers.start_draw)
            self.requireDrawingPoint(draw_action)
            self.exec(position)
            return

        if len(self.selectedItems) == 0:
            self.exec(position)
            return

        self.addSeparator()

        invertAction = self.addAction(self.tr("Invert Selection"))
        disableAction = self.addAction(self.tr("Disable Selection"))
        enableAction = self.addAction(self.tr("Enable Selection"))

        self.addSeparator()

        swdirectionAction = self.addAction(self.tr("Switch Direction"))
        SetNxtStPAction = self.addAction(self.tr("Set Nearest StartPoint"))
        self.requireDrawingPoint(SetNxtStPAction)
        setSharStAction = self.addAction(self.tr("Set Sharpest StartPoint"))

        self.addSeparator()
        
        allClosed = all(item.closed for item in self.selectedItems)
        allArcs = all(item.geos and all(isinstance(geo, ArcGeo)
                                       for geo in item.geos)
                      for item in self.selectedItems)

        # The menu and planner share the same machine/compensation rule.
        if (allClosed and pocket_supported(
                g.config.machine_type,
                g.config.vars.Cutter_Compensation["done_by_machine"])):
            self.PocketAction = self.addAction(self.tr("Pocket Mill"))
            self.PocketAction.setCheckable(True)
            self.PocketAction.triggered.connect(self.setPocket)
            self._updateBoolActionState(self.PocketAction, "Pocket")

        #ONly allow it it's a closed shaep
        if (allClosed == True) and (allArcs == True):
            self.DrillAction = self.addAction(self.tr("Drill Bore"))
            self.DrillAction.setCheckable(True)
            #HoleAction.triggered.connect(self.setHoleGeo)
            self.DrillAction.triggered.connect(self.setDrill)
            self._updateBoolActionState(self.DrillAction, "Drill")
            

        if g.config.machine_type == 'drag_knife':
            pass
        else:
            self.addSeparator()
            submenu1 = QMenu(self.tr('Cutter Compensation'), self)
            self.noCompAction = submenu1.addAction(self.tr("G40 No Compensation"))
            self.noCompAction.setCheckable(True)
            self.leCompAction = submenu1.addAction(self.tr("G41 Left Compensation"))
            self.leCompAction.setCheckable(True)
            self.reCompAction = submenu1.addAction(self.tr("G42 Right Compensation"))
            self.reCompAction.setCheckable(True)

            self.compMenuAction = submenu1.menuAction()
            logger.debug(self.tr("The selected shapes have the following direction: %i") % (self.calcMenuDir()))
            self.checkMenuDir(self.calcMenuDir())

            self.addMenu(submenu1)

        invertAction.triggered.connect(self.invertSelection)
        disableAction.triggered.connect(self.disableSelection)
        enableAction.triggered.connect(self.enableSelection)

        swdirectionAction.triggered.connect(self.switchDirection)
        SetNxtStPAction.triggered.connect(self.setNearestStPoint)
        setSharStAction.triggered.connect(self.setSharpestStPoint)



        if g.config.machine_type == 'drag_knife':
            pass
        else:
            self.noCompAction.triggered.connect(self.setNoComp)
            self.leCompAction.triggered.connect(self.setLeftComp)
            self.reCompAction.triggered.connect(self.setRightComp)

        self.exec(position)

    def requireDrawingPoint(self, action):
        if self.clicked is None:
            action.setEnabled(False)
            action.setToolTip(self.tr("Available in top view."))

    def tr(self, string_to_translate):
        """
        Translate a string using the QCoreApplication translation framework
        @param string_to_translate: a unicode string
        @return: the translated unicode string if it was possible to translate
        """
        return str(QtCore.QCoreApplication.translate('MyDropDownMenu',
                                                           string_to_translate))

    def editMachiningPaths(self, panel, identities, operation):
        points = {}
        if operation == 'nearest':
            for _, entry in panel.commands.entries(panel.binding.project, identities):
                points[entry.id] = (self.clicked.x, self.clicked.y)
        panel.execute(lambda: panel.commands.edit_operation_paths(identities, operation, points))

    def moveWorkpieceZeroHere(self):
        g.window.moveWorkpieceZero(point=self.clicked)

    def calcMenuDir(self):
        """
        This method returns the direction of the selected items. If there are
        different cutter directions in the selection 0 is returned, else
        1 for Left and 2 for right.
        """
        dir = self.selectedItems[0].cut_cor
        for item in self.selectedItems:
            if not(dir == item.cut_cor):
                return -1

        return dir-40

    def checkMenuDir(self, dir):
        """
        This method checks the buttons in the Contextmenu for the direction of
        the selected items.
        @param dir: The direction of the items -1=different, 0=None, 1=left, 2=right
        """
        self.noCompAction.setChecked(False)
        self.leCompAction.setChecked(False)
        self.reCompAction.setChecked(False)

        if dir == 0:
            self.noCompAction.setChecked(True)
        elif dir == 1:
            self.leCompAction.setChecked(True)
        elif dir == 2:
            self.reCompAction.setChecked(True)

        # Mixed cutter compensation (dir == -1): no option is checked; show the
        # "mixed" icon on the submenu action instead (its text stays unchanged).
        comp_action = getattr(self, "compMenuAction", None)
        if comp_action is not None:
            comp_action.blockSignals(True)
            try:
                if dir == -1:
                    comp_action.setIcon(mixedSelectionIcon())
                else:
                    comp_action.setIcon(QIcon())
            finally:
                comp_action.blockSignals(False)

    def _selectionBoolState(self, attr):
        """
        Aggregate the boolean attribute 'attr' over the selected shapes.
        @return: "on" if all are True, "off" if all are False, "mixed" otherwise
        """
        values = [bool(getattr(shape, attr)) for shape in self.selectedItems]
        if all(values):
            return "on"
        if not any(values):
            return "off"
        return "mixed"

    def _updateBoolActionState(self, action, attr):
        """
        Update a checkable action to reflect the aggregated state of the
        selection: checked when all shapes have the attribute set, unchecked
        when none has it, and a dedicated "mixed" icon (drawn without a check
        mark) when the selection is mixed. The action text is never touched.
        @param action: the checkable QAction
        @param attr: the boolean attribute name on the shapes
        """
        state = self._selectionBoolState(attr)
        action.blockSignals(True)  # never fire triggered/toggled here
        try:
            if state == "mixed":
                action.setChecked(False)
                action.setIcon(mixedSelectionIcon())
            else:
                action.setChecked(state == "on")
                action.setIcon(QIcon())
        finally:
            action.blockSignals(False)

    def invertSelection(self):
        """
        This function is called by the Contextmenu of the Graphicsview.
        @purpose: Inverts the selection of all shapes.
        """
        for shape in self.canvas_scene.shapes:
            self.canvas_scene.set_shape_selected(
                shape, not shape.isSelected())
            g.window.TreeHandler.updateShapeSelection(shape, shape.isSelected())
        self.canvas_scene.update()

    def disableSelection(self):
        """
        Disable all shapes which are currently selected. Based on the view
        options they are not shown, or showed in a different color
        """
        for shape in self.selectedItems:
            if shape.allowedToChange:
                self.canvas_scene.set_shape_disabled(shape, True)
                g.window.TreeHandler.updateShapeEnabling(shape, False)
        self.canvas_scene.update()

    def enableSelection(self):
        """
        Enable all shapes which are currently selected. Based on the view
        options they are not shown, or showed in a different color
        """
        for shape in self.selectedItems:
            if shape.allowedToChange:
                self.canvas_scene.set_shape_disabled(shape, False)
                g.window.TreeHandler.updateShapeEnabling(shape, True)
        self.canvas_scene.update()

    def switchDirection(self):
        """
        Switch the Direction of all items. For example from CW direction to CCW
        """
        for shape in self.selectedItems:
            shape.reverse()
            logger.debug(self.tr('Switched Direction at Shape Nr: %i') % shape.nr)
            self.canvas_scene.repaint_shape(shape)
        self.canvas_scene.update()
        g.window.TreeHandler.prepareExportOrderUpdate()

    def setNearestStPoint(self):
        """
        Search the nearest StartPoint to the clicked position of all selected shapes.
        """
        for shape in self.selectedItems:
            shape.setNearestStPoint(self.clicked)
            self.canvas_scene.repaint_shape(shape)
        self.canvas_scene.update()
        g.window.TreeHandler.prepareExportOrderUpdate()

    def setSharpestStPoint(self):
        """
        Search the sharpest StartPoint of all selected shapes.
        """
        for shape in self.selectedItems:
            shape.setSharpestStPoint()
            self.canvas_scene.repaint_shape(shape)
        self.canvas_scene.update()
        g.window.TreeHandler.prepareExportOrderUpdate()

    def _setMachiningMode(self, action, value=None):
        if not self.selectedItems:
            return
        before = [(shape.Drill, shape.Pocket) for shape in self.selectedItems]
        SetMachiningMode().execute(self.selectedItems, action, value)
        tree = g.window.TreeHandler
        for shape, (drill, pocket) in zip(self.selectedItems, before):
            if action == 'pocket' or pocket != shape.Pocket:
                tree.updatePocketMill(shape, shape.Pocket)
            if action == 'drill' or drill != shape.Drill:
                tree.updateDrill(shape, shape.Drill)
            self.canvas_scene.repaint_shape(shape)
        for name, attribute in (('PocketAction', 'Pocket'), ('DrillAction', 'Drill')):
            menu_action = getattr(self, name, None)
            if menu_action is not None:
                self._updateBoolActionState(menu_action, attribute)
        if hasattr(self, 'noCompAction'):
            self.checkMenuDir(self.calcMenuDir())
        refresh = getattr(tree, 'updateToolParameters', None)
        if refresh is not None:
            refresh()
        self.canvas_scene.update()

    def setNoComp(self):
        self._setMachiningMode('compensation', 40)

    def setLeftComp(self):
        self._setMachiningMode('compensation', 41)

    def setRightComp(self):
        self._setMachiningMode('compensation', 42)

    def setPocket(self):
        self._setMachiningMode('pocket')

    def setDrill(self):
        self._setMachiningMode('drill')
