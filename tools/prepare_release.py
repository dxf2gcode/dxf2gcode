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
from release_policy import develop_build_number, publication_channel


def manifest_for(base, revision, epoch, run_id, run_number, event, ref, build_number=None):
    base = release_base(base)
    if not re.fullmatch(r'[0-9a-f]{40}', revision) or not str(run_id).isdigit() or int(run_number) < 1:
        raise ValueError('Invalid CI run or revision')
    kind = publication_channel(event, ref) or 'test'
    stable = kind == 'stable'
    if stable and ref != 'refs/tags/v'+base:
        raise ValueError('Stable tag must match the declared target version')
    build_number = int(run_number) if build_number is None else int(build_number)
    if build_number < 1:
        raise ValueError('Invalid build number')
    version = base if stable else base+'.dev'+str(build_number)
    date = datetime.fromtimestamp(int(epoch), timezone.utc).strftime('%Y%m%d')
    return dict(schema=1, revision=revision, source_date_epoch=int(epoch), date=date,
                run_id=str(run_id), run_number=int(run_number), build_number=build_number,
                kind=kind, version=version,
                msi_version=msi_version(version), windows_signing='unsigned',
                tag='v'+base if stable else 'develop-ci-'+str(run_id),
                wheel_build=date+'g'+revision[:7],
                artifact_stem='dxf2gcode-%s-%s-g%s' % (version, date, revision[:7]))


def read_releases(repository):
    pages = json.loads(subprocess.check_output(
        ['gh', 'api', '--paginate', '--slurp', 'repos/%s/releases?per_page=100' % repository], text=True))
    return [release for page in pages for release in page]


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
    build_number = None
    if publication_channel(os.environ['GITHUB_EVENT_NAME'], os.environ['GITHUB_REF']) == 'develop':
        build_number = develop_build_number(read_releases(os.environ['GITHUB_REPOSITORY']),
                                           os.environ['GITHUB_RUN_ID'])
    manifest = manifest_for(__version__, revision, git('show', '-s', '--format=%ct', 'HEAD'),
                            os.environ['GITHUB_RUN_ID'], os.environ['GITHUB_RUN_NUMBER'],
                            os.environ['GITHUB_EVENT_NAME'], os.environ['GITHUB_REF'], build_number)
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
