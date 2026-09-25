"""Verify classic-scaling inputs and code against one committed version."""

from __future__ import annotations

import json
from pathlib import Path

from audit_b_scaling_laws import ROOT, git_stdout, sha256


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
    """Ensure the executing code is exactly the code named by input_version."""
    for repository_path in paths:
        path = ROOT / repository_path
        committed_blob = git_stdout("rev-parse", f"{input_version}:{repository_path}")
        working_blob = git_stdout(
            "hash-object", f"--path={repository_path}", str(path)
        )
        if committed_blob != working_blob:
            raise ValueError(
                f"code differs from input commit {input_version}: {repository_path}"
            )
