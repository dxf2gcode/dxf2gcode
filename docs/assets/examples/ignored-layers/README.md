# IGNORE import comparison

`ignore-layers-mm.dxf` is an original comparison drawing in millimetres.
Each column contains the same 20 × 12 mm rectangle and radius-4 mm circle.

| Left-to-right column | X range | DXF layer | Expected first import |
| --- | --- | --- | --- |
| 1 | 0–20 mm | `Normal_Machining` | Normal machining assignments |
| 2 | 40–60 mm | `IGNORE:Construction` | Unassigned geometry, no toolpath/export |
| 3 | 80–100 mm | `IGNORE:Helpers` | Unassigned geometry, no toolpath/export |
| 4 | 120–140 mm | `Compare_Unassigned` | Normal assignments; remove them to compare |

For comparison, remove the two machining assignments belonging to column 4
while retaining their original geometry. Those contours and the imported
IGNORE contours should behave alike as unassigned geometry. Select a contour
from column 2 or 3 and assign it to a normal machining step: it should receive
normal export controls and a toolpath. Undo should restore its unassigned state.

Use a profile that imports IGNORE geometry. The separate import option that
excludes IGNORE layers entirely must be off; otherwise those columns are omitted
before geometry is created. Drawing colours use the normal layer colour rather
than a custom IGNORE colour. Selection colours and disabled-path visibility
still follow the application's ordinary settings.
