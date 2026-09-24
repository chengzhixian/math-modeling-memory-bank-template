"""Quality candidate algebra and grouped split tests, independent of fit outputs."""
import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from quality_scaling import design, evaluate, fit, folds


class QualityScalingTests(unittest.TestCase):
    def test_quality_basis_and_prediction(self):
        x = np.array([[1, 10, .5], [1, 10, 1.]])
        self.assertTrue(np.allclose(design(x, [.3, .2], "linear_quality")[:, -1], [.5, 0]))
        self.assertTrue(np.allclose(design(x, [.3, .2], "log_quality")[:, -1], [np.log(2), 0]))
        p = dict(E=1, A=2, B=3, G=.4, alpha=.3, beta=.2)
        result = evaluate(p, x, "linear_quality")
        self.assertAlmostEqual(result[0] - result[1], .2)
        with self.assertRaises(ValueError):
            design(x, [.3, .2], "unknown")

    def test_held_levels_do_not_leak(self):
        x = np.array([[n, d, q] for n in [1, 2, 3] for d in [10, 20] for q in [.1, .5, .9]])
        splits = list(folds(x))
        self.assertEqual(len(splits), 8)
        axes = ("N_params_B", "D_tokens_B", "Q_score")
        for axis, value, train, test in splits:
            column = axes.index(axis)
            self.assertTrue(np.all(x[test, column] == value))
            self.assertFalse(np.any(x[train, column] == value))
            self.assertTrue(np.all(train != test))

    def test_fit_recovers_independent_fixture(self):
        x = np.array([[n, d, q] for n in [.1, .5, 1, 3] for d in [5, 20, 100, 200] for q in [.1, .5, .9]])
        p = dict(E=1.5, A=.4, B=1.2, G=.3, alpha=.3, beta=.2)
        y = evaluate(p, x, "linear_quality")
        result = fit(x, y, "linear_quality")
        self.assertTrue(result["converged"])
        self.assertLess(np.max(np.abs(evaluate(result["parameters"], x, "linear_quality") - y)), 1e-7)
        with self.assertRaises(ValueError):
            fit(x * 0, y, "linear_quality")
