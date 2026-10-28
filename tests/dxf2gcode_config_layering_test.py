"""Architecture checks for configuration/presentation import direction."""
from __future__ import absolute_import

import os
import subprocess
import sys
import unittest

_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
_SOURCE_DIR = os.path.join(os.path.dirname(_TEST_DIR), "source")


class TestConfigurationImportBoundary(unittest.TestCase):
    def test_loading_configuration_models_does_not_load_qt_widget_factory(self):
        script = (
            "import sys; "
            "sys.path.insert(0, {!r}); "
            "import dxf2gcode.adapters.config.runtime_config; "
            "import dxf2gcode.adapters.postprocessor.postprocessorconfig; "
            "assert 'dxf2gcode.presentation.qt.configwindow' not in sys.modules"
        ).format(_SOURCE_DIR)

        subprocess.check_call([sys.executable, "-c", script], cwd=_SOURCE_DIR)


if __name__ == "__main__":
    unittest.main(verbosity=2)
