"""CI acceptance of the unpacked ZIP and an actual per-user MSI installation.

Run only in a disposable Windows runner. No local build or installation is
started by the unit tests; CI invokes this check on the tested commit's files.
"""

import argparse
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
import zipfile


def check_executable(executable, manifest, fixture, directory):
    root = executable.parent
    provenance = json.loads((root / 'lib/dxf2gcode/_build_metadata.json').read_text(encoding='utf-8'))
    for key in ('version', 'revision'):
        assert provenance[key] == manifest[key], (key, provenance, manifest)
    assert provenance['dirty'] is False
    for language in ('de', 'fr', 'ru'):
        assert (root / 'i18n' / ('dxf2gcode_'+language+'.qm')).is_file()
    assert list(root.rglob('qwindows.dll')), 'Qt Windows platform plugin missing'
    environment = os.environ.copy()
    environment.pop('PYTHONPATH', None)
    environment.update(HOME=str(directory), USERPROFILE=str(directory), APPDATA=str(directory),
                       LOCALAPPDATA=str(directory), DXF2GCODE_QT='5')
    environment.pop('QT_QPA_PLATFORM', None)
    output = directory / 'export.ngc'
    subprocess.run([str(executable), '--quiet', '--cfg', 'package_test', '--export', str(output),
                    str(fixture)], cwd=directory, env=environment, check=True, timeout=90)
    text = output.read_text(encoding='utf-8')
    assert 'G1 X' in text and 'M2' in text
    assert manifest['version'] in text and manifest['revision'][:7] in text
    # Test the normal GUI entry point as well, without introducing a product
    # test flag. Only inspect and close the child process started here.
    process = subprocess.Popen([str(executable), '--cfg', 'package_test'], cwd=directory, env=environment)
    user32 = ctypes.windll.user32
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    user32.EnumWindows.argtypes = [callback_type, wintypes.LPARAM]
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user32.IsWindowVisible.argtypes = [wintypes.HWND]
    user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    found = []
    def inspect_window(handle, _unused):
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(handle, ctypes.byref(pid))
        if pid.value == process.pid and user32.IsWindowVisible(handle):
            title = ctypes.create_unicode_buffer(1024)
            user32.GetWindowTextW(handle, title, len(title))
            if 'dxf2gcode' in title.value.lower():
                found.append(handle)
        return True
    callback = callback_type(inspect_window)
    try:
        deadline = time.monotonic()+45
        while not found and process.poll() is None and time.monotonic() < deadline:
            user32.EnumWindows(callback, 0)
            time.sleep(.2)
        assert found, 'Frozen application did not show its main window'
        user32.PostMessageW(found[0], 0x0010, 0, 0)  # WM_CLOSE
        assert process.wait(timeout=20) == 0
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('packages', type=Path)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--fixture', type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding='utf-8'))
    with tempfile.TemporaryDirectory(prefix='dxf2gcode_acceptance_') as temporary:
        folder = Path(temporary)
        archives = list(args.packages.glob('*.zip'))
        installers = list(args.packages.glob('*.msi'))
        assert len(archives) == len(installers) == 1
        unpacked = folder / 'zip'
        with zipfile.ZipFile(archives[0]) as archive:
            archive.extractall(unpacked)
        zip_profile = folder / 'zip-profile'
        zip_profile.mkdir()
        check_executable(unpacked / 'dxf2gcode.exe', manifest, args.fixture.resolve(), zip_profile)
        installed = folder / 'installed'
        log = folder / 'msi.log'
        result = subprocess.run(['msiexec', '/i', str(installers[0].resolve()), '/qn', '/norestart',
                                 'ALLUSERS=2', 'MSIINSTALLPERUSER=1', 'TARGETDIR='+str(installed),
                                 '/l*v', str(log)], timeout=180)
        assert result.returncode in (0, 3010), log.read_text(encoding='utf-16', errors='replace')
        try:
            candidates = list(installed.rglob('dxf2gcode.exe'))
            assert len(candidates) == 1, 'MSI did not install into the isolated target directory'
            profile = folder / 'msi-profile'
            profile.mkdir()
            check_executable(candidates[0], manifest, args.fixture.resolve(), profile)
        finally:
            removed = subprocess.run(['msiexec', '/x', str(installers[0].resolve()), '/qn', '/norestart'], timeout=180)
            assert removed.returncode in (0, 3010)
    print('Windows ZIP and installed MSI: GUI, DXF export, resources and provenance verified')


if __name__ == '__main__':
    main()
