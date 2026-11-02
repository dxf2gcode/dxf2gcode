"""Start the Qt application entry point."""

import runpy
import sys


def _set_windows_app_id():
    """Keep source launches separate from Python's taskbar group."""
    if sys.platform != "win32":
        return

    import ctypes
    import logging

    try:
        set_app_id = ctypes.WinDLL("shell32").SetCurrentProcessExplicitAppUserModelID
        set_app_id.argtypes = [ctypes.c_wchar_p]
        set_app_id.restype = ctypes.c_long
        result = set_app_id("org.dxf2gcode.DXF2GCODE")
        if result != 0:
            logging.getLogger(__name__).warning(
                "Could not set Windows taskbar application ID (HRESULT %s)", result)
    except OSError as error:
        logging.getLogger(__name__).warning(
            "Could not set Windows taskbar application ID: %s", error)


def main():
    _set_windows_app_id()
    runpy.run_module("dxf2gcode.presentation.qt.application",
                     run_name="__main__")
    return 0
