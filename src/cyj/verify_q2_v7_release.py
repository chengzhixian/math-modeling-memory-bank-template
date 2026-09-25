"""Record a verified remote checkpoint for an already accepted Q2 v7 bundle.

Run only after committing and pushing the accepted bundle. This second-stage
record avoids putting the publishing commit SHA inside that same commit.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/cyj/q2_v7"
RECORD = ROOT / "outputs/cyj/q2_v7_release_verification.json"
BRANCH = "team/cyj-scaling"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(["git", "-c", "http.sslBackend=openssl", *args],
                                   cwd=ROOT, text=True, timeout=60).strip()


def write(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
                    encoding="utf-8", newline="\n")


def main() -> dict:
    if git("branch", "--show-current") != BRANCH:
        raise ValueError("Q2 release verification must run on the CYJ branch")
    if git("status", "--porcelain=v1"):
        raise ValueError("Q2 release verification requires a clean committed bundle")
    if RECORD.exists():
        raise ValueError("Q2 release record already exists; do not overwrite it")
    head = git("rev-parse", "HEAD")
    remote_rows = git("ls-remote", "origin", f"refs/heads/{BRANCH}").splitlines()
    if len(remote_rows) != 1 or remote_rows[0].split()[0] != head:
        raise ValueError("Q2 release commit is not verified at the remote branch HEAD")
    manifest_path = OUT / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for name, expected in manifest["files"].items():
        if digest(OUT / name) != expected:
            raise ValueError(f"Q2 bundle changed after acceptance: {name}")
    acceptance_path = OUT / "acceptance.json"
    acceptance = json.loads(acceptance_path.read_text(encoding="utf-8"))
    if not (acceptance["q2_implementation_complete"] and
            acceptance["q2_answer_complete_under_stated_assumptions"] and
            acceptance["q3_consumer_interface_ready"] and
            not acceptance["release_remote_verified"]):
        raise ValueError("Q2 bundle is not in the accepted pre-release state")
    record = {"schema_version": "cyj.q2.v7.remote_verification.v1",
              "status": "PASS", "branch": BRANCH,
              "verified_subject_commit": head, "remote_subject_commit": head,
              "verified_at_utc": datetime.now(timezone.utc).isoformat(),
              "subject_manifest_sha256": digest(manifest_path),
              "subject_acceptance_sha256": digest(acceptance_path),
              "scope": "pre-release accepted bundle commit verified on origin; final record commit must be pushed and checked separately"}
    write(RECORD, record)
    acceptance["release_remote_verified"] = True
    acceptance["release_subject_commit"] = head
    acceptance["release_evidence_path"] = str(RECORD.relative_to(ROOT)).replace("\\", "/")
    acceptance["evidence_paths"].append(acceptance["release_evidence_path"])
    write(acceptance_path, acceptance)
    manifest["files"]["acceptance.json"] = digest(acceptance_path)
    manifest["code_sha256"]["verify_q2_v7_release.py"] = digest(ROOT / "src/cyj/verify_q2_v7_release.py")
    write(manifest_path, manifest)
    return {"status": "PASS", "verified_subject_commit": head,
            "post_release_manifest_sha256": digest(manifest_path)}


if __name__ == "__main__":
    print(json.dumps(main()))
