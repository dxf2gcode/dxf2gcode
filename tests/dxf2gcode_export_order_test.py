"""Visible order survives project roundtrips and real GUI/CLI G-code export."""
import os
import re
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [TEST_DIR, os.path.join(os.path.dirname(TEST_DIR), "source")]

import dxf2gcode_tree_multiselect_test as tree
import dxf2gcode_stmove_gcode_test as machining
from dxf2gcode_leadmove_project_test import _ParentStub
import dxf2gcode.bootstrap.runtime_state as g
from dxf2gcode.application.cli_export import ExportDrawing
from dxf2gcode.application.drawings import DrawingModel
from dxf2gcode.domain.project.layercontent import LayerContent, Layers
from dxf2gcode.domain.project.project import Project
from dxf2gcode.domain.project.tool_settings import ToolSettings
from dxf2gcode.domain.toolpath.customgcode import CustomGCode
from dxf2gcode.presentation.qt.application import MainWindow
from dxf2gcode.presentation.qt.treeview import TreeView


class TestExportOrder(unittest.TestCase):
    def setUp(self):
        self.old_window = g.window
        self.addCleanup(setattr, g, "window", self.old_window)
        self.h = tree.MultiSelectHarness(0)
        self.shapes = [machining.make_shape(machining.square_geos(10 + nr),
                                            nr=nr, cut_cor=40)
                       for nr in range(6)]
        self.layers = Layers([LayerContent(nr, "L%d" % nr,
                                           self.shapes[nr*3:nr*3+3])
                              for nr in range(2)])
        for layer in self.layers:
            layer.lead_in_mode = layer.lead_out_mode = "off"
            for shape in layer.shapes:
                shape.parentLayer = layer
                shape.send_to_TSP = False
        self.shapes[0].tool_override = ToolSettings.from_profile(
            2, g.config.vars.Tool_Parameters["1"])
        self.custom = CustomGCode("marker", 6, "(ORDER MARKER)\n", self.layers[0])
        self.layers[0].shapes.insert(1, self.custom)
        self.h.th.layers_list = self.layers
        self.h.th.buildLayerTree(self.layers)
        self.h.view = TreeView()
        self.h.th.ui.layersShapesTreeView = self.h.view
        self.h.view.setModel(self.h.th.layer_item_model)
        self.h.view.exportOrderUpdateCallback = self.h.th.prepareExportOrderUpdate
        self.h.th.auto_update_export_order = False
        self.h.th.updateExportOrder()
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

    def export(self, cli=False, optimize=False, optimizer_factory=None):
        pp = machining.make_postpro()
        pp.postpro_file_used = "order-test.cfg"
        path = os.path.join(self.temp.name, "order.ngc")
        with patch.dict(g.config.vars.General.__dict__,
                        write_to_stdout=False, automatic_cutter_compensation=False):
            if cli:
                # Profile selection is separate from the real export under test.
                pp.getPostProVars = Mock()
                ExportDrawing(None, None, pp, g.config,
                              optimizer_factory=optimizer_factory).export_model(
                    DrawingModel(None, self.layers, self.shapes),
                    "order.dxf", path, optimize=optimize)
            else:
                for shape in self.shapes:
                    machining.build_stmove(shape)
                pp.exportShapes("order.dxf", path, self.layers)
        with open(path) as stream:
            return stream.read()

    def assert_gcode_order(self, code, expected):
        self.assertEqual([int(nr) for nr in re.findall(r"SHAPE Nr: (\d+)", code)],
                         expected)
        tools = [int(nr) for nr in re.findall(r"T(\d+) M6", code)]
        self.assertEqual(tools, [1, 2, 1])
        self.assertLess(code.index("SHAPE Nr: 0"), code.index("ORDER MARKER"))
        self.assertLess(code.index("ORDER MARKER"), code.index("SHAPE Nr: 1"))

    def test_tree_buttons_roundtrip_and_cli_preserve_gcode_sequence(self):
        # Move a shape and a layer using the actual Up/Down button handlers.
        index = self.h.th.findLayerItemIndexFromShape(self.shapes[2])
        self.h.view.setCurrentIndex(index)
        self.h.view.moveUpCurrentItem()
        self.h.view.moveUpCurrentItem()
        self.h.view.moveUpCurrentItem()
        self.h.view.setCurrentIndex(self.h.th.layer_item_model.index(1, 0))
        self.h.view.moveUpCurrentItem()
        self.assertEqual([layer.nr for layer in self.layers], [1, 0])
        self.assertEqual(self.layers[1].exp_order, [2, 0, 1])
        starts = [shape.get_start_end_points() for shape in self.shapes]
        self.assert_gcode_order(self.export(), [3, 4, 5, 2, 0, 6, 1])

        parent = _ParentStub(self.layers)
        parent.newNumber = len(self.shapes)
        parent.TreeHandler = self.h.th
        project = Project(parent)
        saved = project.export(compleet=False)
        # A project load starts from freshly imported source geometry.
        self.layers[1].shapes.remove(self.custom)
        project.load(saved, compleet=False)
        self.layers = parent.layerContents
        # Rebuild the view as the GUI does after loading a project.
        self.h.th.layers_list = self.layers
        self.h.th.buildLayerTree(self.layers)
        self.h.th.updateExportOrder()
        self.assert_gcode_order(self.export(), [3, 4, 5, 2, 0, 6, 1])
        self.assert_gcode_order(self.export(cli=True), [3, 4, 5, 2, 0, 6, 1])
        self.assertEqual([shape.get_start_end_points() for shape in self.shapes], starts)

    def test_route_display_synchronizes_tree_without_optimizing(self):
        parent = self.h.th.layer_item_model.item(0, 0)
        parent.insertRow(0, parent.takeRow(3))
        scene = Mock(routearrows=[])
        window = SimpleNamespace(TreeHandler=self.h.th, canvas_scene=scene,
                                 layerContents=self.layers)
        starts = [shape.get_start_end_points() for shape in self.shapes]
        MainWindow.updateExportRoute(window)
        self.assertEqual(self.layers[0].exp_order, [2, 0, 1])
        self.assertEqual(scene.addexproute.call_args_list[0].args, ([2, 0, 1], 0))
        self.assertEqual([shape.get_start_end_points() for shape in self.shapes], starts)

    def test_disabled_entries_are_omitted_by_both_export_paths(self):
        from dxf2gcode.application.optimization.tsp import TspOptimization
        self.custom.setDisable(True)
        self.shapes[1].setDisable(True)
        for shape in self.layers[1].shapes:
            shape.setDisable(True)
        self.h.th.updateExportOrder()
        for cli, optimize in ((False, False), (True, False), (True, True)):
            code = self.export(cli=cli, optimize=optimize,
                               optimizer_factory=TspOptimization)
            self.assertEqual(re.findall(r"SHAPE Nr: (\d+)", code), ["0", "2"])
            self.assertNotIn("ORDER MARKER", code)
            self.assertNotIn("LAYER: L1", code)

    def test_cli_exports_enabled_custom_gcode_in_its_visual_slot(self):
        code = self.export(cli=True)
        self.assertEqual(re.findall(r"SHAPE Nr: (\d+)", code),
                         ["0", "6", "1", "2", "3", "4", "5"])
        self.assertLess(code.index("SHAPE Nr: 0"), code.index("ORDER MARKER"))
        self.assertLess(code.index("ORDER MARKER"), code.index("SHAPE Nr: 1"))

    def test_optimize_and_export_forwards_the_requested_output_path(self):
        window = SimpleNamespace(optimizeTSP=Mock(), exportShapes=Mock())
        MainWindow.optimizeAndExportShapes(window, saveas="ordered.ngc")
        window.optimizeTSP.assert_called_once_with()
        window.exportShapes.assert_called_once_with(saveas="ordered.ngc")

    def check_optimized_gui_and_cli_order(self, mode, expected):
        from dxf2gcode.presentation.qt import application

        class Optimizer:
            # Move the released middle shape before the fixed shapes, whose
            # relative order is retained. Both layers use the same test route.
            opt_route = [3, 1, 0, 2]

            def __init__(self, endpoints, fixed, settings):
                self.assertions = (len(endpoints), fixed)
                if self.assertions != (4, [0, 2]):
                    raise AssertionError(self.assertions)

            def calc_next_iteration(self):
                pass

        for shape in self.shapes:
            shape.send_to_TSP = shape.nr in (1, 4)
        fixed_starts = [self.shapes[nr].get_start_end_points()
                        for nr in (0, 2, 3, 5)]
        self.layers.reverse()
        self.h.th.buildLayerTree(self.layers)
        scene = Mock(routearrows=[])
        window = SimpleNamespace(TreeHandler=self.h.th, canvas_scene=scene,
                                 layerContents=self.layers, shapes=self.shapes,
                                 tr=lambda text: text,
                                 app=Mock(), setCursor=Mock(), unsetCursor=Mock())
        window.updateExportRoute = lambda: MainWindow.updateExportRoute(window)
        with patch.dict(g.config.vars.Route_Optimisation.__dict__,
                        TSP_shape_order=mode), patch.object(
                            application, "TspOptimization", Optimizer):
            MainWindow.optimizeTSP(window)
            gui_code = self.export()
            visible = [layer.shapes[index].nr for layer in self.layers
                       for index in layer.exp_order_complete]
            self.assertEqual(visible, expected)
            self.assertEqual([int(nr) for nr in re.findall(
                r"SHAPE Nr: (\d+)", gui_code)], expected)
            # A second normal export and route display keep optimized order.
            window.updateExportRoute()
            self.assertEqual(re.findall(r"SHAPE Nr: (\d+)", self.export()),
                             [str(nr) for nr in expected])
            cli_code = self.export(cli=True, optimize=True,
                                   optimizer_factory=Optimizer)
            self.assertEqual([int(nr) for nr in re.findall(
                r"SHAPE Nr: (\d+)", cli_code)], expected)
            self.assertEqual(re.findall(r"T\d+ M6", cli_code),
                             re.findall(r"T\d+ M6", gui_code))
            self.assertEqual([layer.nr for layer in self.layers], [1, 0])
            self.assertEqual([self.shapes[nr].get_start_end_points()
                              for nr in (0, 2, 3, 5)], fixed_starts)

    def test_order_only_mode_matches_optimized_gui_and_cli_export(self):
        self.check_optimized_gui_and_cli_order(
            "CONSTRAIN_ORDER_ONLY", [4, 3, 5, 6, 1, 0, 2])

    def test_place_after_mode_matches_optimized_gui_and_cli_export(self):
        self.check_optimized_gui_and_cli_order(
            "CONSTRAIN_PLACE_AFTER", [3, 5, 4, 0, 6, 2, 1])

    def test_export_action_has_compiled_translations_in_all_catalogs(self):
        from pathlib import Path
        import xml.etree.ElementTree as ET
        from dxf2gcode.presentation.qt.qt_compat import QtCore
        from dxf2gcode.presentation.qt.qt_compat import PYQT_VERSION
        from importlib import import_module
        from dxf2gcode.presentation.qt.qt_compat.QtWidgets import QMainWindow
        source = "&Export Shapes without Optimization"
        ui_module = import_module(
            "dxf2gcode.presentation.qt.generated.dxf2gcode_ui%d" % PYQT_VERSION)
        root = Path(TEST_DIR).parent / "source" / "i18n"
        for language in ("de", "fr", "ru"):
            catalog = root / ("dxf2gcode_%s.ts" % language)
            messages = ET.parse(catalog).findall("./context[name='MainWindow']/message")
            expected = next(message.findtext("translation") for message in messages
                            if message.findtext("source") == source)
            translator = QtCore.QTranslator()
            self.assertTrue(translator.load(str(catalog.with_suffix(".qm"))))
            self.assertEqual(translator.translate("MainWindow", source), expected)
            app = tree._APP
            app.installTranslator(translator)
            try:
                window = QMainWindow()
                ui = ui_module.Ui_MainWindow()
                ui.setupUi(window)
                self.assertEqual(ui.actionExportShapes.text(), expected)
            finally:
                app.removeTranslator(translator)


if __name__ == "__main__":
    unittest.main()
