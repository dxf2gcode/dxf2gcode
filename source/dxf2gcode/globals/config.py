# -*- coding: utf-8 -*-

############################################################################
#
#   Copyright (C) 2009-2021
#    Christian Kohlöffel
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

from __future__ import absolute_import

import os
import sys
import pprint
import logging
import re

from collections import OrderedDict
from configobj import ConfigObj, flatten_errors
from validate import Validator
import dxf2gcode.globals.globals as g
from dxf2gcode.globals.d2gexceptions import *
from dxf2gcode.gui.configwindow import *

import dxf2gcode.globals.constants as c
#TODO: check if can be removed: from dns.rdataclass import NONE

from dxf2gcode.Qt import QtCore


logger = logging.getLogger("Core.Config")

SUPPORTED_CONFIGS = [9.11, 9.12, 9.13, 9.14]
CONFIG_VERSION = SUPPORTED_CONFIGS[-1]
"""
version tag - increment this each time you edit CONFIG_SPEC

compared to version number in config file so
old versions are recognized and skipped"
"""

# Paths change whether platform is Linux or Windows
if "linux" in sys.platform.lower() or "unix" in sys.platform.lower():
    #Declare here the path that are specific to Linux
    IMPORT_DIR = "~/Documents"
    OUTPUT_DIR = "~/Documents"
    PROJECT_DIR= "~/Documents"
    PDFTOPS_CMD = "/usr/bin/pdftops"
    PSTOEDIT_CMD = "/usr/bin/pstoedit"
else:
    #Declare here the path that are specific to Windows
    IMPORT_DIR = "D:/Eclipse_Workspace/DXF2GCODE/trunk/dxf"
    OUTPUT_DIR = "D:"
    PROJECT_DIR= "D:"
    # Xpdf Tools from http://www.xpdfreader.com/download.html
    PDFTOPS_CMD = "C:/xpdf-tools-win-4.00/bin64/pdftops.exe"
    # pstoedit from https://sourceforge.net/projects/pstoedit/
    # and https://sourceforge.net/projects/ghostscript/ dependency
    # if gs in not on the PATH it might be necessary to add -gs option
    # to psedit in Option->Configuration->Software config->pstoedit
    # e.g.  -gs, C:/Program Files (x86)/gs/gs9.09/bin/gswin32c.exe
    PSTOEDIT_CMD = "C:/Program Files/pstoedit/pstoedit.exe"

