"""Name and ZIP the already-built Windows outputs using the CI manifest."""

import argparse
import json
from pathlib import Path
import shutil


def package(source, manifest_path, output):
    manifest = json.loads(Path(manifest_path).read_text(encoding='utf-8'))
    source, output = Path(source), Path(output)
    output.mkdir(parents=True, exist_ok=True)
    builds = [path for path in (source / 'build').glob('exe.*') if (path / 'dxf2gcode.exe').is_file()]
    installers = list((source / 'dist').glob('*.msi'))
    if len(builds) != 1 or len(installers) != 1:
        raise ValueError('Expected exactly one frozen application and one MSI')
    stem = manifest['artifact_stem']+'-windows-x64'
    shutil.make_archive(str(output / stem), 'zip', builds[0])
    shutil.copy2(installers[0], output / (stem+'.msi'))
    print('Packaged:', stem)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    package(args.source, args.manifest, args.output)
