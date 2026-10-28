# DXF2GCODE source package

The Python package is under `dxf2gcode/` and follows these package boundaries:

- `bootstrap/` starts the GUI and builds runtime dependencies.
- `domain/` contains geometry, project models and toolpath values.
- `application/` coordinates import, project, export and optimization flows.
- `adapters/` handles DXF, project/configuration files and postprocessors.
- `presentation/qt/` contains the Qt interface, generated UI modules and assets.

Run the program from this directory with `python dxf2gcode.py`. UI and resource
modules are generated into `dxf2gcode/presentation/qt/generated/` by
`python make_py_uic.py`; translations are built from `i18n/*.ts` by
`python make_tr.py`. The packaging metadata is in `st-setup.py` and
`setup.py`; `dxf2gcode.pro` lists the current package recursively for Qt
Creator and Linguist.

The test runner lives at the repository root: `python tests/run_tests.py full`.
