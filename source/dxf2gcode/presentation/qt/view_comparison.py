"""Small view band and lazy optional viewport; the legacy canvas stays intact."""

import importlib.util
import logging
from time import perf_counter

from dxf2gcode.presentation.qt.qt_compat import QtCore, PYQT_VERSION
from dxf2gcode.presentation.qt.qt_compat.QtWidgets import QStackedWidget, QToolBar, QStyle
from dxf2gcode.presentation.qt.qt_compat.QtGui import QAction, QActionGroup, QIcon

logger = logging.getLogger(__name__)


class ViewComparison(QtCore.QObject):
    def __init__(self, window):
        super().__init__(window)
        self.window, self.panel = window, window.machining_panel
        self.renderer, self.snapshot, self.key = None, None, None
        self.renderers = {}
        self.active_kind = 'vispy'
        self.legacy_stale = False
        self.sizes = window.ui.splitter.sizes()
        self.stack = QStackedWidget()
        self.stack.setMinimumSize(window.canvas.minimumSize())
        window.ui.splitter.replaceWidget(1, self.stack)
        self.stack.addWidget(window.canvas)
        window.ui.splitter.setStretchFactor(1, 1)
        window.ui.splitter.setSizes(self.sizes)
        self.band = QToolBar(self.tr('View comparison'), window)
        self.band.setObjectName('viewComparisonBand')
        self.band.setMovable(False)
        window.addToolBar(self.band)
        self.group = QActionGroup(self)
        self.actions = {}
        for key, text in (('legacy', self.tr('2D canvas')),
                          ('plane', self.tr('VisPy: top view')),
                          ('spatial', self.tr('VisPy: spatial view')),
                          ('quickplane', self.tr('Qt Quick 3D: top view')),
                          ('quickspatial', self.tr('Qt Quick 3D: spatial view'))):
            action = QAction(text, self)
            action.setCheckable(True)
            self.group.addAction(action)
            self.band.addAction(action)
            action.triggered.connect(lambda checked=False, key=key: self.activate(key, animate=True))
            self.actions[key] = action
        self.actions['legacy'].setChecked(True)
        self.band.addSeparator()
        self.fit_action = self.band.addAction(self.tr('Fit all'))
        self.fit_action.triggered.connect(self.fit)
        self.band.addAction(window.ui.actionShowDisabledPaths)
        self.tools_action = self.band.addAction(self.tr('Transparent tools (test)'))
        self.tools_action.setCheckable(True)
        self.tools_action.setToolTip(self.tr('Selected operations: 25% opacity, actual diameter; test length = four diameters. No collision check.'))
        self.tools_action.toggled.connect(self.update_tools)
        reason = ''
        if PYQT_VERSION != 6:
            reason = self.tr('The prototype requires PyQt6.')
        elif not hasattr(window.canvas, 'mapToScene'):
            reason = self.tr('Start with the existing 2D canvas to use the comparison.')
        if reason:
            self.disable(reason)
            self.disable(reason, 'quick3d')
        else:
            if importlib.util.find_spec('vispy') is None:
                self.disable(self.tr('VisPy is not installed. The 2D canvas remains available.'))
            if any(importlib.util.find_spec('PyQt6.'+module) is None
                   for module in ('QtQuick3D', 'QtQuick', 'QtQml')):
                self.disable(self.tr('Qt Quick 3D is not installed. The 2D canvas remains available.'), 'quick3d')
        self.panel.preview_updated.connect(self.update_scene)

    def tr(self, text):
        return QtCore.QCoreApplication.translate('ViewComparison', text)

    def disable(self, reason, kind='vispy'):
        for key in (('plane', 'spatial') if kind == 'vispy' else ('quickplane', 'quickspatial')):
            self.actions[key].setEnabled(False)
            self.actions[key].setToolTip(reason)

    def failed(self, error, kind=None):
        kind = kind or self.active_kind
        refresh_legacy = self.active_kind == kind and self.legacy_stale
        logger.warning('%s: %s', self.tr('The 3D prototype is unavailable; using the 2D canvas.'), error)
        if self.active_kind == kind:
            self.stack.setCurrentWidget(self.window.canvas)
            self.actions['legacy'].setChecked(True)
            self.renderer = None
            self.legacy_stale = False
        self.disable(self.tr('The 3D prototype is unavailable; using the 2D canvas.')+'\n'+str(error), kind)
        renderer = self.renderers.pop(kind, None)
        if renderer is not None:
            if hasattr(renderer, 'dispose'):
                renderer.dispose()
            self.stack.removeWidget(renderer)
            renderer.deleteLater()
        if refresh_legacy:
            self.panel.refresh_preview()

    def activate(self, key, animate=False):
        vispy = self.renderers.get('vispy')
        if (animate and key == 'plane' and vispy is not None
                and self.stack.currentWidget() is vispy and vispy.animate_top()):
            return
        if vispy is not None:
            vispy.cancel_top_transition()
        if key in ('spatial', 'quickplane', 'quickspatial') and self.panel.modifiers.mode:
            self.panel.modifiers.set_mode(False)
        self.panel.modifiers.close_dimension_editor()
        if key == 'legacy':
            self.stack.setCurrentWidget(self.window.canvas)
            if self.legacy_stale:
                self.legacy_stale = False
                self.panel.refresh_preview()
            return
        kind = 'quick3d' if key.startswith('quick') else 'vispy'
        self.active_kind = kind
        try:
            created = kind not in self.renderers
            if created:
                if kind == 'vispy':
                    from dxf2gcode.presentation.qt.vispy_view import VispyView as Renderer
                else:
                    from dxf2gcode.presentation.qt.quick3d_view import Quick3DView as Renderer
                renderer = Renderer(self.panel, lambda error, kind=kind: self.failed(error, kind))
                self.renderers[kind] = renderer
                self.stack.addWidget(renderer)
            self.renderer = self.renderers[kind]
            self.stack.setCurrentWidget(self.renderer)
            self.renderer.set_tools_visible(self.tools_action.isChecked())
            self.renderer.set_spatial(key in ('spatial', 'quickspatial'))
            # Build once from the active projection batch; selection-only events
            # reuse the immutable snapshot instead of planning everything again.
            self.panel.refresh_preview()
            if self.renderer is not None and (created or not getattr(self.renderer, 'verified', True)):
                self.renderer.verify()
        except Exception as error:
            self.failed(error, kind)

    def scene_key(self):
        binding = self.panel.binding
        from dxf2gcode.application.tab_regions import to_world
        return (id(binding), repr(binding.project.to_dict()),
                repr(self.window.application_context.config.var_dict),
                repr(getattr(self.window.MyPostProcessor, 'vars', None)),
                to_world(binding, ((0, 0), (1, 0), (0, 1))))

    def refresh_cached_selection(self):
        """A hidden legacy canvas need not rematerialize an unchanged project."""
        if (self.active_kind != 'vispy' or self.renderer is None
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
        if self.renderer is not None and self.stack.currentWidget() is self.renderer:
            if self.active_kind == 'vispy':
                self.renderer.finish_top_transition()
            self.renderer.fit()
        elif getattr(self.window, 'canvas_scene', None) is not None:
            self.window.canvas.autoscale()

    def update_tools(self, visible):
        for renderer in self.renderers.values():
            renderer.set_tools_visible(visible)

    def shutdown(self):
        for renderer in self.renderers.values():
            renderer.dispose()
