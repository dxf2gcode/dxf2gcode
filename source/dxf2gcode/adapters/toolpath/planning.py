"""Snapshot project geometry and profiles for the pure toolpath planner."""

from dataclasses import replace

from dxf2gcode.domain.geometry.arcgeo import ArcGeo
from dxf2gcode.domain.geometry.breakgeo import BreakGeo
from dxf2gcode.domain.geometry.holegeo import HoleGeo
from dxf2gcode.domain.geometry.linegeo import LineGeo
from dxf2gcode.domain.geometry.point import Point
from dxf2gcode.domain.project.shape import Geos
from dxf2gcode.domain.project.tool_settings import effective_tool
from dxf2gcode.domain.toolpath.customgcode import CustomGCode
from dxf2gcode.domain.toolpath.inputs import (
    MachineCapabilities, MachiningSettings, PathGeometry, PlanningState,
    ToolpathRequest)
from dxf2gcode.domain.toolpath.leadmove import (
    ERROR, SPACE_NOMINAL, SPACE_TOOL_CENTER, build_exit_geometries,
    get_lead_in_mode, get_lead_out_mode, get_overcut_enabled)
from dxf2gcode.domain.toolpath.pocketmove import PocketMove
from dxf2gcode.domain.toolpath.stmove import RapidPos
from dxf2gcode.domain.toolpath.tabs import TabRegion, map_tabs


def _xy(point):
    return (point.x, point.y)


def snapshot_geometry(geo):
    """Copy value data only; no live geometry or project references escape."""
    result = _snapshot_geometry_value(geo)
    absolute = getattr(geo, "abs_geo", None)
    if absolute is not None:
        result = replace(result, absolute=_snapshot_geometry_value(absolute))
    return result


def _snapshot_geometry_value(geo):
    if isinstance(geo, RapidPos):
        return PathGeometry("rapid", _xy(geo), _xy(geo))
    start = _xy(geo.get_start_end_points(True))
    end = _xy(geo.get_start_end_points(False))
    length = getattr(geo, "length", 0.0)
    if isinstance(geo, BreakGeo):
        return PathGeometry(
            "break", start, end, length, height=geo.height,
            xy_feed=geo.xyfeed, z_feed=geo.zfeed, modifier_id=geo.modifier_id,
            tab_geometry=geo.tab_geometry)
    if isinstance(geo, PocketMove):
        return PathGeometry(
            "pocket", start, end, length, xy_feed=geo.feedXY, z_feed=geo.feedZ,
            safe_depth=geo.safe, depth=geo.depth, retract_depth=geo.retr)
    if isinstance(geo, HoleGeo):
        return PathGeometry("hole", start, end, length)
    if isinstance(geo, ArcGeo):
        return PathGeometry(
            "arc", start, end, length, center=_xy(geo.O), radius=geo.r,
            start_angle=geo.s_ang, end_angle=geo.e_ang, sweep=geo.ext,
            drag=getattr(geo, "drag", False))
    if isinstance(geo, LineGeo):
        return PathGeometry("line", start, end, length)
    raise TypeError("unsupported toolpath geometry: %s" % type(geo).__name__)


def _existing_geometry(geo):
    """Adapt immutable geometry values to the established exit algorithms."""
    start, end = Point(*geo.start), Point(*geo.end)
    if geo.kind == "break":
        return BreakGeo(start, end, geo.height, geo.xy_feed, geo.z_feed, geo.modifier_id, geo.tab_geometry)
    if geo.kind == "pocket":
        result = PocketMove(start, end)
        result.setZMove(geo.z_feed, geo.xy_feed, geo.safe_depth, geo.depth,
                        geo.retract_depth)
        return result
    if geo.kind == "hole":
        return HoleGeo(start)
    if geo.kind == "arc":
        result = ArcGeo(Ps=start, Pe=end, O=Point(*geo.center),
                        r=geo.radius, direction=geo.sweep)
        result.s_ang, result.e_ang = geo.start_angle, geo.end_angle
        result.ext, result.length, result.drag = geo.sweep, geo.length, geo.drag
        return result
    if geo.kind == "rapid":
        return RapidPos(end)
    return LineGeo(start, end)


