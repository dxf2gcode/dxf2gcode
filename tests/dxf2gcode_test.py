#!/usr/bin/env python3
# -*- coding: utf-8 -*-

############################################################################
#
#   Copyright (C) 2018
#    Damian Wrobel <dwrobel@ertelnet.rybnik.pl>
#
#   This file is part of DXF2GCODE.
#
#   DXF2GCODE is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   DXF2GCODE is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with DXF2GCODE.  If not, see <http://www.gnu.org/licenses/>.
#
############################################################################

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from pathlib import PurePath

import sys
_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [_TEST_DIR, os.path.join(os.path.dirname(_TEST_DIR), "source")]


class TestDXF2Gcode(unittest.TestCase):
    """Test the DXF2GCODE command-line workflow."""

    def test_dxf_fixture_files_are_nonempty(self):
        """Verify every bundled DXF fixture exists and is not empty."""
        input_directory = Path(__file__).resolve().parent.parent / 'dxf'
        self.assertTrue(input_directory.is_dir(), 'DXF input directory not found')
        dxf_files = sorted(
            path for path in input_directory.iterdir()
            if path.is_file() and path.suffix.lower() == '.dxf'
        )

        self.assertTrue(dxf_files, 'No DXF input files found')

        for dxf_file in dxf_files:
            with self.subTest(dxf_file=dxf_file.name):
                with dxf_file.open('rb') as file_:
                    self.assertTrue(file_.read(1), 'DXF file is empty')

    def test_quiet_cli_exports_real_dxf_without_gui_shutdown_errors(self):
        repo_dir = Path(__file__).resolve().parent.parent
        with tempfile.TemporaryDirectory(prefix='d2g_cli_export_') as temp_dir:
            profile_dir = Path(temp_dir) / '.config' / 'dxf2gcode.codex_test'
            profile_dir.mkdir(parents=True)
            output_base = Path(temp_dir) / 'converted'
            environment = os.environ.copy()
            environment['HOME'] = temp_dir
            environment['USERPROFILE'] = temp_dir
            environment['QT_QPA_PLATFORM'] = 'offscreen'
            command = [
                sys.executable,
                str(repo_dir / 'source' / 'dxf2gcode.py'),
                '--cfg', 'codex_test',
                '--quiet',
                '--optimize',
                '--export', str(output_base),
                str(repo_dir / 'dxf' / 'test.dxf'),
            ]

            result = subprocess.run(
                command, cwd=temp_dir, env=environment,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                timeout=120)

            output_file = Path(str(output_base) + '.ngc')
            self.assertEqual(
                result.returncode, 0,
                result.stdout.decode('utf-8', errors='replace') +
                result.stderr.decode('utf-8', errors='replace'))
            self.assertTrue(output_file.is_file())
            gcode = output_file.read_text(encoding='utf-8', errors='replace')
            self.assertIn('G21', gcode)
            self.assertIn('G0 X', gcode)
            self.assertIn('G1 X', gcode)
            self.assertIn('M2', gcode)
            self.assertNotIn(b'Exception ignored in atexit callback',
                             result.stderr)

    def test_quiet_cli_exports_d2g_project_without_mainwindow(self):
        repo_dir = Path(__file__).resolve().parent.parent
        with tempfile.TemporaryDirectory(prefix='d2g_cli_project_') as temp_dir:
            profile_dir = Path(temp_dir) / '.config' / 'dxf2gcode.codex_test'
            profile_dir.mkdir(parents=True)
            project_path = Path(temp_dir) / 'test.d2g'
            source_dxf = (repo_dir / 'dxf' / 'test.dxf').as_posix()
            project_path.write_text(
                '# +~+~+~ DXF2GCODE project file V1.3 ~+~+~+\n'
                'd2g.file = {!r}\n'
                'd2g.point_tol = 0.001\n'
                'd2g.fitting_tol = 0.001\n'
                'd2g.scale = 1.0\n'
                'd2g.rot = 0.0\n'
                'd2g.wpzero_x = 0.0\n'
                'd2g.wpzero_y = 0.0\n'
                'd2g.mirrorx = False\n'
                'd2g.mirrory = False\n'
                'd2g.split_lines = False\n'
                'd2g.aut_cut_com = False\n'
                'd2g.machine_type = "milling"\n'
                'd2g.layers = []\n'.format(source_dxf),
                encoding='utf-8')
            output_base = Path(temp_dir) / 'project-export'
            environment = os.environ.copy()
            environment['HOME'] = temp_dir
            environment['USERPROFILE'] = temp_dir
            environment['QT_QPA_PLATFORM'] = 'offscreen'
            command = [
                sys.executable,
                str(repo_dir / 'source' / 'dxf2gcode.py'),
                '--cfg', 'codex_test', '--quiet',
                '--export', str(output_base), str(project_path),
            ]
            result = subprocess.run(
                command, cwd=temp_dir, env=environment,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                timeout=120)

            output_file = Path(str(output_base) + '.ngc')
            self.assertEqual(
                result.returncode, 0,
                result.stdout.decode('utf-8', errors='replace') +
                result.stderr.decode('utf-8', errors='replace'))
            self.assertTrue(output_file.is_file())
            gcode = output_file.read_text(encoding='utf-8', errors='replace')
            self.assertIn('G1 X', gcode)
            self.assertIn('M2', gcode)


def make_test_function(description, dxf2gcode, in_file, out_file):
    """Create a test that converts one DXF file and checks its output."""
    def test(self):
        """Convert a DXF file and verify the generated G-code file."""
        command = [
            sys.executable,
            dxf2gcode,
            '--quiet',
            '-e',
            out_file,
            in_file,
        ]
        print("\n\nExecuting {0}".format(command))
        return_code = subprocess.call(command)
        self.assertEqual(return_code, 0, description)

        output_file = Path(out_file + '.ngc')
        self.assertTrue(output_file.is_file(), description)
        self.assertGreater(output_file.stat().st_size, 0, description)
        output_file.unlink()

    return test


def run_tests():
    """Register a conversion test for every bundled DXF file and run it."""
    _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dxf2gcode = os.path.join(_root, 'source', 'dxf2gcode.py')
    in_dir_name = os.path.join(_root, 'dxf')
    out_dir_name = '.'
    files = os.listdir(in_dir_name)

    for name in files:
        in_file = PurePath(name)

        if not (in_file.match('*.dxf') or in_file.match('*.DXF')):
            continue

        test_name = in_file.name
        test_func = make_test_function(test_name,
                                       dxf2gcode,
                                       os.path.join(in_dir_name, name),
                                       os.path.join(out_dir_name, name))
        setattr(TestDXF2Gcode, 'test_{0}'.format(test_name), test_func)
    unittest.main()


if __name__ == '__main__':
    run_tests()
