# -*- coding: utf-8 -*-
"""Exercise 3D canvas transforms and OpenGL command generation headlessly."""
from __future__ import absolute_import

import os
import sys
import tempfile
import unittest
from unittest import mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_DIR = os.path.dirname(_TEST_DIR)
sys.path.insert(0, os.path.join(_REPO_DIR, "source"))

import dxf2gcode.bootstrap.runtime_state as g  # noqa: E402

if g.config is None:
    from dxf2gcode.adapters.config.runtime_config import MyConfig  # noqa: E402
    g.folder = tempfile.mkdtemp(prefix="d2g_canvas3d_test_")
    g.config = MyConfig()

from dxf2gcode.domain.geometry.boundingbox import BoundingBox  # noqa: E402
from dxf2gcode.domain.project.layercontent import Shapes  # noqa: E402
from dxf2gcode.domain.geometry.point import Point  # noqa: E402
from dxf2gcode.domain.geometry.point3d import Point3D  # noqa: E402
from dxf2gcode.presentation.qt import canvas3d  # noqa: E402
from dxf2gcode.presentation.qt.canvas3d import GLWidget  # noqa: E402
from dxf2gcode.presentation.qt.qt_compat.QtCore import QSize  # noqa: E402


class _FakeGL(object):
    """Record fixed-function calls without requiring an OpenGL context."""

    def __init__(self):
        self.calls = []
        self.next_list = 1

    def __getattr__(self, name):
        if name.startswith("GL_"):
            return name

        def record(*args):
            self.calls.append((name, args))
            if name == "glGenLists":
                result = self.next_list
                self.next_list += args[0]
                return result
            if name == "glGetString":
                return b"test OpenGL"
        return record


class _Canvas(object):
    def __init__(self):
        self.rotX = 13.0
        self.rotY = -27.0
        self.rotZ = 41.0
        self.posX = 0.0
        self.posY = 0.0
        self.posZ = 0.0
        self.scale = 1.0
        self.scaleCorr = 1.0
        self.update_count = 0
        self.BB = BoundingBox(Point(0, 0), Point(2, 1))

    def update(self):
        self.update_count += 1

    def frameSize(self):
        return QSize(800, 400)

    def normalizeAngle(self, angle):
        return GLWidget.normalizeAngle(self, angle)

    def getRotationVectors(self, start, end):
        return GLWidget.getRotationVectors(self, start, end)


class _Shape(object):
    def __init__(self, selected=False, disabled=False, cut_cor=40):
        self.selected = selected
        self.disabled = disabled
        self.cut_cor = cut_cor
        self.drawObject = 10
        self.drawStMove = 11
        self.drawArrowsDirection = (12, 13)
        self.axis3_start_mill_depth = 0.0
        self.axis3_mill_depth = -2.0

    def get_start_end_points_physical(self, *args):
        return Point(0, 0), Point(1, 0)


class _Layer(object):
    def isBreakLayer(self):
        return False