def exit_geometry(chain, side, machine_compensation, settings, closed):
    """Reuse lead/overcut geometry without giving the planner Qt or globals."""
    geometries, status, message = build_exit_geometries(
        tuple(_existing_geometry(geo) for geo in chain), side,
        SPACE_NOMINAL if machine_compensation else SPACE_TOOL_CENTER,
        settings.tool_radius, settings.lead_out_mode, settings.lead_radius,
        settings.overcut_enabled, settings.overcut_length,
        closed=closed, lead_length=settings.lead_length)
    if status == ERROR:
        return (), message
    return tuple(snapshot_geometry(geo) for geo in geometries), ""


def snapshot_capabilities(postprocessor, config):
    general = postprocessor.vars.General
    return MachineCapabilities(
        output_type=general["output_type"],
        repeat_drill_move=general["repeat_drill_move"],
        compensation_outside_piece=general["cc_outside_the_piece"],
        cancel_compensation_for_depth=general["cancel_cc_for_depth"],
        post_decimals=postprocessor.vars.Number_Format["post_decimals"],
        max_arc_radius=general["max_arc_radius"],
        arcs_as_lines=general["export_arcs_as_lines"],
        counterclockwise_arcs_only=general["export_ccw_arcs_only"],
        fitting_tolerance=config.fitting_tolerance,
        absolute_coordinates=postprocessor.abs_export)


