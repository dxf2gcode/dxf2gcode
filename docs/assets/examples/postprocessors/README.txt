WP9-WP13 documentation examples and architecture diagram, 2026-11-04.
Newly authored project material; source baseline bf1ac6d.
Own examples/diagram: GPL-3.0-or-later, following source/COPYING.
No historical wiki profile, screenshot or discussion text copied.

dxf-lines.cfg.example:
  Complete schema-8.3 demonstration, output_type=dxf, absolute, arcs as lines.
  Minimal ENTITIES/LINE group-code text; no depth/rapid/controller entities.
  Intended narrow scope: milling G40 ordinary 2D contour, no pockets/drills/
  tabs/knife/custom code. Not an original-drawing archival exporter.

python-events.cfg.example:
  Complete schema-8.3 text profile, absolute Python event tuples.
  Comments disabled; output is not executed by the application.
  Not a Python plugin or stable external API.

Both were copied into an isolated temporary postprocessor directory and loaded
by MyPostProConfig. No version mismatch or default recovery occurred. Synthetic
LINE formatting produced the expected DXF group-code pairs; representative
Python Program records were formatted and accepted by ast.parse, not executed.
No full application export/reimport, CNC file execution or machine trial run.

../../images/developer/planning-flow.svg:
  Own dependency/responsibility diagram based on current source paths.
  Rendered through Qt SVG and visually inspected; not a screenshot of a model
  claiming complete removal of legacy/global dependencies.

Environment for config/template and SVG checks: Windows, Python 3.11.1,
PyQt5 5.15.11, Qt 5.15.2. No package/release/MSI or source test suite run.

Controller examples added at the user's request for hobby/DIY examples:
grbl11-laser-dry.cfg.example: Grbl 1.1 laser mode, M4 S0 cutting hook;
  M5 S0 at startup/travel/end. No M6/coolant/Z or inherited speed-to-power use.
linuxcnc29-foam-parallel.cfg.example: LinuxCNC 2.9 XYUV, X=U and Y=V;
  matched rapid/cut mappings, no Z or heater commands. No tapered-path solver.
linuxcnc29-lathe-linear.cfg.example: LinuxCNC 2.9 G18/G7/G94/G97;
  application lathe mode, drawing first coordinate -> Z, doubled second -> X.
  Arcs linearized, no generic third-axis motion, automatic tool/spindle start
  or safe tool retract. No native-arc offset compatibility claim.
lathe-radius-profile-mm.dxf: own AC1015 metric open polyline,
  (0,5),(-10,5),(-10,3),(-20,3); drawing Y is radius.
  Layer MILL: SMd:0 Sd:-1 Md:-1 initializes one planner traversal.

These three profiles loaded through MyPostProConfig in an isolated folder and
were synthetically formatted. XYUV duplication, Z/X diameter conversion,
zero S requests, no M3/M6/M8/M9 and suppressed generic Z templates checked.
The own lathe DXF imported as one open three-line contour, radius 3..5 mm and
longitudinal coordinate -20..0 mm, with the one-pass depth settings confirmed.
No application export, controller-interpreter or physical acceptance performed.
Official controller sources were read on 2026-11-04 and are linked on the pages.

The existing LinuxCNC manual-change
page links the existing separately documented repository example rather than
copying a historical external profile into this asset directory.
