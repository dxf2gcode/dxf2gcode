# Tests

This directory holds the DXF2GCODE test suite. The tests were moved here from
`source/` so that production code (`source/dxf2gcode/`), the permanently
maintained tests, the sample data (`dxf/`) and throw-away diagnostics are kept
apart.

## Layout

The suite is intentionally **flat**: all test modules live directly in this
directory. Several test modules share helper functions with each other
(`dxf2gcode_stmove_gcode_test.py` and `dxf2gcode_pocketmill_zigzag_test.py`
are imported by the other pocket tests), so splitting the modules into
`unit/`, `integration/` and `regression/` sub-directories would break those
imports without adding any practical benefit. The classification is documented
in the table below instead.

```
.
├── dxf/                     sample / test data (DXF drawings)
├── source/                  production package (dxf2gcode/)
└── tests/                   this directory
    ├── README.md
    └── dxf2gcode_*test.py   the test suite
```

Every test module starts by adding `source/` (and this directory) to
`sys.path` relative to its own `__file__`, so the suite can be started from
any working directory.

## Prerequisites

* Python 3 (tested with 3.11).
* The application dependencies: `PyQt5`, `PyOpenGL` and `configobj`
  (install them with `python -m pip install -r requirements-test.txt`).
* The GUI tests run headless; they set `QT_QPA_PLATFORM=offscreen`
  themselves, so no display is required.

## Test data

The tests use DXF files from the repository's `dxf/` directory, in
particular:

