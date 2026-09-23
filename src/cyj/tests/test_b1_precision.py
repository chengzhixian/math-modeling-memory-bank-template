"""Regression checks for displayed-compute rounding diagnostics."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from diagnose_b1_precision import compute_identity  # noqa: E402


class ComputeIdentityTests(unittest.TestCase):
    def test_relative_warning_can_be_pure_display_rounding(self) -> None:
        rows = [
            {
                "run_id": "8",
                "N_params_B": "0.070542",
                "D_tokens_B": "0.134",
                "C_FLOPs_1e21": "0.0001",
            }
        ]
        result = compute_identity(rows)
        self.assertEqual(result["rows_matching_four_decimal_rounding"], 1)
        self.assertEqual(len(result["relative_warning_rows"]), 1)
        self.assertTrue(result["relative_warning_rows"][0]["matches_four_decimal_rounding"])

    def test_nonmatching_display_is_not_explained(self) -> None:
        rows = [
            {
                "run_id": "8",
                "N_params_B": "0.070542",
                "D_tokens_B": "0.134",
                "C_FLOPs_1e21": "0.0002",
            }
        ]
        result = compute_identity(rows)
        self.assertEqual(result["rows_matching_four_decimal_rounding"], 0)


if __name__ == "__main__":
    unittest.main()
