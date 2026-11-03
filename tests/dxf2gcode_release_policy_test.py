"""Release cleanup must preserve stable releases and unrelated previews."""

import copy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from release_policy import develop_build_number, release_marker, retention_candidates, write_checksums, verify_checksums
from prepare_release import manifest_for
import prepare_release
from dxf2gcode.bootstrap.version_metadata import VersionInfo
from tools.build.release_metadata import msi_version
import publish_release


class TestReleasePolicy(unittest.TestCase):
    def release(self, number):
        revision = '%040x' % number
        return dict(id=number, tag_name='develop-ci-%d' % number, prerelease=True,
                    name='DXF2GCODE Develop 2.0.0.dev%d' % number,
                    draft=False, target_commitish=revision,
                    body=release_marker(revision, number),
                    published_at='2026-11-%02dT00:00:00Z' % number)

    def test_develop_versions_continue_after_workflow_rename_and_on_retries(self):
        releases = [self.release(10), self.release(11)]
        draft = self.release(20)
        draft['draft'] = True
        stable = self.release(21)
        stable['prerelease'] = False
        self.assertEqual(develop_build_number(releases+[draft, stable], '999'), 12)
        self.assertEqual(develop_build_number(releases, '11'), 11)
        self.assertEqual(develop_build_number([], '999'), 1)
        releases[1]['name'] = 'Renamed without a version'
        with self.assertRaises(ValueError):
            develop_build_number(releases, '999')

    def test_cleanup_keeps_ten_newest_and_all_unrelated_releases(self):
        releases = [self.release(i) for i in range(1, 14)]
        unrelated = []
        for changed in (dict(prerelease=False), dict(draft=True), dict(body='manual preview'),
                        dict(tag_name='v20261102'), dict(target_commitish='develop')):
            item = self.release(14)
            item.update(changed)
            unrelated.append(item)
        original = copy.deepcopy(releases + unrelated)
        self.assertEqual([r['id'] for r in retention_candidates(releases + unrelated)], [3, 2, 1])
        self.assertEqual(releases + unrelated, original)
        self.assertEqual(retention_candidates(unrelated), [])

    def test_marker_must_match_both_revision_and_run(self):
        release = self.release(1)
        release['body'] = release_marker('a'*40, 1)
        self.assertEqual(retention_candidates([release], keep=1), [])
        with self.assertRaises(ValueError):
            retention_candidates([], keep=0)

    def test_checksums_detect_changed_added_and_missing_assets(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            asset = folder / 'package.zip'
            asset.write_bytes(b'original')
            expected = write_checksums(folder)
            self.assertEqual(verify_checksums(folder), expected)
            asset.write_bytes(b'corrupt')
            with self.assertRaises(ValueError):
                verify_checksums(folder)
            asset.write_bytes(b'original')
            (folder / 'unexpected.exe').write_bytes(b'new')
            with self.assertRaises(ValueError):
                verify_checksums(folder)
            (folder / 'unexpected.exe').unlink()
            asset.unlink()
            with self.assertRaises(ValueError):
                verify_checksums(folder)


class TestReleasePublication(unittest.TestCase):
    def manifest(self, event=None, ref='refs/heads/develop'):
        event = event or ('push' if ref.startswith('refs/tags/') else 'workflow_dispatch')
        return manifest_for('2.0.0.dev0', 'a'*40, 1793610000, '1234', 123, event, ref)

    def test_release_description_shows_highlights_and_preserves_provenance(self):
        manifest = self.manifest()
        marker = release_marker(manifest['revision'], manifest['run_id'])
        text = publish_release.release_description(manifest, marker)
        self.assertIn('Highlights of the 2.0.0 development line', text)
        self.assertLess(text.index('Highlights'), text.index('<details>'))
        self.assertIn('**unsigned**', text)
        self.assertIn(manifest['revision'], text)
        self.assertIn(marker, text)
        stable = self.manifest(ref='refs/tags/v2.0.0')
        self.assertTrue(publish_release.release_description(stable, marker).startswith('Stable release 2.0.0.'))

    def test_semver_channels_and_msi_limits(self):
        develop = self.manifest()
        self.assertEqual((develop['version'], develop['msi_version']), ('2.0.0.dev123', '2.0.123'))
        self.assertEqual(self.manifest(ref='refs/tags/v2.0.0')['msi_version'], '2.0.0')
        self.assertEqual(self.manifest(event='pull_request', ref='refs/pull/4/merge')['kind'], 'test')
        self.assertEqual(self.manifest(event='push')['kind'], 'test')
        self.assertEqual(self.manifest(ref='refs/heads/feature')['kind'], 'test')
        with self.assertRaises(ValueError):
            self.manifest(ref='refs/tags/v1.0.0')
        with self.assertRaises(ValueError):
            msi_version('2.0.0.dev65536')

    def test_manifest_separates_release_counter_from_workflow_run_number(self):
        manifest = manifest_for('2.0.0.dev0', 'a'*40, 1793610000, '999', 1,
                                'workflow_dispatch', 'refs/heads/develop', build_number=12)
        self.assertEqual(manifest['run_number'], 1)
        self.assertEqual(manifest['build_number'], 12)
        self.assertEqual((manifest['version'], manifest['msi_version']), ('2.0.0.dev12', '2.0.12'))

    def test_staging_keeps_build_tools_and_excludes_previous_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source'
            for relative in ('tools/build/qt_assets.py', 'build/old.exe',
                             'dxf2gcode/_version.py', 'dxf2gcode/__pycache__/old.pyc'):
                path = source / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('original', encoding='utf-8')
            info = VersionInfo(version='2.0.0.dev0', revision='a'*40, dirty=False)
            with patch.object(prepare_release, 'ROOT', root), \
                    patch.object(prepare_release, 'read_releases', return_value=[]), \
                    patch.object(prepare_release, 'develop_build_number', return_value=123), \
                    patch.object(prepare_release, 'capture_build_info', return_value=info), \
                    patch.object(prepare_release.subprocess, 'check_output',
                                 side_effect=['', 'a'*40, '1793610000']), \
                    patch.dict(os.environ, GITHUB_SHA='a'*40, GITHUB_RUN_ID='1234',
                               GITHUB_RUN_NUMBER='123', GITHUB_EVENT_NAME='workflow_dispatch',
                               GITHUB_REF='refs/heads/develop', GITHUB_OUTPUT='', GITHUB_REPOSITORY='owner/repo'):
                prepare_release.prepare(root / 'staged')
            staged = root / 'staged/source'
            self.assertTrue((staged / 'tools/build/qt_assets.py').is_file())
            self.assertFalse((staged / 'build').exists())
            self.assertFalse((staged / 'dxf2gcode/__pycache__').exists())
            self.assertEqual((source / 'dxf2gcode/_version.py').read_text(), 'original')
            data = json.loads((staged / 'dxf2gcode/_build_metadata.json').read_text())
            self.assertEqual((data['version'], data['revision']), ('2.0.0.dev123', 'a'*40))

    def fixture(self, folder, manifest):
        (folder / 'release-manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
        for name in ('package.whl', 'source.tar.gz', 'windows.zip', 'windows.msi'):
            (folder / name).write_bytes(b'package')
        write_checksums(folder)

    def run_publication(self, kind='develop', complete=True, event=None, draft=False):
        event = event or ('workflow_dispatch' if kind == 'develop' else 'push')
        manifest = self.manifest(ref='refs/tags/v2.0.0' if kind == 'stable' else 'refs/heads/develop')
        calls = []
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            self.fixture(folder, manifest)
            def api(*args, payload=None):
                calls.append((args, payload))
                endpoint = next((arg for arg in args if arg.startswith('repos/')), '')
                if endpoint.endswith('/git/ref/heads/develop'):
                    return {'object': {'sha': 'a'*40}}
                if endpoint.endswith('/releases?per_page=100'):
                    return [[dict(id=7, tag_name=manifest['tag'], target_commitish='a'*40,
                                  body=release_marker('a'*40, manifest['run_id']), draft=True,
                                  name='DXF2GCODE Develop 2.0.0.dev122', assets=[])]] if draft else [[]]
                if payload and payload.get('draft') is True:
                    return dict(id=7, assets=[])
                if args == ('api', 'repos/owner/repo/releases/7'):
                    return dict(assets=[dict(name=p.name, size=p.stat().st_size)
                                        for p in folder.iterdir() if complete or p.name != 'windows.zip'])
                if '/artifacts?' in endpoint:
                    return [dict(artifacts=[])]
                return None
            with patch.dict(os.environ, GITHUB_EVENT_NAME=event), \
                    patch.object(publish_release, 'gh', side_effect=api), \
                    patch.object(publish_release.subprocess, 'run'):
                publish_release.publish(folder, 'owner/repo', 'a'*40,
                                        'refs/tags/v2.0.0' if kind == 'stable' else 'refs/heads/develop')
        return calls

    def test_only_stable_releases_become_latest(self):
        for kind, latest in (('develop', 'false'), ('stable', 'true')):
            calls = self.run_publication(kind)
            published = [payload for args, payload in calls
                         if '--method' in args and 'PATCH' in args]
            self.assertEqual(published, [dict(draft=False, make_latest=latest)])

    def test_incomplete_upload_remains_draft_and_cannot_trigger_cleanup(self):
        with self.assertRaisesRegex(ValueError, 'incomplete'):
            self.run_publication(complete=False)

    def test_pr_cannot_publish(self):
        with self.assertRaisesRegex(ValueError, 'manual develop'):
            self.run_publication(event='pull_request')

    def test_develop_push_cannot_publish_even_with_a_develop_manifest(self):
        with self.assertRaisesRegex(ValueError, 'manual develop'):
            self.run_publication(event='push')

    def test_retried_draft_description_matches_the_current_build(self):
        calls = self.run_publication(draft=True)
        updated = [payload for args, payload in calls if payload and 'body' in payload]
        self.assertEqual(updated[0]['name'], 'DXF2GCODE Develop 2.0.0.dev123')
        self.assertIn('Package version: `2.0.0.dev123`', updated[0]['body'])


if __name__ == '__main__':
    unittest.main()
