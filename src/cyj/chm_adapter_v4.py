"""Conditional CYJ joint B7 candidate; preserves separate A-side p sensitivity."""
from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np

from audit_b_scaling_laws import ROOT,sha256
from chm_adapter_v3 import CHMAdapterV3,checked_point,unique_object
from fit_b7_joint_nonlinear import OUTPUT as JOINT_OUTPUT,predict
from quality_substitution import derivatives

VERSION="cyj.chm.v4"
STATUS="conditional_joint_B7_semi_synthetic"
ID_PATH=ROOT/"outputs/cyj/quality/b7_identifiability.json"
NESTED_PATH=ROOT/"outputs/cyj/quality/b7_nested_cv_predictions.csv"


class CHMAdapterV4(CHMAdapterV3):
    def __init__(self,*,mode):
        if mode!="conditional_diagnostic":raise ValueError("v4 requires conditional_diagnostic; formal gate closed")
        super().__init__(mode=mode)
        self.joint=json.loads(JOINT_OUTPUT.read_text(encoding="utf-8"))
        self.identification=json.loads(ID_PATH.read_text(encoding="utf-8"))
        if (self.joint["source_hash"]!=self.frozen["B7_sha256"] or
            self.identification["model_hash"]!=sha256(JOINT_OUTPUT) or
            self.joint["ready_for_Q3"] or self.identification["ready_for_Q3"]):
            raise ValueError("joint B7 identity or gate mismatch")
        self.joint_theta=self.joint["model"]["theta"]
        self.parameter_samples=np.asarray(self.identification["bootstrap_parameter_samples"],float)
        import csv
        with NESTED_PATH.open(encoding="utf-8",newline="") as f:
            rows=list(csv.DictReader(f))
        self.residuals=np.array([float(r["residual"]) for r in rows if r["axis"]=="N_params_B"])
        if len(self.residuals)!=450 or len(self.parameter_samples)!=200:
            raise ValueError("joint uncertainty source shape changed")

    def value_grad(self,N_B,D_B,Q):
        value,gradient=derivatives(self.joint_theta,*checked_point(N_B,D_B,Q))
        return float(value),tuple(map(float,gradient))

    def elasticities(self,N_B,D_B,Q):
        n,d,q=checked_point(N_B,D_B,Q);loss,grad=self.value_grad(n,d,q)
        return dict(zip(("N_params_B","D_tokens_B","Q_score"),(float(x*g/loss) for x,g in zip((n,d,q),grad))))

    def improvement_elasticities(self,N_B,D_B,Q):
        return {k:-v for k,v in self.elasticities(N_B,D_B,Q).items()}

    def substitution_rates(self,N_B,D_B,Q):
        _,(ln,ld,lq)=self.value_grad(N_B,D_B,Q)
        if min(abs(ln),abs(ld),abs(lq))<1e-15:raise ValueError("undefined local substitution at vanishing derivative")
        return {"dD_dN_at_LQ":-ln/ld,"dQ_dN_at_LD":-ln/lq,"dQ_dD_at_LN":-ld/lq,
                "dN_dQ_at_LD":-lq/ln,"dD_dQ_at_LN":-lq/ld}

    def prediction_interval(self,N_B,D_B,Q):
        n,d,q=checked_point(N_B,D_B,Q)
        point=np.array([[n,d,q]])
        means=np.array([predict(t,point)[0] for t in self.parameter_samples])
        rng=np.random.default_rng(20260925)
        selected=self.residuals[rng.integers(0,len(self.residuals),len(means))]
        draws=means+selected
        if not np.all(np.isfinite(draws)):raise ValueError("nonfinite conditional interval")
        return {"central_estimate":self.value_grad(n,d,q)[0],
                "conditional_mean_percentile_95":list(map(float,np.quantile(means,[.025,.975]))),
                "empirical_prediction_percentile_95":list(map(float,np.quantile(draws,[.025,.975]))),
                "median_predictive_draw":float(np.median(draws)),
                "scope":"B7 semi-synthetic conditional empirical; not independently calibrated",
                "calibrated_coverage_claim":False}

    def capabilities(self):
        result=super().capabilities()
        for old,new in (("frozen_model_sha256","historical_v3_model_sha256"),
                        ("validation_sha256","historical_v3_validation_sha256"),
                        ("uncertainty_sha256","historical_v3_uncertainty_sha256")):
            result[new]=result.pop(old)
        result.update(schema_version=VERSION,status=STATUS,ready_for_Q3=False,
                      scientific_status=STATUS,candidate_result_scope="NDQ_with_p_sensitivity",
                      formal_result_scope=None,support=result["bounds"],
                      source_dataset="official_attachment_B7_semi_synthetic",
                      source_hash=self.joint["source_hash"],model_hash=sha256(JOINT_OUTPUT),
                      joint_identifiability_sha256=sha256(ID_PATH),nested_predictions_sha256=sha256(NESTED_PATH),
                      formula="E+A*N^-alpha+B*D^-beta+(1-Q)*(G0+GN*ln(N)+GD*ln(D/100))",
                      estimator="8-parameter joint constrained SSE; 12 full-data starts",
                      formal_blockers=["historical full-B7 family exploration prevents untouched test",
                                       "semi-synthetic B7 and no real-training external validation",
                                       "joint bootstrap+residual interval not independently calibrated",
                                       "CHM owner acceptance pending"])
        result["uncertainty_policy"]={"U1_parameter_estimation":"200 ND-cluster joint fits",
                                      "U2_model_form":"five-family inner CV, no model probability",
                                      "U3_prediction_residual":"N-axis nested OOF empirical residuals",
                                      "U4_cross_source":None,"U5_benchmark_bridge":None,
                                      "coverage_calibrated_for_this_interval":False}
        return result

    def evaluate(self,**kwargs):
        result=super().evaluate(**kwargs)
        result.update(schema_version=VERSION,status=STATUS,scientific_status=STATUS,
                      candidate_result_scope="NDQ_with_p_sensitivity",formal_result_scope=None,
                      support=self.capabilities()["support"],source_dataset="official_attachment_B7_semi_synthetic",
                      source_hash=self.joint["source_hash"],model_hash=sha256(JOINT_OUTPUT),ready_for_Q3=False)
        result["prediction"]["improvement_elasticities"]=self.improvement_elasticities(**{
            "N_B":kwargs["N_params_B"],"D_B":kwargs["D_tokens_B"],"Q":kwargs["Q_score"]})
        return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--describe",action="store_true")
    group.add_argument("--request",type=Path)
    args=parser.parse_args()
    try:
        model=CHMAdapterV4(mode="conditional_diagnostic")
        if args.describe:result=model.capabilities()
        else:
            request=json.loads(args.request.read_text(encoding="utf-8-sig"),object_pairs_hook=unique_object)
            if not isinstance(request,dict) or set(request)!={"schema_version","mode","requests"} or request["schema_version"]!=VERSION or request["mode"]!="conditional_diagnostic":
                raise ValueError("expected cyj.chm.v4 conditional_diagnostic batch")
            if not isinstance(request["requests"],list) or not request["requests"]:raise ValueError("nonempty requests required")
            required={"request_id","N_params_B","D_tokens_B","Q_score","Q0","context_tokens","quality_family","budget_FLOPs"}
            seen=set();rows=[]
            for row in request["requests"]:
                if not isinstance(row,dict) or not required<=set(row) or set(row)-required-{"p"}:raise ValueError("incorrect request fields")
                identity=row["request_id"]
                if not isinstance(identity,str) or not identity.strip() or identity in seen:raise ValueError("duplicate or empty request_id")
                seen.add(identity);rows.append({"request_id":identity,**model.evaluate(**{k:v for k,v in row.items() if k!="request_id"})})
            result={"schema_version":VERSION,"scientific_status":STATUS,"ready_for_Q3":False,"results":rows}
        print(json.dumps(result,ensure_ascii=False,allow_nan=False));return 0
    except (ValueError,TypeError,KeyError,OSError,subprocess.CalledProcessError) as exc:
        print(json.dumps({"error":str(exc)},ensure_ascii=False),file=sys.stderr);return 2


if __name__=="__main__":raise SystemExit(main())
