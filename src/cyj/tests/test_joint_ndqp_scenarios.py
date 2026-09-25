"""Numerical and provenance checks for an explicitly conditional bridge."""
import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from joint_ndqp_scenarios import ConditionalNDQP


class JointScenarioTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = ConditionalNDQP()
        cls.p = cls.model.a["reference"].copy()
        cls.weights = {"arxiv": 1.0}

    def value(self, n=1.0, d=100.0, q=.5, p=None, lam=.4, eta=.25):
        return self.model.evaluate_ndqp_scenario(n, d, q, p=self.p if p is None else p,
            weights=self.weights, bridge_lambda=lam, eta=eta)

    def test_reference_and_zero_bridge_exact_degeneracy(self):
        base = self.model.evaluate_ndq(1, 100, .5)
        self.assertEqual(self.value()["loss"], base["loss"])
        changed = self.p.copy()
        changed["arxiv"] += .01
        changed["freelaw"] -= .01
        self.assertEqual(self.value(p=changed, lam=0)["loss"], base["loss"])
        self.assertEqual(self.value(q=1)["loss"], self.model.evaluate_ndq(1, 100, 1)["loss"])

    def test_gradient_finite_difference_and_transfer(self):
        p = self.p.copy()
        p["arxiv"] += .01
        p["freelaw"] -= .01
        point = self.value(p=p)
        for axis, step in (("N", 1e-5), ("D", 1e-3), ("Q_B", 1e-5)):
            args = {"n": 1.0, "d": 100.0, "q": .5, "p": p}
            key = {"N": "n", "D": "d", "Q_B": "q"}[axis]
            args[key] += step
            plus = self.value(**args)["loss"]
            args[key] -= 2 * step
            minus = self.value(**args)["loss"]
            self.assertAlmostEqual((plus - minus) / (2 * step), point["gradient"][axis], delta=2e-7)
        h = 1e-5
        shifted = p.copy()
        shifted["arxiv"] += h
        shifted["freelaw"] -= h
        numeric = (self.value(p=shifted)["loss"] - point["loss"]) / h
        analytic = self.model.transfer_derivative(point, "freelaw", "arxiv")
        self.assertAlmostEqual(numeric, analytic, delta=2e-7)

    def test_invalid_inputs_rejected(self):
        cases = [dict(n=.001), dict(d=601), dict(q=float("nan")), dict(lam=float("inf")),
                 dict(eta=float("nan"))]
        for case in cases:
            with self.subTest(case=case), self.assertRaises(ValueError):
                self.value(**case)
        p = self.p.copy()
        p["arxiv"] += .2
        with self.assertRaises(ValueError):
            self.value(p=p)
        with self.assertRaises(ValueError):
            self.model.evaluate_ndqp_scenario(1, 100, .5, p=self.p, weights={"arxiv": .8},
                                               bridge_lambda=.4, eta=.25)

    def test_provenance_and_nonidentification(self):
        status = self.model.calibration_status()
        self.assertFalse(status["ready_for_Q3"])
        self.assertIn("unidentified", status["scenario_bridge"])
        self.assertEqual(self.model.assumptions()["producer_schema"], "chm.q1.v1.3")
        self.assertTrue(all(x > 0 and math.isfinite(x) for x in self.model.a["reference_loss"].values()))

    def test_finite_equal_loss_support(self):
        args = {"baseline": {"N": 1.0, "D": 100.0, "Q_B": .5}, "axis": "N",
                "changed_axis": "Q_B", "p": self.p, "weights": self.weights,
                "bridge_lambda": .4, "eta": .25}
        same = self.model.equal_loss_root(**args, changed_value=.5)
        self.assertEqual(same["status"], "supported")
        self.assertAlmostEqual(same["value"], 1, places=9)
        args["baseline"] = {"N": .07, "D": 100.0, "Q_B": .5}
        self.assertEqual(self.model.equal_loss_root(**args, changed_value=1)["status"],
                         "no_equal_loss_root_in_support")


if __name__ == "__main__":
    unittest.main()
