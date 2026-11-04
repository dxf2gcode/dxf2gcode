# Postprocessor reference

A postprocessor describes the output dialect and capabilities. It is separate
from the application profile, machining mode and contour settings. Select its
description in the export dialog; the [CLI](../user-guide/command-line-usage.md)
also selects by description, not by `.cfg` filename.

## Files and compatibility

Use **Options → Postprocessing configuration** to edit postprocessors. Files
live in the active application's `postpro_config` folder; see
[Windows/Linux paths](../user-guide/application-settings.md#configuration-files).
Copy an existing profile under another `.cfg` name before adapting it. Give it
a distinct `General.output_text` so it can be identified during export.

The current schema is **8.3**, accepting versions **8, 8.1, 8.2 and 8.3**.
Schema defaults fill supported missing fields. Older profiles retain the legacy
tool-change contract. Version 8.3 includes coordinated XYZ movement for knife
ramps. This is a format version, not the application version. Preserve originals
when migrating; changing the version tag alone does not convert an incompatible
profile. Invalid syntax may trigger `.bad` recovery and creation of defaults.

## General settings

| Key | Purpose / default |
| --- | --- |
| `output_text` | Description; default `G-CODE for LinuxCNC` |
| `output_format` | Extension; default `.ngc` |
| `output_type` | `g-code`, `dxf` or `text`; not a plugin/module name |
| `abs_export` | Absolute coordinates when true, incremental otherwise |
| `cancel_cc_for_depth` | Cancel/rebuild compensation around axial depth changes |
| `cc_outside_the_piece` | Build compensation before reaching cutting depth |
| `export_ccw_arcs_only` | Special counterclockwise-arc output treatment; not a general G-code optimization |
| `max_arc_radius` | Radius above which arcs are emitted as lines |
| `export_arcs_as_lines` | Approximate arcs with line segments |
| `repeat_drill_move` | Repeat drilling for depth slices rather than once |
| `code_begin_units_mm/in` | Unit declarations |
| `code_begin_prog_abs/inc` | Distance-mode declarations |
| `code_begin`, `code_end` | Program opening/ending text |

The default opening declares G64, G17, G40 and G49; the default ending is M2.
Selecting `text` or `dxf` does not replace inherited G-code templates with a
complete exporter automatically. The profile still needs appropriate opening,
movement and ending templates. See the [examples](../examples/index.md).

## Program templates

| Key | Event |
| --- | --- |
| `tool_change` | First effective tool and subsequent changed tool numbers |
| `feed_change` | Feed update |
| `rap_pos_plane`, `rap_pos_depth` | Rapid planar / axial positioning |
| `lin_mov_plane`, `lin_mov_depth` | Linear planar / axial cut |
| `lin_mov_xyz` | Coordinated XYZ movement, including knife ramps |
| `lin_mov_drill`, `lin_ret_drill` | Drilling / drilling retract |
| `arc_int_cw`, `arc_int_ccw` | Clockwise / counterclockwise arc |
| `cutter_comp_off/left/right` | Compensation mode commands |
| `pre_shape_cut`, `post_shape_cut` | Actions before / after cutting a contour |
| `comment` | Comment formatting |

The default tool change contains `T%tool_nr M6` and spindle speed. Default
pre/post-cut text includes M3/M8 and M9/M5. A controller may require different
commands, order or line placement. In particular, a stock profile does not
automatically establish suitable tool lengths or machine work offsets.

## Movement placeholders

| Placeholder | Value from the current formatting action |
| --- | --- |
| `%XE`, `%YE` | Programmed planar endpoint; absolute or incremental according to the profile |
| `%XS`, `%YS` | Start coordinates supplied to the current geometry action |
| `%ZE`, `%ZS` | Axial endpoint / previous axial value for the applicable movement |
| `%I`, `%J` | Arc centre offset components |
| `%XO`, `%YO`, `%R` | Arc centre and radius |
| `%AngS`, `%AngE`, `%ext` | Arc start/end/sweep angles in degrees |
| `%feed`, `%speed`, `%tool_nr` | Feed, spindle speed and tool number |
| `%comment` | Current comment text |
| `%nl` | Newline |

Negative-coordinate forms such as `%-XE`, `%-YE`, `%-ZE` and negative arc
angle/offset forms are supported where defined by the formatter. A placeholder
uses the current event's state; it is not a general query for arbitrary drawing
values. In lathe mode the second planar position and corresponding centre/offset
components are doubled; see [the coordinate convention](../user-guide/machine-modes.md#lathe-check-the-coordinate-convention).

Use [managed tool-change placeholders](tool-changes.md#macro-parameters) for
tool-change targets. Reusing `%ZE` as a managed return position is rejected;
it could otherwise refer to unrelated earlier movement state.

## Number format, line numbers and custom text

`Number_Format` controls field width, decimal places, decimal separator,
zero padding, explicit signs and Windows line endings. Default output has
three decimal places and a decimal point. These are serialization settings,
not geometry tolerances. `%feed` and `%speed` use integer formatting.

`Line_Numbers.use_line_nrs` enables numbering, with `line_nrs_begin` and
`line_nrs_step` defining the sequence. Do not add G-code line numbers to a
DXF or Python-text example.

`Custom_GCode` contains named text blocks. Application **Custom actions** used
as tree rows are a different mechanism. Literal custom code may change modal
or positional state outside the planner; it is restricted by the managed
[tool-change contract](tool-changes.md).

## Review a modification

Check profile loading, exact description, units/mode, movement semantics and
representative formatted output separately. A successful schema load does not
validate a controller program. Keep the drawing, D2G preparation, profile and
application revision with a reproducible example. No machine-specific template
is implied by a supported schema key.