"""
HOWTO declare a new variable in the config file:
1) Choose the appropriate section and add the variable in the CONFIG_SPEC string below
(Note: the CONFIG_SPEC is used to set and check the configfile "config.cfg")

2) Set it's default value, the min/max values (if applicable) and a comment above the variable's name
(Important note: the min/max values and the comment are directly used in the configuration window, so carefully set them!)
Example of correct declaration:
    [MySection]
    # Drag angle is used to blah blah blah ...
    drag_angle = float(min = 0, max = 360, default = 20)

3) If you want the setting to appear in the configuration window, fill the cfg_widget_def variable, using the _same_ names as in the CONFIG_SPEC
Example of declaration correlated to the above one:
    'MySection':
    {
        'drag_angle': CfgDoubleSpinBox('Drag angle (in degrees):'),
    }
(Note: the list of available types for the configuration window can be found in the "configwindow.py" file)
"""
"""
ATTENTION:
_Don't_ split the long comments lines in CONFIG_SPEC!
The comments line are used as "QWhatsThis" in the config window.
Any new line in the CONFIG_SPEC is reproduced in the QWhatsThis (intented behaviour to allow creating paragraphs)
ATTENTION
"""
CONFIG_SPEC = str('''
#  Section and variable names must be valid Python identifiers
#      do not use whitespace in names

# do not edit the following section name:
    [Version]
    # do not edit the following value:
    config_version = float(default = "''' + str(CONFIG_VERSION) + '''")

    [Paths]
    # By default look for DXF files in this directory.
    import_dir = string(default = "''' + IMPORT_DIR + '''")

    # Export generated gcode by default to this directory.
    output_dir = string(default = "''' + OUTPUT_DIR + '''")
    
    # Save project files by default to this directory.
    project_dir = string(default = "''' + PROJECT_DIR + '''")
    
    # Automatic save last path to config file. Therefore open with last path
    autosave_path =  boolean(default = True)

    [Filters]
    # pstoedit is an external tool to convert PDF files to PS (postscript) files, which can be further processed by pstoedit tool.
    pdftops_cmd = string(default = "''' + PDFTOPS_CMD + '''")
    pdftops_opt = list(default = list())

    # pstoedit is an external tool to import *.ps (postscript) files and convert them to DXF, in order to import them in dxf2gcode.
    pstoedit_cmd = string(default = "''' + PSTOEDIT_CMD + '''")
    pstoedit_opt = list(default = list('-dt', '-f', 'dxf:-mm'))

    [Axis_letters]
    ax1_letter = string(min = 1, default = "X")
    ax2_letter = string(min = 1, default = "Y")
    ax3_letter = string(min = 1, default = "Z")

    [Plane_Coordinates]
    axis1_start_end = float(default = 0)
    axis2_start_end = float(default = 0)
    std_scale = float(default = 1.0)
 
    [Depth_Coordinates]
    # Third axis' coordinate at which it can do rapid move.
    axis3_retract = float(default = 15.0)
    # Third axis' margin for which it needs to do a slow move.
    axis3_safe_margin = float(default = 3.0)
    # The top third axis' coordinate of the workpiece.
    axis3_start_mill_depth = float(default = 0.0)
    # Relative depth for each cut (third axis' coordinate will be decreased by this value at each step).
    axis3_slice_depth = float(default = -1.5)
    # Relative final third axis' depth.
    axis3_mill_depth = float(default = -3.0)

    [Feed_Rates]
    f_g1_plane = float(default = 400)
    f_g1_depth = float(default = 150)
    
    [General]
    # Enable 3D representation of the piece (requires PyQt5 and OpenGL)
    mode3d = boolean(default = False)
    # Write output to stdout (console), instead of a file. May be used to interface directly with Linux CNC, for example.
    write_to_stdout = boolean(default = False)
    # When enabled, the shapes that are disabled are still shown on the graphic view.
    show_disabled_paths = boolean(default = True)
    # When enabled, export path is live updated on the graphic view.
    live_update_export_route = boolean(default = False)
    # When enabled, a scale bar is drawn in the bottom right corner of the canvas. It shows the physical size of the imported geometry.
    show_scale_bar = boolean(default = False)
    # Divide the lines in 2 parts, in order to start the cutting in the middle of a line (usefull for cutter compensation)
    split_line_segments = boolean(default = False)
    # Automatically enable cutter compensation for all the shapes (G41 & G42)
    automatic_cutter_compensation = boolean(default = False)
    # Machine types supported: milling; lathe; drag_knife
    machine_type = option('milling', 'lathe', 'drag_knife', default = 'milling')
    # The unit used for all values in this file
    tool_units = option('mm', 'in', default = 'mm')

    [Cutter_Compensation]
    # If not checked, DXF2GCODE will create a virtual path for G41 and G42 command. And output will be set to G40; i.e. it will create the path that normally your machine would create with it's cutter compensation.
    done_by_machine = boolean(default = True)


    [Pocketing]
    # Pocket milling keeps the cutter center at (cutter radius + edge clearance)
    # away from the contour, so the cutting edge stops this far from the
    # unmachined contour. This is the "Pocketing edge clearance" and is given
    # here as a percentage of the cutter diameter.
    # - 0   : the cutting edge just touches the contour (no material left).
    # - The value is applied for every compensation direction (G40/G41/G42)
    #   and to inner and outer contour features alike; the cutter radius is
    #   only counted once.
    # The default reproduces the historical behaviour (center stand-off of
    # cutter radius / 0.7 for G42 pocketing).
    pocket_edge_clearance = float(min = 0, max = 100, default = 21.4286)

    # How the cutter compensation is applied while pocket milling a closed
    # contour:
    # - always_inward     : the pocket is always cleared from the inside with
    #                       an inward boundary pass; the G40/G41/G42 selection
    #                       does not change the pocket geometry (default,
    #                       keeps the previous behaviour).
    # - selected_direction: the selected G40/G41/G42 direction determines the
    #                       offset geometry of the boundary pass (G42/G41 give
    #                       the right/left offset relative to the contour
    #                       direction, G40 uses the contour without any cutter
    #                       radius compensation).
    pocket_compensation_mode = option('always_inward', 'selected_direction', default = 'always_inward')


    [Drag_Knife_Options]
    # drag_angle: if angle of movement exceeds this angle (in degrees), the tool retracts to dragDepth (The dragDepth is given by axis3_slice_depth parameter).
    # This parameter depends on the knife that you are using. A bigger knife cannot make small corners like a smaller knife. You will simply break your knife or destroy your working piece. Now, if the angle your knife has to make is bigger than this angle it will move to a different depth (a less deep position) such that the knife will experience less resistance but still has some (otherwise it will not change its angle at all, whence DRAG knife).
    drag_angle = float(min = 0, max = 360, default = 20)

    [Route_Optimisation]
    # If enabled, it will by default check the TSP for all the shapes in the treeview.
    # If disabled and no shape is checked for TSP optimisation in the listbox, the export order will be as defined in the listbox.
    default_TSP = boolean(default = False)

    # Path optimizer behaviour:
    # - CONSTRAIN_ORDER_ONLY: fixed Shapes and optimized Shapes can be mixed. Only order of fixed shapes is kept
    # - CONSTRAIN_PLACE_AFTER: optimized Shapes are always placed after any fixed Shape
    TSP_shape_order = option('CONSTRAIN_ORDER_ONLY', 'CONSTRAIN_PLACE_AFTER', default = 'CONSTRAIN_ORDER_ONLY')
    # This is a value of how much it should deviate the order with each iteration. The higher the value the more you allow alterations.
    mutation_rate = float(min = 0, max = 1, default = 0.95)
    # Number of people the population has for path optimization (values higher than 200 can make everything slow).
    max_population = integer(min = 0, max = 10000, default = 20)
    # Maximum number of iterations that will be done. This is internally also calculated, based on the number of shapes to optimize.
    # Values higher than 10000 can take really long to solve the TSP and are not recommended.
    max_iterations = integer(min = 1, max = 1000000, default = 300)
    # Different methods to initialize the population for the TSP optimizer.
    # - Ordered will start with the defined one in the listbox
    # - Random just random
    # - Heuristic will search the nearest neighbors and starts with the resulting order.
    begin_art = option('ordered', 'random', 'heuristic', default = 'heuristic')

    [Import_Parameters]
    # Tolerance at which similar points will be interpreted as similar
    point_tolerance = float(min = 0, max = 1, default = 0.001)
    # Types of check performed during spline conversion:
    # 1: Checking for Nurbs degree (polygon degree) and similar knots consistence
    # 2: Checking for Nurbs degree (polygon degree) and similar control points
    # 3: Performes check 1 and check 2
    spline_check = integer(min = 1, max = 3, default = 3)
    # This is the tolerance which is used to fit the converted lines and arc segments to the converted NURBS.
    fitting_tolerance = float(min = 0, max = 1, default = 0.001)
    # If checked, the elements (shape, ...) which are part of a block will be inserted on the layer that belongs to the block (even though the elements might be defined on a different layers)
    insert_at_block_layer = boolean(default = False)

    # These settings are intented to be used in the DXF file:
    # - By using MILL: as a prefix to your layer name, you can define milling parameters by using one of the following identifiers.
    # - Example of a layer name: MILL: 1 Md: 2 Sd: 2 FeedXY: 400 FeedZ: 200
    #   (This will cut shapes on the layer 2 mm deep (in one pass, since Sd == Md) using 400 mm / minute speed for X/Y movement and 200 mm / minute for Z movement)
    [Layer_Options]
    # To be used in the DXF layer name. See DXF2GCODE' wiki for more information.
    id_float_separator = string(default = ":")

    # To be used in the DXF layer name. See DXF2GCODE' wiki for more information.
    mill_depth_identifiers = list(default = list('MillDepth', 'Md', 'TiefeGesamt', 'Tg'))
    # To be used in the DXF layer name. See DXF2GCODE' wiki for more information.
    slice_depth_identifiers = list(default = list('SliceDepth', 'Sd', 'TiefeZustellung', 'Tz'))
    # To be used in the DXF layer name. See DXF2GCODE' wiki for more information.
    start_mill_depth_identifiers = list(default = list('StartMillDepth', 'SMd', 'StartTiefe', 'St'))
    # To be used in the DXF layer name. See DXF2GCODE' wiki for more information.
    retract_identifiers = list(default = list('RetractHeight', 'Rh', 'Freifahrthoehe', 'FFh'))
    # To be used in the DXF layer name. See DXF2GCODE' wiki for more information.
    safe_margin_identifiers = list(default = list('SafeMargin', 'Sm', 'Sicherheitshoehe', 'Sh'))
    # To be used in the DXF layer name. See DXF2GCODE' wiki for more information.
    f_g1_plane_identifiers = list(default = list('FeedXY', 'Fxy', 'VorschubXY', 'Vxy', 'F'))
    # To be used in the DXF layer name. See DXF2GCODE' wiki for more information.
    f_g1_depth_identifiers = list(default = list('FeedZ', 'Fz', 'VorschubZ', 'Vz'))

    # To be used in the DXF layer name. See DXF2GCODE' wiki for more information.
    tool_nr_identifiers = list(default = list('ToolNr', 'Tn', 'T', 'WerkzeugNummer', 'Wn'))
    # To be used in the DXF layer name. See DXF2GCODE' wiki for more information.
    tool_diameter_identifiers = list(default = list('ToolDiameter', 'Td', 'WerkzeugDurchmesser', 'Wd'))
    # To be used in the DXF layer name. See DXF2GCODE' wiki for more information.
    spindle_speed_identifiers = list(default = list('SpindleSpeed', 'Drehzahl', 'RPM', 'UPM', 'S'))
    # To be used in the DXF layer name. See DXF2GCODE' wiki for more information.
    start_radius_identifiers = list(default = list('StartRadius', 'Sr'))
    # To be used in the DXF layer name. See DXF2GCODE' wiki for more information.
    milling_offset_identifiers = list(default = list('MillingOffset', 'Mo'))

    # Tools table: define here the tools used for milling:
    # - name: this is the number of the tool, it will be used directly in the GCODE (eg 20 for tool T20)
    # - diameter: diameter of the tool
    # - speed: spindle speed in rpm
    # - start_radius: start radius for tool compensation when using G41 / G42 moves
    # - milling_offset: additional offset (finishing allowance) added to the tool
    #   radius of the software cutter compensation; 0 = unchanged behaviour.
    #   It is only used as the default value for the individual outline offset
    #   of a shape (Tools table -> Shape window), which can be edited there.
    [Tool_Parameters]
    [[1]]
    diameter = float(default = 2.0)
    speed = float(default = 6000)
    start_radius = float(default = 0.2)
    milling_offset = float(default = 0.0)

    [[2]]
    diameter = float(default = 2.0)
    speed = float(default = 6000.0)
    start_radius = float(default = 1.0)
    milling_offset = float(default = 0.0)

    [[10]]
    diameter = float(default = 10.0)
    speed = float(default = 6000.0)
    start_radius = float(default = 2.0)
    milling_offset = float(default = 0.0)

    [[__many__]]
    diameter = float(default = 3.0)
    speed = float(default = 6000)
    start_radius = float(default = 3.0)
    milling_offset = float(default = 0.0)

    # Define here custom GCODE actions:
    # - name: this is the unique name of the action
    # - gcode: the text that will be inserted in the final program (each new line is also translated as a new line in the output file)
    # Custom actions can be inserted in the program by using right-click contextual menu on the treeview.
    [Custom_Actions]
    [[__many__]]
    gcode = string(default = "(change subsection name and insert your custom GCode here. Use triple quote to place the code on several lines)")

    [Logging]
    # Logging to textfile is disabled by default
    logfile = string(default = "")

    # This really goes to stderr
    console_loglevel = option('DEBUG', 'INFO', 'WARNING', 'ERROR','CRITICAL', default = 'CRITICAL')

    # Log levels are, in increasing importance: DEBUG; INFO; WARNING; ERROR; CRITICAL
    # Log events with importance >= loglevel are logged to the corresponding output
    file_loglevel = option('DEBUG', 'INFO', 'WARNING', 'ERROR','CRITICAL', default = 'DEBUG')

    # Logging level for the message window
    window_loglevel = option('DEBUG', 'INFO', 'WARNING', 'ERROR','CRITICAL', default = 'INFO')

''').splitlines()
""" format, type and default value specification of the global config file"""


