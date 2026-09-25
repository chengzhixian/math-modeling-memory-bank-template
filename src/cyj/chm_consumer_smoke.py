"""Verify a pinned CYJ release and exercise its CHM-facing diagnostic API."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess

from audit_b_scaling_laws import ROOT
from chm_adapter_v2 import CHMAdapter, CHM_COMMIT, VERSION

FILES = (
    "src/cyj/chm_adapter_v2.py",
    "src/cyj/build_chm_release_v2.py",
    "src/cyj/chm_consumer_smoke.py",
    "outputs/cyj/interfaces/chm_v2_manifest.json",
    "outputs/cyj/interfaces/chm_v2_request.json",
    "outputs/cyj/interfaces/chm_v2_expected.json",
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release-commit", required=True)
    args = parser.parse_args()
    release = args.release_commit.lower()
    if not re.fullmatch(r"[0-9a-f]{40}", release):
        raise ValueError("release commit must be a full immutable SHA")
    for relative in FILES:
        published = subprocess.check_output(["git", "show", f"{release}:{relative}"], cwd=ROOT)
        local = (ROOT / relative).read_bytes()
        if hashlib.sha256(published).digest() != hashlib.sha256(local).digest():
            raise ValueError(f"local file differs from pinned CYJ release: {relative}")
    manifest = json.loads((ROOT / FILES[3]).read_text(encoding="utf-8"))
    if (manifest["schema_version"] != VERSION or manifest["chm_commit"] != CHM_COMMIT
            or manifest["p_policy"]["mode"] != "sensitivity_only"
            or manifest["ready_for_Q3"] is not False):
        raise ValueError("unexpected release policy")
    for relative, expected in manifest["files_sha256_utf8_lf"].items():
        raw = (ROOT / relative).read_bytes().replace(b"\r\n", b"\n")
        if hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError(f"release manifest file mismatch: {relative}")
    model = CHMAdapter(mode="diagnostic")
    request = json.loads((ROOT / FILES[4]).read_text(encoding="utf-8"))
    expected = json.loads((ROOT / FILES[5]).read_text(encoding="utf-8"))
    rows = [{"request_id": row["request_id"],
             **model.evaluate(**{k: v for k, v in row.items() if k != "request_id"})}
            for row in request["requests"]]
    actual = {"schema_version": VERSION, "status": "diagnostic_only", "ready_for_Q3": False,
              "results": rows}
    if json.loads(json.dumps(actual, allow_nan=False)) != expected:
        raise ValueError("consumer output differs from pinned example")
    value, gradient = model.value_grad(0.07, 10, 0.5)
    if abs(value - rows[0]["prediction"]["loss_value"]) > 1e-12 or len(gradient) != 3:
        raise ValueError("solver value_grad contract failed")
    print(json.dumps({"result": "PASS", "cyj_release_commit": release,
                      "chm_producer_commit": CHM_COMMIT, "schema_version": VERSION,
                      "example_requests": len(rows), "ready_for_Q3": False}))


if __name__ == "__main__":
    main()
