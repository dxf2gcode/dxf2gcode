"""Publish verified CI packages, then prune only this workflow's previews."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from urllib.parse import quote

from release_policy import (owned_develop_release, publication_channel, release_marker,
                            retention_candidates, verify_checksums)


def changes_since_previous(repository, manifest, releases, highlights=None):
    """Describe only commits after the last published release in this channel."""
    candidates = [item for item in releases
                  if item['tag_name'] != manifest['tag'] and not item.get('draft')
                  and (owned_develop_release(item) if manifest['kind'] == 'develop' else
                       not item.get('prerelease') and re.fullmatch(r'v\d+\.\d+\.\d+', item['tag_name']))]
    heading = '### Changes in %s\n\n' % manifest['version']
    if not candidates:
        return heading + ('First published release in this channel; no previous release '
                          'is available for comparison. See the development-line overview below.') + (
                              '\n\n'+highlights.strip() if highlights else '')
    previous = max(candidates, key=lambda item: (item.get('published_at') or '', item['id']))
    baseline = previous['tag_name']
    endpoint = 'repos/%s/compare/%s...%s?per_page=100' % (
        repository, quote(baseline, safe=''), manifest['revision'])
    pages = gh('api', '--paginate', '--slurp', endpoint)
    if not pages or any(page.get('status') not in ('ahead', 'identical') for page in pages):
        raise ValueError('Previous release is not an ancestor of the current release')
    groups = {'Features': [], 'Fixes': [], 'Documentation': [], 'Maintenance and tests': []}
    seen = set()
    for page in pages:
        for commit in page['commits']:
            if commit['sha'] in seen:
                continue
            seen.add(commit['sha'])
            if len(commit.get('parents', [])) > 1:
                continue  # The constituent changes are listed, not the merge again.
            subject = (commit['commit']['message'].splitlines() or ['Untitled commit'])[0]
            match = re.match(r'([a-z]+)(?:\([^)]+\))?!?:\s*(.*)', subject)
            kind, title = match.groups() if match else ('other', subject)
            if match and subject.split(':', 1)[0].endswith('!'):
                title = 'Breaking change: ' + title
            group = {'feat': 'Features', 'fix': 'Fixes', 'docs': 'Documentation'}.get(
                kind, 'Maintenance and tests')
            title = title.replace('\\', '\\\\').replace('[', '\\[').replace(']', '\\]')
            title = title.replace('<', '&lt;').replace('>', '&gt;')
            groups[group].append('- %s ([`%s`](https://github.com/%s/commit/%s))' % (
                title, commit['sha'][:7], repository, commit['sha']))
    intro = 'Since [%s](https://github.com/%s/releases/tag/%s).\n\n' % (
        previous.get('name') or baseline, repository, quote(baseline, safe=''))
    sections = []
    for group, entries in groups.items():
        if entries:
            content = '#### %s\n\n%s' % (group, '\n'.join(entries))
            if group in ('Documentation', 'Maintenance and tests'):
                content = '<details>\n<summary>%s (%d)</summary>\n\n%s\n\n</details>' % (
                    group, len(entries), content)
            sections.append(content)
    if not sections:
        sections.append('No new non-merge commits since the previous release.')
    compare = 'https://github.com/%s/compare/%s...%s' % (
        repository, quote(baseline, safe=''), manifest['revision'])
    history = ('Commit subjects describe development steps; later commits can supersede earlier ones.\n\n'
               + '\n\n'.join(sections))
    if highlights:
        history = (highlights.strip() + '\n\n<details>\n<summary>Development commits</summary>\n\n'
                   + history + '\n\n</details>')
    return heading + intro + history + '\n\n[Full comparison](%s)' % compare


def release_description(manifest, marker, changes=None):
    base = manifest['version'].split('.dev', 1)[0]
    notes = Path(__file__).resolve().parents[1] / 'doc/release-notes' / (base+'.md')
    summary = notes.read_text(encoding='utf-8').strip()
    if not summary:
        raise ValueError('A concise release summary is required')
    channel = ('Development preview for the planned %s release.' % base
               if manifest['kind'] == 'develop' else 'Stable release %s.' % base)
    changes = changes or '### Changes in %s\n\nNo release comparison supplied.' % manifest['version']
    return ('%s\n\n%s\n\n'
            '<details>\n<summary>Overview of the %s development line</summary>\n\n%s\n\n</details>\n\n'
            'Downloads: Windows x64 ZIP (extract fully), per-user MSI, Python wheel and source archive.\n'
            'Windows signing: **%s**. Verify downloads with `SHA256SUMS`.\n\n'
            '<details>\n<summary>Build details</summary>\n\n'
            'Package version: `%s`\n\nCommit: `%s`\n\nMSI ProductVersion: `%s`\n\n'
            '</details>\n\n%s') % (channel, changes, base, summary, manifest['windows_signing'],
                                     manifest['version'], manifest['revision'],
                                     manifest['msi_version'], marker)


def gh(*arguments, payload=None):
    result = subprocess.run(['gh', *arguments], input=None if payload is None else json.dumps(payload),
                            text=True, encoding='utf-8', capture_output=True, check=True)
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
    kind, tag = manifest['kind'], manifest['tag']
    channel = publication_channel(os.environ.get('GITHUB_EVENT_NAME'), ref)
    if (manifest['revision'] != revision or channel is None or kind != channel or
            (kind == 'stable' and ref != 'refs/tags/'+tag)):
        raise ValueError('Publication requires a manual develop run or a matching stable tag push')
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
    notes = Path(__file__).resolve().parents[1] / 'doc/release-notes/releases' / (manifest['version']+'.md')
    highlights = notes.read_text(encoding='utf-8').strip() if notes.is_file() else None
    body = release_description(manifest, marker, changes_since_previous(repository, manifest, releases, highlights))
    if release is not None:
        # A failed run may be retried after another release has advanced the
        # counter. Refresh this owned draft to match the rebuilt manifest.
        gh('api', 'repos/%s/releases/%s' % (repository, release['id']), '--method', 'PATCH', '--input', '-',
           payload=dict(name='DXF2GCODE %s%s' % ('Develop ' if kind == 'develop' else '', manifest['version']),
                        body=body))
    else:
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
