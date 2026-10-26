# -*- coding: utf-8 -*-
"""Run the real MainWindow workflow in an isolated Qt process."""
from __future__ import absolute_import

import os
import subprocess
import sys
import tempfile
import unittest

_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_DIR = os.path.dirname(_TEST_DIR)


class TestMainWindowWorkflow(unittest.TestCase):
    """Exercise load, canvas plot, tree edit, preview, and export together."""

    def test_mainwindow_load_edit_preview_and_export(self):
        with tempfile.TemporaryDirectory(prefix="d2g_mainwindow_") as temp_dir:
            env = os.environ.copy()
            env["QT_QPA_PLATFORM"] = "offscreen"
            env["D2G_WORKFLOW_TEMP"] = temp_dir
            result = subprocess.run(
                [sys.executable, __file__, "--worker"],
                cwd=temp_dir,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=120)

            self.assertEqual(
                result.returncode, 0,
                result.stdout.decode("utf-8", errors="replace") +
                result.stderr.decode("utf-8", errors="replace"))


def _run_mainwindow_workflow():
    """Worker entry point; run separately so a Qt crash cannot kill unittest."""
    import importlib.util
    from types import SimpleNamespace

    sys.path.insert(0, os.path.join(_REPO_DIR, "source"))
    import dxf2gcode.globals.globals as g
    from dxf2gcode.globals.config import MyConfig

    temp_dir = os.environ["D2G_WORKFLOW_TEMP"]
    g.folder = os.path.join(temp_dir, "config")
    os.makedirs(g.folder, exist_ok=True)
    g.config = MyConfig()
    g.config.mode3d = False
    g.quiet = True

    from dxf2gcode.Qt.QtWidgets import QApplication
    from dxf2gcode.Qt import QtCore
    from dxf2gcode_ui5 import Ui_MainWindow
    from dxf2gcode.gui.canvas2d import MyGraphicsScene, ShapeGUI

    script = os.path.join(_REPO_DIR, "source", "dxf2gcode.py")
    spec = importlib.util.spec_from_file_location("dxf2gcode_app", script)
    app_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app_module)
    g.folder = os.path.join(temp_dir, "config")
    app_module.Ui_MainWindow = Ui_MainWindow
    app_module.MyGraphicsScene = MyGraphicsScene
    app_module.Shape = ShapeGUI

    QtCore.QSettings.setDefaultFormat(QtCore.QSettings.Format.IniFormat)
    QtCore.QSettings.setPath(QtCore.QSettings.Format.IniFormat,
                             QtCore.QSettings.Scope.UserScope, temp_dir)
    app = QApplication([])
    window = app_module.MainWindow(app)
    g.window = window
    window.settings = QtCore.QSettings(
        QtCore.QSettings.Format.IniFormat,
        QtCore.QSettings.Scope.UserScope,
        "dxf2gcode-test", "mainwindow-workflow")

    fixture = os.path.join(_REPO_DIR, "dxf", "test.dxf")
    window.filename = fixture
    assert window.load() is True
    assert len(window.shapes) > 0
    assert window.canvas.scene() is window.canvas_scene
    assert len(window.canvas_scene.items()) > len(window.shapes)

    shape = window.shapes[0]
    assert shape.stmove is not None
    index = window.TreeHandler.findLayerItemIndexFromShape(shape)
    assert index.isValid()
    selection = window.ui.layersShapesTreeView.selectionModel()
    selection.select(
        index,
        QtCore.QItemSelectionModel.SelectionFlag.Select |
        QtCore.QItemSelectionModel.SelectionFlag.Rows)
    assert shape.isSelected()

    previous_preview = shape.stmove
    new_offset = 0.25
    window.ui.millingOffsetLineEdit.setText(str(new_offset))
    window.ui.millingOffsetLineEdit.editingFinished.emit()
    app.processEvents()
    assert abs(shape.milling_offset - new_offset) < 1e-9
    assert shape.stmove is not None
    assert shape.stmove is not previous_preview
    assert window.canvas_scene.shapes[shape.nr] is shape

    output_base = os.path.join(temp_dir, "mainwindow-workflow")
    output_format = "%s (*%s)" % (
        window.MyPostProcessor.output_text[0],
        window.MyPostProcessor.output_format[0])
    app_module.options = SimpleNamespace(post_pro=output_format)
    window.exportShapes(None, output_base)
    output = output_base + window.MyPostProcessor.output_format[0]
    assert os.path.isfile(output), "MainWindow.exportShapes did not create output"
    with open(output, "r", encoding="utf-8", errors="replace") as stream:
        gcode = stream.read()
    assert "G21" in gcode
    assert "G1 X" in gcode
    assert "M2" in gcode

    window.close()
    app.processEvents()


if __name__ == "__main__" and "--worker" in sys.argv:
    _run_mainwindow_workflow()
elif __name__ == "__main__":
    unittest.main()
