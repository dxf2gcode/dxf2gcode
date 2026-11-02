"""Pure release ownership and retention rules shared by CI and focused tests."""

from datetime import datetime
import hashlib
from pathlib import Path
import re


DEVELOP_PREFIX = 'develop-ci-'
MARKER_PREFIX = '<!-- dxf2gcode-ci1:'


def release_marker(revision, run_id):
    if not re.fullmatch(r'[0-9a-f]{40}', revision) or not str(run_id).isdigit():
        raise ValueError('Invalid release provenance')
    return '%s%s:%s -->' % (MARKER_PREFIX, revision, run_id)


def owned_develop_release(release):
    """Never classify stable, draft or manually named previews as disposable."""
    match = re.fullmatch(r'develop-ci-([0-9]+)', release.get('tag_name', ''))
    if not match or not release.get('prerelease') or release.get('draft'):
        return False
    revision = release.get('target_commitish', '')
    if not re.fullmatch(r'[0-9a-f]{40}', revision):
        return False
    return release_marker(revision, match[1]) in (release.get('body') or '')


def retention_candidates(releases, keep=10):
    if keep < 1:
        raise ValueError('At least one development release must be retained')
    owned = [release for release in releases if owned_develop_release(release)]
    owned.sort(key=lambda item: (datetime.fromisoformat(item['published_at'].replace('Z', '+00:00')),
                                item['id']), reverse=True)
    return owned[keep:]


def checksums(folder):
    """Hash final files only; never include the checksum file in itself."""
    folder = Path(folder)
    result = {}
    for path in sorted(folder.iterdir()):
        if path.is_file() and path.name != 'SHA256SUMS':
            with path.open('rb') as stream:
                result[path.name] = hashlib.file_digest(stream, 'sha256').hexdigest()
    if not result:
        raise ValueError('No release files')
    return result


def write_checksums(folder):
    values = checksums(folder)
    (Path(folder) / 'SHA256SUMS').write_text(
        ''.join('%s  %s\n' % (digest, name) for name, digest in values.items()),
        encoding='utf-8')
    return values


def verify_checksums(folder):
    expected = {}
    for line in (Path(folder) / 'SHA256SUMS').read_text(encoding='utf-8').splitlines():
        digest, name = line.split('  ', 1)
        if Path(name).name != name or not re.fullmatch(r'[0-9a-f]{64}', digest):
            raise ValueError('Invalid checksum entry')
        if name in expected:
            raise ValueError('Duplicate checksum entry')
        expected[name] = digest
    if checksums(folder) != expected:
        raise ValueError('Release files do not match SHA256SUMS')
    return expected
