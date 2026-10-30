"""Import filters remove layers from the model, including block contents."""

import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "source"))

import dxf2gcode.bootstrap.runtime_state as g
from dxf2gcode.adapters.config.runtime_config import MyConfig
from dxf2gcode.application.drawings import BuildDrawingModel
from dxf2gcode.domain.geometry.linegeo import LineGeo
from dxf2gcode.domain.geometry.point import Point
from dxf2gcode.domain.project.shape import Shape


def line(layer, x):
    return SimpleNamespace(Typ="Line", Layer_Nr=layer,
                           geo=[LineGeo(Point(x, 0), Point(x + 5, 0))])


def insert(layer, block):
    return SimpleNamespace(Typ="Insert", Layer_Nr=layer, BlockName=block,
                           Point=Point(10, 20), Scale=[1, 1, 1], rot=0)


def entities(*geometries):
    return SimpleNamespace(geo=list(geometries), basep=Point(), cont=[
        SimpleNamespace(order=[(index, 0)], closed=False)
        for index in range(len(geometries))])


def drawing(names, geometry, blocks=None):
    blocks = blocks or {}
    return SimpleNamespace(
        layers=[SimpleNamespace(name=name) for name in names],
        entities=geometry,
        blocks=SimpleNamespace(Entities=list(blocks.values())),
        Get_Block_Nr=lambda name: list(blocks).index(name))


def write_layer_filter_fixture(path):
    """Small real DXF with distinguishable paths on all three layer types."""
    pairs = [(0, "SECTION"), (2, "HEADER"), (9, "$INSUNITS"), (70, 4),
             (0, "ENDSEC"), (0, "SECTION"), (2, "TABLES"),
             (0, "TABLE"), (2, "LAYER"), (70, 3)]
    for name in ("0", "IGNORE:guide", "Cut"):
        pairs.extend([(0, "LAYER"), (2, name), (70, 0), (62, 7), (6, "CONTINUOUS")])
    pairs.extend([(0, "ENDTAB"), (0, "ENDSEC"),
                  (0, "SECTION"), (2, "BLOCKS"), (0, "ENDSEC"),
                  (0, "SECTION"), (2, "ENTITIES")])
    for name, x in (("0", 10), ("IGNORE:guide", 20), ("Cut", 30)):
        pairs.extend([(0, "LINE"), (8, name), (10, x), (20, 0), (30, 0),
                      (11, x + 5), (21, 0), (31, 0)])
    pairs.extend([(0, "ENDSEC"), (0, "EOF")])
    path.write_text("".join("%s\n%s\n" % pair for pair in pairs), encoding="ascii")
    return path


