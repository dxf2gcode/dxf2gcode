WP1 example: First DXF to G-code
Created for DXF2GCODE documentation on 2026-11-03.

Authorship: newly authored project example and current application screenshots;
no SourceForge prose, drawing or screenshot has been reused.
License: GPL-3.0-or-later, following the project license in source/COPYING.

rectangle-20x10-mm.dxf:
  DXF AC1015; $INSUNITS=4 (millimetres).
  One closed four-vertex LWPOLYLINE on layer Tutorial.
  Coordinates: (0,0), (20,0), (20,10), (0,10).
  Workpiece origin is at the lower-left corner.

Screenshots (docs/assets/images/first-dxf/):
  01-import.png: enabled drawing, no contour selected.
  02-parameters.png: selected contour with the documented parameters.
  Rendered from the actual MainWindow in an isolated temporary wp1-demo profile.
  Windows; Python 3.11.1; PyQt5 5.15.11; Qt 5.15.2; English interface.
  Source baseline: 935bfc8; branch docs/wiki-migration.
  They are Qt widget captures, not interface mockups or packaged-build tests.
  Personal startup paths were cleared from the message pane.

Final export trace:
  Real actionExportShapes -> exportShapes -> ExportToolpath, normal export
  without optimization, with only the destination chooser supplied by script.
  Built-in postpro_config.cfg: G-CODE for LinuxCNC (*.ngc).
  Milling, G40, tool 1, diameter 2 mm, speed 6000 rpm.
  Retraction 15 mm; safety margin 3 mm; top 0; infeed -0.5 mm; final -1 mm.
  XY feed 200 mm/min; Z feed 100 mm/min; no leads, overcut or pocket milling.
  Checked G21/G90/G40, no G41/G42, all rectangle corners and both depths.
  Default header/tool/spindle/coolant commands remain part of that profile.
  The output was inspected as a file; no controller or machine was operated.
  No release, installer, Debian/SSH or platform-acceptance workflow was run.

The chapter contains a motion excerpt only; it is not a standalone CNC program.
