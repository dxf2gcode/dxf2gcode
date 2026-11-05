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

import os
import time
import re
import shutil
import logging

import dxf2gcode.bootstrap.runtime_state as g
from dxf2gcode.bootstrap.version_metadata import get_version_info

from dxf2gcode.domain.geometry.point import Point
from dxf2gcode.adapters.postprocessor.postprocessorconfig import MyPostProConfig
from dxf2gcode.adapters.postprocessor.breaks import Breaks
from dxf2gcode.adapters.postprocessor.dialect import ProfileDialect
from dxf2gcode.presentation.qt.configwindow import *

import dxf2gcode.domain.constants as c
from dxf2gcode.presentation.qt.qt_compat.QtWidgets import QMessageBox
from dxf2gcode.presentation.qt.qt_compat import QtCore

str_encode = lambda exstr: exstr

logger = logging.getLogger("PostPro.PostProcessor")


class MyPostProcessor(ProfileDialect):
    """
    The PostProcessor Class includes the functions for getting the output
    variables from the PostProcessorConfig Classes and general function related
    to the export of the Code.
    """
    def __init__(self, create_config_window=True):
        """
        The initialisation of the Postprocessor class. This function is called
        during the initialisation of the Main Window. It checks during the
        initialization if a PostProcessor Config file exists and if not creates
        a new one.
        For the Save function it creates a list of all possible Postprocessor
        Config Files.
        """
        self.version_mismatch = '' # no problem for now
        self.postprocessor_files = [] # store the postprocessors filenames
        self.postpro_file_used = None
        self.output_format = [] # store the postprocessors filenames extensions
        self.output_text = [] # store the postprocessors descriptions

        # Load the existing postprocessor config files, or create a new one
        self.loadCreateConfigFiles()

        self.config_postpro_window = None
        if create_config_window:
            logger.info('Creating postprocessor configuration window')
            self.config_postpro_window = ConfigWindow(
                MyPostProConfig.makeConfigWidgets(),
                title=self.tr("Postprocessor configuration"))
            self.config_postpro_window.setConfigSelectorCallback(
                self.postproConfigSelectionChangedCallback,
                self.postproConfigAddFileCallback,
                self.postproConfigRemoveFileCallback,
                self.postproConfigDuplicateFileCallback)
            self.config_postpro_window.setConfigSelectorFilesList(
                self.getConfigsList())
            self.config_postpro_window.finished.connect(
                self.updatePostprocessorConfiguration)


    def tr(self, string_to_translate):
        """
        Translate a string using the QCoreApplication translation framework
        @param: string_to_translate: a unicode string
        @return: the translated unicode string if it was possible to translate
        """
        return str(QtCore.QCoreApplication.translate("MyPostProcessor",
                                                     string_to_translate))

    def add_export_error(self, message):
        """
        Collect an error of the export. The errors are shown to the user at the
        end of the export, so that a single message box is enough and the
        export is not interrupted by a modal dialog for every single shape.
        @param message: the error message
        """
        if message not in self.export_errors:
            self.export_errors.append(message)
        logger.error(message)

    def add_planning_diagnostic(self, diagnostic):
        """Present returned planning diagnostics through the export channel."""
        if diagnostic not in self.planning_diagnostics:
            self.planning_diagnostics.append(diagnostic)
        message = diagnostic.message
        if diagnostic.source_message:
            source = QtCore.QCoreApplication.translate(
                "Shape", diagnostic.source_message)
            from dxf2gcode.presentation.qt.toolpath_labels import translate_message
            message_args = tuple(translate_message(a) if hasattr(a, "context") else a
                                 for a in diagnostic.message_args)
            message = (source % message_args
                       if diagnostic.message_args else source)
        if message not in self.export_errors:
            self.export_errors.append(message)
        if diagnostic.severity == "error":
            logger.error(message)
        else:
            logger.warning(message)


    def updatePostprocessorConfiguration(self, result):
        """
        Some modification occured in the postprocessor configuration window, we need to save these changes into the config file.
        Once done, the signal postprocessor_configuration_changed is emitted, so that anyone interested in this information can connect to this signal.
        """
        if result == ConfigWindow.Applied or result == ConfigWindow.DialogCode.Accepted:
            self.postpro_config_currently_edited.save_varspace() #Write the configuration into the config file (eg postpro_config.cfg, ...)
            self.postpro_config_currently_edited.update_config()


    def postproConfigSelectionChangedCallback(self, config_file_index):
        """
        Callback function called whenever the current configuration file changes in the postprocessor config window.
        The current config object is updated accordingly (this object is only used by the configuration window, it doesn't affect the export functions of dxf2gcode)
        @param: the file index in the postprocessor_files[] list
        """
        if config_file_index >= 0 and config_file_index < len(self.postprocessor_files):
            self.postpro_config_currently_edited = self.getPostProVars(config_file_index)
            self.config_postpro_window.affectValuesFromConfig(self.postpro_config_currently_edited.var_dict, self.postpro_config_currently_edited.var_dict.configspec)


    def postproConfigAddFileCallback(self, new_name):
        """
        Callback function called whenever the user wants to add a new file in the postprocessor config window.
        It creates the new file from scratch, then reaload the list of configuration files and select the new file
        @param: the new filename
        """
        result = True

        new_name += c.CONFIG_EXTENSION #Add the extension
        if new_name not in self.getConfigsList()['filename']:
            logger.debug("New postprocessor config file {0} is going to be created".format(new_name))
            postpro_config = MyPostProConfig(filename=new_name)
            postpro_config.create_default_config()
            postpro_config.default_config = True
            self.loadCreateConfigFiles()
            self.config_postpro_window.setConfigSelectorFilesList(self.getConfigsList(), new_name) #Set the list of current configuration files
        else:
            #File already exists
            result = False

        return result


    def postproConfigRemoveFileCallback(self, remove_name):
        """
        Callback function called whenever the user wants to delete a file in the postprocessor config window.
        It remove the file on the disk, then reaload the list of configuration files to reflect the changes
        @param: the filename to remove
        """
        result = True

        file_to_remove = os.path.join(os.path.join(g.folder, c.DEFAULT_POSTPRO_DIR), remove_name)
        logger.debug("Postprocessor config file {0} is going to be removed".format(file_to_remove))
        try:
            os.remove(file_to_remove) #Definitely removes the selected configfile
        except:
            logger.error(self.tr("An error occured while removing the postprocessor config file {0} ; do the operation manually and restart the software.").format(file_to_remove))
            result = False
        self.loadCreateConfigFiles()
        self.config_postpro_window.setConfigSelectorFilesList(self.getConfigsList()) #Set the list of current configuration files

        return result


    def postproConfigDuplicateFileCallback(self, duplicate_name, new_name):
        """
        Callback function called whenever the user wants to duplicate a file in the postprocessor config window.
        It copies the file on the disk, then reaload the list of configuration files and select the new file
        @param: the filename to remove
        """
        result = True

        new_name += c.CONFIG_EXTENSION
        if new_name not in self.getConfigsList()['filename']:
            new_file = os.path.join(os.path.join(g.folder, c.DEFAULT_POSTPRO_DIR), new_name)
            duplicate_file = os.path.join(os.path.join(g.folder, c.DEFAULT_POSTPRO_DIR), duplicate_name)
            logger.debug("Postprocessor config file {0} is going to be duplicated into {1}".format(duplicate_file, new_file))
            try:
                shutil.copy(duplicate_file, new_file) #Duplicate the files
            except:
                logger.error(self.tr("An error occured while duplicating the postprocessor config file {0} ; do the operation manually and restart the software.").format(duplicate_name))
                result = False
            self.loadCreateConfigFiles()
            self.config_postpro_window.setConfigSelectorFilesList(self.getConfigsList(), new_name) #Set the list of current configuration files
        else:
            result = False

        return result


    def loadCreateConfigFiles(self):
        """
        Load the existing postprocessor config files, or create a new one
        """
        del self.postprocessor_files[:] # store the postprocessors filenames
        del self.output_format[:] # store the postprocessors filenames extensions
        del self.output_text[:] # store the postprocessors descriptions

        try:
            lfiles = sorted(os.listdir(os.path.join(g.folder, c.DEFAULT_POSTPRO_DIR)))
            """
            FIXME Folder needs to be empty or valid config file within.
            """
            # logger.debug(lfiles)
        except:
            # Create a Postprocessor File if none found in folder
            logger.debug(self.tr("created default varspace"))
            PostProConfig = MyPostProConfig()
            PostProConfig.create_default_config()
            PostProConfig.default_config = True

            lfiles = os.listdir(PostProConfig.folder)

        # Only files with the predefined extension, stated in c.CONFIG_EXTENSION
        # (default .cfg), are accepted
        for lfile in lfiles:
            if os.path.splitext(lfile)[1] == c.CONFIG_EXTENSION:
                self.postprocessor_files.append(lfile)

        if len(self.postprocessor_files) == 0:
            PostProConfig = MyPostProConfig()
            PostProConfig.create_default_config()
            PostProConfig.default_config = True
            lfiles = os.listdir(PostProConfig.folder)

            self.postprocessor_files = []
            for lfile in lfiles:
                if os.path.splitext(lfile)[1] == c.CONFIG_EXTENSION:
                    self.postprocessor_files.append(lfile)

        # Load all files to get the possible postprocessor configs to export
        self.get_output_vars()


    def getConfigsList(self):
        """
        Return a dict with the postprocessor files names, their extentions, and the description
        """
        return {'filename': self.postprocessor_files, 'extension': self.output_format, 'description': self.output_text}


    def get_output_vars(self):
        """
        Reads all Postprocessor Config Files located in the PostProcessor Config
        Directory and creates a list of the possible output formats.
        """
        for postprocessor_file in self.postprocessor_files:

            PostProConfig = MyPostProConfig(filename=postprocessor_file)
            PostProConfig.load_config()
            self.version_mismatch += PostProConfig.version_mismatch # Get possible version error encountered when opening the file

            self.output_format.append(PostProConfig.vars.General['output_format'])
            self.output_text.append(PostProConfig.vars.General['output_text'])


    def getPostProVars(self, file_index):
        """
        Get the parameters of the Postprocessor Config File
        @param file_index: The index of the file to read and write variables in
        self.vars.
        """
        self.postpro_file_used=self.postprocessor_files[file_index]
        PostProConfig = MyPostProConfig(filename=self.postprocessor_files[file_index])
        PostProConfig.load_config()
        self.vars = PostProConfig.vars

        return PostProConfig


    def exportShapes(self, load_filename, save_filename, LayerContents):
        """
        This function performs the export to a file or stdout.
        It calls the following dedicated export functions and runs
        though the list of layers to export after checking if there are shapes
        to export on these layers.
        @param load_filename: The name of the loaded dxf file. This name is
        written at the start of the export
        @param save_filename: The name of the file which shall be created.
        @param LayerContents: List which includes the order of the
        LayerContent to be exported and the LayerContent itself includes the
        export parameters (e.g. mill depth) and the shapes to be exported. The
        shape order is also given in a list defined in LayerContent.
        """
        self.breaks = Breaks(LayerContents)
        self.initialize_export_vars()

        exstr = self.write_gcode_be(load_filename)

        from dxf2gcode.adapters.postprocessor.tool_change import managed, ToolChangeError
        managed_profile = managed(self.vars)
        has_moves = True
        if managed_profile:
            try:
                body = self._managed_tool_changes(LayerContents)
                exstr += body
                has_moves = bool(body)
            except ValueError as error:
                message = str(error)
                if isinstance(error, ToolChangeError):
                    message = self.tr(error.message)
                    if error.parameters:
                        message %= error.parameters
                self.export_errors.append(message)
                self.export_failed = True
                return
        else:
            exstr += self._legacy_tool_changes(LayerContents)

        # Move machine to the Final Position
        EndPosition = Point(g.config.vars.Plane_Coordinates['axis1_start_end'],
                            g.config.vars.Plane_Coordinates['axis2_start_end'])

        if has_moves:
            exstr += self.rap_pos_xy(EndPosition)

        # Write the end G-Code at the end
        exstr += self.write_gcode_en()

        exstr = self.make_line_numbers(exstr)
        exstr = self.make_windows_line_endings(exstr)

        # If the String shall be given to STDOUT
        if g.config.vars.General['write_to_stdout']:
            print(exstr)
            logger.info(self.tr("Export to STDOUT was successful"))
        else:
            try:
                with open(save_filename, "w") as stream:
                    stream.write(str_encode(exstr))
                logger.info(self.tr("Export to FILE was successful"))
            except IOError:
                if getattr(g, "window", None) is not None:
                    QMessageBox.warning(g.window,
                                        self.tr("Warning during Export"),
                                        self.tr("Cannot Save the File"))
                else:
                    logger.error("Cannot save G-code output file: %s",
                                 save_filename)

    def _legacy_tool_changes(self, LayerContents):
        """Preserve the original profile traversal and initial Z positioning."""
        exstr = ""

        # Move Machine to retraction Area before continuing anything.
        # Note: none of the changes done in the GUI can affect this height,
        #       only the config file can do so (intended)
        exstr += self.rap_pos_z(g.config.vars.Depth_Coordinates['axis3_retract'])

        previous_tool = None
        # Do the export for each LayerContent in LayerContents List
        for LayerContent in LayerContents.non_break_layer_iter():
            logger.debug(self.tr("Beginning export of Layer Nr. %s, Name %s")
                         % (LayerContent.nr, LayerContent.name))
            logger.debug(self.tr("Nr. of Shapes %s; Nr. of Shapes in Route %s")
                         % (len(LayerContent.shapes), len(LayerContent.exp_order_complete)))

            # Perform export only for Layers which have at least 1 Shape to export
            if len(LayerContent.exp_order_complete):
                exstr += self.commentprint("*** LAYER: %s ***" % LayerContent.name)

                for shape_nr in LayerContent.exp_order_complete:
                    shape = LayerContent.shapes[shape_nr]
                    from dxf2gcode.domain.project.tool_settings import effective_tool
                    tool = effective_tool(shape, LayerContent)
                    if tool.tool_nr != previous_tool:
                        exstr += self.chg_tool(tool.tool_nr, tool.speed)
                        previous_tool = tool.tool_nr
                    logger.debug(self.tr("Beginning export of Shape Nr: %s") % shape.nr)

                    exstr += self.commentprint("* SHAPE Nr: %i *" % shape.nr)

                    exstr += self.write_shape_gcode(shape)

        return exstr

    def _managed_tool_changes(self, layers):
        """Render declared macros around plans prepared once at the boundary."""
        from dxf2gcode.adapters.postprocessor.tool_change import ToolChangeMacro, ToolChangeError
        from dxf2gcode.application.toolpath.tool_change import ToolChangeContext
        from dxf2gcode.domain.project.tool_settings import effective_tool
        from dxf2gcode.domain.toolpath.customgcode import CustomGCode

        if g.config.machine_type != 'milling' or self.vars.General['output_type'] != 'g-code':
            raise ToolChangeError('Managed tool-change macros currently require milling G-code')
        service = self._get_shape_export_use_case()
        prepared = []
        for layer in layers.non_break_layer_iter():
            entries = []
            for index in layer.exp_order_complete:
                shape = layer.shapes[index]
                if isinstance(shape, CustomGCode):
                    raise ToolChangeError('Managed tool-change export does not support opaque Custom G-Code rows')
                result = service.prepare(shape, self)
                if result.plan is None or result.has_errors:
                    raise ToolChangeError('Cannot prepare tool-change entry for shape %s', shape.nr)
                entries.append((shape, result))
            prepared.append((layer, entries))

        output = []
        previous_tool = None
        macro = ToolChangeMacro(self)
        for layer, entries in prepared:
            if entries:
                output.append(self.commentprint('*** LAYER: %s ***' % layer.name))
            for shape, result in entries:
                tool = effective_tool(shape, layer)
                if tool.tool_nr != previous_tool:
                    start = next((action.args[0] for action in result.plan.actions
                                  if action.kind == 'rapid_xy'), result.plan.approach_xy)
                    context = ToolChangeContext(
                        tool.tool_nr, previous_tool, tool.speed, start,
                        result.plan.retract_depth,
                        g.config.vars.Depth_Coordinates['axis3_retract'],
                        g.config.metric == 1)
                    output.append(macro.expand(context))
                    previous_tool = tool.tool_nr
                output.append(self.commentprint('* SHAPE Nr: %i *' % shape.nr))
                output.append(service.export_prepared(result, self))
        return ''.join(output)

    def write_shape_gcode(self, shape):
        """Export a shape through the application toolpath boundary."""
        return self._get_shape_export_use_case().execute(shape, self)

    def _get_shape_export_use_case(self):
        """Return the shared application toolpath service and exporters."""
        exporter = getattr(self, "_shape_export_use_case", None)
        if exporter is None:
            from dxf2gcode.adapters.toolpath.gcode_exporter import (
                ToolpathGCodeExporter)
            from dxf2gcode.adapters.toolpath.planning import (
                ShapePlanningInputs, exit_geometry)
            from dxf2gcode.domain.toolpath.planner import ToolpathPlanner
            from dxf2gcode.application.toolpath.exporting import ExportShape
            from dxf2gcode.application.toolpath.planning import PlanToolpath

            exporter = ExportShape(
                plan_toolpath=PlanToolpath(
                    ToolpathPlanner(exit_geometry),
                    ShapePlanningInputs(lambda: g.config).request),
                plan_exporter=ToolpathGCodeExporter(),
                diagnostic_sink=self.add_planning_diagnostic,
            )
            self._shape_export_use_case = exporter
        return exporter

    def plan_shape_toolpath(self, shape):
        """Return a plan through the same application service used by export."""
        return self._get_shape_export_use_case().plan_shape(shape, self)

    def initialize_export_vars(self):
        """Snapshot output settings and reset formatting state before export."""
        plane = g.config.vars.Plane_Coordinates
        ProfileDialect.__init__(
            self, self.vars,
            start_xy=(plane['axis1_start_end'], plane['axis2_start_end']),
            start_z=g.config.vars.Depth_Coordinates['axis3_retract'],
            diameter_factor=2 if g.config.machine_type == 'lathe' else 1)
        self.export_errors = []
        self.export_failed = False
        self.planning_diagnostics = []

    def write_gcode_be(self, load_filename):
        """
        Adding the begin to a new variable. If the exported file is from the
        type g-code in addition the dxf- filename, dxf2gcode version etc. is
        added to the code. Otherwise just the defined text in the PostProcessor
        file is added.
        @param load_filename: The name of the original dxf filename to append
        it to the begin for information.
        @return: The Function returns the begin of the new string to be
        exported.
        """
        if self.vars.General["output_type"] == 'g-code':
            info = get_version_info()
            # RS274 comments cannot contain nested parentheses.
            version = "%s [%s]" % (info.version, c.RUNTIME_VERSION)
            date = info.commit_date or info.build_date or "unavailable"
            exstr = self.tr("(Generated with: %s)\n(Version: %s, Date: %s)\n") % (c.APPNAME, version, date)
            exstr += self.tr("(Created from file: %s)\n") % re.sub('[()]', '_', load_filename)
            exstr += self.tr("(Used Postprocessor: %s) \n") % (self.postpro_file_used)
            if self.vars.General["output_text"]:
                exstr += self.tr("(Output format description: %s)\n") % re.sub('[()]', '', self.vars.General["output_text"])
            exstr += self.tr("(Time: %s)\n") % time.asctime()
        elif self.vars.General["output_type"] == 'dxf':
            exstr = ''
        else:
            exstr = ''

        # In addition the text defined in the PostProcessor Config file is
        # added.
        if g.config.metric == 0:
            exstr += "%s\n" % self.vars.General["code_begin_units_in"]
        else:
            exstr += "%s\n" % self.vars.General["code_begin_units_mm"]
        if self.abs_export:
            exstr += "%s\n" % self.vars.General["code_begin_prog_abs"]
        else:
            exstr += "%s\n" % self.vars.General["code_begin_prog_inc"]
        exstr += "%s\n" % self.vars.General["code_begin"]

        return self.make_print_str(exstr)
