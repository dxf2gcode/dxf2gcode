"""Profile macro expansion and declared return state; no G-code parsing."""

import re

from dxf2gcode.domain.geometry.point import Point


class ToolChangeError(ValueError):
    """Keep a translatable message separate from its runtime parameters."""

    def __init__(self, message, *parameters):
        self.message = message
        self.parameters = parameters
        super().__init__(message % parameters if parameters else message)


def setting(profile, name, default=None):
    section = getattr(profile, 'Tool_Change', None)
    if section is None:
        return default
    value = section[name]
    return default if value is None else value


def managed(profile):
    return setting(profile, 'return_state', 'legacy') == 'next_start_at_retract'


class ToolChangeMacro:
    """Expand the existing template against a known, absolute work position."""

    def __init__(self, dialect):
        self.dialect = dialect
        self.profile = dialect.vars

    def expand(self, context):
        dialect = self.dialect
        template = self.profile.Program['tool_change']
        if not template or not template.strip():
            raise ToolChangeError('Tool-change macro is empty; its return state cannot be established')
        work_offset = setting(self.profile, 'work_offset', '')
        if not re.fullmatch(r'G5[4-9](?:\.[123])?', work_offset) or (
                '.' in work_offset and not work_offset.startswith('G59.')):
            raise ToolChangeError('Tool-change work offset must be G54 through G59.3')
        end_mode = setting(self.profile, 'end_distance_mode', 'G90')
        if end_mode not in ('G90', 'G91'):
            raise ToolChangeError('Tool-change end distance mode must be G90 or G91')
        length_offset = self._length_offset(context.tool_number)
        values = {
            '%tool_nr': dialect.iprint(context.tool_number),
            '%speed': dialect.iprint(context.speed),
            '%next_start_x': dialect.fnprint(context.next_start[0]),
            '%next_start_y': dialect.fnprint(context.next_start[1]),
            '%retract_z': dialect.fnprint(context.retract_z),
            '%initial_retract_z': dialect.fnprint(context.initial_retract_z),
            '%units_code': 'G21' if context.metric else 'G20',
            '%distance_mode': 'G90' if dialect.abs_export else 'G91',
            '%work_offset': work_offset,
            '%nl': dialect.nlprint(),
        }
        if context.previous_tool_number is not None:
            values['%previous_tool_nr'] = dialect.iprint(context.previous_tool_number)
        if length_offset is not None:
            values['%length_offset_nr'] = dialect.iprint(length_offset)

        def profile_value(match):
            section, name = match.group(1), match.group(2)
            source = getattr(self.profile, section, None)
            try:
                value = source[name] if source is not None else None
            except KeyError:
                value = None
            if isinstance(value, bool):
                return '1' if value else '0'
            if isinstance(value, int):
                return dialect.iprint(value)
            if isinstance(value, float):
                return dialect.fnprint(value)
            if isinstance(value, str):
                return value
            raise ToolChangeError('Unavailable scalar profile parameter: %s.%s', section, name)

        # Expand existing named macros before validating contextual tokens.
        # Resolve recursively with a bound and detect cycles, never eval profile text.
        custom = self.profile.Custom_GCode
        names = sorted(list(custom), key=len, reverse=True)
        for _ in range(len(names) + 1):
            expanded = template
            for name in names:
                if name in expanded:
                    expanded = expanded.replace(name, custom[name]['gcode'])
            if expanded == template:
                break
            template = expanded
        if any(name in template for name in names):
            raise ToolChangeError('Cyclic custom macro in tool-change template')
        template = re.sub(r'\$\{post\.([A-Za-z_][\w]*)\.([A-Za-z_][\w]*)\}',
                          profile_value, template)
        if '${' in template:
            raise ToolChangeError('Unknown or nested profile parameter in tool-change macro')
        template = template.replace('%nl', dialect.nlprint())

        def replace(match):
            token = match.group()
            if token not in values:
                raise ToolChangeError('Unavailable tool-change parameter: %s', token)
            return values[token]

        output = re.sub(r'%[A-Za-z_][A-Za-z_0-9]*', replace, template)
        if not output.endswith('\n'):
            output += '\n'
        # The declaration promises this position with active length correction,
        # matching units, G40, and the configured work offset. It is not inferred.
        dialect.tool_nr = context.tool_number
        dialect.speed = context.speed
        dialect.Pe = dialect.Ps = dialect.lPe = Point(*context.next_start)
        dialect.ze = dialect.zs = dialect.lz = context.retract_z
        dialect._force_feed = True
        resume_mode = values['%distance_mode']
        if end_mode != resume_mode:
            output += ('\n' if not output.endswith('\n') else '') + resume_mode + '\n'
        return output

    def _length_offset(self, tool_number):
        mode = setting(self.profile, 'length_offset_mode', 'none')
        if mode == 'none':
            return None
        if mode == 'tool_number':
            return tool_number
        if mode != 'mapping':
            raise ToolChangeError('Unknown tool length offset mode: %s', mode)
        mapping = {}
        for entry in setting(self.profile, 'length_offset_mapping', '').split(','):
            pair = entry.strip().split(':')
            if len(pair) != 2 or not all(part.strip().isdigit() for part in pair):
                raise ToolChangeError('Tool length offset mapping must use tool:offset pairs')
            tool, offset = (int(part.strip()) for part in pair)
            if tool in mapping:
                raise ToolChangeError('Duplicate tool in length offset mapping: %s', tool)
            mapping[tool] = offset
        if tool_number not in mapping:
            raise ToolChangeError('No tool length offset mapping for tool %s', tool_number)
        return mapping[tool_number]
