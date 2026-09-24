from pathlib import Path
import math
import unittest

import numpy as np

from q1_interface import Q1Interface
from q1_multiloss_decision import (
    build_effect_matrix,
    load_a4,
    solve_minimax,
    solve_protected,
    solve_weighted,
)


ROOT = Path(__file__).resolve().parents[2]


class Q1MultiLossDecisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.q1 = Q1Interface(ROOT)
        cls.ids, raw_domains, x = load_a4(ROOT)
        (
            cls.targets,
            cls.domains,
            cls.x,
            cls.effects,
        ) = build_effect_matrix(cls.q1, raw_domains, x)

    def assert_valid_mixture(self, result):
        p = result["mixture"]
        self.assertEqual(set(p), set(self.domains))
        self.assertTrue(all(v >= -1e-10 for v in p.values()))
        self.assertTrue(math.isclose(sum(p.values()), 1.0, abs_tol=1e-8))

    def test_equal_weight_solution(self):
        w = np.full(len(self.targets), 1.0 / len(self.targets))
        result = solve_weighted(
            self.ids,
            self.domains,
            self.x,
            self.targets,
            self.effects,
            w,
        )
        self.assert_valid_mixture(result)
        self.assertEqual(result["mode"], "weighted")

    def test_minimax_solution(self):
        result = solve_minimax(
            self.ids,
            self.domains,
            self.x,
            self.targets,
            self.effects,
        )
        self.assert_valid_mixture(result)
        worst = max(result["target_effects"].values())
        self.assertAlmostEqual(worst, result["max_target_effect"], places=8)

    def test_reference_is_zero_effect(self):
        for target in self.targets:
            result = self.q1.relative_effect(self.q1.reference, target)
            self.assertAlmostEqual(result["delta_target_loss_1m"], 0.0, places=12)

    def test_protected_threshold_is_enforced(self):
        primary = self.targets[0]
        protected = self.targets[1]
        threshold = float(np.max(self.effects[:, self.targets.index(protected)]))
        result = solve_protected(
            self.ids,
            self.domains,
            self.x,
            self.targets,
            self.effects,
            primary,
            {protected: threshold},
        )
        self.assert_valid_mixture(result)
        self.assertLessEqual(
            result["target_effects"][protected],
            threshold + 1e-8,
        )


if __name__ == "__main__":
    unittest.main()
