import unittest

from geometry import bounding_side, separating_gap, validate_packing


class GeometryTests(unittest.TestCase):
    def test_single_square_and_translation_invariance(self):
        valid, _, side = validate_packing([(5.0, -3.0, 0.0)], gap=0.0)
        self.assertTrue(valid)
        self.assertAlmostEqual(side, 1.0)

    def test_axis_aligned_touch_is_not_strictly_separated(self):
        gap = separating_gap((0.5, 0.5, 0.0), (1.5, 0.5, 0.0))
        self.assertAlmostEqual(gap, 0.0)

    def test_axis_aligned_positive_clearance_is_valid(self):
        valid, _, _ = validate_packing([(0.5, 0.5, 0.0), (1.5001, 0.5, 0.0)])
        self.assertTrue(valid)

    def test_overlap_is_rejected(self):
        valid, message, _ = validate_packing([(0.5, 0.5, 0.0), (1.4, 0.5, 0.0)], gap=0.0)
        self.assertFalse(valid)
        self.assertIn("pair", message)

    def test_rotated_sat_detects_overlap(self):
        valid, message, _ = validate_packing([(0.7, 0.7, 0.7853981633974483), (1.5, 0.7, 0.0)], gap=0.0)
        self.assertFalse(valid)
        self.assertIn("pair", message)

    def test_square_side_uses_corner_span(self):
        self.assertGreater(bounding_side([(0.5, 0.5, 0.7853981633974483)]), 1.4)


if __name__ == "__main__":
    unittest.main()
