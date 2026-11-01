"""Compact, localized version summary for the About dialog."""

from html import escape

from dxf2gcode.bootstrap.version_metadata import get_version_info
from dxf2gcode.domain.constants import RUNTIME_VERSION
from dxf2gcode.presentation.qt.qt_compat import QtCore


def version_details_html(info=None):
    info = get_version_info() if info is None else info
    unavailable = QtCore.QCoreApplication.translate("VersionInfo", "Not available")
    detached = QtCore.QCoreApplication.translate("VersionInfo", "No active branch")
    parts = [info.version]
    if info.revision:
        parts.extend((info.revision[:7], info.branch or detached))
    else:
        parts.append(unavailable)
        if info.branch:
            parts.append(info.branch)
    if info.dirty is True:
        parts.append(QtCore.QCoreApplication.translate("VersionInfo", "Local changes"))
    rows = (
        (QtCore.QCoreApplication.translate("VersionInfo", "Version:"), " · ".join(parts)),
        (QtCore.QCoreApplication.translate("VersionInfo", "Runtime:"), RUNTIME_VERSION),
    )
    return "<br>".join("<b>%s</b> %s" % (escape(str(label)), escape(str(value)))
                       for label, value in rows) + "<br>"
