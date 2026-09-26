"""Load accepted Q2 v8 predictor and Q1 evidence from this main tree.

The original CHM release used a detached CYJ Git export. This integration
checks accepted data identities but resolves code from the current tree.
"""
from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
EXPORT = ROOT
CYJ_V8_SHA = "fd2dbb3b2002983430329cdb2ec6a275c2eed4f6"
Q1_SHA = "c621f7e405106e42720f918f490235b5e8becefb0f7c8cb997736e96337117a9"
B1_SHA = "9b0e381fbc0ea84bb37d63ccb273733f3a03a0c2a834e8ef52cdb75c45bc6ead"
B7_QUALITY_SHA = "30819a5931b0552c1ef207f52f489f9d4ecaf427166bec25a98ce7319ac3d07b"
PINNED_FILES = (
    "src/chm/q1_interface_v2.py",
    "src/cyj/chm_q1_v2_consumer.py",
    "src/cyj/fit_b7_quality_extension_from_b1.py",
    "src/cyj/ndqp_scenarios_v8.py",
    "interfaces/Q1/q1_interface_v2.json",
    "outputs/Q1/hull_bounds.json",
    "outputs/Q2/classic_fit.json",
    "outputs/Q2/b7_quality_extension.json",
    "outputs/Q2/main_policy.json",
    "outputs/Q2/acceptance.json",
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def verify_export(export: Path = EXPORT) -> dict:
    export = Path(export).resolve()
    actual = {}
    for relative in PINNED_FILES:
        path = export / relative
        if not path.is_file():
            raise ValueError(f"missing integrated Q1/Q2 file: {relative}")
        if relative.startswith("src/") and export != ROOT and path.read_bytes() != (ROOT / relative).read_bytes():
            raise ValueError(f"integrated producer file changed: {relative}")
        actual[relative] = digest(path)
    for relative, expected in (
        ("interfaces/Q1/q1_interface_v2.json", Q1_SHA),
        ("outputs/Q2/classic_fit.json", B1_SHA),
        ("outputs/Q2/b7_quality_extension.json", B7_QUALITY_SHA),
    ):
        if actual[relative] != expected:
            raise ValueError(f"accepted Q1/Q2 identity mismatch: {relative}")
    acceptance = json.loads((export / "outputs/Q2/acceptance.json").read_text(encoding="utf-8"))
    if not acceptance["q3_consumer_interface_ready"] or acceptance["cross_source_empirical_calibration_complete"]:
        raise ValueError("Q2 v8 scientific status changed")
    return {"Q2_source_commit": CYJ_V8_SHA, "Q1_manifest_sha256": Q1_SHA,
            "B1_fit_sha256": B1_SHA, "B7_quality_fit_sha256": B7_QUALITY_SHA,
            "verified_files": actual}


def load_v8(export: Path = EXPORT):
    export = Path(export).resolve()
    verify_export(export)
    module_path = str(export / "src/cyj")
    sys.path.insert(0, module_path)
    try:
        module = importlib.import_module("ndqp_scenarios_v8")
        if Path(module.__file__).resolve() != export / "src/cyj/ndqp_scenarios_v8.py":
            raise ValueError("Q2 Python predictor loaded from a different checkout")
        model = module.ConditionalV8(root=export)
        return model, module.BOUNDS
    finally:
        sys.path.remove(module_path)
