from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parent))
from q3_generic_solver import SyntheticLinearQualityLoss,solve_generic,detect_transitions

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
    def test_transition_detector(self):
        rows=[{"context_tokens":2048,"budget_FLOPs":1,"active_set":["N_min","budget"]},
              {"context_tokens":2048,"budget_FLOPs":2,"active_set":["budget"]},
              {"context_tokens":2048,"budget_FLOPs":3,"active_set":["D_max","budget"]}]
        self.assertEqual(len(detect_transitions(rows)),2)
if __name__=="__main__":unittest.main()
