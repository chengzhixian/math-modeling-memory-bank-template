from pathlib import Path
import sys, unittest
sys.path.insert(0, str(Path(__file__).resolve().parent))
from q3_regime_scan import regime_solution, regime_thresholds

class Q3RegimeTests(unittest.TestCase):
    def test_threshold_order(self):
        for c in (2048,8192,131072):
            v=list(regime_thresholds(c).values())
            self.assertEqual(v,sorted(v))
    def test_reference_phases(self):
        self.assertEqual(regime_solution(1e19,2048)["phase"],"interior")
        self.assertEqual(regime_solution(1e22,2048)["phase"],"D_max_bound")
        self.assertEqual(regime_solution(1e22,8192)["phase"],"interior")
        self.assertEqual(regime_solution(1e24,131072)["phase"],"support_corner")
if __name__=="__main__":
    unittest.main()
