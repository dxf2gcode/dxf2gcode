# Support and issue reporting

Choose the channel that matches the problem:

| Need | Destination |
| --- | --- |
| Usage question or machining discussion | [Existing user forum](https://www.ltspiceusers.ch/forums/english-section.67/) |
| Reproducible application defect | [GitHub issue forms](https://github.com/dxf2gcode/dxf2gcode/issues/new/choose) |
| Feature proposal | Feature request in the same chooser |
| Incorrect/missing documentation | Documentation issue in the same chooser |
| Separate Linux installation-script failure | [Installer issues](https://github.com/dxf2gcode/dxf2gcode_installer/issues) |

The forms have English headings and accept descriptions in English or German.
Use an existing matching issue when it already captures the same problem.

## Make a defect reproducible

Include the version/revision, operating system and installation method, machine
mode, units, exact steps, expected result and actual result. Preserve the exact
error message; a screenshot can help explain selection or geometry, but does
not replace a small reproducible drawing.

Attach a minimal DXF and its D2G preparation when contour state matters. A D2G
project references its drawing rather than embedding it. For configuration or
export defects, include the active application profile and **actual selected
postprocessor** when relevant. Paths for both Windows and Linux are in
[Application settings](../user-guide/application-settings.md#configuration-files).
ZIP related files or extensions rejected by the issue form.

Reduce the example without removing the defect. Original contour, prepared path
and exported movement can differ, so describe which one is wrong. For routing,
state whether the export was optimized and which enable/Optimal path boxes were
set. For source changes, note the Qt binding and any uncommitted modifications.

Review personal paths, private drawings, comments and secrets before attaching
files. Do not upload an entire profile folder or raw email/discussion archive
when a small relevant configuration is enough.

## Feature and documentation requests

A feature proposal should describe the task you want to complete, the current
limitation, the desired behaviour and an example. Implementation suggestions
are welcome but not necessary. A documentation issue should identify the page,
unclear instruction, current version and proposed clarification if known.

For immediate investigation, start with [Troubleshooting](../user-guide/troubleshooting.md)
and [Toolpath diagnostics](../user-guide/toolpath-diagnostics.md). A software
fix or passing regression does not establish a safe parameter recipe for a
particular material/controller.
