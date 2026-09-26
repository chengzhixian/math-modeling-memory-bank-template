"""Replay every frozen v8 request/expected pair through the public parser."""
from __future__ import annotations

import hashlib
import json
import math

from chm_q1_v2_consumer import ROOT
from ndqp_scenarios_v8 import ConditionalV8, request, unique

OUT = ROOT / "interfaces/Q2/fixtures_v8"


def matches_expected(expected, actual):
    """Compare frozen structure and identity exactly, float results by roundoff."""
    if type(expected) is not type(actual):
        return False
    if isinstance(expected, dict):
        return expected.keys() == actual.keys() and all(
            matches_expected(expected[key], actual[key]) for key in expected)
    if isinstance(expected, list):
        return len(expected) == len(actual) and all(
            matches_expected(left, right) for left, right in zip(expected, actual))
    if isinstance(expected, float):
        return math.isfinite(expected) and math.isfinite(actual) and math.isclose(
            expected, actual, rel_tol=1e-12, abs_tol=1e-12)
    return expected == actual


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
                if not matches_expected(expected["result"], request(model, payload)):
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
