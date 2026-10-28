# -*- coding: utf-8 -*-
"""Build complete toolpath command plans from the existing shape algorithms."""

from copy import copy, deepcopy
import logging
from math import pi

import dxf2gcode.bootstrap.runtime_state as g
from dxf2gcode.domain.geometry.arcgeo import ArcGeo
from dxf2gcode.domain.geometry.breakgeo import BreakGeo
from dxf2gcode.domain.geometry.holegeo import HoleGeo
from dxf2gcode.domain.toolpath.leadmove import (
    ERROR, LEAD_OFF, SPACE_NOMINAL, SPACE_TOOL_CENTER,
    build_exit_geometries, get_lead_in_mode, get_lead_out_mode,
    get_overcut_enabled, lead_move_enabled)
from dxf2gcode.domain.geometry.linegeo import LineGeo
from dxf2gcode.domain.geometry.point import Point
from dxf2gcode.domain.toolpath.pocketmove import PocketMove
from dxf2gcode.domain.project.shape import Geos
from dxf2gcode.adapters.toolpath.geometry_gcode import GeometryGCodeSerializer
from dxf2gcode.domain.toolpath.customgcode import CustomGCode
from dxf2gcode.presentation.qt.qt_compat.QtWidgets import QMessageBox
from dxf2gcode.domain.toolpath.plan import (
    ToolpathCommand, ToolpathMove, ToolpathPass, ToolpathPlan)

logger = logging.getLogger("Adapter.ShapeToolpathPlan")