class MyConfig(object):
    """
    This class hosts all functions related to the Config File.
    """
    def __init__(self):
        """
        initialize the varspace of an existing plugin instance
        init_varspace() is a superclass method of plugin
        """

        self.folder = os.path.join(g.folder, c.DEFAULT_CONFIG_DIR)
        self.filename = os.path.join(self.folder, 'config' + c.CONFIG_EXTENSION)

        self.version_mismatch = '' # no problem for now
        self.default_config = False # whether a new name was generated
        self.var_dict = dict()
        self.spec = ConfigObj(CONFIG_SPEC, interpolation=False, list_values=False, _inspec=True)

        # try:
        self.load_config()

        # The unit used for the values in the config file. It is fixed until
        # software restart (see 'tool_units' option), so read it here once.
        self.tool_units = self.var_dict['General']['tool_units']
        # Drawing unit; starts with the config file's unit and changes while
        # importing a DXF (importer.py) or via the measurement units menu.
        self.metric = 0 if self.tool_units == 'in' else 1

        self.update_config()

        # The following settings won't be modified after a change in the configuration window.
        # If a setting need to be updated when the configuration changes, move it to the update_config() function
        self.mode3d = self.vars.General['mode3d']

        self.machine_type = self.vars.General['machine_type']
        self.fitting_tolerance = self.vars.Import_Parameters['fitting_tolerance']
        self.point_tolerance = self.vars.Import_Parameters['point_tolerance']

        # Unit of the values currently held in self.vars (set by update_config)
        self.tool_units_metric = self.metric

        # except Exception, msg:
        #     logger.warning(self.tr("Config loading failed: %s") % msg)
        #     return False

    def tr(self, string_to_translate):
        """
        Translate a string using the QCoreApplication translation framework
        @param string_to_translate: a unicode string
        @return: the translated unicode string if it was possible to translate
        """
        return str(QtCore.QCoreApplication.translate('MyConfig',
                                                           string_to_translate))

    def update_config(self):
        """
        Call this function each time the self.var_dict is updated (eg when the configuration window changes some settings)
        """
        # If the config file's unit (tool_units option) was changed, convert
        # all unit-dependent values stored in var_dict so they keep their
        # physical meaning. This makes the change effective immediately -
        # no restart required anymore.
        new_units_metric = 0 if self.var_dict['General']['tool_units'] == 'in' else 1
        old_units_metric = 0 if self.tool_units == 'in' else 1
        if new_units_metric != old_units_metric:
            self._convert_var_dict_units(old_units_metric, new_units_metric)
            self.tool_units = self.var_dict['General']['tool_units']

        # convenience - flatten nested config dict to access it via self.config.sectionname.varname
        self.vars = DictDotLookup(self.var_dict)

        # The values just taken from var_dict are expressed in the config
        # file's unit (self.tool_units), NOT in the current drawing's unit.
        # Reset the tracked unit and convert all unit-dependent values to
        # the drawing unit (self.metric). Without this, changed values would
        # be used with the wrong unit (e.g. a 2 mm cutter interpreted as
        # 2 inch in an inch drawing -> 50x too large).
        self.tool_units_metric = 0 if self.tool_units == 'in' else 1
        self.update_tool_values()

    def _convert_var_dict_units(self, old_metric, new_metric):
        """
        Convert all unit-dependent values stored in var_dict from the old
        unit to the new one. Called when the user changes the 'tool_units'
        option in the configuration window, so the stored values keep their
        physical meaning (e.g. a 2.0 mm cutter becomes 0.0787 in).
        """
        if old_metric == new_metric:
            return
        scale = 1/25.4 if new_metric == 0 else 25.4

        for key in self.var_dict['Plane_Coordinates']:
            if key == 'std_scale':
                continue  # dimensionless scale factor
            self.var_dict['Plane_Coordinates'][key] = float(self.var_dict['Plane_Coordinates'][key]) * scale
        for key in self.var_dict['Depth_Coordinates']:
            self.var_dict['Depth_Coordinates'][key] = float(self.var_dict['Depth_Coordinates'][key]) * scale
        for key in self.var_dict['Feed_Rates']:
            self.var_dict['Feed_Rates'][key] = float(self.var_dict['Feed_Rates'][key]) * scale
        for tool in self.var_dict['Tool_Parameters']:
            self.var_dict['Tool_Parameters'][tool]['diameter'] = float(self.var_dict['Tool_Parameters'][tool]['diameter']) * scale
            self.var_dict['Tool_Parameters'][tool]['start_radius'] = float(self.var_dict['Tool_Parameters'][tool]['start_radius']) * scale
            self.var_dict['Tool_Parameters'][tool]['milling_offset'] = float(self.var_dict['Tool_Parameters'][tool]['milling_offset']) * scale

    def make_settings_folder(self):
        """Create settings folder if necessary"""
        try:
            os.makedirs(self.folder)
        except OSError:
            pass

    def load_config(self):
        """Load Config File"""
        
        logger.info(self.filename)
        
        if os.path.isfile(self.filename):
            try:
                # file exists, read & validate it
                self.var_dict = ConfigObj(self.filename, configspec=CONFIG_SPEC)
                _vdt = Validator()
                result = self.var_dict.validate(_vdt, preserve_errors=True)
                validate_errors = flatten_errors(self.var_dict, result)

                if validate_errors:
                    logger.error(self.tr("errors reading %s:") % self.filename)

                for entry in validate_errors:
                    section_list, key, error = entry
                    if key is not None:
                        section_list.append(key)
                    else:
                        section_list.append('[missing section]')
                    section_string = ', '.join(section_list)
                    if not error:
                        error = self.tr('Missing value or section.')
                    logger.error("%s = %s" % (section_string, error))

                if validate_errors:
                    raise BadConfigFileError("syntax errors in config file")

                # check config file version against internal version
                if CONFIG_VERSION:
                    fileversion = self.var_dict['Version']['config_version']  # this could raise KeyError
                    if fileversion not in  SUPPORTED_CONFIGS:
                        raise VersionMismatchError(fileversion, SUPPORTED_CONFIGS)
                    else:
                        self.var_dict['Version']['config_version']=CONFIG_VERSION

                    #if fileversion != CONFIG_VERSION:
                    #   raise VersionMismatchError(fileversion, CONFIG_VERSION)

            except VersionMismatchError:
                #raise VersionMismatchError(fileversion, CONFIG_VERSION)
                # version mismatch flag, it will be used to display an error.
                self.version_mismatch = self.tr("The configuration file version ({0}) doesn't match any of the software expected version ({1}).\n\nYou have to delete (or carefully edit) the configuration file \"{2}\" to solve the problem.").format(fileversion, SUPPORTED_CONFIGS, self.filename)

            except Exception as inst:
                logger.error(inst)
                (base, ext) = os.path.splitext(self.filename)
                badfilename = base + c.BAD_CONFIG_EXTENSION
                logger.debug(self.tr("trying to rename bad cfg %s to %s") % (self.filename, badfilename))
                try:
                    # os.replace overwrites an already existing .bad file
                    # (os.rename would raise FileExistsError on Windows when a
                    # previous corrupted config was not cleaned up).
                    os.replace(self.filename, badfilename)
                except OSError as e:
                    logger.error(self.tr("rename(%s,%s) failed: %s") % (self.filename, badfilename, e.strerror))
                    raise
                else:
                    logger.debug(self.tr("renamed bad varspace %s to '%s'") % (self.filename, badfilename))
                    self.create_default_config()
                    self.default_config = True
                    logger.debug(self.tr("created default varspace '%s'") % self.filename)
            else:
                self.default_config = False
                # logger.debug(self.dir())
                # logger.debug(self.tr("created default varspace '%s'") % self.filename)
                # logger.debug(self.tr("read existing varspace '%s'") % self.filename)
        else:
            self.create_default_config()
            self.default_config = True
            logger.debug(self.tr("created default varspace '%s'") % self.filename)

        self.var_dict.main.interpolation = False  # avoid ConfigObj getting too clever

    def create_default_config(self):
        # check for existing setting folder or create one
        self.make_settings_folder()

        # derive config file with defaults from spec
        self.var_dict = ConfigObj(configspec=CONFIG_SPEC)
        _vdt = Validator()
        self.var_dict.validate(_vdt, copy=True)
        self.var_dict.filename = self.filename
        self.var_dict.write()

    def save_varspace(self):
        """Saves Variables space"""
        self.var_dict.filename = self.filename
        self.var_dict.write()

    def print_vars(self):
        """Prints Variables"""
        print("Variables:")
        for k, v in self.var_dict['Variables'].items():
            print(k, "=", v)

    def makeConfigWidgets(self):
        """
        Build the configuration widgets and store them into a dictionary.
        The structure of the dictionnary must match the structure of the configuration file. The names of the keys must be identical to those used in the configfile.
        If a name is declared in the configfile but not here, it simply won't appear in the config window (the config_version for example must not be modified by the user, so it is not declared here)
        """
        # The configuration window displays the values in the CONFIG file's
        # unit (tool_units) - NOT in the current drawing's unit
        # (tool_units_metric holds the drawing unit after conversions).
        coordinate_unit = self.tr(" mm") if self.tool_units == 'mm' else self.tr(" in")
        speed_unit = self.tr(" mm/min") if self.tool_units == 'mm' else self.tr(" IPS")
        cfg_widget_def = OrderedDict([
            ('__section_title__', {
                # This section is only used for assigning titles to the keys of the dictionnary (= name of the sections used in the config file).
                # This name is displayed in the tabs of the configuration window ; if no name is provided, the key name is used. A same title may be used for several keys : in this case, all the items that belongs to this section are regrouped into the same tab.
                # Note: the title may be specified in the section itselt too, using special entry "'__section_title__': Title to use"
                'Tool_Parameters': self.tr("Tools table"),
                'Custom_Actions' : self.tr("Custom actions")}),
            ('Paths', OrderedDict([
                ('__section_title__', self.tr("Software config")),
                ('import_dir', CfgLineEdit(self.tr('By default look for DXF files in:'))),
                ('output_dir', CfgLineEdit(self.tr('By default export generated G-Code to:'))),
                ('project_dir', CfgLineEdit(self.tr('By default save Project files to:'))),
                ('autosave_path', CfgCheckBox(self.tr('Update paths with last used path: ')))

            ])),
            ('Filters', OrderedDict([
                ('__section_title__', self.tr("Software config")),
                ('__subtitle__', CfgSubtitle("pdftops")),
                ('pdftops_cmd', CfgLineEdit(self.tr('Location of executable:'))),
                ('pdftops_opt', CfgListEdit(self.tr('Command-line options:'), ',')),

                ('__subtitle2__', CfgSubtitle("pstoedit")),
                ('pstoedit_cmd', CfgLineEdit(self.tr('Location of executable:'))),
                ('pstoedit_opt', CfgListEdit(self.tr('Command-line options:'), ','))
            ])),
            ('General', OrderedDict([
                ('__section_title__', self.tr("General settings")),
                ('mode3d', CfgCheckBox(self.tr('3D mode (requires OpenGL - restart needed)'))),
                ('show_disabled_paths', CfgCheckBox(self.tr('Display disabled paths (default)'))),
                ('live_update_export_route', CfgCheckBox(self.tr('Live update export route (default)'))),
                ('show_scale_bar', CfgCheckBox(self.tr('Show a scale bar in the canvas'))),
                ('__subtitle2__', CfgSubtitle(self.tr("Milling"))),
                ('split_line_segments', CfgCheckBox(self.tr('Split line segments (default)'))),
                ('automatic_cutter_compensation', CfgCheckBox(self.tr('Automatic cutter compensation (default)'))),
                ('machine_type', CfgComboBox(self.tr('Machine type (default):'))),
                ('tool_units', CfgComboBox(self.tr('Configuration values use the unit (restart needed):'))),
                ('__subtitle3__', CfgSubtitle(self.tr("Output"))),
                ('write_to_stdout', CfgCheckBox(self.tr('Export the G-Code to stdout (instead of a file)')))
            ])),
            ('Axis_letters', OrderedDict([
                ('__section_title__', self.tr("Machine config")),
                ('__subtitle__', CfgSubtitle(self.tr("Axes' identifiers"))),
                ('ax1_letter', CfgLineEdit(self.tr('First axis:'))),
                ('ax2_letter', CfgLineEdit(self.tr('Second axis:'))),
                ('ax3_letter', CfgLineEdit(self.tr('Third axis:')))
            ])),
            ('Plane_Coordinates', OrderedDict([
                ('__section_title__', self.tr("Machine config")),
                ('__subtitle__', CfgSubtitle(self.tr("Start and end's coordinate and scaling standard multiplier"))),
                ('axis1_start_end', CfgDoubleSpinBox(self.tr("First axis start/end coordiante:"), coordinate_unit)),
                ('axis2_start_end', CfgDoubleSpinBox(self.tr("Second axis start/end coordinate:"), coordinate_unit)),
                ('std_scale', CfgDoubleSpinBox(self.tr("Scale first and second axis:")))
            ])),
            ('Depth_Coordinates', OrderedDict([
                ('__section_title__', self.tr("Machine config")),
                ('__subtitle__', CfgSubtitle(self.tr("Third axis' defaults"))),
                ('axis3_retract', CfgDoubleSpinBox(self.tr("Retraction coordinate:"), coordinate_unit)),
                ('axis3_safe_margin', CfgDoubleSpinBox(self.tr("Safety margin:"), coordinate_unit)),
                ('axis3_start_mill_depth', CfgDoubleSpinBox(self.tr("Workpiece origin coordinate:"), coordinate_unit)),
                ('axis3_slice_depth', CfgDoubleSpinBox(self.tr("Slice depth:"), coordinate_unit)),
                ('axis3_mill_depth', CfgDoubleSpinBox(self.tr("Final mill depth:"), coordinate_unit))
            ])),
            ('Feed_Rates', OrderedDict([
                ('__section_title__', self.tr("Machine config")),
                ('__subtitle__', CfgSubtitle(self.tr("G1 feed rates"))),
                ('f_g1_plane', CfgDoubleSpinBox(self.tr('First and second axis (2D plane):'), speed_unit)),
                ('f_g1_depth', CfgDoubleSpinBox(self.tr('Third axis:'), speed_unit))
            ])),
            ('Cutter_Compensation', OrderedDict([
                ('__section_title__', self.tr("Output settings")),
                ('__subtitle__', CfgSubtitle(self.tr("Cutter compensation"))),
                ('done_by_machine', CfgCheckBox(self.tr('Cutter compensation is done by machine (check box if machine reconizes G41 and G42 commands / uncheck otherwise. This also disables pocket milling.)')))
            ])),
            ('Pocketing', OrderedDict([
                ('__section_title__', self.tr("Output settings")),
                ('__subtitle__', CfgSubtitle(self.tr("Pocket milling"))),
                ('pocket_edge_clearance', CfgDoubleSpinBox(self.tr('Pocket edge clearance (distance between cutting edge and contour, as % of tool diameter):'), ' %', 0, 100, 2)),
                ('pocket_compensation_mode', CfgComboBox(self.tr('Cutter compensation while pocket milling:')))
            ])),
            ('Drag_Knife_Options', OrderedDict([
                ('__section_title__', self.tr("Output settings")),
                ('__subtitle__', CfgSubtitle(self.tr("Drag Knife options"))),
                ('drag_angle', CfgDoubleSpinBox(self.tr('Retract to drag depth ("Third axis slice depth") if angle exceeds:'), u'°'))#u for unicode
            ])),
            ('Route_Optimisation', OrderedDict([
                ('__section_title__', self.tr("Output settings")),
                ('default_TSP', CfgCheckBox(self.tr("By default enable the TSP optimization for ordering shapes (TSP = Travelling Salesman Problem)"))),
                ('__subtitle__', CfgSubtitle(self.tr("TSP optimizer"))),
                ('TSP_shape_order', CfgComboBox(self.tr('Optimizer behaviour:'))),
                ('mutation_rate', CfgDoubleSpinBox(self.tr('Mutation rate:'))),
                ('max_population', CfgSpinBox(self.tr('Max population:'))),
                ('max_iterations', CfgSpinBox(self.tr('Max iterations:'))),
                ('begin_art', CfgComboBox(self.tr('Starting point:')))
            ])),
            ('Import_Parameters', OrderedDict([
                ('__section_title__', self.tr("Output settings")),
                ('point_tolerance', CfgDoubleSpinBox(self.tr('DXF default import point tolerance:'), '', None, None, 5)),
                ('spline_check', CfgSpinBox(self.tr('DXF import spline check:'))),
                ('fitting_tolerance', CfgDoubleSpinBox(self.tr('DXF default import fit tolerance:'), '', None, None, 5)),
                ('insert_at_block_layer', CfgCheckBox(self.tr('insert elements which are part of a block to layer where the block is inserted')))
            ])),
            ('Layer_Options', OrderedDict([
                ('__section_title__', self.tr("Automatic tool config")),
                ('id_float_separator', CfgLineEdit(self.tr('Separator between identifier and value:'))),
                ('__subtitle__', CfgSubtitle(self.tr("Parameters' identifiers"))),
                ('mill_depth_identifiers', CfgListEdit(self.tr('Final mill depth:'), ',')),
                ('slice_depth_identifiers', CfgListEdit(self.tr('Infeed depth:'), ',')),
                ('start_mill_depth_identifiers', CfgListEdit(self.tr('Workpiece top:'), ',')),
                ('retract_identifiers', CfgListEdit(self.tr('Retraction area:'), ',')),
                ('safe_margin_identifiers', CfgListEdit(self.tr('Safety margin:'), ',')),
                ('f_g1_plane_identifiers', CfgListEdit(self.tr('G1 feed rate for first and second axis (2D plane):'), ',')),
                ('f_g1_depth_identifiers', CfgListEdit(self.tr('G1 feed rate for third axis:'), ',')),
                ('tool_nr_identifiers', CfgListEdit(self.tr('Tool number:'), ',')),
                ('tool_diameter_identifiers', CfgListEdit(self.tr('Tool diameter:'), ',')),
                ('spindle_speed_identifiers', CfgListEdit(self.tr('Spindle speed:'), ',')),
                ('start_radius_identifiers', CfgListEdit(self.tr('Start radius (cutter compensation):'), ',')),
                ('milling_offset_identifiers', CfgListEdit(self.tr('Additional offset (finishing allowance):'), ','))
            ])),
            ('Tool_Parameters', CfgTableToolParameters(self.tr('Define the tools here:'))),
            ('Custom_Actions', CfgTableCustomActions(self.tr('Define here custom GCODE that can be inserted anywhere in the program:'))),
            ('Logging', OrderedDict([
                ('__section_title__', self.tr("Software config")),
                ('logfile', CfgLineEdit(self.tr('File used for logging (restart needed):'))),
                ('console_loglevel', CfgComboBox(self.tr('On stderr console log messages with importance minimal to level (restart needed):'))),
                ('file_loglevel', CfgComboBox(self.tr('For log-file log messages with importance minimal to level (restart needed):'))),
                ('window_loglevel', CfgComboBox(self.tr('For message box log messages with importance minimal to level (restart needed):')))
            ]))
        ])

        return cfg_widget_def

    def update_tool_values(self):
        """
        update the tool default values depending on the unit of the drawing
        """
        if self.tool_units_metric != self.metric:
            scale = 1/25.4 if self.metric == 0 else 25.4
            for key in self.vars.Plane_Coordinates:
                if key == 'std_scale':
                    # std_scale is a dimensionless scale factor, NOT a
                    # coordinate: converting it corrupts the standard scale
                    # (e.g. 1.0 -> 0.0394 after an inch import), which then
                    # shrinks the next imported drawing by 1/25.4 because
                    # open() captures cont_scale BEFORE the importer
                    # converts the values back.
                    continue
                self.vars.Plane_Coordinates[key] *= scale
            for key in self.vars.Depth_Coordinates:
                self.vars.Depth_Coordinates[key] *= scale
            for key in self.vars.Feed_Rates:
                self.vars.Feed_Rates[key] *= scale
            for tool in self.vars.Tool_Parameters:
                self.vars.Tool_Parameters[tool]['diameter'] *= scale
                self.vars.Tool_Parameters[tool]['start_radius'] *= scale
                self.vars.Tool_Parameters[tool]['milling_offset'] *= scale
        self.tool_units_metric = self.metric


