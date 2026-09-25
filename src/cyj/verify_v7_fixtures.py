"""Replay every published v7 fixture through the public request parser."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ndqp_scenarios_v7 import ConditionalV7, _unique, request

ROOT = Path(__file__).resolve().parents[2]
FOLDER = ROOT / "interfaces/cyj/fixtures_v7"


def main():
    manifest = json.loads((FOLDER / "manifest.json").read_text(encoding="utf-8"))
    model = ConditionalV7(ROOT)
    for name, digest in manifest["files"].items():
        if hashlib.sha256((FOLDER / name).read_bytes()).hexdigest() != digest:
            raise ValueError(f"fixture hash mismatch: {name}")
    count = 0
    for path in FOLDER.glob("*.request.json"):
        expected = json.loads(path.with_name(path.name.replace(".request.json", ".expected.json")).read_text(encoding="utf-8"))
        payload = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique)
        if expected["exit_code"] == 0:
            actual = request(model, payload)
            if actual != expected["result"]:
                raise ValueError(f"fixture output mismatch: {path.name}")
        else:
            try:
                request(model, payload)
            except (ValueError, TypeError, KeyError) as exc:
                if str(exc) != expected["error_contains"]:
                    raise ValueError(f"fixture error mismatch: {path.name}") from exc
            else:
                raise ValueError(f"invalid fixture unexpectedly accepted: {path.name}")
        count += 1
    if count != manifest["count"]:
        raise ValueError("fixture count mismatch")
    return {"status": "PASS", "fixtures": count, "Q1_manifest_sha256": model.q1.manifest_sha256}


if __name__ == "__main__":
    print(json.dumps(main()))
