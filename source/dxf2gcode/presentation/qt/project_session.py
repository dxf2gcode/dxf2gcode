"""Qt coordination around pure project persistence/model operations."""
import dxf2gcode.bootstrap.runtime_state as g
from dxf2gcode.domain.project.project import Project as ProjectModel
from dxf2gcode.adapters.project.legacy_d2g import decode_d2g
from dxf2gcode.presentation.qt.qt_compat import QtCore

class Project(ProjectModel):
    def __init__(self, parent):
        config = getattr(parent, 'config', None) or g.config
        tree = getattr(parent, 'TreeHandler', None)
        super().__init__(parent, config, decode=decode_d2g,
            translate=QtCore.QCoreApplication.translate,
            before_export=(lambda: tree.updateExportOrder(True)) if tree else None,
            before_load=(lambda: parent.connectToolbarToConfig(True))
                if hasattr(parent, 'connectToolbarToConfig') else None,
            load_drawing=(lambda: parent.load(False)) if hasattr(parent, 'load') else None,
            after_load=getattr(parent, 'plot', None),
            load_failed=getattr(parent, 'unsetCursor', None),
            before_reload=self._prepare_reload,
            rebuild=getattr(parent, 'makeShapes', None))

    def _prepare_reload(self):
        scene = getattr(self.parent, 'canvas_scene', None)
        if hasattr(scene, 'take_pending_error_messages'):
            scene.take_pending_error_messages()
        self.parent.setCursor(QtCore.Qt.CursorShape.WaitCursor)
        self.parent.canvas.resetAll()
        self.parent.app.processEvents()
