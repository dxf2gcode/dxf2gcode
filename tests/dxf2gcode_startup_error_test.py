"""Exercise startup configuration errors with the real Qt message box."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class TestStartupConfigurationError(unittest.TestCase):
    def _run_worker(self, quiet):
        with tempfile.TemporaryDirectory(prefix="d2g_startup_error_") as folder:
            env = os.environ.copy()
            env["QT_QPA_PLATFORM"] = "offscreen"
            command = [sys.executable, str(Path(__file__).resolve()), "--worker"]
            if quiet:
                command.append("--quiet")
            result = subprocess.run(command, cwd=folder, env=env,
                                    capture_output=True, timeout=20)
            self.assertEqual(result.returncode, 0,
                             result.stdout.decode(errors="replace") +
                             result.stderr.decode(errors="replace"))

    def test_gui_displays_critical_configuration_error(self):
        self._run_worker(quiet=False)

    def test_quiet_reports_configuration_error_without_dialog(self):
        self._run_worker(quiet=True)


def _worker():
    import runpy
    from types import SimpleNamespace
    from unittest.mock import patch

    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "source"))
    from dxf2gcode.adapters.config import runtime_config
    from dxf2gcode.bootstrap import logging as bootstrap_logging
    from dxf2gcode.presentation.qt.qt_compat.QtWidgets import QMessageBox

    quiet = "--quiet" in sys.argv
    sys.argv = ["dxf2gcode"] + (["--quiet"] if quiet else [])
    message = "Unsupported test configuration version"
    config = SimpleNamespace(version_mismatch=message)
    displayed = []

    def check_dialog(dialog):
        assert not quiet, "Quiet startup must not display a dialog"
        assert dialog.icon() == QMessageBox.Icon.Critical
        assert dialog.windowTitle() == "Configuration error"
        assert dialog.text() == message
        displayed.append(dialog.text())
        return 0

    with patch.object(runtime_config, "MyConfig", return_value=config), \
            patch.object(runtime_config, "stored_config_profile", return_value=""), \
            patch.object(runtime_config, "config_profile_folder", return_value=os.getcwd()), \
            patch.object(bootstrap_logging, "LoggerClass"), \
            patch.object(QMessageBox, "exec", check_dialog):
        # Supply just the logging setting read before startup checks the version.
        config.vars = SimpleNamespace(Logging={"logfile": ""})
        try:
            runpy.run_module("dxf2gcode.presentation.qt.application", run_name="__main__")
        except SystemExit as error:
            assert error.code == (2 if quiet else 0), error.code
        else:
            raise AssertionError("Startup must stop after a configuration error")
    assert displayed == ([] if quiet else [message]), displayed


if __name__ == "__main__":
    if "--worker" in sys.argv:
        _worker()
    else:
        unittest.main()
