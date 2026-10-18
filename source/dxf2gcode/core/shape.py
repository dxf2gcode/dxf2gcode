# -*- coding: utf-8 -*-

############################################################################
#
#   Copyright (C) 2008-2015
#    Christian Kohlöffel
#    Vinzenz Schulz
#    Jean-Paul Schouwstra
#
#   Copyright (C) 20019-2020
#    San Zamoyski (PocketMill parts)
#
#   This file is part of DXF2GCODE.
#
#   DXF2GCODE is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   DXF2GCODE is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with DXF2GCODE.  If not, see <http://www.gnu.org/licenses/>.
#
############################################################################

from __future__ import absolute_import
from __future__ import division

from math import radians, pi
from copy import deepcopy
import logging

import dxf2gcode.globals.globals as g
from dxf2gcode.core.point import Point
from dxf2gcode.core.linegeo import LineGeo
from dxf2gcode.core.arcgeo import ArcGeo
from dxf2gcode.core.holegeo import HoleGeo
from dxf2gcode.core.breakgeo import BreakGeo
from dxf2gcode.core.pocketmove import PocketMove

import dxf2gcode.globals.constants as c
from dxf2gcode.Qt import QtCore
from dxf2gcode.Qt.QtWidgets import QMessageBox

logger = logging.getLogger("Core.Shape")


