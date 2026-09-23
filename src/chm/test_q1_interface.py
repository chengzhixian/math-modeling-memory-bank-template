from pathlib import Path
import unittest

from q1_interface import Q1Interface, build_manifest


ROOT = Path(__file__).resolve().parents[2]


class Q1InterfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.q1 = Q1Interface(ROOT)

    def test_manifest_matches_current_files(self):
        self.assertEqual(build_manifest(ROOT), self.q1.manifest)

    def test_quality_mapping_preserves_unknown(self):
        self.assertEqual(self.q1.mapped_quality("arxiv")["quality"]["coordinate"], "A_native_Q_z")
        self.assertFalse(self.q1.quality("arxiv")["direct_B_predictor_input_allowed"])
        self.assertEqual(self.q1.mapped_quality("freelaw")["mapping_type"], "inferred")
        self.assertIsNone(self.q1.mapped_quality("freelaw")["quality"])

    def test_relative_effect_is_zero_at_reference(self):
        for target in self.q1.coefficients:
            self.assertAlmostEqual(self.q1.relative_effect(self.q1.reference, target)["delta_target_loss"], 0)

    def test_mixture_rejects_invalid_weights(self):
        p = self.q1.reference.copy()
        for bad in ({"arxiv": 1.0}, {**p, "extra": 0.0}, {**p, "arxiv": -1.0},
                    {**p, "arxiv": p["arxiv"] + 0.1}):
            with self.assertRaises(ValueError):
                self.q1.relative_effect(bad, "pile_cc")

    def test_scale_is_explicit(self):
        p = self.q1.reference.copy()
        p["arxiv"] += 0.01
        p["freelaw"] -= 0.01
        at_1m = self.q1.relative_effect(p, "pile_cc", n_params=1e6, eta=0)
        at_60m = self.q1.relative_effect(p, "pile_cc", n_params=60e6, eta=0)
        self.assertAlmostEqual(at_1m["delta_target_loss"], at_60m["delta_target_loss"])
        self.assertEqual(at_60m["bridge_to_B1_val_loss"], "unidentified")
        self.assertFalse(at_60m["direct_B1_addition_allowed"])
        self.assertEqual(at_60m["evidence_status"], "conditional_eta_scale_scenario")
        self.assertEqual(self.q1.relative_effect(p, "pile_cc", n_params=2e6)["scale_status"],
                         "extrapolated_model_scale")


if __name__ == "__main__":
    unittest.main()
