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
import unittest
from pathlib import Path
from pathlib import PurePath

import sys
_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [_TEST_DIR, os.path.join(os.path.dirname(_TEST_DIR), "source")]


class TestDXF2Gcode(unittest.TestCase):
    """Test the DXF2GCODE command-line workflow."""

    def test_dxf_files_can_be_opened(self):
        """Open every bundled DXF example and verify that it is not empty."""
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
