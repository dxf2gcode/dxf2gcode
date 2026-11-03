WP3-WP5: machining-basics documentation assets
Created for DXF2GCODE on 2026-11-03; source baseline 6c4bcc9.
Newly authored text/drawing and current application widget captures.
No third-party wiki prose, design or screenshot reused.
License: GPL-3.0-or-later, following source/COPYING.

three-shapes-mm.dxf: AC1015, INSUNITS=4 (millimetres), layer Tutorial.
A: closed rectangle (0,0), (20,0), (20,10), (0,10).
B: circle centre (40,5), radius 3.
C: open polyline (25,20), (35,20), (35,25).
Letters are documentation labels, not DXF text. In the captured import the
shape numbers were 0/1/2; circle B became two arcs. Import options may affect IDs.

Images under docs/assets/images/machining-basics:
three-shapes.png: actual imported drawing, no contour selected.
software-compensation-leads.png: WP1 rectangle, selected clockwise, G41 outside,
software compensation, diameter 2 mm, radius 2 mm, straight length 3 mm,
overcut 1 mm, top 0, infeed -0.5, final -1, XY feed 200 mm/min, Z feed 100,
retraction 15 mm and safety margin 3 mm. Tool defaults and effective values
match the displayed fields. The prepared plan had no error diagnostics.

Both: English MainWindow, isolated temporary profile, Qt widget captures,
Windows, Python 3.11.1, PyQt5 5.15.11, Qt 5.15.2. Personal startup log paths
cleared; only example information in message pane. Images visually reviewed.
The rectangle asset is ../first-dxf/rectangle-20x10-mm.dxf.

Order tables explain deterministic application of an assumed optimizer route;
they do not promise that stochastic optimization returns that route.
No G-code export, machine operation, converter test or package build was run
for WP3-WP5. Screenshots and code review are not platform/machine acceptance.
