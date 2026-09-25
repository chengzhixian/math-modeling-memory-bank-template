import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/"src/cyj"))
from chm_adapter_v2 import CHMAdapter, load_q1, unique_object, CHM_COMMIT, CHM_FILES_SHA


class CHMV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = CHMAdapter(mode="diagnostic")

    def test_value_grad_matches_pinned_b7_and_difference(self):
        x = [1.0, 100.0, 0.5]
        value, grad = self.model.value_grad(*x)
        expected = self.model.model.predict(*x, mode="diagnostic")
        self.assertAlmostEqual(value, expected["loss_value"], places=12)
        for i in range(3):
            step = x[i]*1e-5
            a, b = x.copy(), x.copy()
            a[i] += step; b[i] -= step
            fd = (self.model.value_grad(*a)[0]-self.model.value_grad(*b)[0])/(2*step)
            self.assertAlmostEqual(fd, grad[i], delta=1e-8)

    def test_rejects_legacy_solver_range_and_formal(self):
        for args in [(1,.134,.5),(1,100,"0.5"),(True,100,.5),(1,100,float("nan"))]:
            with self.assertRaises(ValueError): self.model.value_grad(*args)
        with self.assertRaises(ValueError): CHMAdapter(mode="formal")

    def test_q1_v12_centering_and_contrast(self):
        q1, _ = load_q1()
        self.assertFalse(hasattr(q1, "scale"))
        p = dict(q1.reference)
        out = self.model.p_sensitivity(p)
        self.assertEqual(len(out["effects"]), 13)
        self.assertTrue(all(v == 0 for v in out["effects"].values()))
        p["arxiv"] += .01; p["freelaw"] -= .01
        moved = self.model.p_sensitivity(p)
        for target, value in moved["effects"].items():
            coefficients = q1.coefficients[target]
            self.assertAlmostEqual(value, .01*(float(coefficients["arxiv"])-float(coefficients["freelaw"])), places=12)
        self.assertFalse(moved["B_loss_addition_allowed"])
        with self.assertRaises(ValueError): self.model.p_sensitivity({k:2*v for k,v in p.items()})

    def test_pinned_provenance_and_no_legacy_eta(self):
        meta = self.model.capabilities()
        self.assertEqual(meta["chm_commit"], CHM_COMMIT)
        self.assertEqual(meta["chm_consumed_files_sha256"], CHM_FILES_SHA)
        self.assertEqual(meta["p_policy"]["mode"], "sensitivity_only")
        self.assertNotIn("eta_producer_estimate", json.dumps(meta))
        with self.assertRaises(TypeError):
            self.model.evaluate(N_params_B=.07, D_tokens_B=10, Q_score=.5, Q0=.5,
                                context_tokens=2048, quality_family="exponential",
                                budget_FLOPs=1e19, eta=.145)

    def test_budget_and_p_do_not_change_b_loss(self):
        p = dict(load_q1()[0].reference)
        args = dict(N_params_B=.07,D_tokens_B=10,Q_score=.5,Q0=.5,context_tokens=2048,
                    quality_family="exponential",budget_FLOPs=1e19)
        a = self.model.evaluate(**args, p=p)
        self.assertEqual(a["loss_coordinate"]["id"], "attachment_B7_native_val_loss")
        self.assertIsNone(a["uncertainty"]["prediction_interval"])
        self.assertIsNone(a["uncertainty"]["cross_source_uncertainty"])
        self.assertIsNone(a["uncertainty"]["benchmark_bridge_uncertainty"])
        self.assertEqual(set(a["uncertainty"]["components"]),
                         {"U1_parameter_estimation", "U2_model_form", "U3_prediction_residual",
                          "U4_cross_source", "U5_benchmark_bridge"})
        self.assertFalse(a["ready_for_Q3"])
        p["arxiv"] += .01; p["freelaw"] -= .01
        b = self.model.evaluate(**args, p=p)
        self.assertEqual(a["prediction"], b["prediction"])
        self.assertNotEqual(a["p_sensitivity"]["effects"], b["p_sensitivity"]["effects"])
        self.assertAlmostEqual(a["cost"]["total"]/1e18, 4.48672, places=10)
        low = self.model.evaluate(**(args | {"budget_FLOPs": 1e18}))
        self.assertFalse(low["constraints"]["budget_support_nonempty"])
        with self.assertRaises(ValueError): self.model.evaluate(**(args | {"Q0": .7}))

    def test_chm_readiness_gate_not_bypassed(self):
        code = subprocess.check_output(["git","show",f"{CHM_COMMIT}:src/chm/q3_readiness_policy.py"],cwd=ROOT,text=True)
        namespace = {}; exec(compile(code,"chm_readiness_policy","exec"),namespace)
        result = namespace["evaluate_readiness"](self.model.capabilities(), [2048,8192,131072])
        self.assertFalse(result["formal_ready"])
        self.assertEqual(len(result["blockers"]),3)
        self.assertFalse(result["A_Q_mapping_required"])

    def test_cli_fixture_and_duplicate_keys(self):
        path = ROOT/"outputs/cyj/interfaces/chm_v2_request.json"
        run = subprocess.run([sys.executable,"-B",str(ROOT/"src/cyj/chm_adapter_v2.py"),"--request",str(path)],
                             cwd=ROOT.parent,capture_output=True,text=True)
        self.assertEqual(run.returncode,0,run.stderr)
        expected = json.loads((path.parent/"chm_v2_expected.json").read_text(encoding="utf-8"))
        self.assertEqual(json.loads(run.stdout),expected)
        with self.assertRaises(ValueError): json.loads('{"x":1,"x":2}',object_pairs_hook=unique_object)
        payload = json.loads(path.read_text(encoding="utf-8")); payload["requests"][1]["Q_score"] = "0.7"
        with tempfile.TemporaryDirectory() as tmp:
            invalid = Path(tmp)/"request.json"; invalid.write_text(json.dumps(payload),encoding="utf-8")
            bad = subprocess.run([sys.executable,"-B",str(ROOT/"src/cyj/chm_adapter_v2.py"),"--request",str(invalid)],capture_output=True,text=True)
        self.assertEqual(bad.returncode,2)
        self.assertEqual(bad.stdout,"")


if __name__ == "__main__": unittest.main()
