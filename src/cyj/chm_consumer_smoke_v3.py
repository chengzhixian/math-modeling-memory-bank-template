"""Verify a precise immutable CYJ v3 release, then consume its fixtures."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess

from audit_b_scaling_laws import ROOT
from chm_adapter_v3 import CHMAdapterV3, STATUS, VERSION


def git_blob(commit, path):
    return subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=ROOT)


def check(commit):
    if len(commit) != 40 or any(c not in "0123456789abcdef" for c in commit):
        raise ValueError("release commit must be a lowercase 40-hex SHA")
    metadata_path = "outputs/cyj/interfaces/chm_v3_manifest.json"
    manifest_bytes = git_blob(commit, metadata_path)
    if manifest_bytes != (ROOT / metadata_path).read_bytes().replace(b"\r\n", b"\n"):
        raise ValueError("local manifest differs from immutable release")
    manifest = json.loads(manifest_bytes)
    if manifest["schema_version"] != VERSION or manifest["status"] != STATUS or manifest["ready_for_Q3"]:
        raise ValueError("unexpected v3 release status")
    for path, digest in manifest["files_sha256_utf8_lf"].items():
        blob = git_blob(commit, path).replace(b"\r\n", b"\n")
        local = (ROOT / path).read_bytes().replace(b"\r\n", b"\n")
        if hashlib.sha256(blob).hexdigest() != digest or blob != local:
            raise ValueError(f"release file mismatch: {path}")
    model = CHMAdapterV3(mode="conditional_diagnostic")
    request = json.loads((ROOT / "outputs/cyj/interfaces/chm_v3_request.json").read_text(encoding="utf-8"))
    expected = json.loads((ROOT / "outputs/cyj/interfaces/chm_v3_expected.json").read_text(encoding="utf-8"))
    rows = [{"request_id": row["request_id"],
             **model.evaluate(**{k: v for k, v in row.items() if k != "request_id"})}
            for row in request["requests"]]
    actual = {"schema_version": VERSION, "status": STATUS, "ready_for_Q3": False, "results": rows}
    if actual != expected:
        raise ValueError("consumer response differs from release fixture")
    if model.value_grad(.7, 150., .5)[0] != rows[0]["prediction"]["loss_value"]:
        raise ValueError("value_grad differs from evaluate")
    return {"status": "PASS", "release_commit": commit, "requests": len(rows),
            "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
            "ready_for_Q3": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--release-commit", required=True)
    args = parser.parse_args()
    print(json.dumps(check(args.release_commit)))
