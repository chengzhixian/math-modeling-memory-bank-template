"""Replay every frozen v8 request/expected pair through the public parser."""
from __future__ import annotations

import hashlib
import json

from chm_q1_v2_consumer import ROOT
from ndqp_scenarios_v8 import ConditionalV8, request, unique

OUT = ROOT / "interfaces/cyj/fixtures_v8"


def main():
    manifest = json.loads((OUT/"manifest.json").read_text(encoding="utf-8"))
    model = ConditionalV8()
    if manifest["quality_fit_sha256"] != model.quality_fit_sha256:
        raise ValueError("v8 fixture quality fit changed")
    for name, digest in manifest["files"].items():
        if hashlib.sha256((OUT/name).read_bytes()).hexdigest() != digest:
            raise ValueError(f"v8 fixture file hash mismatch: {name}")
    count = 0
    for path in OUT.glob("*.request.json"):
        expected = json.loads(path.with_name(path.name.replace(".request.json", ".expected.json"))
                              .read_text(encoding="utf-8"))
        try:
            payload = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique)
            if expected["exit_code"] == 0:
                if request(model, payload) != expected["result"]:
                    raise ValueError("valid fixture output changed")
            else:
                request(model, payload)
                raise ValueError("invalid fixture unexpectedly accepted")
        except (ValueError, KeyError, TypeError) as exc:
            if expected["exit_code"] != 2 or str(exc) != expected["error_contains"]:
                raise ValueError(f"v8 fixture mismatch: {path.name}: {exc}") from exc
        count += 1
    if count != manifest["count"]:
        raise ValueError("v8 fixture count mismatch")
    return {"status": "PASS", "fixtures": count}


if __name__ == "__main__":
    print(json.dumps(main()))
