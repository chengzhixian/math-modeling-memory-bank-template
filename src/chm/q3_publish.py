"""Formal Q3 publication validator.

This module does not solve Q3. It validates already-computed formal rows and
refuses to publish unless readiness, cost accounting, scope and KKT requirements
are satisfied.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,math
from pathlib import Path

OPT_FIELDS=(
    "run_id","budget_FLOPs","context_tokens","quality_family","result_scope",
    "N_params_B","D_tokens_B","Q_score","loss_value","loss_coordinate_id",
    "C_train_FLOPs","C_quality_FLOPs","C_attention_FLOPs","C_total_FLOPs",
    "budget_residual_FLOPs","budget_utilization","active_set","kkt_check_pass",
    "support_status","extrapolation_status","status",
    "p_policy","p_mixture_id","p_target","lambda_status",
    "cyj_ref","chm_q1_version","zhh_ref",
)

def _finite(x):
    try:return math.isfinite(float(x))
    except Exception:return False

def validate_row(row,readiness,*,rel_tol=1e-8):
    missing=[k for k in OPT_FIELDS if k not in row]
    if missing:raise ValueError(f"missing fields: {missing}")
    if readiness.get("formal_ready") is not True:raise ValueError("formal readiness is false")
    if row["status"]!="formal_validated":raise ValueError("formal publication requires status=formal_validated")
    if row["result_scope"]!=readiness.get("formal_result_scope"):raise ValueError("result scope does not match readiness")
    positive=("budget_FLOPs","N_params_B","D_tokens_B","loss_value","C_train_FLOPs","C_attention_FLOPs","C_total_FLOPs")
    if any(not _finite(row[k]) or float(row[k])<=0 for k in positive):raise ValueError("nonpositive/nonfinite formal numeric field")
    if not _finite(row["Q_score"]) or not 0<float(row["Q_score"])<=1:raise ValueError("Q_score outside (0,1]")
    if not _finite(row["C_quality_FLOPs"]) or float(row["C_quality_FLOPs"])<0:raise ValueError("invalid quality cost")
    subtotal=float(row["C_train_FLOPs"])+float(row["C_quality_FLOPs"])+float(row["C_attention_FLOPs"])
    total=float(row["C_total_FLOPs"]);budget=float(row["budget_FLOPs"])
    if abs(subtotal-total)>rel_tol*max(1,total):raise ValueError("cost components do not sum to total")
    residual=total-budget
    if abs(float(row["budget_residual_FLOPs"])-residual)>rel_tol*max(1,budget):raise ValueError("budget residual mismatch")
    if total>budget*(1+rel_tol):raise ValueError("budget violated")
    if abs(float(row["budget_utilization"])-total/budget)>rel_tol:raise ValueError("budget utilization mismatch")
    if row["kkt_check_pass"] not in (True,"true","True",1,"1"):raise ValueError("KKT check not passed")
    if not row["loss_coordinate_id"]:raise ValueError("loss coordinate missing")
    if not row["support_status"] or not row["extrapolation_status"]:raise ValueError("support/extrapolation status missing")

    if row["result_scope"]=="full_NDQP":
        if row["p_policy"]!="validated_bridge":raise ValueError("full_NDQP requires validated_bridge")
        if not row["p_mixture_id"] or not row["p_target"] or row["lambda_status"]!="validated":
            raise ValueError("full_NDQP p bridge incomplete")
    elif row["result_scope"]=="NDQ_with_p_sensitivity":
        if row["p_policy"]!="sensitivity_only":raise ValueError("NDQ_with_p_sensitivity requires sensitivity_only")
        if row["p_mixture_id"] not in ("",None) or row["p_target"] not in ("",None):
            raise ValueError("sensitivity-only main row must not claim a unique p")
    else:raise ValueError("unsupported result_scope")
    return True

def validate_uncertainty(rows,run_ids):
    required={"run_id","variable","point","median","p025","p975","n_draws","coverage_scope","sources"}
    seen=set()
    for r in rows:
        if not required<=set(r):raise ValueError("uncertainty fields missing")
        if r["run_id"] not in run_ids:raise ValueError("uncertainty row references unknown run")
        vals=[float(r[k]) for k in ("point","median","p025","p975")]
        if not all(map(math.isfinite,vals)) or not vals[2]<=vals[1]<=vals[3]:raise ValueError("invalid uncertainty interval")
        if int(r["n_draws"])<=0 or not r["coverage_scope"]:raise ValueError("invalid uncertainty metadata")
        key=(r["run_id"],r["variable"])
        if key in seen:raise ValueError("duplicate uncertainty variable")
        seen.add(key)
    return True

def validate_p_sensitivity(rows,run_ids):
    required={"run_id","target","loss_coordinate_id","scale_transfer_status","mixture_id","A_target_delta","selection_support","large_scale_reliability_flag","status"}
    for r in rows:
        if not required<=set(r):raise ValueError("p sensitivity fields missing")
        if r["run_id"] not in run_ids:raise ValueError("p sensitivity references unknown run")
        if "eta" in r or "lambda_scenario" in r:raise ValueError("withdrawn scale/bridge fields are forbidden")
        if r["loss_coordinate_id"]!="A4_A5_1M_target_cross_entropy_contrast" or r["scale_transfer_status"]!="not_identified_from_attachment_A":raise ValueError("p sensitivity must remain in A-native 1M coordinate")
        if not _finite(r["A_target_delta"]):raise ValueError("invalid A contrast")
        if r["status"]!="formal_sensitivity":raise ValueError("invalid p sensitivity status")
        if not r["target"] or not r["mixture_id"] or not r["selection_support"]:raise ValueError("incomplete p sensitivity row")
    return True

def sha256(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def write_csv(path,rows,fields):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

def publish(bundle,out_dir):
    readiness=bundle["readiness"];rows=bundle["optimization"]
    if not rows:raise ValueError("no optimization rows")
    for r in rows:validate_row(r,readiness)
    run_ids={r["run_id"] for r in rows}
    if len(run_ids)!=len(rows):raise ValueError("duplicate run_id")
    p_rows=bundle.get("p_sensitivity",[]);u_rows=bundle.get("uncertainty_summary",[])
    validate_p_sensitivity(p_rows,run_ids);validate_uncertainty(u_rows,run_ids)
    if readiness["formal_result_scope"]=="NDQ_with_p_sensitivity" and not p_rows:
        raise ValueError("sensitivity-only formal result requires p_sensitivity rows")
    if {r["run_id"] for r in u_rows} != run_ids:raise ValueError("every run requires uncertainty_summary")
    if readiness["formal_result_scope"]=="NDQ_with_p_sensitivity" and {r["run_id"] for r in p_rows} != run_ids:
        raise ValueError("every run requires p sensitivity")
    out=Path(out_dir);out.mkdir(parents=True,exist_ok=True)
    write_csv(out/"optimization.csv",rows,OPT_FIELDS)
    if p_rows:write_csv(out/"p_sensitivity.csv",p_rows,list(p_rows[0]))
    write_csv(out/"uncertainty_summary.csv",u_rows,list(u_rows[0]))
    manifest={"schema_version":"chm.q3.formal_results.v2","status":"formal_validated",
              "readiness":readiness,"provenance":bundle.get("provenance",{}),"files":{}}
    for name in ("optimization.csv","p_sensitivity.csv","uncertainty_summary.csv"):
        p=out/name
        if p.exists():manifest["files"][name]={"sha256":sha256(p),"bytes":p.stat().st_size}
    (out/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return manifest

def main():
    ap=argparse.ArgumentParser();ap.add_argument("bundle",type=Path)
    ap.add_argument("--output-dir",type=Path,default=Path("outputs/chm/q3_formal_v2"))
    a=ap.parse_args();data=json.loads(a.bundle.read_text(encoding="utf-8"))
    print(json.dumps(publish(data,a.output_dir),ensure_ascii=False))
if __name__=="__main__":main()
