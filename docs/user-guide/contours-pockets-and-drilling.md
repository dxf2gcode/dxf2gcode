# Contours, pockets and drilling

This chapter describes milling operations using the
[three-shape drawing](../assets/examples/machining-basics/three-shapes-mm.dxf).
A is the closed rectangle, B the circle and C the open two-segment contour.
See [the labelled overview](shapes-layers-and-order.md#example-drawing).

Use a separate demonstration configuration as explained in
[First DXF to G-code](../getting-started/first-dxf-to-gcode.md). Values here
illustrate the controls; they are not material-specific cutting recommendations.

## Follow a contour

1. Choose **Options → Machine Type → Milling**.
2. Select C alone in the drawing or tree.
3. In its drawing context menu choose **Cutter Compensation → G40 No Compensation**.
4. Use top `0 mm`, infeed `-0.5 mm`, final depth `-1 mm`, XY feed
   `200 mm/min` and Z feed `100 mm/min` for a file/preview demonstration.
5. Set **Lead in**, **Lead out** and **Overcut** to **None** where available.

The centre path follows C's two segments. Multiple passes on an open contour
can alternate direction. There is no closing segment to the first point.
Overcut is for closed contours and is unavailable for an open-only selection.

For A, the same G40 setup follows the rectangle boundary, not a cutter-radius
offset from it. Use [software or machine compensation](compensation-and-leads.md)
when the drawing is a nominal finished boundary.

## Clear a pocket

1. Select A alone; its contour must be closed.
2. In **Options → Configuration → Output settings**, use software cutter
   compensation by clearing the machine-compensation option.
3. Use a `2 mm` milling tool, zero additional offset and the illustrative depths
   above. Check the lead settings separately.
4. Right-click A and enable **Pocket Mill**.
5. Inspect the boundary and internal clearing paths before any export.

The pocket command is offered for a fully closed selection when compensation
is performed in software in milling mode. It is unavailable for lathe,
drag knife or machine compensation. Loaded pocket settings in these modes are
preserved and reported; change to milling with software compensation or
explicitly disable pocketing before export. A mixed open/closed selection therefore does not offer the same
pocket command as selecting A alone.

Pocket milling includes interior clearing as well as the prepared boundary.
G40 pockets receive an internal boundary treatment; they do not behave like a
G40 contour that simply follows the drawn edge. G41/G42 pocket boundaries also
depend on the configured pocket-compensation strategy. Review the resulting
side and path rather than treating any compensation choice as equivalent.

The pocket edge-clearance percentage controls spacing relative to the cutting
edge and boundary in units of tool diameter. It is not an XY feed rate. Small
regions, unsuitable offsets or a calculation failure can remove or skip pocket
geometry. Read the messages and check that the intended region is actually
cleared; an outline alone is not evidence of successful pocketing.

## Drill at a circular contour

1. Select B alone.
2. Right-click and enable **Drill Bore**.
3. Check the resulting drill position, depth and retraction values.

The command is offered for a closed selection consisting entirely of arcs.
It changes the operation to drilling rather than milling around the circle.
The drawn circle does not automatically choose a physical drill diameter;
select the appropriate tool separately.

Drilling uses the postprocessor's drill command and repetition capabilities.
Do not infer a particular canned cycle or peck depth solely from the source
circle or the general infeed field. Inspect the selected output profile and
the resulting program.

## Compatible mode changes

| Deliberate selection | Result |
| --- | --- |
| Enable Drill Bore | Disable pocket milling and set G40 |
| Enable Pocket Mill | Disable drilling; retain the chosen compensation |
| Choose G40, G41 or G42 | Disable drilling; retain the pocket choice |

Turning an option off does not restore a previous operation automatically.
For a mixed selection, enabling an operation applies that target consistently;
it is not a request to invert every shape's different old value independently.

A loaded project may contain drilling combined with pocketing or G41/G42.
These conflicting settings are reported and preserved for review. The affected
contours have no exportable plan until you explicitly select a compatible
operation. See [machining conflicts](toolpath-diagnostics.md#machining-conflicts).

Save different demonstration preparations under different D2G names. Return to
[Machining parameters](machining-parameters.md) for scope and inheritance.
