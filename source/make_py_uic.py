#!/usr/bin/env python3

"""
Generates the python file based on the defined uifile
"""

import os
import subprocess
import sys
import tempfile
from dxf2gcode.Qt import PYQT_VERSION

import dxf2gcode.globals.constants as c


def which(program):
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None


if "linux" in sys.platform.lower() or "unix" in sys.platform.lower() or "darwin" in sys.platform.lower():
    # On Linux and macOS executables are normally on the PATH (on Linux please install packages like lib64-qt5-devel and python-qt5-devel)
    names = [f"pyuic{PYQT_VERSION}"]
    UICPATH = None

    for name in names:
        if which(name):
            UICPATH = name
            break

    if not UICPATH:
        print("ERROR: Cannot find the pyuic tool.")
        sys.exit(1)

    if PYQT_VERSION == 5:
        names = ["pyrcc5"]
    else:
        names = ["rcc", "/usr/lib64/qt6/libexec/rcc"]
    RCCPATH = None

    for name in names:
        if which(name):
            RCCPATH = name
            break

    if not RCCPATH:
        print("ERROR: Cannot find the pyrcc tool.")
        sys.exit(1)

    print(f"Using platform tools '{UICPATH}' and '{RCCPATH}'\n")
else:
    PYTHONPATH = os.path.split(sys.executable)[0]
    UICPATH = os.path.join(PYTHONPATH, f"Scripts\\pyuic{PYQT_VERSION}.exe")
    if PYQT_VERSION == 5:
        RCCPATH = os.path.join(PYTHONPATH, "Scripts\\pyrcc5.exe")
    else:
        RCCPATH = 'rcc'
    print(f"Using Windows platform tools '{UICPATH}' and '{RCCPATH}'\n")

FILEPATH = os.path.realpath(os.path.dirname(sys.argv[0]))

UIFILE = "dxf2gcode.ui"
PYFILEver = f"dxf2gcode_ui{PYQT_VERSION}.py"

RCFILE = "dxf2gcode_images.qrc"
RCFILEver = f"dxf2gcode_images{PYQT_VERSION}.qrc"

RCPYFILEver = f"dxf2gcode_images{PYQT_VERSION}_rc.py"

ui_data = ""
with open(os.path.join(FILEPATH,UIFILE), "r", encoding="utf-8") as myfile:
    ui_data = myfile.read().replace(RCFILE, RCFILEver)

fd, tmp_ui_filename = tempfile.mkstemp()
try:
    os.write(fd, bytes(ui_data, 'UTF-8'))
    os.close(fd)

    OPTIONS = ("-o", )

    cmd1 = [UICPATH, tmp_ui_filename, *OPTIONS, os.path.join(FILEPATH,PYFILEver)]

    if PYQT_VERSION == 6:
        OPTIONS = ('-g', 'python', '-o')
    cmd2 = [RCCPATH, *OPTIONS, os.path.join(FILEPATH,RCPYFILEver),os.path.join(FILEPATH,RCFILE)]

    print(" ".join(cmd1))
    subprocess.check_call(cmd1)

    print(" ".join(cmd2))
    subprocess.check_call(cmd2)

    if PYQT_VERSION == 6:
        with open(os.path.join(FILEPATH,PYFILEver), "a", encoding="utf-8") as myfile:
            myfile.write('import dxf2gcode_images6_rc\n')

        with open(os.path.join(FILEPATH, RCPYFILEver), "r", encoding="utf-8") as myfile:
            data = myfile.read().replace("from PySide6 import QtCore","from PyQt6 import QtCore")

        with open(os.path.join(FILEPATH, RCPYFILEver), "w", encoding="utf-8") as f:
            f.write(data)

finally:
    os.remove(tmp_ui_filename)

print("Please do not commit any auto-generated files.")
print("\nREADY")