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
* The application dependencies: `PySide6`, `configobj` and `validate`
  (see `source/setup.py` / `source/requires.txt`).
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

Run the complete suite from the **repository root**:

```
python -m unittest discover -s tests -t tests -p "dxf2gcode_*test.py"
```

Add `-v` for the verbose per-test output.

The same command works from any directory if the paths are given absolute:

```
python -m unittest discover -s <repo>/tests -t <repo>/tests -p "dxf2gcode_*test.py"
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
| `dxf2gcode_test.py` | integration | opens every bundled DXF |
| `dxf2gcode_canvas_mixed_test.py` | integration | 2D canvas / mixed selection |
| `dxf2gcode_pocket_multiselect_test.py` | integration | multi-select pocket activation |
| `dxf2gcode_tree_group_state_test.py` | integration | tree group state |
| `dxf2gcode_tree_multiselect_test.py` | integration | tree multi-select |
| `dxf2gcode_stmove_gcode_test.py` | unit | StMove building, G-code export (support module for many tests) |
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
| `dxf2gcode_scalebar_test.py` | unit/integration | scale bar: units, zoom, viewport position, config option |

Modules that mutate global configuration state reset it again in
`tearDownModule` so the suite passes independently of the module order.

## Diagnostics and profiling

Temporary scripts for debugging, profiling or performance comparisons are
**not** part of the test suite. Keep them out of `tests/` (for example in an
untracked local directory, or a future `tools/` directory) and remember that
`python -m unittest discover -s tests -p "dxf2gcode_*test.py"` only picks up
files matching that pattern.
