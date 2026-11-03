# Troubleshooting and FAQ

Start with the message pane, current machine mode and units. Keep a copy of
the DXF and D2G preparation before changing import settings or moving files.
For individual path warnings, see [Toolpath diagnostics](toolpath-diagnostics.md).

## Why is geometry missing after import?

Check the message counts and unsupported-entity messages. Optional filters can
exclude IGNORE layers or layer 0, and block-layer assignment can change which
layer contains geometry. A disabled shape can also be hidden by the display
setting even though it exists in the tree. See
[import options](import-and-projects.md#units-connections-and-import-options).

## Why does the size or depth look wrong?

Check the mm/inch labels against a known drawing dimension. Do not correct
an import-unit problem by guessing a cutting depth. Confirm workpiece top and
final Z as coordinates, not unsigned thicknesses. Lathe mode has a separate
[radius/diameter output convention](machine-modes.md#lathe-check-the-coordinate-convention).

## Why did export include an unselected shape?

Selection controls inspection/editing; enable checkboxes control export.
Normal export follows enabled tree rows. **Optimal path** is an optimizer
choice, not the export-enable checkbox. See
[tree order](shapes-layers-and-order.md) and [route optimization](route-optimization.md).

## Why did a setting change after opening a project?

A D2G project restores preparation values and its saved machine type. It
references an external drawing; it is not an embedded DXF or complete machine
configuration. After CAD changes, geometry matching may fail and new contours
may use defaults. See [project restoration](import-and-projects.md#reload-and-changed-drawings).

## Why are parameters grey or marked Different?

Grey standard numeric values can still be editable. **Different** indicates
mixed values or applicability. Select one compatible contour to inspect it,
or enter a common value deliberately if the shared field is enabled. See
[parameter states](machining-parameters.md#read-shared-and-mixed-values).

## Why does a lead or pocket have no effect?

Check the effective tool dimensions, chosen method, contour closure and
compensation mode. An unused lead dimension changes nothing. A zero-length
overcut adds no continuation. A failed pocket calculation can leave a boundary
without clearing the interior. Check the relevant
[diagnostic](toolpath-diagnostics.md), not just whether a file was saved.

## Why did the window not switch to the new profile?

A configuration-profile switch takes effect at restart. A new profile begins
with factory defaults and does not copy the current profile. Check the active
profile indication and startup folder message. CLI jobs should use an explicit
`--cfg` to avoid depending on the last GUI selection.

## Why does the application request a restart?

2D/3D mode and logging changes require restart. Applied changes produce a
notice; after confirmation and closing configuration, the application restarts
with an empty drawing window. Save your preparation first. A machine-type
change refreshes the current drawing and does not require that restart.
See [when settings take effect](application-settings.md#when-settings-take-effect).

## Why does PDF or PS import fail?

The chooser accepts these extensions, but conversion needs `pdftops` and/or
`pstoedit` installed with correct executable paths and options. Check the
conversion error and exit status. `pdf2ps` is not the configured `pdftops`
stage. A scanned picture does not become a vector contour automatically.

## Where should I report a problem?

Use the [user forum](https://www.ltspiceusers.ch/forums/english-section.67/)
for operating questions, [GitHub issue forms](https://github.com/dxf2gcode/dxf2gcode/issues/new/choose)
for reproducible application defects or documentation improvements, and the
[Linux installer tracker](https://github.com/dxf2gcode/dxf2gcode_installer/issues)
for that installation script.

Include version, operating system/install method, exact steps, expected result,
actual result and relevant messages. Attach a minimal DXF and its D2G project
when preparation matters. Add the active application configuration and actual
postprocessor when relevant; their
[Windows/Linux locations](application-settings.md#configuration-files)
are documented. ZIP related files if the attachment form rejects an extension.
Review personal paths and private drawing content before posting.

Descriptions in the issue forms may be written in English or German. A feature
request should explain the intended workflow, current limitation and desired
behaviour; a runnable failing drawing is useful for a defect but not required
for every proposal.
