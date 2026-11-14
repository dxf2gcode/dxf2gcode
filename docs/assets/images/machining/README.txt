Current development UI screenshots, captured 2026-11-14

Provenance: actual application widgets from integration/maschining-project-release
(develop + maschining-project, including the revised IGNORE import). Captured
with Python 3.11 / PyQt6 on Windows using QWidget.grab(), an isolated English
profile, Segoe UI 10 and a temporary QSettings store. No third-party screenshots
or personal drawing/configuration files were used. Message-pane startup paths
were cleared before capture. Images are original project documentation assets,
under the repository license.

The same session replaced the six previous screenshots under first-dxf/,
machining-basics/ and settings/. Those earlier capture records in the example
README files describe historical images; this record describes their replacements.

Inputs: repository-owned rectangle-20x10-mm.dxf, three-shapes-mm.dxf,
rectangle-with-tab-mm.dxf and ignore-layers-mm.dxf, under assets/examples/.
Drawing and tool units: millimetres. Profile tool 1: diameter 2, speed 6000;
tool 2: diameter 1, speed 8000; software compensation. Tutorial depths:
top 0, infeed -0.5, final -1, feeds 200/100, retract 15, safety 3, no leads.
The compensation image additionally uses G41, lead radius 2, straight length 3,
overcut length 1. The tab image uses its DXF-specified top -1 and final -1.5.

operations.png: Roughing and Finishing share the rectangle; selected Finishing
uses tool 2 and G41. Original geometry was not translated to separate paths.
assign-existing/new.png: one dialog, Copy retained while changing its target.
geometry-regions.png: original trees plus project-region catalogue.
tab-selected/drag/dialog.png: resting measurements, actual corner-drag gesture
with hidden measurement fields, and the region editor respectively.
ignore-unassigned.png: initial IGNORE import, no assignments for those contours.
tools-table.png and settings images: current configuration pages; the two demo
tools differ from factory entries and are not material-specific recommendations.

Executed check: export the tutorial rectangle through the default LinuxCNC
postprocessor, verify G21 and depths -0.500/-1.000 without G41/G42. This is
file-export evidence, not package, Linux desktop, controller or machine acceptance.
Manual screenshot inspection and documentation build are recorded separately
in doc/archive/toolpath-refactoring-completed.md.
