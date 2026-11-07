"""Atomic project writes; UTF-8 JSON and platform-encoded legacy readers."""

import locale
import os
from pathlib import Path
import tempfile


class LegacyProjectFileStore:
    """Read legacy/UTF-8 projects and replace destination files atomically."""

    def read_text(self, filename):
        content = Path(filename).read_bytes()
        try:
            return content.decode('utf-8-sig')
        except UnicodeDecodeError:
            return content.decode(locale.getpreferredencoding(False))

    def write_text(self, filename, content):
        target = Path(filename)
        is_current = content.lstrip().startswith('{')
        if is_current and target.exists() and not self.read_text(target).lstrip().startswith('{'):
            raise IOError('Save a migrated project under a new filename')
        encoding = 'utf-8' if is_current else locale.getpreferredencoding(False)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', encoding=encoding,
                    newline='\n' if is_current else None,
                    dir=str(target.parent), prefix='.' + target.name + '.', delete=False) as stream:
                temporary = stream.name
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, target)
        finally:
            if temporary and os.path.exists(temporary):
                os.unlink(temporary)

