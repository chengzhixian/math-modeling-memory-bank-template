"""Fixture replay keeps identity fields exact while tolerating roundoff."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src/cyj"))

from verify_v8_fixtures import matches_expected


class FixtureComparisonTests(unittest.TestCase):
    def test_floating_roundoff_in_nested_result_is_accepted(self):
        expected = {"version": "cyj.ndqp.scenario.v8", "status": "ok",
                    "sha256": "abc123", "values": [2.0, {"Loss": 2.344348}]}
        actual = {"version": "cyj.ndqp.scenario.v8", "status": "ok",
                  "sha256": "abc123", "values": [2.0 + 2.22e-16,
                                                  {"Loss": 2.344348 + 2.22e-16}]}
        self.assertTrue(matches_expected(expected, actual))

    def test_identity_and_material_numeric_changes_are_rejected(self):
        expected = {"version": "v8", "sha256": "abc", "Loss": 2.0, "valid": True}
        for actual in ({**expected, "version": "v9"},
                       {**expected, "sha256": "abd"},
                       {**expected, "Loss": 2.000001},
                       {**expected, "valid": 1},
                       {**expected, "extra": "unexpected"}):
            with self.subTest(actual=actual):
                self.assertFalse(matches_expected(expected, actual))


if __name__ == "__main__":
    unittest.main()
