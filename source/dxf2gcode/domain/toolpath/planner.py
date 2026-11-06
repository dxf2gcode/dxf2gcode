"""Select pure planning strategies for explicit toolpath requests."""

from dxf2gcode.domain.toolpath.diagnostics import (
    START_ERROR, MODE_CONFLICT, POCKET_UNSUPPORTED, diagnostic)
from dxf2gcode.domain.project.machining import machining_conflict, pocket_supported
from dxf2gcode.domain.toolpath.movements import MovementPlan
from dxf2gcode.domain.toolpath.plan import ToolpathPlanningResult
from dxf2gcode.domain.toolpath.strategies.contour import ContourStrategy
from dxf2gcode.domain.toolpath.strategies.knife_passes import KnifePassStrategy
from dxf2gcode.domain.toolpath.strategies.simple_milling import SimpleMillingStrategy


class ToolpathPlanner:
    """Plan without Shapes, Qt, globals or a postprocessor instance.

    exit_geometry is an explicitly supplied geometry service. It reuses the
    established lead/overcut algorithms during their separate migration.
    """

    def __init__(self, exit_geometry=None):
        self._simple_milling = SimpleMillingStrategy()
        self._contour = ContourStrategy(exit_geometry)

    def plan(self, request):
        if request.literal is not None:
            output = MovementPlan(request)
            output.add("literal", request.literal)
            return ToolpathPlanningResult(output.finish())
        if machining_conflict(request.drill, request.pocket, request.compensation):
            return ToolpathPlanningResult(None, (diagnostic(
                request, "machining.conflict", MODE_CONFLICT, request.shape_number),))
        if request.pocket and not pocket_supported(
                request.settings.machine_type, request.settings.machine_compensation):
            return ToolpathPlanningResult(None, (diagnostic(
                request, "machining.pocket_unsupported", POCKET_UNSUPPORTED,
                request.shape_number),))
        if request.start_error:
            return ToolpathPlanningResult(None, (diagnostic(
                request, "lead.invalid_start", START_ERROR,
                request.shape_number, request.start_error),))
        if self._simple_milling.supports(request):
            return ToolpathPlanningResult(self._simple_milling.plan(request))
        if request.settings.machine_type == "drag_knife":
            try:
                return ToolpathPlanningResult(KnifePassStrategy().plan(request))
            except ValueError as error:
                return ToolpathPlanningResult(None, (diagnostic(
                    request, "knife.invalid", START_ERROR,
                    request.shape_number, error.args[0]),))
        return self._contour.plan(request)
