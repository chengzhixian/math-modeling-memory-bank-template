"""Independent checks for the new conditional bridge and pinned Q1 release."""
import copy
import math
import shutil
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src/cyj"))

from chm_q1_v2_consumer import Q1V2Consumer, sha256
from ndqp_scenarios_v7 import ConditionalV7, THETA, b7, request, VERSION


class ConditionalV7Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = ConditionalV7(ROOT)
        cls.q1 = cls.model.q1
        cls.p = cls.q1.p_dict(cls.q1.recipes[135])
        cls.w = {target: 1/13 for target in cls.q1.targets}

    def test_manifest_and_reference_anchor(self):
        with self.assertRaisesRegex(ValueError, "manifest identity mismatch"):
            Q1V2Consumer(ROOT, expected_sha="0" * 64)
        self.assertEqual(self.q1.manifest_sha256,
                         "c621f7e405106e42720f918f490235b5e8becefb0f7c8cb997736e96337117a9")
        result = self.model.predict_baseline(1, 100, .5, self.q1.reference, self.w,
                                             p_policy="algebraic_reference_only")
        self.assertAlmostEqual(result["Loss"], result["B7_loss"], places=10)
        self.assertTrue(result["conditional_on_bridge_assumptions"])
        self.assertFalse(result["empirically_calibrated_A_to_B"])

    def test_producer_file_hash_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = Path("interfaces/chm/q1_interface_v2.json")
            (root / manifest).parent.mkdir(parents=True)
            shutil.copy2(ROOT / manifest, root / manifest)
            source = Path("outputs/chm/q1_v2/interaction_coefficients_13_targets.json")
            (root / source).parent.mkdir(parents=True)
            (root / source).write_bytes((ROOT / source).read_bytes() + b" ")
            with self.assertRaisesRegex(ValueError, "identity mismatch: model"):
                Q1V2Consumer(root)

    def test_bound_file_hash_fail_closed(self):
        def changed_bounds(path):
            return "0"*64 if Path(path).name == "bounds.json" else sha256(path)
        with mock.patch("chm_q1_v2_consumer.sha256", side_effect=changed_bounds):
            with self.assertRaisesRegex(ValueError, "hull bounds identity mismatch"):
                Q1V2Consumer(ROOT)

    def test_b7_direct_formula_and_gradients(self):
        e, a, b, alpha, beta, g0, gn, gd = THETA
        expected = e+a*1**-alpha+b*100**-beta+(1-.5)*(g0+gn*math.log(1)+gd*math.log(1))
        value, gradient = b7(1, 100, .5)
        self.assertAlmostEqual(value, expected, places=12)
        self.assertAlmostEqual(gradient[2], -g0, places=12)
        for index, step in enumerate((1e-5, 1e-3, 1e-5)):
            point = [1, 100, .5]
            point[index] += step
            plus = b7(*point)[0]
            point[index] -= 2*step
            minus = b7(*point)[0]
            self.assertAlmostEqual((plus-minus)/(2*step), gradient[index], delta=2e-7)

    def test_baseline_sensitivity_and_no_transfer(self):
        baseline = self.model.predict_baseline(1, 100, .5, self.p, self.w, p_policy="observed_512")
        equivalent = self.model.predict_sensitivity(1, 100, .5, self.p, self.w, p_policy="observed_512",
                                                    bridge_lambda=1, eta=0, bridge_model="exp_bridge")
        off = self.model.predict_sensitivity(1, 100, .5, self.p, self.w, p_policy="observed_512",
                                             bridge_lambda=0, eta=.4, bridge_model="exp_bridge")
        self.assertEqual(baseline["Loss"], equivalent["Loss"])
        self.assertEqual(off["Loss"], off["B7_loss"])
        self.assertAlmostEqual(off["gradients"]["p_ambient"]["arxiv"], 0)
        with self.assertRaisesRegex(ValueError, "bridge scale"):
            self.model.predict_sensitivity(.07, 100, .5, self.p, self.w, p_policy="observed_512",
                                           bridge_lambda=1, eta=1e300, bridge_model="exp_bridge")

    def test_q1_explicit_polynomial_recalculation(self):
        upstream = self.q1.upstream
        x = self.q1.point(self.p)
        k = 0
        direct = upstream.intercepts[k] + float(x @ upstream.main[k])
        direct += sum(upstream.gamma[k, j]*x[a]*x[b]
                      for j, (a, b) in enumerate(upstream.pairs))
        relative = direct/upstream.reference_loss[k]-1
        self.assertAlmostEqual(relative, self.q1.relative_effect(self.p, self.q1.targets[k]), places=12)

    def test_sensitivity_gradients(self):
        for form in ("exp_bridge", "linear_bridge"):
            result = self.model.predict_sensitivity(1, 100, .5, self.p, self.w, p_policy="observed_512",
                                                    bridge_lambda=.75, eta=.2, bridge_model=form)
            for name, index, step in (("N_B", 0, 1e-5), ("D_B", 1, 1e-3), ("Q_B", 2, 1e-5)):
                point = [1, 100, .5]
                point[index] += step
                plus = self.model.predict_sensitivity(*point, self.p, self.w, p_policy="observed_512",
                                                      bridge_lambda=.75, eta=.2, bridge_model=form)["Loss"]
                point[index] -= 2*step
                minus = self.model.predict_sensitivity(*point, self.p, self.w, p_policy="observed_512",
                                                       bridge_lambda=.75, eta=.2, bridge_model=form)["Loss"]
                self.assertAlmostEqual((plus-minus)/(2*step), result["gradients"][name], delta=2e-7)

    def test_policy_and_request_rejection(self):
        base = {"schema_version": VERSION, "mode": "baseline", "N_params_B": 1, "D_tokens_B": 100,
                "Q_score": .5, "p": self.p, "weights": self.w, "p_policy": "observed_512"}
        self.assertGreater(request(self.model, base)["Loss"], 0)
        with self.assertRaisesRegex(ValueError, "override"):
            request(self.model, {**base, "bridge_lambda": 1})
        with self.assertRaises(ValueError):
            request(self.model, {**base, "p": {}})
        with self.assertRaises(ValueError):
            request(self.model, {**base, "N_params_B": float("nan")})
        off_hull = {key: float(key == self.q1.domains[0]) for key in self.q1.domains}
        with self.assertRaises(ValueError):
            request(self.model, {**base, "p": off_hull, "p_policy": "convex_hull"})
        invalid_weights = {**self.w, "arxiv": -1}
        with self.assertRaises(ValueError):
            request(self.model, {**base, "weights": invalid_weights})

    def test_q1_relative_gradient_and_hessian(self):
        q1 = self.q1
        p = q1.p_dict(q1.recipes.mean(axis=0))
        grad = q1.gradient(p, self.w)
        hess = q1.hessian(self.w)
        direction = q1.recipes[10] - q1.recipes[20]
        for step in (1e-4, 1e-5):
            center = q1.point(p)
            plus = q1.weighted_effect(q1.p_dict(center+step*direction), self.w)
            minus = q1.weighted_effect(q1.p_dict(center-step*direction), self.w)
            self.assertAlmostEqual((plus-minus)/(2*step), float(grad @ direction), delta=1e-8)
            value = q1.weighted_effect(p, self.w)
            self.assertAlmostEqual((plus-2*value+minus)/(step*step),
                                   float(direction @ hess @ direction), delta=1e-6)


if __name__ == "__main__":
    unittest.main()
