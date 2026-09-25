"""Cross-check joint interface policy, gradients, CLI and immutable manifest inputs."""
import hashlib
import json
import math
import subprocess
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/"src/cyj"))
from chm_adapter_v4 import CHMAdapterV4,VERSION
from build_chm_release_v4 import run as rebuild


class JointInterfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.model=CHMAdapterV4(mode="conditional_diagnostic")

    def test_metadata_and_p_separation(self):
        m=self.model;meta=m.capabilities()
        self.assertFalse(meta["ready_for_Q3"])
        for key in ("scientific_status","candidate_result_scope","formal_result_scope","support",
                    "source_dataset","source_hash","model_hash"):
            self.assertIn(key,meta)
        self.assertEqual(tuple(meta["support"]["D_tokens_B"]),(10.,600.))
        self.assertFalse(meta["p_policy"]["B_loss_addition_allowed"])
        p=meta["reference_p"];other=dict(p);other["arxiv"]+=.01;other["freelaw"]-=.01
        request=dict(N_params_B=.7,D_tokens_B=150.,Q_score=.5,Q0=.5,context_tokens=2048,
                     quality_family="exponential",budget_FLOPs=1e22)
        a=m.evaluate(**request,p=p);b=m.evaluate(**request,p=other)
        self.assertEqual(a["prediction"],b["prediction"])
        self.assertNotEqual(a["p_sensitivity"],b["p_sensitivity"])
        self.assertFalse(a["prediction"]["uncertainty"]["calibrated_coverage_claim"])
        external=m.evaluate(**{**request,"context_tokens":32768})
        self.assertEqual(external["cost"]["context_source_status"],
                         "CYJ_external_sensitivity_not_C7_observation")
        self.assertEqual(external["constraints"]["minimum_supported_cost_FLOPs"],
                         m.evaluate(**{**request,"context_tokens":32768,"N_params_B":.07,
                                       "D_tokens_B":10.,"Q_score":.5})["cost"]["total"])
        with self.assertRaises(ValueError):m.evaluate(**{**request,"context_tokens":4097})

    def test_gradient_and_invalid_support(self):
        m=self.model;point=(.7,150.,.5);_,gradient=m.value_grad(*point)
        for axis in range(3):
            h=1e-5*point[axis];low=list(point);high=list(point);low[axis]-=h;high[axis]+=h
            numeric=(m.value_grad(*high)[0]-m.value_grad(*low)[0])/(2*h)
            self.assertAlmostEqual(gradient[axis],numeric,delta=max(1e-8,abs(gradient[axis])*1e-5))
        self.assertTrue(all(v>0 for v in m.improvement_elasticities(*point).values()))
        self.assertLess(m.substitution_rates(*point)["dN_dQ_at_LD"],0)
        for bad in ((.7,9.,.5),(.7,601.,.5),(.7,150.,0.),(.7,150.,1.01),
                    (float("nan"),150.,.5),(-.7,150.,.5),(.7,"150",.5)):
            with self.assertRaises(ValueError):m.value_grad(*bad)
        with self.assertRaises(ValueError):CHMAdapterV4(mode="formal")

    def test_manifest_and_cli_consistency(self):
        before=(ROOT/"outputs/cyj/interfaces/chm_v4_manifest.json").read_bytes()
        rebuild()
        self.assertEqual(before,(ROOT/"outputs/cyj/interfaces/chm_v4_manifest.json").read_bytes())
        manifest=json.loads(before)
        for path,digest in manifest["files_sha256_utf8_lf"].items():
            local=(ROOT/path).read_bytes().replace(b"\r\n",b"\n")
            self.assertEqual(hashlib.sha256(local).hexdigest(),digest)
        command=[sys.executable,"-B",str(ROOT/"src/cyj/chm_adapter_v4.py"),"--request",
                 str(ROOT/"outputs/cyj/interfaces/chm_v4_request.json")]
        process=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,check=True)
        actual=json.loads(process.stdout)
        expected=json.loads((ROOT/"outputs/cyj/interfaces/chm_v4_expected.json").read_text(encoding="utf-8"))
        self.assertEqual(actual,expected)


if __name__=="__main__":unittest.main()
