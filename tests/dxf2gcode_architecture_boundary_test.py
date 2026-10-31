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
