"""Construct application services from concrete runtime adapters."""

from dxf2gcode.adapters.project.legacy_repository import (
    LegacyProjectRepository)
from dxf2gcode.application.context import ApplicationContext


def create_application_context(config, logger, quiet=False):
    """Build the shared context used by GUI and command-line workflows."""
    return ApplicationContext(
        config=config,
        logger=logger,
        quiet=quiet,
        project_repository=LegacyProjectRepository(),
    )


def create_drawing_exporter(import_drawing, build_model, postprocessor, config,
                            optimizer_factory=None):
    from dxf2gcode.application.cli_export import ExportDrawing
    from dxf2gcode.adapters.toolpath.preparation import prepare_shape
    return ExportDrawing(import_drawing, build_model, postprocessor, config,
                         optimizer_factory, prepare_shape=prepare_shape)


def create_drawing_session(config, project_filename):
    from dxf2gcode.application.cli_export import DrawingSession
    from dxf2gcode.application.importing import ImportDrawing
    from dxf2gcode.adapters.dxf.reader import DxfReaderAdapter
    return DrawingSession(config, project_filename, ImportDrawing(DxfReaderAdapter(config)))


def create_project_exporter(project_repository, config, postprocessor,
                            optimizer_factory=None):
    from dxf2gcode.application.cli_export import ExportProject
    from dxf2gcode.application.importing import ImportDrawing
    from dxf2gcode.adapters.dxf.reader import DxfReaderAdapter
    from dxf2gcode.adapters.toolpath.preparation import prepare_shape
    from dxf2gcode.adapters.project.machining_d2g import decode_project
    return ExportProject(project_repository, config, postprocessor,
        optimizer_factory, import_drawing=ImportDrawing(DxfReaderAdapter(config)),
        prepare_shape=prepare_shape, decode_project=decode_project)
