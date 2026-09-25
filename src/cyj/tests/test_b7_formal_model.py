"""Formula and derivative checks for the frozen B7 candidate."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src/cyj"))
from b7_formal_model import BOUNDS, OUTPUT, elasticities, predict_gradient, substitution_rates


class FrozenB7Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = json.loads(OUTPUT.read_text(encoding="utf-8"))["parameters"]

    def test_gradient_finite_difference(self):
        points = [(0.7, 150.0, 0.5), (0.0701, 10.01, 0.101),
                  (11.969, 599.99, 0.999)]
        for point in points:
            _, gradient = predict_gradient(*point, self.model)
            for axis, value in enumerate(point):
                lo, hi = BOUNDS[axis]
                h = min(value * 1e-5, (value - lo) / 3, (hi - value) / 3)
                left, right = list(point), list(point)
                left[axis] -= h
                right[axis] += h
                finite_difference = (predict_gradient(*right, self.model)[0]
                                     - predict_gradient(*left, self.model)[0]) / (2 * h)
                self.assertAlmostEqual(gradient[axis], finite_difference,
                                       delta=max(1e-8, abs(gradient[axis]) * 1e-5))

    def test_support_and_derived_quantities(self):
        value, gradient = predict_gradient(0.7, 150.0, 0.5, self.model)
        self.assertLess(gradient[2], 0)
        self.assertEqual(len(elasticities(0.7, 150.0, 0.5, self.model)), 3)
        self.assertEqual(len(substitution_rates(0.7, 150.0, 0.5, self.model)), 3)
        with self.assertRaises(ValueError):
            predict_gradient(0.7, 0.134, 0.5, self.model)


if __name__ == "__main__":
    unittest.main()
