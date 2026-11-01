#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run the focused core suite or the complete DXF2GCODE test suite."""
from __future__ import absolute_import

import argparse
import os
import sys
import unittest

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.dirname(TEST_DIR)
sys.path[:0] = [TEST_DIR, os.path.join(REPO_DIR, "source")]

FAST_MODULES = (
    "dxf2gcode_import_contract_test",
    "dxf2gcode_postpro_config_test",
    "dxf2gcode_offset_geometry_test",
    "dxf2gcode_ellipse_offset_test",
    "dxf2gcode_spline_end_test",
    "dxf2gcode_tsp_optimization_test",
    "dxf2gcode_toolpath_depths_test",
    "dxf2gcode_toolpath_contract_test",
    "dxf2gcode_shape_tool_test",
    "dxf2gcode_tool_change_test",
    "dxf2gcode_stmove_gcode_test",
    "dxf2gcode_leadmove_project_test",
    "dxf2gcode_workflow_test",
    "dxf2gcode_mainwindow_workflow_test",
    "dxf2gcode_test",
)


def build_suite(name):
    loader = unittest.TestLoader()
    if name == "full":
        return loader.discover(
            start_dir=TEST_DIR,
            pattern="dxf2gcode_*test.py",
            top_level_dir=TEST_DIR)

    suite = unittest.TestSuite()
    for module in FAST_MODULES:
        suite.addTests(loader.loadTestsFromName(module))
    return suite


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "suite", choices=("fast", "full"), nargs="?", default="full",
        help="fast runs core import/geometry/export/project checks; full discovers all tests")
    args = parser.parse_args(argv)

    result = unittest.TextTestRunner(verbosity=2).run(build_suite(args.suite))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