class DictDotLookup(object):
    """
    Creates objects that behave much like a dictionaries, but allow nested
    key access using object '.' (dot) lookups.
    """
    def __init__(self, d):
        for k in d:
            if isinstance(d[k], dict):
                self.__dict__[k] = DictDotLookup(d[k])
            elif isinstance(d[k], (list, tuple)):
                l = []
                for v in d[k]:
                    if isinstance(v, dict):
                        l.append(DictDotLookup(v))
                    else:
                        l.append(v)
                self.__dict__[k] = l
            else:
                self.__dict__[k] = d[k]

    def __getitem__(self, name):
        if name in self.__dict__:
            return self.__dict__[name]

    def __setitem__(self, name, value):
        if name in self.__dict__:
            self.__dict__[name] = value

    def __iter__(self):
        return iter(self.__dict__.keys())

    def __repr__(self):
        return pprint.pformat(self.__dict__)

# if __name__ == '__main__':
#     cfg_data = eval("""{
#         'foo' : {
#             'bar' : {
#                 'tdata' : (
#                     {'baz' : 1 },
#                     {'baz' : 2 },
#                     {'baz' : 3 },
#                 ),
#             },
#         },
#         'quux' : False,
#     }""")
#
#     cfg = DictDotLookup(cfg_data)
#
#     # iterate
#     for k, v in cfg.__iter__(): #foo.bar.iteritems():
#         print k, " = ", v
#
#     print "cfg=", cfg
#
#     #   Standard nested dictionary lookup.
#     print 'normal lookup :', cfg['foo']['bar']['tdata'][0]['baz']
#
#     #   Dot-style nested lookup.
#     print 'dot lookup    :', cfg.foo.bar.tdata[0].baz
#
#     print "qux=", cfg.quux
#     cfg.quux = '123'
#     print "qux=", cfg.quux
#
#     del cfg.foo.bar
#     cfg.foo.bar = 4711
#     print 'dot lookup    :', cfg.foo.bar #.tdata[0].baz


