"""Check v3 conditional interface and recorded CHM consumer diagnostic."""
import hashlib
import json
import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src/cyj"))
from chm_adapter_v3 import CHMAdapterV3


class V3CandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = CHMAdapterV3(mode="conditional_diagnostic")

    def test_gate_and_policy(self):
        metadata = self.model.capabilities()
        self.assertFalse(metadata["ready_for_Q3"])
        self.assertEqual(metadata["p_policy"]["mode"], "sensitivity_only")
        self.assertFalse(metadata["p_policy"]["B_loss_addition_allowed"])
        self.assertEqual(self.model.bounds[1][0], 10)
        with self.assertRaises(ValueError):
            CHMAdapterV3(mode="formal")

    def test_p_does_not_change_B_loss_and_invalid_inputs(self):
        reference = self.model.capabilities()["reference_p"]
        changed = dict(reference)
        changed["arxiv"] += .01
        changed["freelaw"] -= .01
        common = dict(N_params_B=.7, D_tokens_B=150., Q_score=.5, Q0=.5,
                      context_tokens=2048, quality_family="exponential", budget_FLOPs=1e22)
        first = self.model.evaluate(**common, p=reference)
        second = self.model.evaluate(**common, p=changed)
        self.assertEqual(first["prediction"], second["prediction"])
        self.assertNotEqual(first["p_sensitivity"], second["p_sensitivity"])
        self.assertLess(first["prediction"]["uncertainty"]["empirical_prediction_percentile_95"][0],
                        first["prediction"]["uncertainty"]["empirical_prediction_percentile_95"][1])
        for bad in (.134, 601., float("nan"), "150"):
            with self.assertRaises(ValueError):
                self.model.value_grad(.7, bad, .5)
        with self.assertRaises(ValueError):
            self.model.evaluate(**{**common, "budget_FLOPs": -1})

    def test_manifest_and_exact_solver_record(self):
        manifest = json.loads((ROOT / "outputs/cyj/interfaces/chm_v3_manifest.json").read_text(encoding="utf-8"))
        for path, digest in manifest["files_sha256_utf8_lf"].items():
            self.assertEqual(hashlib.sha256((ROOT / path).read_bytes().replace(b"\r\n", b"\n")).hexdigest(), digest)
        record = json.loads((ROOT / "outputs/cyj/interfaces/chm_solver_consumption_b7_candidate.json").read_text(encoding="utf-8"))
        self.assertEqual(record["chm_exact_commit"], "92e0592000cba58fca355a881dc59caadbd446b2")
        self.assertEqual(len(record["results"]), 27)
        solved = [r for r in record["results"] if r["status"] == "converged_feasible"]
        self.assertEqual(len(solved), 24)
        self.assertTrue(all(r["solution"]["kkt_check_pass"] and r["solution"]["primal_feasible"]
                            and math.isfinite(r["solution"]["kkt_relative_violation"]) for r in solved))


if __name__ == "__main__":
    unittest.main()
