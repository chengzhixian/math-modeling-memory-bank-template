from pathlib import Path
import sys,tempfile,unittest
sys.path.insert(0,str(Path(__file__).resolve().parent))
from q3_publish import publish

def bundle():
    ready={"formal_ready":True,"formal_result_scope":"NDQ_with_p_sensitivity"}
    row={"run_id":"r1","budget_FLOPs":1e22,"context_tokens":8192,"quality_family":"power",
         "result_scope":"NDQ_with_p_sensitivity","N_params_B":1.0,"D_tokens_B":100.0,"Q_score":0.7,
         "loss_value":2.0,"loss_coordinate_id":"B_joint","C_train_FLOPs":6e20,
         "C_quality_FLOPs":1e20,"C_attention_FLOPs":1e20,"C_total_FLOPs":8e20,
         "budget_residual_FLOPs":8e20-1e22,"budget_utilization":.08,"active_set":"budget",
         "kkt_check_pass":True,"support_status":"inside","extrapolation_status":"none",
         "status":"formal_validated","p_policy":"sensitivity_only","p_mixture_id":"",
         "p_target":"","lambda_status":"scenario_only","cyj_ref":"x","chm_q1_version":"v1.1","zhh_ref":"z"}
    p={"run_id":"r1","target":"pile_cc","lambda_scenario":"0.1","eta":"0.145","mixture_id":"291",
       "A_target_delta":"-0.9","selection_support":"A4 observed","large_scale_reliability_flag":"caution",
       "status":"formal_sensitivity"}
    u={"run_id":"r1","variable":"loss_value","point":"2","median":"2","p025":"1.9","p975":"2.1",
       "n_draws":"100","coverage_scope":"cyj params only","sources":"test"}
    return {"readiness":ready,"optimization":[row],"p_sensitivity":[p],"uncertainty_summary":[u],
            "provenance":{"synthetic_test_only":True}}

class PublishTests(unittest.TestCase):
    def test_valid_bundle_publishes(self):
        with tempfile.TemporaryDirectory() as d:self.assertEqual(publish(bundle(),d)["status"],"formal_validated")
    def test_not_ready_rejected(self):
        b=bundle();b["readiness"]["formal_ready"]=False
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):publish(b,d)
    def test_cost_mismatch_rejected(self):
        b=bundle();b["optimization"][0]["C_total_FLOPs"]=9e20
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):publish(b,d)
    def test_unique_p_forbidden_in_sensitivity_mode(self):
        b=bundle();b["optimization"][0]["p_mixture_id"]="291"
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):publish(b,d)
    def test_uncertainty_required(self):
        b=bundle();b["uncertainty_summary"]=[]
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):publish(b,d)
if __name__=="__main__":unittest.main()
