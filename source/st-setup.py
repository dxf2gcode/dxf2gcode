#!/usr/bin/env python3
############################################################################
#
#   Copyright (C) 2017
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

import glob
import os
import platform
import shutil
from pathlib import Path

from setuptools import find_packages, setup
from setuptools.command.install_scripts import install_scripts as base_install_scripts


PROJECT_DIR = Path(__file__).resolve().parent
os.chdir(PROJECT_DIR)


class install_scripts(base_install_scripts):
    def run(self):
        super().run()
        for script in self.get_outputs():
            if script.endswith(".py"):
                shutil.move(script, script[:-3])


setup_requires = []

if platform.system() == 'Darwin':
    setup_requires.append('py2app')

setup(
    name='dxf2gcode',

    version='20261028',

    description='2D drawings to CNC machine compatible G-Code converter.',

    long_description=(PROJECT_DIR / 'README.txt').read_text(encoding='utf-8'),
    long_description_content_type='text/plain',

    url='https://sourceforge.net/p/dxf2gcode/wiki/Home/',

    author='Christian Kohloeffel',

    author_email='christian.kohloeffel@googlemail.com',

    license='GPLv3',

    packages=find_packages(include=["dxf2gcode", "dxf2gcode.*"]),



    install_requires=[
        'configobj>=5.0.6',
        'PyQt5>=5.9',
        'PyOpenGL>=3.1'
    ],

    extras_require={
        'qt6': ['PyQt6'],
    },

    include_package_data=True,

    data_files=[
        ('share/metainfo', ['dxf2gcode.appdata.xml']),
        ('share/applications', ['dxf2gcode.desktop']),
        ('share/dxf2gcode/i18n', sorted(glob.glob('i18n/*.qm'))),
        ('share/icons/hicolor/scalable/apps/', ['dxf2gcode/presentation/qt/resources/images/dxf2gcode.svg'])
    ],

    cmdclass={"install_scripts": install_scripts},

    scripts=['dxf2gcode.py'],

    # setup for py2app
    app=['dxf2gcode.py'],
    options={
        'py2app': {
            'iconfile': 'dxf2gcode/presentation/qt/resources/images/dxf2gcode.icns',
            'plist': {
                'CFBundleName': "dxf2gcode",
                'CFBundleDisplayName': "dxf2gcode",
                'CFBundleIdentifier': "org.sourceforge.dxf2gcode"
            }
        }
    },
    setup_requires=setup_requires
)
