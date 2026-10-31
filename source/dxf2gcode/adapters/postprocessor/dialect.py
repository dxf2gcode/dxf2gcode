# -*- coding: utf-8 -*-

############################################################################
#
#   Copyright (C) 2008-2016
#    Christian Kohlöffel
#    Vinzenz Schulz
#    Jean-Paul Schouwstra
#    Xavier Izard
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

"""Profile-driven formatting and modal output state, without planning or Qt."""

from math import degrees

from dxf2gcode.domain.geometry.point import Point


class ProfileDialect:
    """Format prepared actions using explicit profile and coordinate settings.

    The caller owns project traversal and planning. This class owns only
    output words, modal feed/position values and profile template expansion.
    """

    def __init__(self, profile, start_xy=(0.0, 0.0), start_z=0.0,
                 diameter_factor=1):
        self.vars = profile
        self.diameter_factor = diameter_factor
        self.feed = 0
        self.speed = 0
        self.tool_nr = 1
        self.comment = ""
        self.abs_export = profile.General["abs_export"]
        self.Pe = Point(*start_xy)
        self.Ps = Point(*start_xy)
        self.lPe = Point(*start_xy)
        self.IJ = Point()
        self.O = Point()
        self.r = 0.0
        self.s_ang = 0.0
        self.e_ang = 0.0
        self.ext = 0.0
        self.ze = start_z
        self.lz = start_z
        self.zs = start_z

        self.keyvars = {"%feed": 'self.iprint(self.feed)',
                        "%speed": 'self.iprint(self.speed)',
                        "%tool_nr": 'self.iprint(self.tool_nr)',
                        "%nl": 'self.nlprint()',
                        "%XE": 'self.fnprint(self.Pe.x)',
                        "%-XE": 'self.fnprint(-self.Pe.x)',
                        "%XS": 'self.fnprint(self.Ps.x)',
                        "%-XS": 'self.fnprint(-self.Ps.x)',
                        "%YE": 'self.fnprint(self.Pe.y*fac)',
                        "%-YE": 'self.fnprint(-self.Pe.y*fac)',
                        "%YS": 'self.fnprint(self.Ps.y*fac)',
                        "%-YS": 'self.fnprint(-self.Ps.y*fac)',
                        "%ZS": "self.fnprint(self.zs)",
                        "%-ZS": "self.fnprint(-self.zs)",
                        "%ZE": 'self.fnprint(self.ze)',
                        "%-ZE": 'self.fnprint(-self.ze)',
                        "%I": 'self.fnprint(self.IJ.x)',
                        "%-I": 'self.fnprint(-self.IJ.x)',
                        "%J": 'self.fnprint(self.IJ.y*fac)',
                        "%-J": 'self.fnprint(-self.IJ.y*fac)',
                        "%XO": 'self.fnprint(self.O.x)',
                        "%-XO": 'self.fnprint(-self.O.x)',
                        "%YO": 'self.fnprint(self.O.y*fac)',
                        "%-YO": 'self.fnprint(-self.O.y*fac)',
                        "%R": 'self.fnprint(self.r)',
                        "%AngS": 'self.fnprint(degrees(self.s_ang))',
                        "%-AngS": 'self.fnprint(degrees(-self.s_ang))',
                        "%AngE": 'self.fnprint(degrees(self.e_ang))',
                        "%-AngE": 'self.fnprint(degrees(-self.e_ang))',
                        "%ext": 'self.fnprint(degrees(self.ext))',
                        "%-ext": 'self.fnprint(degrees(-self.ext))',
                        "%comment": 'self.sprint(self.comment)'}

        for c_name in self.vars.Custom_GCode:
            self.keyvars.update({c_name: 'self.cgcprint('"'%s'"')' %c_name})

    def write_gcode_en(self):
        """
        Return the text to be added at the end of the exported file.
        @return: The Function returns the string to be added.
        """
        return self.make_print_str(self.vars.General["code_end"])

    def make_line_numbers(self, exstr):
        """
        This Method adds Line Numbers to the existing exstr when required for export.
        @param exstr: This is the string which shall be exported where the line
        numbers are added.
        @return: It returns the string with line numbers added to it.
        """
        use_line_nrs = self.vars.Line_Numbers["use_line_nrs"]
        line_nrs_begin = self.vars.Line_Numbers["line_nrs_begin"]
        line_nrs_step = self.vars.Line_Numbers["line_nrs_step"]

        line_format = 'N%i '
        if use_line_nrs:
            nr = 0
            line_nr = line_nrs_begin
            exstr = ((line_format + '%s') % (line_nr, exstr))
            nr = exstr.find('\n', nr)
            while not nr == -1:
                line_nr += line_nrs_step
                exstr = (('%s' + line_format + '%s') % (exstr[0:nr + 1],
                                                        line_nr,
                                                        exstr[nr + 1:len(exstr)]))

                nr = exstr.find('\n', nr + len(line_format % line_nr) + 2)

        return exstr

    def make_windows_line_endings(self, exstr):
        if self.vars.Number_Format["win_line_endings"]:
            return exstr.replace('\n', '\r\n')

        return exstr

    def chg_tool(self, tool_nr, speed):
        """
        This Method is called to change the tool.  It can change the tool or
        change the tool speed
        @param tool_nr: The tool_nr of the new tool
        @param speed: The speed for the tool
        """
        self.tool_nr = tool_nr
        self.speed = speed
        return self.make_print_str(self.vars.Program["tool_change"])

    def chg_feed_rate(self, feed):
        """
        This Method is called to change the feedrate
        @param feed: New feedrate
        @return: Returns the string which shall be added.
        """
        if self.feed != feed:
            self.feed = feed
            return self.make_print_str(self.vars.Program["feed_change"])
        return ""

    def set_cut_cor(self, cut_cor):
        """
        This function is called if Cutter Correction should be enabled.
        @param cut_cor = The new value of the cutter correction (41/42)
        """
        self.cut_cor = cut_cor
        if cut_cor == 41:
            return self.make_print_str(self.vars.Program["cutter_comp_left"])
        elif cut_cor == 42:
            return self.make_print_str(self.vars.Program["cutter_comp_right"])

    def deactivate_cut_cor(self):
        """
        This function is called if Cutter Correction should be disabled.
        """
        return self.make_print_str(self.vars.Program["cutter_comp_off"])

    def lin_pol_arc(self, dir, Ps, Pe, s_ang, e_ang, R, O, IJ, ext):
        """
        This function is called if an arc shall be cut.
        @param dir: The direction of the arc to cut, can be cw or ccw
        @param Ps: The Start Point of the the Arc
        @param Pe: The End Point of the Arc
        @param s_ang: The angle at which the Startpoint Starts
        @param e_ang: The angle at which the Endpoint Ends
        @param R: The Radius of the Arc
        @param O: The Center (Origin) of the Arc
        @param IJ: The distance from Center to Start Point.
        """
        self.O = O
        self.IJ = IJ

        self.s_ang = s_ang
        self.e_ang = e_ang

        self.Ps = Ps
        self.r = R

        self.ext = ext

        if not self.abs_export:
            self.Pe = Pe - self.lPe
            self.lPe = Pe
        else:
            self.Pe = Pe

        if dir == 'cw':
            return self.make_print_str(self.vars.Program["arc_int_cw"])
        else:
            return self.make_print_str(self.vars.Program["arc_int_ccw"])

    def rap_pos_z(self, z_pos):
        """
        Code to add if the machine is rapidly commanded to a new
        3rd Axis Position.
        @param z_pos: the value at which shall be positioned
        @return: Returns the string which shall be added.
        """
        #Store the last Z value as the start value
        self.zs=self.ze

        if not self.abs_export:
            self.ze = z_pos - self.lz
            self.lz = z_pos
        else:
            self.ze = z_pos

        return self.make_print_str(self.vars.Program["rap_pos_depth"])

    def rap_pos_xy(self, Pe):
        """
        Code to add if the machine is rapidly commanded to a new
        XY Plane Position.
        @param Pe: the value at which machine shall be positioned
        @return: Returns the string which shall be added.
        """
        if not self.abs_export:
            self.Pe = Pe - self.lPe
            self.lPe = Pe
        else:
            self.Pe = Pe

        return self.make_print_str(self.vars.Program["rap_pos_plane"])

    def lin_pol_z(self, z_pos):
        """
        Code to add if the machine is commanded to a new
        3rd Axis Position.
        @param z_pos: the value at which shall be positioned
        @return: Returns the string which shall be added.
        """
        #Store the last Z value as the start value
        self.zs=self.ze

        if not self.abs_export:
            self.ze = z_pos - self.lz
            self.lz = z_pos
        else:
            self.ze = z_pos

        return self.make_print_str(self.vars.Program["lin_mov_depth"])

    def lin_pol_drill(self, z_pos):
        """
        Code to add if the machine is commanded to drill a HoleGeo
        @param z_pos: the value at which shall be positioned
        @return: Returns the string which shall be added.
        """

        #Store the last Z value as the start value
        self.zs=self.ze

        if not self.abs_export:
            self.ze = z_pos - self.lz
            self.lz = z_pos
        else:
            self.ze = z_pos

        return self.make_print_str(self.vars.Program["lin_mov_drill"])

    def lin_ret_drill(self, z_pos):
        """
        Code to add if the machine is commanded to drill a HoleGeo
        @param z_pos: the value at which shall be positioned
        @return: Returns the string which shall be added.
        """

        #Store the last Z value as the start value
        self.zs=self.ze

        if not self.abs_export:
            self.ze = z_pos - self.lz
            self.lz = z_pos
        else:
            self.ze = z_pos

        return self.make_print_str(self.vars.Program["lin_ret_drill"])


    def lin_pol_xy(self, Ps, Pe):
        """
        Code to add if the machine is rapidly commanded to a new
        XY Plane Position.
        @param Pe: the value at which shall be positioned
        @return: Returns the string which shall be added.
        """
        self.Ps = Ps
        if not self.abs_export:
            self.Pe = Pe - self.lPe
            self.lPe = Pe
        else:
            self.Pe = Pe

        return self.make_print_str(self.vars.Program["lin_mov_plane"])

    def write_pre_shape_cut(self):
        """
        Return the text to add before a shape.
        @return: Returns the string to be added.
        """
        return self.make_print_str(self.vars.Program["pre_shape_cut"])

    def write_post_shape_cut(self):
        """
        Return the text to add after (post) a shape.
        @return: Returns the string to be added.
        """
        return self.make_print_str(self.vars.Program["post_shape_cut"])

    def commentprint(self, comment):
        """
        This function is called to print a comment.
        @return: Returns the comment
        """
        self.comment = comment
        return self.make_print_str(self.vars.Program["comment"])

    def make_print_str(self, keystr):
        """
        This is the main function which converts the Keyvalues given in the
        Postprocessor Configuration into the values.
        @param keystr: String in which all keywords are to be
        replaced by the variables etc.
        @return: Returns the string with replaced keyvars (e.g. %Z is replaced
        by the real Z value in the defined Number Format.
        """
        fac = self.diameter_factor

        exstr = keystr
        for key, value in self.keyvars.items():
            exstr = exstr.replace(key, eval(value))
        return exstr

    # Function which returns the given value as a formatted integer
    def iprint(self, integer):
        """
        This method returns an integer formatted as a string
        @param integer: The integer value to convert to a string
        @return: The integer formatted as a string.
        """
        return '%i' % integer

    def sprint(self, string):
        """
        This method is called to return a string formatted as a string
        @param string: The string values which shall be returned as a string
        @return: The string formatted as a string.
        """
        return '%s' % string

    def nlprint(self):
        """
        This function is used to generate a new line.
        @return: Returns the character set required to get a new line
        """
        return '\n'

    def cgcprint(self, cgcnr):
        """
        This method is called to retrun a string of a custom G-Code which was added to the post-
        processor configuration.
        @param cgcnr: The name of the called custom g-code line
        @return: The value of the line.
        """
        c_code=self.vars.Custom_GCode[cgcnr]['gcode']
        return c_code

    def fnprint(self, number):
        """
        This function returns the given real values in the defined format. The
        format which shall be returned is defined in the postprocessor file.
        @param number: The number which shall be returned in a formatted string
        @return: The formatted string of the number.
        """
        pre_dec = self.vars.Number_Format["pre_decimals"]
        post_dec = self.vars.Number_Format["post_decimals"]
        dec_sep = self.vars.Number_Format["decimal_separator"]
        pre_dec_z_pad = self.vars.Number_Format["pre_decimal_zero_padding"]
        post_dec_z_pad = self.vars.Number_Format["post_decimal_zero_padding"]
        signed_val = self.vars.Number_Format["signed_values"]

        exstr = ''

        # + or - sign if required. Also used for Leading Zeros
        if signed_val and pre_dec_z_pad:
            numstr = ('%+0' + str(pre_dec + post_dec + 1) +
                      '.' + str(post_dec) + 'f') % number
        elif signed_val == 0 and pre_dec_z_pad:
            numstr = ('%0' + str(pre_dec + post_dec + 1) +
                      '.' + str(post_dec) + 'f') % number
        elif signed_val and pre_dec_z_pad == 0:
            numstr = ('%+' + str(pre_dec + post_dec + 1) +
                      '.' + str(post_dec) + 'f') % number
        elif signed_val == 0 and pre_dec_z_pad == 0:
            numstr = ('%' + str(pre_dec + post_dec + 1) +
                      '.' + str(post_dec) + 'f') % number

        # Gives the required decimal format.
        exstr += numstr[0:-(post_dec + 1)]

        exstr_end = dec_sep
        exstr_end += numstr[-post_dec:]

        # Add's Zero's to the end if required
        if not post_dec_z_pad:
            while len(exstr_end) > 0 and (exstr_end[-1] == '0' or exstr_end[-1] == dec_sep):
                exstr_end = exstr_end[0:-1]
        return exstr + exstr_end
