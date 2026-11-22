"""Optional Windows title bar with room for the machining history actions."""

from dxf2gcode.presentation.qt.qt_compat import QtCore
from dxf2gcode.presentation.qt.qt_compat.QtGui import QPainter
from dxf2gcode.presentation.qt.qt_compat.QtWidgets import QApplication, QHBoxLayout, QLabel, QSizePolicy, QWidget

Qt = QtCore.Qt


def install_title_bar(window):
    """Use expanded client space only when the Qt Windows backend provides it."""
    expanded = getattr(Qt.WindowType, 'ExpandedClientAreaHint', None)
    if QApplication.platformName() != 'windows' or expanded is None:
        return None

    original_flags = window.windowFlags()
    flags = (original_flags | expanded | Qt.WindowType.NoTitleBarBackgroundHint
             | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowSystemMenuHint
             | Qt.WindowType.WindowMinMaxButtonsHint | Qt.WindowType.WindowCloseButtonHint)
    window.setWindowFlags(flags)
    window.winId()
    handle = window.windowHandle()
    if handle.safeAreaMargins().top() <= 0:
        window.setWindowFlags(original_flags)
        return None

    # QWidget restores WindowTitleHint when caption buttons are requested.
    # Apply the change on the native QWindow so it draws only the system buttons.
    handle.setFlag(Qt.WindowType.WindowTitleHint, False)
    window.overrideWindowFlags(handle.flags())
    window.setAttribute(Qt.WidgetAttribute.WA_ContentsMarginsRespectsSafeArea, False)
    title_bar = TitleBar(window)
    window.setMenuWidget(title_bar)
    return title_bar


class TitleText(QLabel):
    def paintEvent(self, event):
        text = self.fontMetrics().elidedText(self.text(), Qt.TextElideMode.ElideMiddle, self.width())
        with QPainter(self) as painter:
            painter.setPen(self.palette().color(self.foregroundRole()))
            painter.drawText(self.rect(), int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft), text)


class TitleBar(QWidget):
    def __init__(self, window):
        super().__init__(window)
        self.setObjectName('historyTitleBar')
        self.row = QHBoxLayout(self)
        self.row.setSpacing(4)
        self.icon = QLabel(self)
        self.row.addWidget(self.icon)
        self.text = TitleText(window.windowTitle(), self)
        self.text.setTextFormat(Qt.TextFormat.PlainText)
        self.text.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.row.addWidget(self.text, 1)
        window.windowTitleChanged.connect(self.text.setText)
        window.windowIconChanged.connect(self.update_icon)
        handle = window.windowHandle()
        handle.safeAreaMarginsChanged.connect(self.update_margins)
        handle.screenChanged.connect(lambda screen: self.update_icon(window.windowIcon()))
        self.update_icon(window.windowIcon())
        self.update_margins(handle.safeAreaMargins())

    def add_history_buttons(self, undo, redo):
        for index, button in enumerate((undo, redo), start=1):
            button.setIconSize(QtCore.QSize(16, 16))
            self.row.insertWidget(index, button, alignment=Qt.AlignmentFlag.AlignVCenter)

    def update_icon(self, icon):
        self.icon.setPixmap(icon.pixmap(QtCore.QSize(16, 16), self.devicePixelRatioF()))

    def update_margins(self, safe_area):
        height = safe_area.top()
        # Qt's Windows backend reserves three caption controls, each 1.5 times
        # the title height. Keep another half-height clear before the buttons.
        self.row.setContentsMargins(max(12, safe_area.left()), 3, max(5 * height, safe_area.right()), 0)
        self.setFixedHeight(height)