class Shape(object):

    """
    The Shape Class includes all plotting, GUI functionality and export functions
    related to the Shapes.
    """
    # only need default arguments here because of the change of usage with
    # super in QGraphicsItem

    def __init__(self, nr=-1, closed=True, parentEntity=None, geos=[]):
        if nr == -1:
            return

        self.type = "Shape"
        self.nr = nr
        self.closed = closed
        self.cut_cor = 40
        self.Pocket = False
        self.Drill = False
        self.parentEntity = parentEntity
        self.parentLayer = None
        self.geos = Geos(geos)

        self.cw = True

        self.stmove = None

        self.send_to_TSP = g.config.vars.Route_Optimisation['default_TSP']

        self.selected = False
        self.disabled = False
        self.allowedToChange = True

        # preset defaults
        self.axis3_start_mill_depth = g.config.vars.Depth_Coordinates[
            'axis3_start_mill_depth']
        self.axis3_slice_depth = g.config.vars.Depth_Coordinates[
            'axis3_slice_depth']
        self.axis3_mill_depth = g.config.vars.Depth_Coordinates[
            'axis3_mill_depth']
        self.f_g1_plane = g.config.vars.Feed_Rates['f_g1_plane']
        self.f_g1_depth = g.config.vars.Feed_Rates['f_g1_depth']
        # Parameters for drag knife
        self.drag_angle = radians(
            g.config.vars.Drag_Knife_Options['drag_angle'])

        # Break tab processing: -1 = last pass (default), 0 = never,
        # 1..n = process the tabs from this pass number on.
        self.break_pass = -1

    def __repr__(self):
        """
        Standard method to print the object
        @return: A string
        """

        #logger.debug(self.closed)
        return "Shape (nr=%i, closed=%s, geos=%s)" % \
                (self.nr, self.closed, self.geos)

    def tr(self, string_to_translate):
        """
        Translate a string using the QCoreApplication translation framework
        @param: string_to_translate: a unicode string
        @return: the translated unicode string if it was possible to translate
        """
        return str(QtCore.QCoreApplication.translate("Shape",
                                                           string_to_translate))

    def setSelected(self, flag=False):
        self.selected = flag

    def isSelected(self):
        return self.selected

    def setDisable(self, flag=False):
        self.disabled = flag

    def isDisabled(self):
        return self.disabled

    def isDrill(self):
        return self.Drill

    def setToolPathOptimized(self, flag=False):
        self.send_to_TSP = flag

    def isToolPathOptimized(self):
        return self.send_to_TSP

    def isDirectionOfGeosCCW(self, geos):
        # By calculating the area of the shape
        start = geos.abs_el(0).get_start_end_points(True)
        summe = 0.0
        for geo in geos.abs_iter():
            if isinstance(geo, LineGeo):
                end = geo.get_start_end_points(False)
                summe += (start.x + end.x) * (end.y - start.y)
                start = end
            elif isinstance(geo, ArcGeo):
                segments = 10
                for i in range(1, segments + 1):
                    end = geo.get_point_from_start(i, segments)
                    summe += (end.x + start.x) * (end.y - start.y)
                    start = end
        if not self.closed:
            # if shape is not closed... simply treat it as closed
            end = geos.abs_el(0).get_start_end_points(True)
            summe += (end.x + start.x) * (end.y - start.y)

        if summe == 0:  # inconclusive
            logger.debug(
                self.tr("Shoelace method cannot (directly) be applied to this shape"))
            # lets take it clock wise with relation to the workpiece zero

            start = geos.abs_el(0).get_start_end_points(True)
            # get the farthest end point with relation to the start
            end = start
            distance2 = 0
            for geo in geos.abs_iter():
                pos_end = geo.get_start_end_points(False)
                pos_distance2 = (start - pos_end).length_squared()
                if pos_distance2 > distance2:
                    end = pos_end
                    distance2 = pos_distance2
            direction = start.to3D().cross_product(end.to3D()).z
            # start and end are aligned wrt to wp zero
            if -1e-5 < direction < 1e-5:
                direction = start.length_squared() - end.length_squared()
            summe = direction
        return summe > 0.0

    def AnalyseAndOptimize(self):
        self.setNearestStPoint(Point())
        logger.debug(
            self.tr("Analysing the shape for CW direction Nr: %s" % self.nr))

        if self.isDirectionOfGeosCCW(self.geos):
            self.reverse()
            logger.debug(self.tr("Had to reverse the shape to be CW"))
        self.cw = True

    def setNearestStPoint(self, stPoint):
        if self.closed:
            logger.debug(self.tr("Clicked Point: %s" % stPoint))
            start = self.get_start_end_points(True)
            logger.debug(self.tr("Old Start Point: %s" % start))

            min_geo_nr, _ = min(enumerate(self.geos.abs_iter()),
                                key=lambda geo:
                                geo[1].get_start_end_points(True).distance(stPoint))

            # Overwrite the geometries in changed order.
            self.geos = Geos(self.geos[min_geo_nr:] + self.geos[:min_geo_nr])

            start = self.get_start_end_points(True)
            logger.debug(self.tr("New Start Point: %s" % start))
        elif len (self.geos) > 0:
            # if shape is not closed, we can just select between start and end points
            dist1 = self.geos.abs_el(0).get_start_end_points(True).distance(stPoint)
            dist2 = self.geos.abs_el(-1).get_start_end_points(False).distance(stPoint)
            if dist2 < dist1:
                self.reverse()

        # Update start move after reordering the shape
        if self.stmove is not None:
            self.stmove.updateShape()

    def setSharpestStPoint(self):
        """
        Loops over the geometries of a closed shape and searches the highest
        angle between the end geometry to the start geometry. The one with the 
        highest angle inbetween will be the new start point.        
        """           
            
        # Do only if more then 2 geometies of a closed shape
        if len(self.geos) < 2 and self.closed:
            return

        sharpest_ang=0.0
        max_index=0
        for i in range(len(self.geos)):
             end_point, end_ang = self.geos[i-1].get_start_end_points(0,1) 
             st_point,  st_ang  = self.geos[i].get_start_end_points(1,1)
             
             ang_diff=(st_ang-end_ang-pi)
             
             if ang_diff < -pi: 
                ang_diff += 2*pi
             if ang_diff > pi:
                ang_diff -=2*pi
                      
             logger.debug("st_point: %s; end_ang: %0.2f; st_ang: %0.2f; ang_diff: %0.2f" %(st_point, st_ang, end_ang, ang_diff))

             if sharpest_ang<abs(ang_diff):
                 sharpest_ang=abs(ang_diff)
                 sharpest_geo_nr=i             
             
        logger.debug("sharpest_ang: %0.2f " %(sharpest_ang))     
             
        # Overwrite the geometries in changed order.
        self.geos = Geos(self.geos[sharpest_geo_nr:] + self.geos[:sharpest_geo_nr])

        start = self.get_start_end_points(True)
        logger.debug(self.tr("New Start Point: %s" %start))


        # Update start move after reordering the shape
        if self.stmove is not None:
            self.stmove.updateShape()



    def reverse(self, geos=None):
        if not geos:
            geos = self.geos
            # switch direction if working with own geometry
            self.cw = not self.cw
        geos.reverse()
        for geo in geos:
            geo.reverse()

    def switch_cut_cor(self):
        """
        Switches the cutter direction between 41 and 42.

        G41 = Tool radius compensation left.
        G42 = Tool radius compensation right
        """
        if self.cut_cor == 41:
            self.cut_cor = 42
        elif self.cut_cor == 42:
            self.cut_cor = 41

    def append(self, geo):
        geo.make_abs_geo(self.parentEntity)
        self.geos.append(geo)

    def get_start_end_points_physical(self, start_point=None, angles=None, PPocket=False):
        """
        With multiple slices end point could be start point.
        e.g. useful for the optimal rout etc
        """
        
        if self.cw ==True:
            direction = -1;
        else:
            direction = 1;
            
        ### drill cut here
        
        #TODO: end point will change to zig-zag's end
        
        if start_point or self.closed:
            return self.get_start_end_points(start_point, angles)
        else:
            max_slice = max(self.axis3_slice_depth,
                            self.axis3_mill_depth -
                            self.axis3_start_mill_depth)
            if max_slice == 0:
                end_should_be_start = True
            else:
                end_should_be_start = (
                    self.axis3_start_mill_depth - self.axis3_mill_depth) // max_slice % 2 == 0
            if not end_should_be_start:
                return self.get_start_end_points(start_point, angles)
            else:
                start_stuff = self.get_start_end_points(True, angles)
                if angles is False:
                    end_stuff = start_stuff[0], -start_stuff[1]
                else:
                    end_stuff = start_stuff
                if start_point is None:
                    return start_stuff, end_stuff
                else:
                    return end_stuff

    def get_start_end_points(self, start_point=None, angles=None, PPocket=False):

        if self.cw ==True:
            direction = -1;
        else:
            direction = 1;
                  
        
        if start_point is None:
            return (self.geos.abs_el(0).get_start_end_points(True, angles),
                    self.geos.abs_el(-1).get_start_end_points(False, angles))
        elif start_point:
            return self.geos.abs_el(0).get_start_end_points(True, angles)
        else:
            return self.geos.abs_el(-1).get_start_end_points(False, angles)

    def make_path(self, drawHorLine, drawVerLine):

        for geo in self.geos.abs_iter():
            drawVerLine(self, geo.get_start_end_points(True))

            geo.make_path(self, drawHorLine)

        if not self.closed:
            drawVerLine(self, geo.get_start_end_points(False))

        self.calc_bounding_box()

    def calc_bounding_box(self):
        """
        Calculated the BoundingBox of the geometry and saves it into self.BB
        """
        self.BB = self.geos.abs_el(0).BB
        for geo in self.geos.abs_iter():
            self.BB = self.BB.joinBB(geo.BB)

    def make_shape_ccw(self):
        """
        This method is called after the shape has been generated before it gets
        plotted to change all shape direction to a CW shape.
        """

        if not(self.closed):
            return

        # Optimization for closed shapes
        # Start value for the first sum

        if self.isDirectionOfGeosCCW(self.geos):
            self.reverse()
            logger.debug(self.tr("Had to reverse the shape to be CW"))
        self.cw = True

    def isHit(self, xy, tol):
        if self.BB.Ps.x - tol <= xy.x <= self.BB.Pe.x + tol\
                and self.BB.Ps.y - tol <= xy.y <= self.BB.Pe.y + tol:
            for geo in self.geos.abs_iter():
                if geo.isHit(self, xy, tol):
                    return True
        return False

    def Write_GCode_for_geo(self, geo, PostPro):
        # Used to remove zero length geos. If not, arcs can become a full
        # circle
        
        if isinstance(geo, PocketMove):
            return geo.Write_GCode(PostPro)
        
        if (self.Drill==True):
            Ps=Point(geo.O.x,geo.O.y)
            hgeo=HoleGeo(Ps)
            logger.debug("Will Write HoleGeo")
            return hgeo.Write_GCode(PostPro)
        
        post_dec = PostPro.vars.Number_Format["post_decimals"]
        if isinstance(geo, HoleGeo) or\
           round(geo.Ps.x, post_dec) != round(geo.Pe.x, post_dec) or\
           round(geo.Ps.y, post_dec) != round(geo.Pe.y, post_dec) or\
           isinstance(geo, ArcGeo) and geo.length > 0.5 * 0.1 ** post_dec * pi:
            return geo.Write_GCode(PostPro)
        else:
            return ""

    def get_pass_depths(self, single_pass=False):
        """
        Returns the Z depths of all milling passes as they are written by
        Write_GCode(): the first pass at the initial mill depth followed by
        one pass per additional slice. The arithmetic mirrors the while loop
        in Write_GCode() exactly (same order of operations) so that the
        number and depth of the passes is always identical to the export.
        @param single_pass: True when the export is limited to a single pass
        (DXF output type or a drill without repeated drill moves).
        """
        max_slice = -abs(self.axis3_slice_depth)
        initial_mill_depth = self.axis3_start_mill_depth + max_slice
        if single_pass:
            initial_mill_depth = self.axis3_mill_depth

        depths = [initial_mill_depth]
        mom_depth = initial_mill_depth
        while mom_depth > self.axis3_mill_depth and max_slice < 0.0:
            mom_depth = mom_depth + max_slice
            if mom_depth < self.axis3_mill_depth:
                mom_depth = self.axis3_mill_depth
            depths.append(mom_depth)
        return depths

    def Write_GCode(self, PostPro):
        """
        This method returns the string to be exported for this shape, including
        the defined start and end move of the shape.
        @param PostPro: this is the Postprocessor class including the methods
        to export
        """
        if g.config.machine_type == 'drag_knife':
            return self.Write_GCode_Drag_Knife(PostPro)

        if isinstance(self.geos[0], HoleGeo):
            self.Drill            

        prv_cut_cor = self.cut_cor
        if ((self.cut_cor != 40 or self.Pocket) and
                not g.config.vars.Cutter_Compensation["done_by_machine"] and 
                not self.Drill):
            # Software compensation (G41/G42) or a pocket: the exported
            # geometry is the pre-computed toolpath held in stmove (the
            # compensated contour and/or the pocket fill), not the raw shape
            # contour. Without this a G40 pocket would export only the
            # contour and silently drop the whole pocket toolpath.
            self.cut_cor = 40
            new_geos = Geos(self.stmove.geos[1:])
        else:
            new_geos = self.geos

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

        # If the Output Format is DXF do not perform more then one cut or specially defined for Drill move..
        if ((PostPro.vars.General["output_type"] == 'dxf') or ((self.Drill) and PostPro.vars.General["repeat_drill_move"]==False)):
            #depth = abs(max_slice)
            initial_mill_depth=self.axis3_mill_depth

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
        # them, using the same Z height semantics as BreakGeo.Write_GCode().
        pass_depths = self.get_pass_depths(
            single_pass=(PostPro.vars.General["output_type"] == 'dxf' or
                         ((self.Drill) and
                          PostPro.vars.General["repeat_drill_move"] == False)))
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
            
            # This will position the cutter on the first geometry with or without cutter comp. G1 move.
            exstr += self.stmove.geos.abs_el(0).Write_GCode(PostPro)

            # Add string to be added before the shape will be cut.
            exstr += PostPro.write_pre_shape_cut()
            # Cutter radius compensation when G41 or G42 is on, AND cutter
            # compensation option is set to be done outside the piece
            if (self.cut_cor != 40 and PostPro.vars.General["cc_outside_the_piece"]):
                exstr += PostPro.set_cut_cor(self.cut_cor)
    
                exstr += PostPro.chg_feed_rate(f_g1_plane)
                exstr += self.stmove.geos.abs_el(1).Write_GCode(PostPro)
                exstr += self.stmove.geos.abs_el(2).Write_GCode(PostPro)
            
            exstr += PostPro.rap_pos_z(workpiece_top_Z + abs(safe_margin))  
            exstr += PostPro.chg_feed_rate(f_g1_depth)
            exstr += PostPro.lin_pol_z(mom_depth)
            exstr += PostPro.chg_feed_rate(f_g1_plane)
            

            # Cutter radius compensation when G41 or G42 is on, AND cutter
            # compensation option is set to be done inside the piece
            if (self.cut_cor != 40 and not PostPro.vars.General["cc_outside_the_piece"]):
                exstr += PostPro.set_cut_cor(self.cut_cor)
    
                exstr += self.stmove.geos.abs_el(1).Write_GCode(PostPro)
                exstr += self.stmove.geos.abs_el(2).Write_GCode(PostPro)
            
            for geo in pass_geos(1).abs_iter():
                if isinstance(geo, PocketMove):
                    geo.setZMove(f_g1_depth, f_g1_plane, workpiece_top_Z + abs(safe_margin), mom_depth, safe_retract_depth)
                    exstr += geo.Write_GCode(PostPro)
                else:
                    exstr += self.Write_GCode_for_geo(geo, PostPro)
                if (self.Drill==True):
                    logger.debug("Stopping after 1st geometry as it will be drilled.")
                    break
                
                        # Turning the cutter radius compensation
            if (self.cut_cor != 40 and PostPro.vars.General["cancel_cc_for_depth"]):
                exstr += PostPro.deactivate_cut_cor()
        
        # If its a drill
        else:
            # This will position the cutter on the first geometry with or without cutter comp. G1 move.
            exstr += self.stmove.geos.abs_el(0).Write_GCode(PostPro)

            # Add string to be added before the shape will be cut.
            exstr += PostPro.write_pre_shape_cut()
            
            #Posiioning is part of the Start Move                
            exstr += PostPro.rap_pos_z(workpiece_top_Z + abs(safe_margin))  
            exstr += PostPro.chg_feed_rate(f_g1_depth)
            exstr += PostPro.lin_pol_drill(mom_depth)
        


        # Numbers of loops
        snr = 0
        
        #logger.debug(size(depth))
        #logger.debug(depth)
        #logger.debug(max_slice)
        #logger.debug(mom_depth)
        # Loops for the number of cuts
        while mom_depth > depth and max_slice < 0.0:
            snr += 1
            mom_depth = mom_depth + max_slice
            if mom_depth < depth:
                mom_depth = depth
                #logger.debug(mom_depth)
                
            #If this is last slice, remove last element
            # (no need to return to start point)
            cur_geos = pass_geos(snr + 1,
                                 mom_depth == depth and self.Pocket == True)

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
                        exstr += geo.Write_GCode(PostPro)
                    else:
                        exstr += self.Write_GCode_for_geo(geo, PostPro)
                                
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

    def Write_GCode_Drag_Knife(self, PostPro):
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
        exstr += self.stmove.geos.abs_el(0).Write_GCode(PostPro)

        # Add string to be added before the shape will be cut.
        exstr += PostPro.write_pre_shape_cut()

        # Move into workpiece and start cutting into Z
        exstr += PostPro.rap_pos_z(
            workpiece_top_Z + abs(safe_margin))  # Compute the safe margin from the initial mill depth
        exstr += PostPro.chg_feed_rate(f_g1_depth)

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

        exstr += self.stmove.geos.abs_el(1).Write_GCode(PostPro)

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

            exstr += self.Write_GCode_for_geo(geo, PostPro)

        # Do the tool retraction
        exstr += PostPro.chg_feed_rate(f_g1_depth)
        exstr += PostPro.lin_pol_z(workpiece_top_Z + abs(safe_margin))
        exstr += PostPro.rap_pos_z(safe_retract_depth)

        # Add string to be added before the shape will be cut.
        exstr += PostPro.write_post_shape_cut()

        return exstr

    def join_colinear_lines(self):
        """
        This function is called to search for colinear connected lines an joins 
        them if there are any
        """
        # Do only if more then 2 geometies
        if len(self.geos) < 2:
            return

        new_geos = []
        for i in range(len(self.geos)):
            if len(new_geos) == 0:
                new_geos.append(self.geos[i])
                continue

            geo1 = new_geos[-1]
            geo2 = self.geos[i]

            if isinstance(geo1, LineGeo) and isinstance(geo2, LineGeo):
                # Remove first geometry and add result of joined geometries. Required
                # Cause the join will give back the last 2 geometries.
                new_geos.pop()
                new_geos += geo1.join_colinear_line(geo2)
            elif isinstance(geo1, ArcGeo) or isinstance(geo2, ArcGeo):
                new_geos.append(geo2)

            # If start end End Point are the same remove geometry
            if new_geos[-1].Ps == new_geos[-1].Pe:
                # Note that this can make new_geos absolutely empty!
                new_geos.pop()

        # For closed polylines check if the first and last items are colinear
        if self.closed and (len (new_geos) > 1):
            geo1 = new_geos[-1]
            geo2 = new_geos[0]
            if isinstance(geo1, LineGeo) and isinstance(geo2, LineGeo):
                joined_geos = geo1.join_colinear_line(geo2)

                # If they are joined replace first item by joined and remove
                # last one
                if len(joined_geos) == 1:
                    new_geos[0] = joined_geos[0]
                    new_geos.pop()

        self.geos = new_geos


class Geos(list):

    def __init__(self, *args):
        list.__init__(self, *args)


    def __repr__(self):
        res = "Geos ("
        sep = "\n"
        for i in range(len(self)):
            res += sep
            res += "[%i] %s" % (i, repr(self[i]))
            sep = ",\n"
        res += ")"
        return res


    def abs_iter(self):
        for geo in list.__iter__(self):
            yield geo.abs_geo if geo.abs_geo else geo

    def rel_iter(self):
        for geo in list.__iter__(self):
            yield geo

    def abs_el(self, element):
        return self[element].abs_geo if self[element].abs_geo else self[element]
