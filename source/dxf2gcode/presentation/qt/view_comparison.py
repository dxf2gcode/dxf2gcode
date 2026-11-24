"""View band and startup selection for the VisPy and 2D views."""

import importlib.util
import logging
from time import perf_counter

from dxf2gcode.presentation.qt.qt_compat import QtCore, PYQT_VERSION
from dxf2gcode.presentation.qt.qt_compat.QtWidgets import (
    QFrame, QGridLayout, QLabel, QSizePolicy, QStackedWidget, QStyle, QToolBar, QToolButton, QToolTip, QVBoxLayout, QWidget)
from dxf2gcode.presentation.qt.qt_compat.QtGui import QAction, QActionGroup, QIcon, QPainter, QPainterPath, QPalette, QPen, QPixmap
from dxf2gcode.presentation.qt.scalebar import scale_bar_enabled

logger = logging.getLogger(__name__)

VIEW_ICON_LINES = {
    'options': (((10, 2), (14, 2), (15, 5), (17, 6), (20, 5), (22, 9), (20, 11),
                 (20, 13), (22, 15), (20, 19), (17, 18), (15, 19), (14, 22), (10, 22),
                 (9, 19), (7, 18), (4, 19), (2, 15), (4, 13), (4, 11), (2, 9), (4, 5),
                 (7, 6), (9, 5), (10, 2)),
                ((12, 8), (15, 10), (15, 14), (12, 16), (9, 14), (9, 10), (12, 8))),
    'info': (((12, 2), (17, 3), (21, 7), (22, 12), (21, 17), (17, 21), (12, 22),
              (7, 21), (3, 17), (2, 12), (3, 7), (7, 3), (12, 2)),
             ((12, 7), (12, 8)), ((10, 11), (12, 11), (12, 17)), ((10, 17), (14, 17))),
    'open': (((3, 19), (3, 5), (9, 5), (11, 8), (21, 8), (21, 11)),
             ((3, 19), (7, 11), (22, 11), (18, 19), (3, 19))),
    'reload': (((20, 10), (18, 6), (14, 4), (9, 4), (5, 7), (4, 12),
                (5, 17), (9, 20), (14, 20), (18, 18)),
               ((15, 10), (20, 10), (20, 5))),
    'save_project': (((4, 3), (17, 3), (21, 7), (21, 21), (3, 21), (3, 3), (4, 3)),
                     ((8, 3), (8, 9), (16, 9), (16, 3)),
                     ((7, 21), (7, 14), (17, 14), (17, 21))),
    'exit': (((12, 3), (4, 3), (4, 21), (12, 21)),
             ((9, 12), (21, 12)), ((17, 8), (21, 12), (17, 16))),
    'new': (((18, 8), (13, 3), (4, 3), (4, 21), (10, 21)),
            ((13, 3), (13, 8), (18, 8)), ((12, 16), (22, 16)), ((17, 11), (17, 21))),
    'optimize': (((3, 18), (9, 7), (14, 15), (21, 5)), ((16, 5), (21, 5), (21, 10))),
    'export': (((4, 3), (12, 3), (16, 7), (16, 9)),
               ((4, 3), (4, 21), (16, 21), (16, 17)),
               ((9, 13), (22, 13)), ((18, 9), (22, 13), (18, 17))),
    'optimize_export': (((12, 2), (6, 11), (11, 11), (8, 20), (17, 9), (12, 9), (12, 2)),
                        ((15, 18), (22, 18)), ((19, 15), (22, 18), (19, 21))),
    'workpiece_zero': (((3, 21), (3, 3), (21, 3)), ((3, 13), (21, 13)),
                       ((12, 4), (12, 21)), ((9, 10), (15, 10), (15, 16), (9, 16), (9, 10))),
    'scale': (((3, 21), (3, 12), (12, 12), (12, 21), (3, 21)),
              ((13, 11), (21, 3)), ((15, 3), (21, 3), (21, 9))),
    'rotate': (((8, 9), (16, 9), (16, 17), (8, 17), (8, 9)),
               ((4, 10), (5, 6), (9, 3), (15, 3), (20, 7)), ((16, 7), (20, 7), (20, 3))),
    'mirror': (((12, 3), (12, 21)), ((3, 18), (8, 7), (8, 18), (3, 18)),
               ((21, 18), (16, 7), (16, 18), (21, 18))),
    'plane': (((4, 4), (20, 4), (20, 20), (4, 20), (4, 4)),),
    'spatial': (((12, 2), (21, 7), (21, 17), (12, 22), (3, 17), (3, 7), (12, 2)),
                ((3, 7), (12, 12), (21, 7)), ((12, 12), (12, 22))),
    'fit': (((3, 9), (3, 3), (9, 3)), ((15, 3), (21, 3), (21, 9)),
            ((21, 15), (21, 21), (15, 21)), ((9, 21), (3, 21), (3, 15))),
    'disabled_paths': (((2, 12), (6, 8), (9, 6), (15, 6), (18, 8), (22, 12),
                        (18, 16), (15, 18), (9, 18), (6, 16), (2, 12)),
                       ((12, 9), (15, 12), (12, 15), (9, 12), (12, 9))),
    'directions': (((3, 18), (8, 18), (8, 6), (21, 6)), ((16, 2), (21, 6), (16, 10))),
    'selected_paths': (((3, 9), (3, 3), (9, 3)), ((15, 3), (21, 3), (21, 9)),
                       ((21, 15), (21, 21), (15, 21)), ((9, 21), (3, 21), (3, 15)),
                       ((7, 16), (11, 8), (17, 16))),
    'retracts': (((12, 3), (12, 19)), ((7, 8), (12, 3), (17, 8)), ((4, 21), (20, 21))),
    'scale_bar': (((3, 8), (21, 8), (21, 17), (3, 17), (3, 8)),
                  ((7, 8), (7, 12)), ((12, 8), (12, 14)), ((17, 8), (17, 12))),
    'origin_axes': (((9, 15), (9, 3)), ((6, 6), (9, 3), (12, 6)),
                    ((9, 15), (21, 19)), ((17, 15), (21, 19), (16, 21)),
                    ((9, 15), (3, 21)), ((3, 17), (3, 21), (7, 21))),
    'snap_tab': (((3, 17), (21, 7)), ((7, 7), (17, 7), (17, 17), (7, 17), (7, 7))),
    'manual_tab': (((3, 4), (16, 4), (16, 18), (3, 18), (3, 4)),
                   ((13, 13), (22, 22)), ((18, 22), (22, 22), (22, 18))),
    'tools': (((6, 5), (8, 3), (16, 3), (18, 5), (18, 17), (12, 22),
               (6, 17), (6, 5), (8, 7), (16, 7), (18, 5)),
              ((12, 9), (12, 11)), ((12, 14), (12, 16))),
    'route_live': (((3, 18), (8, 7), (15, 15), (21, 5)),
                   ((16, 6), (21, 5), (22, 10)), ((3, 17), (3, 19))),
}


