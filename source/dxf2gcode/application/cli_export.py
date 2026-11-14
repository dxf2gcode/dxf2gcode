"""Headless import, project-model construction and export workflow."""

import os

from dxf2gcode.domain.geometry.point import Point
from dxf2gcode.application.optimization.routes import OptimizeRoutes
from dxf2gcode.application.shapes import AutomaticCutterCompensation
from dxf2gcode.application.exporting import ExportToolpath
from dxf2gcode.application.drawings import BuildDrawingModel, DrawingModel
from dxf2gcode.domain.project.shape import Shape
from dxf2gcode.domain.project.project import Project
from dxf2gcode.domain.toolpath.customgcode import CustomGCode
from dxf2gcode.domain.project.document import MachiningProjectDocument
from dxf2gcode.application.machining import MachiningDrawing, ProjectConfiguration


class ExportDrawing:
    """Run the shared import, model-building, optimization and export services."""

    def __init__(self, import_drawing, build_model, postprocessor, config,
                 optimizer_factory=None, *, prepare_shape):
        self._prepare_shape = prepare_shape
        self._import_drawing = import_drawing
        self._build_model = build_model
        self._postprocessor = postprocessor
        self._config = config
        self._optimizer_factory = optimizer_factory

    def execute(self, filename, output_filename, optimize=False,
                postprocessor_index=0, import_filename=None):
        import_result = self._import_drawing.execute(import_filename or filename)
        model = self._build_model(import_result.drawing)
        self.export_model(model, filename, output_filename, optimize,
                          postprocessor_index)
        return model, import_result.diagnostics

    def export_model(self, model, filename, output_filename, optimize=False,
                     postprocessor_index=0):
        for layer in model.layers:
            enabled_shapes = [shape for shape in layer.shapes
                              if not shape.isDisabled()]
            layer.exp_order = [shape.nr for shape in enabled_shapes
                               if not isinstance(shape, CustomGCode)]
            layer.exp_order_complete = [
                index for index, shape in enumerate(layer.shapes)
                if not shape.isDisabled()]

        if not hasattr(model.layers, 'machining_config'):
            AutomaticCutterCompensation().execute(
                model.layers.non_break_layer_iter(),
                self._config.vars.General['automatic_cutter_compensation'],
                self._config.machine_type)
        if optimize and self._optimizer_factory is not None:
            coordinates = self._config.vars.Plane_Coordinates
            optimizer = OptimizeRoutes(
                optimizer_factory=self._optimizer_factory,
                max_iterations=self._config.vars.Route_Optimisation[
                    'max_iterations'],
                start_point=Point(coordinates['axis1_start_end'],
                                  coordinates['axis2_start_end']),
                route_settings=self._config.vars.Route_Optimisation)
            optimizer.execute(model.layers.non_break_layer_iter(),
                              model.shapes)

        for shape in model.shapes:
            if not isinstance(shape, CustomGCode):
                shape.stmove = self._prepare_shape(shape, config=self._config, build_preview=False)

        ExportToolpath(self._postprocessor).execute(
            filename, output_filename, model.layers, postprocessor_index)
        if getattr(self._postprocessor, 'export_failed', False):
            raise ValueError('; '.join(self._postprocessor.export_errors))


class DrawingSession:
    """Drawing state and loading operation shared with project restoration."""

    def __init__(self, config, project_filename, import_drawing):
        self.import_drawing = import_drawing
        self.config = config
        self.project_filename = project_filename
        self.filename = None
        self.cont_scale = 1.0
        self.cont_rotate = 0.0
        self.cont_dx = 0.0
        self.cont_dy = 0.0
        self.cont_mirrorx = False
        self.cont_mirrory = False
        self.layerContents = []
        self.shapes = []
        self.newNumber = 0
        self.drawing = None
        self.entityRoot = None
        self.loaded = False
        self.diagnostics = ()
        self.excluded_layers = ()

    def load(self):
        filename = self.filename
        if not filename:
            return False
        if not os.path.isabs(filename):
            filename = os.path.join(
                os.path.dirname(self.project_filename), filename)
        if not os.path.isfile(filename):
            return False
        self.filename = filename
        importer = self.import_drawing
        if hasattr(self, 'build_config'):
            importer = importer.with_configuration(self.build_config)
        result = importer.execute(filename)
        self.diagnostics = result.diagnostics
        self.drawing = result.drawing
        model = BuildDrawingModel(
            drawing=result.drawing,
            config=getattr(self, 'build_config', self.config),
            shape_factory=Shape,
            split_line_segments=self.config.vars.General[
                'split_line_segments'],
            transform={
                'x': self.cont_dx, 'y': self.cont_dy,
                'scale': self.cont_scale, 'rotation': self.cont_rotate,
                'mirrorx': self.cont_mirrorx,
                'mirrory': self.cont_mirrory,
            }).execute()
        self.layerContents = model.layers
        self.shapes = model.shapes
        self.entityRoot = model.entity_root
        self.excluded_layers = model.excluded_layers
        self.newNumber = len(self.shapes)
        self.loaded = True
        return True

class ExportProject:
    """Load a versioned .d2g model and export it without constructing Qt UI."""

    def __init__(self, project_repository, config, postprocessor,
                 optimizer_factory=None, *, import_drawing, prepare_shape, decode_project):
        self._import_drawing = import_drawing
        self._prepare_shape = prepare_shape
        self._decode_project = decode_project
        self._repository = project_repository
        self._config = config
        self._postprocessor = postprocessor
        self._optimizer_factory = optimizer_factory

    def execute(self, project_filename, output_filename, optimize=False,
                postprocessor_index=0):
        session = DrawingSession(self._config, project_filename, self._import_drawing)
        project = Project(session, self._config, decode=self._decode_project,
                          load_drawing=session.load)
        project_document = self._repository.load(project_filename)
        if isinstance(project_document, MachiningProjectDocument):
            session.build_config = ProjectConfiguration(project_document.machining)
        project.load(project_document)
        if not session.loaded:
            raise FileNotFoundError(
                "project source drawing could not be loaded: %s" %
                project_document.values.get('file'))

        source_filename = session.filename
        if not source_filename:
            source_filename = project_filename
        model = DrawingModel(session.entityRoot, session.layerContents,
                             session.shapes, session.excluded_layers)
        export_config = self._config
        if isinstance(project_document, MachiningProjectDocument):
            machining = MachiningDrawing(project_document.machining, session.layerContents)
            model.layers = machining.materialize()
            model.shapes = [shape for layer in model.layers for shape in layer.shapes]
            export_config = ProjectConfiguration(machining.project)
        else:
            # Legacy projects follow the same live-table policy as GUI migration.
            model.layers.machining_project = MachiningDrawing.capture(
                session.layerContents, self._config).project
        exporter = ExportDrawing(
            import_drawing=None, build_model=None,
            postprocessor=self._postprocessor, config=export_config,
            optimizer_factory=self._optimizer_factory, prepare_shape=self._prepare_shape)
        exporter.export_model(model, source_filename, output_filename,
                              optimize, postprocessor_index)
        return model, session.diagnostics
