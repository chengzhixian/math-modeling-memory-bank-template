"""Independently check CYJ's two Q1 upstream exports against frozen CHM data.

This is an owner review, not a new model fit or a Q2 acceptance test.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data/raw/real_attachments/A_data_value/regmix_tables"
BASE = ROOT / "outputs/chm/q1_exports"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def check() -> dict:
    q = BASE / "q1_q2_bundle_v1"
    inter = BASE / "q1_interaction_bundle_v1"
    qm = json.loads((q / "export_manifest.json").read_text(encoding="utf-8"))
    im = json.loads((inter / "interaction_manifest.json").read_text(encoding="utf-8"))
    frozen = json.loads((ROOT / "interfaces/chm/q1_interface_v1_3.json").read_text(encoding="utf-8"))
    assert qm["schema_version"] == "chm.q1.q2_bundle.v1"
    assert im["schema_version"] == "chm.q1.interaction_bundle.v1"
    assert frozen["schema_version"] == "chm.q1.v1.3"
    assert qm["frozen_q1_commit"] == "cdda1ad62c5c7eb72b413c4228caeff87d2bad30"
    assert qm["audit_commit"] == im["candidate_source_commit"] == "2450971d15b7f6516d6db408759bf1b22f497808"
    for folder, manifest in ((q, qm), (inter, im)):
        for name, expected in manifest["files_sha256"].items():
            assert digest(folder / name) == expected, name
    assert digest(RAW / "train_mixture_1m.csv") == qm["source_A4_sha256"]
    assert digest(RAW / "train_pile_loss_1m.csv") == im["source_A4_A5_sha256"]["train_pile_loss_1m.csv"]
    for key, alias in (("quality", "quality.csv"), ("mapping", "mapping.csv"),
                       ("coefficients", "coefficients.csv"), ("reference", "reference.csv"),
                       ("validation", "validation.csv")):
        item = frozen["files"][key]
        canonical = (ROOT / item["path"]).read_bytes().decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n").encode()
        assert hashlib.sha256(canonical).hexdigest() == item["sha256"]
        assert hashlib.sha256(canonical).hexdigest() == digest(q / alias)
    a4 = read_csv(RAW / "train_mixture_1m.csv")
    recipe = read_csv(q / "recipes_512.csv")
    a5 = read_csv(RAW / "train_pile_loss_1m.csv")
    domains = [r["mixture_domain"] for r in read_csv(q / "reference.csv")]
    assert len(a4) == len(recipe) == len(a5) == 512
    assert [r["index"] for r in a4] == [r["index"] for r in recipe] == [r["index"] for r in a5]
    assert [c.removeprefix("train_the_pile_") for c in a4[0] if c != "index"] == domains
    raw = np.array([[float(row["train_the_pile_" + d]) for d in domains] for row in a4])
    exported = np.array([[float(row[d]) for d in domains] for row in recipe])
    assert np.isfinite(raw).all() and (raw >= 0).all()
    max_recipe_error = float(np.max(np.abs(raw / raw.sum(axis=1, keepdims=True) - exported)))
    assert max_recipe_error < 1e-14
    selected = np.argsort(np.var(exported, axis=0))[-5:]
    features = json.loads((inter / "interaction_feature_definition.json").read_text(encoding="utf-8"))
    assert features["selected_domain_order"] == [domains[i] for i in selected]
    assert len(features["pairs_order"]) == 10
    coefs = json.loads((inter / "interaction_coefficients_13_targets.json").read_text(encoding="utf-8"))["targets"]
    assert len(coefs) == 13 and all(len(row["main"]) == 17 and len(row["pairs"]) == 10 for row in coefs.values())
    cv = read_csv(inter / "interaction_cv_summary.csv")
    max_cv_error = max(float(row["max_abs_cv_diff"]) for row in cv)
    assert len(cv) == 13 and max_cv_error < 1e-10
    official_primary = {r["quality_domain"]: r for r in read_csv(ROOT / "outputs/chm/domain_quality.csv") if r["dataset_scope"] == "sample"}
    qa = json.loads((q / "qa_mapping.json").read_text(encoding="utf-8"))["rows"]
    scope_differences = []
    for row in qa:
        if row["mapping_type"] == "inferred":
            assert row["Q_A"] is None
            continue
        primary = official_primary[row["quality_domain"]]
        if row["Q_A_dataset_scope"] != "sample" or abs(float(row["Q_A"]) - float(primary["Q"])) > 1e-12:
            scope_differences.append({"mixture_domain": row["mixture_domain"],
                                      "export_scope": row["Q_A_dataset_scope"],
                                      "primary_scope": "sample", "export_Q_A": row["Q_A"],
                                      "primary_Q_A": float(primary["Q"])})
    return {"status": "IDENTITY_PASS_WITH_QA_SCOPE_DIFFERENCE" if scope_differences else "PASS",
            "frozen_q1_version": "chm.q1.v1.3", "q1_recipe_count": len(recipe),
            "max_recipe_abs_error": max_recipe_error, "interaction_target_count": len(coefs),
            "max_interaction_cv_error": max_cv_error,
            "qa_primary_scope_differences": scope_differences,
            "q1_export_manifest_sha256": digest(q / "export_manifest.json"),
            "interaction_export_manifest_sha256": digest(inter / "interaction_manifest.json")}


if __name__ == "__main__":
    print(json.dumps(check(), ensure_ascii=False, indent=2))
