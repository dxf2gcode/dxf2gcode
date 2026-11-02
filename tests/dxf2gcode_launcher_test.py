"""Windows taskbar identity and platform-independent launcher checks."""

from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, call, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "source"))

from dxf2gcode.bootstrap import launcher


class TestLauncher(unittest.TestCase):
    def test_identity_is_set_before_entering_the_qt_application(self):
        events = Mock()
        with patch.object(launcher, "_set_windows_app_id") as identity, \
                patch.object(launcher.runpy, "run_module") as run_module:
            events.attach_mock(identity, "identity")
            events.attach_mock(run_module, "run_module")
            self.assertEqual(launcher.main(), 0)
        self.assertEqual(events.mock_calls, [
            call.identity(),
            call.run_module("dxf2gcode.presentation.qt.application",
                            run_name="__main__"),
        ])

    def test_other_platforms_do_not_load_the_windows_shell(self):
        with patch.object(launcher.sys, "platform", "linux"), \
                patch("ctypes.WinDLL", create=True) as load_library:
            launcher._set_windows_app_id()
        load_library.assert_not_called()

    def test_windows_uses_a_stable_identity_across_python_environments(self):
        with patch.object(launcher.sys, "platform", "win32"), \
                patch("ctypes.WinDLL", create=True) as load_library:
            set_id = load_library.return_value.SetCurrentProcessExplicitAppUserModelID
            set_id.return_value = 0
            launcher._set_windows_app_id()
        set_id.assert_called_once_with("org.dxf2gcode.DXF2GCODE")

    def test_shell_failure_is_reported_without_blocking_startup(self):
        with patch.object(launcher.sys, "platform", "win32"), \
                patch("ctypes.WinDLL", create=True) as load_library:
            for failure in (OSError("shell unavailable"), -2147467259):
                with self.subTest(failure=failure):
                    load_library.side_effect = failure if isinstance(failure, OSError) else None
                    load_library.return_value.SetCurrentProcessExplicitAppUserModelID.return_value = failure
                    with self.assertLogs(launcher.__name__, level="WARNING"):
                        launcher._set_windows_app_id()


if __name__ == "__main__":
    unittest.main()