* `dxf/1997.DXF`        – offset / GIR-LIR and pocket zig-zag tests
* `dxf/pocketing1.dxf`  – pocketing (ticket #176), edge clearance,
                          compensation mode and ticket regression tests

`dxf2gcode_test.py` additionally scans every `*.dxf` in `dxf/`.

Change a data file only if you also accept that the measured geometry of the
affected tests changes.

## Running the suite

Code, test and executable-tool commits run the fast suite through the versioned pre-commit
hook. Enable it once per checkout with `python tools/install_hooks.py` from the
prepared test environment; see [hook setup](../CONTRIBUTING.md#fast-tests-before-every-local-commit).
GitHub runs the full suite automatically on pushes to `develop` and pull
requests targeting `develop`. Pure documentation changes use documentation
checks rather than source-code tests; follow the current [repository rules](../AGENTS.md).

Run the focused core checks from the **repository root** before submitting a
change:

```
python tests/run_tests.py fast
```

This group exercises DXF entity import and transforms, offsets, spline and
ellipse regressions, postprocessor settings, project persistence, and a real
quiet CLI conversion from `dxf/test.dxf` to a temporary `.ngc` file. The CLI
test gives the subprocess its own temporary configuration profile.
It also checks all Domain/Application imports without Qt or concrete adapters,
explicit model configuration, machining conflicts and whole-job export failure.
The machining-project regressions cover JSON 2.0 identities/provenance,
legacy migration, missing references and protected output. A real offscreen
MainWindow workflow verifies save/load/reload and GUI/CLI program parity with
two operations referencing one original contour.
The machining-command/panel regressions also exercise atomic move/copy and
stable undo/redo identities, real Qt drops, step/custom-code optimizer barriers,
saved-value provenance, unit interpretation, all new DE/FR/RU translations and
visible step order through actual GUI/CLI output. OpenGL adapter checks use
mocks and do not establish GPU acceptance.

Run every test before a release or a broad change:

```
python tests/run_tests.py full
```

Both commands print each test and return a nonzero exit status when a test
fails. Add `-h` to see runner options.

For isolated environments, install tox once and use its provider-neutral
environments:

```
python -m pip install tox
tox -e fast
tox -e full
```

CI systems can invoke `tox -e fast` for pushes and pull requests, then
`tox -e full` for release checks. Dependency versions and environment
variables are shared in `tox.ini` and `requirements-test.txt`.

The original unittest discovery command remains available from the repository
root:

```
python -m unittest discover -s tests -t tests -p "dxf2gcode_*test.py"
```

### Single modules

Run one module from the repository root:

```
python -m unittest discover -s tests -t tests -p "dxf2gcode_stmove_gcode_test.py" -v
```

or, when the current directory is `tests/`, simply:

```
python -m unittest dxf2gcode_stmove_gcode_test -v
```

### Notes on the discovery pattern

The default discovery pattern `test*.py` does **not** match the module names
(they are called `dxf2gcode_*test.py`), so `-p` must be given. Use
`dxf2gcode_*test.py` for the full suite; the narrower
`dxf2gcode_*_test.py` would silently skip `dxf2gcode_test.py`.

## Test categories

| Module | Type | Focus |
| --- | --- | --- |
| `dxf2gcode_test.py` | smoke / integration | checks fixture presence and runs a real quiet DXF-to-G-code CLI export |
| `dxf2gcode_linuxcnc_filter_test.py` | GUI / process integration | checks interactive stdout filter selection, atomic output, cancellation and failure exit codes |
| `dxf2gcode_import_contract_test.py` | integration | entity conversion, contour references, nested block contents and transforms |
| `dxf2gcode_postpro_config_test.py` | unit/regression | postprocessor defaults, supported versions, save/reload and invalid-file recovery |
| `dxf2gcode_canvas_mixed_test.py` | integration | 2D canvas / mixed selection |
| `dxf2gcode_canvas3d_test.py` | unit | 3D canvas transforms, view state and generated geometry |
| `dxf2gcode_canvas_warning_marker_test.py` | integration | canvas warning markers for invalid toolpaths |
| `dxf2gcode_pocket_multiselect_test.py` | integration | multi-select pocket activation |
| `dxf2gcode_tree_group_state_test.py` | integration | tree group state |
| `dxf2gcode_tree_multiselect_test.py` | integration | tree multi-select, export order and enable-state synchronization |
| `dxf2gcode_treeview_test.py` | integration | tree keyboard, selection and drag-and-drop behavior |
| `dxf2gcode_tsp_optimization_test.py` | unit | route distance, constraints, genetic optimizer and initializers |
| `dxf2gcode_parameter_state_test.py` | integration | GUI parameter state and persistence |
| `dxf2gcode_overcut_gui_test.py` | integration | GUI overcut controls and state |
| `dxf2gcode_stmove_gcode_test.py` | unit | StMove building, G-code export (support module for many tests) |
| `dxf2gcode_ellipse_offset_test.py` | regression | complete closed ellipse offsets and a real GIR corridor case |
| `dxf2gcode_offset_geometry_test.py` | unit/regression | offset distance, continuity, closure and intersection invariants |
| `dxf2gcode_spline_end_test.py` | regression | short spline end segments and offset behavior |
| `dxf2gcode_pocketmill_zigzag_test.py` | unit | pocket zig-zag start/points (also provides the DXF loader helper) |
| `dxf2gcode_gir_loop_test.py` | unit/regression | GIR / LIR loop splitting of the offset |
| `dxf2gcode_offset_status_test.py` | unit | `offset_status` classification |
| `dxf2gcode_breaks_pass_test.py` | regression | ticket #150 breaks/tabs |
| `dxf2gcode_pocketing_ticket176_test.py` | regression | ticket #176 missing pocket lines / crash |
| `dxf2gcode_pocketing_clearance_test.py` | regression | pocket edge clearance |
| `dxf2gcode_pocket_compensation_test.py` | regression | G40/G41/G42 offset geometry |
| `dxf2gcode_pocket_comp_mode_test.py` | regression | `pocket_compensation_mode` behaviour + GUI gating |
| `dxf2gcode_pocket_edge_clearance_test.py` | regression | edge clearance relative to the offset contour |
| `dxf2gcode_config_pocketing_test.py` | unit/regression | config versioning and migration |
| `dxf2gcode_leadmove_test.py` | unit | geometry of the lead in / lead out / overcut |
| `dxf2gcode_leadmove_function_test.py` | unit/integration | lead in / lead out / overcut: errors, depth passes, configuration |
| `dxf2gcode_leadmove_golden_test.py` | regression | G-Code of the lead in / lead out / overcut (reference files in `tests/golden`) |
| `dxf2gcode_leadmove_project_test.py` | unit | persistence of the layer values and overrides in the project file (`.d2g`) |
| `dxf2gcode_leadmove_common_test.py` | unit/integration | common radius / length of the lead in and the lead out: methods, GUI dropdowns, tool table validation, config migration |
| `dxf2gcode_leadmove_startpoint_test.py` | unit/integration | the lead in / lead out are at the start point set by the user, also with the option "split line segments" |
| `dxf2gcode_leadmove_modes_test.py` | unit/integration | the four methods of the lead in / lead out: generated geometry elements and the resulting G-Code movements |
| `dxf2gcode_overcut_test.py` | unit/integration | the overcut: the length per tool, the activation per shape, the standard of the configuration file, the migration |
| `dxf2gcode_scalebar_test.py` | unit/integration | scale bar: units, zoom, viewport position, config option |

Modules that mutate global configuration state reset it again in
`tearDownModule` so the suite passes independently of the module order.

The suite's test count is not a code-coverage measurement. `coverage.py` is
optional and is not a runtime dependency. To collect branch coverage for the
application package, including the GUI and CLI subprocess workflows, install
`coverage.py` 7.10 or newer in the Python environment used to run the suite,
then set `D2G_SOURCE_ROOT` to the absolute repository root and run:

```
python -m coverage erase --rcfile tests/coverage.ini
python -m coverage run --rcfile tests/coverage.ini tests/run_tests.py full
python -m coverage combine --rcfile tests/coverage.ini
python -m coverage report --rcfile tests/coverage.ini -m
```

The configuration follows Python subprocesses and writes its data to the
ignored `.coverage` file in the repository root. For a quick check on the core
group, replace `full` with `fast`. Review coverage by module and critical
behavior; no overall minimum is set. Use the report to find meaningful
untested paths, then add regression tests for those behaviors rather than
aiming to execute every line.

The golden G-code files in `tests/golden/` are output regression fixtures used
by the lead-move tests. The DXF drawings in `dxf/` also serve as fixtures for
the importer, ellipse-offset and CLI export regressions; keep assertions tied
to geometric or emitted G-code behavior when updating them.

## Diagnostics and profiling

Temporary scripts for debugging, profiling or performance comparisons are
**not** part of the test suite. Keep them out of `tests/` (for example in an
untracked local directory, or a future `tools/` directory) and remember that
`python -m unittest discover -s tests -p "dxf2gcode_*test.py"` only picks up
files matching that pattern.

`dxf2gcode_numeric_display_test.py` checks configurable mm/inch/angle display,
full-precision focus/input and compiled translations. The machining-panel
workflow also checks shared resizing columns, fixed visible status buttons
and changing display settings without modifying the machining project.
