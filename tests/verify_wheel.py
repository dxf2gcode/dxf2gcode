"""Check a built wheel and exercise it in an already installed environment.

Usage: python tests/verify_wheel.py source/dist/dxf2gcode-....whl
           --python .venv/bin/python [--qt 5|6]

Install the wheel and its runtime dependencies in that environment first.
This check does not install packages or modify a user's configuration.
"""

import argparse
import configparser
import json
from email.parser import Parser
import os
from pathlib import Path
import subprocess
import tempfile
import zipfile


def check_archive(wheel):
    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
        required = {
            "dxf2gcode/_build_metadata.json",
            "dxf2gcode/__main__.py",
            "dxf2gcode/domain/toolpath/planner.py",
            "dxf2gcode/presentation/qt/generated/dxf2gcode_ui5.py",
            "dxf2gcode/presentation/qt/generated/dxf2gcode_ui6.py",
            "dxf2gcode/presentation/qt/generated/dxf2gcode_images5_rc.py",
            "dxf2gcode/presentation/qt/generated/dxf2gcode_images6_rc.py",
        }
        required.update(
            "dxf2gcode/presentation/qt/resources/i18n/dxf2gcode_%s.qm" % language
            for language in ("de", "fr", "ru"))
        assert required <= names, required - names
        assert not any(".egg" in name for name in names)
        assert "dxf2gcode/presentation/qt/resources/dxf2gcode_images_rc.py" not in names
        for package in ("core", "gui", "postpro", "globals", "dxfimport", "Qt"):
            assert not any(name.startswith("dxf2gcode/" + package + "/")
                           for name in names), package
        metadata_path = next(name for name in names if name.endswith(".dist-info/METADATA"))
        metadata = Parser().parsestr(archive.read(metadata_path).decode("utf-8"))
        assert metadata["Name"] == "dxf2gcode"
        provenance = json.loads(archive.read("dxf2gcode/_build_metadata.json"))
        assert provenance["schema"] == 1
        assert provenance["version"] == metadata["Version"]
        assert provenance["build_date"]
        assert provenance["origin"] == "build"
        assert not any("cx-freeze" in item.lower()
                       for item in metadata.get_all("Requires-Dist", []))
        entries_path = next(name for name in names
                            if name.endswith(".dist-info/entry_points.txt"))
        entries = configparser.ConfigParser()
        entries.read_string(archive.read(entries_path).decode("utf-8"))
        assert entries["console_scripts"]["dxf2gcode"] == "dxf2gcode.bootstrap.launcher:main"
        for suffix in ("/share/applications/dxf2gcode.desktop",
                       "/share/metainfo/dxf2gcode.appdata.xml",
                       "/share/icons/hicolor/scalable/apps/dxf2gcode.svg"):
            assert any(name.endswith(suffix) for name in names), suffix
    return metadata["Version"]


def check_installed(python, version, qt):
    repo = Path(__file__).resolve().parent.parent
    with tempfile.TemporaryDirectory(prefix="d2g_wheel_") as directory:
        folder = Path(directory)
        environment = os.environ.copy()
        environment.pop("PYTHONPATH", None)
        environment.update(
            HOME=directory, USERPROFILE=directory,
            APPDATA=directory, LOCALAPPDATA=directory,
            QT_QPA_PLATFORM="offscreen", DXF2GCODE_QT=qt)
        (folder / ".config" / "dxf2gcode.wheel_test").mkdir(parents=True)

        def run(command):
            result = subprocess.run(
                command, cwd=directory, env=environment,
                capture_output=True, text=True, timeout=120)
            assert result.returncode == 0, result.stdout + result.stderr
            return result.stdout

        script = """
import importlib.metadata as metadata
from pathlib import Path
import sys
import dxf2gcode
distribution = metadata.distribution('dxf2gcode')
assert distribution.version == sys.argv[1]
from dxf2gcode.bootstrap.version_metadata import get_version_info
provenance = get_version_info()
assert provenance.version == distribution.version
assert provenance.origin == 'build'
assert Path(dxf2gcode.__file__).resolve() == Path(
    distribution.locate_file('dxf2gcode/__init__.py')).resolve()
assert Path(sys.prefix) in Path(dxf2gcode.__file__).resolve().parents
from dxf2gcode.presentation.qt.qt_compat import PYQT_VERSION, QtCore, QtWidgets
assert str(PYQT_VERSION) == sys.argv[2]
from dxf2gcode.presentation.qt.translations import translation_search_paths
app = QtWidgets.QApplication([])
import dxf2gcode.bootstrap.runtime_state as g
from dxf2gcode.adapters.config.runtime_config import MyConfig
g.folder = str(Path.cwd() / 'config')
Path(g.folder).mkdir()
g.config = MyConfig()
g.config.mode3d = False
for language in ('de', 'fr', 'ru'):
    translator = QtCore.QTranslator()
    assert any(translator.load('dxf2gcode_' + language, folder)
               for folder in translation_search_paths()), language
    assert translator.translate('TreeHandler', 'Different tools'), language
if PYQT_VERSION == 5:
    from dxf2gcode.presentation.qt.generated.dxf2gcode_ui5 import Ui_MainWindow
else:
    from dxf2gcode.presentation.qt.generated.dxf2gcode_ui6 import Ui_MainWindow
window = QtWidgets.QMainWindow()
ui = Ui_MainWindow()
ui.setupUi(window)
assert hasattr(ui, 'toolDiameterComboBox')
assert not window.windowIcon().isNull()
prefix = Path(sys.prefix) / 'share'
assert (prefix / 'applications/dxf2gcode.desktop').is_file()
assert (prefix / 'metainfo/dxf2gcode.appdata.xml').is_file()
assert (prefix / 'icons/hicolor/scalable/apps/dxf2gcode.svg').is_file()
print('Installed package, Qt resources, desktop files and translations verified')
"""
        print(run([str(python), "-c", script, version, qt]).strip())
        help_text = run([str(python), "-m", "dxf2gcode", "--help"])
        assert "export" in help_text.lower()
        launcher = python.parent / ("dxf2gcode.exe" if os.name == "nt" else "dxf2gcode")
        assert launcher.is_file(), launcher
        assert "export" in run([str(launcher), "--help"]).lower()
        output = folder / "wheel-export"
        run([str(python), "-m", "dxf2gcode", "--quiet", "--cfg", "wheel_test",
             "--export", str(output), str(repo / "dxf" / "test.dxf")])
        gcode = output.with_suffix(".ngc").read_text(encoding="utf-8")
        assert "G1 X" in gcode and "M2" in gcode
        print("Module/console launch and headless DXF export verified")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wheel", type=Path)
    parser.add_argument("--python", required=True, type=Path)
    parser.add_argument("--qt", choices=("5", "6"), default="5")
    args = parser.parse_args()
    version = check_archive(args.wheel.resolve())
    check_installed(args.python.absolute(), version, args.qt)
    print("Wheel acceptance check passed for Qt " + args.qt)


if __name__ == "__main__":
    main()
