"""Runtime metadata at the Qt application boundary."""

import platform
from dxf2gcode.presentation.qt.qt_compat import QtCore

RUNTIME_VERSION = "Py%s PyQt%s" % (platform.python_version(), QtCore.PYQT_VERSION_STR)
