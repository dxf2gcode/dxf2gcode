"""Stage a clean tested commit without changing its checked-out version file."""

import argparse
from dataclasses import replace
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'source'))
from dxf2gcode.bootstrap.version_metadata import capture_build_info, write_build_metadata
from dxf2gcode._version import __version__
from tools.build.release_metadata import release_base, msi_version


def manifest_for(base, revision, epoch, run_id, run_number, event, ref):
    base = release_base(base)
    if not re.fullmatch(r'[0-9a-f]{40}', revision) or not str(run_id).isdigit() or int(run_number) < 1:
        raise ValueError('Invalid CI run or revision')
    stable = event == 'push' and ref.startswith('refs/tags/v')
    if stable and ref != 'refs/tags/v'+base:
        raise ValueError('Stable tag must match the declared target version')
    kind = 'stable' if stable else 'develop' if event == 'push' and ref == 'refs/heads/develop' else 'test'
    version = base if stable else base+'.dev'+str(run_number)
    date = datetime.fromtimestamp(int(epoch), timezone.utc).strftime('%Y%m%d')
    return dict(schema=1, revision=revision, source_date_epoch=int(epoch), date=date,
                run_id=str(run_id), run_number=int(run_number), kind=kind, version=version,
                msi_version=msi_version(version, run_number), windows_signing='unsigned',
                tag='v'+base if stable else 'develop-ci-'+str(run_id),
                wheel_build=date+'g'+revision[:7],
                artifact_stem='dxf2gcode-%s-%s-g%s' % (version, date, revision[:7]))


def prepare(output):
    output = Path(output).resolve()
    if output.exists() or (ROOT / 'source').resolve() in output.parents:
        raise ValueError('Staging directory must be new and outside source/')
    def git(*args):
        return subprocess.check_output(['git', '-C', str(ROOT), *args], text=True).strip()
    if git('status', '--porcelain'):
        raise ValueError('Release preparation requires a clean checkout')
    revision = git('rev-parse', 'HEAD')
    if revision != os.environ['GITHUB_SHA']:
        raise ValueError('Checkout and tested workflow commit differ')
    manifest = manifest_for(__version__, revision, git('show', '-s', '--format=%ct', 'HEAD'),
                            os.environ['GITHUB_RUN_ID'], os.environ['GITHUB_RUN_NUMBER'],
                            os.environ['GITHUB_EVENT_NAME'], os.environ['GITHUB_REF'])
    info = capture_build_info(ROOT / 'source/dxf2gcode')
    if info.revision != revision or info.dirty is not False:
        raise ValueError('Cannot capture clean source provenance')
    stage = output / 'source'
    def ignore_outputs(directory, names):
        ignored = shutil.ignore_patterns('__pycache__', '*.egg-info')(directory, names)
        if Path(directory) == ROOT / 'source':
            ignored.update({'build', 'dist'} & set(names))
        return ignored
    shutil.copytree(ROOT / 'source', stage,
                    ignore=ignore_outputs)
    (stage / 'dxf2gcode/_version.py').write_text(
        '__version__ = %r\n' % manifest['version'], encoding='utf-8')
    info = replace(info, version=manifest['version'],
                   build_date=datetime.fromtimestamp(manifest['source_date_epoch'], timezone.utc).isoformat())
    write_build_metadata(stage / 'dxf2gcode/_build_metadata.json', info=info)
    (output / 'release-manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'], 'a', encoding='utf-8') as stream:
            stream.write('source=%s\nversion=%s\nwheel_build=%s\n' %
                         (stage, manifest['version'], manifest['wheel_build']))
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    prepare(parser.parse_args().output)
