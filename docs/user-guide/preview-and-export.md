# Preview and export

Use three views of a prepared operation together: the original drawing,
the planned tool motion and the exported controller program. Each answers a
different question.

## Read the 2D display

The original contour remains the geometry used for selection. The toolpath
preview adds compensation, pocket clearing, leads and overcut where applicable.
The [compensated rectangle example](compensation-and-leads.md#inspect-a-concrete-software-compensation-example)
shows how these layers relate.

| Display element in the current 2D view | Meaning |
| --- | --- |
| Original contour | Input geometry; selection/mode can change its colour |
| Blue solid path | Prepared contour/tool path |
| Light-blue internal paths | Pocket clearing |
| Orange dashed path | Lead-in geometry |
| Orange dashed circle | Tool radius at entry, when enabled |
| Magenta dashed path | Lead-out/overcut detail |
| Dark dotted paths | Planned rapid/travel portions where represented |
| Red warning marker | A preparation/planning problem; inspect its message |

The example's selected original rectangle is red. Unselected originals and
disabled geometry use other styles. Colours alone are insufficient to identify
a machining mode; check the selection, settings and tooltips. This table is
specific to 2D and does not define 3D colours.

The tool-entry circle is a display aid, not another circular movement. With
machine compensation its position is approximate. Its visibility is controlled
by the general configuration's 2D tool-circle option.

## Understand depth and profile differences

Repeated passes at the same XY coordinates overlap in 2D. The 3D projection
retains depth movements, but neither projection simulates a real controller,
material removal or collision clearance. Check top, final depth, infeed,
retraction and safety margin numerically as well.

Preview and export consume the same planning model, so a changed lead or offset
should have a consistent explanation in both. They can still be prepared using
different postprocessor capabilities: the preview uses its currently loaded
profile, or a default preview profile, while export uses the output type chosen
in the save dialog. Changing that selection can affect drilling repetitions,
compensation handling, arcs and other emitted actions. Compare like-for-like
profiles before diagnosing a mismatch.

A layer or contour edit requests a fresh preview. It does not automatically
mean “optimize the route”. [Route arrows](route-optimization.md) are a separate
display of inter-operation order.

## Export the intended order

1. Confirm the enable checkboxes, tree order and applicable machining settings.
2. Read warnings and resolve blocking conflicts.
3. Choose **Export → Export Shapes without Optimization**, or deliberately use
   **Optimize and Export Shapes** when you want reordering.
4. Select the postprocessor/output type in the export dialog and save the file.
5. Inspect the generated program and operation sequence.

For the illustrated software-compensated rectangle, expect the offset centre
path to be programmed in G40. In machine compensation, expect nominal geometry
with the required G41/G42 build-up movement. A drawing coloured for G41 is not
proof that the output must contain G41 in both compensation modes.

Check units and absolute/incremental mode, depth/feed values, compensation,
tool changes, spindle/coolant actions and the ending sequence. A preview does
not display every macro or literal custom G-code action in the same way as
geometry. Empty, missing or partial operations require investigation even when
the export creates a file.

Use [First DXF to G-code](../getting-started/first-dxf-to-gcode.md) for a
step-by-step file-export demonstration. If something differs, consult
[Toolpath diagnostics](toolpath-diagnostics.md), then preserve a small DXF,
the D2G preparation and relevant profiles for a reproducible report.
