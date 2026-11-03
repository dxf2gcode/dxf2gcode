WP6-WP8 documentation assets; created 2026-11-03.
Newly authored project drawing, diagram and actual configuration widget captures.
Source baseline 6c4bcc9; no foreign wiki text, diagrams or DXFs reused.
License: GPL-3.0-or-later, following source/COPYING.

rectangle-with-tab-mm.dxf: DXF AC1015, INSUNITS=4 (millimetres).
Main closed contour: (0,0),(20,0),(20,10),(0,10), layer
MILL: Tn:1 SMd:0 Sd:-0.5 Md:-1.5 FeedXY:200 FeedZ:100
Closed tab region: (9,-1),(11,-1),(11,1),(9,1), layer
BREAKS: Md:-1 FeedXY:200 FeedZ:100
Imported in an isolated actual MainWindow as two closed contours. Parsed final
depth -1.5, infeed -0.5, tab Z -1 and XY feed 200 confirmed.

../../images/tabs/pass-depths.svg: own schematic side view, not a machine or
material-removal simulation. Top 0, cuts -0.5/-1/-1.5, tab top -1 mm.

../../images/settings/general-settings.png and parameter-names.png:
actual ConfigWindow in a fresh isolated profile, English labels; Windows,
Python 3.11.1, PyQt5 5.15.11, Qt 5.15.2. 1280 x 850 widget captures, visually
reviewed; no interface mockup and no personal configuration paths shown.

CLI --help was executed. Export command examples were checked against the
argument parser and direct-export paths, not executed. No converter run,
source-code test suite, release/package build or physical-machine trial.
Historical external knife articles are linked, not reproduced or accepted
as current tool-offset or controller instructions.
