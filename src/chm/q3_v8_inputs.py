"""Load the exact CYJ v8 conditional predictor from a local detached export.

The export is made with ``git archive <commit>``. Only derived Q1 and Q2 files
are needed; the original A/B attachments are never read by this consumer.
"""
from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
CYJ_V8_SHA = "fd2dbb3b2002983430329cdb2ec6a275c2eed4f6"
CYJ_V8_SUBJECT = "615c078517379284f6b0504c568790a7975c6eda"
Q1_SHA = "c621f7e405106e42720f918f490235b5e8becefb0f7c8cb997736e96337117a9"
B1_SHA = "9b0e381fbc0ea84bb37d63ccb273733f3a03a0c2a834e8ef52cdb75c45bc6ead"
B7_QUALITY_SHA = "30819a5931b0552c1ef207f52f489f9d4ecaf427166bec25a98ce7319ac3d07b"
EXPORT = ROOT / ".upstream/cyj-v8"
PINNED_FILES = (
    "src/chm/q1_interface_v2.py",
    "src/cyj/chm_q1_v2_consumer.py",
    "src/cyj/fit_b7_quality_extension_from_b1.py",
    "src/cyj/ndqp_scenarios_v8.py",
    "interfaces/chm/q1_interface_v2.json",
    "outputs/chm/q1_v2_hull_bounds/bounds.json",
    "outputs/cyj/classic/classic_fit.json",
    "outputs/cyj/q2_v8/b7_quality_extension.json",
    "outputs/cyj/q2_v8/main_policy.json",
    "outputs/cyj/q2_v8/manifest.json",
    "outputs/cyj/q2_v8/acceptance.json",
    "outputs/cyj/q2_v8_release_verification.json",
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def verify_export(export: Path = EXPORT) -> dict:
    export = Path(export).resolve()
    actual = {}
    for relative in PINNED_FILES:
        path = export / relative
        if not path.is_file():
            raise ValueError(f"missing CYJ v8 export file: {relative}")
        subject = subprocess.run(["git", "show", f"{CYJ_V8_SHA}:{relative}"],
                                 cwd=ROOT, capture_output=True, check=True).stdout
        if path.read_bytes() != subject:
            raise ValueError(f"CYJ v8 export differs from pinned Git object: {relative}")
        actual[relative] = digest(path)
    if actual["interfaces/chm/q1_interface_v2.json"] != Q1_SHA:
        raise ValueError("Q1 v2 identity mismatch")
    if actual["outputs/cyj/classic/classic_fit.json"] != B1_SHA:
        raise ValueError("B1 identity mismatch")
    if actual["outputs/cyj/q2_v8/b7_quality_extension.json"] != B7_QUALITY_SHA:
        raise ValueError("B7 quality identity mismatch")
    record = json.loads((export / "outputs/cyj/q2_v8_release_verification.json").read_text(encoding="utf-8"))
    if record["status"] != "PASS" or record["verified_subject_commit"] != CYJ_V8_SUBJECT:
        raise ValueError("CYJ v8 release record is not the accepted subject")
    acceptance = json.loads((export / "outputs/cyj/q2_v8/acceptance.json").read_text(encoding="utf-8"))
    if not acceptance["q3_consumer_interface_ready"] or acceptance["cross_source_empirical_calibration_complete"]:
        raise ValueError("CYJ v8 scientific state changed")
    return {"CYJ_v8_commit": CYJ_V8_SHA, "release_subject": CYJ_V8_SUBJECT,
            "Q1_manifest_sha256": Q1_SHA, "B1_fit_sha256": B1_SHA,
            "B7_quality_fit_sha256": B7_QUALITY_SHA, "verified_files": actual}


def load_v8(export: Path = EXPORT):
    verify_export(export)
    module_path = str(Path(export).resolve() / "src/cyj")
    sys.path.insert(0, module_path)
    try:
        module = importlib.import_module("ndqp_scenarios_v8")
        if Path(module.__file__).resolve() != Path(export).resolve() / "src/cyj/ndqp_scenarios_v8.py":
            raise ValueError("CYJ v8 Python module loaded from a different checkout")
        model = module.ConditionalV8(root=Path(export).resolve())
        return model, module.BOUNDS
    finally:
        sys.path.remove(module_path)
