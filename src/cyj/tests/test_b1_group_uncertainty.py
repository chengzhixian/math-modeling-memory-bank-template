"""Unit checks for B1 whole-trajectory resampling."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from diagnose_b1_group_uncertainty import quantiles, resample_groups  # noqa: E402


class BootstrapHelperTests(unittest.TestCase):
    def test_duplicate_group_draws_are_retained_with_distinct_weight_ids(self) -> None:
        rows = {"a": [{"id": "a1"}, {"id": "a2"}], "b": [{"id": "b1"}]}
        sampled, labels = resample_groups(rows, ["a", "a", "b"])
        self.assertEqual([row["id"] for row in sampled], ["a1", "a2", "a1", "a2", "b1"])
        self.assertEqual(labels, ["draw_0", "draw_0", "draw_1", "draw_1", "draw_2"])

    def test_quantiles_are_ordered(self) -> None:
        result = quantiles([1.0, 2.0, 3.0, 4.0])
        self.assertLessEqual(result["p025"], result["median"])
        self.assertLessEqual(result["median"], result["p975"])


if __name__ == "__main__":
    unittest.main()