############################################################################
# Configuration profiles
#
# A configuration profile is simply a different folder below ~/.config. The
# default profile lives in DEFAULT_CONFIG_FOLDER, an alternative profile adds
# '.suffix' to that folder name (e.g. ~/.config/dxf2gcode.laser). The global
# variable g.folder always points to the folder of the currently active
# profile; the whole existing configuration management (config/config.cfg and
# postpro_config/*.cfg) then works unchanged for every profile.
############################################################################

# A profile suffix becomes part of a directory name, so keep it to a safe
# subset and never allow path separators or relative path components.
CONFIG_PROFILE_SUFFIX_PATTERN = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_-]*$')


def validate_config_profile_suffix(suffix):
    """
    Check whether a profile suffix can safely be used as a directory name.
    @param suffix: the requested profile suffix (without the leading separator)
    @return (valid, message): valid is True when the suffix may be used,
            otherwise message explains the problem.
    """
    if not suffix:
        return (False, "Empty configuration profile name.")
    if not CONFIG_PROFILE_SUFFIX_PATTERN.match(str(suffix)):
        return (False, "Invalid configuration profile name '{0}'. Only letters, "
                       "digits, '-' and '_' are allowed (and it must start with "
                       "a letter or digit).".format(suffix))
    return (True, '')


