# LinuxCNC 2.9 parallel hot-wire example

This example targets a hobby two-tower wire machine controlled by **LinuxCNC
2.9 with XYUV axes**. Download
[linuxcnc29-foam-parallel.cfg.example](../assets/examples/postprocessors/linuxcnc29-foam-parallel.cfg.example),
save it as `linuxcnc29-foam-parallel.cfg` and select
**LinuxCNC 2.9 - parallel XYUV wire motion**. It formats the same planar path
at both ends of the wire. It supplies **motion only**, with no heater commands.

DXF2GCODE can format a planar contour for a hot-wire setup whose controller
accepts that motion. Its ordinary two-dimensional drawing and depth planner
do not create independent root/tip paths for a four-axis tapered-wing machine.
Renaming output axes does not add that planning capability. The supplied
profile is intentionally limited to parallel/constant-section cuts, not tapered
wings or different profiles at the two towers.

## Establish the geometry and axes

Use a LinuxCNC configuration with the actual X/Y/U/V joints, origins, limits
and homing established. This postprocessor does not create that machine setup.
AXIS can show foam motion with `FOAM = 1` under `[DISPLAY]`; that is a preview
setting, not a kinematics configuration. See the official
[AXIS foam view](https://linuxcnc.org/docs/2.9/html/gui/axis.html#_using_axis_in_foam_cutting_mode)
and [INI reference](https://linuxcnc.org/docs/2.9/html/config/ini-config.html).

The complete profile uses these matched rapid/cut mappings:

```ini
[Program]
rap_pos_plane = "G0 X%XE Y%YE U%XE V%YE%nl"
lin_mov_plane = "G1 X%XE Y%YE U%XE V%YE%nl"
```

For drawing endpoint (20, 10), the cut block contains X20 Y10 U20 V10. Both
pairs need compatible zero references and scaling. AXIS preview-plane placement
does not calculate the physical tower spacing or a tapered profile.

Choose milling/G40, no leads, pockets, drilling or tabs, and a single pass in
a separate application profile: top 0, infeed -1, final -1. No Z movement is
emitted; these values control pass count only. Arcs are approximated as lines.
Check the feed interpretation and real tower speed for the configured XYUV
kinematics rather than treating a number as a foam-cutting recipe.

## Heating and path transitions

The profile does not switch a power supply or prescribe heat-up/cool-down time.
Heating remains a separate setup/process responsibility. No generic M3/M8
substitution is made for an unknown heater circuit. First inspect motion in
the appropriate LinuxCNC simulation/configuration without heating the wire.

Use an [open and closed contour](../assets/examples/machining-basics/three-shapes-mm.dxf)
to review direction changes and repeated passes as text. Configuration loading
and synthetic XYUV formatting were checked, not a LinuxCNC interpreter or real
machine. No independent four-axis solver or accepted material process is implied.
See [Machine modes](../user-guide/machine-modes.md) and
[Postprocessor reference](../reference/postprocessors.md).

## Complete configuration

The code below is included directly from the downloadable profile, so both
represent the same file. Use the download link above to save the configuration.

```ini title="linuxcnc29-foam-parallel.cfg.example"
--8<-- "linuxcnc29-foam-parallel.cfg.example"
```
