from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from q3_nd_baseline import bounded_optimum


class Q3NDDiagnosticTests(unittest.TestCase):
    def test_low_budget_is_interior_and_spends_budget(self):
        out = bounded_optimum(1e19, 2048)
        self.assertEqual(out["support_flags"], "none")
        self.assertAlmostEqual(out["budget_utilization"], 1.0, places=10)
        self.assertAlmostEqual(out["N_params_B"], 0.221311693734, places=8)
        self.assertAlmostEqual(out["D_tokens_B"], 7.04960381459, places=8)

    def test_medium_budget_low_context_hits_D_max(self):
        out = bounded_optimum(1e22, 2048)
        self.assertIn("D_max", out["support_flags"])
        self.assertAlmostEqual(out["D_tokens_B"], 299.893, places=9)
        self.assertAlmostEqual(out["budget_utilization"], 1.0, places=10)

    def test_high_budget_is_support_limited(self):
        out = bounded_optimum(1e24, 8192)
        self.assertIn("N_max", out["support_flags"])
        self.assertIn("D_max", out["support_flags"])
        self.assertIn("support_limited_budget_slack", out["support_flags"])
        self.assertLess(out["budget_utilization"], 0.03)

    def test_longer_context_worsens_same_budget_diagnostic_loss(self):
        low = bounded_optimum(1e19, 2048)
        high = bounded_optimum(1e19, 131072)
        self.assertGreater(high["diagnostic_loss"], low["diagnostic_loss"])


if __name__ == "__main__":
    unittest.main()