class TestGLWidgetGeometry(unittest.TestCase):

    def setUp(self):
        self.canvas = _Canvas()
        self.gl = _FakeGL()
        self.old_start_coordinates = (
            g.config.vars.Plane_Coordinates["axis1_start_end"],
            g.config.vars.Plane_Coordinates["axis2_start_end"])
        self.patch_gl = mock.patch.object(canvas3d, "GL", self.gl)
        self.patch_gl.start()
        self.addCleanup(self.patch_gl.stop)
        self.addCleanup(self._restore_start_coordinates)

    def _restore_start_coordinates(self):
        (g.config.vars.Plane_Coordinates["axis1_start_end"],
         g.config.vars.Plane_Coordinates["axis2_start_end"]) = \
            self.old_start_coordinates

    def test_rotate_and_derotate_are_inverse_transforms(self):
        point = (0.25, -0.5, 1.2)
        rotated = GLWidget.rotate(self.canvas, *point)
        restored = GLWidget.deRotate(self.canvas, *rotated)

        for actual, expected in zip(restored, point):
            self.assertAlmostEqual(actual, expected)

    def test_rotation_vectors_are_identity_for_equal_directions(self):
        axes = GLWidget.getRotationVectors(
            self.canvas, Point3D(0, 0, 1), Point3D(0, 0, 1))

        self.assertEqual(axes, (Point3D(1, 0, 0), Point3D(0, 1, 0),
                                Point3D(0, 0, 1)))

    def test_rotation_angles_normalize_and_view_actions_reset_orientation(self):
        GLWidget.setXRotation(self.canvas, 540)
        self.assertEqual(self.canvas.rotX, 180)
        GLWidget.setYRotation(self.canvas, -181)
        self.assertEqual(self.canvas.rotY, 179)
        GLWidget.isometricView(self.canvas)
        self.assertEqual((self.canvas.rotX, self.canvas.rotY, self.canvas.rotZ),
                         (-22, -22, 0))
        GLWidget.topView(self.canvas)
        self.assertEqual((self.canvas.rotX, self.canvas.rotY, self.canvas.rotZ),
                         (0, 0, 0))
        GLWidget.setShowPathDirections(self.canvas, True)
        GLWidget.setShowDisabledPaths(self.canvas, True)
        self.assertTrue(self.canvas.showPathDirections)
        self.assertTrue(self.canvas.showDisabledPaths)

    def test_autoscale_fits_the_current_bounding_box(self):
        GLWidget.autoscale(self.canvas)

        self.assertAlmostEqual(self.canvas.scale, 0.95)
        self.assertAlmostEqual(self.canvas.posX, -0.95)
        self.assertAlmostEqual(self.canvas.posY, 0.475)
        self.assertEqual(self.canvas.posZ, 0)
        self.assertEqual(self.canvas.update_count, 1)

    def test_resize_gl_uses_viewport_aspect_ratio(self):
        GLWidget.resizeGL(self.canvas, 800, 400)
        calls = dict((name, args) for name, args in self.gl.calls)

        self.assertIn(("glViewport", (0, 0, 800, 400)), self.gl.calls)
        self.assertEqual(calls["glOrtho"], (-1.0, 1.0, 0.5, -0.5,
                                            -14.0, 14.0))
        self.assertEqual(self.canvas.scaleCorr, 1.0)

    def test_depth_lines_emit_top_and_final_mill_coordinates(self):
        shape = _Shape()
        start, end = Point(2, 3), Point(5, 7)
        GLWidget.drawHorLine(self.canvas, shape, start, end)
        GLWidget.drawVerLine(self.canvas, shape, start)
        vertices = [args for name, args in self.gl.calls if name == "glVertex3f"]

        self.assertEqual(vertices, [
            (2, -3, 0.0), (5, -7, 0.0),
            (2, -3, -2.0), (5, -7, -2.0),
            (2, -3, 0.0), (2, -3, -2.0)])

    def test_plan_shape_display_list_contains_each_cutting_depth(self):
        from dxf2gcode.domain.toolpath.plan import (
            ToolpathMove, ToolpathPass, ToolpathPlan)

        shape = _Shape()
        shape.BB = BoundingBox(Point(0, 0), Point(10, 1))
        move = ToolpathMove("linear_xy", (0, 0), (10, 0))
        plan = ToolpathPlan(
            shape_number=1, approach_xy=(0, 0),
            passes=(ToolpathPass(1, -1, (move,)),
                    ToolpathPass(2, -2, (move,))),
            workpiece_top=0, safe_margin=0, retract_depth=5,
            feed_depth=100, feed_xy=500)

        GLWidget.makeShape(self.canvas, shape, plan)
        vertices = [args for name, args in self.gl.calls
                    if name == "glVertex3f"]

        self.assertEqual(vertices, [
            (0, 0, 0), (10, 0, 0),
            (0, 0, -1), (10, 0, -1),
            (0, 0, -2), (10, 0, -2)])

    def test_solid_circle_cone_and_cylinder_emit_expected_vertices(self):
        GLWidget.drawSolidCircle(self.canvas, Point(1, 2), 1, 0.5, 4)
        circle_vertices = [args for name, args in self.gl.calls
                           if name == "glVertex3f"]
        self.assertEqual(len(circle_vertices), 6)
        self.assertEqual(circle_vertices[0], (1, -2, 0.5))

        self.gl.calls = []
        GLWidget.drawCone(self.canvas, Point(), 1, 2, -1, 4)
        cone_vertices = [args for name, args in self.gl.calls
                         if name == "glVertex3f"]
        self.assertEqual(len(cone_vertices), 6)
        self.assertEqual(cone_vertices[0], (0, 0, 2))

        self.gl.calls = []
        GLWidget.drawCylinder(self.canvas, Point(), 1, 2, -1, 4)
        cylinder_vertices = [args for name, args in self.gl.calls
                             if name == "glVertex3f"]
        self.assertEqual(len(cylinder_vertices), 10)
        self.assertEqual(cylinder_vertices[0], (1.0, 0.0, 2))
        self.assertEqual(cylinder_vertices[1], (1.0, 0.0, -1))

    def test_sphere_emits_two_vertices_per_longitude_for_each_strip(self):
        GLWidget.drawSphere(self.canvas, 1, 4, 2, 4, 2)
        vertices = [name for name, _args in self.gl.calls
                    if name == "glVertex3f"]
        normals = [name for name, _args in self.gl.calls
                   if name == "glNormal3f"]

        self.assertEqual(len(vertices), 12)
        self.assertEqual(len(normals), 12)

    def test_route_arrow_defaults_to_up_when_start_equals_end(self):
        self.canvas.drawn_arrow = None
        self.canvas.drawArrowHead = lambda origin, rx, ry, rz, offset: \
            setattr(self.canvas, "drawn_arrow", (rx, ry, rz, offset))

        arrow_id = GLWidget.makeRouteArrowHead(
            self.canvas, Point3D(1, 2, 3), Point3D(1, 2, 3))

        self.assertEqual(arrow_id, 1)
        self.assertEqual(self.canvas.drawn_arrow[:3],
                         (Point3D(1, 0, 0), Point3D(0, 1, 0),
                          Point3D(0, 0, 1)))
        self.assertEqual(self.canvas.drawn_arrow[3], 0)

    def test_export_route_transforms_each_contour_endpoint_to_depth(self):
        class RouteShape(object):
            axis3_start_mill_depth = 0.0
            axis3_mill_depth = -2.0

            def get_start_end_points_physical(self):
                return Point(1, 2), Point(3, 4)

        class RouteCanvas(_Canvas):
            shapes = [RouteShape()]
            routearrows = []

        route_canvas = RouteCanvas()
        g.config.vars.Plane_Coordinates["axis1_start_end"] = 10.0
        g.config.vars.Plane_Coordinates["axis2_start_end"] = 20.0
        GLWidget.addexproutest(route_canvas)
        GLWidget.addexproute(route_canvas, [0], 0)

        route = route_canvas.routearrows[0]
        self.assertEqual(route[0], Point3D(10, 20, 0))
        self.assertEqual(route[1], Point3D(1, 2, 0))
        self.assertEqual(route_canvas.expprv, Point3D(3, 4, -2))


if __name__ == "__main__":
    unittest.main()
