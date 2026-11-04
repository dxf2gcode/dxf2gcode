<h1 id="dxf2gcode"><img src="assets/images/dxf2gcode_logo.png" alt="dxf2gcode"></h1>

dxf2gcode converts 2D DXF drawings into G-code for CNC machines. It provides
a Qt interface for preparing drawings and toolpaths, with configurable
postprocessors for output.

**Development documentation.** These chapters describe the current development
version toward 2.0.0. The guide covers operation, postprocessors, examples and
development. Example acceptance limits are stated on the relevant pages.

- Follow [First DXF to G-code](getting-started/first-dxf-to-gcode.md) for a
  step-by-step example with a downloadable drawing.
- Explore [Interface and navigation](user-guide/interface-and-navigation.md)
  and [Import drawings and save projects](user-guide/import-and-projects.md).
- Prepare [tree order](user-guide/shapes-layers-and-order.md) and
  [route optimization](user-guide/route-optimization.md), set
  [machining parameters](user-guide/machining-parameters.md), and choose
  [contours, pockets or drilling](user-guide/contours-pockets-and-drilling.md).
- Review [compensation and leads](user-guide/compensation-and-leads.md),
  compare [preview and export](user-guide/preview-and-export.md), and resolve
  [toolpath diagnostics](user-guide/toolpath-diagnostics.md).
- Add [tabs](user-guide/tabs-and-breaking-layers.md), understand
  [machine modes](user-guide/machine-modes.md) and prepare
  [drag-knife cuts](user-guide/drag-knife-cutting.md).
- Use the [command line](user-guide/command-line-usage.md), consult
  [troubleshooting](user-guide/troubleshooting.md), and configure
  [application settings](user-guide/application-settings.md) or
  [parameterized layer names](user-guide/layer-naming-rules.md).
- Follow [Installation and startup](installation.md) to run a development checkout.
- Adapt output using the [postprocessor reference](reference/postprocessors.md),
  [tool-change contracts](reference/tool-changes.md) and
  [five example references](examples/index.md).
- Start development with [setup](developer/setup.md),
  [architecture](developer/architecture.md), [tests](developer/tests.md) and
  [Qt/translations](developer/qt-and-translations.md). See
  [packaging](developer/packaging.md), [contributing](developer/contributing.md)
  and [website maintenance](developer/documentation.md) for maintenance work.
- Find [downloads](project/downloads.md), [support](project/support.md),
  [license and credits](project/license-and-credits.md) and
  [historical documentation](project/history.md).
- Find the source code in the [GitHub repository](https://github.com/dxf2gcode/dxf2gcode).
- Previously published packages remain in the
  [SourceForge download archive](https://sourceforge.net/projects/dxf2gcode/files/).
  Check each package's description: the archive also contains development builds.

The historical [SourceForge wiki](https://sourceforge.net/p/dxf2gcode/wiki/Home/)
may describe older versions. Use the current chapters above for the development
interface and preparation workflow.
