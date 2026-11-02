"""Qt widget definitions for application and postprocessor settings."""

from collections import OrderedDict

from dxf2gcode.presentation.qt.qt_compat import QtCore
from dxf2gcode.presentation.qt.qt_compat.QtCore import QT_TRANSLATE_NOOP

# Local tr callbacks choose runtime contexts. Mark each literal explicitly so
# both pylupdate versions extract it in that same context after this relocation.
from dxf2gcode.presentation.qt.toolpath_labels import lead_mode_labels
from dxf2gcode.presentation.qt.configwindow import (
    CfgCheckBox,
    CfgComboBox,
    CfgDoubleSpinBox,
    CfgLineEdit,
    CfgListEdit,
    CfgNote,
    CfgSpinBox,
    CfgSubtitle,
    CfgTableCustomActions,
    CfgTableToolParameters,
    CfgTextEdit,
)


def build_application_config_widgets(config):
    """Build Qt controls for the current application configuration model."""
    tr = config.tr
    coordinate_unit = tr(QT_TRANSLATE_NOOP('MyConfig', " mm")) if config.tool_units == "mm" else tr(QT_TRANSLATE_NOOP('MyConfig', " in"))
    speed_unit = tr(QT_TRANSLATE_NOOP('MyConfig', " mm/min")) if config.tool_units == "mm" else tr(QT_TRANSLATE_NOOP('MyConfig', " IPS"))
    log_levels = {
        "DEBUG": tr(QT_TRANSLATE_NOOP('MyConfig', "Debug")), "INFO": tr(QT_TRANSLATE_NOOP('MyConfig', "Information")),
        "WARNING": tr(QT_TRANSLATE_NOOP('MyConfig', "Warning")), "ERROR": tr(QT_TRANSLATE_NOOP('MyConfig', "Error")),
        "CRITICAL": tr(QT_TRANSLATE_NOOP('MyConfig', "Critical")),
    }
    widgets = OrderedDict([
        ("__section_title__", {
            "Tool_Parameters": tr(QT_TRANSLATE_NOOP('MyConfig', "Tools table")),
            "Custom_Actions": tr(QT_TRANSLATE_NOOP('MyConfig', "Custom actions")),
        }),
        ("Paths", OrderedDict([
            ("__section_title__", tr(QT_TRANSLATE_NOOP('MyConfig', "Software config"))),
            ("import_dir", CfgLineEdit(tr(QT_TRANSLATE_NOOP('MyConfig', "By default look for DXF files in:")))),
            ("output_dir", CfgLineEdit(tr(QT_TRANSLATE_NOOP('MyConfig', "By default export generated G-Code to:")))),
            ("project_dir", CfgLineEdit(tr(QT_TRANSLATE_NOOP('MyConfig', "By default save Project files to:")))),
            ("autosave_path", CfgCheckBox(tr(QT_TRANSLATE_NOOP('MyConfig', "Update paths with last used path: ")))),
        ])),
        ("Filters", OrderedDict([
            ("__section_title__", tr(QT_TRANSLATE_NOOP('MyConfig', "Software config"))),
            ("__subtitle__", CfgSubtitle("pdftops")),
            ("pdftops_cmd", CfgLineEdit(tr(QT_TRANSLATE_NOOP('MyConfig', "Location of executable:")))),
            ("pdftops_opt", CfgListEdit(tr(QT_TRANSLATE_NOOP('MyConfig', "Command-line options:")), ",")),
            ("__subtitle2__", CfgSubtitle("pstoedit")),
            ("pstoedit_cmd", CfgLineEdit(tr(QT_TRANSLATE_NOOP('MyConfig', "Location of executable:")))),
            ("pstoedit_opt", CfgListEdit(tr(QT_TRANSLATE_NOOP('MyConfig', "Command-line options:")), ",")),
        ])),
        ("General", OrderedDict([
            ("__section_title__", tr(QT_TRANSLATE_NOOP('MyConfig', "General settings"))),
            ("__intro__", CfgNote(tr(QT_TRANSLATE_NOOP('MyConfig', "The controls show the loaded profile values. A new profile starts with factory defaults; it does not copy this profile.")))),
            ("mode3d", CfgCheckBox(tr(QT_TRANSLATE_NOOP('MyConfig', "3D mode (requires OpenGL - restart needed)")))),
            ("show_disabled_paths", CfgCheckBox(tr(QT_TRANSLATE_NOOP('MyConfig', "Show disabled paths")))),
            ("live_update_export_route", CfgCheckBox(tr(QT_TRANSLATE_NOOP('MyConfig', "Update export route live")))),
            ("show_scale_bar", CfgCheckBox(tr(QT_TRANSLATE_NOOP('MyConfig', "Show a scale bar in the canvas")))),
            ("expand_layers_on_load", CfgCheckBox(
                QtCore.QCoreApplication.translate(
                    "MyConfig", "Expand layers when loading a drawing"))),
            ("__subtitle2__", CfgSubtitle(tr(QT_TRANSLATE_NOOP('MyConfig', "Milling")))),
            ("split_line_segments", CfgCheckBox(tr(QT_TRANSLATE_NOOP('MyConfig', "Split imported line segments")))),
            ("automatic_cutter_compensation", CfgCheckBox(tr(QT_TRANSLATE_NOOP('MyConfig', "Automatic cutter compensation")))),
            ("machine_type", CfgComboBox(tr(QT_TRANSLATE_NOOP('MyConfig', "Machine type:")), item_labels={
                "milling": tr(QT_TRANSLATE_NOOP('MyConfig', "Milling")), "lathe": tr(QT_TRANSLATE_NOOP('MyConfig', "Lathe")),
                "drag_knife": tr(QT_TRANSLATE_NOOP('MyConfig', "Drag knife")),
            })),
            ("tool_units", CfgComboBox(tr(QT_TRANSLATE_NOOP('MyConfig', "Configuration values use the unit:")), item_labels={
                "mm": tr(QT_TRANSLATE_NOOP('MyConfig', "Millimeters (mm)")), "in": tr(QT_TRANSLATE_NOOP('MyConfig', "Inches (in)")),
            })),
            ("__subtitle3__", CfgSubtitle(tr(QT_TRANSLATE_NOOP('MyConfig', "Output")))),
            ("write_to_stdout", CfgCheckBox(tr(QT_TRANSLATE_NOOP('MyConfig', "Export the G-Code to stdout (instead of a file)")))),
        ])),
        ("Axis_letters", OrderedDict([
            ("__section_title__", tr(QT_TRANSLATE_NOOP('MyConfig', "Machine config"))),
            ("__subtitle__", CfgSubtitle(tr(QT_TRANSLATE_NOOP('MyConfig', "Axes' identifiers")))),
            ("ax1_letter", CfgLineEdit(tr(QT_TRANSLATE_NOOP('MyConfig', "First axis:")))),
            ("ax2_letter", CfgLineEdit(tr(QT_TRANSLATE_NOOP('MyConfig', "Second axis:")))),
            ("ax3_letter", CfgLineEdit(tr(QT_TRANSLATE_NOOP('MyConfig', "Third axis:")))),
        ])),
        ("Plane_Coordinates", OrderedDict([
            ("__section_title__", tr(QT_TRANSLATE_NOOP('MyConfig', "Machine config"))),
            ("__subtitle__", CfgSubtitle(tr(QT_TRANSLATE_NOOP('MyConfig', "Start and end's coordinate and scaling standard multiplier")))),
            ("axis1_start_end", CfgDoubleSpinBox(tr(QT_TRANSLATE_NOOP('MyConfig', "First axis start/end coordiante:")), coordinate_unit)),
            ("axis2_start_end", CfgDoubleSpinBox(tr(QT_TRANSLATE_NOOP('MyConfig', "Second axis start/end coordinate:")), coordinate_unit)),
            ("std_scale", CfgDoubleSpinBox(tr(QT_TRANSLATE_NOOP('MyConfig', "Scale first and second axis:")))),
        ])),
        ("Depth_Coordinates", OrderedDict([
            ("__section_title__", tr(QT_TRANSLATE_NOOP('MyConfig', "Machine config"))),
            ("__subtitle__", CfgSubtitle(tr(QT_TRANSLATE_NOOP('MyConfig', "Third axis' defaults")))),
            ("axis3_retract", CfgDoubleSpinBox(tr(QT_TRANSLATE_NOOP('MyConfig', "Retraction coordinate:")), coordinate_unit)),
            ("axis3_safe_margin", CfgDoubleSpinBox(tr(QT_TRANSLATE_NOOP('MyConfig', "Safety margin:")), coordinate_unit)),
            ("axis3_start_mill_depth", CfgDoubleSpinBox(tr(QT_TRANSLATE_NOOP('MyConfig', "Workpiece origin coordinate:")), coordinate_unit)),
            ("axis3_slice_depth", CfgDoubleSpinBox(tr(QT_TRANSLATE_NOOP('MyConfig', "Slice depth:")), coordinate_unit)),
            ("axis3_mill_depth", CfgDoubleSpinBox(tr(QT_TRANSLATE_NOOP('MyConfig', "Final mill depth:")), coordinate_unit)),
        ])),
        ("Feed_Rates", OrderedDict([
            ("__section_title__", tr(QT_TRANSLATE_NOOP('MyConfig', "Machine config"))),
            ("__subtitle__", CfgSubtitle(tr(QT_TRANSLATE_NOOP('MyConfig', "G1 feed rates")))),
            ("f_g1_plane", CfgDoubleSpinBox(tr(QT_TRANSLATE_NOOP('MyConfig', "First and second axis (2D plane):")), speed_unit)),
            ("f_g1_depth", CfgDoubleSpinBox(tr(QT_TRANSLATE_NOOP('MyConfig', "Third axis:")), speed_unit)),
        ])),
        ("Cutter_Compensation", OrderedDict([
            ("__section_title__", tr(QT_TRANSLATE_NOOP('MyConfig', "Output settings"))),
            ("__subtitle__", CfgSubtitle(tr(QT_TRANSLATE_NOOP('MyConfig', "Cutter compensation")))),
            ("done_by_machine", CfgCheckBox(tr(QT_TRANSLATE_NOOP('MyConfig', "Machine cutter compensation"))).setDescription(tr(QT_TRANSLATE_NOOP('MyConfig', 'Cutter compensation is done by machine (check box if machine reconizes G41 and G42 commands / uncheck otherwise. This also disables pocket milling.)')))),
        ])),
        ("Pocketing", OrderedDict([
            ("__section_title__", tr(QT_TRANSLATE_NOOP('MyConfig', "Output settings"))),
            ("__subtitle__", CfgSubtitle(tr(QT_TRANSLATE_NOOP('MyConfig', "Pocket milling")))),
            ("pocket_edge_clearance", CfgDoubleSpinBox(tr(QT_TRANSLATE_NOOP('MyConfig', "Pocket edge clearance:")), " %", 0, 100, 2).setDescription(tr(QT_TRANSLATE_NOOP('MyConfig', 'Pocket edge clearance (distance between cutting edge and contour, as % of tool diameter):')))),
        ])),
        ("Drag_Knife_Options", OrderedDict([
            ("__section_title__", tr(QT_TRANSLATE_NOOP('MyConfig', "Output settings"))),
            ("__subtitle__", CfgSubtitle(tr(QT_TRANSLATE_NOOP('MyConfig', "Drag Knife options")))),
            ("entry_mode", CfgComboBox(tr(QT_TRANSLATE_NOOP('MyConfig', "Knife orientation before entry:")), item_labels={
                'fixed': tr(QT_TRANSLATE_NOOP('MyConfig', "Assume configured start angle")),
                'previous': tr(QT_TRANSLATE_NOOP('MyConfig', "Retain previous angle (first cut: start angle)")),
                'unknown': tr(QT_TRANSLATE_NOOP('MyConfig', "Unknown: external settling stroke")),
            })),
            ("alignment_length", CfgDoubleSpinBox(tr(QT_TRANSLATE_NOOP('MyConfig', "Alignment length:")), coordinate_unit, 0, None, 4).setDescription(tr(QT_TRANSLATE_NOOP('MyConfig', 'Settling length (verify on the actual knife and material):')))),
            ("return_to_start", CfgCheckBox(tr(QT_TRANSLATE_NOOP('MyConfig', "Return knife to start angle"))).setDescription(tr(QT_TRANSLATE_NOOP('MyConfig', 'Return to start angle in lead out before lifting')))),
            ("swivel_depth", CfgDoubleSpinBox(tr(QT_TRANSLATE_NOOP('MyConfig', "Swivel contact Z:")), coordinate_unit, None, None, 4)),
            ("extra_pass", CfgCheckBox(tr(QT_TRANSLATE_NOOP('MyConfig', "Additional cut at final depth"))).setDescription(tr(QT_TRANSLATE_NOOP('MyConfig', 'One additional complete cut at final depth')))),
            ("alternate", CfgCheckBox(tr(QT_TRANSLATE_NOOP('MyConfig', "Alternate open cuts"))).setDescription(tr(QT_TRANSLATE_NOOP('MyConfig', 'Alternate open cuts using external straight leads')))),
            ("lead_out_length", CfgDoubleSpinBox(tr(QT_TRANSLATE_NOOP('MyConfig', "Knife lead out length:")), coordinate_unit, 0, None, 4).setDescription(tr(QT_TRANSLATE_NOOP('MyConfig', 'Knife lead out length (lead in uses tool lead length):')))),
            ("drag_angle", CfgDoubleSpinBox(tr(QT_TRANSLATE_NOOP('MyConfig', 'Lift for swivels if angle exceeds:')), "°")),
            ("drag_start_angle", CfgDoubleSpinBox(tr(QT_TRANSLATE_NOOP('MyConfig', "Initial knife angle:")), "°").setDescription(tr(QT_TRANSLATE_NOOP('MyConfig', 'Direction the knife points to when the cut starts (0 = positive X axis):')))),
            ("ramp_in_length", CfgDoubleSpinBox(tr(QT_TRANSLATE_NOOP('MyConfig', "Ramp length (0 = vertical plunge):")), coordinate_unit, 0, None, 4)),
        ])),
        ("Lead_In_Out", OrderedDict([
            ("__section_title__", tr(QT_TRANSLATE_NOOP('MyConfig', "Output settings"))),
            ("__subtitle__", CfgSubtitle(tr(QT_TRANSLATE_NOOP('MyConfig', "Lead in / lead out")))),
            ("lead_in_mode", CfgComboBox(tr(QT_TRANSLATE_NOOP('MyConfig', "Default lead in at the start of the contour:")), item_labels=lead_mode_labels())),
            ("lead_out_mode", CfgComboBox(tr(QT_TRANSLATE_NOOP('MyConfig', "Default lead out at the end of the contour:")), item_labels=lead_mode_labels())),
            ("overcut_enabled", CfgCheckBox(tr(QT_TRANSLATE_NOOP('MyConfig', "Overcut closed contours"))).setDescription(tr(QT_TRANSLATE_NOOP('MyConfig', 'Overcut: continue the cut along the contour beyond the closing point (closed contours only) - the length is defined per tool in the tools table')))),
        ])),
        ("Route_Optimisation", OrderedDict([
            ("__section_title__", tr(QT_TRANSLATE_NOOP('MyConfig', "Output settings"))),
            ("__subtitle__", CfgSubtitle(tr(QT_TRANSLATE_NOOP('MyConfig', "TSP optimizer")))),
            ("default_TSP", CfgCheckBox(tr(QT_TRANSLATE_NOOP('MyConfig', "Allow optimization for new shapes")))),
            ("TSP_shape_order", CfgComboBox(tr(QT_TRANSLATE_NOOP('MyConfig', "Optimizer behaviour:")), item_labels={
                "CONSTRAIN_ORDER_ONLY": tr(QT_TRANSLATE_NOOP('MyConfig', "Keep fixed shapes in relative order")),
                "CONSTRAIN_PLACE_AFTER": tr(QT_TRANSLATE_NOOP('MyConfig', "Place optimized shapes after fixed shapes")),
            })),
            ("mutation_rate", CfgDoubleSpinBox(tr(QT_TRANSLATE_NOOP('MyConfig', "Mutation rate:")))),
            ("max_population", CfgSpinBox(tr(QT_TRANSLATE_NOOP('MyConfig', "Max population:")))),
            ("max_iterations", CfgSpinBox(tr(QT_TRANSLATE_NOOP('MyConfig', "Max iterations:")))),
            ("begin_art", CfgComboBox(tr(QT_TRANSLATE_NOOP('MyConfig', "Starting point:")), item_labels={
                "ordered": tr(QT_TRANSLATE_NOOP('MyConfig', "Current order")), "random": tr(QT_TRANSLATE_NOOP('MyConfig', "Random")),
                "heuristic": tr(QT_TRANSLATE_NOOP('MyConfig', "Nearest neighbor")),
            })),
        ])),
        ("Import_Parameters", OrderedDict([
            ("__section_title__", tr(QT_TRANSLATE_NOOP('MyConfig', "Output settings"))),
            ("point_tolerance", CfgDoubleSpinBox(tr(QT_TRANSLATE_NOOP('MyConfig', "DXF default import point tolerance:")), "", None, None, 5)),
            ("spline_check", CfgSpinBox(tr(QT_TRANSLATE_NOOP('MyConfig', "DXF import spline check:")))),
            ("fitting_tolerance", CfgDoubleSpinBox(tr(QT_TRANSLATE_NOOP('MyConfig', "DXF default import fit tolerance:")), "", None, None, 5)),
            ("insert_at_block_layer", CfgCheckBox(tr(QT_TRANSLATE_NOOP('MyConfig', "Import inserted entities on block layer"))).setDescription(tr(QT_TRANSLATE_NOOP('MyConfig', 'insert elements which are part of a block to layer where the block is inserted')))),
            ("exclude_ignore_layers", CfgCheckBox(QtCore.QCoreApplication.translate(
                "MyConfig", "Do not import IGNORE layers"))),
            ("exclude_layer_zero", CfgCheckBox(QtCore.QCoreApplication.translate(
                "MyConfig", "Do not import layer 0"))),
        ])),
        ("Layer_Options", OrderedDict([
            ("__section_title__", tr(QT_TRANSLATE_NOOP('MyConfig', "Parameter names"))),
            ("__intro__", CfgNote(tr(QT_TRANSLATE_NOOP('MyConfig', "These names identify parameters in DXF layer names. Enter multiple names per parameter separated by commas.")))),
            ("id_float_separator", CfgLineEdit(tr(QT_TRANSLATE_NOOP('MyConfig', "Separator between identifier and value:")))),
            ("__subtitle__", CfgSubtitle(tr(QT_TRANSLATE_NOOP('MyConfig', "Parameters' identifiers")))),
            ("mill_depth_identifiers", CfgListEdit(tr(QT_TRANSLATE_NOOP('MyConfig', "Final mill depth:")), ",")),
            ("slice_depth_identifiers", CfgListEdit(tr(QT_TRANSLATE_NOOP('MyConfig', "Infeed depth:")), ",")),
            ("start_mill_depth_identifiers", CfgListEdit(tr(QT_TRANSLATE_NOOP('MyConfig', "Workpiece top:")), ",")),
            ("retract_identifiers", CfgListEdit(tr(QT_TRANSLATE_NOOP('MyConfig', "Retraction area:")), ",")),
            ("safe_margin_identifiers", CfgListEdit(tr(QT_TRANSLATE_NOOP('MyConfig', "Safety margin:")), ",")),
            ("f_g1_plane_identifiers", CfgListEdit(tr(QT_TRANSLATE_NOOP('MyConfig', "XY feed rate:")), ",").setDescription(tr(QT_TRANSLATE_NOOP('MyConfig', 'G1 feed rate for first and second axis (2D plane):')))),
            ("f_g1_depth_identifiers", CfgListEdit(tr(QT_TRANSLATE_NOOP('MyConfig', "Z feed rate:")), ",").setDescription(tr(QT_TRANSLATE_NOOP('MyConfig', 'G1 feed rate for third axis:')))),
            ("tool_nr_identifiers", CfgListEdit(tr(QT_TRANSLATE_NOOP('MyConfig', "Tool number:")), ",")),
            ("tool_diameter_identifiers", CfgListEdit(tr(QT_TRANSLATE_NOOP('MyConfig', "Tool diameter:")), ",")),
            ("spindle_speed_identifiers", CfgListEdit(tr(QT_TRANSLATE_NOOP('MyConfig', "Spindle speed:")), ",")),
            ("start_radius_identifiers", CfgListEdit(tr(QT_TRANSLATE_NOOP('MyConfig', "Legacy start radius:")), ",").setDescription(tr(QT_TRANSLATE_NOOP('MyConfig', 'Start radius (cutter compensation, deprecated - use the lead radius instead):')))),
            ("milling_offset_identifiers", CfgListEdit(tr(QT_TRANSLATE_NOOP('MyConfig', "Finishing allowance:")), ",").setDescription(tr(QT_TRANSLATE_NOOP('MyConfig', 'Additional offset (finishing allowance):')))),
            ("lead_in_mode_identifiers", CfgListEdit(tr(QT_TRANSLATE_NOOP('MyConfig', "Lead in mode:")), ",").setDescription(tr(QT_TRANSLATE_NOOP('MyConfig', 'Lead in mode (0 = start move, 1 = off, 2 = straight, 3 = radius, 4 = configuration default):')))),
            ("lead_out_mode_identifiers", CfgListEdit(tr(QT_TRANSLATE_NOOP('MyConfig', "Lead out mode:")), ",").setDescription(tr(QT_TRANSLATE_NOOP('MyConfig', 'Lead out mode (0 = off, 1 = straight, 2 = radius, 3 = start move, 4 = configuration default):')))),
            ("lead_radius_identifiers", CfgListEdit(tr(QT_TRANSLATE_NOOP('MyConfig', "Lead radius:")), ",").setDescription(tr(QT_TRANSLATE_NOOP('MyConfig', 'Common lead in / lead out radius at the workpiece:')))),
            ("lead_length_identifiers", CfgListEdit(tr(QT_TRANSLATE_NOOP('MyConfig', "Straight lead length:")), ",").setDescription(tr(QT_TRANSLATE_NOOP('MyConfig', 'Common lead in / lead out length of the straight part:')))),
            ("overcut_length_identifiers", CfgListEdit(tr(QT_TRANSLATE_NOOP('MyConfig', "Overcut length:")), ",")),
        ])),
        ("Tool_Parameters", CfgTableToolParameters(tr(QT_TRANSLATE_NOOP('MyConfig', "Define the tools here:")), knife_offset=lambda: config.machine_type == 'drag_knife')),
        ("Custom_Actions", CfgTableCustomActions(tr(QT_TRANSLATE_NOOP('MyConfig', "Define here custom GCODE that can be inserted anywhere in the program:")))),
        ("Logging", OrderedDict([
            ("__section_title__", tr(QT_TRANSLATE_NOOP('MyConfig', "Software config"))),
            ("logfile", CfgLineEdit(tr(QT_TRANSLATE_NOOP('MyConfig', "File used for logging (restart needed):")))),
            ("console_loglevel", CfgComboBox(tr(QT_TRANSLATE_NOOP('MyConfig', "On stderr console log messages with importance minimal to level (restart needed):")), item_labels=log_levels)),
            ("file_loglevel", CfgComboBox(tr(QT_TRANSLATE_NOOP('MyConfig', "For log-file log messages with importance minimal to level (restart needed):")), item_labels=log_levels)),
            ("window_loglevel", CfgComboBox(tr(QT_TRANSLATE_NOOP('MyConfig', "For message box log messages with importance minimal to level (restart needed):")), item_labels=log_levels)),
        ])),
    ])
    from validate import Validator
    validator = Validator()
    explanations = {
        ('General', 'show_disabled_paths'): tr(QT_TRANSLATE_NOOP('MyConfig', 'Initial visibility of disabled contours. The View menu can change visibility for the current session.')),
        ('General', 'live_update_export_route'): tr(QT_TRANSLATE_NOOP('MyConfig', 'Initial live display of export connections. Manual route display remains available when live updates are off.')),
        ('General', 'split_line_segments'): tr(QT_TRANSLATE_NOOP('MyConfig', 'Used when importing DXF line segments. Saved projects retain their own import settings.')),
        ('General', 'automatic_cutter_compensation'): tr(QT_TRANSLATE_NOOP('MyConfig', 'Controls automatic compensation selection for imported contours. Contour settings and saved projects are separate from this profile default.')),
        ('General', 'machine_type'): tr(QT_TRANSLATE_NOOP('MyConfig', 'Applies the machine type to the current drawing and saves it for new sessions. The drawing is rebuilt without restarting the application.')),
        ('Route_Optimisation', 'default_TSP'): tr(QT_TRANSLATE_NOOP('MyConfig', 'Initial optimization permission for new contours. Existing contour permissions are not reset by opening this dialog.')),
    }
    for (section, key), explanation in explanations.items():
        control = widgets[section][key]
        default = validator.get_default_value(config.spec[section][key])
        if isinstance(default, bool):
            label = tr(QT_TRANSLATE_NOOP('MyConfig', 'On')) if default else tr(QT_TRANSLATE_NOOP('MyConfig', 'Off'))
        else:
            label = control.item_labels.get(default, str(default))
        control.setDescription(explanation)
        control.setDefaultHint(tr(QT_TRANSLATE_NOOP('MyConfig', 'Default for new profiles: %s')) % label)
    return widgets


