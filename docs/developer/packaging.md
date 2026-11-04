# Packaging and builds

Build metadata is in `source/pyproject.toml`. Setuptools builds the Python
package; helper commands prepare Qt assets and verify release inputs. Building
a package is a separate task from editing documentation or starting the app.
The commands below are instructions, not builds executed for this chapter.

## Python distribution

`requires-python` is >=3.9. Dependencies declare ConfigObj, PyQt5 and PyOpenGL;
the `qt6` extra adds PyQt6. The installed console entry is
`dxf2gcode.bootstrap.launcher:main`. Source archives and wheels include the
prepared resources/translation data specified by the build helpers and manifests.

For a release build, install build tooling, both PyQt bindings, Qt6 `rcc` and
Qt Linguist `lrelease`. From the repository root on a POSIX shell:

```sh
python -m pip install build PyQt5 PyQt6 configobj PyOpenGL
DXF2GCODE_QT=5 python source/tools/build/qt_assets.py
DXF2GCODE_QT=6 python source/tools/build/qt_assets.py
DXF2GCODE_QT=5 python source/tools/build/translations.py --no-pylupdate
python -m build source
```

On PowerShell set `$env:DXF2GCODE_QT = "5"` or `"6"` before the corresponding
command. Output is under `source/dist/`; filenames contain the version of the
prepared source. Use actual filenames rather than old date-version examples.
From `source/`, `make package PYTHON=python` combines release preparation/build.

The release build rejects missing prepared assets. A runtime wheel install
does not need Qt development compilers. A source-development editable install
and an accepted wheel installation are different checks.

## Verify the built wheel

Install/check it in an isolated interpreter using the repository verifier:

```sh
python tests/verify_wheel.py source/dist/ACTUAL_WHEEL_FILE.whl --python PATH_TO_TEST_PYTHON --qt 5
```

This placeholder command must be filled with real paths. The verifier examines
package contents, installed resources/translations, desktop files, entry points
and a quiet DXF export from an unrelated directory with isolated configuration.
Qt6 requires its own environment and `--qt 6`. These are substantive acceptance
checks, not a reason to run a complete build after a prose-only edit.

## Windows packages

Windows packaging uses cx_Freeze. After preparing release assets, the helper
can build an MSI:

```sh
python source/tools/build/windows.py bdist_msi
```

Install the required cx_Freeze version/environment first; see the source build
README for platform prerequisites. CI's `tools/package_windows.py` stages the
portable ZIP and MSI, startup checks and provenance. Initial published Windows
packages use Python 3.11 / PyQt5 and are unsigned. Signing needs a separately
configured certificate workflow; no existing signature is implied.

The portable ZIP must be extracted completely. MSI installation is per user;
Develop and stable channels use separate upgrade identities/directories. MSI
needs a numeric product version, so `2.0.0.dev123` maps to `2.0.123`, while
stable `2.0.0` maps to `2.0.0`. Overflow stops the build rather than wrapping.

## CI checks versus publication

[Tests and package checks](https://github.com/dxf2gcode/dxf2gcode/actions/workflows/checks.yml)
runs automatically for develop pushes/PRs. It does not create a public release.
[Publish release](https://github.com/dxf2gcode/dxf2gcode/actions/workflows/publish-release.yml)
is manually started on develop for previews; stable publication is triggered
by a matching `v<version>` tag and the existing release gate. It checks the
selected revision before publishing. Do not use a test workflow as a release action.

`tools/prepare_release.py` stages a clean revision, writes version/provenance
metadata and creates the release manifest. The publication counter and workflow
run number are different. Check `_build_metadata.json`, About, manifest and
`SHA256SUMS` against the intended revision.

The next stable target remains **2.0.0 after the entire Todo is completed**.
Preparing this documentation does not authorize a tag, new release, MSI build,
Debian/SSH acceptance or physical-machine trial. See
[Releases and downloads](../project/downloads.md) for user-facing policy and
the [technical pipeline](https://github.com/dxf2gcode/dxf2gcode/blob/develop/doc/release-pipeline.md)
for exact current implementation.
