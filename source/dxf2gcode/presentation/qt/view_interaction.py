"""Shared appearance and selection rules for experimental view adapters."""

from math import dist
from dxf2gcode.presentation.qt.qt_compat import QtCore
from dxf2gcode.presentation.qt.qt_compat.QtGui import QPen
from dxf2gcode.presentation.qt.qt_compat.QtWidgets import QMenu
from dxf2gcode.application.view_scene import hit_paths

def dash_segments(segments, unit, dotted=False):
    """Expand dashes for portable GL lines; preserve phase across short pieces."""
    result, phase = [], 0.
    on, period = (1., 3.) if dotted else (5., 8.)
    for start, end in segments:
        length, offset = dist(start, end), 0.
        if not length:
            continue
        while offset < length:
            remaining = ((on if phase < on else period)-phase)*unit
            stop = min(length, offset+max(remaining, unit*1e-6))
            if phase < on:
                for position in (offset, stop):
                    result.append(tuple(a+(b-a)*position/length for a, b in zip(start, end)))
            phase = (phase+(stop-offset)/unit) % period
            offset = stop
    return result



class ViewInteraction:
    def path_style(self, path, role):
        from dxf2gcode.presentation.qt.canvas2d import ShapeGUI
        selected = path.identity in self.selected
        if path.kind == 'operation':
            pen = self.panel.canvas_preview.path_pen(role, path.enabled,
                path.identity == self.panel.context, selected)
        elif path.kind == 'region':
            pen = QPen(ShapeGUI.PEN_BREAK)
            pen.setWidthF(2 if selected else .6)
        else:
            count, total = self.geometry_selection.get(path.identity, (0, 0))
            source = self.panel.binding.sources.get(path.identity)
            normal = {41: ShapeGUI.PEN_LEFT, 42: ShapeGUI.PEN_RIGHT}.get(
                source.cut_cor if source is not None else 40, ShapeGUI.PEN_NORMAL)
            selected_original = bool(count) or source is not None and source.isSelected()
            if source is not None and source.isDisabled():
                pen = QPen(ShapeGUI.PEN_SELECT_DISABLED if selected_original else ShapeGUI.PEN_NORMAL_DISABLED)
            else:
                pen = QPen(ShapeGUI.PEN_SELECT if selected_original else normal)
            if 0 < count < total:
                pen.setStyle(QtCore.Qt.PenStyle.DotLine)
        return pen


    def pick(self, point, control=False):
        hits = hit_paths(self.snapshot, (point.x(), point.y()), self.project,
                         self.spatial, show_disabled=self.show_disabled)
        if not hits:
            hits = hit_paths(self.snapshot, (point.x(), point.y()), self.project,
                             self.spatial, kinds=('geometry',))
        identity = hits[0] if len(hits) == 1 else None
        if len(hits) > 1:
            menu = QMenu(self)
            for hit in hits:
                path = next(p for p in self.snapshot.paths if p.identity == hit)
                action = menu.addAction(path.title)
                action.setData(hit)
            chosen = menu.exec(self.pick_widget.mapToGlobal(point))
            identity = chosen.data() if chosen else None
        if identity:
            path = next(p for p in self.snapshot.paths if p.identity == identity)
            if path.kind == 'region':
                self.panel.modifiers.select(identity)
            elif path.kind == 'geometry':
                source = self.panel.binding.sources[identity]
                for shape in self.panel.window.shapes:
                    selected = (not shape.isSelected() if shape is source and control
                                else shape is source or control and shape.isSelected())
                    self.panel.window.TreeHandler.setShapeSelected(shape, selected)
                self.panel.geometry_selected()
            else:
                self.panel.select_canvas_operation(identity, control)
        elif not hits and not control:
            self.panel.tree.setCurrentItem(None)
            self.panel.tree.clearSelection()
            self.panel.modifiers.clear_reference()
            self.panel.refresh_preview()
