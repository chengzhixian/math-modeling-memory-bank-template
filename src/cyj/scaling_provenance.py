"""Verify classic-scaling inputs and code against one committed version."""

from __future__ import annotations

import json
from pathlib import Path

from audit_b_scaling_laws import ROOT, sha256


B_DATA_PREFIX = "data/raw/real_attachments/B_scaling_laws"


def verify_source_files(
    data_root: Path, manifest_path: Path, filenames: tuple[str, ...]
) -> dict[str, dict[str, int | str]]:
    """Reject source files whose bytes differ from the committed F manifest."""
    entries = json.loads(manifest_path.read_text(encoding="utf-8"))["files"]
    by_path = {entry["path"]: entry for entry in entries}
    if len(by_path) != len(entries):
        raise ValueError("duplicate paths in F_MANIFEST.json")
    verified: dict[str, dict[str, int | str]] = {}
    for filename in filenames:
        repository_path = f"{B_DATA_PREFIX}/{filename}"
        expected = by_path.get(repository_path)
        if expected is None:
            raise ValueError(f"source missing from F_MANIFEST.json: {repository_path}")
        path = data_root / filename
        actual_bytes = path.stat().st_size
        actual_sha256 = sha256(path)
        if actual_bytes != expected["bytes"] or actual_sha256 != expected["sha256"]:
            raise ValueError(f"source differs from F_MANIFEST.json: {repository_path}")
        verified[filename] = {
            "path": repository_path,
            "bytes": actual_bytes,
            "sha256": actual_sha256,
        }
    return verified


def verify_code_files(input_version: str, paths: tuple[str, ...]) -> None:
    """Check integrated producer bytes against the current main code manifest."""
    if input_version != "main-frozen-raw-v1":
        raise ValueError("unexpected integrated input version")
    manifest = json.loads((ROOT / "interfaces/Q2/code_manifest.json").read_text(encoding="utf-8"))
    for repository_path in paths:
        path = ROOT / repository_path
        if manifest["sha256"].get(repository_path) != sha256(path):
            raise ValueError(f"integrated producer code mismatch: {repository_path}")
