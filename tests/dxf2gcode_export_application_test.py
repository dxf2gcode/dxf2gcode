"""Regression coverage for the shared GUI and CLI export action."""
from __future__ import absolute_import

import os
import sys
import unittest

_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(_TEST_DIR), "source"))

from dxf2gcode.application.exporting import ExportToolpath  # noqa: E402


class _PostProcessorStub:
    def __init__(self):
        self.calls = []
        self.export_errors = ["warning"]

    def getPostProVars(self, index):
        self.calls.append(("profile", index))

    def exportShapes(self, filename, output_filename, layers):
        self.calls.append(("export", filename, output_filename, layers))


class TestExportToolpath(unittest.TestCase):
    def test_selects_profile_exports_existing_order_and_returns_diagnostics(self):
        postprocessor = _PostProcessorStub()
        layers = [object(), object()]

        errors = ExportToolpath(postprocessor).execute(
            "drawing.dxf", "drawing.ngc", layers, postprocessor_index=2)

        self.assertEqual(postprocessor.calls, [
            ("profile", 2),
            ("export", "drawing.dxf", "drawing.ngc", layers),
        ])
        self.assertEqual(errors, ("warning",))


if __name__ == "__main__":
    unittest.main(verbosity=2)
