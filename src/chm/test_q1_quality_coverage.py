import unittest

from q1_quality_coverage import coverage


class QualityCoverageTests(unittest.TestCase):
    def setUp(self):
        self.rows = [
            {"mixture_domain": "arxiv", "mapping_type": "direct", "Q_A_proxy": -0.5},
            {"mixture_domain": "wikipedia_en", "mapping_type": "near_direct", "Q_A_proxy": 0.3},
            {"mixture_domain": "dm_mathematics", "mapping_type": "inferred", "Q_A_proxy": None},
        ]

    def test_negative_q_is_valid(self):
        result = coverage({"arxiv": 1, "wikipedia_en": 0, "dm_mathematics": 0}, self.rows)
        self.assertEqual(result["global_Q_A"], -0.5)
        self.assertEqual(result["B7_Q_score"], "NOT_IDENTIFIED")

    def test_unknown_share_never_becomes_zero_quality(self):
        result = coverage({"arxiv": 0.1, "wikipedia_en": 0, "dm_mathematics": 0.9}, self.rows)
        self.assertEqual(result["global_quality_status"], "PARTIAL_UNKNOWN")
        self.assertIsNone(result["global_Q_A"])
        self.assertAlmostEqual(result["unknown_share"], 0.9)

    def test_invalid_mixture_rejected(self):
        for mix in [{"arxiv": 1},
                    {"arxiv": 0.5, "wikipedia_en": 0, "dm_mathematics": 0},
                    {"arxiv": -0.1, "wikipedia_en": 0.1, "dm_mathematics": 1}]:
            with self.assertRaises(ValueError):
                coverage(mix, self.rows)


if __name__ == "__main__":
    unittest.main()
