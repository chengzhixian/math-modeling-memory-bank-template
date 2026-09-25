"""Execute the v7 builder under Python's file-open audit and check its manifest."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from build_q2_v7 import OUT, main as build
from chm_q1_v2_consumer import ROOT, sha256


def main():
    original_a = (ROOT / "data/raw/real_attachments" / "A_data_value").resolve()
    derived_q1 = (ROOT / "outputs/chm/q1_v2").resolve()
    reads = {"original_A": [], "derived_Q1": []}

    def audit(event, args):
        if event != "open" or not args:
            return
        try:
            path = Path(args[0]).resolve()
        except (TypeError, ValueError, OSError):
            return
        try:
            if path.is_relative_to(original_a):
                reads["original_A"].append(str(path.relative_to(ROOT)))
            elif path.is_relative_to(derived_q1):
                reads["derived_Q1"].append(str(path.relative_to(ROOT)))
        except ValueError:
            pass

    sys.addaudithook(audit)
    built = build()
    if reads["original_A"] or not reads["derived_Q1"]:
        raise ValueError("raw-A read or no Q1 derived-file read during v7 build")
    manifest_path = OUT / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    mismatches = [name for name, digest in manifest["files"].items() if sha256(OUT / name) != digest]
    if mismatches:
        raise ValueError(f"Q2 output manifest mismatch: {mismatches}")
    result = {"schema_version": "cyj.q2.v7.audit.v1", "status": "PASS",
              "original_A_open_events": len(reads["original_A"]),
              "derived_Q1_open_events": len(reads["derived_Q1"]),
              "scope": "Python open events during build_q2_v7 main; not OS subprocess file tracing",
              "builder": built, "manifest_sha256": sha256(manifest_path)}
    (ROOT / "outputs/cyj/q2_v7_runtime_audit.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(main()))
