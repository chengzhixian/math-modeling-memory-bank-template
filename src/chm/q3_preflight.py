"""Q3 upstream gate for chm.

Formal mode reads exact Git objects and applies q3_readiness_policy.v2. It never
turns an unidentified A-Q/B-Q mapping into a fake numerical bridge.
"""
from __future__ import annotations

import argparse,csv,io,json,subprocess
from pathlib import Path
from q3_readiness_policy import evaluate_readiness

REPO=Path(__file__).resolve().parents[2]
DEFAULT_CYJ_REF="6c17cb4e387e1ac047f8fe0e9ecb6fe42fc5ef3b"
DEFAULT_ZHH_REF="d47cd2dc921333caecfcb95f09eb5a2f2714d0db"

def git_show(ref,path):
    p=subprocess.run(["git","show",f"{ref}:{path}"],cwd=REPO,check=True,capture_output=True,text=True,encoding="utf-8")
    return p.stdout

def parse_context_csv(text):
    rows=list(csv.DictReader(io.StringIO(text))); out=[]
    for row in rows:
        raw=row.get("contextTokens") or row.get("context_length") or row.get("max_position_embeddings") or row.get("context_tokens")
        if raw is not None: out.append(int(float(raw)))
    return sorted(set(out))

def normalize_legacy_bundle(bundle):
    if "quality_policy" in bundle and "p_policy" in bundle:
        return bundle
    adoption=bundle.get("adoption",{})
    copy=dict(bundle)
    copy.setdefault("quality_policy",{
        "coordinate":None,
        "performance_status":"missing",
        "joint_NDQ_status":"unidentified",
        "loss_coordinate_id":None,
        "A_Q_mapping_status":adoption.get("Q_mapping_status","unidentified"),
    })
    copy.setdefault("p_policy",{
        "mode":None,
        "target_panel":adoption.get("target_panel",[]),
        "primary_anchor":adoption.get("primary_anchor"),
        "lambda_status":adoption.get("lambda_status"),
        "unique_p_claim_allowed":None,
    })
    return copy

def inspect(cyj_ref,zhh_ref):
    bundle=json.loads(git_show(cyj_ref,"outputs/cyj/interfaces/q3_bundle.json"))
    contract=git_show(cyj_ref,"interfaces/cyj/CONTRACT.md")
    api=git_show(cyj_ref,"interfaces/cyj/Q3_API.md")
    contexts=parse_context_csv(git_show(zhh_ref,"outputs/zhh/context_scenarios.csv"))
    normalized=normalize_legacy_bundle(bundle)
    result=evaluate_readiness(normalized,contexts)
    blockers=list(result["blockers"])
    compact=(contract+api).replace(" ","")
    if "ready_for_Q3=false" in compact:
        blockers.append("producer contract/API still explicitly declares ready_for_Q3=false")
    result.update({
        "cyj_ref":cyj_ref,"zhh_ref":zhh_ref,
        "formal_ready":not blockers,"blockers":blockers,
        "producer_schema":bundle.get("schema_version"),
        "diagnostic_available":True,
        "diagnostic_scope":["B1 N-D","explicit p scenarios","cost geometry","C7 contexts"],
    })
    return result

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--cyj-ref",default=DEFAULT_CYJ_REF)
    ap.add_argument("--zhh-ref",default=DEFAULT_ZHH_REF)
    ap.add_argument("--output",type=Path,default=Path("outputs/chm/q3_preflight.json"))
    a=ap.parse_args()
    result=inspect(a.cyj_ref,a.zhh_ref)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False))
    if not result["formal_ready"]: raise SystemExit(2)
if __name__=="__main__":main()