def build_postprocessor_config_widgets(translate):
    """Build Qt controls for the current postprocessor profile schema."""
    tr = translate
    return OrderedDict([
        ("__section_title__", {"Custom_GCode": tr(QT_TRANSLATE_NOOP('MyPostProConfig', "Custom GCode"))}),
        ("General", OrderedDict([
            ("__section_title__", tr(QT_TRANSLATE_NOOP('MyPostProConfig', "Software config"))),
            ("__subtitle__", CfgSubtitle(tr(QT_TRANSLATE_NOOP('MyPostProConfig', "Output specifications")))),
            ("output_text", CfgLineEdit(tr(QT_TRANSLATE_NOOP('MyPostProConfig', "Output format description (should be unique):")))),
            ("output_format", CfgLineEdit(tr(QT_TRANSLATE_NOOP('MyPostProConfig', "Output file extension:")))),
            ("output_type", CfgComboBox(tr(QT_TRANSLATE_NOOP('MyPostProConfig', "Output type:")), item_labels={
                "g-code": "G-code", "dxf": "DXF", "text": tr(QT_TRANSLATE_NOOP('MyPostProConfig', "Text")),
            })),
            ("__subtitle2__", CfgSubtitle(tr(QT_TRANSLATE_NOOP('MyPostProConfig', "Output options")))),
            ("abs_export", CfgCheckBox(tr(QT_TRANSLATE_NOOP('MyPostProConfig', "Export absolute coordinates")))),
            ("cancel_cc_for_depth", CfgCheckBox(tr(QT_TRANSLATE_NOOP('MyPostProConfig', "Cancel cutter compensation at each slice")))),
            ("cc_outside_the_piece", CfgCheckBox(tr(QT_TRANSLATE_NOOP('MyPostProConfig', "Perform cutter compensation outside the piece")))),
            ("export_ccw_arcs_only", CfgCheckBox(tr(QT_TRANSLATE_NOOP('MyPostProConfig', "Export only counter clockwise arcs")))),
            ("max_arc_radius", CfgDoubleSpinBox(tr(QT_TRANSLATE_NOOP('MyPostProConfig', "Maximum arc radius:")))),
            ("export_arcs_as_lines", CfgCheckBox(tr(QT_TRANSLATE_NOOP('MyPostProConfig', "Export all arcs as line seg")))),
            ("repeat_drill_move", CfgCheckBox(tr(QT_TRANSLATE_NOOP('MyPostProConfig', "Repeat Drill move for slices (only use wit abs coordinates)")))),
            ("__subtitle3__", CfgSubtitle(tr(QT_TRANSLATE_NOOP('MyPostProConfig', "G-code constants")))),
            ("code_begin_units_mm", CfgLineEdit(tr(QT_TRANSLATE_NOOP('MyPostProConfig', "Units in millimeters:")))),
            ("code_begin_units_in", CfgLineEdit(tr(QT_TRANSLATE_NOOP('MyPostProConfig', "Units in inch:")))),
            ("code_begin_prog_abs", CfgLineEdit(tr(QT_TRANSLATE_NOOP('MyPostProConfig', "Absolute programming:")))),
            ("code_begin_prog_inc", CfgLineEdit(tr(QT_TRANSLATE_NOOP('MyPostProConfig', "Incremental programming:")))),
            ("code_begin", CfgTextEdit(tr(QT_TRANSLATE_NOOP('MyPostProConfig', "Startup:")))),
            ("code_end", CfgTextEdit(tr(QT_TRANSLATE_NOOP('MyPostProConfig', "End:")))),
        ])),
        ("Number_Format", OrderedDict([
            ("__section_title__", tr(QT_TRANSLATE_NOOP('MyPostProConfig', "Output formatting"))),
            ("__subtitle__", CfgSubtitle(tr(QT_TRANSLATE_NOOP('MyPostProConfig', "Output formatting")))),
            ("win_line_endings", CfgCheckBox(tr(QT_TRANSLATE_NOOP('MyPostProConfig', "Windows line-endings")))),
            ("signed_values", CfgCheckBox(tr(QT_TRANSLATE_NOOP('MyPostProConfig', "Prepend numbers with the '+' sign for positive values")))),
            ("pre_decimals", CfgSpinBox(tr(QT_TRANSLATE_NOOP('MyPostProConfig', "Number of digits before the decimal separator:")))),
            ("pre_decimal_zero_padding", CfgCheckBox(tr(QT_TRANSLATE_NOOP('MyPostProConfig', "Padding with '0' digit before the decimal separator")))),
            ("post_decimals", CfgSpinBox(tr(QT_TRANSLATE_NOOP('MyPostProConfig', "Number of digits after the decimal separator:")))),
            ("post_decimal_zero_padding", CfgCheckBox(tr(QT_TRANSLATE_NOOP('MyPostProConfig', "Padding with '0' digit after the decimal separator")))),
            ("decimal_separator", CfgLineEdit(tr(QT_TRANSLATE_NOOP('MyPostProConfig', "Decimal separator:")))),
        ])),
        ("Line_Numbers", OrderedDict([
            ("__section_title__", tr(QT_TRANSLATE_NOOP('MyPostProConfig', "Output formatting"))),
            ("__subtitle__", CfgSubtitle(tr(QT_TRANSLATE_NOOP('MyPostProConfig', "Line numbers")))),
            ("use_line_nrs", CfgCheckBox(tr(QT_TRANSLATE_NOOP('MyPostProConfig', "Export line numbers")))),
            ("line_nrs_begin", CfgSpinBox(tr(QT_TRANSLATE_NOOP('MyPostProConfig', "Line number starts at:")))),
            ("line_nrs_step", CfgSpinBox(tr(QT_TRANSLATE_NOOP('MyPostProConfig', "Line number step:")))),
        ])),
        ("Program", OrderedDict([
            ("__section_title__", tr(QT_TRANSLATE_NOOP('MyPostProConfig', "G-code codes"))),
            ("tool_change", CfgLineEdit(tr(QT_TRANSLATE_NOOP('MyPostProConfig', "Tool change:")))),
            ("feed_change", CfgLineEdit(tr(QT_TRANSLATE_NOOP('MyPostProConfig', "Feed rate change:")))),
            ("rap_pos_plane", CfgLineEdit(tr(QT_TRANSLATE_NOOP('MyPostProConfig', "Rapid positioning for XY plane:")))),
            ("rap_pos_depth", CfgLineEdit(tr(QT_TRANSLATE_NOOP('MyPostProConfig', "Rapid positioning for Z plane:")))),
            ("lin_mov_plane", CfgLineEdit(tr(QT_TRANSLATE_NOOP('MyPostProConfig', "Linear feed move for XY plane:")))),
            ("lin_mov_xyz", CfgLineEdit(tr(QT_TRANSLATE_NOOP('MyPostProConfig', "Coordinated linear XYZ move:")))),
            ("lin_mov_depth", CfgLineEdit(tr(QT_TRANSLATE_NOOP('MyPostProConfig', "Linear feed move for Z plane:")))),
            ("lin_mov_drill", CfgLineEdit(tr(QT_TRANSLATE_NOOP('MyPostProConfig', "Linear feed move for drilling:")))),
            ("lin_ret_drill", CfgLineEdit(tr(QT_TRANSLATE_NOOP('MyPostProConfig', "Linear retract move during drilling:")))),
            ("arc_int_cw", CfgLineEdit(tr(QT_TRANSLATE_NOOP('MyPostProConfig', "Clockwise feed move:")))),
            ("arc_int_ccw", CfgLineEdit(tr(QT_TRANSLATE_NOOP('MyPostProConfig', "Counter clockwise feed move:")))),
            ("cutter_comp_off", CfgLineEdit(tr(QT_TRANSLATE_NOOP('MyPostProConfig', "Disable cutter compensation:")))),
            ("cutter_comp_left", CfgLineEdit(tr(QT_TRANSLATE_NOOP('MyPostProConfig', "Left cutter compensation:")))),
            ("cutter_comp_right", CfgLineEdit(tr(QT_TRANSLATE_NOOP('MyPostProConfig', "Right cutter compensation:")))),
            ("pre_shape_cut", CfgLineEdit(tr(QT_TRANSLATE_NOOP('MyPostProConfig', "Placed in front of any shape:")))),
            ("post_shape_cut", CfgLineEdit(tr(QT_TRANSLATE_NOOP('MyPostProConfig', "Placed after any shape:")))),
            ("comment", CfgLineEdit(tr(QT_TRANSLATE_NOOP('MyPostProConfig', "Comment for current shape:")))),
        ])),
        ("Tool_Change", OrderedDict([
            ("__section_title__", tr(QT_TRANSLATE_NOOP('MyPostProConfig', "Tool change macro"))),
            ("return_state", CfgComboBox(tr(QT_TRANSLATE_NOOP('MyPostProConfig', "Declared return position:")), item_labels={
                "legacy": tr(QT_TRANSLATE_NOOP('MyPostProConfig', "Legacy (unchanged output)")),
                "next_start_at_retract": tr(QT_TRANSLATE_NOOP('MyPostProConfig', "Next start at retract height")),
            })),
            ("end_distance_mode", CfgComboBox(tr(QT_TRANSLATE_NOOP('MyPostProConfig', "Distance mode at macro end:")))),
            ("work_offset", CfgLineEdit(tr(QT_TRANSLATE_NOOP('MyPostProConfig', "Work coordinate system after change:")))),
            ("length_offset_mode", CfgComboBox(tr(QT_TRANSLATE_NOOP('MyPostProConfig', "Tool length offset selection:")), item_labels={
                "none": tr(QT_TRANSLATE_NOOP('MyPostProConfig', "Handled by the macro")),
                "tool_number": tr(QT_TRANSLATE_NOOP('MyPostProConfig', "Offset number equals tool number")),
                "mapping": tr(QT_TRANSLATE_NOOP('MyPostProConfig', "Explicit tool-to-offset mapping")),
            })),
            ("length_offset_mapping", CfgLineEdit(tr(QT_TRANSLATE_NOOP('MyPostProConfig', "Tool-to-offset mapping (1:1,4:8):")))),
        ])),
        ("Custom_GCode", CfgTableCustomActions(tr(QT_TRANSLATE_NOOP('MyPostProConfig', "Define here custom GCODE that can be inserted anywhere in the program:")))),
    ])

