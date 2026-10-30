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

Use Python 3.9 or newer with PyQt5 or PyQt6, PyOpenGL and configobj. For PDF or PostScript
input, install pdftops and pstoedit as well.

Install the Python package
--------------------------

Install a release wheel or source archive in a virtual environment:

  python3 -m venv .venv
  . .venv/bin/activate
  python -m pip install ./dxf2gcode-20261028-py3-none-any.whl
  dxf2gcode

pipx can also install the wheel in an isolated application environment.
Release archives contain UI/resource modules and German, French and Russian
translations. Users do not need Qt compilers to install a release.

Build a release from a repository checkout
----------------------------------------

Install the build frontend and both Qt bindings in a developer environment:

  python -m pip install build PyQt5 PyQt6 configobj PyOpenGL

Install Qt 6 rcc and Qt Linguist lrelease using the operating system's
development tools and put them on PATH. From this directory, run:

  make package PYTHON=python

This prepares both Qt variants and translations, then runs python -m build
to produce a wheel and source archive under dist/. See README.md for the
equivalent commands without Make.

On Windows, the separate cx_Freeze MSI builder is:

  python build_windows.py bdist_msi

Do not use the old st-setup.py install or setup.py install commands.

Tests
-----

From the repository root, run the complete test suite with:

  python tests/run_tests.py full
