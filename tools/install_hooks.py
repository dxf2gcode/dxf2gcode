#!/usr/bin/env python3
"""Enable the versioned fast-test hook for this checkout and interpreter."""

from pathlib import Path
import subprocess
import sys


def install(root, interpreter):
    def git(*args, check=True):
        return subprocess.run(['git', '-C', str(root), *args], check=check,
                              capture_output=True, text=True)

    previous = git('config', '--get', 'core.hooksPath', check=False)
    if previous.returncode not in (0, 1):
        raise RuntimeError(previous.stderr.strip())
    if previous.stdout.strip() not in ('', '.githooks'):
        raise RuntimeError('An existing core.hooksPath is configured; integrate the hook manually')
    original = git('rev-parse', '--git-path', 'hooks/pre-commit').stdout.strip()
    original = Path(original)
    if not original.is_absolute():
        original = root / original
    if not previous.stdout.strip() and original.exists():
        raise RuntimeError('An existing pre-commit hook is installed; integrate it manually')

    hook = root / '.githooks' / 'pre-commit'
    hook.chmod(hook.stat().st_mode | 0o111)
    git('config', '--local', 'dxf2gcode.testPython', str(interpreter))
    git('config', '--local', 'core.hooksPath', '.githooks')
    print('Enabled pre-commit fast tests with: %s' % interpreter)


if __name__ == '__main__':
    try:
        install(Path(__file__).resolve().parents[1], Path(sys.executable).resolve())
    except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
        print('Cannot install Git hook: %s' % error, file=sys.stderr)
        raise SystemExit(1)
