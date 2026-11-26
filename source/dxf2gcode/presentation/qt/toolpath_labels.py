"""Qt presentation of toolkit-independent toolpath source messages."""

from dxf2gcode.presentation.qt.qt_compat import QtCore
from dxf2gcode.domain.toolpath import leadmove


def translate_message(message):
    if not getattr(message, "context", ""):
        return str(message)
    text = QtCore.QCoreApplication.translate(message.context, message.source)
    args = tuple(translate_message(a) if hasattr(a, "context") else a
                 for a in message.args)
    return text % args if args else text


def translate_diagnostic(diagnostic):
    if not diagnostic.source_message:
        return translate_message(diagnostic.message)
    source = QtCore.QCoreApplication.translate('Shape', diagnostic.source_message)
    args = tuple(translate_message(arg) if hasattr(arg, 'context') else arg
                 for arg in diagnostic.message_args)
    return source % args if args else source


def lead_mode_labels():
    return {leadmove.LEAD_OFF: QtCore.QCoreApplication.translate("LeadMove", "None"),
            leadmove.LEAD_STRAIGHT: QtCore.QCoreApplication.translate("LeadMove", "Straight"),
            leadmove.LEAD_RADIUS: QtCore.QCoreApplication.translate("LeadMove", "Circle"),
            leadmove.LEAD_STARTMOVE: QtCore.QCoreApplication.translate("LeadMove", "Straight with circle")}


def validate_lead_move(*args, **kwargs):
    ok, errors, warnings = leadmove.validate_lead_move(*args, **kwargs)
    return (ok, [(field, translate_message(text)) for field, text in errors],
            [(field, translate_message(text)) for field, text in warnings])
