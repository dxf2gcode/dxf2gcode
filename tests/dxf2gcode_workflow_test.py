# -*- coding: utf-8 -*-
"""Exercise the interactive contour workflow across its real components."""
from __future__ import absolute_import

import os
import sys
import tempfile
import unittest
from copy import copy

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_DIR = os.path.dirname(_TEST_DIR)
sys.path[:0] = [_TEST_DIR, os.path.join(_REPO_DIR, "source")]

import dxf2gcode.bootstrap.runtime_state as g  # noqa: E402
from dxf2gcode.domain.project.entitycontent import EntityContent  # noqa: E402
from dxf2gcode.domain.project.layercontent import LayerContent, Layers  # noqa: E402
from dxf2gcode.domain.geometry.point import Point  # noqa: E402
from dxf2gcode.domain.project.shape import Shape  # noqa: E402
from dxf2gcode.domain.toolpath.shapeoffset import offShapeClass  # noqa: E402
from dxf2gcode.adapters.toolpath.preparation import prepare_shape  # noqa: E402
from dxf2gcode.adapters.dxf.parser import ReadDXF  # noqa: E402
from dxf2gcode.adapters.postprocessor.postprocessor import MyPostProcessor  # noqa: E402
from dxf2gcode.presentation.qt.qt_compat.QtWidgets import QApplication  # noqa: E402

import dxf2gcode_import_contract_test as import_contract  # noqa: E402
import dxf2gcode_parameter_state_test as parameter_state  # noqa: E402

_APP = None


def _first_imported_shape(dxf):
    """Build one production Shape from the first imported DXF contour."""
    entities = dxf.entities
    contour = next(contour for contour in entities.cont
                   if contour.order and entities.geo[contour.order[0][0]].Typ
                   != "Insert")
    root = EntityContent(nr=0, name="Entities", parent=None, p0=Point(),
                         pb=Point(), sca=[1.0, 1.0, 1.0], rot=0.0)
    shape = Shape(0, contour.closed, root)
    for geo_nr, reverse in contour.order:
        entity = entities.geo[geo_nr]
        geos = entity.geo
        if reverse:
            for geo in reversed(geos):
                item = copy(geo)
                item.reverse()
                shape.append(item)
        else:
            for geo in geos:
                shape.append(copy(geo))
    shape.AnalyseAndOptimize()
    root.append(shape)

    layer_nr = entities.geo[contour.order[0][0]].Layer_Nr
    layer = LayerContent(layer_nr, dxf.layers[layer_nr].name, [shape])
    shape.parentLayer = layer
    shape.milling_offset = layer.milling_offset
    return shape, layer


class TestInteractiveWorkflow(unittest.TestCase):
    """DXF import, Qt selection/edit, offset preview geometry, and G-code."""

    def setUp(self):
        global _APP
        _APP = QApplication.instance() or QApplication([])
        self.old_quiet = g.quiet
        g.quiet = True
        self.temp_dir = tempfile.TemporaryDirectory(prefix="d2g_workflow_")

    def tearDown(self):
        g.quiet = self.old_quiet
        self.temp_dir.cleanup()

    def test_load_select_edit_preview_and_export(self):
        fixture = os.path.join(_REPO_DIR, "dxf", "test.dxf")
        dxf = import_contract.read_dxf("test.dxf")
        self.assertTrue(dxf.entities.cont)
        shape, layer = _first_imported_shape(dxf)
        self.assertGreater(len(shape.geos), 0)

        # Drive actual Qt tree selection and the parameter edit slot.
        harness = parameter_state._Harness([layer])
        class PreviewScene(object):
            def __init__(self):
                self.repainted = []

            def repaint_shape(self, item):
                self.repainted.append(item)

            def update(self):
                pass

        g.window.canvas_scene = PreviewScene()
        harness.select([shape])
        edited_offset = 0.25
        harness.line_edits["millingOffsetLineEdit"].setText(str(edited_offset))
        harness.th.toolParameterMillingOffsetUpdate()
        self.assertAlmostEqual(shape.milling_offset, edited_offset)
        self.assertIn(shape, g.window.canvas_scene.repainted)

        # The same production offset class used by the canvas creates preview
        # geometry from the edited shape parameters.
        preview = offShapeClass(parent=shape,
                                offset=layer.getToolRadius() + edited_offset)
        self.assertEqual(preview.offset_status, "ok")
        self.assertGreater(len(preview.geos), 0)

        # Export the selected shape through the production postprocessor.
        shape.stmove = prepare_shape(shape)
        layer.exp_order = [shape.nr]
        layer.exp_order_complete = [0]
        layers = Layers([layer])
        processor = MyPostProcessor()
        processor.getPostProVars(0)
        output = os.path.join(self.temp_dir.name, "workflow.ngc")
        processor.exportShapes(fixture, output, layers)
        self.assertTrue(os.path.isfile(output))
        with open(output, "r", encoding="utf-8", errors="replace") as stream:
            gcode = stream.read()
        self.assertIn("G21", gcode)
        self.assertIn("G1 X", gcode)
        self.assertIn("M2", gcode)


if __name__ == "__main__":
    unittest.main()
