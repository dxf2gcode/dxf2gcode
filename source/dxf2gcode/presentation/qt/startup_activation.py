"""One Windows foreground handoff after the main window has been shown."""

import logging
import sys

logger = logging.getLogger(__name__)


class WindowsStartupActivation:
    def __init__(self):
        from ctypes import WinDLL, wintypes

        user32 = WinDLL('user32')
        self.foreground = user32.GetForegroundWindow
        self.foreground.argtypes = ()
        self.foreground.restype = wintypes.HWND
        self.launch_window = self.foreground()
        self.set_foreground = user32.SetForegroundWindow
        self.set_foreground.argtypes = (wintypes.HWND,)
        self.set_foreground.restype = wintypes.BOOL
        self.window_thread = user32.GetWindowThreadProcessId
        self.window_thread.argtypes = (wintypes.HWND, wintypes.LPDWORD)
        self.window_thread.restype = wintypes.DWORD
        self.current_thread = WinDLL('kernel32').GetCurrentThreadId
        self.current_thread.argtypes = ()
        self.current_thread.restype = wintypes.DWORD
        self.attach_input = user32.AttachThreadInput
        self.attach_input.argtypes = (wintypes.DWORD, wintypes.DWORD, wintypes.BOOL)
        self.attach_input.restype = wintypes.BOOL
        self.bring_to_top = user32.BringWindowToTop
        self.bring_to_top.argtypes = (wintypes.HWND,)
        self.bring_to_top.restype = wintypes.BOOL
        self.set_active = user32.SetActiveWindow
        self.set_active.argtypes = (wintypes.HWND,)
        self.set_active.restype = wintypes.HWND
        self.is_hung = user32.IsHungAppWindow
        self.is_hung.argtypes = (wintypes.HWND,)
        self.is_hung.restype = wintypes.BOOL

    def activate(self, window):
        current = self.foreground()
        if not current or current == window or current != self.launch_window:
            return
        if self.set_foreground(window):
            return
        foreground_thread = self.window_thread(current, None)
        thread = self.current_thread()
        if not foreground_thread or foreground_thread == thread or self.is_hung(current):
            return
        if self.foreground() != current or not self.attach_input(thread, foreground_thread, True):
            return
        try:
            # As in Qt's Windows activation path, share input only for the
            # handoff from the window that was in front at launch.
            if self.foreground() == current:
                self.bring_to_top(window)
                self.set_active(window)
                logger.debug('Windows startup window in foreground: %s', self.foreground() == window)
        finally:
            self.attach_input(thread, foreground_thread, False)


def capture_startup_activation():
    if sys.platform == 'win32':
        try:
            return WindowsStartupActivation()
        except (OSError, AttributeError) as error:
            logger.debug('Windows startup foreground handoff unavailable: %s', error)
    return None
