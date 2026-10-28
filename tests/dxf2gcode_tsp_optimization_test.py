# -*- coding: utf-8 -*-
"""Behavioral tests for TSP distance, ordering and population optimization."""
from __future__ import absolute_import

import os
import random
import sys
import tempfile
import unittest

_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_DIR = os.path.dirname(_TEST_DIR)
sys.path[:0] = [_TEST_DIR, os.path.join(_REPO_DIR, "source")]

import dxf2gcode.bootstrap.runtime_state as g  # noqa: E402
from dxf2gcode.domain.geometry.point import Point  # noqa: E402
from dxf2gcode.application.optimization.tsp import (  # noqa: E402
    DistanceMatrixClass, FittnessClass, PopulationClass, TspOptimization)


def _ensure_config():
    if g.config is None:
        from dxf2gcode.adapters.config.runtime_config import MyConfig
        g.folder = tempfile.mkdtemp(prefix="d2g_tsp_test_")
        g.config = MyConfig()


_ensure_config()


def _endpoints(count=4):
    return [(Point(i * 3.0, 0.0), Point(i * 3.0 + 1.0, 0.0))
            for i in range(count)]


class TestTspOptimization(unittest.TestCase):

    def setUp(self):
        self.settings = g.config.vars.Route_Optimisation
        self.old_settings = {
            key: self.settings[key]
            for key in ("begin_art", "mutation_rate", "max_population")
        }
        self.settings["begin_art"] = "ordered"
        self.settings["mutation_rate"] = 0.2
        self.settings["max_population"] = 8
        self.random_state = random.getstate()
        random.seed(4271)

    def tearDown(self):
        random.setstate(self.random_state)
        for key, value in self.old_settings.items():
            self.settings[key] = value

    def test_distance_matrix_measures_end_to_next_start(self):
        matrix = DistanceMatrixClass()
        matrix.generate_matrix(_endpoints(3))

        self.assertEqual(matrix.size, [3, 3])
        self.assertAlmostEqual(matrix.matrix[0][1], 2.0)
        self.assertAlmostEqual(matrix.matrix[1][0], 4.0)
        self.assertEqual(matrix.matrix[1][1], 1.0)

    def test_population_start_and_constraint_order_are_preserved(self):
        matrix = DistanceMatrixClass()
        matrix.generate_matrix(_endpoints())
        population = PopulationClass([4, 8], matrix.matrix, 0.0)
        fitness = FittnessClass(population, [0.0] * 8, [2, 0])

        fitness.set_startpoint()
        self.assertTrue(all(route[0] == 3 for route in population.pop))

        fitness.correct_constrain_order()
        for route in population.pop:
            self.assertEqual(sorted(route), [0, 1, 2, 3])
            self.assertLess(route.index(2), route.index(0))

    def test_genetic_iteration_keeps_routes_as_permutations(self):
        matrix = DistanceMatrixClass()
        matrix.generate_matrix(_endpoints())
        population = PopulationClass([4, 8], matrix.matrix, 0.2)
        fitness = FittnessClass(population, list(range(8)), [])

        population.genetic_algorithm(fitness, 0.2)

        self.assertEqual(len(population.pop), 8)
        for route in population.pop:
            self.assertEqual(sorted(route), [0, 1, 2, 3])

    def test_optimizer_initializes_and_advances_a_valid_route(self):
        optimizer = TspOptimization(_endpoints(), [1, 3])
        self.assertEqual(sorted(optimizer.opt_route), [0, 1, 2, 3])
        self.assertLess(optimizer.opt_route.index(1),
                        optimizer.opt_route.index(3))

        optimizer.calc_next_iteration()
        self.assertEqual(sorted(optimizer.opt_route), [0, 1, 2, 3])
        self.assertLess(optimizer.opt_route.index(1),
                        optimizer.opt_route.index(3))
        self.assertIn("Opt. route", str(optimizer))

    def test_random_and_nearest_neighbor_initializers_make_complete_tours(self):
        matrix = DistanceMatrixClass()
        matrix.generate_matrix(_endpoints())
        population = PopulationClass([4, 8], matrix.matrix, 0.0)

        random_tour = population.random_begin(4)
        nearest_tour = population.heuristic_begin(matrix.matrix)
        nearest_next = population.heuristic_find_next(1, [0, 2, 3],
                                                      matrix.matrix)

        self.assertEqual(sorted(random_tour), [0, 1, 2, 3])
        self.assertEqual(sorted(nearest_tour), [0, 1, 2, 3])
        self.assertEqual(nearest_next, 2)

    def test_application_route_use_case_updates_layer_and_reports_it(self):
        from dxf2gcode.application.optimization.routes import OptimizeRoutes

        class Shape(object):
            def __init__(self, start, end, send_to_tsp):
                self.Pocket = False
                self.send_to_TSP = send_to_tsp
                self.endpoints = (start, end)

            def get_start_end_points(self):
                return self.endpoints

        class Layer(object):
            exp_order = [0, 1]
            nr = 4
            name = "test layer"

            def optimize(self):
                self.optimized = True

        class Optimizer(object):
            opt_route = [2, 1, 0]

            def __init__(self):
                self.iterations = 0

            def calc_next_iteration(self):
                self.iterations += 1

        start, end = Point(0, 0), Point(1, 0)
        shapes = [Shape(start, end, True), Shape(end, start, False)]
        layer = Layer()
        optimizer = Optimizer()
        factory_args = []

        def factory(endpoints, fixed_order, route_settings):
            factory_args.append((endpoints, fixed_order, route_settings))
            return optimizer

        updated = []
        result = OptimizeRoutes(factory, max_iterations=100,
                                start_point=Point(5, 5),
                                route_settings={"max_population": 8}).execute(
                                    [layer], shapes, after_layer=updated.append)

        self.assertEqual(layer.exp_order, [1, 0])
        self.assertTrue(layer.optimized)
        self.assertEqual(optimizer.iterations, 2)
        self.assertEqual(factory_args[0][1], [1])
        self.assertEqual(factory_args[0][0][-1], (Point(5, 5), Point(5, 5)))
        self.assertEqual(updated, [layer])
        self.assertEqual(result.shape_count, 2)


if __name__ == "__main__":
    unittest.main()
