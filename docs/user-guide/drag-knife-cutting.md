# Drag-knife cutting

Select **Options → Machine Type → Drag Knife**. The current implementation
uses one knife-planning workflow: lead-in, lead-out and overcut do not require
an additional “planned cuts” switch. None for both leads and disabled overcut
omit those optional movements.

Use the closed rectangle A and open contour C in the
[three-shape example](../assets/examples/machining-basics/three-shapes-mm.dxf)
for separate preview preparations. Disable circle B for these examples.
All dimensions below are illustrative, not material-tested cutting values.

## Tool offset, depth and swivel height

Enter the blade offset in the knife tool-table field: the distance from the
holder's rotation axis to the tip. An indicated offset of **0.25 mm** is stored
internally as **0.50 mm diameter**. Do not copy an old tutorial's “diameter”
value into the new offset field without checking that convention.

| Setting | Meaning/example |
| --- | --- |
| Workpiece top | `0 mm` in the example |
| Infeed depth | `-0.1 mm` per cut |
| Final depth | `-0.3 mm`, giving cuts at -0.1, -0.2 and -0.3 mm |
| Swivel contact height Z | Separate absolute Z coordinate used for corner relief |
| Lift-angle threshold | Corner angle above which the blade is relieved for a swivel |

Swivelling never plunges below the current cutting depth. The swivel-contact
height can be overridden per contour; clear that contour field to use the
global value again. It is not another name for infeed depth.

Global knife choices are in **Configuration → Output settings**. Tip path,
holder path and the original contour are distinct geometries. The planner
accounts for the tip offset; it does not detect clamps or neighbouring parts.

## Choose the assumed entry heading

| Entry choice | What it assumes |
| --- | --- |
| Configured start angle | Assume that angle at each renewed entry; 0° is positive X |
| Keep previous angle | Carry the reached heading to the next contour using the same tool |
| Unknown: external alignment | Use a straight contact/alignment stretch before the lead-in |

Previous-angle mode uses the configured angle for the first operation and
after a tool change or custom G-code. It assumes the blade keeps its heading
when lifted. If it can rotate freely while raised, use the unknown-heading
option with an external lead-in and a sufficiently long alignment stretch.

Unknown heading requires at least **twice the offset** as alignment length.
That is a geometric minimum, not proof that a real blade has aligned. The
software measures no angle and cannot promise an exact tip track during
alignment from an arbitrary initial heading. Establish the needed contact
distance on the actual blade/material and allow room outside the contour.

The optional return to the configured start angle happens once in the lead-out
before lifting and requires a lead-out. It does not guarantee the blade's
heading after it has lifted.

## Leads and ramp entry

Use the existing lead selectors. Tool lead length sets the straight lead-in
portion; knife lead-out length is a separate global setting. Curved or combined
leads use the existing lead radius for the **tip** path, from which holder motion
is calculated. Short or unsuitable geometry produces a planning error.

**Ramp length = 0** plunges at fixed XY. A positive length changes XYZ together
over that distance on the tip path. With a suitable lead-in, the first depth
is reached at the intended contour start. Choosing no lead-in instead places
entry/ramp on the contour deliberately.

Straight ramps emit coordinated XYZ lines; curved ramps are approximated by
XYZ lines within the fitting tolerance. Component feeds are limited by the
configured XY and Z feeds. The G-code profile needs the `lin_mov_xyz` program
template for these movements; the default supplies it.

## Closed contours

External alignment and lead-in occur on the first entry. Later depth cuts
continue without an intermediate retract, with the next plunge/ramp starting
at the contour start. Corner relief still applies.

After the last depth cut, the planner recuts any ramp section not yet covered
at final depth. The option for **one additional complete pass at final depth**
is independent of that automatic correction. Overcut then extends along the
closure, followed by lead-out. A 2 mm ramp correction and 0.5 mm overcut can
therefore produce 2.5 mm of continued contour motion.

## Open contours

With alternating cuts off, the tool retracts and approaches the start again
between depth cuts. With alternating cuts on, **straight leads at both ends**
are required. The blade exits the nominal contour, turns outside it and feeds
to the next depth on the way back. Insufficient leads block planning rather
than silently changing this sequence.

If the final depth was reached using a ramp inside an open contour, the planner
adds a complete final-depth pass automatically. An explicitly requested extra
final-depth pass is additional to that correction. Open contours have no
closed-contour overcut.

## Older projects and further reading

Older knife profiles/projects used slice depth as swivel depth. Migration
separates those meanings, preserves per-contour swivel values and initially
uses one depth cut for legacy preparations. New D2G files use format 1.5.
Previously active multi-pass settings keep their newer meaning. Keep a backup
and inspect the migrated paths; migration does not promise an identical
movement sequence from the historical planner.

For background, see Erich Styger's
[Optimized Vinyl Cutting G-Code Tool Path with DXF2GCODE](https://mcuoneclipse.com/2021/07/06/optimized-g-code-tool-path-for-vinyl-cutting-with-dxf2gcode/)
(2021). Its interface and machine-specific postprocessor edits are historical;
use the offset convention and controls described above. The
[2022 Dragknife issue](https://www.ltspiceusers.ch/threads/dragknife-issue.1126/)
records a historical final-swivel problem, not a claim that the same defect
exists now. Neither source's images or example files are reproduced here.

Use [Toolpath diagnostics](toolpath-diagnostics.md) for errors and
[Preview and export](preview-and-export.md) to compare the planned result.
