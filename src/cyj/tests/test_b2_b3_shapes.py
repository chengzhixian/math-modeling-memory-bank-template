"""Unit checks for trajectory shape summaries."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from diagnose_b2_b3_shapes import describe_curve  # noqa: E402


class ShapeTests(unittest.TestCase):
    def test_counts_increases_and_decreases_after_sorting(self) -> None:
        rows = [
            {"N_params_B": "1", "D_tokens_B": "3", "step": "3", "val_loss": "2.5"},
            {"N_params_B": "1", "D_tokens_B": "1", "step": "1", "val_loss": "3"},
            {"N_params_B": "1", "D_tokens_B": "2", "step": "2", "val_loss": "2"},
        ]
        curve = describe_curve(rows)
        self.assertEqual(curve["adjacent_loss_increases"], 1)
        self.assertEqual(curve["adjacent_loss_decreases"], 1)
        self.assertEqual(curve["val_loss_last_minus_first"], -0.5)

    def test_reports_duplicate_training_tokens(self) -> None:
        rows = [
            {"N_params_B": "1", "D_tokens_B": "1", "steps": "1", "val_loss": "3"},
            {"N_params_B": "1", "D_tokens_B": "1", "steps": "2", "val_loss": "2"},
        ]
        self.assertEqual(describe_curve(rows)["adjacent_equal_D_pairs"], 1)

    def test_rejects_mixed_model_sizes(self) -> None:
        rows = [
            {"N_params_B": "1", "D_tokens_B": "1", "step": "1", "val_loss": "3"},
            {"N_params_B": "2", "D_tokens_B": "2", "step": "2", "val_loss": "2"},
        ]
        with self.assertRaises(ValueError):
            describe_curve(rows)


if __name__ == "__main__":
    unittest.main()
