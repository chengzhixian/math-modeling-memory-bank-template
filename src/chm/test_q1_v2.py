from pathlib import Path
import math
import unittest
import numpy as np
from q1_interface import Q1Interface as DefaultQ1
from q1_interface_v1_3 import Q1Interface as FrozenRidge
from q1_mixture_decision_v2 import choose, quality_constraints
from q1_hull_bounds_v2 import data as hull_data, solve_node
from q2_interaction_scenarios_v2 import release as q2_release

ROOT = Path(__file__).resolve().parents[2]


class Q1V2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.q1 = DefaultQ1(ROOT)

    def test_default_is_interaction_and_legacy_is_immutable(self):
        self.assertEqual(self.q1.manifest["schema_version"], "chm.q1.v2.0")
        self.assertEqual(FrozenRidge(ROOT).manifest["schema_version"], "chm.q1.v1.3")
        self.assertEqual(len(self.q1.pairs), 10)
        with self.assertRaises(ValueError):
            self.q1.interaction_matrix()

    def test_frozen_predictions_and_reference(self):
        q1 = self.q1
        for row, idx in zip(q1.recipes[[0, 135, 476]], [0, 135, 476]):
            p = dict(zip(q1.domains, map(float, row)))
            result = q1.predict(p)
            self.assertTrue(result["support"]["in_A4_hull"])
            self.assertEqual(result["support"]["observed_index"], q1.recipe_ids[idx])
            direct = q1.intercepts + q1.main @ row + q1.gamma @ np.array([row[a] * row[b] for a,b in q1.pairs])
            np.testing.assert_allclose([result["loss"][k] for k in q1.targets], direct, atol=1e-12)
        np.testing.assert_allclose([q1.predict(q1.reference)["delta"][k] for k in q1.targets],
                                   np.zeros(13), atol=1e-10)

    def test_support_gate_and_gradient(self):
        q1 = self.q1
        outside = {d: float(i == 0) for i, d in enumerate(q1.domains)}
        if q1.support(outside)["in_A4_hull"]:
            self.skipTest("unit vertex happens to be in A4 hull")
        with self.assertRaises(ValueError):
            q1.predict(outside)
        self.assertFalse(q1.predict(outside, allow_extrapolation=True)["support"]["in_A4_hull"])
        x = (q1.recipes[0] + q1.recipes[1]) / 2
        p = dict(zip(q1.domains, map(float, x)))
        g = q1.gradient(p)
        eps = 1e-6
        a, b = 0, 1
        left, right = x.copy(), x.copy()
        left[a] += eps; left[b] -= eps
        right[a] -= eps; right[b] += eps
        fd = (q1._predict(left[None])[0] - q1._predict(right[None])[0]) / (2 * eps)
        np.testing.assert_allclose(fd, g[:, a] - g[:, b], atol=1e-8)

    def test_exact_finite_decision_and_quality(self):
        q1 = self.q1
        weights = {k: 1 / len(q1.targets) for k in q1.targets}
        relative = q1._predict(q1.recipes) / q1.reference_loss - 1
        for policy in ("unconstrained", "quality_direct", "quality_direct_and_near"):
            allowed, _, _ = quality_constraints(q1, q1.recipes, policy)
            result = choose(q1, weights, policy)
            index = q1.recipe_ids.index(result["selected_index"])
            self.assertTrue(allowed[index])
            self.assertTrue(np.all(relative[allowed].mean(axis=1) >= result["objective_relative"] - 1e-12))
            self.assertIsNone(result["B7_Q_score"])
        self.assertEqual(choose(q1, weights)["selected_index"], "136")
        self.assertEqual(choose(q1, weights, "quality_direct")["selected_index"], "301")

    def test_q2_recalculation_tracks_v2_manifest(self):
        manifest = q2_release()
        self.assertEqual(manifest["Q1_manifest_sha256"], self.q1.manifest_sha256)
        self.assertFalse(manifest["ready_for_Q3_empirical_absolute_loss"])
        self.assertEqual(manifest["conditional_scenario_count"], 3)

    def test_validation_reports_frozen_interaction_columns(self):
        rows = self.q1.ranking_validation("pile_cc")
        self.assertTrue(any(r["scope"] == "test_1B" and r["support_group"] == "all" for r in rows))
        self.assertTrue(all(r["rmse"] > 0 for r in rows))

    def test_hull_relaxation_bounds_feasible_blends(self):
        q1 = self.q1
        w = {k:1/len(q1.targets) for k in q1.targets}
        rng = np.random.default_rng(20260925)
        for mode in ("weighted","minimax"):
            prepared = hull_data(q1,"unconstrained",w,mode)
            box = tuple(zip(prepared[2],prepared[3]))
            lower, upper, omega, x, _ = solve_node(q1,prepared,box,mode)
            self.assertLessEqual(lower,upper+1e-8)
            np.testing.assert_allclose(omega.sum(),1,atol=1e-8)
            np.testing.assert_allclose(x,omega @ q1.recipes,atol=1e-8)
            for _ in range(20):
                ids = rng.choice(len(q1.recipes), 4, replace=False)
                mix = rng.dirichlet(np.ones(4)) @ q1.recipes[ids]
                relative = q1._predict(mix[None])[0] / q1.reference_loss - 1
                value = relative.mean() if mode == "weighted" else relative.max()
                self.assertLessEqual(lower,value+1e-7)


if __name__ == "__main__":
    unittest.main()