class ShapeToolpathCommandBuilder:
    """Turn the established shape algorithm into an immutable command plan."""

    def __init__(self, shape):
        object.__setattr__(self, "_shape", shape)
        object.__setattr__(self, "_geometry_serializer", GeometryGCodeSerializer())

    def __getattr__(self, name):
        return getattr(self._shape, name)

    def __setattr__(self, name, value):
        shape = self.__dict__.get("_shape")
        if shape is not None and hasattr(shape, name):
            setattr(shape, name, value)
        else:
            object.__setattr__(self, name, value)

    @classmethod
    def build(cls, shape, postprocessor):
        """Plan every currently supported shape without emitting G-Code."""
        if isinstance(shape, CustomGCode):
            return cls._custom_code_plan(shape)
        if not hasattr(shape, "stmove"):
            raise TypeError("expected a Shape or CustomGCode instance")
        # Planning must not alter the live project model. The historical
        # algorithm reverses open contours and updates pocket move depths while
        # it walks passes, so it runs against an isolated model snapshot.
        planned_shape = copy(shape)
        external_refs = {id(shape): planned_shape}
        parent_layer = getattr(shape, "parentLayer", None)
        if parent_layer is not None:
            # A layer points back into GUI/project state; the plan builder only
            # reads its machining settings and must not clone that object graph.
            external_refs[id(parent_layer)] = parent_layer
        parent_entity = getattr(shape, "parentEntity", None)
        if parent_entity is not None:
            external_refs[id(parent_entity)] = parent_entity
        planned_shape.geos = deepcopy(shape.geos, external_refs)
        planned_shape.stmove = deepcopy(shape.stmove, external_refs)
        planning_postprocessor = copy(postprocessor)
        recorder = _ToolpathCommandRecorder(
            planning_postprocessor, postprocessor)
        builder = cls(planned_shape)
        builder.build_shape_commands(recorder)
        commands = () if recorder.had_export_error else recorder.commands
        return _plan_from_recorded_commands(planned_shape, commands)

    @staticmethod
    def _custom_code_plan(shape):
        return ToolpathPlan(
            shape_number=getattr(shape, "nr", 0), approach_xy=(0.0, 0.0),
            passes=(), workpiece_top=0.0, safe_margin=0.0,
            retract_depth=0.0, feed_depth=0.0, feed_xy=0.0,
            commands=(ToolpathCommand("literal", (shape.gcode,)),))

    def plan_lead_out_and_overcut(self, PostPro, geos, machine_comp):
        """
        The lead out and the overcut of the shape. Both of them are only
        written in the last pass.

        The overcut continues the cut along the existing contour beyond the
        closing point and is written first, the lead out starts at the end of
        the overcut and is written after it. Both of them can be used at the
        same time.

        @param PostPro: the post processor
        @param geos: the geometry of the last pass
        @param machine_comp: True if the machine compensates the tool radius
        @return: the G-Code, an empty string if nothing has to be written or
                None if an error occurred (the shape is not exported)
        """
        layer = self.parentLayer
        lead_out_mode = get_lead_out_mode(self)
        overcut_enabled = get_overcut_enabled(
            self, g.config.vars.Lead_In_Out['overcut_enabled'])
        if not lead_move_enabled():
            # The lathe is not supported by the lead out and the overcut.
            return ""
        if lead_out_mode == LEAD_OFF and not overcut_enabled:
            return ""

        if not len(geos):
            return ""

        tool_rad = layer.getToolRadius()
        # The lead out has to curve to the side of the active cutter
        # compensation: the machine offsets the programmed path to that side,
        # so the arc has to curve to the same side to get the wanted tool
        # center path radius (the workpiece radius minus the tool radius).
        # The compensation side changes with the direction of the contour (the
        # open contours are milled in alternating directions), so it has to be
        # taken from the pass which is exported now - not from the start
        # move, which was calculated for the first pass.
        if self.cut_cor == 41:
            side = 1
        elif self.cut_cor == 42:
            side = -1
        else:
            # The internal compensation: the offset direction does not change
            # with the direction of the contour.
            side = getattr(self.stmove, 'lead_side', 1)
            # The free side (away from the material) is a physical property.
            # The open contours are milled in alternating directions and the
            # last pass can be the mirrored one: relative to its reversed
            # travel direction the lead out has to curve to the other side.
            # (With the machine compensation this is already handled by the
            # switched cut_cor above.)
            last_pass_is_mirrored = getattr(self.stmove,
                                             '_last_pass_is_mirrored', None)
            if last_pass_is_mirrored is not None and last_pass_is_mirrored():
                side = -side
        # The machine compensates the tool radius: the exported path is the
        # nominal contour and the lead out is programmed in the nominal plane
        # (the machine offsets it). Without a machine compensation the
        # exported path is the tool center path, so the lead out has to be
        # calculated in the tool center plane.
        space = SPACE_NOMINAL if machine_comp else SPACE_TOOL_CENTER

        exit_geos, status, message = build_exit_geometries(
            geos, side, space, tool_rad, lead_out_mode,
            getattr(layer, 'lead_radius', 0.0), overcut_enabled,
            getattr(layer, 'overcut_length', 0.0), closed=self.closed,
            lead_length=getattr(layer, 'lead_length', 0.0))
        if status == ERROR:
            PostPro.add_export_error(
                self.tr("Shape %i: %s The shape is NOT milled!")
                % (self.nr, message))
            return None

        exstr = ""
        for geo in exit_geos:
            exstr += self.record_geometry_command(geo, PostPro)
        return exstr

    def plan_drag_knife_ramp_in(self, PostPro, ramp_length, z_start, z_end,
                                drag_depth, f_g1_plane, f_g1_depth):
        """
        The ramp in of the drag knife: over the given length (measured along
        the tip path) the knife is plunged gradually from z_start to z_end.

        The ramp ends before the first drag hop: there the knife is lifted to
        the drag depth instead of being plunged.

        @param PostPro: the post processor
        @param ramp_length: the length of the ramp in
        @param z_start: the Z at the beginning of the ramp
        @param z_end: the Z at the end of the ramp (the mill depth)
        @param drag_depth: the Z of a drag hop
        @return: the G-Code
        """
        exstr = ""
        ramp_remaining = ramp_length
        ramp_finished = False
        drag = False

        for geo in Geos(self.stmove.geos[1:]).abs_iter():
            is_drag = isinstance(geo, ArcGeo) and geo.drag
            if not ramp_finished and ramp_remaining > 0 and not is_drag:
                ramp_exstr, ramp_remaining = self.plan_ramp_geometry(
                    PostPro, geo, ramp_remaining, ramp_length, z_start, z_end)
                exstr += ramp_exstr
                if ramp_remaining > 0:
                    # The whole geometry was used for the ramp.
                    continue
                # The ramp is finished, the depth feed rate is used again.
                ramp_finished = True
                exstr += PostPro.chg_feed_rate(f_g1_plane)
                continue
            if is_drag:
                # The ramp in ends here, the knife is lifted instead.
                ramp_finished = True
                exstr += PostPro.chg_feed_rate(f_g1_depth)
                exstr += PostPro.lin_pol_z(drag_depth)
                exstr += PostPro.chg_feed_rate(f_g1_plane)
                drag = True
            elif drag:
                exstr += PostPro.chg_feed_rate(f_g1_depth)
                exstr += PostPro.lin_pol_z(z_end)
                exstr += PostPro.chg_feed_rate(f_g1_plane)
                drag = False
            exstr += self.record_geometry_command(geo, PostPro)

        return exstr

    def plan_ramp_geometry(self, PostPro, geo, length, ramp_length, z_start,
                         z_end):
        """
        The part of a geometry which is covered by the ramp in. The Z is
        decreased gradually while the tip advances.
        @param PostPro: the post processor
        @param geo: the geometry
        @param length: the length of the ramp in part of the geometry
        @param ramp_length: the total length of the ramp in
        @param z_start: the Z at the beginning of the ramp
        @param z_end: the Z at the end of the ramp
        @return: (gcode, remaining length of the ramp in)
        """
        total = geo.length
        if total <= 0:
            return "", length

        used = min(total, length)
        steps = max(2, int(round(used)))

        points = []
        if isinstance(geo, LineGeo):
            factor = used / total
            end = geo.Ps + (geo.Pe - geo.Ps) * factor
            for i in range(steps + 1):
                points.append(geo.Ps + (end - geo.Ps) * (float(i) / steps))
        elif isinstance(geo, ArcGeo):
            factor = used / total
            end_angle = geo.s_ang + geo.ext * factor
            for i in range(steps + 1):
                angle = geo.s_ang + (end_angle - geo.s_ang) * (float(i) / steps)
                points.append(geo.O.get_arc_point(angle, geo.r))
        else:
            return "", length

        exstr = ""
        previous = points[0]
        covered = 0.0
        for point in points[1:]:
            covered += previous.distance(point)
            z = z_start + (z_end - z_start) * (covered / ramp_length)
            exstr += PostPro.lin_pol_z(z)
            exstr += PostPro.lin_pol_xy(previous, point)
            previous = point
        return exstr, length - used

    def record_geometry_command(self, geo, PostPro):
        # Used to remove zero length geos. If not, arcs can become a full
        # circle
        
        if isinstance(geo, PocketMove):
            return self._geometry_serializer.export(geo, PostPro)
        
        if (self.Drill==True):
            Ps=Point(geo.O.x,geo.O.y)
            hgeo=HoleGeo(Ps)
            logger.debug("Will Write HoleGeo")
            return self._geometry_serializer.export(hgeo, PostPro)
        
        post_dec = PostPro.vars.Number_Format["post_decimals"]
        if isinstance(geo, HoleGeo) or\
           round(geo.Ps.x, post_dec) != round(geo.Pe.x, post_dec) or\
           round(geo.Ps.y, post_dec) != round(geo.Pe.y, post_dec) or\
           isinstance(geo, ArcGeo) and geo.length > 0.5 * 0.1 ** post_dec * pi:
            return self._geometry_serializer.export(geo, PostPro)
        else:
            return ""

    def build_shape_commands(self, PostPro):
        """
        This method returns the string to be exported for this shape, including
        the defined start and end move of the shape.
        @param PostPro: this is the Postprocessor class including the methods
        to export
        """
        # The start move calculation may have failed (e.g. an invalid lead in
        # radius or an overcut which is not possible): the shape is not
        # exported at all and the user gets a hint. This has to be checked
        # before the drag knife is handled, because the drag knife has no
        # lead in but it can have an overcut.
        start_move_error = getattr(self.stmove, 'start_move_error', "")
        if start_move_error:
            PostPro.add_export_error(
                self.tr("Shape %i: %s") % (self.nr, start_move_error))
            return ""

        if g.config.machine_type == 'drag_knife':
            return self.build_drag_knife_commands(PostPro)

        if isinstance(self.geos[0], HoleGeo):
            self.Drill            

        # The overcut continues the cut along the contour beyond the closing
        # point and is written first, the lead out starts at the end of the
        # overcut and is written after it. The overcut is only possible for
        # closed contours: for an open contour it is silently ignored (it is
        # not an error).
        layer = self.parentLayer

        prv_cut_cor = self.cut_cor
        # The cutter compensation is done by dxf2gcode itself: the exported
        # geometry is the pre-computed toolpath held in stmove (the
        # compensated contour and/or the pocket fill), not the raw shape
        # contour.
        software_comp = ((self.cut_cor != 40 or self.Pocket) and
                         not g.config.vars.Cutter_Compensation["done_by_machine"] and
                         not self.Drill)
        if software_comp:
            self.cut_cor = 40
            # The lead in is exported separately (it is written after the
            # plunge), so it is not part of the toolpath here.
            new_geos = Geos(self.stmove.geos[1 + len(self.stmove.lead_in_geos):])
        else:
            new_geos = self.geos

        if (self.cut_cor in (41, 42) and
                get_lead_in_mode(self) == LEAD_OFF):
            # Without a movement in the XY plane the machine can not build the
            # tool radius compensation: the plunge would be done at the
            # nominal contour position and the offset would be built up with
            # a lateral step in the milling depth.
            PostPro.add_export_error(
                self.tr("Shape %i: the lead in mode 'off' is not possible "
                        "with G41/G42: the machine can only build the tool "
                        "radius compensation with a movement in the XY plane "
                        "- the shape is NOT milled! Use the lead in mode "
                        "'startmove', 'straight' or 'radius'.") % self.nr)
            self.cut_cor = prv_cut_cor
            return ""

        # If there is nothing to export
        if len(new_geos) == 0:
            self.cut_cor = prv_cut_cor
            return ""

        # Break the contour once; for each pass it is decided whether the
        # original (unbroken) contour or the broken contour is exported.
        plain_geos = Geos(new_geos)
        split_geos = PostPro.breaks.getNewGeos(new_geos)
        break_heights = [geo.height for geo in split_geos
                         if isinstance(geo, BreakGeo)]
        # initialisation of the string
        exstr = ""

        # Get the mill settings defined in the GUI
        safe_retract_depth = self.parentLayer.axis3_retract
        safe_margin = self.parentLayer.axis3_safe_margin

        max_slice = -abs(self.axis3_slice_depth)
        workpiece_top_Z = self.axis3_start_mill_depth
        # We want to mill the piece, even for the first pass, so remove one
        # "slice"
        initial_mill_depth = workpiece_top_Z + max_slice
        depth = self.axis3_mill_depth
        f_g1_plane = self.f_g1_plane
        f_g1_depth = self.f_g1_depth

        # DXF output and non-repeated drill moves are emitted at one depth.
        single_pass = (
            PostPro.vars.General["output_type"] == 'dxf' or
            (self.Drill and
             PostPro.vars.General["repeat_drill_move"] == False))
        pass_depths = self.get_pass_depths(single_pass=single_pass)
        initial_mill_depth = pass_depths[0]

        if max_slice == 0:
            logger.warning(self.tr("Z infeed depth is null!"))
            QMessageBox.warning(g.window,
                                self.tr("Warning during Export"),
                                self.tr(self.tr("Error: Z infeed depth is null!")))

        if workpiece_top_Z < depth:
            logger.warning(self.tr(
                "Workpiece Top Z (%f0.2) is lower than end mill depth (%f0.2)") % (
                workpiece_top_Z, depth))
            QMessageBox.warning(g.window,
                        self.tr("Warning during Export"),
                        self.tr(self.tr("Workpiece Top Z (%f0.2) is lower than end mill depth (%f0.2)") % (
                                        workpiece_top_Z, depth)))
        # Compute the safe margin from the initial mill depth
        if initial_mill_depth < depth:
            logger.warning(self.tr(
                "Initial mill depth (%f0.2) is lower than end mill depth (%f0.2)") % (
                initial_mill_depth, depth))
            QMessageBox.warning(g.window,
                                    self.tr("Warning during Export"),
                                    self.tr(self.tr("Initial mill depth (%f0.2) is lower than end mill depth (%f0.2)") % (
                                                    initial_mill_depth, depth)))

            # Do not cut below the depth.
            # initial_mill_depth = depth

        mom_depth = initial_mill_depth

        # Resolve the pass from which the break tabs are processed.
        # break_pass: -1 = last pass (default), 0 = never, 1..n = pass number.
        # "Last pass" only processes the tabs when the final pass reaches
        # them, using the same Z height semantics as BreakGeo serialization.
        n_passes = len(pass_depths)
        break_pass = getattr(self, 'break_pass', -1)
        if self.Drill:
            # Drills never write the broken contour pieces: keep the
            # previous behavior (split list everywhere) unchanged.
            start_pass = 1
        elif break_pass == -1:
            start_pass = n_passes if any(
                height > pass_depths[-1] for height in break_heights) else 0
        elif break_pass == 0:
            start_pass = 0
        else:
            start_pass = min(int(break_pass), n_passes)

        if 1 < start_pass <= n_passes:
            # Both contour variants are exported: the broken one must not
            # share geometry objects with the original one, because the
            # per pass reversal of open contours would corrupt the other
            # list otherwise.
            plain_ids = set(id(geo) for geo in plain_geos.abs_iter())
            split_geos = Geos(
                deepcopy(geo) if id(geo) in plain_ids else geo
                for geo in split_geos)

        # Per pass contour selection with orientation bookkeeping for open
        # contours: pass 1 runs forward, passes 2, 4, ... run backwards. The
        # final restore reverses each contour variant that is left flipped
        # and balances the cutter compensation switches.
        flipped = {id(plain_geos): False, id(split_geos): False}
        reversals = [0]

        def pass_geos(pass_nr, pop_last=False):
            use_split = 0 < start_pass <= pass_nr
            geos = split_geos if use_split else plain_geos
            if pop_last:
                geos.pop()
            if not self.Drill and not self.closed:
                if flipped[id(geos)] != (pass_nr % 2 == 0):
                    self.reverse(geos)
                    flipped[id(geos)] = not flipped[id(geos)]
                    reversals[0] += 1
                    self.switch_cut_cor()
            return geos


        # This will be performed for "normal shapes only"
        if not(self.Drill):

            # The lead in is split into two parts:
            #  * the G40 part (up to lead_in_nominal_index): the tool center
            #    path which dxf2gcode calculates itself, cut without cutter
            #    compensation (G40),
            #  * the nominal part (from lead_in_nominal_index): the geometry
            #    which the machine compensates (G41/G42 is active while it is
            #    cut).
            # The straight lead in has no nominal part; the circle / start move
            # has the G40 approach line followed by the nominal line + arc.
            index = getattr(self.stmove, 'lead_in_nominal_index',
                            len(self.stmove.lead_in_geos))
            g40_geos = self.stmove.lead_in_geos[:index]
            nominal_geos = self.stmove.lead_in_geos[index:]

            # This will position the cutter on the first geometry with or without cutter comp. G1 move.
            exstr += self._geometry_serializer.export(
                self.stmove.geos.abs_el(0), PostPro)

            # Add string to be added before the shape will be cut.
            exstr += PostPro.write_pre_shape_cut()
            # The G40 lead in (the tool center path the dxf2gcode offset itself)
            # is cut before the plunge (in the free space above the workpiece)
            # if the cutter compensation is done outside the piece.
            if (self.cut_cor != 40 and
                    PostPro.vars.General["cc_outside_the_piece"]):
                exstr += PostPro.chg_feed_rate(f_g1_plane)
                for geo in g40_geos:
                    exstr += self._geometry_serializer.export(geo, PostPro)

            exstr += PostPro.rap_pos_z(workpiece_top_Z + abs(safe_margin))
            exstr += PostPro.chg_feed_rate(f_g1_depth)
            exstr += PostPro.lin_pol_z(mom_depth)
            exstr += PostPro.chg_feed_rate(f_g1_plane)


            # The G40 lead in is cut after the plunge if the compensation is
            # done inside the piece.
            if (self.cut_cor != 40 and
                    not PostPro.vars.General["cc_outside_the_piece"]):
                for geo in g40_geos:
                    exstr += self._geometry_serializer.export(geo, PostPro)
            elif software_comp:
                # The lead in of the internal cutter compensation is part of
                # the toolpath: it is cut after the plunge.
                for geo in self.stmove.lead_in_geos:
                    exstr += self.record_geometry_command(geo, PostPro)

            # Activate the machine cutter compensation after the G40 lead in:
            # the G40 part was cut without compensation, so the machine
            # compensates the nominal lead in and the nominal contour.
            if self.cut_cor != 40:
                exstr += PostPro.set_cut_cor(self.cut_cor)

            # The nominal lead in (circle / start move) is compensated by the
            # machine, so it is written after G41/G42.
            for geo in nominal_geos:
                exstr += self._geometry_serializer.export(geo, PostPro)

            first_pass_geos = pass_geos(1)
            for geo in first_pass_geos.abs_iter():
                if isinstance(geo, PocketMove):
                    geo.setZMove(f_g1_depth, f_g1_plane, workpiece_top_Z + abs(safe_margin), mom_depth, safe_retract_depth)
                    exstr += self._geometry_serializer.export(geo, PostPro)
                else:
                    exstr += self.record_geometry_command(geo, PostPro)
                if (self.Drill==True):
                    logger.debug("Stopping after 1st geometry as it will be drilled.")
                    break
                
                        # Turning the cutter radius compensation
            if (self.cut_cor != 40 and PostPro.vars.General["cancel_cc_for_depth"]):
                exstr += PostPro.deactivate_cut_cor()
        
        # If its a drill
        else:
            # This will position the cutter on the first geometry with or without cutter comp. G1 move.
            exstr += self._geometry_serializer.export(
                self.stmove.geos.abs_el(0), PostPro)

            # Add string to be added before the shape will be cut.
            exstr += PostPro.write_pre_shape_cut()
            
            #Posiioning is part of the Start Move                
            exstr += PostPro.rap_pos_z(workpiece_top_Z + abs(safe_margin))  
            exstr += PostPro.chg_feed_rate(f_g1_depth)
            exstr += PostPro.lin_pol_drill(mom_depth)
        


        # Numbers of loops
        snr = 0
        last_pass_geos = first_pass_geos if not self.Drill else Geos([])

        #logger.debug(size(depth))
        #logger.debug(depth)
        #logger.debug(max_slice)
        #logger.debug(mom_depth)
        # Loops for the number of cuts
        for snr, mom_depth in enumerate(pass_depths[1:], start=1):
                #logger.debug(mom_depth)
                
            #If this is last slice, remove last element
            # (no need to return to start point)
            cur_geos = pass_geos(snr + 1,
                                 mom_depth == depth and self.Pocket == True)
            if not self.Drill:
                last_pass_geos = cur_geos

            # Erneutes Eintauchen
            # This will be performed for "normal shapes only"
            if not(self.Drill):
                exstr += PostPro.chg_feed_rate(f_g1_depth)
                exstr += PostPro.lin_pol_z(mom_depth)
                exstr += PostPro.chg_feed_rate(f_g1_plane)

                # If it is not a closed contour: the reversal itself (and the
                # cutter compensation switch belonging to it) is handled in
                # pass_geos(); some interpreters cannot handle a switch, so
                # the compensation is turned off and on again around the pass
                if not self.closed:
                    if self.cut_cor != 40 and not PostPro.vars.General["cancel_cc_for_depth"]:
                        exstr += PostPro.deactivate_cut_cor()
                        exstr += PostPro.set_cut_cor(self.cut_cor)

                # If cutter correction is enabled
                if self.cut_cor != 40 and PostPro.vars.General["cancel_cc_for_depth"]:
                    exstr += PostPro.set_cut_cor(self.cut_cor)
                
                for geo in cur_geos.abs_iter():
                    if isinstance(geo, PocketMove):
                        geo.setZMove(f_g1_depth, f_g1_plane, workpiece_top_Z + abs(safe_margin), mom_depth, safe_retract_depth)
                        exstr += self._geometry_serializer.export(geo, PostPro)
                    else:
                        exstr += self.record_geometry_command(geo, PostPro)
                                
                # Turning off the cutter radius compensation if needed
                if self.cut_cor != 40 and PostPro.vars.General["cancel_cc_for_depth"]:
                    exstr += PostPro.deactivate_cut_cor()

                # Turning off the cutter radius compensation if needed
                if self.cut_cor != 40 and PostPro.vars.General["cancel_cc_for_depth"]:
                    exstr += PostPro.deactivate_cut_cor()

            # If its a drill do intermediate retraction and drill operation again
            else:
                exstr += PostPro.lin_ret_drill(workpiece_top_Z + abs(safe_margin))
                exstr += PostPro.lin_pol_drill(mom_depth)
        

        # The lead out and the overcut are written in the last pass only: in a
        # intermediate pass they would remove material which is not part of
        # the wanted geometry (and they could release the workpiece before it
        # is finished).
        machine_comp = (prv_cut_cor in (41, 42) and
                        g.config.vars.Cutter_Compensation["done_by_machine"])
        lead_out_exstr = self.plan_lead_out_and_overcut(PostPro,
                                                          last_pass_geos,
                                                          machine_comp)
        if lead_out_exstr is None:
            # An error occurred: the shape is not exported at all.
            self.cut_cor = prv_cut_cor
            return ""
        exstr += lead_out_exstr

        # Do the tool retraction for a "normal" shape and Drill
        exstr += PostPro.chg_feed_rate(f_g1_depth)
        exstr += PostPro.lin_pol_z(workpiece_top_Z + abs(safe_margin))
        exstr += PostPro.rap_pos_z(safe_retract_depth)

        # If cutter radius compensation is turned on.
        if self.cut_cor != 40 and not PostPro.vars.General["cancel_cc_for_depth"]:
            exstr += PostPro.deactivate_cut_cor()

        # Initial values of direction and cutter compensation restored if
        # necessary
        if flipped[id(plain_geos)]:
            self.reverse(plain_geos)
        if flipped[id(split_geos)]:
            self.reverse(split_geos)
        if reversals[0] % 2 == 1:
            self.switch_cut_cor()

        self.cut_cor = prv_cut_cor

        # Add string to be added before the shape will be cut.
        exstr += PostPro.write_post_shape_cut()

        return exstr

    def build_drag_knife_commands(self, PostPro):
        """
        This method returns the string to be exported for this shape, including
        the defined start and end move of the shape. This function is used for
        Drag Knife cutting machine only.
        @param PostPro: this is the Postprocessor class including the methods
        to export
        """

        # initialisation of the string
        exstr = ""

        # Get the mill settings defined in the GUI
        safe_retract_depth = self.parentLayer.axis3_retract
        safe_margin = self.parentLayer.axis3_safe_margin

        workpiece_top_Z = self.axis3_start_mill_depth
        f_g1_plane = self.f_g1_plane
        f_g1_depth = self.f_g1_depth

        """
        Cutting in slices is not supported for Swivel Knife tool. All is cut at once.
        """
        mom_depth = self.axis3_mill_depth
        drag_depth = self.axis3_slice_depth

        # Move the tool to the start with G1.
        exstr += self._geometry_serializer.export(
                self.stmove.geos.abs_el(0), PostPro)

        # Add string to be added before the shape will be cut.
        exstr += PostPro.write_pre_shape_cut()

        # Move into workpiece and start cutting into Z
        exstr += PostPro.rap_pos_z(
            workpiece_top_Z + abs(safe_margin))  # Compute the safe margin from the initial mill depth
        exstr += PostPro.chg_feed_rate(f_g1_depth)

        ramp_length = g.config.vars.Drag_Knife_Options['ramp_in_length']
        if ramp_length > 0:
            # The knife is plunged gradually over the ramp in length. The ramp
            # ends before the first drag hop, because there the knife is
            # lifted instead of plunged.
            exstr += self.plan_drag_knife_ramp_in(
                PostPro, ramp_length, workpiece_top_Z + abs(safe_margin),
                mom_depth, drag_depth, f_g1_plane, f_g1_depth)
        else:
            # Write the geometries for the first cut
            if isinstance(self.stmove.geos.abs_el(1), ArcGeo):
                if self.stmove.geos.abs_el(1).drag:
                    exstr += PostPro.lin_pol_z(drag_depth)
                    drag = True
                else:
                    exstr += PostPro.lin_pol_z(mom_depth)
                    drag = False
            else:
                exstr += PostPro.lin_pol_z(mom_depth)
                drag = False
            exstr += PostPro.chg_feed_rate(f_g1_plane)

            exstr += self._geometry_serializer.export(
                self.stmove.geos.abs_el(1), PostPro)

            for geo in Geos(self.stmove.geos[2:]).abs_iter():
                if isinstance(geo, ArcGeo):
                    if geo.drag:
                        exstr += PostPro.chg_feed_rate(f_g1_depth)
                        exstr += PostPro.lin_pol_z(drag_depth)
                        exstr += PostPro.chg_feed_rate(f_g1_plane)
                        drag = True
                    elif drag:
                        exstr += PostPro.chg_feed_rate(f_g1_depth)
                        exstr += PostPro.lin_pol_z(mom_depth)
                        exstr += PostPro.chg_feed_rate(f_g1_plane)
                        drag = False
                elif drag:
                    exstr += PostPro.chg_feed_rate(f_g1_depth)
                    exstr += PostPro.lin_pol_z(mom_depth)
                    exstr += PostPro.chg_feed_rate(f_g1_plane)
                    drag = False

                exstr += self.record_geometry_command(geo, PostPro)

        # Do the tool retraction
        exstr += PostPro.chg_feed_rate(f_g1_depth)
        exstr += PostPro.lin_pol_z(workpiece_top_Z + abs(safe_margin))
        exstr += PostPro.rap_pos_z(safe_retract_depth)

        # Add string to be added before the shape will be cut.
        exstr += PostPro.write_post_shape_cut()

        return exstr


