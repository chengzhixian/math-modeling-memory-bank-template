"""Read exact v4 release objects, compare all listed files and consume fixtures."""
import argparse
import hashlib
import json
import subprocess
from audit_b_scaling_laws import ROOT
from chm_adapter_v4 import CHMAdapterV4,VERSION,STATUS


def check(commit):
    if len(commit)!=40 or any(c not in "0123456789abcdef" for c in commit):
        raise ValueError("release commit must be exact lowercase 40-hex SHA")
    name="outputs/cyj/interfaces/chm_v4_manifest.json"
    blob=subprocess.check_output(["git","show",f"{commit}:{name}"],cwd=ROOT)
    local=(ROOT/name).read_bytes().replace(b"\r\n",b"\n")
    if blob!=local:raise ValueError("manifest differs from release")
    manifest=json.loads(blob)
    if manifest["schema_version"]!=VERSION or manifest["ready_for_Q3"] or manifest["scientific_status"]!=STATUS:
        raise ValueError("unexpected release status")
    for path,digest in manifest["files_sha256_utf8_lf"].items():
        raw=subprocess.check_output(["git","show",f"{commit}:{path}"],cwd=ROOT).replace(b"\r\n",b"\n")
        if hashlib.sha256(raw).hexdigest()!=digest or raw!=(ROOT/path).read_bytes().replace(b"\r\n",b"\n"):
            raise ValueError(f"release file mismatch: {path}")
    model=CHMAdapterV4(mode="conditional_diagnostic")
    request=json.loads((ROOT/"outputs/cyj/interfaces/chm_v4_request.json").read_text(encoding="utf-8"))
    expected=json.loads((ROOT/"outputs/cyj/interfaces/chm_v4_expected.json").read_text(encoding="utf-8"))
    rows=[{"request_id":r["request_id"],**model.evaluate(**{k:v for k,v in r.items() if k!="request_id"})} for r in request["requests"]]
    actual=json.loads(json.dumps({"schema_version":VERSION,"scientific_status":STATUS,
                                  "ready_for_Q3":False,"results":rows},allow_nan=False))
    if actual!=expected:raise ValueError("consumer response differs from exact fixture")
    if model.value_grad(.7,150.,.5)[0]!=rows[0]["prediction"]["loss_value"]:
        raise ValueError("value_grad/evaluate mismatch")
    return {"status":"PASS","release_commit":commit,"manifest_sha256":hashlib.sha256(blob).hexdigest(),
            "requests":len(rows),"ready_for_Q3":False}


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--release-commit",required=True);args=p.parse_args()
    print(json.dumps(check(args.release_commit)))
