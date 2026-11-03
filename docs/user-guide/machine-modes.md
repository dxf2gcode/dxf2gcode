# Machine modes

Choose **Options → Machine Type** to select **Milling**, **Lathe** or
**Drag Knife**. The current drawing is refreshed when the mode changes.
Machine mode selects application behaviour; the postprocessor selected during
export controls the actual command syntax. Check both settings.

## Milling

Milling uses tool diameter, contour compensation, depth passes, optional pockets
and drilling. Start with [Machining parameters](machining-parameters.md) and
[Contours, pockets and drilling](contours-pockets-and-drilling.md).
Automatic cutter compensation is available in this mode.

## Drag knife

A freely swivelling blade has a tip offset from the holder axis. Its planned
holder motion differs from the desired tip path, especially at corners.
The tool table therefore displays **Knife offset** in knife mode rather than
a milling diameter. Confirm the translated label in your interface.

Knife cutting uses separate controls for depth passes, swivel contact height,
entry alignment, ramps and external turnaround. Pocket milling and the milling
G40/G41/G42 context-menu choices are not offered for this mode. Follow
[Drag-knife cutting](drag-knife-cutting.md) for the current sequence and offset
convention.

## Lathe: check the coordinate convention

Lathe mode disables automatic milling-compensation assignment. The drawing
is still represented in its two planar coordinates. In the output formatter,
the second coordinate's position and corresponding centre-offset placeholders
are multiplied by **2**: a drawn radial coordinate of 5 becomes a formatted
diameter coordinate of 10 when that placeholder is used. The first planar
coordinate is not doubled.

This does not automatically establish a conventional X/Z turning program.
Axis letters and program templates come from configuration and postprocessor
settings; the defaults are X/Y/Z. The interface's **No Z-Axis for lathe** label
must not be read as a guarantee that a generic profile emits no third-axis
commands or milling-style depth repetitions.

Use a deliberately reviewed turning profile and compare coordinate mapping,
radius/diameter handling, arcs and depth/retract commands with your controller.
Do not change only the mode and run an unchanged generic milling program.
The current documentation establishes the formatter convention; it does not
provide an accepted lathe-machine setup.

## Switching modes and saving work

A mode switch updates the active drawing and saves the machine choice for
future sessions. A D2G project can restore its own saved machine type when
opened. Recheck the active mode after loading a project.

Keep separate [configuration profiles](application-settings.md#configuration-profiles)
for different setups. In particular, a cutter diameter and a knife offset are
different physical quantities even though the stored tool entry is shared.
Save the current preparation before experimenting with another mode.
