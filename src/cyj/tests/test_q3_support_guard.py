"""Guard numerical optimizer roundoff without accepting invalid coordinates."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src/cyj"))
from q3_joint_sweeps import checked_supported_point


class Q3SupportGuardTests(unittest.TestCase):
    def test_roundoff_only_clamp(self):
        self.assertEqual(checked_supported_point((.07, 10., .1)), [.07, 10., .1])
        self.assertEqual(checked_supported_point((11.97 + 1e-14, 600. + 1e-12, 1. + 1e-14)),
                         [11.97, 600., 1.])

    def test_invalid_points_fail_fast(self):
        invalid = ((float("nan"), 10., .5), (float("inf"), 10., .5),
                   (.07, -10., .5), (.07, 600.1, .5), (.07, 10., 1.01),
                   (.07, 10., -.1), ("0.07", 10., .5), (True, 10., .5),
                   (.07, 10.), (.07, 10., .5, 1.))
        for point in invalid:
            with self.subTest(point=point), self.assertRaises(ValueError):
                checked_supported_point(point)


if __name__ == "__main__":
    unittest.main()
