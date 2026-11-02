# DXF2GCODE logo contour example

`dxf2gcode-logo.dxf` is a reusable import, selection and preview fixture derived
from the project's own `dxf2gcode-logo.svg` under
`source/dxf2gcode/presentation/qt/resources/images/` (02 November 2026).

- DXF AC1015, millimetres; the SVG canvas is scaled to 180 mm wide.
- Text is converted to outlines using Arial, as specified by the source SVG.
- Curves are approximated by polyline vertices. The drawing contains 46 closed
  contours on Wordmark, Toolpath, Spindle, Cutter, Flutes and Flute_highlights
  layers. Cutter decorations are clipped to the cutter silhouette.
- Colour gradients are appearance information and are not represented in DXF.
  Decorative layers overlap intentionally; select the relevant contours when
  assigning machining operations.

The drawing was loaded through the current DXF2GCODE importer and used for the
organization profile screenshot. It is an illustration/import fixture, not a
preconfigured machining project.
