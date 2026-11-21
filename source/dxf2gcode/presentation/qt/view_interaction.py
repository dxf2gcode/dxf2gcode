"""Shared appearance and selection rules for experimental view adapters."""

from math import dist
from dxf2gcode.presentation.qt.qt_compat import QtCore
from dxf2gcode.presentation.qt.qt_compat.QtGui import QPen
from dxf2gcode.presentation.qt.qt_compat.QtWidgets import QMenu
from dxf2gcode.application.view_scene import hit_paths

def dash_segments(segments, unit, dotted=False, align_depth_passes=False):
    """Expand dashes for portable GL lines; preserve phase across short pieces."""
    result, phase = [], 0.
    patterns = {}
    on, period = (1., 3.) if dotted else (5., 8.)
    for start, end in segments:
        length, offset = dist(start, end), 0.
        if not length:
            continue
        pattern_phase = phase
        if align_depth_passes and start[2] == end[2]:
            a, b = (tuple(round(v, 12) for v in point[:2]) for point in (start, end))
            key = tuple(sorted((a, b)))
            first_start, pattern_phase = patterns.setdefault(key, (a, phase))
            if a != first_start:
                start, end = end, start
        while offset < length:
            remaining = ((on if pattern_phase < on else period)-pattern_phase)*unit
            stop = min(length, offset+max(remaining, unit*1e-6))
            if pattern_phase < on:
                for position in (offset, stop):
                    result.append(tuple(a+(b-a)*position/length for a, b in zip(start, end)))
            pattern_phase = (pattern_phase+(stop-offset)/unit) % period
            offset = stop
        phase = (phase+length/unit) % period if align_depth_passes else pattern_phase
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


    def path_hits(self, point, kinds=('operation', 'region')):
        return hit_paths(self.snapshot, (point.x(), point.y()), self.project,
                         self.spatial, show_disabled=self.show_disabled, kinds=kinds)

    def pick(self, point, control=False):
        hits = self.path_hits(point)
        if not hits:
            hits = self.path_hits(point, kinds=('geometry',))
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
            # Clear current item and selection as one logical action. Native
            # signals used to repaint twice before the explicit third refresh.
            blocked = self.panel.tree.blockSignals(True)
            try:
                self.panel.tree.setCurrentItem(None)
                self.panel.tree.clearSelection()
            finally:
                self.panel.tree.blockSignals(blocked)
            self.panel.selection_changed()