def config_profile_folder(suffix=None):
    """
    @param suffix: profile suffix or None/'' for the default profile
    @return: the configuration folder of the requested profile
    """
    if suffix:
        return c.DEFAULT_CONFIG_FOLDER + c.CONFIG_PROFILE_SEPARATOR + suffix
    return c.DEFAULT_CONFIG_FOLDER


def active_config_profile_suffix():
    """
    @return: the suffix of the currently active profile ('' for the default
             profile). Derived from g.folder, so it always matches the folder
             the running configuration was loaded from.
    """
    base = c.DEFAULT_CONFIG_FOLDER
    folder = (g.folder if g.folder else base).replace("\\", "/")
    if folder == base:
        return ''
    prefix = base + c.CONFIG_PROFILE_SEPARATOR
    if folder.startswith(prefix):
        return folder[len(prefix):]
    return ''


def available_config_profiles():
    """
    Detect the configuration profiles that exist next to DEFAULT_CONFIG_FOLDER.
    Only real directories named like the default folder or the default folder
    plus a valid '.suffix' are reported.
    @return: an ordered dict mapping the profile suffix ('' for the default
             profile) to its folder. The default profile and the currently
             active profile are always present.
    """
    base = c.DEFAULT_CONFIG_FOLDER
    base_name = os.path.basename(base)
    parent = os.path.dirname(base)
    prefix = base_name + c.CONFIG_PROFILE_SEPARATOR

    profiles = OrderedDict([('', base)])

    try:
        entries = sorted(os.listdir(parent))
    except OSError:
        entries = []

    for entry in entries:
        if entry == base_name or not entry.startswith(prefix):
            continue
        suffix = entry[len(prefix):]
        valid, _message = validate_config_profile_suffix(suffix)
        if valid and os.path.isdir(os.path.join(parent, entry)):
            profiles[suffix] = os.path.join(parent, entry)

    # Make sure the active profile is selectable even if its folder does not
    # exist yet (it is created on first use).
    active = active_config_profile_suffix()
    if active and active not in profiles:
        profiles[active] = config_profile_folder(active)

    return profiles


def _config_profile_settings():
    """
    QSettings store used to remember the profile selected in the GUI. It is
    shared with the window state settings and lives outside of any profile
    folder, so it is not affected by a profile switch.
    """
    return QtCore.QSettings("dxf2gcode", "dxf2gcode")


def stored_config_profile():
    """
    @return: the profile suffix selected in the GUI ('' for the default
             profile), or None when no profile was selected yet. Invalid
             values are treated as "not selected".
    """
    settings = _config_profile_settings()
    if not settings.contains("Config/profile"):
        return None
    value = settings.value("Config/profile")
    if value is None:
        return ''
    value = str(value)
    if value:
        valid, _message = validate_config_profile_suffix(value)
        if not valid:
            return None
    return value


def store_config_profile(suffix):
    """
    Remember the profile selected in the GUI so that the next program start
    uses it. Pass '' to select the default profile again.
    """
    settings = _config_profile_settings()
    settings.setValue("Config/profile", suffix if suffix else '')
    settings.sync()
