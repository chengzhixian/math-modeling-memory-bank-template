from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parent))
from q3_quality_cost_geometry import g_second,quality_to_base_ratio,critical_N_equal_base,critical_Q_equal_base
class Q3QualityCostTests(unittest.TestCase):
    def test_curvature(self):
        self.assertGreater(g_second(.5,"exponential"),0);self.assertGreater(g_second(.5,"power"),0);self.assertLess(g_second(.5,"logarithmic"),0)
    def test_ratio_inverse_in_N(self):
        for f in ("exponential","power","logarithmic"):
            self.assertAlmostEqual(quality_to_base_ratio(1,1,.5,2048,f),10*quality_to_base_ratio(10,1,.5,2048,f))
    def test_critical_N_identity(self):
        for f in ("exponential","power","logarithmic"):
            n=critical_N_equal_base(1,.5,8192,f);self.assertAlmostEqual(quality_to_base_ratio(n,1,.5,8192,f),1)
    def test_inverse_Q(self):
        for f in ("exponential","power","logarithmic"):
            q=critical_Q_equal_base(.1,.5,2048,f)
            if q is not None:self.assertAlmostEqual(quality_to_base_ratio(.1,q,.5,2048,f),1,places=10)
if __name__=="__main__":unittest.main()
