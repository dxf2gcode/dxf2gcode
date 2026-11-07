"""Validated JSON .d2g 2.0 codec and dispatch to legacy 1.1--1.5 readers."""

import json
from math import isfinite

from dxf2gcode.adapters.project.legacy_d2g import decode_d2g, validate_knife_settings
from dxf2gcode.application.exceptions import VersionMismatchError
from dxf2gcode.domain.project.document import MachiningProjectDocument
from dxf2gcode.domain.project.machining_project import MachiningProject

FORMAT = 'DXF2GCODE'
VERSION = 2.0
SOURCE_FIELDS = frozenset((
    'file', 'point_tol', 'fitting_tol', 'scale', 'rot', 'wpzero_x', 'wpzero_y',
    'mirrorx', 'mirrory', 'split_lines', 'aut_cut_com', 'machine_type', 'layers', 'drag_knife'))


def _number(value):
    return type(value) in (int, float) and isfinite(value)


def _unique_object(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError('Duplicate project field: ' + key)
        result[key] = value
    return result


def _invalid_number(value):
    raise ValueError('Non-finite project number: ' + value)


def validate_source(values):
    if not isinstance(values, dict) or not set(values) <= SOURCE_FIELDS:
        raise ValueError('Invalid source project fields')
    if not (SOURCE_FIELDS - {'drag_knife'}) <= set(values):
        raise ValueError('Missing source project fields')
    if not isinstance(values['file'], str) or not isinstance(values['layers'], list):
        raise ValueError('Invalid project drawing source')
    for key in ('point_tol', 'fitting_tol', 'scale', 'rot', 'wpzero_x', 'wpzero_y'):
        if type(values[key]) not in (int, float) or not isfinite(values[key]):
            raise ValueError('Invalid source transform')
    if values['scale'] == 0 or min(values['point_tol'], values['fitting_tol']) <= 0:
        raise ValueError('Invalid source tolerance or scale')
    for key in ('mirrorx', 'mirrory', 'split_lines', 'aut_cut_com'):
        if type(values[key]) is not bool:
            raise ValueError('Invalid source switch')
    if values['machine_type'] not in ('milling', 'lathe', 'drag_knife'):
        raise ValueError('Invalid machine type')
    if 'drag_knife' in values:
        validate_knife_settings(values['drag_knife'])
    layer_required = {'name', 'tool_nr', 'diameter', 'speed', 'retract', 'safe_margin', 'shapes'}
    shape_required = {'hash_', 'cut_cor', 'Pocket_Mill', 'Drill', 'cw', 'send_to_TSP',
                      'disabled', 'start_mill_depth', 'slice_depth', 'mill_depth',
                      'f_g1_plane', 'f_g1_depth', 'start_x', 'start_y'}
    for layer in values['layers']:
        if not isinstance(layer, dict) or not layer_required <= set(layer):
            raise ValueError('Invalid source layer')
        if (not isinstance(layer['name'], str) or type(layer['tool_nr']) is not int
                or layer['tool_nr'] < 1 or not isinstance(layer['shapes'], list)):
            raise ValueError('Invalid source layer values')
        if any(not _number(layer[key]) for key in ('diameter', 'speed', 'retract', 'safe_margin')):
            raise ValueError('Invalid source layer number')
        for shape in layer['shapes']:
            required = {'gcode', 'name', 'disabled'} if isinstance(shape, dict) and 'gcode' in shape else shape_required
            if not isinstance(shape, dict) or not required <= set(shape):
                raise ValueError('Invalid source contour')
            if type(shape['disabled']) is not bool:
                raise ValueError('Invalid source contour activation')
            if 'gcode' in shape:
                if not isinstance(shape['gcode'], str) or not isinstance(shape['name'], str):
                    raise ValueError('Invalid source literal action')
            elif (any(type(shape[key]) is not bool for key in ('Pocket_Mill', 'Drill', 'cw', 'send_to_TSP'))
                  or any(not _number(shape[key]) for key in ('cut_cor', 'start_mill_depth',
                      'slice_depth', 'mill_depth', 'f_g1_plane', 'f_g1_depth', 'start_x', 'start_y'))
                  or not isinstance(shape['hash_'], str)):
                raise ValueError('Invalid source contour values')


def validate_configuration(project):
    # A saved snapshot must be usable without filling missing fields from a
    # live profile. Keep the 2.0 contract independent of runtime/Qt config I/O.
    required = {
        'General': 'machine_type split_line_segments automatic_cutter_compensation',
        'Cutter_Compensation': 'done_by_machine',
        'Pocketing': 'pocket_edge_clearance',
        'Drag_Knife_Options': 'drag_angle drag_start_angle ramp_in_length swivel_depth extra_pass alternate lead_out_length entry_mode alignment_length return_to_start',
        'Lead_In_Out': 'lead_in_mode lead_out_mode overcut_enabled',
        'Depth_Coordinates': 'axis3_retract axis3_safe_margin axis3_start_mill_depth axis3_slice_depth axis3_mill_depth',
        'Feed_Rates': 'f_g1_plane f_g1_depth',
        'Plane_Coordinates': 'axis1_start_end axis2_start_end std_scale',
        'Route_Optimisation': 'default_TSP TSP_shape_order mutation_rate max_population max_iterations begin_art',
        'Import_Parameters': 'point_tolerance fitting_tolerance spline_check insert_at_block_layer exclude_ignore_layers exclude_layer_zero',
        'Layer_Options': 'id_float_separator',
        'Tool_Parameters': '1'}
    config = project.configuration
    if not isinstance(config, dict) or set(config) != set(required):
        raise ValueError('Invalid saved machining configuration')
    for section, keys in required.items():
        if not isinstance(config[section], dict) or not set(keys.split()) <= set(config[section]):
            raise ValueError('Missing saved configuration fields: ' + section)
    boolean = {'split_line_segments', 'automatic_cutter_compensation', 'done_by_machine',
               'extra_pass', 'alternate', 'return_to_start', 'overcut_enabled', 'default_TSP',
               'insert_at_block_layer', 'exclude_ignore_layers', 'exclude_layer_zero'}
    text = {'machine_type', 'entry_mode', 'lead_in_mode', 'lead_out_mode', 'TSP_shape_order', 'begin_art'}
    for section, keys in required.items():
        if section in ('Layer_Options', 'Tool_Parameters'):
            continue
        for key in keys.split():
            value = config[section][key]
            if ((key in boolean and type(value) is not bool)
                    or (key in text and not isinstance(value, str))
                    or (key not in boolean | text and not _number(value))):
                raise ValueError('Invalid saved configuration value: ' + key)
    if config['General']['machine_type'] not in ('milling', 'lathe', 'drag_knife'):
        raise ValueError('Invalid saved machine type')
    for key, value in config['Layer_Options'].items():
        if key == 'id_float_separator':
            if not isinstance(value, str) or not value:
                raise ValueError('Invalid layer separator')
        elif not isinstance(value, list) or any(not isinstance(v, str) for v in value):
            raise ValueError('Invalid layer identifiers')
    for tool in config['Tool_Parameters'].values():
        fields = {'diameter', 'speed', 'start_radius', 'lead_radius', 'lead_length', 'overcut_length', 'milling_offset'}
        if not isinstance(tool, dict) or not fields <= set(tool):
            raise ValueError('Invalid saved tool profile')
        if any(not _number(tool[key]) for key in fields if not (key == 'start_radius' and tool[key] is None)):
            raise ValueError('Invalid saved tool profile value')
    if min(config['Import_Parameters'][key] for key in ('point_tolerance', 'fitting_tolerance')) <= 0:
        raise ValueError('Invalid saved tolerance')


def decode_project(content):
    if not isinstance(content, str):
        raise ValueError('Project text required')
    if not content.lstrip('\ufeff \r\n\t').startswith('{'):
        return decode_d2g(content)
    data = json.loads(content.lstrip('\ufeff'), object_pairs_hook=_unique_object,
                      parse_constant=_invalid_number)
    if not isinstance(data, dict) or set(data) != {'format', 'version', 'source', 'machining'}:
        raise ValueError('Invalid .d2g document fields')
    if data['format'] != FORMAT:
        raise ValueError('Incorrect project format')
    if type(data['version']) not in (float, int) or data['version'] != VERSION:
        raise VersionMismatchError(data['version'], VERSION)
    validate_source(data['source'])
    try:
        project = MachiningProject.from_dict(data['machining'])
        validate_configuration(project)
    except (KeyError, TypeError, AttributeError) as error:
        raise ValueError('Invalid machining project data') from error
    return MachiningProjectDocument(VERSION, data['source'], project)


def encode_project(source, machining):
    validate_source(source)
    validate_configuration(machining)
    return json.dumps(dict(format=FORMAT, version=VERSION, source=source,
                           machining=machining.to_dict()), ensure_ascii=False,
                      allow_nan=False, indent=2) + '\n'
