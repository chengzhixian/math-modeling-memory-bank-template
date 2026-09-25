"""Cold-import and build v8 under a fail-closed Python raw-A/subprocess audit."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUDIT_OUT = ROOT / "outputs/cyj/q2_v8_runtime_audit.json"


def main():
    original_a = (ROOT/"data/raw/real_attachments"/"A_data_value").resolve()
    derived_q1 = (ROOT/"outputs/chm/q1_v2").resolve()
    reads = {"original_A": [], "derived_Q1": []}
    spawns = []
    active = [True]

    def audit(event, args):
        if not active[0]:
            return
        if event in ("subprocess.Popen", "os.system", "os.spawn", "os.exec"):
            spawns.append(event)
            raise ValueError(f"v8 builder attempted subprocess: {event}")
        if event != "open" or not args:
            return
        try:
            path = Path(args[0]).resolve()
            if path.is_relative_to(original_a):
                reads["original_A"].append(str(path.relative_to(ROOT)))
            elif path.is_relative_to(derived_q1):
                reads["derived_Q1"].append(str(path.relative_to(ROOT)))
        except (TypeError, ValueError, OSError):
            return

    sys.addaudithook(audit)
    try:
        from build_q2_v8 import OUT, main as build
        from chm_q1_v2_consumer import sha256
        built = build()
    finally:
        active[0] = False
    if reads["original_A"] or not reads["derived_Q1"] or spawns:
        raise ValueError("v8 raw-A or subprocess audit failed")
    manifest = json.loads((OUT/"manifest.json").read_text(encoding="utf-8"))
    changed = [name for name, digest in manifest["files"].items() if sha256(OUT/name) != digest]
    if changed:
        raise ValueError(f"v8 output hash mismatch: {changed}")
    report = {"schema_version": "cyj.q2.v8.runtime_audit.v1", "status": "PASS",
              "original_A_open_events": len(reads["original_A"]),
              "derived_Q1_open_events": len(reads["derived_Q1"]),
              "subprocess_launch_events": len(spawns),
              "scope": "Python file-open and process-spawn events during cold imports and build; native-library file access outside Python audit coverage",
              "builder": built, "manifest_sha256": sha256(OUT/"manifest.json")}
    AUDIT_OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)+"\n",
                         encoding="utf-8", newline="\n")
    return report


if __name__ == "__main__":
    print(json.dumps(main(), ensure_ascii=False))
