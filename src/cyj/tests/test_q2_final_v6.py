"""Independent invariants and process regressions for the conditional v6 API."""
import hashlib
import json
import math
import os
import subprocess
import sys
import unittest
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "src/cyj"))
from q2_final_core import Q2Final


class FinalQ2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = Q2Final()
        cls.weights = cls.model.weight_policy("equal_13")

    def test_q1_derived_recipe_support_and_tamper_detection(self):
        self.assertEqual(self.model.matrix.shape, (512, 17))
        self.assertTrue(self.model.hull(self.model.reference)["inside"])
        self.assertTrue(np.allclose(self.model.matrix.sum(axis=1), 1, atol=1e-12))
        for name, digest in self.model.manifest["files_sha256"].items():
            self.assertEqual(hashlib.sha256((self.model.bundle / name).read_bytes()).hexdigest(), digest)

    def test_linear_lp_equals_independent_vertex_enumeration(self):
        relative = self.model.relative_recipe_effects @ np.array([self.weights[k] for k in self.model.targets])
        index = int(np.argmin(relative))
        result = self.model.optimize("convex_hull")
        self.assertAlmostEqual(result["weighted_relative_A_effect"], float(relative[index]), places=11)
        self.assertEqual(result["recipe_weights"][0]["index"], self.model.indices[index])
        self.assertAlmostEqual(result["min_factor_over_B7_N"], result["factor"], places=12)

    def test_quality_lp_creates_valid_new_feasible_vertex(self):
        unrestricted = self.model.optimize("convex_hull")
        constrained = self.model.optimize("quality_direct")
        self.assertGreater(constrained["conditional_loss"], unrestricted["conditional_loss"])
        self.assertGreater(len(constrained["recipe_weights"]), 1)
        self.assertTrue(self.model.hull(constrained["p"])["inside"])
        req = constrained["quality_constraint"]
        qa = constrained["qa_direct"]
        self.assertGreaterEqual(qa["covered_mass"] + 1e-8, req["reference_covered_mass"])
        self.assertGreaterEqual(qa["mean_Q_A_on_mapped"] + 1e-8, req["reference_mean_Q_A"])
        with self.assertRaisesRegex(ValueError, "quality"):
            self.model.evaluate(1, 100, .5, unrestricted["p"], self.weights, 1, 0, p_policy="quality_direct")

    def test_degeneracy_and_finite_differences(self):
        p = self.model.optimize("convex_hull")["p"]
        zero = self.model.evaluate(1, 100, .5, p, self.weights, 0, 0)
        base = self.model.v5.evaluate_ndq(1, 100, .5)
        self.assertEqual(zero["factor"], 1)
        self.assertAlmostEqual(zero["loss"], base["loss"], places=12)
        tie = self.model.optimize("convex_hull", lam=0)
        self.assertEqual(tie["status"], "all_feasible_p_tied")
        self.assertFalse(tie["unique_optimum"])
        got = self.model.evaluate(1, 100, .5, p, self.weights, 1, 0)
        for axis, index, step in (("N", 0, 1e-5), ("D", 1, 1e-3), ("Q_B", 2, 1e-5)):
            x1, x2 = [1.0, 100.0, .5], [1.0, 100.0, .5]
            x1[index] -= step
            x2[index] += step
            finite = (self.model.v5.evaluate_ndqp_scenario(*x2, p=p, weights=self.weights, bridge_lambda=1, eta=0)["loss"] -
                      self.model.v5.evaluate_ndqp_scenario(*x1, p=p, weights=self.weights, bridge_lambda=1, eta=0)["loss"]) / (2 * step)
            self.assertAlmostEqual(got["gradient"][axis], finite, delta=1e-7)

    def test_strict_domain_and_model_rejection(self):
        p = self.model.optimize("convex_hull")["p"]
        bad = {k: float(k == "arxiv") for k in p}
        with self.assertRaisesRegex(ValueError, "outside"):
            self.model.evaluate(1, 100, .5, bad, self.weights, 1, 0)
        with self.assertRaisesRegex(ValueError, "support"):
            self.model.evaluate(1000, 100, .5, p, self.weights, 1, 0)
        with self.assertRaisesRegex(ValueError, "coefficients unavailable"):
            self.model.evaluate(1, 100, .5, p, self.weights, 1, 0, model_variant="interaction_sensitivity")

    def test_process_fixtures_and_runtime_path_audit(self):
        folder = ROOT / "interfaces/cyj/fixtures_v6"
        observed_paths = []
        def audit(event, args):
            if event == "open" and args:
                observed_paths.append(str(args[0]).replace("\\", "/"))
        sys.addaudithook(audit)
        fresh = Q2Final()
        self.assertEqual(len(fresh.matrix), 512)
        for request in sorted(folder.glob("*.request.json")):
            expected = json.loads(request.with_name(request.name.replace(".request.", ".expected.")).read_text())
            completed = subprocess.run([sys.executable, "-B", str(ROOT / "src/cyj/ndqp_scenarios_v6.py"),
                "--request", str(request)], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(completed.returncode, expected["exit_code"], completed.stderr)
            if completed.returncode == 0:
                self.assertEqual(json.loads(completed.stdout), expected["output"])
            else:
                self.assertEqual(json.loads(completed.stderr)["error"], expected["error"])
        self.model.evaluate(1, 100, .5, self.model.p_dict(self.model.reference), self.weights, 0, 0)
        forbidden = "data/raw/real_attachments/" + "A_data_value"
        self.assertFalse(any(forbidden in path for path in observed_paths))
        self.assertTrue(any("q1_q2_bundle_v1" in path for path in observed_paths))
        for path in (ROOT / "src/cyj").rglob("*.py"):
            self.assertNotIn(forbidden, path.read_text(encoding="utf-8"))

    def test_artifact_manifest_and_validation_roles(self):
        output = ROOT / "outputs/cyj/q2_final"
        manifest = json.loads((output / "manifest.json").read_text())
        for name, digest in manifest["files_sha256"].items():
            self.assertEqual(hashlib.sha256((output / name).read_bytes()).hexdigest(), digest)
        for name, digest in manifest["figures_sha256"].items():
            path = ROOT / "figures/cyj/q2_final" / name
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), digest)
        self.assertEqual(len(manifest["figures_sha256"]), 5)  # four PNG and figure manifest
        summary = (output / "validation_summary.csv").read_text()
        self.assertIn("estimated_stress_only", summary)
        self.assertIn("within_family_source_descriptive", summary)


if __name__ == "__main__":
    unittest.main()
