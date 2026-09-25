"""Producer example, fail-closed boundaries and numerical derivative checks."""
import hashlib
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from q3_interface import Predictor, load_chm, producer_bytes
from q3_costs import costs, constraint_residuals

CHM_COMMIT = "7c14a0c894072048d09f04bd03653be1301f7257"


class Q3InterfaceTests(unittest.TestCase):
    def test_upstream_example_and_mapping(self):
        q1, identities = load_chm(CHM_COMMIT)
        p = q1.reference.copy()
        self.assertEqual(q1.relative_effect(p, "pile_cc")["delta_target_loss"], 0)
        p["arxiv"] += 0.01
        p["freelaw"] -= 0.01
        value = q1.relative_effect(p, "pile_cc", 60e6)["delta_target_loss"]
        self.assertAlmostEqual(value, 0.001309803924525102, places=14)
        self.assertIsNone(q1.mapped_quality("freelaw")["quality"])
        recovered = [r for r in identities.values() if r.get("materialization") == "LF_to_CRLF_exact_published_SHA"]
        self.assertEqual(len(recovered), 3)

    def test_newline_recovery_does_not_mask_data_changes(self):
        original = b"a,b\r\n1,2\r\n"
        actual, mode = producer_bytes(b"a,b\n1,2\n", hashlib.sha256(original).hexdigest())
        self.assertEqual(actual, original)
        self.assertIn("CRLF", mode)
        with self.assertRaises(ValueError):
            producer_bytes(b"a,b\n1,3\n", hashlib.sha256(original).hexdigest())

    def test_predictor_baseline_and_fail_closed_inputs(self):
        model = Predictor()
        request = dict(N_params_B=0.070542, D_tokens_B=0.134, mode="diagnostic")
        out = model.predict(**request)
        self.assertAlmostEqual(out["loss_value"], 4.738637013477364, places=12)
        self.assertFalse(out["ready_for_Q3"])
        for changes in ({"mode": "formal"}, {"Q_score": 0.5}, {"N_params_B": 0},
                        {"N_params_B": float("nan")}, {"N_params_B": 20}):
            with self.assertRaises(ValueError):
                model.predict(**(request | changes))

    def test_mixture_gradient_and_no_silent_normalization(self):
        model = Predictor()
        p = model.q1.reference.copy()
        p["arxiv"] += 0.01
        p["freelaw"] -= 0.01
        request = dict(N_params_B=1.0, D_tokens_B=100, mode="scenario", p=p,
                       target="pile_cc", lambda_loss=0.2, eta=0.14503317, allow_extrapolation=True)
        out = model.predict(**request)
        for key in ("N_params_B", "D_tokens_B"):
            eps = request[key] * 1e-5
            numerical = (model.predict(**(request | {key: request[key] + eps}))["loss_value"]
                         - model.predict(**(request | {key: request[key] - eps}))["loss_value"]) / (2 * eps)
            self.assertAlmostEqual(numerical, out["gradient"][key], delta=1e-8)
        for changes in ({"p": {k: 2*v for k, v in p.items()}}, {"lambda_loss": None},
                        {"target": "unknown"}, {"p": {k: v for k, v in p.items() if k != "arxiv"}}):
            with self.assertRaises(ValueError):
                model.predict(**(request | changes))

    def test_cost_units_and_quality_kink(self):
        request = dict(N_params_B=1, D_tokens_B=100, Q_score=0.5, Q0=0.5,
                       L_ctx=2048, quality_family="exponential", budget_FLOPs=1e22)
        result = costs(**request)
        self.assertEqual(result["training"], 6e20)
        self.assertEqual(result["quality"], 0)
        self.assertEqual(result["attention"], 4.096e19)
        self.assertEqual(result["context_critical_tokens"], 30000)
        self.assertEqual(result["gradient"]["Q_score_left"], 0)
        self.assertGreater(result["gradient"]["Q_score_right"], 0)
        for family in ("exponential", "power", "logarithmic"):
            r = request | {"quality_family": family, "Q_score": 0.7}
            numerical = (costs(**(r | {"Q_score": 0.700001}))["total"] - costs(**(r | {"Q_score": 0.699999}))["total"]) / 2e-6
            self.assertAlmostEqual(numerical / costs(**r)["gradient"]["Q_score_right"], 1, places=7)
        with self.assertRaises(ValueError):
            costs(**(request | {"L_ctx": 30000}))
        q1, _ = load_chm(CHM_COMMIT)
        residual = constraint_residuals(q1.reference, q1.reference, result)
        self.assertAlmostEqual(residual["simplex_equality"], 0)


if __name__ == "__main__":
    unittest.main()
