"""Tests for the first inward-facing domain and application boundaries."""
from __future__ import absolute_import

import os
from pathlib import Path
import subprocess
import sys
import unittest

_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
_SOURCE_DIR = os.path.join(os.path.dirname(_TEST_DIR), "source")


class TestDomainImportBoundary(unittest.TestCase):
    def test_all_domain_and_application_modules_are_inward_facing(self):
        script = '''
import importlib, pkgutil, sys
import dxf2gcode.domain as domain
import dxf2gcode.application as application
for package in (domain, application):
    for module in pkgutil.walk_packages(package.__path__, package.__name__ + '.'):
        importlib.import_module(module.name)
assert not any(name.startswith(('PyQt', 'dxf2gcode.presentation',
    'dxf2gcode.adapters', 'dxf2gcode.bootstrap.runtime_state')) for name in sys.modules)
from types import SimpleNamespace
from dxf2gcode.domain.project.shape import Shape
from dxf2gcode.domain.project.layercontent import LayerContent, Layers
from dxf2gcode.domain.project.project import Project
from dxf2gcode.domain.project.document import LegacyProjectDocument
class Values(dict):
    __getattr__ = dict.__getitem__
tool = dict(diameter=2, speed=1000, start_radius=1, lead_radius=2,
            lead_length=1, overcut_length=0, milling_offset=0)
values = Values(Route_Optimisation={'default_TSP': True},
    Depth_Coordinates=dict(axis3_start_mill_depth=0, axis3_slice_depth=-1,
        axis3_mill_depth=-2, axis3_retract=5, axis3_safe_margin=1),
    Feed_Rates=dict(f_g1_plane=200, f_g1_depth=50),
    Drag_Knife_Options=Values(drag_angle=20, swivel_depth=-.1),
    Tool_Parameters={'1': tool}, Layer_Options={'id_float_separator': ':'},
    Lead_In_Out=dict(lead_in_mode='off', lead_out_mode='off', overcut_enabled=False),
    General=dict(split_line_segments=False, automatic_cutter_compensation=False))
config = SimpleNamespace(vars=values, var_dict=values, point_tolerance=.001,
                         fitting_tolerance=.001, machine_type='milling', tool_units='mm')
shape = Shape(nr=1, config=config)
layer = LayerContent(1, 'plain', [shape], config=config)
shape.parentLayer = layer
layer.overrideDefaults()
assert shape.axis3_mill_depth == -2 and layer.tool_diameter == 2
values.Drag_Knife_Options['swivel_depth'] = -.2
assert shape.drag_swivel_depth == -.2
state = SimpleNamespace(layerContents=Layers([layer]))
project = Project(state, config)
project.load(LegacyProjectDocument(1.5, {'layers': []}), compleet=False)
assert state.layerContents[0].shapes[0] is shape
assert not any(name.startswith(('PyQt', 'dxf2gcode.presentation',
    'dxf2gcode.adapters', 'dxf2gcode.bootstrap.runtime_state')) for name in sys.modules)
'''
        environment = os.environ.copy()
        environment['PYTHONPATH'] = _SOURCE_DIR
        subprocess.check_call([sys.executable, '-c', script], env=environment)

    def test_legacy_package_namespaces_are_removed(self):
        package = Path(_SOURCE_DIR) / "dxf2gcode"
        for old_name in ("core", "dxfimport", "globals", "gui", "postpro",
                         "Qt"):
            with self.subTest(package=old_name):
                self.assertFalse((package / old_name).exists())

        old_imports = (
            "dxf2gcode.core.", "dxf2gcode.dxfimport.",
            "dxf2gcode.globals.", "dxf2gcode.gui.",
            "dxf2gcode.postpro.", "dxf2gcode.Qt.",
        )
        for source_file in package.rglob("*.py"):
            source = source_file.read_text(encoding="utf-8")
            for old_import in old_imports:
                with self.subTest(file=source_file, import_path=old_import):
                    self.assertNotIn(old_import, source)

    def test_geometry_primitives_do_not_import_qt_or_runtime_globals(self):
        script = (
            "import sys; "
            "sys.path.insert(0, {!r}); "
            "from dxf2gcode.domain.geometry import Point, Point3D; "
            "from dxf2gcode.domain.toolpath.depths import "
            "calculate_depth_passes; "
            "from dxf2gcode.domain.toolpath.plan import ToolpathPlan; "
            "from dxf2gcode.domain.toolpath.planner import ToolpathPlanner; "
            "from dxf2gcode.domain.toolpath.inputs import ToolpathRequest; "
            "assert 'dxf2gcode.presentation.qt.qt_compat' not in sys.modules; "
            "assert 'dxf2gcode.bootstrap.runtime_state' not in sys.modules"
        ).format(_SOURCE_DIR)

        subprocess.check_call([sys.executable, "-c", script], cwd=_SOURCE_DIR)

    def test_all_geometry_and_toolpath_modules_import_without_qt_or_runtime(self):
        script = (
            "import sys, importlib, pkgutil; "
            "sys.path.insert(0, {!r}); "
            "import dxf2gcode.domain.geometry as geometry; "
            "import dxf2gcode.domain.toolpath as toolpath; "
            "[importlib.import_module(m.name) for package in (geometry, toolpath) "
            "for m in pkgutil.walk_packages(package.__path__, package.__name__ + '.')]; "
            "assert 'dxf2gcode.bootstrap.runtime_state' not in sys.modules; "
            "assert not any(m.startswith(('PyQt', 'dxf2gcode.presentation', "
            "'dxf2gcode.adapters.postprocessor')) for m in sys.modules)"
        ).format(_SOURCE_DIR)
        subprocess.check_call([sys.executable, "-c", script], cwd=_SOURCE_DIR)

    def test_application_use_cases_do_not_import_qt_or_runtime_globals(self):
        script = (
            "import sys; "
            "sys.path.insert(0, {!r}); "
            "import dxf2gcode.application.importing; "
            "import dxf2gcode.application.projects; "
            "assert 'dxf2gcode.presentation.qt.qt_compat' not in sys.modules; "
            "assert 'dxf2gcode.bootstrap.runtime_state' not in sys.modules"
        ).format(_SOURCE_DIR)

        subprocess.check_call([sys.executable, "-c", script], cwd=_SOURCE_DIR)

    def test_profile_dialect_and_serializer_do_not_import_qt_or_runtime_globals(self):
        script = (
            "import sys; "
            "sys.path.insert(0, {!r}); "
            "from dxf2gcode.adapters.postprocessor.dialect import ProfileDialect; "
            "from dxf2gcode.adapters.toolpath.gcode_exporter import ToolpathGCodeExporter; "
            "assert 'dxf2gcode.presentation.qt.qt_compat' not in sys.modules; "
            "assert 'dxf2gcode.bootstrap.runtime_state' not in sys.modules; "
            "assert 'dxf2gcode.domain.toolpath.planner' not in sys.modules"
        ).format(_SOURCE_DIR)
        subprocess.check_call([sys.executable, "-c", script], cwd=_SOURCE_DIR)

    def test_geometry_classes_are_defined_in_the_domain_package(self):
        sys.path.insert(0, _SOURCE_DIR)
        try:
            from dxf2gcode.domain.geometry import Point, Point3D

            self.assertEqual(Point.__module__,
                             "dxf2gcode.domain.geometry.point")
            self.assertEqual(Point3D.__module__,
                             "dxf2gcode.domain.geometry.point3d")
        finally:
            sys.path.remove(_SOURCE_DIR)

    def test_2d_graphics_items_compose_domain_objects(self):
        script = (
            "import os, sys, tempfile; "
            "sys.path.insert(0, {!r}); "
            "import dxf2gcode.bootstrap.runtime_state as g; "
            "from dxf2gcode.adapters.config.runtime_config import MyConfig; "
            "g.folder = tempfile.mkdtemp(prefix='d2g_gui_boundary_'); "
            "g.config = MyConfig(); "
            "from dxf2gcode.domain.project.shape import Shape; "
            "from dxf2gcode.domain.toolpath.stmove import StMove; "
            "from dxf2gcode.presentation.qt.canvas2d import ShapeGUI, StMoveGUI; "
            "assert not issubclass(ShapeGUI, Shape); "
            "assert not issubclass(StMoveGUI, StMove)"
        ).format(_SOURCE_DIR)
        subprocess.check_call([sys.executable, "-c", script],
                              cwd=_SOURCE_DIR)


if __name__ == "__main__":
    unittest.main(verbosity=2)
