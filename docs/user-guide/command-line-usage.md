# Command-line usage

The examples below run from the repository root using the Python environment
prepared in [Installation and startup](../installation.md). Substitute your
environment's Python executable for `python` if necessary. These are
code-reviewed command examples; only `--help` was executed for this chapter.

## Available options

```sh
python source/dxf2gcode.py --help
```

| Argument | Purpose |
| --- | --- |
| `filename` | Input DXF, D2G project, PS or PDF |
| `-e FILE`, `--export FILE` | Output destination |
| `-p NAME`, `--postpro NAME` | Select a postprocessor by its displayed description |
| `-o`, `--optimize` | Optimize the route before export |
| `-q`, `--quiet` | Request the non-GUI export path |
| `-c NAME`, `--cfg NAME`, `--config-suffix NAME` | Select a named application configuration profile |
| `-h`, `--help` | Print usage and exit |

The `--postpro` value is the displayed description, for example
`"G-CODE for LinuxCNC"`, or its full filter text, not the configuration filename
`postpro_config.cfg`. Matching is exact. An unmatched value currently falls
back to the first available profile; inspect the resulting header instead of
assuming a typo is rejected. A missing output extension, or one differing from
the selected profile's extension, has that profile's extension appended.

## Export the rectangle without opening a window

Prepare a separate `wp1-demo` configuration profile as described in
[First DXF to G-code](../getting-started/first-dxf-to-gcode.md). The raw-DXF
command uses that profile's defaults and any drawing layer parameters; it does
not inherit unsaved contour settings from an open GUI session.

```sh
python source/dxf2gcode.py --quiet --cfg wp1-demo --postpro "G-CODE for LinuxCNC" --export rectangle-cli.ngc docs/assets/examples/first-dxf/rectangle-20x10-mm.dxf
```

This produces an output file using the profile's current preparation defaults.
It does not by itself reproduce the tutorial's manually entered -0.5/-1 mm
depths. To export those saved settings, first save the tutorial preparation as
a D2G project, then use its actual path:

```sh
python source/dxf2gcode.py --quiet --cfg wp1-demo --postpro "G-CODE for LinuxCNC" --export rectangle-project.ngc rectangle-20x10-mm.d2g
```

The D2G file must already exist and its referenced drawing must be available.
The command-line project loader cannot ask you to locate missing geometry in
an interactive file chooser. Quote paths containing spaces.

To request route optimization deliberately, add `--optimize`:

```sh
python source/dxf2gcode.py --quiet --cfg wp1-demo --optimize --export three-shapes.ngc docs/assets/examples/machining-basics/three-shapes-mm.dxf
```

Review [route constraints](route-optimization.md) and the chosen profile's
defaults. This command illustrates the option; it does not promise a particular
optimized order or material-specific cutting parameters.

## What “headless” covers

The direct non-GUI paths require **all three**: `--quiet`, an input filename,
and an export filename. DXF, D2G, PS and PDF are routed through these paths
before constructing the main window. Quiet mode alone, an unsupported suffix
or an incomplete combination is not a universal guarantee that GUI setup is
avoided. Use the complete form in unattended jobs.

The application still depends on its Python/Qt libraries. These supported
direct-export paths do not require the historical virtual-display workaround
just to construct a MainWindow. Other invocation paths can initialize GUI
objects, so do not generalize that statement to every command.

PDF/PS import also needs the external converters described in
[Import drawings and save projects](import-and-projects.md#input-formats).
Converter failures are reported separately; a PDF is not automatically a
vector cutting drawing.

## Profiles, messages and exit status

An explicit `--cfg` takes precedence over the profile selected last in the GUI.
Without it, the saved GUI profile selection is used; with no saved selection,
the default profile is used. A CLI override chooses that invocation's folder
without changing the saved GUI selection. See
[profile names and folders](application-settings.md#configuration-profiles).

Direct export returns `0` on completion and `2` for handled configuration,
conversion or export failures. Argument errors also use the parser's nonzero
exit status. Inspect stderr/log messages, output existence and its contents:
completion does not prove that every contour produced a usable cutting path.

In PowerShell, read `$LASTEXITCODE` immediately after the command. In a POSIX
shell, read `$?`. The configuration's **export to stdout** option can redirect
program output away from a file; keep it off when following the file examples.
`--quiet` means no GUI for the supported export path, not “suppress all logs”.

Continue with [Troubleshooting and FAQ](troubleshooting.md).
