"""Check fixed-family evidence identities and finite empirical intervals."""
import json
import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src/cyj"))
from b7_formal_model import OUTPUT as MODEL_OUTPUT
from build_b7_frozen_uncertainty import OUTPUT as UNCERTAINTY_OUTPUT, interval
from validate_b7_frozen_model import OUTPUT as VALIDATION_OUTPUT


class FrozenEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = json.loads(MODEL_OUTPUT.read_text(encoding="utf-8"))["parameters"]
        cls.validation = json.loads(VALIDATION_OUTPUT.read_text(encoding="utf-8"))
        cls.uncertainty = json.loads(UNCERTAINTY_OUTPUT.read_text(encoding="utf-8"))

    def test_fixed_family_grouping_and_provenance(self):
        data = self.validation
        self.assertEqual(len(data["folds"]), 24)
        self.assertEqual(len(data["oof_residuals"]), 1350)
        self.assertFalse(data["ready_for_Q3_candidate"])
        self.assertEqual(data["source_sha256"], self.uncertainty["source_sha256"])
        self.assertTrue(all(data["primary_better_than_constant_G_all_axes"].values()))
        for axis in ("N_params_B", "D_tokens_B", "Q_score"):
            selected = [r for r in data["oof_residuals"] if r["axis"] == axis]
            self.assertEqual(len(selected), 450)
            self.assertEqual(len({r["source_line"] for r in selected}), 450)
            self.assertTrue(all(math.isfinite(r["residual_observed_minus_predicted"])
                                for r in selected))

    def test_empirical_interval_scope_and_order(self):
        data = self.uncertainty
        self.assertEqual(data["accepted_bootstrap"], 500)
        self.assertFalse(data["ready_for_Q3"])
        self.assertIsNone(data["cross_source_uncertainty"])
        for point in ((.7, 150., .5), (.07, 10., .1), (11.97, 600., 1.)):
            result = interval(*point, self.model, data)
            lo, hi = result["empirical_prediction_percentile_95"]
            self.assertTrue(all(math.isfinite(v) for v in (lo, hi, result["central_estimate"])))
            self.assertLess(lo, hi)
            self.assertFalse(result["calibrated_coverage_claim"])


if __name__ == "__main__":
    unittest.main()
