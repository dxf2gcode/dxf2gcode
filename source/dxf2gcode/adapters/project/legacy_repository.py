"""Repository adapter for legacy and machining ``.d2g`` documents."""

from dxf2gcode.adapters.project.file_store import LegacyProjectFileStore
from dxf2gcode.adapters.project.machining_d2g import decode_project


class LegacyProjectRepository:
    """Read validated project documents and write serialized project text."""

    def __init__(self, file_store=None):
        self._file_store = file_store or LegacyProjectFileStore()

    def load(self, filename):
        return decode_project(self._file_store.read_text(filename))

    def save(self, filename, content):
        self._file_store.write_text(filename, content)
