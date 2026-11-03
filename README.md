# dxf2gcode

<p align="center">
  <img src="source/dxf2gcode/presentation/qt/resources/images/dxf2gcode_logo.png" alt="dxf2gcode logo" width="400">
</p>

dxf2gcode is an open-source converter from 2D DXF drawings to G-code for CNC
machines. It provides a Qt interface for preparing drawings and toolpaths,
with configurable postprocessors for output.

**[Downloads](https://github.com/dxf2gcode/dxf2gcode/releases) ·
[Linux Installer](https://github.com/dxf2gcode/dxf2gcode_installer "Installation script for Debian/Ubuntu, Linux Mint and Arch-based systems") ·
[Documentation](https://dxf2gcode.github.io/dxf2gcode/)**

See the documentation for installation, startup and an introduction to the workflow.

**Development status:** the `develop` branch on GitHub is being actively
modernized and restructured. It does not automatically represent a stable
release. [Develop downloads](https://github.com/dxf2gcode/dxf2gcode/releases?q=develop-ci-&include_prereleases=1)
are published after tests and package checks pass. For historical releases, visit the
[SourceForge downloads](https://sourceforge.net/projects/dxf2gcode/files/).
The download archive also contains development builds and release candidates;
check the selected version's description before installing.

## Features

- Import 2D DXF drawings and save or reload `.d2g` projects.
- Inspect drawings and toolpaths in the Qt interface.
- Configure milling, lathe and drag-knife machine modes.
- Prepare contours and pockets, including depth passes and lead moves.
- Export through configurable postprocessor profiles, including G-code output.
- Run command-line exports as well as the graphical application.
- Import PDF and PostScript through the optional external `pdftops` and
  `pstoedit` programs.

See the [technical documentation](source/README.md) for the package structure,
runtime requirements and build details.

## Installation and startup

### Published releases

Choose a [stable GitHub release](https://github.com/dxf2gcode/dxf2gcode/releases/latest)
when available, or a clearly marked
[Develop preview](https://github.com/dxf2gcode/dxf2gcode/releases?q=develop-ci-&include_prereleases=1).
The next stable target is **2.0.0**; a Develop package such as `2.0.0.dev123`
is a preview. Downloads include a Python wheel, source archive, Windows x64
portable ZIP and MSI. Windows packages initially use Python 3.11 / PyQt5 and
are **unsigned**. Verify files against the supplied `SHA256SUMS`.

Extract the entire Windows ZIP before starting `dxf2gcode.exe`, or install
the MSI for the current user. Develop and stable MSI installations use separate
directories. For Python, install the downloaded wheel with `python -m pip install
<wheel-file>` in a virtual environment. When replacing an old date-versioned
installation, use a fresh environment or explicitly install the chosen wheel:
the old date version sorts above `2.0.0`.

[Historical SourceForge downloads](https://sourceforge.net/projects/dxf2gcode/files/)
can have different requirements. See the [release pipeline](doc/release-pipeline.md)
for version mapping, verification and retention rules.

### Linux installer

For Debian- and Arch-based distributions, including Ubuntu and Linux Mint,
the [Linux Installer](https://github.com/dxf2gcode/dxf2gcode_installer "Installation script for Debian/Ubuntu, Linux Mint and Arch-based systems")
provides a script-based installation path. Follow the installer repository's
README for instructions, supported versions and the current development status.

### Run the development checkout

The package declares Python 3.9 or newer; the test documentation identifies
Python 3.11 as a tested version. The commands below use PyQt5 explicitly.
PyQt6 is also supported; see [source/README.md](source/README.md) for its
additional resource-generation requirements. PySide6 is not a supported
runtime binding at present.

Clone the repository and enter it:

```sh
git clone --branch develop --single-branch --no-tags https://github.com/dxf2gcode/dxf2gcode.git
cd dxf2gcode
python -m venv .venv
```

Activate the environment and select PyQt5. On a POSIX shell:

```sh
. .venv/bin/activate
export DXF2GCODE_QT=5
```

On Windows PowerShell instead:

```powershell
.\.venv\Scripts\Activate.ps1
$env:DXF2GCODE_QT = "5"
```

Install the runtime dependencies. Qt Linguist's `lrelease` tool must also be
installed and available on `PATH` for translation compilation; see the
[build documentation](source/README.md).

```sh
python -m pip install "PyQt5>=5.15" "configobj>=5.0.6" "PyOpenGL>=3.1"
python source/tools/build/qt_assets.py
python source/tools/build/translations.py --no-pylupdate
python source/dxf2gcode.py
```

These commands generate Qt modules and compiled translations locally without
updating the maintained translation catalogs. They do not build a release.
PDF/PostScript import additionally requires `pdftops` and `pstoedit`.

## Help and development tasks

- **User questions and discussions:** use the existing
  [forum on ltspiceusers.ch](https://www.ltspiceusers.ch/forums/english-section.67/).
- **Bugs and development proposals:** use
  [GitHub Issues](https://github.com/dxf2gcode/dxf2gcode/issues).
  Include the version or commit and enough detail to reproduce a problem.
- **Earlier releases:** remain available through
  [SourceForge](https://sourceforge.net/projects/dxf2gcode/files/).

## Development and contributions

Pull requests should target `develop`. Keep changes small and explain their
purpose and validation, especially while the application is being restructured.
See [CONTRIBUTING.md](CONTRIBUTING.md) before starting a contribution.

After preparing the checkout as above, run the focused regression checks from
the repository root:

```sh
python tests/run_tests.py fast
```

See the [test guide](tests/README.md),
[technical documentation](source/README.md) and
[architecture documentation](doc/architecture.md) for further details.

## License

dxf2gcode is distributed under the GNU General Public License, version 3 or
(at your option) any later version (`GPL-3.0-or-later`). See [LICENSE](LICENSE)
for the full text. The original package copy remains in
[source/COPYING](source/COPYING).
