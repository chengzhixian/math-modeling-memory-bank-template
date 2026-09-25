"""Execute the v7 builder under Python's file-open audit and check its manifest."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    original_a = (ROOT / "data/raw/real_attachments" / "A_data_value").resolve()
    derived_q1 = (ROOT / "outputs/chm/q1_v2").resolve()
    reads = {"original_A": [], "derived_Q1": []}
    approved_git_show = []
    blocked_spawns = []
    active = [True]

    def audit(event, args):
        if not active[0]:
            return
        if event in ("subprocess.Popen", "os.system", "os.spawn", "os.exec"):
            argv = args[1] if event == "subprocess.Popen" and len(args) > 1 else None
            words = argv.split() if isinstance(argv, str) else list(argv) if isinstance(argv, (list, tuple)) else []
            if (event == "subprocess.Popen" and len(words) == 3 and words[:2] == ["git", "show"]
                    and words[2].startswith("cdda1ad62c5c7eb72b413c4228caeff87d2bad30:")
                    and words[2].split(":", 1)[1].startswith(("interfaces/chm/", "outputs/chm/"))):
                approved_git_show.append(words[2])
                return
            blocked_spawns.append(event)
            raise ValueError(f"unapproved subprocess launch inside v7 builder audit: {event}")
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
    from build_q2_v7 import OUT, main as build
    from chm_q1_v2_consumer import sha256
    built = build()
    active[0] = False
    if reads["original_A"] or not reads["derived_Q1"] or blocked_spawns:
        raise ValueError("raw-A read, missing derived-Q1 read, or unapproved subprocess during v7 build")
    manifest_path = OUT / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    mismatches = [name for name, digest in manifest["files"].items() if sha256(OUT / name) != digest]
    if mismatches:
        raise ValueError(f"Q2 output manifest mismatch: {mismatches}")
    result = {"schema_version": "cyj.q2.v7.audit.v1", "status": "PASS",
              "original_A_open_events": len(reads["original_A"]),
              "derived_Q1_open_events": len(reads["derived_Q1"]),
              "approved_legacy_git_show_events": len(approved_git_show),
              "approved_legacy_git_show_paths": sorted(set(approved_git_show)),
              "unapproved_subprocess_launch_events": len(blocked_spawns),
              "scope": "Python open and subprocess-launch events during v7 imports and build; only pinned CHM v1.3 derived-file git show is allowed; native-library file access is outside Python audit coverage",
              "builder": built, "manifest_sha256": sha256(manifest_path)}
    (ROOT / "outputs/cyj/q2_v7_runtime_audit.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(main()))
