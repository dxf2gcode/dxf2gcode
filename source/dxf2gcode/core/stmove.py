# -*- coding: utf-8 -*-

############################################################################
#
#   Copyright (C) 2008-2015
#    Christian Kohlöffel
#    Vinzenz Schulz
#    Jean-Paul Schouwstra
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

from math import sin, cos, pi, sqrt
from copy import deepcopy
import traceback

#for dumps
from inspect import getmembers
from pprint import pprint

import dxf2gcode.globals.globals as g

from dxf2gcode.core.linegeo import LineGeo
from dxf2gcode.core.arcgeo import ArcGeo
from dxf2gcode.core.point import Point
from dxf2gcode.core.shape import Geos
from dxf2gcode.core.shape import Shape
from dxf2gcode.core.pocketmill import PocketMill
from dxf2gcode.core.pocketmove import PocketMove
from dxf2gcode.core.shapeoffset import *

from dxf2gcode.Qt import QtCore

import logging
logger = logging.getLogger('core.stmove')


class StMove(object):
    """
    This Function generates the StartMove for each shape. It
    also performs the Plotting and Export of this moves. It is linked
    to the shape of its parent
    """
    # only need default arguments here because of the change of usage with super in QGraphicsLineItem
    def __init__(self, shape=None):
        if shape is None:
            return

        self.shape = shape

        self.updateShape()

    def __repr__(self):
        return "StMove(shape %d start %s angle %s end %s)" % \
            (self.shape.nr, str(self.start), str(self.angle), str(self.end))

    def tr(self, string_to_translate):
        """
        Translate a string using the QCoreApplication translation framework
        @param: string_to_translate: a unicode string
        @return: the translated unicode string if it was possible to translate
        """
        return str(QtCore.QCoreApplication.translate("StMove",
                                                     string_to_translate))

    def append(self, geo):
        # we don't want to additional scale / rotate the stmove geo
        # so no geo.make_abs_geo(self.shape.parentEntity)
        geo.make_abs_geo()
        self.geos.append(geo)

    def updateShape(self):
        """
        Update start move after shape is changed.
        """
        self.start, self.angle = self.shape.get_start_end_points(True, True)
        self.end = self.start

        self.geos = Geos([])
        # Index where the pocket mill geometries start (set by
        # make_start_moves); everything before belongs to the G41/G42
        # compensation contour or the start moves. Used by the canvas to
        # render both with different line widths.
        self.pocket_geos_start = 0
        logging.debug("Updating the Start Move / Offset Geometry")
        self.make_start_moves()
        


    def make_start_moves(self):
        """
        This function called to create the start move. It will
        be generated based on the given values for start and angle.
        """
        self.geos = Geos([])
        # Signed distance of the pocket fill's reference contour from the
        # original contour (0 = original contour, +radius = offset outward,
        # -radius = offset inward). The pocket fill keeps its edge clearance
        # relative to this reference contour. 0.0 keeps the previous behaviour.
        self.pocket_fill_offset = 0.0
        # Geometry the pocket fill is derived from when the additional offset
        # (finishing allowance) shifts the milled contour. None means: the fill
        # works on the original contour (previous behaviour).
        self.pocket_wall_reference = None

        if g.config.machine_type == 'drag_knife':
            self.make_swivelknife_move()
            # All swivel knife geometries belong to the compensated toolpath
            self.pocket_geos_start = len(self.geos)
            return

        # Get the start rad. and the length of the line segment at begin.
        start_rad = self.shape.parentLayer.start_radius

        # Get tool radius based on tool diameter.
        tool_rad = self.shape.parentLayer.getToolRadius()

        # Calculate the starting point with and without compensation.
        start = self.start
        angle = self.angle

        ### drill cutted from here

        if self.shape.Drill == True:
            if isinstance(self.shape.geos[0], ArcGeo):
                start = self.shape.geos[0].abs_geo.O

            self.append(RapidPos(start))

            Ps_ein = start.get_arc_point(0,  tool_rad)

            # generate the start rad. and append it.
            circle = ArcGeo(Ps=Ps_ein, Pe=Ps_ein, O=start,
                               r=tool_rad, direction=1)

            self.append(circle)


        elif (not g.config.vars.Cutter_Compensation["done_by_machine"] and
                (self.shape.cut_cor != 40 or self.shape.Pocket)):
            # Software cutter compensation: the compensated contour is baked
            # into the exported geometry.
            #
            # For pocket milling the boundary pass offset is selected below
            # according to the configured pocket_compensation_mode. Non-pocket
            # shapes always keep the plain G41/G42 direction mapping.

            logging.debug("We have custom offset by tool")

            toolwidth = self.shape.parentLayer.getToolRadius()

            # Additional offset (finishing allowance) of this individual shape:
            # it is added to the cutter radius so that a roughing pass can leave
            # material which a following finishing pass removes. 0.0 keeps the
            # previous behaviour. A positive value shifts the compensated
            # toolpath away from the outline on the compensated side (outward
            # for outside contours, inward for inside contours/pockets), i.e.
            # it always leaves more material. Only the software cutter
            # compensation can apply it geometrically.
            extra_offset = getattr(self.shape, 'milling_offset', 0.0)
            comp_offset = toolwidth + extra_offset
            if comp_offset <= 0.0:
                # The additional offset cancels the cutter compensation, so no
                # valid compensated toolpath exists for this shape. Keep the
                # previous safe handling: warn and export nothing (Write_GCode
                # drops shapes whose stmove contains no geometry).
                logging.error(
                    self.tr("Shape %i: the additional offset (%.3f mm) cancels "
                            "the cutter compensation (tool diameter %.3f mm) - "
                            "the shape will NOT be milled!")
                    % (self.shape.nr, extra_offset,
                       self.shape.parentLayer.tool_diameter))
                self.pocket_geos_start = len(self.geos)
                return

            # How pocket milling is compensated is configurable:
            #  * always_inward      : the pocket is always cleared from the
            #                         inside (inward boundary pass); the
            #                         G40/G41/G42 selection has no effect on
            #                         the pocket (default, previous behaviour).
            #  * selected_direction : the selected direction decides the
            #                         boundary pass offset (G42/G41 = right/
            #                         left offset relative to the contour
            #                         direction; G40 = no cutter compensation,
            #                         the contour itself is the toolpath).
            pocket_mode = getattr(g.config.vars.Pocketing,
                                  "pocket_compensation_mode",
                                  "always_inward")
            forced_inward = (self.shape.Pocket and
                             pocket_mode == "always_inward")

            if forced_inward:
                offtype = "in"
            elif self.shape.cut_cor == 41 and self.shape.cw is True:
                offtype = "out"
            elif self.shape.cut_cor == 41 and self.shape.cw is False:
                offtype = "in"
            elif self.shape.cut_cor == 42 and self.shape.cw is False:
                offtype = "out"
            elif self.shape.cut_cor == 42 and self.shape.cw is True:
                offtype = "in"
            else:
                offtype = "out"
                Warning("should not be here")
            logger.debug("Shape.cw %s; shape.cut_cor %i; Offset in direction: %s" %(self.shape.cw, self.shape.cut_cor,offtype))

            if (self.shape.Pocket and not forced_inward and
                    self.shape.cut_cor == 40):
                # G40 = no cutter compensation: the contour itself is the tool
                # center path (no radius offset). The pocket fill is appended
                # afterwards by the pocket block below.
                self.append(RapidPos(start))
                self.geos += Geos(deepcopy(geo)
                                  for geo in self.shape.geos.abs_iter())
            else:
                offshape = offShapeClass(parent = self.shape, offset = comp_offset, offtype = offtype)

                if len(offshape.rawoff) == 0:
                    # P1: No offset geometry was produced. Distinguish the
                    # expected border case (the selected cutter diameter removed
                    # the whole contour) from genuine computation failures, so
                    # the user gets a meaningful hint. With an empty stmove,
                    # Write_GCode skips this shape.
                    status = getattr(offshape, "offset_status", None)
                    tool_dia = self.shape.parentLayer.tool_diameter
                    if status == "vanished":
                        # Reliable border case: nothing left to mill.
                        if self.shape.Pocket:
                            logging.warning(
                                self.tr("Shape %i: the cutter diameter (%.3f mm) removes "
                                        "the whole boundary - only the pocket will be "
                                        "milled!") % (self.shape.nr, tool_dia))
                        else:
                            logging.warning(
                                self.tr("Shape %i cannot be milled: the selected cutter "
                                        "diameter (%.3f mm) leaves no valid toolpath for "
                                        "this contour.") % (self.shape.nr, tool_dia))
                    elif status in ("walk_overflow", "no_intersection",
                                    "exception"):
                        # A real computation problem, not an expected border case.
                        logging.error(
                            self.tr("Cutter compensation failed for shape %i (%s) - the "
                                    "shape will NOT be milled!")
                            % (self.shape.nr, status))
                    else:
                        # Unknown cause - keep the previous safe handling.
                        if self.shape.Pocket:
                            logging.warning(
                                self.tr("Cutter compensation failed for shape %i - only "
                                        "the pocket will be milled, the boundary pass is "
                                        "skipped!") % self.shape.nr)
                        else:
                            logging.error(
                                self.tr("Cutter compensation failed for shape %i - the "
                                        "shape will NOT be milled!") % self.shape.nr)

                if len(offshape.rawoff) > 0:
                    # The rapid positioning must target the start of the FIRST
                    # milling loop: after a loop split the sequence is rotated,
                    # so loops[0][0] is not necessarily rawoff[0]. Positioning
                    # at rawoff[0] instead would leave an unmarked gap which
                    # the post processor would cut as a straight line.
                    if offshape.loops:
                        start, angle = offshape.loops[0][0].get_start_end_points(True, True)
                    else:
                        start, angle = offshape.rawoff[0].get_start_end_points(True, True)

                    self.append(RapidPos(start))

                    # P2: Mill each loop as its own path; the loops are connected
                    # with rapid moves (retract / move / plunge) like the pocket
                    # milling paths.
                    prev_end = None
                    for loop in offshape.loops:
                        if not loop:
                            continue
                        if prev_end is not None:
                            self.append(PocketMove(prev_end, loop[0].Ps))
                        self.geos += loop
                        prev_end = loop[-1].Pe

                    if (self.shape.Pocket and not forced_inward and
                            self.shape.cut_cor in (41, 42)):
                        # selected_direction: the pocket fill keeps its edge
                        # clearance relative to THIS compensated offset
                        # contour, so record how far it sits from the original
                        # contour (offtype "out" -> offset outward, +radius).
                        # Only the cutter radius is recorded here; the
                        # additional offset (finishing allowance) is applied to
                        # the fill stand-off in pocketmill so that it works the
                        # same way for every pocket mode.
                        self.pocket_fill_offset = (
                            -toolwidth if offtype == "in" else toolwidth)

                    if self.shape.Pocket and extra_offset:
                        # The additional offset (finishing allowance) shifts the
                        # contour the tool really mills, so the pocket grows (or
                        # shrinks) with it. Derive the pocket fill from that
                        # shifted contour ("wall" = compensated contour inset by
                        # the tool radius = original contour shifted by the extra
                        # offset to the compensated side) so the fill follows the
                        # additional offset.
                        wall_outside = ((offtype == "out") ==
                                        (extra_offset > 0.0))
                        wall = offShapeClass(
                            parent=self.shape, offset=abs(extra_offset),
                            offtype=("out" if wall_outside else "in"))
                        if wall.loops:
                            reference = Geos()
                            for loop in wall.loops:
                                reference += loop
                            self.pocket_wall_reference = reference

        elif self.shape.cut_cor == 40:
            # No cutter compensation: the shape contour itself is the tool
            # center path. (Pockets with G40 are handled by the software
            # compensation branch above so they are exported correctly.)
            self.append(RapidPos(start))

        # Cutting Compensation Left
        elif self.shape.cut_cor == 41:
            # Center of the Starting Radius.
            Oein = start.get_arc_point(angle + pi/2, start_rad + tool_rad)
            # Start Point of the Radius
            Ps_ein = Oein.get_arc_point(angle + pi, start_rad + tool_rad)
            # Start Point of the straight line segment at begin.
            Pg_ein = Ps_ein.get_arc_point(angle + pi/2, start_rad)

            # Get the dive point for the starting contour and append it.
            start_ein = Pg_ein.get_arc_point(angle, tool_rad)
            self.append(RapidPos(start_ein))

            # generate the Start Line and append it including the compensation.
            start_line = LineGeo(start_ein, Ps_ein)
            self.append(start_line)

            # generate the start rad. and append it.
            start_rad = ArcGeo(Ps=Ps_ein, Pe=start, O=Oein,
                               r=start_rad + tool_rad, direction=1)
            self.append(start_rad)

        # Cutting Compensation Right
        elif self.shape.cut_cor == 42:
            # Center of the Starting Radius.
            Oein = start.get_arc_point(angle - pi/2, start_rad + tool_rad)
            # Start Point of the Radius
            Ps_ein = Oein.get_arc_point(angle + pi, start_rad + tool_rad)
            # Start Point of the straight line segment at begin.
            Pg_ein = Ps_ein.get_arc_point(angle - pi/2, start_rad)

            # Get the dive point for the starting contour and append it.
            start_ein = Pg_ein.get_arc_point(angle, tool_rad)
            self.append(RapidPos(start_ein))

            # generate the Start Line and append it including the compensation.
            start_line = LineGeo(start_ein, Ps_ein)
            self.append(start_line)

            # generate the start rad. and append it.
            start_rad = ArcGeo(Ps=Ps_ein, Pe=start, O=Oein,
                               r=start_rad + tool_rad, direction=0)
            self.append(start_rad)
            
        # Remember where the pocket mill geometries start. Everything before
        # belongs to the G41/G42 compensation contour (or the start moves).
        # If the shape is no pocket this equals the total geo count.
        self.pocket_geos_start = len(self.geos)

        # Pocket Milling - draw toolpath
        if self.shape.Pocket == True:
            # PocketMill expects a current position (stmove.geos[-1].Pe).
            # With a failed/vanished cutter compensation nothing was
            # appended so far - anchor the pocket at the shape start point
            # instead of crashing with an IndexError.
            if len(self.geos) == 0:
                self.append(RapidPos(self.start))
            
            pocket = PocketMill(self)
            try:
                pocket.createLines()
            except Exception:
                # Safety net: an unexpected error in the pocket calculation
                # must not crash the application nor leave a half-built
                # toolpath behind. Drop everything the pocket appended after
                # the boundary pass so no broken path is exported.
                del self.geos[self.pocket_geos_start:]
                logging.error(
                    self.tr("Pocket milling failed for shape %i - the pocket is "
                            "skipped. This is a bug, please report it with the "
                            "offending DXF file.\n%s")
                    % (self.shape.nr, traceback.format_exc()))
            
    def make_swivelknife_move(self):
        """
        Set these variables for your tool and material
        @param offset: knife tip distance from tool centerline. The radius of the
        tool is used for this.
        """
        offset = self.shape.parentLayer.getToolRadius()
        drag_angle = self.shape.drag_angle

        startnorm = offset*Point(1, 0)  # TODO make knife direction a config setting
        prvend, prvnorm = Point(), Point()
        first = True

        for geo in self.shape.geos.abs_iter():
            if isinstance(geo, LineGeo):
                geo_b = deepcopy(geo)
                if first:
                    first = False
                    prvend = geo_b.Ps + startnorm
                    prvnorm = startnorm
                norm = offset * (geo_b.Pe - geo_b.Ps).unit_vector()
                geo_b.Ps += norm
                geo_b.Pe += norm
                if not prvnorm == norm:
                    direction = prvnorm.to3D().cross_product(norm.to3D()).z
                    swivel = ArcGeo(Ps=prvend, Pe=geo_b.Ps, r=offset, direction=direction)
                    swivel.drag = drag_angle < abs(swivel.ext)
                    logger.debug(swivel)
                    self.append(swivel)
                logger.debug(geo_b)
                self.append(geo_b)

                prvend = geo_b.Pe
                prvnorm = norm
            elif isinstance(geo, ArcGeo):
                geo_b = deepcopy(geo)
                if first:
                    first = False
                    prvend = geo_b.Ps + startnorm
                    prvnorm = startnorm
                if geo_b.ext > 0.0:
                    norma = offset*Point(cos(geo_b.s_ang+pi/2), sin(geo_b.s_ang+pi/2))
                    norme = Point(cos(geo_b.e_ang+pi/2), sin(geo_b.e_ang+pi/2))
                else:
                    norma = offset*Point(cos(geo_b.s_ang-pi/2), sin(geo_b.s_ang-pi/2))
                    norme = Point(cos(geo_b.e_ang-pi/2), sin(geo_b.e_ang-pi/2))
                geo_b.Ps += norma
                if norme.x > 0:
                    geo_b.Pe = Point(geo_b.Pe.x+offset/(sqrt(1+(norme.y/norme.x)**2)),
                                     geo_b.Pe.y+(offset*norme.y/norme.x)/(sqrt(1+(norme.y/norme.x)**2)))
                elif norme.x == 0:
                    geo_b.Pe = Point(geo_b.Pe.x,
                                     geo_b.Pe.y)
                else:
                    geo_b.Pe = Point(geo_b.Pe.x-offset/(sqrt(1+(norme.y/norme.x)**2)),
                                     geo_b.Pe.y-(offset*norme.y/norme.x)/(sqrt(1+(norme.y/norme.x)**2)))
                if prvnorm != norma:
                    direction = prvnorm.to3D().cross_product(norma.to3D()).z
                    swivel = ArcGeo(Ps=prvend, Pe=geo_b.Ps, r=offset, direction=direction)
                    swivel.drag = drag_angle < abs(swivel.ext)
                    logger.debug(swivel)
                    self.append(swivel)
                prvend = geo_b.Pe
                prvnorm = offset*norme
                if -pi < geo_b.ext < pi:
                    swivel = ArcGeo(Ps=geo_b.Ps, Pe=geo_b.Pe, r=sqrt(geo_b.r ** 2 + offset ** 2), direction=geo_b.ext)
                    logger.debug(swivel)
                    self.append(swivel)

                else:
                    geo_b = ArcGeo(Ps=geo_b.Ps, Pe=geo_b.Pe, r=sqrt(geo_b.r**2+offset**2), direction=-geo_b.ext)
                    geo_b.ext = -geo_b.ext
                    logger.debug(geo_b)
                    self.append(geo_b)
            # TODO support different geos, or disable them in the GUI
            # else:
            #     self.append(copy(geo))
        if not prvnorm == startnorm:
            direction = prvnorm.to3D().cross_product(startnorm.to3D()).z
            swivel = ArcGeo(Ps=prvend, Pe=prvend - prvnorm + startnorm, r=offset, direction=direction)
            swivel.drag = drag_angle < abs(swivel.ext)
            logger.debug(swivel)
            self.append(swivel)

        self.geos.insert(0, RapidPos(self.geos.abs_el(0).Ps))
        self.geos[0].make_abs_geo()


    def make_path(self, drawHorLine, drawVerLine):
        for geo in self.geos.abs_iter():
            drawVerLine(self.shape, geo.get_start_end_points(True))
            geo.make_path(self.shape, drawHorLine)
        if len(self.geos):
            drawVerLine(self.shape, geo.get_start_end_points(False))


class RapidPos(Point):
    def __init__(self, point):
        Point.__init__(self, point.x, point.y)
        self.abs_geo = None

    def get_start_end_points(self, start_point, angles=None):
        if angles is None:
            return self
        elif angles:
            return self, 0
        else:
            return self, Point(0, -1) if start_point else Point(0, -1)

    def make_abs_geo(self, parent=None):
        """
        Generates the absolute geometry based on itself and the parent. This
        is done for rotating and scaling purposes
        """
        self.abs_geo = RapidPos(self.rot_sca_abs(parent=parent))

    def make_path(self, caller, drawHorLine):
        pass

    def Write_GCode(self, PostPro):
        """
        Writes the GCODE for a rapid position.
        @param PostPro: The PostProcessor instance to be used
        @return: Returns the string to be written to a file.
        """
        return PostPro.rap_pos_xy(self)
