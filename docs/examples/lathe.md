# LinuxCNC 2.9 linear lathe example

This example targets a hobby CNC lathe running **LinuxCNC 2.9**, with longitudinal
Z and diameter X. Download
[linuxcnc29-lathe-linear.cfg.example](../assets/examples/postprocessors/linuxcnc29-lathe-linear.cfg.example),
save it as `linuxcnc29-lathe-linear.cfg` and select
**LinuxCNC 2.9 - lathe linear diameter demonstration**.

The profile establishes G18, G7, G94 and G97, leaves the spindle stopped at S0
and emits no automatic tool change. It is a linear motion demonstration,
not a complete roughing cycle, thread program or machine commissioning setup.

Select lathe mode only with an explicitly reviewed turning profile. The current
formatter doubles the second planar coordinate and its corresponding centre/
offset components. It leaves the first coordinate unchanged; `%R` is still
the stored arc radius. A mode change does not establish every controller's
diameter/arc convention.

## Follow the numbers before assigning axes

| Drawing point | First coordinate formatting | Second coordinate formatting |
| --- | --- | --- |
| (-10, 5) | `%XE` = -10 | `%YE` = 10 in lathe mode |
| (-20, 3) | `%XE` = -20 | `%YE` = 6 in lathe mode |

Select **Lathe** in the application before preparing/exporting the drawing.
Both supplied planar templates map its first coordinate to Z and the already
doubled second coordinate to X:

```ini
[Program]
rap_pos_plane = "G0 Z%XE X%YE%nl"
lin_mov_plane = "G1 Z%XE X%YE%nl"
```

Drawing point (-10, 5) becomes Z-10 X10 before formatting padding. Do not
double X again. G7 selects LinuxCNC's diameter convention; G18 selects XZ.
See [LinuxCNC lathe information](https://linuxcnc.org/docs/2.9/html/lathe/lathe-user.html)
and the [G7/G18/G94/G97 definitions](https://linuxcnc.org/docs/2.9/html/gcode/g-code.html).

## Own stepped-profile drawing

Download [lathe-radius-profile-mm.dxf](../assets/examples/postprocessors/lathe-radius-profile-mm.dxf).
It is an open line chain with drawing coordinates (0,5), (-10,5), (-10,3),
(-20,3): longitudinal positions 0…-20 mm and radii 5/3 mm. Set the start at
(0,5), use G40 and no leads/overcut. Its layer sets one planner pass through
top 0, infeed -1 and final -1; these are not physical radial roughing depths.

The generic axial templates are empty. There is **no automatic safe X retract**
or clearance calculation: rapid XY events map directly to Z/X. Review the
entire approach/return against the actual stock, chuck and tool before any
machine use. Multiple planner depth passes would repeat the same planar path.

## Arcs, compensation and tooling

G94 keeps the application's feed in units per minute, not per revolution.
G97 selects fixed-RPM interpretation, but the demonstration never starts the
spindle. Work offsets and tool offsets must be established separately. G40
means no tool-nose compensation, so this is not a finished-dimension guarantee.

Arcs are deliberately converted to lines. LinuxCNC's G7 diameter X convention
does not double arc-centre offsets in the same way. A future native-arc profile
needs explicit I/K and direction treatment; copying the application's doubled
second offset placeholder would be wrong. Do not enable native arcs by merely
clearing `export_arcs_as_lines` in this demonstration.

The managed next-start tool-change contract currently supports milling G-code,
so this reference uses no managed turning macro. Tool station changes, length/
nose offsets and machine clearance need their own controller configuration.

Configuration loading, diameter formatting and the own drawing import were
checked; no LinuxCNC interpreter or physical turning trial was run.
See [Machine modes](../user-guide/machine-modes.md#lathe-check-the-coordinate-convention)
and [Tool changes](../reference/tool-changes.md).
