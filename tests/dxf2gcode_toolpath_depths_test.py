"""Regression tests for the pure toolpath depth sequence rule."""
from __future__ import absolute_import

import os
import sys
import unittest

_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(_TEST_DIR), "source"))

from dxf2gcode.domain.toolpath.depths import calculate_depth_passes  # noqa: E402


class TestDepthPassCalculation(unittest.TestCase):
    def test_slices_end_exactly_at_final_depth(self):
        self.assertEqual(calculate_depth_passes(0.0, 2.0, -5.0),
                         [-2.0, -4.0, -5.0])

    def test_single_pass_starts_at_final_depth(self):
        self.assertEqual(calculate_depth_passes(0.0, 2.0, -5.0,
                                                single_pass=True),
                         [-5.0])

    def test_zero_slice_preserves_one_initial_pass(self):
        self.assertEqual(calculate_depth_passes(0.0, 0.0, -5.0), [0.0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
