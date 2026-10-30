"""Resource location checks for source, wheel and virtualenv launches."""

from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parent.parent / "source"
sys.path.insert(0, str(SOURCE))

from dxf2gcode.presentation.qt import translations


class TestTranslationSearchPaths(unittest.TestCase):
    def test_installed_package_catalogs_and_environment_prefix_are_searched(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            module = root / "site-packages/dxf2gcode/presentation/qt/translations.py"
            with patch.object(translations, "__file__", str(module)), patch.object(
                    sys, "prefix", str(root / "venv")):
                paths = translations.translation_search_paths()
            self.assertIn(str(module.parent / "resources/i18n"), paths)
            self.assertIn(str(root / "venv/share/dxf2gcode/i18n"), paths)

    def test_source_catalog_path_is_independent_of_working_directory(self):
        with tempfile.TemporaryDirectory() as temporary, patch.object(
                Path, "cwd", return_value=Path(temporary)):
            paths = translations.translation_search_paths()
        self.assertIn(str(SOURCE / "i18n"), paths)


if __name__ == "__main__":
    unittest.main()
