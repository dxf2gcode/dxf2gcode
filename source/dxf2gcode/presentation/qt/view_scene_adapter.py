"""Bridge the existing machining projection to a reusable renderer snapshot."""

from dxf2gcode.application.view_scene import ScenePath, ViewScene
from dxf2gcode.application.tab_regions import world_vertices
from dxf2gcode.application.toolpath.projections import plan_preview_segments
from dxf2gcode.adapters.toolpath.preview import preview_result
from dxf2gcode.adapters.toolpath.preparation import prepare_shape
from dxf2gcode.domain.project.machining_project import MachiningOperation
from dxf2gcode.presentation.qt.toolpath_labels import translate_diagnostic


def build_view_scene(panel, layers):
    binding = panel.binding
    if binding is None:
        return ViewScene()
    paths = []
    for identity, source in binding.sources.items():
        if source.parentLayer.isBreakLayer():
            continue
        segments = []
        z = source.axis3_start_mill_depth
        source.make_path(lambda caller, a, b: segments.append(
            ((a.x, a.y, z), (b.x, b.y, z), 'geometry')), lambda *args: None)
        paths.append(ScenePath(identity, identity, 'geometry', tuple(segments),
                               panel.tr('Contour {0}').format(source.nr)))
    views = {s.operation_id: s for layer in layers for s in layer.shapes
             if hasattr(s, 'operation_id') and hasattr(s, 'geos')}
    for step in binding.project.steps:
        if step.kind in ('break', 'ignore'):
            continue
        for entry in step.entries:
            if not isinstance(entry, MachiningOperation) or entry.id not in views:
                continue
            view = views[entry.id]
            if view.stmove is None:
                prepare_shape(view, build_preview=False)
            result = preview_result(view, panel.window.MyPostProcessor, layers)
            plan = result.plan if not result.has_errors else None
            segments = tuple((s.start, s.end, 'retract' if s.is_retract else s.role)
                             for s in plan_preview_segments(plan))
            source = binding.sources[entry.geometry_id]
            tool = binding.project.tools[step.tool_id]
            title = '%s · %s · T%d' % (step.name, panel.tr('Contour {0}').format(source.nr), tool.tool_nr)
            diagnostic = '; '.join(translate_diagnostic(d) for d in result.diagnostics)
            if not segments:
                p = source.get_start_end_points(True)
                anchor = (p.x, p.y, source.axis3_start_mill_depth)
                segments = ((anchor, anchor, 'diagnostic'),)
            paths.append(ScenePath(entry.id, entry.geometry_id, 'operation', segments,
                                   title, entry.enabled, plan, diagnostic))
    for identity, region in binding.project.regions.items():
        vertices = world_vertices(binding, region)
        z = region.height
        points = tuple((p[0], p[1], z) for p in vertices)
        segments = tuple((a, b, 'tab') for a, b in zip(points, points[1:]+points[:1]))
        paths.append(ScenePath(identity, region.geometry_id or '', 'region', segments,
                               panel.modifiers.label(region), region.enabled))
    return ViewScene(tuple(paths), binding.project.units)
