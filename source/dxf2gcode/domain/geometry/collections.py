"""Geometry collections and contour operations, independent of project defaults."""

import logging
from dxf2gcode.domain.geometry.linegeo import LineGeo
from dxf2gcode.domain.geometry.arcgeo import ArcGeo
logger = logging.getLogger(__name__)

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


class ContourGeometry:
    def __init__(self, nr=-1, closed=True, geos=()):
        self.nr, self.closed, self.cw = nr, closed, True
        self.geos = Geos(geos)

    @staticmethod
    def tr(text):
        return text

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


    def reverse(self, geos=None):
        if not geos:
            geos = self.geos
            # switch direction if working with own geometry
            self.cw = not self.cw
        geos.reverse()
        for geo in geos:
            geo.reverse()


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



    def join_colinear_lines(self):
        """
        This function is called to search for colinear connected lines an joins
        them if there are any

        The first and the last geometry of a closed polyline are not joined
        (they are connected at the closing point of the contour): the joined
        geometry would start at the start point of the last geometry, so the
        start point of the polyline would move to the end of the contour. The
        start point of a shape is the position of the lead in (and of the lead
        out, the contour is closed), so it must stay where the user set it.
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

        # For closed polylines the first and the last item may be colinear
        # too (they are connected at the closing point of the contour). They
        # are NOT joined here: the joined geometry would start at the start
        # point of the last geometry, so the start point of the closed
        # polyline would move to the end of the contour. The start point of a
        # shape is the position of the lead in (and of the lead out, the
        # contour is closed), so it must stay where the user set it.
        #
        # This is not an issue for the offset algorithm: the colinear vertex
        # is neither a convex nor a reflex point, it is simply skipped
        # (see make_segment_types).
        #
        # The case occurs with the "split line segments" option, where the
        # contour is cut in the middle of a line: the first and the last
        # geometry of the contour are then the two halves of that line and
        # therefore colinear.

        self.geos = new_geos
