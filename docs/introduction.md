# Introduction

Start with [Installation and startup](installation.md) if you have not yet
prepared the application environment.

Then follow [First DXF to G-code](getting-started/first-dxf-to-gcode.md) for a
complete example with a 20 x 10 mm rectangle, screenshots and export checks.

## Drawings, projects and output

A DXF file supplies drawing geometry. In dxf2gcode, you prepare the shapes and
machining parameters, inspect the drawing and toolpath, and export through a
postprocessor profile. The profile controls the output format for the target
controller.

A saved `.d2g` project lets you reload the project's settings and drawing
references. It is distinct from the exported machine program.

## A basic workflow

1. Open a DXF drawing and check its units, scale and workpiece origin.
2. Choose the shapes to export and review their machining parameters.
3. Review the shape order and inspect the toolpath preview.
4. Select the appropriate postprocessor profile and export the program.

The development checkout includes milling, lathe and drag-knife machine modes.
Machine mode and postprocessor profile are separate settings. A preview does
not establish that a profile is suitable for a particular CNC controller.

See [Interface and navigation](user-guide/interface-and-navigation.md) for
the window controls, and [Import drawings and save projects](user-guide/import-and-projects.md)
for supported inputs, saved preparation and reload limitations.

Further operating instructions, configuration references and machine examples
will be added after comparison with the current code. Historical wiki examples
are not treated as validated machine profiles.

Return to the [project overview](index.md), or see how to
[preview the documentation](documentation-preview.md).
