"""Tests for the legacy project persistence adapters."""
from __future__ import absolute_import

import os
import sys
import tempfile
import unittest

_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [_TEST_DIR, os.path.join(os.path.dirname(_TEST_DIR), "source")]

from dxf2gcode.adapters.project.file_store import LegacyProjectFileStore  # noqa: E402
from dxf2gcode.adapters.project.legacy_repository import (  # noqa: E402
    LegacyProjectRepository,
)
from dxf2gcode.adapters.project.legacy_d2g import (  # noqa: E402
    D2G_HEADER,
    decode_d2g,
)
from dxf2gcode.application.projects import LoadProject, SaveProject  # noqa: E402


class TestLegacyD2GCodec(unittest.TestCase):
    def test_decodes_supported_legacy_version_and_literal_values(self):
        content = (D2G_HEADER % "1.1") + '\n' + \
            'd2g.file = "part.dxf"\n' + \
            'd2g.layers = [{"name": "MILL", "shapes": []}]\n'

        document = decode_d2g(content)

        self.assertEqual(document.version, 1.1)
        self.assertEqual(document.values["file"], "part.dxf")
        self.assertEqual(document.values["layers"],
                         [{"name": "MILL", "shapes": []}])

    def test_rejects_unknown_attributes(self):
        content = (D2G_HEADER % "1.3") + "\nd2g.window = None\n"

        with self.assertRaisesRegex(ValueError, "Unknown/dangerous attribute"):
            decode_d2g(content)

    def test_rejects_executable_values(self):
        content = (D2G_HEADER % "1.3") + \
            "\nd2g.file = __import__('os').getcwd()\n"

        with self.assertRaises(ValueError):
            decode_d2g(content)


class TestLegacyProjectFileStore(unittest.TestCase):
    def test_reads_and_writes_project_text(self):
        store = LegacyProjectFileStore()
        handle, filename = tempfile.mkstemp(suffix=".d2g")
        os.close(handle)
        self.addCleanup(lambda: os.path.exists(filename) and os.remove(filename))

        content = (D2G_HEADER % "1.3") + '\nd2g.file = "part.dxf"\n'
        store.write_text(filename, content)

        self.assertEqual(store.read_text(filename), content)


class TestLegacyProjectRepository(unittest.TestCase):
    def test_load_use_case_returns_a_decoded_document(self):
        content = (D2G_HEADER % "1.3") + '\nd2g.file = "part.dxf"\n'

        class MemoryStore(object):
            def read_text(self, filename):
                self.filename = filename
                return content

        store = MemoryStore()
        document = LoadProject(LegacyProjectRepository(store)).execute(
            "part.d2g")

        self.assertEqual(store.filename, "part.d2g")
        self.assertEqual(document.version, 1.3)
        self.assertEqual(document.values["file"], "part.dxf")

    def test_save_use_case_passes_serialized_content_to_repository(self):
        class MemoryRepository(object):
            def save(self, filename, content):
                self.saved = (filename, content)

        repository = MemoryRepository()
        SaveProject(repository).execute("part.d2g", "legacy project text")

        self.assertEqual(repository.saved,
                         ("part.d2g", "legacy project text"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
