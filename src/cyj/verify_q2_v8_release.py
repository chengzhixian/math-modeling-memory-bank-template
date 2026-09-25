"""Verify the accepted v8 subject commit before recording its remote release."""
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone

from chm_q1_v2_consumer import ROOT, sha256

OUT = ROOT / "outputs/cyj/q2_v8"
RECORD = ROOT / "outputs/cyj/q2_v8_release_verification.json"
BRANCH = "team/cyj-scaling"


def git(*args):
    return subprocess.check_output(["git", "-c", "http.sslBackend=openssl", *args],
                                   cwd=ROOT, text=True, timeout=60).strip()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+"\n",
                    encoding="utf-8", newline="\n")


def main():
    if git("branch", "--show-current") != BRANCH:
        raise ValueError("v8 release must run on the CYJ branch")
    if git("status", "--porcelain=v1", "--untracked-files=all") != "?? src/cyj/verify_q2_v8_release.py":
        raise ValueError("v8 release requires only its new verification script uncommitted")
    if RECORD.exists():
        raise ValueError("v8 release record already exists")
    head = git("rev-parse", "HEAD")
    rows = git("ls-remote", "origin", f"refs/heads/{BRANCH}").splitlines()
    if len(rows) != 1 or rows[0].split()[0] != head:
        raise ValueError("accepted v8 subject commit is not the remote branch HEAD")
    manifest_path = OUT / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if any(sha256(OUT/name) != digest for name, digest in manifest["files"].items()):
        raise ValueError("accepted v8 manifest files have changed")
    acceptance_path = OUT / "acceptance.json"
    acceptance = json.loads(acceptance_path.read_text(encoding="utf-8"))
    if not (acceptance["q2_implementation_complete"] and
            acceptance["q2_competition_requirements_complete"] and
            acceptance["q3_consumer_interface_ready"] and
            not acceptance["release_remote_verified"]):
        raise ValueError("v8 acceptance is not in pre-release state")
    record = {"schema_version": "cyj.q2.v8.remote_verification.v1", "status": "PASS",
              "branch": BRANCH, "verified_subject_commit": head, "remote_subject_commit": head,
              "verified_at_utc": datetime.now(timezone.utc).isoformat(),
              "subject_manifest_sha256": sha256(manifest_path),
              "subject_acceptance_sha256": sha256(acceptance_path),
              "scope": "accepted v8 subject commit verified on origin; release-record commit must be pushed and checked separately"}
    write(RECORD, record)
    acceptance["release_remote_verified"] = True
    acceptance["release_subject_commit"] = head
    acceptance["release_evidence_path"] = str(RECORD.relative_to(ROOT)).replace("\\", "/")
    acceptance["evidence_paths"].append(acceptance["release_evidence_path"])
    acceptance["status"] = "conditional_v8_competition_requirements_complete_remote_verified_pending_CHM_consumption"
    write(acceptance_path, acceptance)
    manifest["files"]["acceptance.json"] = sha256(acceptance_path)
    manifest["code_sha256"]["verify_q2_v8_release.py"] = sha256(ROOT/"src/cyj/verify_q2_v8_release.py")
    write(manifest_path, manifest)
    return {"status": "PASS", "verified_subject_commit": head,
            "post_release_manifest_sha256": sha256(manifest_path)}


if __name__ == "__main__":
    print(json.dumps(main()))
