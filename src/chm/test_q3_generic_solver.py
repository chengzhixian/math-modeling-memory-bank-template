from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parent))
from q3_generic_solver import SyntheticLinearQualityLoss,solve_generic,detect_transitions,Support,enrich_kkt

class GenericSolverTests(unittest.TestCase):
    def test_synthetic_solver_feasible(self):
        sol,trials=solve_generic(SyntheticLinearQualityLoss(.2),budget=1e22,context_tokens=8192,Q0=.5,family="power",starts=20,seed=123)
        self.assertLessEqual(sol["budget_utilization"],1.00000001)
        self.assertGreaterEqual(sol["Q"],.5);self.assertLessEqual(sol["Q"],1)
        self.assertGreaterEqual(sum(t["feasible"] for t in trials),15)
    def test_more_budget_cannot_worsen_best_synthetic_loss(self):
        m=SyntheticLinearQualityLoss(.2)
        a,_=solve_generic(m,budget=1e20,context_tokens=2048,Q0=.5,family="power",starts=16,seed=1)
        b,_=solve_generic(m,budget=1e21,context_tokens=2048,Q0=.5,family="power",starts=16,seed=1)
        self.assertLessEqual(b["loss"],a["loss"]+1e-8)
    def test_context_cost_hurts_at_fixed_budget(self):
        m=SyntheticLinearQualityLoss(.2)
        a,_=solve_generic(m,budget=1e20,context_tokens=2048,Q0=.5,family="power",starts=16,seed=2)
        b,_=solve_generic(m,budget=1e20,context_tokens=131072,Q0=.5,family="power",starts=16,seed=2)
        self.assertGreaterEqual(b["loss"],a["loss"]-1e-7)
    def test_tiny_boundary_ratios_reject_wrong_corner(self):
        m=SyntheticLinearQualityLoss(.2)
        sol={"N_params_B":m.support.N[0],"D_tokens_B":m.support.D[0],"Q":.5}
        r=enrich_kkt(sol,m,1e24,8192,.5,"power")
        self.assertFalse(r["kkt_check_pass"])
        self.assertGreater(r["kkt_relative_violation"],.9)
    def test_explicit_support_and_exact_endpoint(self):
        m=SyntheticLinearQualityLoss(.2)
        support=Support((.07,.08),(10.,11.),(.1,.8))
        sol,_=solve_generic(m,budget=1e24,context_tokens=8192,Q0=.5,family="power",starts=3,support=support)
        self.assertAlmostEqual(sol["N_params_B"],.08)
        self.assertAlmostEqual(sol["D_tokens_B"],11.)
        self.assertAlmostEqual(sol["Q"],.8,places=14)
        self.assertTrue(sol["kkt_check_pass"])
    def test_missing_support_rejected(self):
        class Unspecified:
            value_grad=SyntheticLinearQualityLoss().value_grad
        with self.assertRaises(ValueError):
            solve_generic(Unspecified(),budget=1e22,context_tokens=8192,Q0=.5,family="power")
    def test_slack_free_point_rejected(self):
        r=enrich_kkt({"N_params_B":1.,"D_tokens_B":100.,"Q":.7},SyntheticLinearQualityLoss(),1e24,8192,.5,"power")
        self.assertFalse(r["kkt_check_pass"])
    def test_transition_detector(self):
        rows=[{"context_tokens":2048,"budget_FLOPs":1,"active_set":["N_min","budget"]},
              {"context_tokens":2048,"budget_FLOPs":2,"active_set":["budget"]},
              {"context_tokens":2048,"budget_FLOPs":3,"active_set":["D_max","budget"]}]
        self.assertEqual(len(detect_transitions(rows)),2)
if __name__=="__main__":unittest.main()

