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
    from types import SimpleNamespace

    sys.path.insert(0, os.path.join(_REPO_DIR, "source"))
    import dxf2gcode.bootstrap.runtime_state as g
    from dxf2gcode.adapters.config.runtime_config import MyConfig

    temp_dir = os.environ["D2G_WORKFLOW_TEMP"]
    g.folder = os.path.join(temp_dir, "config")
    os.makedirs(g.folder, exist_ok=True)
    g.config = MyConfig()
    g.config.mode3d = False
    g.quiet = True

    from dxf2gcode.presentation.qt.qt_compat.QtWidgets import QApplication
    from dxf2gcode.presentation.qt.qt_compat import QtCore
    from dxf2gcode.presentation.qt.qt_compat import PYQT_VERSION
    if PYQT_VERSION == 5:
        from dxf2gcode.presentation.qt.generated.dxf2gcode_ui5 import Ui_MainWindow
    else:
        from dxf2gcode.presentation.qt.generated.dxf2gcode_ui6 import Ui_MainWindow
    from dxf2gcode.presentation.qt.canvas2d import MyGraphicsScene, ShapeGUI

    from dxf2gcode.presentation.qt import application as app_module
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
    assert window.config_window.cfg_window_def["General"][
        "expand_layers_on_load"].getValue() is True
    window.settings = QtCore.QSettings(
        QtCore.QSettings.Format.IniFormat,
        QtCore.QSettings.Scope.UserScope,
        "dxf2gcode-test", "mainwindow-workflow")

    def assert_empty_machining_dropdowns():
        for name in ("toolDiameterComboBox", "leadInComboBox",
                     "leadOutComboBox", "overcutComboBox"):
            combo = getattr(window.ui, name)
            assert combo.count() > 0, name + " has lost its choices"
            assert combo.currentIndex() == -1, name + " has an unexpected selection"
            assert combo.currentText() == "", name + " is not empty"

    assert_empty_machining_dropdowns()
    for name in ("layersCollapsePushButton", "layersExpandPushButton",
                 "blocksCollapsePushButton", "blocksExpandPushButton"):
        assert not getattr(window.ui, name).isEnabled(), name
    window.TreeHandler.updateConfiguration()
    assert_empty_machining_dropdowns()

    from unittest.mock import patch
    from dxf2gcode import __version__
    with patch.object(app_module, "AboutDialog") as dialog:
        window.about()
        message = dialog.call_args.kwargs["message"]
        assert __version__ in message
        assert "Package version:" in message
        assert "Source branch:" in message
        assert "$Date" not in message and "$Revision" not in message

    fixture = os.path.join(_REPO_DIR, "dxf", "test.dxf")
    window.filename = fixture
    assert window.load() is True
    assert len(window.shapes) > 0
    assert window.canvas.scene() is window.canvas_scene
    assert len(window.canvas_scene.items()) > len(window.shapes)
    assert_empty_machining_dropdowns()

    # Both actual toolbars follow their own tree, including the Entities root.
    for view, collapse, expand in (
            (window.ui.layersShapesTreeView, window.ui.layersCollapsePushButton,
             window.ui.layersExpandPushButton),
            (window.ui.entitiesTreeView, window.ui.blocksCollapsePushButton,
             window.ui.blocksExpandPushButton)):
        view.expandAll()
        assert collapse.isEnabled() and not expand.isEnabled()
        collapse.click()
        assert not collapse.isEnabled() and expand.isEnabled()
        assert not view.isExpanded(view.model().index(0, 0))
        expand.click()
        assert collapse.isEnabled() and not expand.isEnabled()

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
    for name in ("toolDiameterComboBox", "leadInComboBox",
                 "leadOutComboBox", "overcutComboBox"):
        assert getattr(window.ui, name).currentIndex() >= 0, name

    # Real keyboard actions and checkbox synchronization must work with Qt6's
    # scoped key/check-state enums as well as with Qt5.
    from dxf2gcode.presentation.qt.qt_compat.QtGui import QKeyEvent
    for expected_disabled in (True, False):
        event = QKeyEvent(QtCore.QEvent.Type.KeyPress,
                          QtCore.Qt.Key.Key_Space,
                          QtCore.Qt.KeyboardModifier.NoModifier)
        assert window.TreeHandler.actionOnKeyPress(event)
        assert shape.isDisabled() == expected_disabled
        window.TreeHandler.updateShapeEnabling(shape, not expected_disabled)
    optimize_item = index.model().itemFromIndex(index.sibling(index.row(), 3))
    previous_check = optimize_item.checkState()
    for changed in (True, False):
        event = QKeyEvent(QtCore.QEvent.Type.KeyPress, QtCore.Qt.Key.Key_O,
                          QtCore.Qt.KeyboardModifier.NoModifier)
        assert window.TreeHandler.actionOnKeyPress(event)
        assert (optimize_item.checkState() != previous_check) == changed

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

    machining_values = (shape.lead_in_mode, shape.lead_out_mode,
                        shape.overcut_enabled, shape.tool_override)
    selection.clearSelection()
    window.TreeHandler.updateToolParameters()
    assert_empty_machining_dropdowns()
    assert (shape.lead_in_mode, shape.lead_out_mode,
            shape.overcut_enabled, shape.tool_override) == machining_values

    # The configured load preference applies only to the layer tree and
    # never changes machining values or the layer/shape order.
    entities_view = window.ui.entitiesTreeView
    entities_view.expandAll()
    entities_root = entities_view.model().index(0, 0)
    order = [(layer.nr, [item.nr for item in layer.shapes])
             for layer in window.layerContents]
    layer_view = window.ui.layersShapesTreeView
    for expand_on_load in (False, True):
        g.config.vars.General.expand_layers_on_load = expand_on_load
        window.TreeHandler.buildLayerTree(window.layerContents)
        for row in range(layer_view.model().rowCount()):
            layer_index = layer_view.model().index(row, 0)
            if layer_view.model().hasChildren(layer_index):
                assert layer_view.isExpanded(layer_index) == expand_on_load
        assert window.ui.layersCollapsePushButton.isEnabled() == expand_on_load
        assert window.ui.layersExpandPushButton.isEnabled() != expand_on_load
        assert entities_view.isExpanded(entities_root)
        assert [(layer.nr, [item.nr for item in layer.shapes])
                for layer in window.layerContents] == order
        assert (shape.lead_in_mode, shape.lead_out_mode,
                shape.overcut_enabled, shape.tool_override) == machining_values

    from pathlib import Path
    from dxf2gcode_import_filters_test import write_layer_filter_fixture

    filtered_fixture = write_layer_filter_fixture(Path(temp_dir) / "filter-layers.dxf")
    for ignore, zero, names in (
            (False, False, {"0", "IGNORE:guide", "Cut"}),
            (True, False, {"0", "Cut"}),
            (False, True, {"IGNORE:guide", "Cut"}),
            (True, True, {"Cut"})):
        g.config.vars.Import_Parameters.exclude_ignore_layers = ignore
        g.config.vars.Import_Parameters.exclude_layer_zero = zero
        window.filename = filtered_fixture.as_posix()
        assert window.load() is True
        assert {layer.name for layer in window.layerContents} == names
        assert len(window.shapes) == len(names)
        assert len(window.canvas_scene.shapes) == len(names)
        assert window.ui.layersShapesTreeView.model().rowCount() == len(names)
        assert [item.nr for item in window.shapes] == list(range(len(names)))

    filtered_fixture.write_text(
        filtered_fixture.read_text().replace("Cut", "IGNORE:cut"), encoding="ascii")
    assert window.load() is True
    assert not window.shapes and not window.layerContents
    for name in ("layersCollapsePushButton", "layersExpandPushButton",
                 "blocksCollapsePushButton", "blocksExpandPushButton"):
        assert not getattr(window.ui, name).isEnabled(), name

    window.close()
    app.processEvents()


if __name__ == "__main__" and "--worker" in sys.argv:
    _run_mainwindow_workflow()
elif __name__ == "__main__":
    unittest.main()
