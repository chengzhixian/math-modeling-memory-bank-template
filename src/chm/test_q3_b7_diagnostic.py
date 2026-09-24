import math
import unittest

from q3_b7_diagnostic import CONTEXTS, FAMILIES, Q0, cost_parts, load_model, loss, optimize


class B7DiagnosticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = load_model()

    def test_published_prediction_and_gradient_direction(self):
        p = self.model["models"]["linear_quality"]["full_fit"]["parameters"]
        self.assertAlmostEqual(loss(.07, 10, .5, p), 3.492870995028143, places=8)
        self.assertLess(loss(.07, 10, .6, p), loss(.07, 10, .5, p))

    def test_support_infeasibility_and_all_costs(self):
        for family in FAMILIES:
            row = optimize(1e19, CONTEXTS[-1], family, self.model)
            self.assertFalse(row["feasible"])
            self.assertGreater(row["minimum_supported_cost_FLOPs"], 1e19)
            row = optimize(1e22, CONTEXTS[0], family, self.model)
            self.assertTrue(row["feasible"])
            total = sum(cost_parts(row["N_params_B"], row["D_tokens_B"], row["Q_score"], Q0, CONTEXTS[0], family))
            self.assertAlmostEqual(total / 1e22, row["budget_utilization"], places=9)
            self.assertLessEqual(total / 1e22, 1 + 1e-9)

    def test_nested_search_beats_independent_coarse_grid(self):
        budget, context, family = 1e22, 8192, "power"
        row = optimize(budget, context, family, self.model)
        p = self.model["models"]["linear_quality"]["full_fit"]["parameters"]
        support = self.model["support"]
        nlo, nhi = support["N_params_B"][0], support["N_params_B"][-1]
        dlo, dhi = support["D_tokens_B"][0], support["D_tokens_B"][-1]
        coarse = math.inf
        for i in range(41):
            q = Q0 + (1 - Q0) * i / 40
            for j in range(51):
                n = nlo + (nhi - nlo) * j / 50
                # For fixed (N,Q), larger D always reduces the B7 diagnostic Loss.
                unit_cost = sum(cost_parts(n, 1, q, Q0, context, family))
                d = min(dhi, budget / unit_cost)
                if d >= dlo:
                    coarse = min(coarse, loss(n, d, q, p))
        self.assertLessEqual(row["B7_diagnostic_loss"], coarse + 1e-8)


if __name__ == "__main__":
    unittest.main()
