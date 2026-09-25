"""Small independent fixtures for trend and overlap diagnostics."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from diagnose_b_quality import coordinate_map, overlap, trends


def row(q, loss, n=1):
    return dict(N_params_B=n, D_tokens_B=10, Q_score=q, val_loss=loss)


class QualityAuditTests(unittest.TestCase):
    def test_conditional_directions_not_pooled(self):
        rows = [row(.1, 1), row(.2, 2), row(.3, 2), row(.1, 100, 2), row(.2, 99, 2)]
        result = trends(rows, "Q_score")
        self.assertEqual(result["adjacent_pairs"], dict(increasing=1, decreasing=1, tied=1))
        self.assertEqual(result["group_types"]["mixed"], 1)
        self.assertEqual(result["group_types"]["decreasing"], 1)

    def test_overlap_and_duplicate_rejection(self):
        result = overlap([row(.1, 1), row(.2, 2)], [row(.1, 1), row(.2, 3), row(.3, 4)])
        self.assertEqual(result["shared_coordinates"], 2)
        self.assertEqual(result["identical_loss"], 1)
        self.assertEqual(result["right_minus_left_max"], 1)
        with self.assertRaises(ValueError):
            coordinate_map([row(.1, 1), row(.1, 2)])

    def test_singleton_is_not_evidence_of_monotonicity(self):
        result = trends([row(.1, 1)], "Q_score")
        self.assertEqual(result["group_types"]["singleton"], 1)
        self.assertIsNone(result["slope_min"])
