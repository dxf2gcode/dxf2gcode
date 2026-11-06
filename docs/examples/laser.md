# Grbl 1.1 diode-laser example

This example targets a DIY diode-laser machine running **Grbl 1.1**, using
its dynamic laser mode. Download
[grbl11-laser-dry.cfg.example](../assets/examples/postprocessors/grbl11-laser-dry.cfg.example),
save it as `grbl11-laser-dry.cfg` in the active postprocessor folder and select
**Grbl 1.1 - laser zero-power demonstration**.

It is a complete motion-demonstration profile, deliberately using **S0**.
It sends no controller settings, no tool changes, no coolant and no Z movements.
Configuration loading and synthetic formatting were checked; no controller or
powered cutting run was performed.

## Controller prerequisites

Confirm the installed firmware and the machine's laser wiring/configuration.
Grbl's laser mode requires `$32=1`; the profile does not change this stored
setting. M4 selects dynamic power behaviour and G0 does not energize the laser
in that mode. See the official
[Grbl laser-mode reference](https://github.com/gnea/grbl/wiki/Grbl-v1.1-Laser-Mode).

The S scale depends on `$30` and the controller configuration, not a universal
percentage. For example, an S value of 250 on a 0–1000 scale is not the same
command as 250 on a 0–255 scale. Check the actual `$30`/`$31` values against the
[configuration reference](https://github.com/gnea/grbl/wiki/Grbl-v1.1-Configuration).

## Separate travel from cutting

`Program.rap_pos_plane` formats positioning. `pre_shape_cut` and `post_shape_cut`
are contour-boundary hooks; `lin_mov_plane` and arc templates format the path.
The supplied profile emits M5 S0 before every XY rapid and after each contour;
its cutting hook emits M4 S0. All arcs are approximated as lines. Application
tool speed is deliberately not substituted as laser power, so the factory
milling spindle speed cannot silently become an S power request.

The standard milling profile contains M6, spindle/coolant actions and Z moves.
Changing its description to “laser” does not remove those actions. Review all
templates, including program opening/ending, depth, drilling and tool changes.
Multiple depth passes can repeat the laser path; they are not automatically
power levels or a controller-specific pass count.

## Demonstration settings

Use milling mode, G40, no pockets/drilling/tabs, no leads and no overcut. Set
top 0, infeed -1 and final depth -1 in a separate mm demonstration profile
to obtain one traversal. These are planner pass-control values; no Z words
are emitted and they are not laser material depths. Use a deliberately chosen
XY feed and inspect the output before any controller use.

The principal supplied templates are:

```ini
[Program]
rap_pos_plane = "M5 S0%nlG0 X%XE Y%YE%nl"
pre_shape_cut = "M4 S0%nl"
post_shape_cut = "M5 S0%nl"
```

The full download also replaces startup, ending and unused milling templates.
For a later powered adaptation, change only the intended cutting S value after
establishing the machine's scale and process. Do not globally replace S0: travel
and ending must remain off. No power or material-feed recipe is prescribed here.

## Compare an adaptation

Use an [own simple drawing](../assets/examples/first-dxf/rectangle-20x10-mm.dxf),
first as a text-only review. Confirm one intended pass, M5 S0 around travel,
M4 S0 at the cut hook, and absence of M6/M8/M9, G64 and Z words. Multiple depth
passes would repeat the planar path despite suppressed Z output. These hooks
are not a hardware interlock. Any hardware trial is separate from file review.

Historical laser examples remain [historical references](../project/history.md),
not current accepted profiles. See [Postprocessor reference](../reference/postprocessors.md).

## Complete configuration

The code below is included directly from the downloadable profile, so both
represent the same file. Use the download link above to save the configuration.

```ini title="grbl11-laser-dry.cfg.example"
--8<-- "grbl11-laser-dry.cfg.example"
```
