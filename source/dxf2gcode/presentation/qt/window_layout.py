"""Keep user-sized side/message panes stable while the canvas grows."""

from dxf2gcode.presentation.qt.qt_compat import QtCore


class WindowLayout(QtCore.QObject):
    def __init__(self, window):
        super().__init__(window)
        self.window = window
        ui = window.ui
        ui.splitter.setStretchFactor(0, 0)
        ui.splitter.setStretchFactor(1, 1)
        ui.messageSplitter.setStretchFactor(0, 1)
        ui.messageSplitter.setStretchFactor(1, 0)
        window.machining_panel.splitter.setStretchFactor(0, 1)
        window.machining_panel.splitter.setStretchFactor(1, 0)
        self.splitters = {'geometry': window.geometry_panel.splitter,
                          'machining': window.machining_panel.splitter}
        ui.splitter.splitterMoved.connect(self.update_minimum)
        ui.messageSplitter.splitterMoved.connect(self.update_minimum)
        self.timer = QtCore.QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.apply_initial)

    def restore(self, settings):
        self.sidebar = settings.value('sidebarWidth', 200, type=int) if settings.contains('sidebarWidth') else None
        self.messages = settings.value('messageHeight', 100, type=int)
        self.saved = {key: settings.value('splitter_'+key) for key in self.splitters}
        self.open_states = {'geometry': settings.value('geometry_open')}
        self.timer.start(0)

    def apply_initial(self):
        window, ui = self.window, self.window.ui
        if self.sidebar is not None:
            ui.splitter.setSizes([max(200, self.sidebar), max(200, ui.splitter.width()-ui.splitter.handleWidth()-self.sidebar)])
        ui.messageSplitter.setSizes([max(200, ui.messageSplitter.height()-ui.messageSplitter.handleWidth()-self.messages), max(48, self.messages)])
        for key, toggles in self.toggles().items():
            state = self.open_states.get(key)
            if isinstance(state, (list, tuple)) and len(state) == len(toggles):
                for toggle, value in zip(toggles, state):
                    toggle.setChecked(str(value).lower() in ('true', '1'))
        for key, splitter in self.splitters.items():
            state = self.saved.get(key)
            if isinstance(state, QtCore.QByteArray):
                splitter.restoreState(state)
        self.update_minimum()

    def toggles(self):
        return {'geometry': [button for button, _ in self.window.geometry_panel.sections]}

    def update_minimum(self, *unused):
        window, ui = self.window, self.window.ui
        sidebar = ui.splitter.sizes()[0]
        messages = ui.messageSplitter.sizes()[1]
        margins = ui.centralwidget.layout().contentsMargins()
        width = sidebar + ui.canvas.minimumWidth() + ui.splitter.handleWidth() + margins.left()+margins.right()
        height = max(240, ui.canvas.minimumHeight()) + messages + ui.messageSplitter.handleWidth()
        height += window.menuBar().height() + margins.top()+margins.bottom()
        window.setMinimumSize(width, height)

    def save(self, settings):
        ui = self.window.ui
        settings.setValue('sidebarWidth', ui.splitter.sizes()[0])
        settings.setValue('messageHeight', ui.messageSplitter.sizes()[1])
        for key, splitter in self.splitters.items():
            settings.setValue('splitter_'+key, splitter.saveState())
        for key, toggles in self.toggles().items():
            settings.setValue(key+'_open', [toggle.isChecked() for toggle in toggles])
