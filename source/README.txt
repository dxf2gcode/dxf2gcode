DXF2GCODE
=========

DXF2GCODE converts 2D DXF drawings to CNC machine compatible G-Code. PDF and
PostScript input is supported through the optional pdftops and pstoedit tools.

Package structure
-----------------

The Python package is under dxf2gcode/:

  bootstrap/       GUI/CLI entry points and runtime wiring
  domain/          geometry, project state and toolpath values
  application/     import, project, preview, export and optimization flows
  adapters/        DXF, project/configuration and postprocessor integration
  presentation/qt/ Qt interface, generated UI modules and resources

Run from this directory with:

  python dxf2gcode.py

Dependencies
------------

Use Python 3 with PyQt5 or PyQt6, PyOpenGL and configobj. For PDF or PostScript
input, install pdftops and pstoedit as well.

Build and install
-----------------

Generate the UI/resource and translation files before building:

  python make_py_uic.py
  python make_tr.py

For a Python package build, run:

  python st-setup.py build
  python st-setup.py install

On Windows, setup.py builds the cx_Freeze installer:

  python setup.py bdist_msi

Tests
-----

From the repository root, run the complete test suite with:

  python tests/run_tests.py full