def view_icon(palette, name):
    path = QPainterPath()
    for first, *rest in VIEW_ICON_LINES[name]:
        path.moveTo(*first)
        for point in rest:
            path.lineTo(*point)
    icon = QIcon()
    for mode, group in ((QIcon.Mode.Normal, QPalette.ColorGroup.Active),
                        (QIcon.Mode.Disabled, QPalette.ColorGroup.Disabled)):
        for size in (18, 24, 36, 48):
            pixmap = QPixmap(size, size)
            pixmap.fill(QtCore.Qt.GlobalColor.transparent)
            with QPainter(pixmap) as painter:
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                painter.scale(size/24, size/24)
                painter.setPen(QPen(palette.color(group, QPalette.ColorRole.ButtonText), 1.6,
                                    QtCore.Qt.PenStyle.SolidLine, QtCore.Qt.PenCapStyle.RoundCap,
                                    QtCore.Qt.PenJoinStyle.RoundJoin))
                painter.drawPath(path)
            icon.addPixmap(pixmap, mode)
    return icon


class ViewButton(QToolButton):
    def focusInEvent(self, event):
        super().focusInEvent(event)
        if event.reason() in (QtCore.Qt.FocusReason.TabFocusReason, QtCore.Qt.FocusReason.BacktabFocusReason):
            QToolTip.showText(self.mapToGlobal(self.rect().bottomLeft()), self.toolTip(), self)

    def focusOutEvent(self, event):
        QToolTip.hideText()
        super().focusOutEvent(event)


