# Installation and startup

## Choose a release or the development checkout

Previously published packages are in the
[SourceForge download archive](https://sourceforge.net/projects/dxf2gcode/files/).
Read the selected package's description and supplied instructions: that archive
also contains development builds and release candidates. Older releases can
require different Python/Qt versions and installation steps.

The GitHub `develop` branch is actively being modernized. The instructions below
describe running that source checkout, **not installing a stable release**.
They do not imply that a new Windows installer or wheel has been published.

## Requirements

| Component | Declared requirement / purpose |
| --- | --- |
| Python | Application metadata: **3.9 or newer** |
| ConfigObj | `configobj>=5.0.6`, configuration files |
| PyOpenGL | `PyOpenGL>=3.1`, rendering support |
| PyQt5 | `PyQt5>=5.15`, the simplest starting point and a required package dependency |
| PyQt6 | Optional alternative; the package's `qt6` extra adds it without removing PyQt5 |
| Git | Obtaining a checkout |
| Qt build tools | Prepare UI/resources and compiled translations in a fresh checkout; see below |

Python 3.11 is the baseline identified by the repository's test documentation.
The command checks for this guide used Windows, Python 3.11.1, PyQt 5.15.11 and
Qt 5.15.2 in an existing environment. This is **not** a clean-install acceptance
test of every declared minimum. The Ubuntu 24.04 Desktop and PyQt6 instructions
were checked against code and official tool/package documentation, but were not
executed as new installations for this guide. Package availability also depends
on Python version, operating system and architecture.

Use a [Python virtual environment](https://docs.python.org/3/library/venv.html)
to keep application packages separate from system Python and other projects.
The application's `.venv` below is separate from the documentation-build
environment. Instructions for maintaining the website are in the repository's
[documentation notes](https://github.com/dxf2gcode/dxf2gcode/blob/develop/doc/documentation-notes/documentation-site-maintenance.md).
PySide6 is not a
supported runtime binding for this checkout.

## Windows PowerShell: PyQt5

Install Python with the Windows Python launcher and Git first. For translated
menus, also install Qt Linguist tools providing `lrelease.exe`. The
[official Qt installer](https://doc.qt.io/qt-6/qt-online-installation.html)
lets you select development components; availability depends on the Qt version
and license. If the directory containing `lrelease.exe` is not already on
`PATH`, add its actual location for this PowerShell session:

```powershell
$qtToolBin = Read-Host "Directory containing lrelease.exe"
$env:PATH = "$qtToolBin;$env:PATH"
Get-Command lrelease
```

`lrelease` is an external executable, not a Python import. Installing the PyQt
runtime wheel alone is not a substitute for making this tool available.
Prefer the tools for the selected Qt major version. The PyQt5 UI/resource
generators themselves are supplied by PyQt5; no separate `rcc` is needed for
this path.

The clone destination must not already exist. If you already have a checkout,
skip cloning and enter its root instead; do not overwrite it or switch away
from work in progress. The commands below deliberately call the virtual
environment's interpreter directly, so PowerShell script activation and an
execution-policy change are unnecessary.

```powershell
Set-Location D:\GIT
git clone --branch develop --single-branch https://github.com/dxf2gcode/dxf2gcode.git dxf2gcode-sourcecode
Set-Location .\dxf2gcode-sourcecode

py -3.11 -m venv .venv
& .\.venv\Scripts\python.exe -m pip install "PyQt5>=5.15" "configobj>=5.0.6" "PyOpenGL>=3.1"

$env:DXF2GCODE_QT = "5"
& .\.venv\Scripts\python.exe source\tools\build\qt_assets.py
& .\.venv\Scripts\python.exe source\tools\build\translations.py --no-pylupdate
& .\.venv\Scripts\python.exe source\dxf2gcode.py
```

Select another installed Python version of at least 3.9 if necessary; the
3.11 example uses the documented test baseline. Once prepared, restart from
the checkout root with the last command. Set `DXF2GCODE_QT` in each new shell
if you want to keep selecting PyQt5 explicitly.

## Ubuntu 24.04 Desktop: PyQt5

Run this in a terminal in the directory where you want the new checkout.
The distribution's `python3` is used; this does not specifically install 3.11.
The Qt translation tools are in Ubuntu's `qttools5-dev-tools` package
(Universe repository).

```sh
sudo apt update
sudo apt install git python3 python3-venv python3-pip qttools5-dev-tools libgl1

git clone --branch develop --single-branch https://github.com/dxf2gcode/dxf2gcode.git dxf2gcode-sourcecode
cd dxf2gcode-sourcecode
python3 -m venv .venv
. .venv/bin/activate

python -m pip install "PyQt5>=5.15" "configobj>=5.0.6" "PyOpenGL>=3.1"
export DXF2GCODE_QT=5
python source/tools/build/qt_assets.py
python source/tools/build/translations.py --no-pylupdate
python source/dxf2gcode.py
```

Activation makes `python` refer to `.venv/bin/python`. In a later terminal,
enter the checkout, activate `.venv`, select the binding and run the launcher
again. Alternatively, call `.venv/bin/python` directly. Use `deactivate` to
leave the activated environment. These are desktop GUI instructions; they do
not configure a display server on a headless machine.

## PyQt6 alternative and binding selection

The selection logic is shared by the application and build helpers:

| `DXF2GCODE_QT` | Selection |
| --- | --- |
| `5` | PyQt5 |
| `6` | PyQt6 if its Python package is discoverable; otherwise PyQt5 |
| Unset | PyQt6 if discoverable; otherwise PyQt5 |

Only the exact value `5` forces PyQt5. Other values currently follow the same
logic as an unset variable; use `5` or `6` deliberately. The fallback checks
package discovery, not whether a discovered PyQt6 can actually load its DLLs
or platform plugins. Such import/runtime failures do not automatically retry
PyQt5. Missing generated Qt6 modules also do not trigger a PyQt5 fallback.

After completing the PyQt5 setup, add PyQt6 in the **same application
environment**. For Windows, install Qt 6 development tools providing `rcc.exe`
and `lrelease.exe` and put their directories on `PATH`. Check with
`Get-Command rcc, lrelease`. The resource compiler must be Qt 6 and support
`-g python`; the helper does not turn a Qt 5 `rcc` into a Qt 6 compiler.

```powershell
& .\.venv\Scripts\python.exe -m pip install PyQt6
$env:DXF2GCODE_QT = "6"
& .\.venv\Scripts\python.exe source\tools\build\qt_assets.py
& .\.venv\Scripts\python.exe source\tools\build\translations.py --no-pylupdate
& .\.venv\Scripts\python.exe source\dxf2gcode.py
```

On Ubuntu, with the application environment activated:

```sh
sudo apt install qt6-base-dev-tools qt6-l10n-tools libegl1 libopengl0 libxcb-cursor0
python -m pip install PyQt6
export DXF2GCODE_QT=6
export PATH="/usr/lib/qt6/libexec:/usr/lib/qt6/bin:$PATH"
python source/tools/build/qt_assets.py
python source/tools/build/translations.py --no-pylupdate
python source/dxf2gcode.py
```

Ubuntu provides Qt 6 `rcc` at `/usr/lib/qt6/libexec/rcc` and translation tools
through `qt6-l10n-tools`. The helpers recognize the standard Qt 6 tool paths.
If `rcc` on `PATH` belongs to Qt 5, correct `PATH` before generating resources.
See [Ubuntu's resource compiler file list](https://packages.ubuntu.com/noble/amd64/qt6-base-dev-tools/filelist)
and [translation tools](https://packages.ubuntu.com/noble/qt6-l10n-tools).

For a binding check, enter `source/` and use your environment's Python:

```python
from dxf2gcode.presentation.qt.qt_compat import PYQT_VERSION, QtCore
print(PYQT_VERSION, QtCore.PYQT_VERSION_STR, QtCore.QT_VERSION_STR)
```

This can be entered in an interactive Python session; exit it before running
further shell commands. Check that the printed major version matches the
modules you generated.

## Generated files and translations

`qt_assets.py` writes the selected binding's `dxf2gcode_ui5.py` /
`dxf2gcode_images5_rc.py` or `dxf2gcode_ui6.py` / `dxf2gcode_images6_rc.py`
under `source/dxf2gcode/presentation/qt/generated/`. Regenerate the appropriate
pair after UI/resource changes or when preparing another binding. Do not edit
or commit generated modules.

For ordinary source-tree startup, `translations.py --no-pylupdate` compiles
existing `source/i18n/*.ts` catalogs into `.qm` files using
[Qt Linguist's lrelease](https://doc.qt.io/qt-6/linguist-lrelease.html). It does
**not** update the maintained TS catalogs. Without compiled catalogs the
application uses its source-language text where translations are unavailable.

For maintainers changing GUI text, running `translations.py` **without**
`--no-pylupdate` first updates catalogs using `pylupdate5` or `pylupdate6`, then
compiles them. That is a separate editing workflow: review and translate the
maintained German, French and Russian catalogs together. `--keep-ln` preserves
source locations and skips QM compilation. It is not the normal startup step.

## Package entry points and developer installation

The source launcher is `python source/dxf2gcode.py`. An installed package also
provides `python -m dxf2gcode` and a `dxf2gcode` console command (on Windows,
`.venv\Scripts\dxf2gcode.exe` for that environment). Add `--help` to inspect
command-line options. Installing only the dependencies above does not install
that console command; use the source launcher in that case.

A developer can install a **prepared** checkout with
`python -m pip install --editable ./source`. Package preparation is a separate
step: its asset validation expects **both Qt5 and Qt6 generated variants** and
compiled translations. Preparing just PyQt5 for source startup is not the full
release-preparation procedure. A prepared wheel or source archive includes
these assets, so its installer does not need to generate them.

See the repository's
[technical setup and packaging documentation](https://github.com/dxf2gcode/dxf2gcode/blob/develop/source/README.md#preparing-and-building-a-release)
for that workflow. Package build dependencies are `setuptools>=77` and `wheel`;
they are distinct from runtime requirements. No release build is needed merely
to run the source launcher. Follow [First DXF to G-code](getting-started/first-dxf-to-gcode.md) for
the drawing-to-output workflow.

## Optional PDF / PostScript import

For DXF import, the external converters are unnecessary. For PostScript import
you additionally need `pstoedit`; PDF import uses `pdftops` followed by
`pstoedit`. On Ubuntu these are available as `poppler-utils` and `pstoedit`:

```sh
sudo apt install poppler-utils pstoedit
```

On Windows install the converter executables separately and configure their
actual paths. Application configuration stores them as
`Filters.pdftops_cmd` and `Filters.pstoedit_cmd`; the historical default paths
may not match your installation. The application does not install these
programs for you. Consult the converter's own installation instructions for
its dependencies.

## Troubleshooting and help

- **Missing generated module:** generate the UI and resources using the same
  interpreter and binding that you use to start the application.
- **Missing lrelease / Qt 6 rcc:** install the external tools and correct
  `PATH`; rerunning `pip install PyQt5` alone does not supply every Qt tool.
- **Unexpected binding:** check `DXF2GCODE_QT` and the printed binding version.
- **Qt platform-plugin error:** keep the terminal error text. Check the Qt
  runtime's [Linux desktop-library requirements](https://doc.qt.io/qt-6/linux-requirements.html)
  for your system, including XCB cursor support for Qt6. The commands above are
  not a complete dependency list for every minimal Linux installation.
- Report reproducible faults to
  [GitHub Issues](https://github.com/dxf2gcode/dxf2gcode/issues), including
  checkout revision, OS, Python/PyQt/Qt versions and the command/error output.
- Ask usage questions in the existing
  [dxf2gcode English forum on ltspiceusers.ch](https://www.ltspiceusers.ch/forums/english-section.67/).
