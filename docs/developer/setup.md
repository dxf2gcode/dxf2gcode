# Development setup

Use [Installation and startup](../installation.md) for platform-specific runtime
instructions. This page describes a source-development checkout; it does not
run the preparation or test commands on your behalf.

## Checkout and environment

```sh
git clone --branch develop https://github.com/dxf2gcode/dxf2gcode.git
cd dxf2gcode
python -m venv .venv
```

Activate `.venv` using your shell, then install `requirements-test.txt` for a
test environment. Select the intended binding before generation/startup:

```sh
python -m pip install -r requirements-test.txt
```

On POSIX shells use `export DXF2GCODE_QT=5`; on PowerShell use
`$env:DXF2GCODE_QT = "5"`. Qt6 uses value `6` and requires PyQt6 plus its
resource compiler. The package declares Python **>=3.9**; that declaration is
not proof of a fresh acceptance on every allowed Python/platform combination.
CI currently covers Python 3.11/3.12/3.13 with Qt5 and 3.11 with Qt6 on Linux.
Windows packaging uses 3.11/Qt5. PySide6 is not a supported runtime binding.

## Prepare only what the selected runtime needs

From the repository root:

```sh
python source/tools/build/qt_assets.py
python source/tools/build/translations.py --no-pylupdate
python source/dxf2gcode.py
```

Install Qt Linguist `lrelease` as described in the installation guide. Qt6 also
needs Qt's `rcc` development tool. These commands compile existing catalogs;
they do not update translation source texts. See
[Qt resources and translations](qt-and-translations.md) for text changes.

For an editable package, after preparation:

```sh
python -m pip install --editable ./source
```

The installed console command is `dxf2gcode`; `python -m dxf2gcode` is also
supported. The source launcher remains `python source/dxf2gcode.py` from the
repository root. Build helper commands invoked from `source/` omit that prefix.

## Isolate machine settings

Use a named application profile for development work instead of altering a
production setup. `--cfg dev-demo` selects `~/.config/dxf2gcode.dev-demo`;
[profile rules](../user-guide/application-settings.md#configuration-profiles)
also apply on Windows. A D2G project still references an external drawing.

Use small own examples under `docs/assets/examples/` for documentation work.
The maintained `dxf/` fixtures support regression tests: changing them can
change measured geometry, so they are not disposable scratch files.

## Work within the current contracts

Read [Architecture](architecture.md), [Tests](tests.md) and
[Contributing](contributing.md) before changing behaviour. Internal package
paths are implementation details; old `core`, `gui`, `postpro`, `Qt`, `globals`
and `dxfimport` re-export packages are not provided as a compatibility API.

Generated assets, `.tox`, build output and local profiles follow repository
ignore rules. Do not force-add generated files to make a checkout appear
prepared. Wheel/release preparation is a separate
[packaging workflow](packaging.md).
