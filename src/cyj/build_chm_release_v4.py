"""Deterministic joint-candidate v4 manifest and three consumer fixtures."""
import hashlib
import json
from audit_b_scaling_laws import ROOT
from chm_adapter_v4 import CHMAdapterV4,VERSION,STATUS


def normalized_hash(relative):
    return hashlib.sha256((ROOT/relative).read_bytes().replace(b"\r\n",b"\n")).hexdigest()


def run():
    model=CHMAdapterV4(mode="conditional_diagnostic")
    metadata=model.capabilities();reference=metadata["reference_p"];changed=dict(reference)
    changed["arxiv"]+=.01;changed["freelaw"]-=.01
    common=dict(N_params_B=.7,D_tokens_B=150.,Q_score=.5,Q0=.5,context_tokens=2048,
                quality_family="exponential",budget_FLOPs=1e22)
    requests=[{"request_id":"reference",**common,"p":reference},
              {"request_id":"p-sensitivity",**common,"p":changed},
              {"request_id":"context-32768",**{**common,"context_tokens":32768}}]
    response={"schema_version":VERSION,"scientific_status":STATUS,"ready_for_Q3":False,
              "results":[{"request_id":r["request_id"],**model.evaluate(**{k:v for k,v in r.items() if k!="request_id"})} for r in requests]}
    if response["results"][0]["prediction"]!=response["results"][1]["prediction"]:
        raise AssertionError("p changed B-native prediction")
    directory=ROOT/"outputs/cyj/interfaces";directory.mkdir(parents=True,exist_ok=True)
    for name,data in (("chm_v4_request.json",{"schema_version":VERSION,"mode":"conditional_diagnostic","requests":requests}),
                      ("chm_v4_expected.json",response)):
        (directory/name).write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8",newline="\n")
    files=["src/cyj/chm_adapter_v4.py","src/cyj/build_chm_release_v4.py","src/cyj/chm_consumer_smoke_v4.py",
           "src/cyj/fit_b7_joint_nonlinear.py","src/cyj/quality_substitution.py","src/cyj/q3_costs.py",
           "outputs/cyj/quality/b7_joint_fit.json","outputs/cyj/quality/b7_identifiability.json",
           "outputs/cyj/quality/b7_nested_cv_predictions.csv","outputs/cyj/quality/b7_nested_cv_summary.json",
           "outputs/cyj/quality/b7_interval_calibration.json",
           "outputs/cyj/interfaces/chm_v4_request.json","outputs/cyj/interfaces/chm_v4_expected.json"]
    metadata["files_sha256_utf8_lf"]={path:normalized_hash(path) for path in files}
    (directory/"chm_v4_manifest.json").write_text(json.dumps(metadata,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8",newline="\n")
    return metadata


if __name__=="__main__":
    m=run();print(json.dumps({"schema_version":m["schema_version"],"files":len(m["files_sha256_utf8_lf"]),"ready_for_Q3":m["ready_for_Q3"]}))
