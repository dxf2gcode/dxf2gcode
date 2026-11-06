# DXF output example

Download [dxf-lines.cfg.example](../assets/examples/postprocessors/dxf-lines.cfg.example).
It is a newly authored, loadable demonstration producing simple **2D LINE
entities**. Copy it as `dxf-lines.cfg` into the active `postpro_config` folder
and select **DXF - 2D line demonstration**. Preserve other profiles.

## Scope

The profile sets `output_type = dxf`, absolute coordinates, no line numbers,
a decimal point and line approximation for arcs. Its program opening/ending
form a minimal DXF ENTITIES section. Each planar cutting line emits start/end
group codes. Positioning and axial movements emit no drawing entity.

Use ordinary milling mode, G40, no pocket/drill/tab/knife operations and
[the simple rectangle](../assets/examples/first-dxf/rectangle-20x10-mm.dxf)
for this narrow example. DXF output uses a single-pass planning treatment;
it is not an archive of every cutting depth or controller state.

```ini
[General]
output_type = dxf
output_format = .dxf
abs_export = True
export_arcs_as_lines = True
```

These keys alone are insufficient; use the full download, which replaces all
relevant G-code templates. Default unit/G90/header commands must not be left
in a DXF entity stream.

## What to inspect

The result should be plain group-code/value pairs, beginning with SECTION /
ENTITIES and ending with ENDSEC / EOF. The profile does not preserve original
blocks, layer metadata, annotations, splines or an entire CAD document. Its
output layer is `TOOLPATH`; Z values are zero. Units are the prepared geometry's
coordinates; the minimal file contains no independent unit declaration.

Schema loading and synthetic LINE-template formatting were checked for this
documentation. No new complete drawing export/reimport was run. Before using
it as an interchange workflow, export and reopen a controlled example in your
target CAD program and compare dimensions and closed connectivity.

See [Postprocessor reference](../reference/postprocessors.md) and
[Preview and export](../user-guide/preview-and-export.md).

## Complete configuration

The code below is included directly from the downloadable profile, so both
represent the same file. Use the download link above to save the configuration.

```ini title="dxf-lines.cfg.example"
--8<-- "dxf-lines.cfg.example"
```
