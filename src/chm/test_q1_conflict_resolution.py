import unittest
import numpy as np
import pandas as pd

from q1_conflict_resolution import decide, score_and_decide
from q1_quality_analysis import QUALITY_FIELDS


class ConflictResolutionTests(unittest.TestCase):
    def test_decisions_preserve_quality_and_missing(self):
        self.assertEqual(decide(2, 3, 0, 2)[0], "RETAIN_FLAG_REVIEW")
        self.assertEqual(decide(-1, 0.5, 0, 2)[0], "LOW_PRIORITY")
        self.assertEqual(decide(1, np.nan, 0, 2)[0], "REVIEW_MISSING_D")
        self.assertEqual(decide(np.nan, 1, 0, 2)[0], "REVIEW_MISSING_Q")

    def test_all_missing_edges_are_not_zero(self):
        raw = pd.DataFrame({"_source_domain": ["book"], "_line": [1], "_id": ["fixture"]})
        for field in QUALITY_FIELDS:
            raw[field] = np.nan
        params = pd.DataFrame({"metric": QUALITY_FIELDS, "median": 0., "scale": 1.})
        orientation = pd.DataFrame({"metric": QUALITY_FIELDS, "orientation": 1})
        edges = pd.DataFrame({"metric_a": [QUALITY_FIELDS[0]], "metric_b": [QUALITY_FIELDS[1]], "rho": [-0.5]})
        result = score_and_decide(raw, params, orientation, {"Q_raw_mean": 0., "Q_raw_std": 1.}, edges, 0, 1)
        self.assertTrue(np.isnan(result.D_conflict.iloc[0]))
        self.assertEqual(result.n_usable_edges.iloc[0], 0)
        self.assertEqual(result.conflict_status.iloc[0], "REVIEW_MISSING_Q_AND_D")

    def test_missing_metric_rejected(self):
        with self.assertRaises(ValueError):
            score_and_decide(pd.DataFrame(), None, None, None, None, 0, 1)


if __name__ == "__main__":
    unittest.main()
