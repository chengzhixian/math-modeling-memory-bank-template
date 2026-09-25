"""Official Q3 budget and cost checks against the pinned B7 model."""
import math
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from q3_conditional_grid import B7Adapter, solve_scenario, main_grid, transition_pairs, refine_transition, scan_group, midpoint_refine, structural_state  # noqa: E402


class ConditionalGridTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = B7Adapter()

    def test_long_context_low_budget_is_explicitly_infeasible(self):
        row = solve_scenario(self.model, 1e19, 131072, "power")
        self.assertEqual(row["status"], "infeasible_within_B7_support")
        self.assertAlmostEqual(row["minimum_cost_FLOPs"], 2.255008e19, delta=1e9)
        self.assertIsNone(row["B_native_loss"])

    def test_three_cost_terms_sum_to_total(self):
        row = solve_scenario(self.model, 1e22, 8192, "power")
        self.assertEqual(row["status"], "conditional_B_native_feasible")
        parts = ("C_train_FLOPs", "C_quality_FLOPs", "C_attention_FLOPs")
        self.assertAlmostEqual(sum(row[k] for k in parts), row["C_total_FLOPs"], delta=1e-8 * row["C_total_FLOPs"])
        self.assertLessEqual(row["C_total_FLOPs"], 1e22 * (1 + 1e-8))
        self.assertTrue(row["kkt_check_pass"])
        self.assertLess(row["global_gap"], 2e-7)

    def test_attention_training_ratio_matches_problem(self):
        row = solve_scenario(self.model, 1e22, 8192, "exponential")
        self.assertTrue(math.isclose(row["C_attention_FLOPs"] / row["C_train_FLOPs"], 8192 / 30000, rel_tol=1e-12))

    def test_grid_keeps_official_infeasibility(self):
        rows = main_grid(self.model)
        self.assertEqual(len(rows), 36)
        invalid = [r for r in rows if r["status"] == "infeasible_within_B7_support"]
        self.assertEqual(len(invalid), 3)
        self.assertTrue(all(r["budget_FLOPs"] == 1e19 and r["context_tokens"] == 131072 for r in invalid))

    def test_transition_pairs_ignore_feasibility_boundary(self):
        rows = [
            {"budget_FLOPs": 1.0, "context_tokens": 2048, "quality_family": "power", "status": "infeasible_within_B7_support"},
            {"budget_FLOPs": 2.0, "context_tokens": 2048, "quality_family": "power", "status": "conditional_B_native_feasible", "active_set": "N_min;budget"},
            {"budget_FLOPs": 3.0, "context_tokens": 2048, "quality_family": "power", "status": "conditional_B_native_feasible", "active_set": "budget"},
        ]
        brackets = transition_pairs(rows)
        self.assertEqual(len(brackets), 1)
        self.assertEqual((brackets[0]["budget_left"], brackets[0]["budget_right"]), (2.0, 3.0))

    def test_transition_refinement_brackets_known_change(self):
        left = {"budget_FLOPs": 2.0, "context_tokens": 2048, "quality_family": "power",
                "active_set": "N_min;budget", "status": "conditional_B_native_feasible"}
        right = {**left, "budget_FLOPs": 4.0, "active_set": "budget"}

        def fake_solve(budget):
            return {**left, "budget_FLOPs": budget,
                    "active_set": "N_min;budget" if budget < 3 else "budget"}

        bracket = refine_transition(left, right, fake_solve, relative_width=1e-5)
        self.assertLess(bracket["budget_right"] / bracket["budget_left"] - 1, 1e-5)
        self.assertLess(bracket["budget_left"], 3)
        self.assertGreaterEqual(bracket["budget_right"], 3)

    def test_scan_group_is_ordered_and_monotone(self):
        rows = scan_group(self.model, 2048, "power", points=5)
        self.assertEqual(len(rows), 5)
        self.assertEqual(rows[0]["budget_FLOPs"], 1e19)
        self.assertAlmostEqual(rows[-1]["budget_FLOPs"], 1e24, delta=1e10)
        losses = [r["B_native_loss"] for r in rows if r["B_native_loss"] is not None]
        self.assertTrue(all(a >= b - 1e-7 for a, b in zip(losses, losses[1:])))

    def test_midpoint_probe_finds_state_hidden_between_equal_endpoints(self):
        left = {"budget_FLOPs": 2.0, "active_set": "A"}
        right = {"budget_FLOPs": 4.0, "active_set": "A"}
        refined = midpoint_refine([left, right],
                                  lambda budget: {"budget_FLOPs": budget, "active_set": "B"})
        self.assertEqual([r["active_set"] for r in refined], ["A", "B", "A"])

    def test_support_corner_is_one_stable_state_at_budget_equality(self):
        boundary = {"active_set": "D_max;N_max;Q1;budget"}
        beyond = {"active_set": "D_max;N_max;Q1"}
        self.assertEqual(structural_state(boundary), structural_state(beyond))


if __name__ == "__main__":
    unittest.main()
