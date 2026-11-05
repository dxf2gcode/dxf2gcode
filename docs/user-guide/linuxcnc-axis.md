# LinuxCNC / AXIS integration

AXIS can open a DXF through DXF2GCODE as an **interactive file filter**:
choose a drawing in AXIS, edit its machining settings in DXF2GCODE, then
export. The G-code returns to AXIS for preview. Closing DXF2GCODE without
export cancels the filter operation.

This uses LinuxCNC's [INI `[FILTER]` mechanism](https://linuxcnc.org/docs/2.9/html/config/ini-config.html#_filter_section).
It does not start the machining program or control the machine from DXF2GCODE.

## Prepare a dedicated profile

Use a separate [configuration profile](application-settings.md#configuration-profiles),
for example `linuxcnc`, for this workflow. In
`~/.config/dxf2gcode.linuxcnc/config/config.cfg`, configure:

```ini
[General]
write_to_stdout = True
mode3d = False
```

Change these entries in the existing profile, preserving its other sections.
The stdout setting sends exports to AXIS instead of a file and closes
DXF2GCODE after export. Keep stdout disabled in profiles used for normal
[file export](command-line-usage.md).

Prepare a suitable G-code postprocessor in this profile and note its exact
`output_text` description. The built-in description is `G-CODE for LinuxCNC`.
Pass that description with `--postpro`; an unknown or ambiguous description
is an error. Without `--postpro`, the legacy first-postprocessor default
still applies and can change when profiles are added.

## Configure AXIS

Add the following entries to the existing `[FILTER]` section of the LinuxCNC
INI file. Replace both paths with the actual interpreter and source checkout
containing the corrected filter:

```ini
[FILTER]
PROGRAM_EXTENSION = .dxf DXF drawing
dxf = /absolute/path/to/python3 /absolute/path/to/source/dxf2gcode.py --cfg linuxcnc --postpro "G-CODE for LinuxCNC"
```

LinuxCNC appends the drawing filename. Keep existing filter entries for other
formats. Use quoted paths if they contain spaces. The interpreter needs the
DXF2GCODE runtime dependencies. An installed `dxf2gcode` console entry point
can replace the interpreter/source pair, provided that installation contains
the filter corrections; the acceptance described below used a source checkout.

Open the DXF in AXIS, check units, tool, depths and machining choices in
DXF2GCODE, then choose **Export → Export Shapes without Optimization**
(`Ctrl+Shift+E`). AXIS receives the program and builds its preview.

## Results and errors

| Filter status | Meaning |
| --- | --- |
| `0` | Export succeeded; G-code is returned on stdout |
| `1` | The window was closed without export |
| `2` | A handled input or export failure occurred |

Handled export failures discard the buffered G-code. Diagnostics use stderr.
AXIS displays a filter-error dialog on nonzero status; in the tested cases
the previously loaded valid program stayed loaded. Correct the error and
open the drawing again.

Do not use `--quiet drawing.dxf` as an automatic filter command. The existing
headless export requires an output argument; a dedicated automatic stdout
filter mode is not provided by this interactive integration.

## Verified scope

On 5 November 2026, the real AXIS filter/preview workflow was checked on
Debian 13 with LinuxCNC 2.9.4, Python 3.13.5 and PyQt5 5.15.11 / Qt 5.15.15.
The test used a separate metric simulation, private configuration, Xvfb and
a logging wrapper around the actual source entry point. It verified a DXF
path with spaces, explicit selection of a postprocessor placed after another
profile, visible toolpath preview, cancellation, unknown postprocessor and
invalid DXF. AXIS and Qt were not mocked.

The initial run exposed nested parentheses in the generated version comment;
the runtime information now uses square brackets so AXIS can interpret it.
Use a version containing that correction.

The simulation stayed in ESTOP with an idle interpreter and unchanged
positions. No program execution or machine movement was tested. This does
not establish machine/material safety, packaged-installation acceptance,
GMOCCAPY support, Wayland behavior or Linux/PyQt6 acceptance.
