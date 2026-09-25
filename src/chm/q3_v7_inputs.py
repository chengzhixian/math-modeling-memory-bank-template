"""Read CYJ's immutable conditional v7 predictor without changing its files."""
from __future__ import annotations

import hashlib
import importlib
from pathlib import Path
import subprocess
import sys


CYJ_SHA = "895ad42de670ece04ba7e781817a2126ec34327e"
EXPECTED_Q1_SHA = "c621f7e405106e42720f918f490235b5e8becefb0f7c8cb997736e96337117a9"
EXPECTED_BOUNDS_SHA = "969f810c0bf54f03492afc243091c339aaf4b27aed5c2164c186e651c7589acc"
EXPECTED_B7_SHA = "d6f5b665d3806a322d0ebf87da46889822d2eff89324eacded6040383e7b6733"


def _sha256_lf(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def verify_release(
    cyj_root: Path,
    expected_release: str = CYJ_SHA,
    expected_q1: str = EXPECTED_Q1_SHA,
) -> dict:
    """Reject a moving producer or altered signed CHM inputs before import."""
    root = Path(cyj_root).resolve()
    result = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode or result.stdout.strip() != expected_release:
        raise ValueError("CYJ release SHA mismatch")
    paths = {
        "q1_sha": root / "interfaces/chm/q1_interface_v2.json",
        "bounds_sha": root / "outputs/chm/q1_v2_hull_bounds/bounds.json",
        "b7_sha": root / "outputs/cyj/q2_final/model_coefficients.json",
    }
    try:
        hashes = {key: _sha256_lf(path) for key, path in paths.items()}
    except OSError as exc:
        raise ValueError("CYJ release input missing") from exc
    if hashes["q1_sha"] != expected_q1:
        raise ValueError("Q1 manifest SHA mismatch")
    if hashes["bounds_sha"] != EXPECTED_BOUNDS_SHA:
        raise ValueError("Q1 hull bounds SHA mismatch")
    if hashes["b7_sha"] != EXPECTED_B7_SHA:
        raise ValueError("B7 coefficient SHA mismatch")
    return {"release_sha": result.stdout.strip(), **hashes}


def load_release(cyj_root: Path):
    """Load the producer only after exact Git and file identity checks pass."""
    root = Path(cyj_root).resolve()
    verify_release(root)
    module_dir = str(root / "src/cyj")
    sys.path.insert(0, module_dir)
    try:
        module = importlib.import_module("ndqp_scenarios_v7")
        if Path(module.__file__).resolve() != root / "src/cyj/ndqp_scenarios_v7.py":
            raise ValueError("CYJ v7 module loaded from a different checkout")
        return module.ConditionalV7(root=root)
    finally:
        sys.path.remove(module_dir)
