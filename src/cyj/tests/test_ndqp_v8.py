"""Independent numerical and source-role checks for the conditional v8 predictor."""
from __future__ import annotations

import csv
import json
import math
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/"src/cyj"))

from fit_b7_quality_extension_from_b1 import B1_SHA, b1_parameters, fit_gamma, predict
from ndqp_scenarios_v8 import ConditionalV8, VERSION, request
from quality_scaling import source_data
from validate_b3_against_b1 import normalized


class V8Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = ConditionalV8()
        cls.q1 = cls.model.q1
        cls.weights = {t: 1/len(cls.q1.targets) for t in cls.q1.targets}
        cls.center = cls.q1.recipes.mean(axis=0)
        cls.p = cls.q1.p_dict(cls.center)

    def test_b1_backbone_is_exactly_pinned(self):
        fit = json.loads((ROOT/"outputs/cyj/q2_v8/b7_quality_extension.json").read_text(encoding="utf-8"))
        self.assertEqual(fit["B1_fit_sha256"], B1_SHA)
        self.assertEqual(self.model.b1, b1_parameters())
        self.assertEqual(fit["B1_parameters"], self.model.b1)
        self.assertEqual(len(fit["quality_parameters"]), 3)

    def test_three_parameter_fit_independent_linear_recalculation(self):
        _, x, y, _ = source_data()
        gamma = fit_gamma(self.model.b1, x, y, 0)
        self.assertTrue(np.allclose(gamma, self.model.gamma, rtol=0, atol=1e-11))
        self.assertAlmostEqual(float(np.sqrt(np.mean((predict(self.model.b1, gamma, x)-y)**2))),
                               .048540124773653444, places=10)

    def test_q1_quality_reference_anchor_and_coverage(self):
        qa = self.model.qa(self.q1.reference, "direct_and_near")
        self.assertAlmostEqual(qa["Q_A_mapped"], qa["Q_A_reference"])
        self.assertAlmostEqual(qa["Q_B_proxy"], qa["Q_B_reference_proxy"])
        self.assertEqual(qa["mapped_domain_count"], 6)
        self.assertLess(qa["mapped_coverage"], 1)
        self.assertEqual(sum(row["Q_A"] is None for row in self.q1.qa_rows.values()), 11)
        reference = self.model.predict_baseline_v8(1, 100, self.q1.reference, self.weights,
                                                   p_policy="algebraic_reference_only")
        self.assertAlmostEqual(reference["Q1_weighted_effect"], 0, places=12)
        self.assertAlmostEqual(reference["Loss"], reference["NDQ_loss"], places=12)

    def test_zero_mapped_coverage_fails(self):
        point = self.q1.p_dict(self.q1.recipes[130])
        with self.assertRaisesRegex(ValueError, "positive mapped coverage"):
            self.model.predict_baseline_v8(1, 100, point, self.weights, p_policy="observed_512")

    def test_quality_bridge_monotone_and_deterministic(self):
        low = self.q1.p_dict(self.q1.recipes[10])
        high = self.q1.p_dict(self.q1.recipes[20])
        a, b = self.model.qa(low, "direct_and_near"), self.model.qa(high, "direct_and_near")
        self.assertGreaterEqual((a["Q_A_mapped"]-b["Q_A_mapped"])*
                                (a["Q_B_proxy"]-b["Q_B_proxy"]), 0)
        self.assertEqual(a["Q_B_proxy"], self.model.qa(low, "direct_and_near")["Q_B_proxy"])
        self.assertTrue(.1 <= a["Q_B_proxy"] <= 1)
        for scale in (.5, 1.0, 1.5):
            self.assertTrue(.1 <= self.model.qa(self.p, "direct_and_near", scale)["Q_B_proxy"] <= 1)

    def test_ndq_and_p_gradients_match_finite_differences(self):
        result = self.model.predict_baseline_v8(1, 100, self.p, self.weights, p_policy="convex_hull")
        for name, step, args_plus, args_minus in (
            ("N_B", 1e-5, (1+1e-5, 100), (1-1e-5, 100)),
            ("D_B", 1e-3, (1, 100+1e-3), (1, 100-1e-3))):
            plus = self.model.predict_baseline_v8(*args_plus, self.p, self.weights, p_policy="convex_hull")["Loss"]
            minus = self.model.predict_baseline_v8(*args_minus, self.p, self.weights, p_policy="convex_hull")["Loss"]
            self.assertAlmostEqual((plus-minus)/(2*step), result["gradients"][name], delta=2e-7)
        direction = self.q1.recipes[10]-self.q1.recipes[20]
        step = 1e-4
        plus = self.model.predict_baseline_v8(1, 100, self.q1.p_dict(self.center+step*direction),
                                              self.weights, p_policy="convex_hull")["Loss"]
        minus = self.model.predict_baseline_v8(1, 100, self.q1.p_dict(self.center-step*direction),
                                               self.weights, p_policy="convex_hull")["Loss"]
        gradient = np.array([result["gradients"]["p_ambient"][d] for d in self.q1.domains])
        self.assertAlmostEqual((plus-minus)/(2*step), float(gradient@direction), delta=2e-6)

    def test_domain_pair_hessian_direction_matches_finite_difference(self):
        direction = self.q1.recipes[10]-self.q1.recipes[20]
        h = self.model.p_hessian_baseline(1, 100, self.p, self.weights)
        step = 5e-4
        value = self.model.predict_baseline_v8(1, 100, self.p, self.weights, p_policy="convex_hull")["Loss"]
        plus = self.model.predict_baseline_v8(1, 100, self.q1.p_dict(self.center+step*direction),
                                              self.weights, p_policy="convex_hull")["Loss"]
        minus = self.model.predict_baseline_v8(1, 100, self.q1.p_dict(self.center-step*direction),
                                               self.weights, p_policy="convex_hull")["Loss"]
        self.assertAlmostEqual((plus-2*value+minus)/step**2, float(direction@h@direction), delta=2e-5)

    def test_pair_tables_are_full_and_hull_feasible(self):
        for name in ("domain_pair_substitution.csv", "domain_pair_interaction.csv"):
            with (ROOT/"outputs/cyj/q2_v8"/name).open(encoding="utf-8", newline="") as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(len(rows), 136)
            self.assertEqual(len({(r["domain_i"], r["domain_j"]) for r in rows}), 136)
            self.assertTrue(all(float(r.get("feasible_epsilon_max", r.get("forward_epsilon_max"))) > 0
                                for r in rows))

    def test_b3_is_quantitative_but_not_independent(self):
        self.assertTrue(np.allclose(normalized([5, 3, 1]), [1, .5, 0]))
        summary = json.loads((ROOT/"outputs/cyj/q2_v8/b2_b3_validation_summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["summary"]["B3"]["trajectories"], 8)
        self.assertLess(summary["summary"]["B3"]["mean_normalized_RMSE"], .01)
        self.assertIsNone(summary["absolute_cross_source_RMSE_claim"])

    def test_public_baseline_rejects_native_q_and_support_shift(self):
        point = self.q1.p_dict(self.q1.recipes[135])
        base = {"schema_version": VERSION, "mode": "baseline", "N_params_B": 1,
                "D_tokens_B": 100, "p": point, "weights": self.weights,
                "p_policy": "observed_512", "quality_mapping_policy": "direct_and_near"}
        self.assertGreater(request(self.model, base)["Loss"], 0)
        with self.assertRaisesRegex(ValueError, "baseline rejects"):
            request(self.model, {**base, "native_QB": .5})
        with self.assertRaisesRegex(ValueError, "outside v8 common"):
            request(self.model, {**base, "N_params_B": .07})

    def test_native_quality_gradient_and_no_transfer(self):
        point = self.q1.p_dict(self.q1.recipes[135])
        value = self.model.evaluate(1, 100, point, self.weights, p_policy="observed_512",
                                    quality_mode="native_QB_sensitivity", native_QB=.5,
                                    mixture_bridge_lambda=0)
        self.assertIsNone(value["Q_A_mapped"])
        self.assertAlmostEqual(value["Loss"], value["NDQ_loss"])
        self.assertTrue(all(abs(g) < 1e-12 for g in value["gradients"]["p_ambient"].values()))


if __name__ == "__main__":
    unittest.main()