class TestImportLayerFilters(unittest.TestCase):
    def setUp(self):
        self.old_folder, self.old_config = g.folder, g.config
        self.directory = tempfile.TemporaryDirectory(prefix="d2g_filters_")
        g.folder = self.directory.name
        self.config = MyConfig()
        g.config = self.config
        self.created = []
        self.drawing = drawing(
            ["Cut", "0", "IGNORE:guide"],
            entities(line(0, 0), line(1, 10), line(2, 20)))

    def tearDown(self):
        g.folder, g.config = self.old_folder, self.old_config
        self.directory.cleanup()

    def build(self, ignore=False, zero=False, block_layers=False, source=None):
        options = self.config.vars.Import_Parameters
        options.exclude_ignore_layers = ignore
        options.exclude_layer_zero = zero
        options.insert_at_block_layer = block_layers
        return BuildDrawingModel(
            source or self.drawing, self.config, Shape, False,
            shape_created=self.created.append).execute()

    def assert_consistent(self, model):
        self.assertEqual([s.nr for s in model.shapes], list(range(len(model.shapes))))
        layer_shapes = [s for layer in model.layers for s in layer.shapes]
        self.assertCountEqual(layer_shapes, model.shapes)
        self.assertEqual(self.created, list(model.shapes))
        for shape in model.shapes:
            self.assertIsNotNone(shape.BB)
            self.assertIn(shape, shape.parentLayer.shapes)
            self.assertIn(shape, shape.parentEntity.children)

    def test_filters_off_keep_existing_import_and_disabled_ignore_shape(self):
        model = self.build()
        self.assertEqual([l.name for l in model.layers], ["Cut", "0", "IGNORE:guide"])
        self.assertTrue(model.layers[2].shapes[0].isDisabled())
        self.assertEqual(model.excluded_layers, ())
        self.assert_consistent(model)

    def test_ignore_filter_removes_shapes_layers_and_callbacks(self):
        model = self.build(ignore=True)
        self.assertEqual([l.name for l in model.layers], ["Cut", "0"])
        self.assertEqual(model.excluded_layers, ("IGNORE:guide",))
        self.assert_consistent(model)

    def test_zero_filter_uses_name_not_layer_number(self):
        model = self.build(zero=True)
        self.assertEqual([l.name for l in model.layers], ["Cut", "IGNORE:guide"])
        self.assertEqual(model.excluded_layers, ("0",))
        self.assert_consistent(model)

    def test_both_filters_are_independent(self):
        model = self.build(ignore=True, zero=True)
        self.assertEqual([l.name for l in model.layers], ["Cut"])
        self.assertEqual(model.excluded_layers, ("0", "IGNORE:guide"))
        self.assert_consistent(model)

    def test_ignore_matching_keeps_existing_case_and_separator_rules(self):
        self.config.vars.Layer_Options.id_float_separator = "|"
        names = ["IGNORE|guide", "IGNORE:other", "ignore|lower", "IGNORED|other"]
        source = drawing(names, entities(*(line(n, n * 10) for n in range(4))))
        model = self.build(ignore=True, source=source)
        self.assertEqual([l.name for l in model.layers], names[1:])
        self.assert_consistent(model)

    def test_ignored_insert_excludes_entire_block_and_empty_entity_node(self):
        source = drawing(["Cut", "0", "IGNORE:guide"], entities(insert(2, "B")),
                         {"B": entities(line(0, 0), line(1, 10))})
        model = self.build(ignore=True, source=source)
        self.assertEqual(list(model.layers), [])
        self.assertEqual(list(model.shapes), [])
        self.assertEqual(model.entity_root.children, [])
        self.assertEqual(model.excluded_layers, ("IGNORE:guide",))
        self.assert_consistent(model)

    def test_block_zero_is_not_filtered_when_assigned_to_insert_layer(self):
        source = drawing(["Cut", "0"], entities(insert(0, "B")),
                         {"B": entities(line(1, 0))})
        model = self.build(zero=True, block_layers=True, source=source)
        self.assertEqual([l.name for l in model.layers], ["Cut"])
        self.assertEqual(model.excluded_layers, ())
        self.assert_consistent(model)

    def test_nested_zero_insert_inherits_outer_block_layer(self):
        source = drawing(["Cut", "0"], entities(insert(0, "Outer")), {
            "Outer": entities(insert(1, "Inner")), "Inner": entities(line(1, 0))})
        model = self.build(zero=True, block_layers=True, source=source)
        self.assertEqual([l.name for l in model.layers], ["Cut"])
        self.assertEqual(len(model.shapes), 1)
        self.assert_consistent(model)

    def test_original_block_layer_option_is_respected(self):
        source = drawing(["Cut", "0"], entities(insert(0, "B")),
                         {"B": entities(line(1, 0))})
        model = self.build(zero=True, block_layers=False, source=source)
        self.assertEqual(list(model.shapes), [])
        self.assertEqual(model.entity_root.children, [])
        self.assert_consistent(model)

    def test_insert_on_excluded_zero_layer_does_not_reintroduce_children(self):
        source = drawing(["Cut", "0"], entities(insert(1, "B")),
                         {"B": entities(line(0, 0))})
        model = self.build(zero=True, source=source)
        self.assertEqual(list(model.shapes), [])
        self.assertEqual(model.entity_root.children, [])
        self.assertEqual(model.excluded_layers, ("0",))
        self.assert_consistent(model)

    def test_real_dxf_headless_export_omits_filtered_movements(self):
        from dxf2gcode.application.cli_export import ExportDrawing
        from dxf2gcode.application.importing import ImportDrawing
        from dxf2gcode.adapters.dxf.reader import DxfReaderAdapter
        from dxf2gcode.adapters.postprocessor.postprocessor import MyPostProcessor

        source = write_layer_filter_fixture(Path(self.directory.name) / "layers.dxf")
        output = Path(self.directory.name) / "layers.ngc"
        self.config.vars.Import_Parameters.exclude_ignore_layers = True
        self.config.vars.Import_Parameters.exclude_layer_zero = True
        postprocessor = MyPostProcessor(create_config_window=False)
        model, diagnostics = ExportDrawing(
            ImportDrawing(DxfReaderAdapter(self.config)),
            lambda data: BuildDrawingModel(data, self.config, Shape, False).execute(),
            postprocessor, self.config).execute(str(source), str(output))
        self.assertEqual([l.name for l in model.layers], ["Cut"])
        self.assertEqual(len(model.shapes), 1)
        code = output.read_text()
        self.assertRegex(code, r"\bX\s*35\.0+\b")
        self.assertNotRegex(code, r"\bX\s*15\.0+\b")
        self.assertNotRegex(code, r"\bX\s*25\.0+\b")
        self.assertFalse(any(d.severity == "error" for d in diagnostics))

    def test_old_projects_restore_remaining_values_after_filtering_and_renumbering(self):
        from dxf2gcode.application.cli_export import _HeadlessProjectSession
        from dxf2gcode.domain.project.project import Project

        path = write_layer_filter_fixture(Path(self.directory.name) / "layers.dxf")
        source = _HeadlessProjectSession(self.config, str(path.with_suffix(".d2g")))
        source.filename = path.as_posix()
        self.assertTrue(source.load())
        cut = next(l for l in source.layerContents if l.name == "Cut")
        cut.shapes[0].f_g1_plane = 321.25
        self.assertNotEqual(cut.shapes[0].nr, 0)
        source.TreeHandler = SimpleNamespace(updateExportOrder=lambda *args: None)
        action = SimpleNamespace(isChecked=lambda: False)
        source.ui = SimpleNamespace(actionSplitLineSegments=action,
                                    actionAutomaticCutterCompensation=action)
        for layer in source.layerContents:
            layer.exp_order_complete = list(range(len(layer.shapes)))
        documents = {}
        for version in (1.1, 1.2, 1.3):
            with patch.object(Project, "version", version):
                documents[version] = Project(source).export()

        self.config.vars.Import_Parameters.exclude_ignore_layers = True
        self.config.vars.Import_Parameters.exclude_layer_zero = True
        for version, content in documents.items():
            with self.subTest(version=version):
                target = _HeadlessProjectSession(self.config, source.project_filename)
                Project(target).load(content)
                self.assertEqual([l.name for l in target.layerContents], ["Cut"])
                self.assertEqual([s.nr for s in target.shapes], [0])
                self.assertEqual(target.shapes[0].f_g1_plane, 321.25)
                self.assertCountEqual(target.excluded_layers, ["0", "IGNORE:guide"])
                target.TreeHandler = source.TreeHandler
                target.ui = source.ui
                target.layerContents[0].exp_order_complete = [0]
                saved = Project(target).export()
                restored = _HeadlessProjectSession(self.config, source.project_filename)
                Project(restored).load(saved)
                self.assertEqual([l.name for l in restored.layerContents], ["Cut"])
                self.assertEqual([s.nr for s in restored.shapes], [0])
                self.assertEqual(restored.shapes[0].f_g1_plane, 321.25)


if __name__ == "__main__":
    unittest.main()
