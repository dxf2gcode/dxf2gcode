"""Codec for the existing, versioned ``.d2g`` assignment format.

The legacy Project facade applies the decoded values to current application
objects. This module only validates and decodes the persisted representation.
"""

import ast
import re
from math import isfinite
from dataclasses import dataclass

from dxf2gcode.application.exceptions import VersionMismatchError


D2G_HEADER = "# +~+~+~ DXF2GCODE project file V%s ~+~+~+"
SUPPORTED_D2G_VERSIONS = (1.1, 1.2, 1.3, 1.4, 1.5)
CURRENT_D2G_VERSION = SUPPORTED_D2G_VERSIONS[-1]

_ALLOWED_D2G_ATTRS = frozenset([
    "file", "point_tol", "fitting_tol",
    "scale", "rot",
    "wpzero_x", "wpzero_y",
    "mirrorx", "mirrory",
    "split_lines", "aut_cut_com", "machine_type", "layers", "drag_knife",
])


@dataclass(frozen=True)
class LegacyProjectDocument:
    version: float
    values: dict


def decode_d2g(content):
    """Decode a legacy project string without executing its contents."""
    header_pattern = D2G_HEADER.replace("+", r"\+") % r"(\d+\.\d+)"
    match = re.match(header_pattern, content)
    if not match:
        raise Exception("Incorrect project file")

    version = float(match.groups()[0])
    if version not in SUPPORTED_D2G_VERSIONS:
        raise VersionMismatchError(match.group(), CURRENT_D2G_VERSION)

    tree = ast.parse(content)
    values = {}
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Assign):
            targets = node.targets
            if len(targets) != 1 or not isinstance(targets[0], ast.Attribute):
                raise ValueError(
                    "Line {}: Only 'd2g.<attr> = <value>' assignments allowed"
                    .format(node.lineno))
            attr_node = targets[0]
            if not (isinstance(attr_node.value, ast.Name)
                    and attr_node.value.id == "d2g"):
                raise ValueError(
                    "Line {}: Target must be 'd2g', got {}"
                    .format(node.lineno, ast.dump(attr_node)))
            attr_name = attr_node.attr
            if attr_name not in _ALLOWED_D2G_ATTRS:
                raise ValueError(
                    "Line {}: Unknown/dangerous attribute '{}'"
                    .format(node.lineno, attr_name))
            values[attr_name] = ast.literal_eval(node.value)
        elif isinstance(node, ast.Expr):
            # Match the legacy reader: standalone expressions are ignored.
            pass
        else:
            raise ValueError(
                "Line {}: Unexpected statement '{}'"
                .format(node.lineno, type(node).__name__))

    if 'drag_knife' in values:
        validate_knife_settings(values['drag_knife'], legacy=version < 1.5)
    if version < 1.5:
        knife = values.get('drag_knife')
        legacy_knife = values.get('machine_type') == 'drag_knife' and not (knife or {}).get('planned_passes', False)
        if legacy_knife:
            for layer in values.get('layers', []):
                layer.update(lead_in_mode='off', lead_out_mode='off')
                for shape in layer['shapes']:
                    if 'gcode' in shape:
                        continue
                    shape['drag_swivel_depth'] = shape['slice_depth']
                    shape['slice_depth'] = -(abs(shape['mill_depth'] - shape['start_mill_depth'])
                                             or abs(shape['slice_depth']) or 1.0)
                    shape.update(lead_in_mode='off', lead_out_mode='off')
            if knife:
                knife.update(extra_pass=False, alternate=False, return_to_start=False, entry_mode='fixed')
                knife['lead_defaults'].update(lead_in_mode='off', lead_out_mode='off')
        if knife:
            knife.pop('planned_passes', None)
    for layer in values.get('layers', []):
        for shape in layer.get('shapes', []):
            depth = shape.get('drag_swivel_depth')
            if depth is not None and (type(depth) not in (int, float) or not isfinite(depth)):
                raise ValueError('Invalid contour swivel depth')
    return LegacyProjectDocument(version=version, values=values)


def validate_knife_settings(values, legacy=False):
    """Reject malformed project settings before applying any application state."""
    boolean = {'extra_pass', 'alternate', 'return_to_start'}
    if legacy:
        boolean.add('planned_passes')
    numeric = {'swivel_depth', 'ramp_in_length', 'lead_out_length', 'drag_angle', 'drag_start_angle', 'alignment_length'}
    if not isinstance(values, dict):
        raise ValueError('Invalid drag-knife project settings')
    # Earlier local 1.4 snapshots contain only the original start-angle mode.
    values.setdefault('entry_mode', 'fixed')
    values.setdefault('alignment_length', 0.0)
    values.setdefault('return_to_start', False)
    if set(values) != boolean | numeric | {'units', 'lead_defaults', 'entry_mode'}:
        raise ValueError('Invalid drag-knife project settings')
    if values['units'] not in ('mm', 'in'):
        raise ValueError('Invalid drag-knife units')
    if values['entry_mode'] not in ('fixed','previous','unknown'):
        raise ValueError('Invalid drag-knife orientation mode')
    leads = values['lead_defaults']
    if (not isinstance(leads, dict) or set(leads) != {'lead_in_mode', 'lead_out_mode', 'overcut_enabled'}
            or leads['lead_in_mode'] not in ('off','straight','startmove')
            or leads['lead_out_mode'] not in ('off','straight','radius','startmove')
            or type(leads['overcut_enabled']) is not bool):
        raise ValueError('Invalid drag-knife lead defaults')
    if any(type(values[k]) is not bool for k in boolean):
        raise ValueError('Invalid drag-knife switch')
    if any(type(values[k]) not in (int, float) or not isfinite(values[k]) for k in numeric):
        raise ValueError('Invalid drag-knife number')
    if (min(values['ramp_in_length'], values['lead_out_length'], values['alignment_length']) < 0
            or not 0 <= values['drag_angle'] <= 360
            or not -360 <= values['drag_start_angle'] <= 360):
        raise ValueError('Invalid drag-knife range')

