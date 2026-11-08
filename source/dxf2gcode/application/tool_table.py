"""Compare saved project tools with the current table before any output."""

from dxf2gcode.domain.project.tool_settings import ToolSettings


def table_tool(config, number, units):
    profile = config.vars.Tool_Parameters[str(number)]
    if profile is None:
        return None
    tool = ToolSettings.from_profile(number, profile)
    metric = bool(getattr(config, 'tool_units_metric', config.metric))
    if metric != (units == 'mm'):
        tool = tool.scaled(25.4 if units == 'mm' else 1/25.4)
    return tool


def project_tool_errors(project, config, translate=lambda text: text):
    """Ignore unused/special steps; report full values without display rounding."""
    tr = translate
    labels = dict(tool_diameter=tr('Diameter'), speed=tr('Spindle speed'),
                  start_radius=tr('Start radius'), lead_radius=tr('Lead radius'),
                  lead_length=tr('Lead length'), overcut_length=tr('Overcut length'))
    used = {}
    for step in project.steps:
        if step.kind not in ('break', 'ignored') and any(e.enabled for e in step.entries):
            used.setdefault(step.tool_id, []).append(step.name)
    errors = []
    for identity, names in used.items():
        saved = project.tools[identity]
        current = table_tool(config, saved.tool_nr, project.units)
        if current == saved:
            continue
        lines = [tr('T{0} — steps: {1}').format(saved.tool_nr, ', '.join(names))]
        if current is None:
            lines.append(tr('Tool number is missing from the current tool table.'))
        else:
            lines.append(tr('Project tool differs from the current tool table.'))
        for key, label in labels.items():
            value = getattr(saved, key)
            unit = 'rpm' if key == 'speed' else project.units
            if current is None:
                lines.append(tr('{0}: project {1} {2}').format(label, value, unit))
            elif value != getattr(current, key):
                lines.append(tr('{0}: project {1}; table {2} {3}').format(
                    label, value, getattr(current, key), unit))
        lines.append(tr('Add or correct the tool in the tool table, or assign an existing table tool to the affected steps.'))
        errors.append('\n'.join(lines))
    if errors:
        errors.insert(0, tr('Export blocked: resolve the tool table conflicts first.'))
    return errors
