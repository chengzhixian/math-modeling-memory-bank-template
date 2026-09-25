"""Regression checks for the pinned v8 Q3 conditional calculation."""
from __future__ import annotations

import math
import csv
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

from scipy.optimize import minimize

sys.path.insert(0, str(Path(__file__).resolve().parent))
from q3_conditional_v8 import OUTPUT, main_grid, main_policy, native_q_sensitivity_grid, observed_joint_grid, solve_fixed_p  # noqa: E402
from q3_generic_solver import cost_and_grad  # noqa: E402
from q3_v8_inputs import EXPORT, load_v8, verify_export  # noqa: E402
from q3_v8_publish import validate, verify_manifest  # noqa: E402
from q3_v8_transition_scan import state  # noqa: E402


class ConditionalV8Q3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model, cls.bounds = load_v8()
        cls.policy = main_policy(cls.model)

    def solve_main(self, budget=1e22, context=8192, family="power"):
        return solve_fixed_p(self.model, self.bounds, self.policy["p"],
                             self.policy["weights"], p_policy="observed_512",
                             mapping_policy="direct_and_near", budget=budget,
                             context=context, family=family, recipe_index="172")

    def test_export_rejects_tampered_producer_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for relative in (
                "src/chm/q1_interface_v2.py", "src/cyj/chm_q1_v2_consumer.py",
                "src/cyj/fit_b7_quality_extension_from_b1.py", "src/cyj/ndqp_scenarios_v8.py",
                "interfaces/chm/q1_interface_v2.json", "outputs/chm/q1_v2_hull_bounds/bounds.json",
                "outputs/cyj/classic/classic_fit.json", "outputs/cyj/q2_v8/b7_quality_extension.json",
                "outputs/cyj/q2_v8/main_policy.json", "outputs/cyj/q2_v8/manifest.json",
                "outputs/cyj/q2_v8/acceptance.json", "outputs/cyj/q2_v8_release_verification.json",
            ):
                destination = root / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(EXPORT / relative, destination)
            (root / "src/cyj/ndqp_scenarios_v8.py").write_text("tampered\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "differs from pinned Git object"):
                verify_export(root)

    def test_v8_main_smoke_and_cost(self):
        row = self.solve_main()
        self.assertEqual(row["status"], "conditional_v8_fixed_policy_feasible")
        self.assertAlmostEqual(row["Q_B_proxy"], 0.6713607648391644, places=12)
        self.assertAlmostEqual(row["conditional_bridge_loss"], 2.094421151267249, places=9)
        self.assertLessEqual(row["C_total_FLOPs"], 1e22*(1+1e-9))
        self.assertAlmostEqual(row["C_train_FLOPs"]+row["C_attention_FLOPs"]+
                               row["C_quality_FLOPs"], row["C_total_FLOPs"], delta=1e9)
        self.assertLessEqual(row["fixed_p_convex_gap"], 1e-8)

    def test_independent_slsqp_matches_fixed_policy_reduction(self):
        row = self.solve_main()
        p, weights = self.policy["p"], self.policy["weights"]
        q = row["Q_B_proxy"]
        budget, context, family = 1e22, 8192, "power"

        def objective(z):
            n, d = map(math.exp, z)
            result = self.model.predict_baseline_v8(n, d, p, weights, p_policy="observed_512")
            return result["Loss"], [n*result["gradients"]["N_B"],
                                    d*result["gradients"]["D_B"]]

        def constraint(z):
            n, d = map(math.exp, z)
            cost, grad = cost_and_grad(n, d, q, .5, context, family)
            return 1-cost/budget, [-n*grad[0]/budget, -d*grad[1]/budget]

        result = minimize(objective, [math.log(1), math.log(100)], jac=True,
                          method="SLSQP", bounds=[tuple(map(math.log, axis)) for axis in self.bounds[:2]],
                          constraints=[{"type": "ineq", "fun": lambda z: constraint(z)[0],
                                        "jac": lambda z: constraint(z)[1]}],
                          options={"ftol": 1e-12, "maxiter": 1000})
        self.assertTrue(result.success, result.message)
        self.assertAlmostEqual(result.fun, row["conditional_bridge_loss"], delta=1e-8)

    def test_declared_q1_primary_policy_is_below_q0(self):
        from q3_joint_v7_check import policy_candidates
        candidate = policy_candidates(self.model)[0]
        result = solve_fixed_p(self.model, self.bounds, candidate["p"], candidate["weights"],
                               p_policy=candidate["p_policy"], mapping_policy="direct_and_near",
                               budget=1e22, context=8192, family="power")
        self.assertEqual(result["status"], "policy_quality_below_Q0")
        self.assertLess(result["Q_B_proxy"], .5)

    def test_fixed_and_observed_joint_grid_roles(self):
        fixed = main_grid(self.model, self.bounds, self.policy)
        joint = observed_joint_grid(self.model, self.bounds, fixed)
        self.assertEqual(len(fixed), 36)
        self.assertEqual(len(joint), 36)
        self.assertEqual(sum(r["status"] == "conditional_v8_fixed_policy_feasible" for r in fixed), 30)
        self.assertEqual(sum(r["status"] == "conditional_v8_fixed_policy_feasible" for r in joint), 33)
        self.assertEqual({r["eligible_observed_recipes"] for r in joint}, {87})
        self.assertEqual({r["recipe_index"] for r in joint if r.get("recipe_index")}, {"172", "477"})
        self.assertTrue(all(r.get("fixed_policy_regret") is None or r["fixed_policy_regret"] >= -1e-10
                            for r in joint))

    def test_native_quality_is_labeled_sensitivity(self):
        rows = native_q_sensitivity_grid(self.model, self.bounds, self.policy)
        self.assertEqual(len(rows), 36)
        self.assertEqual(sum(r["status"] == "conditional_v8_native_Q_sensitivity_feasible" for r in rows), 33)
        sample = next(r for r in rows if r["budget_FLOPs"] == 1e22 and
                      r["context_tokens"] == 8192 and r["quality_family"] == "power")
        self.assertEqual(sample["model_scope"], "CYJ_v8_native_QB_sensitivity")
        self.assertAlmostEqual(sample["Q_score"], 1.0)
        self.assertLess(sample["global_gap"], 1.1e-7)

    def test_published_result_gates_and_short_context_transition(self):
        counts = validate(OUTPUT)
        verify_manifest(OUTPUT)
        self.assertEqual(counts["transition_brackets"], 82)
        import csv
        with (OUTPUT/"transitions.csv").open(encoding="utf-8", newline="") as stream:
            transitions = list(csv.DictReader(stream))
        recipe_switches = [r for r in transitions if r["scenario"] == "observed_joint" and
                           r["context_tokens"] == "8192" and r["quality_family"] == "power" and
                           r["state_left"].startswith("recipe=477;") and
                           r["state_right"].startswith("recipe=172;")]
        self.assertEqual(len(recipe_switches), 1)
        self.assertLess(float(recipe_switches[0]["relative_width"]), 1e-4)
        self.assertEqual(state({"status": "infeasible_within_v8_support"}),
                         "infeasible_within_v8_support")

    def test_assumption_stress_replays_v8_sensitivity_mode(self):
        row = solve_fixed_p(self.model, self.bounds, self.policy["p"], self.policy["weights"],
                            p_policy="observed_512", mapping_policy="direct_and_near",
                            budget=1e22, context=8192, family="power", recipe_index="172",
                            quality_bridge_scale=1.5, mixture_bridge_lambda=2.0)
        upstream = self.model.evaluate(row["N_params_B"], row["D_tokens_B"],
                                       self.policy["p"], self.policy["weights"],
                                       p_policy="observed_512",
                                       quality_mode="q1_quality_bridge_sensitivity",
                                       quality_bridge_scale=1.5, mixture_bridge_lambda=2.0)
        self.assertEqual(row["status"], "conditional_v8_fixed_policy_feasible")
        self.assertAlmostEqual(row["conditional_bridge_loss"], upstream["Loss"], places=11)
        self.assertAlmostEqual(row["Q_B_proxy"], upstream["Q_B_proxy_or_native"], places=12)

    def test_assumption_and_external_published_claims(self):
        verify_manifest(OUTPUT)
        with (OUTPUT/"assumption_official_grid.csv").open(encoding="utf-8", newline="") as stream:
            scenarios = list(csv.DictReader(stream))
        self.assertEqual(len(scenarios), 243)
        low = {(r["scenario"], r["budget_FLOPs"], r["context_tokens"],
                r["quality_family"]): r for r in scenarios}
        def recipe(label):
            return low[(label, "1e+19", "8192", "power")]["recipe_index"]
        self.assertEqual(recipe("baseline"), "477")
        self.assertEqual(recipe("Q0_0p60"), "475")
        self.assertEqual(recipe("Q0_0p65"), "172")
        self.assertEqual(recipe("mixture_lambda_0"), "159")
        external = json.loads((OUTPUT/"external_nd_audit.json").read_text(encoding="utf-8"))
        self.assertFalse(external["full_cross_attachment_optimum_validated"])
        self.assertEqual(external["common_support_models"], 42)
        self.assertEqual(external["budget_restricting_selection_match_count"], 5)
        self.assertEqual(external["budget_restricting_selection_total"], 6)


if __name__ == "__main__":
    unittest.main()
