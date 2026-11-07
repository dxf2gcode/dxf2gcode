"""Original selection trees in two independently collapsible sections."""

from dxf2gcode.presentation.qt.qt_compat import QtCore
from dxf2gcode.presentation.qt.qt_compat.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QToolButton, QSplitter

Qt = QtCore.Qt


class GeometryPanel(QWidget):
    def __init__(self, window):
        super().__init__(window)
        ui = window.ui
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.splitter = QSplitter(Qt.Orientation.Vertical, self)
        self.splitter.setChildrenCollapsible(False)
        layout.addWidget(self.splitter)
        self.sections = []
        for title, page, collapse, expand in (
                (self.tr('Entities'), ui.tab, ui.blocksCollapsePushButton, ui.blocksExpandPushButton),
                (self.tr('Layers'), ui.tab_2, ui.layersCollapsePushButton, ui.layersExpandPushButton)):
            ui.mytabWidget.removeTab(ui.mytabWidget.indexOf(page))
            section = QWidget(self.splitter)
            section_layout = QVBoxLayout(section)
            section_layout.setContentsMargins(0, 0, 0, 0)
            header = QHBoxLayout()
            toggle = QToolButton(section)
            toggle.setText(title)
            toggle.setCheckable(True)
            toggle.setChecked(True)
            toggle.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
            toggle.setArrowType(Qt.ArrowType.DownArrow)
            header.addWidget(toggle)
            header.addStretch()
            header.addWidget(collapse)
            header.addWidget(expand)
            # Remove the old toolbar, including the obsolete layer-order arrows.
            old = page.layout().takeAt(0).layout()
            while old.count():
                item = old.takeAt(0)
                if item.widget() is not None:
                    item.widget().hide()
            section_layout.addLayout(header)
            section_layout.addWidget(page)
            page.show()
            def toggle_section(checked, page=page, toggle=toggle, section=section):
                page.setVisible(checked)
                toggle.setArrowType(Qt.ArrowType.DownArrow if checked else Qt.ArrowType.RightArrow)
                section.setMaximumHeight(16777215 if checked else toggle.sizeHint().height() + 8)
            toggle.toggled.connect(toggle_section)
            self.sections.append((toggle, page))
        self.splitter.setSizes([250, 250])
        ui.mytabWidget.insertTab(0, self, self.tr('Geometry'))
        ui.mytabWidget.setCurrentWidget(self)
