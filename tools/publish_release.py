"""Publish verified CI packages, then prune only this workflow's previews."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
from urllib.parse import quote

from release_policy import release_marker, retention_candidates, verify_checksums


def gh(*arguments, payload=None):
    result = subprocess.run(['gh', *arguments], input=None if payload is None else json.dumps(payload),
                            text=True, capture_output=True, check=True)
    return json.loads(result.stdout) if result.stdout.strip() else None


def remove_transient_packages(repository, run_id):
    pages = gh('api', '--paginate', '--slurp',
               'repos/%s/actions/runs/%s/artifacts?per_page=100' % (repository, run_id))
    for page in pages:
        for artifact in page['artifacts']:
            if artifact['name'] in ('release-wheel', 'release-windows'):
                gh('api', 'repos/%s/actions/artifacts/%s' % (repository, artifact['id']), '--method', 'DELETE')


def publish(folder, repository, revision, ref):
    folder = Path(folder)
    verify_checksums(folder)
    manifest = json.loads((folder / 'release-manifest.json').read_text(encoding='utf-8'))
    for suffix in ('.whl', '.tar.gz', '.zip', '.msi'):
        if len(list(folder.glob('*'+suffix))) != 1:
            raise ValueError('Expected exactly one release package of type '+suffix)
    if manifest['revision'] != revision or os.environ.get('GITHUB_EVENT_NAME') != 'push':
        raise ValueError('Only tested push commits may publish')
    kind, tag = manifest['kind'], manifest['tag']
    if ((kind == 'develop' and ref != 'refs/heads/develop') or
            (kind == 'stable' and ref != 'refs/tags/'+tag) or kind not in ('develop', 'stable')):
        raise ValueError('Release channel does not match the triggering ref')
    if kind == 'develop':
        tip = gh('api', 'repos/%s/git/ref/heads/develop' % repository)
        if tip['object']['sha'] != revision:
            print('A newer develop commit exists; keeping the previous public download.')
            return
    pages = gh('api', '--paginate', '--slurp', 'repos/%s/releases?per_page=100' % repository)
    releases = [release for page in pages for release in page]
    marker = release_marker(revision, manifest['run_id'])
    release = next((item for item in releases if item['tag_name'] == tag), None)
    if release is not None:
        if marker not in (release.get('body') or '') or release['target_commitish'] != revision:
            raise ValueError('Refusing to modify an unrelated release')
        if not release['draft']:
            remove_transient_packages(repository, manifest['run_id'])
            print('This tested release is already published; leaving it unchanged.')
            return
    else:
        body = ('Commit: `%s`\n\nPackage version: `%s`\n\nMSI ProductVersion: `%s`\n\n'
                'Windows signing: `%s`. Verify downloads with `SHA256SUMS`.\n\n%s') % (
                    revision, manifest['version'], manifest['msi_version'], manifest['windows_signing'], marker)
        release = gh('api', 'repos/%s/releases' % repository, '--method', 'POST', '--input', '-',
                     payload=dict(tag_name=tag, target_commitish=revision,
                                  name='DXF2GCODE %s%s' % ('Develop ' if kind == 'develop' else '', manifest['version']),
                                  body=body, draft=True, prerelease=kind == 'develop', make_latest='false'))
    # Recover an interrupted draft without touching any published release.
    for asset in release.get('assets', []):
        gh('api', 'repos/%s/releases/assets/%s' % (repository, asset['id']), '--method', 'DELETE')
    for path in sorted(folder.iterdir()):
        if path.is_file():
            subprocess.run(['gh', 'release', 'upload', tag, str(path), '--repo', repository], check=True)
    uploaded = gh('api', 'repos/%s/releases/%s' % (repository, release['id']))
    actual = {asset['name']: asset['size'] for asset in uploaded['assets']}
    expected = {path.name: path.stat().st_size for path in folder.iterdir() if path.is_file()}
    if actual != expected:
        raise ValueError('Uploaded release assets are incomplete; leaving a draft')
    for asset in uploaded['assets']:
        if asset.get('digest'):
            with (folder / asset['name']).open('rb') as stream:
                digest = 'sha256:'+hashlib.file_digest(stream, 'sha256').hexdigest()
            if asset['digest'] != digest:
                raise ValueError('Uploaded asset checksum differs; leaving a draft')
    gh('api', 'repos/%s/releases/%s' % (repository, release['id']), '--method', 'PATCH', '--input', '-',
       payload=dict(draft=False, make_latest='false' if kind == 'develop' else 'true'))
    if kind == 'develop':
        pages = gh('api', '--paginate', '--slurp', 'repos/%s/releases?per_page=100' % repository)
        for old in retention_candidates([item for page in pages for item in page]):
            tag_path = quote(old['tag_name'], safe='')
            endpoint = 'repos/%s/git/refs/tags/%s' % (repository, tag_path)
            target = gh('api', 'repos/%s/git/ref/tags/%s' % (repository, tag_path))
            if target['object']['type'] != 'commit' or target['object']['sha'] != old['target_commitish']:
                raise ValueError('Refusing cleanup: a development tag was changed outside CI')
            gh('api', 'repos/%s/releases/%s' % (repository, old['id']), '--method', 'DELETE')
            gh('api', endpoint, '--method', 'DELETE')
            print('Removed owned preview:', old['tag_name'])
    remove_transient_packages(repository, manifest['run_id'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder', type=Path)
    args = parser.parse_args()
    publish(args.folder, os.environ['GITHUB_REPOSITORY'], os.environ['GITHUB_SHA'], os.environ['GITHUB_REF'])
