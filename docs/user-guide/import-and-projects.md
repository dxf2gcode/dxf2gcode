# Import drawings and save projects

DXF2GCODE distinguishes the source drawing, its machining preparation and the
exported program. Keeping these files separate makes it easier to resume work
and share a reproducible example.

| File | Contains | Open or create it with |
| --- | --- | --- |
| `.dxf` | Source drawing geometry and layers | **File → Open...** |
| `.d2g` | Saved preparation settings and a reference to the source drawing | **File → Save Project As...**, then **File → Open...** to reopen |
| `.ngc` or another postprocessor extension | Exported controller program | **Export** menu; inspect the output in a text editor or suitable controller preview |

A project does **not** embed the source drawing or replace the application
configuration and postprocessor profiles. Keep the drawing and any relevant
profiles with your project. Saving a project does not generate G-code, and
exporting G-code does not save the project.

## Open a drawing

1. Choose **File → Open...** (**Ctrl + O**).
2. Select a supported file and open it.
3. Read the import messages. Check the displayed units, drawing size and origin.
4. Expand the layer tree and inspect the resulting contours before assigning
   machining settings.

Opening another file replaces the current drawing. Save the current
preparation first; do not rely on an automatic save or an unsaved-changes prompt.

### Input formats

| Input | How it is handled |
| --- | --- |
| DXF | Read directly by the DXF importer |
| PostScript (`.ps`) | Converted to DXF using the configured external `pstoedit` command |
| PDF (`.pdf`) | Converted to PostScript with `pdftops`, then to DXF with `pstoedit` |
| D2G project (`.d2g`) | Reopens the referenced drawing and reapplies saved preparation settings |

PDF and PostScript entries in the file chooser do not mean their converters
are installed. Those programs and their command paths/options must be available
in the application's **Filters** configuration. `pdftops` and `pdf2ps` are
different programs. A conversion error should be investigated in the message
pane; check the resulting geometry and dimensions after a successful conversion.
A scanned picture in a PDF is not automatically traced into cutting contours.

For predictable examples, use a 2D DXF. The importer handles lines, arcs,
circles, polylines, lightweight polylines, splines, ellipses, block inserts
and points. This is not support for every DXF entity or a full CAD document:
unsupported geometry is reported, and the imported cutting geometry may omit
annotations or other CAD content. Compare the preview with the intended drawing.

### Units, connections and import options

Do not assume that a drawing is in millimetres because it looks the right
shape. Check a known dimension and the units beside the fields. Correct unit
or scale problems before setting machining depths or exporting.

The importer uses a **point tolerance** when connecting geometry and a
**fitting tolerance** when approximating curves. These influence the contours
created from the input; they are not a finishing allowance or a promise of
machine accuracy. Increasing a tolerance can alter which endpoints connect
or how a curve is represented. Recheck contour closure and shape count after
changing import settings.

Import options can also exclude layer `0` or ignore-marked layers and assign
block geometry to the insertion layer. These options can explain differences
between a CAD layer list and the imported tree. Excluding a layer during import
is different from disabling a visible contour for export.

## Save and reopen the rectangle example

Use the same [rectangle](../assets/examples/first-dxf/rectangle-20x10-mm.dxf)
and preparation from [First DXF to G-code](../getting-started/first-dxf-to-gcode.md).

1. Save the DXF in a permanent working folder and open it from there.
2. Select `Shape 0` and enter the tutorial's tool, depth and feed settings.
3. Choose **File → Save Project As...** (**Ctrl + S**).
4. Save as `rectangle-20x10-mm.d2g`, preferably beside the DXF. This command
   opens a destination chooser; choose the same project file to update it later.
5. Choose **File → Open...** and select the `.d2g` project, rather than the DXF.
6. Select `Shape 0` again and compare its settings: G40, infeed `-0.5 mm`,
   final depth `-1 mm`, XY feed `200 mm/min` and Z feed `100 mm/min`.

The expected result is one closed rectangle with the saved preparation
reapplied. Reopening a project is not a new export: generate a fresh program
after making changes and review it before use.

### What is restored

The project stores drawing transformations and import tolerances, the machine
type, layer tools and values, contour depths and feeds, compensation and
machining modes, start points and directions, enablement, ordering, lead/overcut
settings and stored tool overrides. It also preserves the project's drag-knife
settings where applicable.

This does not make the project a complete machine setup archive. Application
defaults, the tool catalogue and output postprocessor remain separate files;
settings inherited from them still matter. A loaded project can also change
the active machine type and relevant import or knife settings. Check these
before continuing with another drawing.

## Keep the referenced drawing available

The project records the source filename/path; it does not automatically turn
the DXF into an embedded or portable relative-path attachment. Moving the
project and DXF into one folder does not itself rewrite that reference.

If the drawing cannot be found when opening a project, the application asks
you to locate it manually. Select the matching source drawing, check the
restored contours and save the project again to record its current reference.
When sharing work, send both the project and drawing, plus relevant configuration
or postprocessor files. A project can contain local paths, so review attachments
before posting them publicly.

## Reload and changed drawings

**File → Reload** (**Ctrl + R**) rereads the current source drawing. It is not
an undo command and does not mean “restore my last saved D2G project”. Save
your preparation first. To restore a saved preparation, explicitly open the
`.d2g` file.

When a project is opened, saved contour settings are matched to the newly
imported geometry within matching layer names. Changing the CAD geometry,
layer names, units or import result can prevent that match. New or unrecognized
contours can be appended using their current defaults; removed contours cannot
be restored from the project alone. Do not assume that a successful file open
means every old machining setting was transferred.

After revising a drawing, check the layer/shape count, enablement, tools, depths,
start points, directions and order, then inspect the preview and a fresh export.
If the application reports contradictory machining settings, resolve them
through the contour context menu; affected shapes cannot be exported meanwhile.

Projects are versioned. The current reader supports the historical D2G versions
1.1 through 1.5, with migration of older settings where implemented. That does
not guarantee that an older application can read a newly saved project. Keep
the original project when migrating and save the result under a new name first.

Return to [Interface and navigation](interface-and-navigation.md), or follow
[First DXF to G-code](../getting-started/first-dxf-to-gcode.md) for the export steps.
