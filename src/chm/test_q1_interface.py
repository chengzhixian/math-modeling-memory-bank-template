from pathlib import Path
import unittest

from q1_interface import Q1Interface, build_manifest


ROOT = Path(__file__).resolve().parents[2]


class Q1InterfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.q1 = Q1Interface(ROOT)

    def test_manifest_matches_current_files(self):
        built = build_manifest(ROOT)
        self.assertEqual(built["schema_version"], self.q1.manifest["schema_version"])
        self.assertEqual(built["hash_mode"], "sha256_utf8_lf_normalized")
        self.assertEqual(built["files"], self.q1.manifest["files"])
        self.assertEqual(
            built["scale_transfer_status"],
            "not_identified_from_attachment_A",
        )

    def test_manifest_is_cross_platform_text_hash(self):
        self.assertEqual(self.q1.manifest["schema_version"], "chm.q1.v1.3")
        self.assertEqual(self.q1.manifest["hash_mode"], "sha256_utf8_lf_normalized")
        self.assertNotIn("scale", self.q1.manifest["files"])

    def test_quality_mapping_preserves_unknown(self):
        self.assertEqual(
            self.q1.mapped_quality("arxiv")["quality"]["coordinate"],
            "A_composite_quality_proxy_z",
        )
        self.assertFalse(
            self.q1.quality("arxiv")["direct_B_predictor_input_allowed"]
        )
        self.assertEqual(
            self.q1.mapped_quality("freelaw")["mapping_type"],
            "inferred",
        )
        self.assertIsNone(self.q1.mapped_quality("freelaw")["quality"])

    def test_relative_effect_is_zero_at_reference(self):
        for target in self.q1.coefficients:
            result = self.q1.relative_effect(self.q1.reference, target)
            self.assertAlmostEqual(result["delta_target_loss_1m"], 0)
            self.assertEqual(
                result["cross_scale_transfer"],
                "not_identified_from_attachment_A",
            )

    def test_mixture_rejects_invalid_weights(self):
        p = self.q1.reference.copy()
        for bad in (
            {"arxiv": 1.0},
            {**p, "extra": 0.0},
            {**p, "arxiv": -1.0},
            {**p, "arxiv": p["arxiv"] + 0.1},
        ):
            with self.assertRaises(ValueError):
                self.q1.relative_effect(bad, "pile_cc")

    def test_example_is_unscaled_1m_contrast(self):
        p = self.q1.reference.copy()
        p["arxiv"] += 0.01
        p["freelaw"] -= 0.01
        result = self.q1.relative_effect(p, "pile_cc")
        self.assertAlmostEqual(
            result["delta_target_loss_1m"],
            0.002371904510480527,
        )
        self.assertEqual(
            result["loss_coordinate"],
            "A4_A5_1M_target_cross_entropy_contrast",
        )
        self.assertEqual(result["bridge_to_B1_val_loss"], "unidentified")
        self.assertFalse(result["direct_B1_addition_allowed"])

    def test_effect_vector_and_interaction_matrix(self):
        vector = self.q1.effect_vector(self.q1.reference)
        self.assertEqual(len(vector["effects"]), 13)
        for value in vector["effects"].values():
            self.assertAlmostEqual(value, 0.0, places=12)

        matrix = self.q1.interaction_matrix()
        self.assertEqual(len(matrix["targets"]), 13)
        self.assertEqual(len(matrix["domains"]), 17)
        self.assertEqual(len(matrix["matrix"]), 13)
        self.assertTrue(all(len(row) == 17 for row in matrix["matrix"]))

    def test_ranking_validation_is_explicit(self):
        result = self.q1.ranking_validation("pile_cc")
        self.assertAlmostEqual(result["test_1m_spearman"], 0.9007345788509955)
        self.assertAlmostEqual(result["test_60m_spearman"], 0.8918996051728083)
        self.assertAlmostEqual(result["test_1B_spearman"], 0.8875915750915748)
        self.assertEqual(
            result["interpretation"],
            "rank_transfer_evidence_not_absolute_scale_calibration",
        )


if __name__ == "__main__":
    unittest.main()
