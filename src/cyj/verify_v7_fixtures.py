"""Replay published v7 predictor and upstream-integrity request/expected pairs."""
from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from pathlib import Path

from chm_q1_v2_consumer import Q1V2Consumer
from ndqp_scenarios_v7 import ConditionalV7, _unique, request

ROOT = Path(__file__).resolve().parents[2]
FOLDER = ROOT / "interfaces/cyj/fixtures_v7"


def check_integrity(payload):
    mutation = payload["mutation"]
    if mutation == "manifest_identity":
        Q1V2Consumer(ROOT, expected_sha="0" * 64)
    elif mutation == "model_file_hash":
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = Path("interfaces/chm/q1_interface_v2.json")
            (root / manifest).parent.mkdir(parents=True)
            shutil.copy2(ROOT / manifest, root / manifest)
            source = Path("outputs/chm/q1_v2/interaction_coefficients_13_targets.json")
            (root / source).parent.mkdir(parents=True)
            (root / source).write_bytes((ROOT / source).read_bytes() + b" ")
            Q1V2Consumer(root)
    else:
        raise ValueError(f"unknown integrity fixture mutation: {mutation}")


def main():
    manifest = json.loads((FOLDER / "manifest.json").read_text(encoding="utf-8"))
    model = ConditionalV7(ROOT)
    for name, digest in manifest["files"].items():
        if hashlib.sha256((FOLDER / name).read_bytes()).hexdigest() != digest:
            raise ValueError(f"fixture hash mismatch: {name}")
    count = 0
    for path in FOLDER.glob("*.request.json"):
        expected = json.loads(path.with_name(path.name.replace(".request.json", ".expected.json")).read_text(encoding="utf-8"))
        payload = {}
        try:
            payload = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique)
            if payload.get("test_kind") == "consumer_integrity":
                check_integrity(payload)
                raise ValueError(f"invalid integrity fixture unexpectedly accepted: {path.name}")
            elif expected["exit_code"] == 0:
                actual = request(model, payload)
                if actual != expected["result"]:
                    raise ValueError(f"fixture output mismatch: {path.name}")
            else:
                request(model, payload)
                raise ValueError(f"invalid fixture unexpectedly accepted: {path.name}")
        except (ValueError, TypeError, KeyError) as exc:
            matches = (expected.get("error_contains", "") in str(exc) if payload.get("test_kind") == "consumer_integrity"
                       else str(exc) == expected.get("error_contains"))
            if expected["exit_code"] != 2 or not matches:
                raise ValueError(f"fixture error mismatch: {path.name}: {exc}") from exc
        count += 1
    if count != manifest["count"]:
        raise ValueError("fixture count mismatch")
    return {"status": "PASS", "fixtures": count, "Q1_manifest_sha256": model.q1.manifest_sha256}


if __name__ == "__main__":
    print(json.dumps(main()))
