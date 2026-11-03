# Route optimization

Route optimization reorders machining operations to reduce travel between
contour endpoints. It works within each layer; it does not solve workholding,
part stability or the machining order required by your process.

Start with the [three-shape example](shapes-layers-and-order.md). Keep the
enable checkboxes on for shapes that belong in the output.

## Choose the action you need

| Action | Effect |
| --- | --- |
| Export Shapes without Optimization | Synchronize the tree order and export enabled rows in that order |
| Optimize Paths | Calculate a route and update the contour order in the tree |
| Optimize and Export Shapes | Optimize, then export the resulting order |
| Live Update Export Route | Control automatic redrawing of the route display after edits |

The first three commands are in the **Export** menu. A normal export also
updates the route display, but does not optimize it. A displayed route is a
visualization of the current sequence; drawing arrows is not an optimization
request. When live display is off, reordering still updates the export order.

After **Optimize Paths**, inspect the new tree order before exporting. A later
normal export retains that resulting order; it does not restore the old manual
one. Save a project before experimenting if you want to reopen the old preparation.

## Constraints and custom rows

The **Optimal path** checkbox releases a contour for free reordering. Unchecked
contours retain their relative order constraints. This does not give each
unchecked contour an immutable absolute row number.

In **Options → Configuration**, the output settings include the route
optimizer's `TSP_shape_order` choice. The two existing modes have different
effects on the tree:

| Mode | Effect |
| --- | --- |
| `CONSTRAIN_ORDER_ONLY` | Apply the computed route to all routed contours, preserving the relative order of constrained contours |
| `CONSTRAIN_PLACE_AFTER` | Keep non-released rows in relative order, then append released contours in their optimized order |

For an explicit example, use contour labels A, B and C from the drawing and
imagine an enabled custom-code row M between A and B. Only B is released for
optimization; A must remain before C. **Assume** the optimizer proposes B, A, C.
This is an explanation of applying a route, not a guaranteed optimizer result
for those coordinates.

| Operation/mode | Resulting enabled rows |
| --- | --- |
| Normal export before optimization | A, M, B, C |
| `CONSTRAIN_ORDER_ONLY` with proposed route B, A, C | M, B, A, C |
| `CONSTRAIN_PLACE_AFTER` with the same proposal | A, M, C, B |

In both modes A remains before C. In neither mode is M a fixed boundary that
all contour movements respect. Check custom actions after optimizing, especially
when they change controller state.

Disabled contours and custom rows are excluded from the enabled export route.
They can remain visible in the tree; their presence is not a machining operation.

## Limits of the route display

The route uses contour start/end positions, including the prepared pocket
endpoints where applicable. It is not a material-removal simulation. It does
not prove that the cutter clears clamps or that an inner part remains attached.
Review [tool motion and export](preview-and-export.md) separately.

The command-line export also has an explicit optimization choice. Saved D2G
ordering and constraints can be used by that path; importing a raw DXF starts
from a newly built model rather than the unsaved GUI tree. GUI drawing arrows
are not a command-line setting. See [Command-line usage](command-line-usage.md)
for the explicit export options.

Continue with [Machining parameters](machining-parameters.md).
