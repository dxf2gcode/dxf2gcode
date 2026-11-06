# Toolpath diagnostics

If a movement is missing, inspect the selected contour's warning tooltip and
the message pane before altering geometry. Save a copy of the preparation
first. A warning, a blocked plan and a contour intentionally removed by an
offset are different outcomes.

## Machining conflicts

A contour cannot drill while also pocket milling or using G41/G42. Projects
containing such combinations retain their values and report the conflict.
The affected contour has no exportable plan until you choose a compatible
operation explicitly.

Select the contour and use its context menu to enable **Drill Bore**, enable
**Pocket Mill**, or choose the intended **Cutter Compensation**. Each deliberate
choice applies the compatible transition described in
[Contours, pockets and drilling](contours-pockets-and-drilling.md#compatible-mode-changes).
Check the resulting settings rather than dismissing the warning and assuming
the application selected an operation for you.

## Unsupported pocket settings

Pocket milling requires milling mode with software compensation. Projects
loaded with pockets in lathe, drag-knife or machine-compensation mode retain
their values and report the unsupported combination. Switch to a supported
mode or explicitly disable pocketing. Machine and compensation changes refresh
the plan and warning; dismissing a dialog does not repair the settings.

If any enabled contour has a blocking planning error, the entire export is
rejected before writing. An existing target file remains unchanged and stdout
is empty. Resolve the error or deliberately disable that contour, then export
again. Nonblocking warnings can still accompany a valid plan.

## Missing or invalid leads

| Symptom | Check |
| --- | --- |
| Machine G41/G42 with no entry | Choose an entry with XY movement; None cannot build machine compensation |
| Arc/radius warning | Compare workpiece radius with tool radius, compensation side and selected lead method |
| No change after editing a dimension | Check that the selected method uses that dimension and that the effective tool/layer is the one you edited |
| Overcut absent | Check contour closure, enablement and a nonzero overcut length |
| Entry or exit error | Read the specific geometry/parameter message; a blocking error rejects the entire export |

Choosing a straight method does not require an unused arc radius. Conversely,
increasing a radius arbitrarily can move a lead into another part of the work.
Review the [lead definitions](compensation-and-leads.md#choose-lead-in-and-lead-out-methods).

## Offset and pocket failures

An inward offset can legitimately remove a region narrower than the tool.
An empty result is not always that case: an incomplete calculation, unsupported
geometry or an unknown failure must not be interpreted as proof that the tool
does not fit. Read the reported classification and preserve the example for
investigation when the result is unexplained.

Check tool diameter, additional milling offset, contour closure, side and
direction. If a pocket calculation fails, the application reports it and
discards the failed clearing portion; a remaining boundary is not a cleared
pocket. Inspect both messages and actual planned/output movements.

## Depth warnings and unexpected output

Check that infeed is nonzero, final depth is not above the workpiece top and
the first infeed does not go below the requested final depth. These depth
messages can be warnings; correct the inputs even if export remains possible.

For a preview/export difference, compare the postprocessor used by each,
software versus machine compensation, shape enablement and tree order.
For a 2D “missing second pass”, check whether both passes simply overlap in XY.

## Report a reproducible problem

Use the [GitHub issue forms](https://github.com/dxf2gcode/dxf2gcode/issues/new/choose)
for a defect, or the [user forum](https://www.ltspiceusers.ch/forums/english-section.67/)
for usage questions. Include the application version, machine mode, units,
exact action, relevant message and expected/actual result. Attach a minimal
DXF, its D2G preparation and relevant configuration/postprocessor when needed.
Review personal paths before sharing attachments.

Return to [Preview and export](preview-and-export.md).
