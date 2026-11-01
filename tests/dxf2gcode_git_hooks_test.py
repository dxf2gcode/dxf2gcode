"""Exercise hook installation and commit rejection in disposable repositories."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which('git'), 'Git is required for hook integration')
class TestGitHooks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='d2g hook test ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.env = {key: value for key, value in os.environ.items()
                    if not key.startswith('GIT_')}
        self.env.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull)
        self.git('init')
        self.git('config', 'core.autocrlf', 'false')
        for relative in ('.githooks/pre-commit', 'tools/install_hooks.py'):
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)
        (self.root / 'tests').mkdir()
        (self.root / 'tests/run_tests.py').write_text(
            'import json, os, pathlib, sys\n'
            'pathlib.Path(".git/observed.json").write_text(json.dumps({\n'
            ' "args": sys.argv[1:], "index": os.environ.get("GIT_INDEX_FILE"),\n'
            ' "platform": os.environ.get("QT_QPA_PLATFORM")}))\n'
            'sys.exit(int(pathlib.Path(".git/fast-result").read_text()))\n',
            encoding='utf-8')

    def git(self, *args, check=True, env=None):
        return subprocess.run(
            ['git', '-c', 'user.name=Hook Test', '-c', 'user.email=hook@example.invalid',
             '-c', 'commit.gpgsign=false', *args], cwd=self.root,
            env=self.env if env is None else env, capture_output=True,
            text=True, check=check)

    def install(self):
        return subprocess.run([sys.executable, str(self.root / 'tools/install_hooks.py')],
                              cwd=self.root, env=self.env, capture_output=True, text=True)

    def test_fast_failure_blocks_commit_and_success_allows_it(self):
        installed = self.install()
        self.assertEqual(installed.returncode, 0, installed.stderr)
        self.assertEqual(self.git('config', '--get', 'core.hooksPath').stdout.strip(),
                         '.githooks')
        (self.root / 'payload.txt').write_text('commit this')
        self.git('add', 'payload.txt')
        result_file = self.root / '.git/fast-result'
        result_file.write_text('1')
        env = dict(self.env, GIT_INDEX_FILE=str(self.root / '.git/index'))
        failed = self.git('commit', '-m', 'test: reject failing fast suite',
                          check=False, env=env)
        self.assertNotEqual(failed.returncode, 0)
        self.assertNotEqual(self.git('rev-parse', '--verify', 'HEAD', check=False).returncode, 0)
        observed = json.loads((self.root / '.git/observed.json').read_text())
        self.assertEqual(observed, {'args': ['fast'], 'index': None, 'platform': 'offscreen'})
        result_file.write_text('0')
        passed = self.git('commit', '-m', 'test: accept passing fast suite', check=False)
        self.assertEqual(passed.returncode, 0, passed.stderr)

    def test_existing_hooks_are_not_overwritten(self):
        original = self.root / '.git/hooks/pre-commit'
        original.write_text('# existing hook\n')
        self.assertNotEqual(self.install().returncode, 0)
        self.assertEqual(original.read_text(), '# existing hook\n')
        original.unlink()
        self.git('config', 'core.hooksPath', 'custom-hooks')
        self.assertNotEqual(self.install().returncode, 0)
        self.assertEqual(self.git('config', '--get', 'core.hooksPath').stdout.strip(),
                         'custom-hooks')


if __name__ == '__main__':
    unittest.main()