class _ToolpathCommandRecorder:
    """Record postprocessor operations while simulating their state changes."""

    def __init__(self, planning_postprocessor, diagnostic_sink):
        self._planning_postprocessor = planning_postprocessor
        self._diagnostic_sink = diagnostic_sink
        self.commands = []
        self.had_export_error = False

    def __getattr__(self, name):
        value = getattr(self._planning_postprocessor, name)
        if name == "add_export_error":
            def add_export_error(message):
                self.had_export_error = True
                return self._diagnostic_sink.add_export_error(message)
            return add_export_error
        if not callable(value):
            return value

        def record(*args, **kwargs):
            self.commands.append(ToolpathCommand(
                method=name,
                args=deepcopy(args),
                kwargs=tuple(sorted(deepcopy(kwargs).items())),
            ))
            # The return text is discarded here, but invoking the real method
            # on the private postprocessor copy preserves its modal state for
            # later planning decisions (incremental coordinates, feed, Z).
            value(*args, **kwargs)
            return ""

        return record


def _xy(point):
    return (float(point.x), float(point.y))


def _plan_from_recorded_commands(shape, commands):
    layer = getattr(shape, "parentLayer", None)
    workpiece_top = float(getattr(shape, "axis3_start_mill_depth", 0.0))
    moves_by_depth = []
    active_depth = workpiece_top

    def add_move(move):
        if not moves_by_depth or moves_by_depth[-1][0] != active_depth:
            moves_by_depth.append((active_depth, []))
        moves_by_depth[-1][1].append(move)

    approach = (0.0, 0.0)
    for command in commands:
        args = command.args
        if command.method == "rap_pos_xy" and args:
            approach = _xy(args[0])
        elif command.method in ("lin_pol_z", "lin_pol_drill") and args:
            active_depth = float(args[0])
        elif command.method == "lin_pol_xy" and len(args) >= 2:
            add_move(ToolpathMove("linear_xy", _xy(args[0]), _xy(args[1])))
        elif command.method == "lin_pol_arc" and len(args) >= 9:
            _direction, start, end, _start_angle, _end_angle, _radius, center, _ij, sweep = args[:9]
            add_move(ToolpathMove(
                "arc", _xy(start), _xy(end), _xy(center), float(sweep)))

    passes = tuple(
        ToolpathPass(number=index + 1, depth=depth,
                     moves=tuple(moves))
        for index, (depth, moves) in enumerate(moves_by_depth) if moves)
    return ToolpathPlan(
        shape_number=getattr(shape, "nr", 0),
        approach_xy=approach,
        passes=passes,
        workpiece_top=workpiece_top,
        safe_margin=float(getattr(layer, "axis3_safe_margin", 0.0)),
        retract_depth=float(getattr(layer, "axis3_retract", 0.0)),
        feed_depth=float(getattr(shape, "f_g1_depth", 0.0)),
        feed_xy=float(getattr(shape, "f_g1_plane", 0.0)),
        commands=tuple(commands),
    )
