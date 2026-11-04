# Postprocessor examples

These five references explain output adaptation. They are newly written from
the current implementation, rather than copied historical machine profiles.
Use a separate application profile and keep the existing postprocessors intact.

| Example | What is provided | Acceptance boundary |
| --- | --- | --- |
| [Grbl 1.1 diode laser](laser.md) | Complete zero-power motion profile | Laser mode/scale must match; no powered trial |
| [LinuxCNC 2.9 hot-wire](hot-wire.md) | Complete matched XYUV motion profile | Parallel paths only; no heating control or tapered planning |
| [LinuxCNC 2.9 lathe](lathe.md) | Complete linear Z/diameter-X profile and own drawing | No automatic tool/spindle/clearance procedure or interpreter acceptance |
| [DXF output](dxf-output.md) | Own loadable line-entity demonstration | Schema/template checks; no full reimport/export acceptance |
| [Python text output](python-output.md) | Own loadable event-recording demonstration | Text generation; no plugin execution or machine control |

All five downloads are complete **demonstration configurations** with an
intentionally narrow scope. The three controller examples were selected for
DIY/hobby setups; they do not certify a particular manufacturer's machine.
Laser/spindle power remains zero and the wire profile sends no heater commands.
Their metadata records loading and synthetic template checks. No controller
interpreter or physical machine was exercised for this documentation package.

For a controller adaptation, specify its version, units, work offsets, axis and
arc conventions, switching/tool-change procedure and representative expected
output before calling it ready. Start with [Postprocessor reference](../reference/postprocessors.md)
and [Tool changes](../reference/tool-changes.md).
