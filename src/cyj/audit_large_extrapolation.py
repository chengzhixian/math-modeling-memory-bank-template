"""Audit B9/B10 provenance and overlap; do not fit or validate a model."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import platform
import statistics
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data/raw/real_attachments/B_scaling_laws"
MANIFEST = ROOT / "data/raw/F_MANIFEST.json"
FIT = ROOT / "outputs/cyj/classic/classic_fit.json"
OUTPUT = ROOT / "outputs/cyj/diagnostics/b9_b10_extrapolation_audit.json"
FILES = {
    "B9": "supplementary_large_models.csv",
    "B10": "supplementary_large_baseline.csv",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def checked_rows(path: Path, expected: dict) -> list[dict[str, str]]:
    if path.stat().st_size != expected["bytes"] or sha256(path) != expected["sha256"]:
        raise ValueError(f"raw input differs from F_MANIFEST: {path.name}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise ValueError(f"missing or duplicated columns in {path.name}")
        rows = list(reader)
    if any(None in row for row in rows):
        raise ValueError(f"extra CSV fields in {path.name}")
    return rows


def positive(row: dict[str, str], field: str, *, allow_zero: bool = False) -> float:
    value = float(row[field])
    if not math.isfinite(value) or value < 0 or (value == 0 and not allow_zero):
        raise ValueError(f"invalid {field}: {value}")
    return value


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    expected = {entry["path"]: entry for entry in manifest["files"]}
    rows = {}
    file_meta = {}
    for label, name in FILES.items():
        path = DATA / name
        rel = path.relative_to(ROOT).as_posix()
        rows[label] = checked_rows(path, expected[rel])
        file_meta[label] = {"path": rel, "bytes": path.stat().st_size, "sha256": sha256(path)}

    b9 = {row["model_name"]: row for row in rows["B9"]}
    b10 = {row["family"]: row for row in rows["B10"]}
    if len(b9) != len(rows["B9"]) or len(b10) != len(rows["B10"]):
        raise ValueError("duplicate model name in B9 or B10")
    if set(b10) - set(b9):
        raise ValueError("B10 contains models absent from B9")

    for row in rows["B9"]:
        positive(row, "N_params_B")
        positive(row, "D_tokens_B", allow_zero=True)
        if row["FLOPs"]:
            positive(row, "FLOPs")
    for name, row in b10.items():
        n = positive(row, "N_params_B")
        d = positive(row, "D_tokens_B")
        positive(row, "val_loss")
        source = b9[name]
        if n != float(source["N_params_B"]) or d != float(source["D_tokens_B"]):
            raise ValueError(f"B9/B10 coordinate mismatch for {name}")

    fit = json.loads(FIT.read_text(encoding="utf-8"))
    if fit["status"] != "draft_classic_baseline_not_validated_predictor":
        raise ValueError("unexpected B1 fit status")
    p = fit["full_fit"]["parameters"]
    residuals = []
    coordinate_groups: dict[tuple[float, float], list[dict[str, str]]] = defaultdict(list)
    for row in rows["B10"]:
        n, d = float(row["N_params_B"]), float(row["D_tokens_B"])
        coordinate_groups[(n, d)].append(row)
        b1_curve = p["E"] + p["A"] * n ** -p["alpha"] + p["B"] * d ** -p["beta"]
        residuals.append(float(row["val_loss"]) - b1_curve)
    abs_residuals = list(map(abs, residuals))
    repeated = [group for group in coordinate_groups.values() if len(group) > 1]
    only_b9 = sorted(set(b9) - set(b10))
    result = {
        "schema_version": 1,
        "status": "descriptive_extrapolation_audit_not_validation",
        "provenance": {
            "script_sha256": sha256(Path(__file__)),
            "manifest_sha256": sha256(MANIFEST),
            "python_version": platform.python_version(),
            "raw_files": file_meta,
            "b1_fit_path": FIT.relative_to(ROOT).as_posix(),
            "b1_fit_sha256": sha256(FIT),
            "b1_fit_input_version": fit["input_version"],
        },
        "data_roles": {
            "B9": "reported_metadata_no_observed_loss_column",
            "B10": "estimated_loss_stress_reference_not_independent_test",
            "B1_curve": "draft_fit_descriptive_comparison_only",
        },
        "checks": {
            "B9_rows": len(rows["B9"]),
            "B10_rows": len(rows["B10"]),
            "B10_exact_name_and_coordinate_matches_B9": len(b10),
            "B9_unmatched_models": only_b9,
            "B9_unmatched_D_tokens_B": {name: float(b9[name]["D_tokens_B"]) for name in only_b9},
            "B9_zero_D_count": sum(float(row["D_tokens_B"]) == 0 for row in rows["B9"]),
            "B9_missing_FLOPs_count": sum(not row["FLOPs"] for row in rows["B9"]),
            "B10_N_params_B_range": [min(float(r["N_params_B"]) for r in rows["B10"]), max(float(r["N_params_B"]) for r in rows["B10"])],
            "B10_D_tokens_B_range": [min(float(r["D_tokens_B"]) for r in rows["B10"]), max(float(r["D_tokens_B"]) for r in rows["B10"])],
            "B10_above_B1_N_max_count": sum(float(r["N_params_B"]) > fit["data_scope"]["N_params_B_range"][1] for r in rows["B10"]),
            "B10_above_B1_D_max_count": sum(float(r["D_tokens_B"]) > fit["data_scope"]["D_tokens_B_range"][1] for r in rows["B10"]),
            "B10_below_B1_D_min_count": sum(float(r["D_tokens_B"]) < fit["data_scope"]["D_tokens_B_range"][0] for r in rows["B10"]),
            "B10_unique_ND_coordinates": len(coordinate_groups),
            "B10_repeated_ND_coordinate_groups": len(repeated),
            "B10_repeated_ND_extra_rows": sum(len(group) - 1 for group in repeated),
            "B10_repeated_ND_groups_with_identical_estimated_loss": sum(len({row["val_loss"] for row in group}) == 1 for group in repeated),
            "B10_minus_B1_curve_rmse_descriptive_only": math.sqrt(statistics.mean(x * x for x in residuals)),
            "B10_minus_B1_curve_mae_descriptive_only": statistics.mean(abs_residuals),
            "B10_minus_B1_curve_max_abs_descriptive_only": max(abs_residuals),
        },
        "gate": {
            "independent_external_validation": False,
            "reason": "B10 Loss is labelled estimated and shares B9 N/D coordinates; generation mechanism and Loss coordinate are unverified. Numerical agreement with a B1 fit is circular or otherwise non-independent until provenance is established.",
            "allowed_use": "B9 metadata support inventory and B10 clearly labelled estimated stress scenario only",
        },
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"PASS B9={len(b9)} B10={len(b10)} matched={len(b10)}; validation=false")


if __name__ == "__main__":
    main()
