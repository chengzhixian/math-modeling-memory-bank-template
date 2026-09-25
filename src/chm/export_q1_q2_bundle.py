"""Q1 production stage: publish frozen CHM outputs and normalized A4 recipes.

This is deliberately outside src/cyj.  It reads raw A4 once as a Q1 export,
using the row normalization in CHM q3_p_support.load_a4.  Q2 consumes only the
versioned outputs of this script; no Q1 model is refitted here.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / "outputs/chm/q1_exports/q1_q2_bundle_v1"
SOURCE_COMMIT = "cdda1ad62c5c7eb72b413c4228caeff87d2bad30"
AUDIT_COMMIT = "2450971d15b7f6516d6db408759bf1b22f497808"
A4 = ROOT / "data/raw/real_attachments/A_data_value/regmix_tables/train_mixture_1m.csv"
A4_SHA256 = "04a32ef4ab594376bf90e11404c033668f887c351d6a03ad3744824c7296a2d8"
MANIFEST = "interfaces/chm/q1_interface_v1_3.json"
AUDIT_FILES = {
    "heldout_target_metrics.csv": "outputs/chm/q1_mixture_final/heldout_target_metrics.csv",
    "paired_scale_metrics.csv": "outputs/chm/q1_mixture_final/same_mixture_1m_60m.csv",
    "mixture_model_selection.csv": "outputs/chm/q1_mixture_final/interaction_candidate_comparison.csv",
    "composition_support.csv": "outputs/chm/q1_mixture_final/composition_support.csv",
    "q3_p_support_summary.json": "outputs/chm/q3_p_support_summary.json",
}


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def git_blob(commit: str, path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=ROOT)


def csv_rows(raw: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))


def dump_json(path: Path, obj: object) -> None:
    path.write_bytes((json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8"))


def export() -> dict:
    DEST.mkdir(parents=True, exist_ok=True)
    official = json.loads(git_blob(SOURCE_COMMIT, MANIFEST))
    if official.get("schema_version") != "chm.q1.v1.3":
        raise ValueError("unexpected frozen Q1 schema")
    file_names = {"quality": "quality.csv", "mapping": "mapping.csv",
                  "coefficients": "coefficients.csv", "reference": "reference.csv",
                  "validation": "validation.csv"}
    output_source = {}
    source_tables = {}
    for key, name in file_names.items():
        item = official["files"][key]
        raw = git_blob(SOURCE_COMMIT, item["path"])
        normalized = raw.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
        if sha(normalized) != item["sha256"] or len(csv_rows(raw)) != item["rows"]:
            raise ValueError(f"frozen Q1 identity failed: {key}")
        (DEST / name).write_bytes(normalized)
        output_source[name] = {"commit": SOURCE_COMMIT, "path": item["path"]}
        source_tables[key] = csv_rows(raw)
    domains = [r["mixture_domain"] for r in source_tables["reference"]]
    if len(domains) != 17 or len(set(domains)) != 17:
        raise ValueError("expected 17 unique Q1 domains")

    raw_a4 = A4.read_bytes()
    if sha(raw_a4) != A4_SHA256:
        raise ValueError("raw A4 SHA does not match CHM's published audit")
    a4 = csv_rows(raw_a4)
    if len(a4) != 512:
        raise ValueError("expected 512 A4 recipes")
    raw_columns = list(a4[0])
    if raw_columns[0] != "index" or [x.removeprefix("train_the_pile_") for x in raw_columns[1:]] != domains:
        raise ValueError("A4 column order differs from frozen Q1 order")
    seen, recipe_rows, raw_sums, changes = set(), [], [], []
    for row in a4:
        idx = row["index"]
        if not idx or idx in seen:
            raise ValueError("missing or duplicate A4 index")
        seen.add(idx)
        values = [float(row[c]) for c in raw_columns[1:]]
        total = math.fsum(values)
        if any(not math.isfinite(v) or v < 0 for v in values) or total <= 0:
            raise ValueError("invalid A4 mixture")
        normalized = [v / total for v in values]
        raw_sums.append(total)
        changes.append(math.fsum(abs(a - b) for a, b in zip(normalized, values)))
        recipe_rows.append({"index": idx, **dict(zip(domains, normalized))})
    with (DEST / "recipes_512.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["index", *domains], lineterminator="\n")
        writer.writeheader()
        writer.writerows(recipe_rows)
    dump_json(DEST / "recipe_manifest.json", {
        "schema_version": "chm.q1.q2_recipes.v1", "producer_stage": "Q1_export_not_Q2_raw_read",
        "source_commit": AUDIT_COMMIT, "frozen_q1_commit": SOURCE_COMMIT,
        "raw_A4_path": str(A4.relative_to(ROOT)).replace("\\", "/"),
        "raw_A4_sha256": A4_SHA256, "rows": 512, "domain_order": domains,
        "normalization": "each nonnegative raw row divided by its row sum; CHM q3_p_support.load_a4 semantics",
        "raw_sum_min": min(raw_sums), "raw_sum_max": max(raw_sums),
        "max_normalization_l1": max(changes),
        "recipes_sha256": sha((DEST / "recipes_512.csv").read_bytes()),
    })

    quality = {(r["quality_domain"], r["dataset_scope"]): r for r in source_tables["quality"]}
    mapped = []
    for r in source_tables["mapping"]:
        domain, qdomain = r["mixture_domain"], r["quality_domain"]
        preferred = "arxiv_extended" if qdomain == "arxiv" else "github_extended" if qdomain == "github" else "sample"
        qrow = quality.get((qdomain, preferred)) or quality.get((qdomain, "sample"))
        mapped.append({"mixture_domain": domain, "quality_domain": qdomain,
                       "mapping_type": r["mapping_type"],
                       "mapping_confidence": r["mapping_confidence"],
                       "Q_A": float(qrow["Q"]) if qrow else None,
                       "Q_A_dataset_scope": qrow["dataset_scope"] if qrow else None})
    dump_json(DEST / "qa_mapping.json", {
        "schema_version": "chm.q1.q2_quality_policy.v1", "coordinate": official["quality_coordinate"],
        "B_Q_mapping": "unidentified; Q_A only constrains p policy", "rows": mapped})

    for name, source_path in AUDIT_FILES.items():
        raw = git_blob(AUDIT_COMMIT, source_path)
        (DEST / name).write_bytes(raw.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n").encode("utf-8"))
        output_source[name] = {"commit": AUDIT_COMMIT, "path": source_path}
    manifest = {
        "schema_version": "chm.q1.q2_bundle.v1", "status": "Q1_derived_export_pending_CHM_owner_signoff",
        "generation_command": "python -B src/chm/export_q1_q2_bundle.py",
        "frozen_q1_commit": SOURCE_COMMIT, "audit_commit": AUDIT_COMMIT,
        "frozen_q1_manifest_sha256": sha(git_blob(SOURCE_COMMIT, MANIFEST)),
        "source_A4_sha256": A4_SHA256, "source_files": output_source,
        "interaction_model": "diagnostic metrics only; full 13-target second-order coefficients unavailable",
        "exporter_code_sha256": sha(Path(__file__).read_bytes()),
        "files_sha256": {p.name: sha(p.read_bytes()) for p in sorted(DEST.iterdir()) if p.name != "export_manifest.json"},
    }
    dump_json(DEST / "export_manifest.json", manifest)
    return {"path": str(DEST.relative_to(ROOT)).replace("\\", "/"),
            "rows": len(recipe_rows), "files": len(manifest["files_sha256"]),
            "manifest_sha256": sha((DEST / "export_manifest.json").read_bytes())}


if __name__ == "__main__":
    print(json.dumps(export(), ensure_ascii=False))
