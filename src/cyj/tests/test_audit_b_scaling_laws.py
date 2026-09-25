from __future__ import annotations

import math
import sys
import tempfile
import unittest
from pathlib import Path


CYJ_SRC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CYJ_SRC))

import audit_b_scaling_laws as audit  # noqa: E402


class AuditHelpersTest(unittest.TestCase):
    def test_zero_d_is_detected(self) -> None:
        rows = [{"D_tokens_B": "0"}, {"D_tokens_B": "1.5"}]
        violations = audit.nonpositive_numeric_values(rows, ["D_tokens_B"])
        self.assertEqual(
            violations,
            [{"line": 2, "column": "D_tokens_B", "value": "0"}],
        )

    def test_missing_required_numeric_is_detected(self) -> None:
        rows = [{"N_params_B": ""}, {"N_params_B": "1.2"}]
        issues = audit.required_numeric_issues(rows, ["N_params_B"])
        self.assertEqual(issues["missing"], {"N_params_B": 1})
        self.assertEqual(issues["invalid_or_nonfinite"], {})

    def test_nonfinite_loss_is_detected(self) -> None:
        rows = [{"val_loss": "nan"}, {"val_loss": "inf"}, {"val_loss": "2.1"}]
        issues = audit.required_numeric_issues(rows, ["val_loss"])
        self.assertEqual(issues["missing"], {})
        self.assertEqual(issues["invalid_or_nonfinite"], {"val_loss": 2})

    def test_csv_row_width_mismatch_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.csv"
            path.write_text("a,b\n1\n2,3,4\n", encoding="utf-8", newline="\n")
            header, rows, raw_rows, mismatches = audit.read_csv(path)
        self.assertEqual(header, ["a", "b"])
        self.assertEqual(len(rows), 2)
        self.assertEqual(len(raw_rows), 2)
        self.assertEqual(
            mismatches,
            [
                {"line": 2, "expected": 2, "actual": 1},
                {"line": 3, "expected": 2, "actual": 3},
            ],
        )

    def test_compute_identity_outlier_is_not_hidden_by_median(self) -> None:
        stats = audit.compute_identity_stats([1.0, 1.0, 1.0, 1.2])
        self.assertEqual(stats["median_C_over_6ND"], 1.0)
        self.assertTrue(math.isclose(stats["max_absolute_deviation"], 0.2))
        self.assertGreater(stats["p95_absolute_deviation"], 0.0)
        self.assertGreater(stats["p99_absolute_deviation"], 0.0)

    def test_unknown_data_type_is_detected(self) -> None:
        rows = [
            {"data_type": "calibrated"},
            {"data_type": "unexpected"},
        ]
        violations = audit.enum_violations(
            rows, "data_type", audit.B8_ALLOWED_DATA_TYPES
        )
        self.assertEqual(violations, [{"line": 3, "value": "unexpected"}])

    def test_extrapolated_rows_are_never_fit_eligible(self) -> None:
        rows = [
            {"experiment_id": "fit-1", "data_type": "calibrated"},
            {"experiment_id": "test-1", "data_type": "extrapolated"},
        ]
        calibrated, extrapolated, overlap = audit.split_b8_rows(rows)
        self.assertEqual([row["experiment_id"] for row in calibrated], ["fit-1"])
        self.assertEqual(
            [row["experiment_id"] for row in extrapolated], ["test-1"]
        )
        self.assertEqual(overlap, set())

    def test_b8_cross_label_id_overlap_is_detected(self) -> None:
        rows = [
            {"experiment_id": "same", "data_type": "calibrated"},
            {"experiment_id": "same", "data_type": "extrapolated"},
        ]
        _, _, overlap = audit.split_b8_rows(rows)
        self.assertEqual(overlap, {"same"})

    def test_input_version_rejects_arbitrary_label(self) -> None:
        with self.assertRaisesRegex(ValueError, "full 40-hex"):
            audit.validate_input_version(
                "latest", audit.DEFAULT_MANIFEST, audit.DEFAULT_SOURCE_MANIFEST
            )


if __name__ == "__main__":
    unittest.main()
