#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import subprocess
import sys

PYTHONPATH = os.path.split(sys.executable)[0]
pyinpfad = os.path.join(PYTHONPATH, "Scripts\\pyinstaller.exe")

pyt = os.path.join(PYTHONPATH, "python.exe")
filepfad = os.path.realpath(os.path.dirname(sys.argv[0]))
entry_point = os.path.join(filepfad, "dxf2gcode.py")
icon = os.path.join(
    filepfad, "dxf2gcode", "presentation", "qt", "resources", "images",
    "DXF2GCODE-001.ico")
translations = os.path.join(filepfad, "i18n")

cmd = [
    pyinpfad,
    "--noconsole",
    "--icon=%s" % icon,
    "--add-data=%s;i18n" % translations,
    entry_point,
]
print(" ".join(cmd))
subprocess.check_call(cmd)

print("\n!!!!!!!Do not forget the language folder!!!!!!")
print("\nREADY")
