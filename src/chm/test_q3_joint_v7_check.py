"""Q1 policy and conditional bridge checks for Q3."""
import math
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from q3_conditional_grid import B7Adapter, solve_scenario  # noqa: E402
from q3_v7_inputs import load_release  # noqa: E402
from q3_joint_v7_check import evaluate_policy, evaluate_bridge_sensitivity, policy_candidates  # noqa: E402


class JointV7PolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = load_release(Path(__file__).resolve().parents[2] / ".upstream/cyj-v7")
        cls.row = solve_scenario(B7Adapter(), 1e22, 8192, "power")
        cls.weights = {target: 1 / len(cls.model.q1.targets) for target in cls.model.q1.targets}

    def test_zero_bridge_has_no_unique_p(self):
        p = self.model.q1.p_dict(self.model.q1.recipes[135])
        result = evaluate_bridge_sensitivity(self.model, self.row, p, self.weights,
                                             "observed_512", bridge_lambda=0.0, eta=0.0)
        self.assertEqual(result["p_identifiability"], "unidentified")
        self.assertAlmostEqual(result["conditional_bridge_loss"], self.row["B_native_loss"])

    def test_v7_baseline_factorization(self):
        p = self.model.q1.p_dict(self.model.q1.recipes[135])
        result = evaluate_policy(self.model, self.row, p, self.weights, "observed_512")
        self.assertTrue(math.isclose(result["conditional_bridge_loss"],
                                     result["B_native_loss"] * math.exp(result["r_w"]), rel_tol=1e-10))
        self.assertEqual(result["status"], "conditional_scenario")

    def test_observed_policy_rejects_unobserved_hull_point(self):
        p = self.model.q1.p_dict((self.model.q1.recipes[0] + self.model.q1.recipes[1]) / 2)
        with self.assertRaisesRegex(ValueError, "observed"):
            evaluate_policy(self.model, self.row, p, self.weights, "observed_512")

    def test_signed_q1_candidates_have_declared_support(self):
        candidates = policy_candidates(self.model)
        self.assertEqual(len(candidates), 4)
        self.assertEqual(candidates[0]["p_policy"], "convex_hull")
        for item in candidates:
            self.assertTrue(self.model.q1.support(item["p"], item["p_policy"])["in_A4_hull"])
            self.assertAlmostEqual(sum(item["p"].values()), 1.0)


if __name__ == "__main__":
    unittest.main()
