"""Check unit conversion and derivatives at the attention/training crossover."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src/cyj"))
from q3_costs import costs


class ContextCriticalTests(unittest.TestCase):
    def scenario(self, family, context, q=.7, n=.7, d=150.):
        return costs(N_params_B=n, D_tokens_B=d, Q_score=q, Q0=.5,
                     L_ctx=context, quality_family=family,
                     allowed_contexts=(30000, 32768))

    def test_training_attention_crossover(self):
        exact = self.scenario("exponential", 30000)
        above = self.scenario("exponential", 32768)
        self.assertAlmostEqual(exact["attention"] / exact["training"], 1.)
        self.assertAlmostEqual(exact["context_critical_tokens"], 30000.)
        self.assertGreater(above["attention"] / above["training"], 1.)
        self.assertEqual(above["context_source_status"],
                         "CYJ_external_sensitivity_not_C7_observation")

    def test_three_cost_family_gradients(self):
        for family in ("exponential", "power", "logarithmic"):
            with self.subTest(family=family):
                point = dict(n=.7, d=150., q=.7)
                baseline = self.scenario(family, 30000, **point)
                for field, analytic in (("n", "N_params_B"), ("d", "D_tokens_B"),
                                        ("q", "Q_score_right")):
                    step = point[field] * 1e-5
                    low, high = dict(point), dict(point)
                    low[field] -= step
                    high[field] += step
                    numeric = (self.scenario(family, 30000, **high)["total"] -
                               self.scenario(family, 30000, **low)["total"]) / (2 * step)
                    self.assertAlmostEqual(numeric / baseline["gradient"][analytic], 1., delta=1e-6)
                at_base = self.scenario(family, 30000, q=.5)
                self.assertEqual(at_base["gradient"]["Q_score_left"], 0.)
                self.assertGreater(at_base["gradient"]["Q_score_right"], 0.)


if __name__ == "__main__":
    unittest.main()
