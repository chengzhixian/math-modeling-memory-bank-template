from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parent))
from q3_readiness_policy import evaluate_readiness

class ReadinessPolicyTests(unittest.TestCase):
    def base(self):
        return {"ready_for_Q3":True,
                "quality_policy":{"coordinate":"B_native_Q_score","performance_status":"validated",
                                  "joint_NDQ_status":"validated","loss_coordinate_id":"attachment_B_joint_val_loss",
                                  "A_Q_mapping_status":"unidentified"},
                "p_policy":{"mode":"sensitivity_only","target_panel":["pile_cc","arxiv","github"],
                            "unique_p_claim_allowed":False,"lambda_status":"scenario_only"}}
    def test_unidentified_A_B_Q_mapping_is_allowed(self):
        x=evaluate_readiness(self.base(),[2048,8192,131072]);self.assertTrue(x["formal_ready"])
        self.assertEqual(x["formal_result_scope"],"NDQ_with_p_sensitivity")
    def test_validated_bridge_requires_lambda(self):
        b=self.base();b["p_policy"]={"mode":"validated_bridge","primary_anchor":"pile_cc","lambda_status":"scenario_only"}
        self.assertFalse(evaluate_readiness(b,[2048,8192,131072])["formal_ready"])
    def test_missing_quality_model_blocks(self):
        b=self.base();b["quality_policy"]["performance_status"]="draft"
        self.assertFalse(evaluate_readiness(b,[2048,8192,131072])["formal_ready"])
    def test_standalone_Q_model_without_joint_loss_blocks(self):
        b=self.base();b["quality_policy"]["joint_NDQ_status"]="unidentified"
        self.assertFalse(evaluate_readiness(b,[2048,8192,131072])["formal_ready"])
if __name__=="__main__":unittest.main()