class ViewComparison(QtCore.QObject):
    def __init__(self, window):
        super().__init__(window)
        self.window, self.panel = window, window.machining_panel
        self.renderer, self.snapshot, self.key = None, None, None
        self.legacy_stale = False
        self.sizes = window.ui.splitter.sizes()
        self.stack = QStackedWidget()
        self.stack.setMinimumSize(window.canvas.minimumSize())
        window.ui.splitter.replaceWidget(1, self.stack)
        self.stack.addWidget(window.canvas)
        self.stack.show()
        window.ui.splitter.setStretchFactor(1, 1)
        window.ui.splitter.setSizes(self.sizes)
        self.band = QToolBar(self.tr('View'), window)
        self.band.setObjectName('viewBand')
        self.band.setMovable(False)
        window.addToolBar(self.band)
        # Override a hidden toolbar restored from an older window state.
        self.band.show()
        self.group = QActionGroup(self)
        self.actions = {}
        self.buttons = {}
        options = window.ui.menuOptions
        options_button_action = QAction(window.tr('Options'), self)
        window.ui.actionOpen.setText(self.tr('Open'))
        window.ui.actionOpen.setToolTip(self.tr('Open DXF or project...'))
        self.add_group(self.tr('Program'), (
            ('open', window.ui.actionOpen), ('reload', window.ui.actionReload),
            ('save_project', window.ui.actionSaveProjectAs), ('options', options_button_action),
            ('exit', window.ui.actionClose)), primary=True, separator_before='options')
        self.buttons['options'].setMenu(options)
        self.buttons['options'].setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        for action in options.actions():
            if not action.shortcut().isEmpty():
                window.addAction(action)
        self.band.addSeparator()
        window.ui.actionMoveWorkpieceZero.setToolTip(self.tr('Set workpiece zero...'))
        self.add_group(self.tr('Drawing'), (
            ('workpiece_zero', window.ui.actionMoveWorkpieceZero), ('scale', window.ui.actionScaleAll),
            ('rotate', window.ui.actionRotateAll), ('mirror', window.ui.actionMirrorAll)))

        self.band.addSeparator()
        self.add_group(self.tr('Machining'), (
            ('new', self.panel.buttons['new']), ('tabs', self.panel.buttons['tabs'])),
            primary=True, below_last=self.panel.tab_placement)
        for index in range(self.panel.tab_placement.count()):
            name = self.panel.tab_placement.itemData(index)
            self.panel.tab_placement.setItemIcon(index, view_icon(self.band.palette(), name + '_tab'))
        history = (('undo', self.panel.buttons['undo']), ('redo', self.panel.buttons['redo']))
        if window.title_bar is None:
            self.band.addSeparator()
            self.add_group(self.tr('History'), history)
        else:
            window.title_bar.add_history_buttons(*(self.add_button(name, action, window.title_bar)
                                                   for name, action in history))

        self.band.addSeparator()
        window.ui.actionExportShapes.setText(self.tr('Export G-code'))
        window.ui.actionExportShapes.setToolTip(self.tr('Export G-code...'))
        window.ui.actionOptimizeAndExportShapes.setToolTip(self.tr('Optimize and export G-code...'))
        self.add_group(self.tr('Output'), (
            ('export', window.ui.actionExportShapes), ('optimize', window.ui.actionOptimizePaths),
            ('optimize_export', window.ui.actionOptimizeAndExportShapes),
            ('route_live', window.ui.actionLiveUpdateExportRoute)), primary=True, separator_before='route_live')

        self.band.addSeparator()
        for key, action in (('plane', window.ui.actionTopView),
                            ('spatial', window.ui.actionIsometricView)):
            action.setText(self.tr('Top view') if key == 'plane' else self.tr('Spatial view'))
            action.setToolTip(action.text())
            action.setEnabled(True)
            action.setCheckable(True)
            self.group.addAction(action)
            action.triggered.connect(lambda checked=False, key=key: self.activate(key, animate=True))
            self.actions[key] = action
        fit = window.ui.actionAutoscale
        fit.setToolTip(self.tr('Fit all'))
        self.tools_action = QAction(self.tr('Transparent tools'), self)
        self.tools_action.setCheckable(True)
        self.tools_action.setToolTip(self.tools_action.text() + '\n' +
                                     self.tr('Show selected tools at their diameter with a schematic length.'))
        self.tools_action.toggled.connect(self.update_tools)
        self.selected_paths_action = QAction(self.tr('Toolpaths for selected contours only'), self)
        self.retracts_action = QAction(self.tr('Show Z retracts'), self)
        self.origin_axes_action = QAction(self.tr('Show XYZ axes at workpiece zero'), self)
        self.origin_axes_action.setCheckable(True)
        self.origin_axes_action.setChecked(True)
        self.origin_axes_action.toggled.connect(self.update_origin_axes)
        label = QtCore.QCoreApplication.translate('MyConfig', 'Show a scale bar in the canvas')
        self.scale_bar_action = QAction(label, self)
        self.scale_bar_action.setCheckable(True)
        self.scale_bar_action.setChecked(scale_bar_enabled(window.application_context.config))
        self.scale_bar_action.triggered.connect(self.set_scale_bar)
        for action in (self.selected_paths_action, self.retracts_action):
            action.setCheckable(True)
        self.retracts_action.setChecked(True)
        for action in (self.selected_paths_action, self.retracts_action):
            action.toggled.connect(self.update_display_filters)
        self.display_actions = {
            'selectedPathsOnly': self.selected_paths_action,
            'showRetracts': self.retracts_action,
            'showDisabledPaths': window.ui.actionShowDisabledPaths,
            'showPathDirections': window.ui.actionShowPathDirections,
            'transparentTools': self.tools_action,
            'showOriginAxes': self.origin_axes_action,
        }
        for name, action in self.display_actions.items():
            blocked = action.blockSignals(True)
            try:
                action.setChecked(window.settings.value('MainWindow/view/' + name, action.isChecked(), type=bool))
            finally:
                action.blockSignals(blocked)
        self.add_group(self.tr('View'), (
            ('plane', self.actions['plane']), ('spatial', self.actions['spatial']), ('fit', fit),
            ('disabled_paths', window.ui.actionShowDisabledPaths),
            ('directions', window.ui.actionShowPathDirections), ('selected_paths', self.selected_paths_action),
            ('retracts', self.retracts_action), ('scale_bar', self.scale_bar_action),
            ('origin_axes', self.origin_axes_action), ('tools', self.tools_action)),
            separator_before='disabled_paths')

        spacer = QWidget(self.band)
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.band.addWidget(spacer)
        window.ui.actionAbout.setToolTip(window.tr('About DXF2GCODE'))
        self.add_group(self.tr('Info'), (('info', window.ui.actionAbout),))
        self.panel.preview_updated.connect(self.update_scene)
        self.set_vispy_actions(False)

    def tr(self, text):
        return QtCore.QCoreApplication.translate('ViewComparison', text)

    def add_group(self, title, actions, *, primary=False, separator_before=None, below_last=None):
        group = QWidget(self.band)
        group.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        layout = QVBoxLayout(group)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(1)
        buttons = QGridLayout()
        buttons.setSpacing(2)
        buttons.setRowStretch(0, 1)
        buttons.setRowStretch(1, 1)
        layout.addLayout(buttons, 1)
        layout.addWidget(QLabel(title, group), alignment=QtCore.Qt.AlignmentFlag.AlignHCenter)
        column = 0
        for index, (name, action) in enumerate(actions):
            if name == separator_before:
                separator = QFrame(group)
                separator.setFrameShape(QFrame.Shape.VLine)
                separator.setFrameShadow(QFrame.Shadow.Sunken)
                buttons.addWidget(separator, 0, column, 2, 1)
                column += 1
            large = primary and index == 0
            button = self.add_button(name, action, group, large)
            stacked = primary and not large
            grid_row = (index - 1) % 2 if stacked else 0
            row_span = 1 if stacked else 2
            buttons.addWidget(button, grid_row, column, row_span, 1, QtCore.Qt.AlignmentFlag.AlignCenter)
            if not stacked or grid_row == 1:
                column += 1
        if below_last is not None:
            buttons.addWidget(below_last, 1, column)
        self.band.addWidget(group)

    def add_button(self, name, action, parent, large=False):
        if name in VIEW_ICON_LINES:
            action.setIcon(view_icon(self.band.palette(), name))
        if not action.shortcut().isEmpty():
            self.window.addAction(action)
        button = ViewButton(parent)
        button.setDefaultAction(action)
        button.setAutoRaise(True)
        button.setIconSize(QtCore.QSize(28, 28) if large else QtCore.QSize(18, 18))
        button.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon
                                  if large else QtCore.Qt.ToolButtonStyle.ToolButtonIconOnly)
        button.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        button.setAccessibleName(action.text().replace('&', ''))
        self.buttons[name] = button
        return button

    def set_vispy_actions(self, visible):
        for action in (*self.actions.values(), self.tools_action, self.origin_axes_action):
            action.setVisible(visible)
        for name in ('plane', 'spatial', 'origin_axes', 'tools'):
            self.buttons[name].setVisible(visible)

    def start(self, use_vispy):
        if not use_vispy:
            return
        if PYQT_VERSION != 6:
            self.failed(self.tr('PyQt6 is required.'))
            return
        if importlib.util.find_spec('vispy') is None:
            self.failed(self.tr('VisPy is not installed.'))
            return
        try:
            from dxf2gcode.presentation.qt.vispy_view import VispyView
            renderer = VispyView(self.panel, self.failed)
            self.renderer = renderer
            renderer.set_tools_visible(self.tools_action.isChecked())
            renderer.show_origin_axes = self.origin_axes_action.isChecked()
            renderer.set_display_filters(self.selected_paths_action.isChecked(), self.retracts_action.isChecked())
            # The first QOpenGLWidget changes how Qt composites the top-level
            # window. Attach it before showing that window at startup.
            self.stack.addWidget(renderer)
            self.stack.setCurrentWidget(renderer)
            renderer.ensurePolished()
            self.set_vispy_actions(True)
            self.actions['spatial'].setChecked(True)
        except Exception as error:
            self.failed(error)
            return
        if self.window.isVisible():
            self.finish_renderer_startup()

    def finish_renderer_startup(self):
        if self.renderer is None:
            return
        try:
            self.renderer.verify()
            self.activate('spatial')
            if self.panel.binding is not None:
                self.panel.refresh_preview()
        except Exception as error:
            self.failed(error)

    def failed(self, error):
        logger.warning('%s %s', self.tr('VisPy is unavailable. Using the 2D canvas.'), error)
        self.stack.setCurrentWidget(self.window.canvas)
        self.set_vispy_actions(False)
        self.shutdown()
        self.panel.modifiers.cancel()
        if self.legacy_stale:
            self.legacy_stale = False
            self.panel.refresh_preview()

    def activate(self, key, animate=False):
        renderer = self.renderer
        if renderer is None:
            return
        self.actions[key].setChecked(True)
        self.panel.modifiers.close_dimension_editor()
        if animate and key == 'plane' and renderer.animate_top():
            return
        renderer.cancel_top_transition()
        if key == 'spatial' and self.panel.modifiers.mode:
            self.panel.modifiers.set_mode(False)
        renderer.set_spatial(key == 'spatial')
        renderer.pick_widget.setFocus()

    def scene_key(self):
        binding = self.panel.binding
        from dxf2gcode.application.tab_regions import to_world
        return (id(binding), repr(binding.project.to_dict()),
                repr(self.window.application_context.config.var_dict),
                repr(getattr(self.window.MyPostProcessor, 'vars', None)),
                to_world(binding, ((0, 0), (1, 0), (0, 1))))

    def refresh_cached_selection(self):
        """A hidden legacy canvas need not rematerialize an unchanged project."""
        if (self.renderer is None
                or self.stack.currentWidget() is not self.renderer or self.snapshot is None
                or self.window.TreeHandler.auto_update_export_order):
            return False
        self.panel.binding.synchronize_editor()
        if self.scene_key() != self.key:
            return False
        self.legacy_stale = True
        self.update_scene(())
        self.panel.modifiers.repaint()
        return True

    def update_scene(self, layers):
        if self.renderer is None or self.stack.currentWidget() is not self.renderer:
            return
        try:
            binding = self.panel.binding
            key = self.scene_key()
            if key != self.key:
                from dxf2gcode.presentation.qt.view_scene_adapter import build_view_scene
                started = perf_counter()
                self.snapshot = build_view_scene(self.panel, layers)
                self.key = key
                # Keep every operation's diagnostic available even when pure
                # selection no longer repaints the hidden active-operation view.
                from dxf2gcode.presentation.qt.machining_panel import SOURCE_ROLE
                for path in self.snapshot.paths:
                    item = self.panel.entry_items.get(path.identity)
                    if path.kind == 'operation' and item is not None:
                        item.setToolTip(0, item.data(0, SOURCE_ROLE) + (' · ' + path.diagnostic if path.diagnostic else ''))
                        item.setIcon(0, self.panel.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxWarning)
                                     if path.diagnostic else QIcon())
                logger.debug('View snapshot: %d paths, %.3f s',
                             len(self.snapshot.paths), perf_counter()-started)
            selected = set(self.panel.selected_entries()) | self.panel.modifiers.selected_regions
            selected.update(self.panel.modifiers.related_operations)
            if getattr(self.renderer, 'view_binding', None) != id(binding):
                self.renderer.fitted.clear()
                self.renderer.view_binding = id(binding)
            self.renderer.set_scene(self.snapshot, selected)
        except Exception as error:
            self.failed(error)

    def fit(self):
        if self.renderer is not None:
            self.renderer.finish_top_transition()
            self.renderer.fit()
        elif getattr(self.window, 'canvas_scene', None) is not None:
            self.window.canvas.autoscale()

    def update_tools(self, visible):
        if self.renderer is not None:
            self.renderer.set_tools_visible(visible)

    def repaint_overlay(self):
        self.scale_bar_action.setChecked(scale_bar_enabled(self.window.application_context.config))
        if self.renderer is not None:
            self.renderer.labels.update()

    def update_origin_axes(self, visible):
        if self.renderer is not None:
            self.renderer.show_origin_axes = visible
            self.renderer.labels.update()

    def set_scale_bar(self, visible):
        config = self.window.application_context.config
        config.var_dict['General']['show_scale_bar'] = visible
        config.save_varspace()
        self.window.config_window.cfg_window_def['General']['show_scale_bar'].setValue(visible)
        self.window.updateCanvasOverlay()

    def update_display_filters(self):
        if self.renderer is not None:
            self.renderer.set_display_filters(self.selected_paths_action.isChecked(), self.retracts_action.isChecked())
        self.panel.canvas_preview.update_visibility()

    def save_display_settings(self):
        for name, action in self.display_actions.items():
            self.window.settings.setValue('MainWindow/view/' + name, action.isChecked())

    def refresh_path_directions(self):
        if self.renderer is None:
            return False
        # The toggle changes markers only. Refresh the hidden 2D preview on fallback.
        self.legacy_stale = True
        self.repaint_overlay()
        return True

    def shutdown(self):
        renderer, self.renderer = self.renderer, None
        if renderer is not None:
            renderer.dispose()
            self.stack.removeWidget(renderer)
            renderer.deleteLater()
