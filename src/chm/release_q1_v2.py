"""Verify the frozen Q1 v2 release after intermediate-file cleanup.

The original one-time publishing inputs were removed from this lean branch.
This command checks every file against the immutable v2 manifest and reports
the release identity. It does not refit or silently republish a model.
"""
from pathlib import Path
import json
from q1_interface_v2 import Q1Interface

ROOT = Path(__file__).resolve().parents[2]


def release():
    model = Q1Interface(ROOT)
    return {
        "schema_version": model.manifest["schema_version"],
        "manifest_sha256": model.manifest_sha256,
        "verified_files": {k: v["path"] for k, v in model.manifest["files"].items()},
        "status": "frozen release verified; no model refit",
    }


if __name__ == "__main__":
    print(json.dumps(release(), ensure_ascii=False, indent=2))