class ShapePlanningInputs:
    """Read existing model/profile values at the application boundary."""

    def __init__(self, config_provider):
        self._config_provider = config_provider

    def request(self, shape, postprocessor):
        shape = getattr(shape, '_machining_view', None) or shape
        config = getattr(shape, 'machining_config', None) or self._config_provider()
        capabilities = snapshot_capabilities(postprocessor, config)
        if isinstance(shape, CustomGCode):
            return ToolpathRequest(
                shape.nr, MachiningSettings(), capabilities, literal=shape.gcode)
        if getattr(shape, "stmove", None) is None:
            raise ValueError("shape start geometry must be prepared before planning")
        tool, layer = effective_tool(shape), shape.parentLayer
        settings = MachiningSettings(
            machine_type=config.machine_type,
            machine_compensation=config.vars.Cutter_Compensation["done_by_machine"],
            workpiece_top=shape.axis3_start_mill_depth,
            slice_depth=shape.axis3_slice_depth, final_depth=shape.axis3_mill_depth,
            feed_xy=shape.f_g1_plane, feed_depth=shape.f_g1_depth,
            safe_margin=layer.axis3_safe_margin, retract_depth=layer.axis3_retract,
            break_pass=getattr(shape, "break_pass", -1),
            lead_in_mode=get_lead_in_mode(shape),
            lead_out_mode=get_lead_out_mode(shape),
            overcut_enabled=get_overcut_enabled(
                shape, config.vars.Lead_In_Out["overcut_enabled"]),
            tool_radius=tool.getToolRadius(),
            lead_radius=getattr(tool, "lead_radius", 0.0),
            lead_length=getattr(tool, "lead_length", 0.0),
            overcut_length=getattr(tool, "overcut_length", 0.0),
            lead_side=getattr(shape.stmove, "lead_side", 1),
            drag_ramp_length=config.vars.Drag_Knife_Options["ramp_in_length"],
            drag_swivel_depth=getattr(shape, 'drag_swivel_depth', config.vars.Drag_Knife_Options.swivel_depth),
            drag_extra_pass=getattr(config.vars.Drag_Knife_Options, "extra_pass", False),
            drag_alternate=getattr(config.vars.Drag_Knife_Options, "alternate", False),
            drag_exit_length=getattr(config.vars.Drag_Knife_Options, "lead_out_length", 1.5),
            drag_start_angle=config.vars.Drag_Knife_Options["drag_start_angle"],
            drag_angle=shape.drag_angle,
            drag_entry_mode=getattr(config.vars.Drag_Knife_Options, 'entry_mode', 'fixed'),
            drag_alignment_length=getattr(config.vars.Drag_Knife_Options, 'alignment_length', 0.0),
            drag_return=getattr(config.vars.Drag_Knife_Options, 'return_to_start', False),
            tool_number=tool.tool_nr,
            point_tolerance=config.point_tolerance)
        # Preserve source metadata as well as the absolute movement geometry.
        # In particular, a source BreakGeo can have a LineGeo as abs_geo:
        # exit geometry must still recognize the source tab.
        contour = tuple(shape.geos)
        prepared = tuple(shape.stmove.geos)
        leads = tuple(shape.stmove.lead_in_geos)
        software_comp = ((shape.cut_cor != 40 or shape.Pocket) and
                         not settings.machine_compensation and not shape.Drill)
        cut_geos = prepared[1 + len(leads):] if software_comp else contour
        breaks = getattr(postprocessor, "breaks", None)
        # Break intersection is an existing geometry adapter, not a postprocessor
        # movement call. Freeze its result before any strategy traverses passes.
        pocket_ids = {id(geo) for geo in prepared[
            getattr(shape.stmove, "pocket_geos_start", len(prepared)):]} if shape.Pocket else set()

        def frozen(geo, role=None):
            return replace(snapshot_geometry(geo),
                           role=role or ("pocket" if id(geo) in pocket_ids else "cut"))

        def legacy_split(geometries):
            return tuple(frozen(part, 'pocket' if id(geo) in pocket_ids else 'cut')
                         for geo in geometries for part in
                         (breaks.getNewGeos(Geos([geo])) if breaks is not None else (geo,)))

        split = None
        skipped_tabs = 0
        if breaks is not None and settings.machine_type != 'drag_knife' and not shape.Drill:
            regions = []
            unsupported = 0
            for break_layer in breaks.breakLayers:
                for region in break_layer.shapes.not_disabled_iter():
                    edges = tuple(region.geos.abs_iter())
                    if (region.closed and len(edges) >= 3 and all(isinstance(edge, LineGeo) for edge in edges)
                            and all(edge.Pe.distance(next_edge.Ps) <= config.point_tolerance
                                    for edge, next_edge in zip(edges, edges[1:]+edges[:1]))):
                        regions.append(TabRegion(tuple(_xy(edge.Ps) for edge in edges),
                            region.axis3_mill_depth, region.f_g1_plane, region.f_g1_depth,
                            getattr(region, 'operation_id', '')))
                    else:
                        unsupported += 1
            nominal = tuple(snapshot_geometry(geo).resolved for geo in contour)
            if all(geo.kind in ('line', 'arc') for geo in nominal):
                # Boundary contours use nominal contact points in both modes.
                # Pocket raster passes have no one-to-one contour counterpart;
                # their existing spatial region intersections remain unchanged.
                boundary = tuple(frozen(geo) for geo in cut_geos if id(geo) not in pocket_ids)
                offset = (settings.tool_radius + getattr(shape, 'milling_offset', 0.0)
                          if software_comp and shape.cut_cor != 40 else 0.)
                mapped, skipped = map_tabs(nominal, boundary, tuple(regions), offset,
                                          shape.closed, max(1e-8, config.point_tolerance))
                fill = legacy_split(geo for geo in cut_geos if id(geo) in pocket_ids)
                split = mapped + fill
                skipped_tabs = len(skipped) + unsupported
        if split is None:
            split = legacy_split(cut_geos)
        return ToolpathRequest(
            shape.nr, settings, capabilities,
            contour=tuple(snapshot_geometry(geo) for geo in contour),
            prepared_path=tuple(frozen(geo) for geo in prepared),
            split_contour=split,
            lead_in=tuple(snapshot_geometry(geo) for geo in leads),
            lead_nominal_index=getattr(shape.stmove, "lead_in_nominal_index",
                                       len(leads)),
            closed=shape.closed, compensation=shape.cut_cor,
            pocket=shape.Pocket, drill=shape.Drill,
            has_break_layers=bool(getattr(breaks, "breakLayers", ())),
            skipped_tabs=skipped_tabs,
            start_error=getattr(shape.stmove, "start_move_error", ""),
            initial_state=PlanningState(postprocessor.feed, postprocessor.ze,
                                        postprocessor.lz,
                                        getattr(postprocessor, 'knife_heading', None)
                                        if (getattr(config.vars.Drag_Knife_Options, 'entry_mode', 'fixed') == 'previous'
                                            and getattr(postprocessor, 'knife_tool', None) == (tool.tool_nr, tool.getToolRadius()))
                                        else None))
