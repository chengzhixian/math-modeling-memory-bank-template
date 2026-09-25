"""Behavior checks for the pinned CYJ v7 Q3 dependency."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from q3_v7_inputs import (  # noqa: E402
    EXPECTED_Q1_SHA,
    load_release,
    verify_release,
)


ROOT = Path(__file__).resolve().parents[2]
CYJ_ROOT = ROOT / ".upstream/cyj-v7"


class V7InputTests(unittest.TestCase):
    def test_rejects_wrong_release(self):
        with self.assertRaisesRegex(ValueError, "release SHA"):
            verify_release(ROOT, expected_release="0" * 40)

    def test_rejects_wrong_q1_manifest(self):
        with self.assertRaisesRegex(ValueError, "Q1 manifest"):
            verify_release(CYJ_ROOT, expected_q1="0" * 64)

    def test_official_pins_match(self):
        release = load_release(CYJ_ROOT)
        self.assertEqual(release.q1.manifest_sha256, EXPECTED_Q1_SHA)
        self.assertEqual(len(release.q1.recipes), 512)


if __name__ == "__main__":
    unittest.main()
