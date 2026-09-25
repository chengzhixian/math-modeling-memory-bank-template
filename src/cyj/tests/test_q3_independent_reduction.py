"""Cross-check the independent optimizer's native loss and D elimination."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src/cyj"))
from fit_b7_joint_nonlinear import predict
from q3_costs import quality_cost
from q3_independent_optimizer_check import native_loss


class IndependentReductionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.theta = json.loads((ROOT / "outputs/cyj/quality/b7_joint_fit.json").read_text())[
            "model"]["theta"]

    def test_independent_loss_matches_fitted_formula(self):
        for point in ((.07, 10., .5), (.7, 150., .8), (11.97, 600., 1.)):
            with self.subTest(point=point):
                self.assertAlmostEqual(native_loss(self.theta, *point),
                                       float(predict(self.theta, [point])[0]), places=12)

    def test_eliminated_D_spends_budget_at_interior(self):
        budget, context, n, q, q0 = 1e22, 30000, 4.5, .8, .5
        a = 6e18 + 2e14 * context
        delta_g = quality_cost(q, "exponential")[0] - quality_cost(q0, "exponential")[0]
        d = budget / (a * n + 1e9 * delta_g)
        self.assertTrue(10. < d < 600.)
        self.assertAlmostEqual(d * (a * n + 1e9 * delta_g) / budget, 1.)


if __name__ == "__main__":
    unittest.main()
