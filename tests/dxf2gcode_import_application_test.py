"""Tests for the application-facing DXF import boundary."""
from __future__ import absolute_import

import os
import sys
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [_TEST_DIR, os.path.join(os.path.dirname(_TEST_DIR), "source")]

from dxf2gcode.application.importing import (  # noqa: E402
    ImportDiagnostic,
    ImportDrawing,
    ImportResult,
)
from dxf2gcode.adapters.dxf.reader import DxfReaderAdapter  # noqa: E402
from dxf2gcode.adapters.dxf.parser import ReadDXF  # noqa: E402
from dxf2gcode.presentation.qt.qt_compat import QtCore  # noqa: E402


class _FakeReader(object):
    def __init__(self, result):
        self.result = result
        self.filename = None

    def read(self, filename):
        self.filename = filename
        return self.result


class TestImportDrawing(unittest.TestCase):
    def test_use_case_delegates_to_reader_and_returns_diagnostics(self):
        drawing = object()
        diagnostics = (ImportDiagnostic("warning", "Import", "Notice"),)
        result = ImportResult(drawing=drawing, diagnostics=diagnostics)
        reader = _FakeReader(result)

        actual = ImportDrawing(reader).execute("part.dxf")

        self.assertEqual(reader.filename, "part.dxf")
        self.assertIs(actual.drawing, drawing)
        self.assertEqual(actual.diagnostics, diagnostics)

    @patch("dxf2gcode.adapters.dxf.reader.ReadDXF")
    def test_legacy_adapter_wraps_existing_parser_payload(self, read_dxf):
        drawing = read_dxf.return_value
        drawing.diagnostics = [
            ImportDiagnostic("short_elements_skipped", "Short Elements", "Skipped")
        ]

        result = DxfReaderAdapter().read("part.dxf")

        read_dxf.assert_called_once_with("part.dxf")
        self.assertIs(result.drawing, drawing)
        self.assertEqual(result.diagnostics, tuple(drawing.diagnostics))

    @patch("dxf2gcode.adapters.dxf.reader.ReadDXF")
    def test_legacy_adapter_passes_an_explicit_config(self, read_dxf):
        drawing = read_dxf.return_value
        drawing.diagnostics = []
        config = object()

        result = DxfReaderAdapter(config).read("part.dxf")

        read_dxf.assert_called_once_with("part.dxf", config=config)
        self.assertIs(result.drawing, drawing)

    def test_parser_collects_invalid_group_code_without_showing_dialog(self):
        parser = ReadDXF.__new__(ReadDXF)
        QtCore.QObject.__init__(parser)
        parser.diagnostics = []
        parser.tr = lambda message: message

        pairs = parser.Get_Line_Pairs(["0", "SECTION", "bad-code", "BROKEN"])

        self.assertEqual(pairs.nrs, 1)
        self.assertEqual(len(parser.diagnostics), 1)
        self.assertEqual(parser.diagnostics[0].code, "invalid_line_pair_code")
        self.assertIn("bad-code", parser.diagnostics[0].message)


if __name__ == "__main__":
    unittest.main(verbosity=2)
