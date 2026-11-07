"""Qt coordination around pure project persistence/model operations."""
import dxf2gcode.bootstrap.runtime_state as g
from dxf2gcode.domain.project.project import Project as ProjectModel
from dxf2gcode.adapters.project.legacy_d2g import decode_d2g
from dxf2gcode.adapters.project.machining_d2g import decode_project, encode_project
from dxf2gcode.domain.project.document import LegacyProjectDocument, MachiningProjectDocument
from dxf2gcode.domain.project.layercontent import Layers
from dxf2gcode.application.machining import MachiningDrawing
from copy import deepcopy
from dataclasses import replace
import os
from dxf2gcode.presentation.qt.qt_compat import QtCore

class Project(ProjectModel):
    def __init__(self, parent):
        config = getattr(parent, 'config', None) or g.config
        tree = getattr(parent, 'TreeHandler', None)
        self.machining_drawing = None
        self.loading_machining_project = None
        super().__init__(parent, config, decode=decode_project,
            translate=QtCore.QCoreApplication.translate,
            before_export=(lambda: tree.updateExportOrder(True)) if tree else None,
            before_load=(lambda: parent.connectToolbarToConfig(True))
                if hasattr(parent, 'connectToolbarToConfig') else None,
            load_drawing=(lambda: parent.load(False)) if hasattr(parent, 'load') else None,
            after_load=getattr(parent, 'plot', None),
            load_failed=getattr(parent, 'unsetCursor', None),
            before_reload=self._prepare_reload,
            rebuild=getattr(parent, 'makeShapes', None))

    def export_current(self):
        """Explicit migration/save boundary; legacy export remains for compatibility."""
        source = decode_d2g(self.export()).values
        if self.machining_drawing is None:
            self.machining_drawing = MachiningDrawing.capture(self.parent.layerContents, self.config)
        else:
            self.machining_drawing.synchronize_editor()
        project = self.machining_drawing.project
        source['machine_type'] = project.configuration['General']['machine_type']
        source['point_tol'] = project.configuration['Import_Parameters']['point_tolerance']
        source['fitting_tol'] = project.configuration['Import_Parameters']['fitting_tolerance']
        # The restoration snapshot must not reintroduce live profile defaults.
        source['drag_knife'] = dict(deepcopy(project.configuration['Drag_Knife_Options']),
            units=project.units,
            lead_defaults={key: project.configuration['Lead_In_Out'][key] for key in
                ('lead_in_mode', 'lead_out_mode', 'overcut_enabled')})
        source['split_lines'] = project.configuration['General']['split_line_segments']
        source['aut_cut_com'] = project.configuration['General']['automatic_cutter_compensation']
        self.parent.layerContents = Layers(self.parent.layerContents)
        self.machining_drawing.source_layers = self.parent.layerContents
        self.parent.layerContents.machining_binding = self.machining_drawing
        self.machining_drawing.bind_legacy_editor()
        return encode_project(source, project)

    def load(self, content, compleet=True):
        document = content if isinstance(content, LegacyProjectDocument) else decode_project(content)
        self.machining_drawing = None
        if not isinstance(document, MachiningProjectDocument):
            return super().load(document, compleet)
        project_filename = getattr(self, 'project_filename', None)
        if project_filename and not os.path.isabs(document.values['file']):
            document = replace(document, values=dict(document.values, file=os.path.abspath(
                os.path.join(os.path.dirname(project_filename), document.values['file']))))
        after_load = self.after_load
        self.after_load = lambda: None
        self.loading_machining_project = document.machining
        try:
            result = super().load(document, compleet)
            if self.load_drawing is not None and compleet and result is None:
                return result
            self.parent.layerContents = Layers(self.parent.layerContents)
            self.machining_drawing = MachiningDrawing(deepcopy(document.machining), self.parent.layerContents)
            self.parent.layerContents.machining_binding = self.machining_drawing
            self.machining_drawing.bind_legacy_editor()
        finally:
            self.after_load = after_load
            self.loading_machining_project = None
        after_load()
        return result

    def reload(self, compleet=True):
        if self.machining_drawing is None:
            return super().reload(compleet)
        if self.parent.filename:
            document = self.export_current()
            self.before_reload()
            if compleet:
                self.load(document, compleet=True)
            else:
                self.rebuild()
                self.load(document, compleet=False)

    def _prepare_reload(self):
        scene = getattr(self.parent, 'canvas_scene', None)
        if hasattr(scene, 'take_pending_error_messages'):
            scene.take_pending_error_messages()
        self.parent.setCursor(QtCore.Qt.CursorShape.WaitCursor)
        self.parent.canvas.resetAll()
        self.parent.app.processEvents()
