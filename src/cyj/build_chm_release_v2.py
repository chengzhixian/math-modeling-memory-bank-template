"""Create deterministic chm v2 metadata and executable consumer examples."""
import hashlib
import json
from pathlib import Path
from chm_adapter_v2 import CHMAdapter, ROOT, VERSION


def main():
    model = CHMAdapter(mode="diagnostic")
    metadata = model.capabilities()
    reference = metadata["reference_p"]
    perturbed = dict(reference)
    perturbed["arxiv"] += 0.01
    perturbed["freelaw"] -= 0.01
    common = dict(N_params_B=0.07, D_tokens_B=10, Q0=0.5, context_tokens=2048,
                  quality_family="exponential", budget_FLOPs=1e19)
    requests = [dict(request_id="reference", **common, Q_score=0.5, p=reference),
                dict(request_id="quality-and-p-sensitivity", **common, Q_score=0.7, p=perturbed)]
    response = {"schema_version": VERSION, "status": "diagnostic_only", "ready_for_Q3": False,
                "results": [{"request_id": row["request_id"], **model.evaluate(**{k:v for k,v in row.items() if k != "request_id"})} for row in requests]}
    files = {
        "chm_v2_request.json": {"schema_version": VERSION, "mode": "diagnostic", "requests": requests},
        "chm_v2_expected.json": response,
    }
    directory = ROOT / "outputs/cyj/interfaces"
    for name, data in files.items():
        (directory / name).write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False)+"\n", encoding="utf-8", newline="\n")
    paths = ["src/cyj/chm_adapter_v2.py", "src/cyj/build_chm_release_v2.py", "src/cyj/chm_consumer_smoke.py", "src/cyj/quality_scaling.py",
             "src/cyj/q3_costs.py"] + [f"outputs/cyj/interfaces/{n}" for n in files]
    metadata["files_sha256_utf8_lf"] = {p: hashlib.sha256((ROOT/p).read_bytes().replace(b"\r\n", b"\n")).hexdigest() for p in paths}
    (directory/"chm_v2_manifest.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2)+"\n", encoding="utf-8", newline="\n")
    print("PASS: chm_v2_manifest.json, chm_v2_request.json, chm_v2_expected.json")


if __name__ == "__main__":
    main()
