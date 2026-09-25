"""Build deterministic conditional v3 metadata and consumer fixtures."""
from __future__ import annotations

import hashlib
import json

from audit_b_scaling_laws import ROOT
from chm_adapter_v3 import CHMAdapterV3, STATUS, VERSION


def normalized_hash(path):
    return hashlib.sha256((ROOT / path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def main():
    model = CHMAdapterV3(mode="conditional_diagnostic")
    metadata = model.capabilities()
    reference = metadata["reference_p"]
    changed = dict(reference)
    changed["arxiv"] += .01
    changed["freelaw"] -= .01
    common = {"N_params_B": .7, "D_tokens_B": 150., "Q_score": .5,
              "Q0": .5, "context_tokens": 2048,
              "quality_family": "exponential", "budget_FLOPs": 1e22}
    requests = [{"request_id": "reference", **common, "p": reference},
                {"request_id": "p-sensitivity", **common, "p": changed}]
    response = {"schema_version": VERSION, "status": STATUS, "ready_for_Q3": False,
                "results": [{"request_id": row["request_id"],
                             **model.evaluate(**{k: v for k, v in row.items() if k != "request_id"})}
                            for row in requests]}
    if response["results"][0]["prediction"] != response["results"][1]["prediction"]:
        raise AssertionError("p changed B-native prediction")
    outputs = {"chm_v3_request.json": {"schema_version": VERSION,
                                       "mode": "conditional_diagnostic", "requests": requests},
               "chm_v3_expected.json": response}
    directory = ROOT / "outputs/cyj/interfaces"
    directory.mkdir(parents=True, exist_ok=True)
    for name, data in outputs.items():
        (directory / name).write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
                                      encoding="utf-8", newline="\n")
    paths = ["src/cyj/chm_adapter_v3.py", "src/cyj/build_chm_release_v3.py",
             "src/cyj/chm_consumer_smoke_v3.py", "src/cyj/b7_formal_model.py",
             "src/cyj/build_b7_frozen_uncertainty.py", "src/cyj/validate_b7_frozen_model.py",
             "outputs/cyj/quality/b7_frozen_model.json",
             "outputs/cyj/quality/b7_frozen_validation.json",
             "outputs/cyj/quality/b7_frozen_uncertainty.json",
             "outputs/cyj/interfaces/chm_v3_request.json",
             "outputs/cyj/interfaces/chm_v3_expected.json"]
    metadata["files_sha256_utf8_lf"] = {path: normalized_hash(path) for path in paths}
    (directory / "chm_v3_manifest.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8", newline="\n")
    print("PASS: chm_v3_manifest.json, chm_v3_request.json, chm_v3_expected.json")


if __name__ == "__main__":
    main()
