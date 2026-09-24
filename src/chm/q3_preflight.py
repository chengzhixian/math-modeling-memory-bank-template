"""Q3 upstream gate for chm.

Reads exact remote/local Git objects only. It does not silently fall back to stale
working-tree files. Formal Q3 remains blocked until the producer explicitly marks
its interface ready_for_Q3=true and required bridge fields are identified.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

DEFAULT_CYJ_REF = "6c17cb4e387e1ac047f8fe0e9ecb6fe42fc5ef3b"
DEFAULT_ZHH_REF = "d47cd2dc921333caecfcb95f09eb5a2f2714d0db"

def git_show(ref: str, path: str) -> str:
    proc = subprocess.run(
        ["git", "show", f"{ref}:{path}"],
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return proc.stdout

def load_json(ref: str, path: str):
    return json.loads(git_show(ref, path))

def parse_context_csv(text: str):
    import csv, io
    rows = list(csv.DictReader(io.StringIO(text)))
    out = []
    for row in rows:
        raw = row.get("context_length") or row.get("max_position_embeddings") or row.get("context_tokens")
        if raw is None:
            for v in row.values():
                try:
                    x = int(float(v))
                    if x in (2048, 8192, 131072):
                        raw = str(x)
                        break
                except Exception:
                    pass
        if raw is not None:
            out.append(int(float(raw)))
    return sorted(set(out))

def inspect(cyj_ref: str, zhh_ref: str):
    bundle = load_json(cyj_ref, "outputs/cyj/interfaces/q3_bundle.json")
    contract = git_show(cyj_ref, "interfaces/cyj/CONTRACT.md")
    api = git_show(cyj_ref, "interfaces/cyj/Q3_API.md")
    contexts = parse_context_csv(git_show(zhh_ref, "outputs/zhh/context_scenarios.csv"))

    adoption = bundle.get("adoption", {})
    blockers = []
    if bundle.get("ready_for_Q3") is not True:
        blockers.append("cyj bundle ready_for_Q3 is not true")
    if "ready_for_Q3=false" in contract.replace(" ", "") or "ready_for_Q3=false" in api.replace(" ", ""):
        blockers.append("cyj producer contract/API explicitly remains draft")
    if adoption.get("Q_mapping_status") in (None, "unidentified"):
        blockers.append("A/B Q mapping is unidentified")
    if adoption.get("primary_anchor") in (None, ""):
        blockers.append("primary p target/anchor is unidentified")
    if adoption.get("lambda_status") != "validated":
        blockers.append("cross-Loss lambda_loss is not validated")
    if contexts != [2048, 8192, 131072]:
        blockers.append(f"zhh C7 contexts unexpected: {contexts}")

    return {
        "schema_version": "chm.q3.preflight.v1",
        "cyj_ref": cyj_ref,
        "zhh_ref": zhh_ref,
        "formal_ready": not blockers,
        "blockers": blockers,
        "diagnostic_available": True,
        "diagnostic_scope": [
            "B1 N-D predictor",
            "explicit p/target/lambda/eta scenario only",
            "three cost families and constraint residuals",
            "C7 external context scenarios",
        ],
        "contexts": contexts,
        "producer_ready_for_Q3": bundle.get("ready_for_Q3"),
        "Q_mapping_status": adoption.get("Q_mapping_status"),
        "primary_anchor": adoption.get("primary_anchor"),
        "lambda_status": adoption.get("lambda_status"),
        "eta_producer_estimate": adoption.get("eta_producer_estimate"),
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cyj-ref", default=DEFAULT_CYJ_REF)
    parser.add_argument("--zhh-ref", default=DEFAULT_ZHH_REF)
    parser.add_argument("--output", type=Path, default=Path("outputs/chm/q3_preflight.json"))
    args = parser.parse_args()

    result = inspect(args.cyj_ref, args.zhh_ref)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    if not result["formal_ready"]:
        raise SystemExit(2)

if __name__ == "__main__":
    main()
