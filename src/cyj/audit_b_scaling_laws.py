"""Audit attachment B without changing any source data.

The audit is intentionally descriptive.  It verifies file identity, tabular
shape, missing/duplicate records, documented row counts, and a small set of
unit/relationship checks.  It does not fit a scaling law or turn synthetic
records into observations.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import statistics
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_ROOT = ROOT / "data/raw/real_attachments/B_scaling_laws"
DEFAULT_MANIFEST = ROOT / "data/raw/F_MANIFEST.json"
DEFAULT_SOURCE_MANIFEST = ROOT / "data/raw/real_attachments/source_manifest.json"
DEFAULT_OUTPUT = ROOT / "outputs/cyj/b_data_audit.json"
B_DATA_PREFIX = Path("data/raw/real_attachments/B_scaling_laws")
FULL_COMMIT_RE = re.compile(r"[0-9a-fA-F]{40}")


DATASETS = {
    "B1": {
        "paths": ["pythia_training_log_existing.csv"],
        "nature": "observed",
        "role": "main_fit",
        "documented_rows": 1176,
    },
    "B2": {
        "paths": ["cerebras_training_log.csv"],
        "nature": "semi_synthetic",
        "role": "out_of_family_validation",
        "documented_rows": 1029,
    },
    "B3": {
        "glob": "training_trajectories/*.csv",
        "nature": "interpolated",
        "role": "trajectory_validation",
        "documented_files": 8,
        "documented_rows_per_file": 500,
        "documented_rows": 4000,
    },
    "B4": {
        "paths": ["scaling_baseline.csv"],
        "nature": "observed",
        "role": "cross_family_validation",
        "documented_rows": 57,
    },
    "B5": {
        "paths": ["published_scaling_data.csv"],
        "nature": "observed",
        "role": "literature_validation",
        "documented_rows": 44,
    },
    "B6": {
        "paths": ["supplementary_NQ_experiment.csv"],
        "nature": "semi_synthetic",
        "role": "quality_base",
        "documented_rows": 360,
    },
    "B7": {
        "paths": ["supplementary_NQ_experiment_expanded.csv"],
        "nature": "semi_synthetic",
        "role": "quality_expanded",
        "documented_rows": 450,
    },
    "B8": {
        "paths": ["supplementary_NQ_experiment_large.csv"],
        "nature": "semi_synthetic",
        "role": "quality_large_and_extrapolation",
        "documented_rows": 1704,
    },
    "B9": {
        "paths": ["supplementary_large_models.csv"],
        "nature": "reported_metadata",
        "role": "large_model_parameters",
        "documented_rows": 132,
    },
    "B10": {
        "paths": ["supplementary_large_baseline.csv"],
        "nature": "estimated",
        "role": "large_model_extrapolation",
        "documented_rows": 128,
    },
    "B11": {
        "paths": ["open_model_family_metadata.csv"],
        "nature": "reported_metadata",
        "role": "family_metadata",
        "documented_rows": 18,
    },
    "B12": {
        "paths": ["pythia_checkpoint_index.csv"],
        "nature": "observed_metadata",
        "role": "checkpoint_index",
        "documented_rows": 1386,
    },
}

REQUIRED_NUMERIC = {
    "pythia_training_log_existing.csv": [
        "N_params_B",
        "D_tokens_B",
        "C_FLOPs_1e21",
        "steps",
        "train_loss",
        "val_loss",
        "ppl",
    ],
    "cerebras_training_log.csv": [
        "N_params_B",
        "D_tokens_B",
        "C_FLOPs_1e21",
        "steps",
        "train_loss",
        "val_loss",
        "ppl",
    ],
    "scaling_baseline.csv": ["N_params_B", "D_tokens_B", "val_loss"],
    "published_scaling_data.csv": ["N_params_B", "D_tokens_B", "val_loss"],
    "supplementary_NQ_experiment.csv": [
        "N_params_B",
        "D_tokens_B",
        "Q_score",
        "val_loss",
    ],
    "supplementary_NQ_experiment_expanded.csv": [
        "N_params_B",
        "D_tokens_B",
        "Q_score",
        "val_loss",
    ],
    "supplementary_NQ_experiment_large.csv": [
        "N_params_B",
        "D_tokens_B",
        "Q_score",
        "val_loss",
    ],
    "supplementary_large_models.csv": ["N_params_B", "D_tokens_B", "FLOPs"],
    "supplementary_large_baseline.csv": ["N_params_B", "D_tokens_B", "val_loss"],
}

KEY_COLUMNS = {
    "pythia_training_log_existing.csv": ["run_id", "steps"],
    "cerebras_training_log.csv": ["run_id", "steps"],
    "scaling_baseline.csv": ["family", "N_params_B", "D_tokens_B"],
    "published_scaling_data.csv": ["family", "N_params_B", "D_tokens_B", "source"],
    "supplementary_NQ_experiment.csv": ["experiment_id"],
    "supplementary_NQ_experiment_expanded.csv": ["experiment_id"],
    "supplementary_NQ_experiment_large.csv": ["experiment_id"],
    "supplementary_large_models.csv": ["model_name"],
    "supplementary_large_baseline.csv": ["family"],
    "open_model_family_metadata.csv": ["model_repo"],
    "pythia_checkpoint_index.csv": ["model_repo", "branch"],
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_stdout(*args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(ROOT), *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "unknown Git error"
        raise ValueError(f"Git command failed ({' '.join(args)}): {detail}")
    return result.stdout.strip()


def validate_input_version(
    input_version: str, manifest: Path, source_manifest: Path
) -> str:
    if not FULL_COMMIT_RE.fullmatch(input_version):
        raise ValueError("--input-version must be a full 40-hex Git commit SHA")
    resolved = git_stdout("rev-parse", "--verify", f"{input_version}^{{commit}}")
    if resolved.lower() != input_version.lower():
        raise ValueError(
            f"--input-version did not resolve exactly: requested {input_version}, got {resolved}"
        )

    for label, path in (("manifest", manifest), ("source manifest", source_manifest)):
        resolved_path = path.resolve()
        try:
            repository_path = resolved_path.relative_to(ROOT).as_posix()
        except ValueError as exc:
            raise ValueError(
                f"{label} must be inside the repository to verify input provenance: {path}"
            ) from exc
        committed_blob = git_stdout("rev-parse", f"{resolved}:{repository_path}")
        working_blob = git_stdout(
            "hash-object", f"--path={repository_path}", str(resolved_path)
        )
        if committed_blob != working_blob:
            raise ValueError(
                f"{label} does not match input commit {resolved}: {repository_path}"
            )
    return resolved.lower()


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]], list[list[str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        try:
            header = next(reader)
        except StopIteration:
            return [], [], []
        raw_rows = [row for row in reader]
    rows = [dict(zip(header, row, strict=False)) for row in raw_rows]
    return header, rows, raw_rows


def parse_finite(value: str) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def numeric_summary(rows: list[dict[str, str]], column: str) -> dict[str, Any]:
    values = [row.get(column, "").strip() for row in rows]
    present = [value for value in values if value != ""]
    parsed = [parse_finite(value) for value in present]
    finite = [value for value in parsed if value is not None]
    return {
        "count": len(finite),
        "missing": len(values) - len(present),
        "invalid_or_nonfinite": len(parsed) - len(finite),
        "min": min(finite) if finite else None,
        "max": max(finite) if finite else None,
        "unique": len(set(finite)),
    }


def monotone(values: list[float], *, strict: bool = False) -> bool:
    pairs = zip(values, values[1:])
    return all(left < right if strict else left <= right for left, right in pairs)


def add_check(
    checks: list[dict[str, Any]],
    check_id: str,
    status: str,
    evidence: Any,
    note: str,
) -> None:
    checks.append(
        {"check_id": check_id, "status": status, "evidence": evidence, "note": note}
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--source-manifest", type=Path, default=DEFAULT_SOURCE_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--input-version", required=True)
    args = parser.parse_args()

    data_root = args.data_root.resolve()
    manifest_path = args.manifest.resolve()
    source_manifest_path = args.source_manifest.resolve()
    try:
        resolved_input_version = validate_input_version(
            args.input_version, manifest_path, source_manifest_path
        )
    except (OSError, ValueError) as exc:
        parser.error(str(exc))

    expected_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest_by_path = {entry["path"]: entry for entry in expected_manifest["files"]}
    source_manifest = json.loads(source_manifest_path.read_text(encoding="utf-8"))
    source_by_file = {
        entry["file"]: entry for entry in source_manifest if entry.get("problem") == "B"
    }

    file_reports: list[dict[str, Any]] = []
    checks: list[dict[str, Any]] = []
    rows_by_relative: dict[str, list[dict[str, str]]] = {}
    dataset_rows: Counter[str] = Counter()
    dataset_files: Counter[str] = Counter()

    expected_csv_paths = {
        Path(entry["path"]).relative_to(B_DATA_PREFIX).as_posix()
        for entry in expected_manifest["files"]
        if Path(entry["path"]).is_relative_to(B_DATA_PREFIX)
        and Path(entry["path"]).suffix.lower() == ".csv"
    }
    actual_csv_paths = {
        path.relative_to(data_root).as_posix()
        for path in data_root.rglob("*.csv")
        if path.is_file()
    }
    missing_csv_paths = sorted(expected_csv_paths - actual_csv_paths)
    unexpected_csv_paths = sorted(actual_csv_paths - expected_csv_paths)
    add_check(
        checks,
        "B_manifest_csv_inventory",
        "pass" if not missing_csv_paths and not unexpected_csv_paths else "fail",
        {
            "expected_files": len(expected_csv_paths),
            "actual_files": len(actual_csv_paths),
            "missing": missing_csv_paths,
            "unexpected": unexpected_csv_paths,
        },
        "The complete attachment B CSV path set must match F_MANIFEST.json",
    )

    for dataset_id, spec in DATASETS.items():
        if "glob" in spec:
            paths = sorted(data_root.glob(spec["glob"]))
        else:
            paths = [data_root / relative for relative in spec["paths"]]
        if not paths:
            add_check(checks, f"{dataset_id}_files_present", "fail", 0, "No files found")
            continue

        for path in paths:
            relative = path.relative_to(data_root).as_posix()
            repository_path = (
                Path("data/raw/real_attachments/B_scaling_laws") / relative
            ).as_posix()
            if not path.is_file():
                add_check(
                    checks,
                    f"{dataset_id}_{relative}_present",
                    "fail",
                    False,
                    "Required CSV is missing",
                )
                continue

            header, rows, raw_rows = read_csv(path)
            rows_by_relative[relative] = rows
            missing = {
                column: sum(row.get(column, "").strip() == "" for row in rows)
                for column in header
            }
            duplicate_rows = len(raw_rows) - len({tuple(row) for row in raw_rows})
            required_numeric = REQUIRED_NUMERIC.get(Path(relative).name, [])
            if dataset_id == "B3":
                required_numeric = [
                    "N_params_B",
                    "D_tokens_B",
                    "val_loss",
                    "step",
                    "interpolated",
                ]
            numeric = {
                column: numeric_summary(rows, column)
                for column in required_numeric
                if column in header
            }
            missing_required_columns = [
                column for column in required_numeric if column not in header
            ]
            actual_hash = sha256(path)
            expected = manifest_by_path.get(repository_path)
            identity_ok = bool(
                expected
                and expected["bytes"] == path.stat().st_size
                and expected["sha256"].lower() == actual_hash.lower()
            )
            source_entry = source_by_file.get(
                (Path("B_scaling_laws") / relative).as_posix(), {}
            )
            report = {
                "dataset_id": dataset_id,
                "nature": spec["nature"],
                "role": spec["role"],
                "path": repository_path,
                "bytes": path.stat().st_size,
                "sha256": actual_hash,
                "manifest_identity_match": identity_ok,
                "rows": len(rows),
                "columns": len(header),
                "header": header,
                "missing_by_column": missing,
                "duplicate_rows": duplicate_rows,
                "required_numeric": numeric,
                "missing_required_columns": missing_required_columns,
                "source_metadata": {
                    key: source_entry[key]
                    for key in ("source", "note")
                    if key in source_entry
                },
            }
            file_reports.append(report)
            dataset_rows[dataset_id] += len(rows)
            dataset_files[dataset_id] += 1

            add_check(
                checks,
                f"{dataset_id}_{Path(relative).stem}_manifest_identity",
                "pass" if identity_ok else "fail",
                {
                    "bytes": path.stat().st_size,
                    "sha256": actual_hash,
                    "manifest_entry_present": expected is not None,
                },
                "Byte count and SHA256 must match data/raw/F_MANIFEST.json",
            )
            numeric_invalid = {
                column: stats["invalid_or_nonfinite"]
                for column, stats in numeric.items()
                if stats["invalid_or_nonfinite"]
            }
            add_check(
                checks,
                f"{dataset_id}_{Path(relative).stem}_required_numeric",
                "pass" if not missing_required_columns and not numeric_invalid else "fail",
                {
                    "missing_columns": missing_required_columns,
                    "invalid_or_nonfinite": numeric_invalid,
                },
                "Required numeric fields must exist and contain finite values when populated",
            )
            add_check(
                checks,
                f"{dataset_id}_{Path(relative).stem}_exact_duplicate_rows",
                "pass" if duplicate_rows == 0 else "fail",
                duplicate_rows,
                "Exact duplicate source rows are not removed by this audit",
            )
            key_columns = (
                ["N_params_B", "D_tokens_B"]
                if dataset_id == "B3"
                else KEY_COLUMNS.get(Path(relative).name, [])
            )
            if key_columns and all(column in header for column in key_columns):
                keys = [tuple(row[column] for column in key_columns) for row in rows]
                duplicate_keys = len(keys) - len(set(keys))
                add_check(
                    checks,
                    f"{dataset_id}_{Path(relative).stem}_key_uniqueness",
                    "pass" if duplicate_keys == 0 else "fail",
                    {"key_columns": key_columns, "duplicate_keys": duplicate_keys},
                    "Candidate record keys must be unique before fitting or joining",
                )

    for dataset_id, spec in DATASETS.items():
        actual_rows = dataset_rows[dataset_id]
        expected_rows = spec["documented_rows"]
        add_check(
            checks,
            f"{dataset_id}_documented_row_count",
            "pass" if actual_rows == expected_rows else "warn",
            {"actual": actual_rows, "documented": expected_rows},
            "A mismatch is an input-documentation issue to resolve, not an automatic data error",
        )
        if dataset_id == "B3":
            per_file = sorted(
                report["rows"]
                for report in file_reports
                if report["dataset_id"] == "B3"
            )
            ok = (
                dataset_files[dataset_id] == spec["documented_files"]
                and per_file
                == [spec["documented_rows_per_file"]] * spec["documented_files"]
            )
            add_check(
                checks,
                "B3_file_and_per_file_counts",
                "pass" if ok else "warn",
                {"files": dataset_files[dataset_id], "rows_per_file": per_file},
                "Data description states 8 trajectory files with 500 rows each",
            )

    for relative in ("pythia_training_log_existing.csv", "cerebras_training_log.csv"):
        rows = rows_by_relative.get(relative, [])
        stem = Path(relative).stem
        if not rows:
            add_check(
                checks,
                f"{stem}_compute_identity",
                "fail",
                {"rows": 0},
                "Cannot check C=6ND without source rows",
            )
            add_check(
                checks,
                f"{stem}_ppl_exp_loss",
                "fail",
                {"rows": 0},
                "Cannot check ppl against exp(val_loss) without source rows",
            )
            continue
        ratios = []
        ppl_errors = []
        for row in rows:
            n_value = parse_finite(row["N_params_B"])
            d_value = parse_finite(row["D_tokens_B"])
            c_value = parse_finite(row["C_FLOPs_1e21"])
            loss = parse_finite(row["val_loss"])
            ppl = parse_finite(row["ppl"])
            if (
                n_value is not None
                and n_value > 0
                and d_value is not None
                and d_value > 0
                and c_value is not None
            ):
                ratios.append(c_value / (0.006 * n_value * d_value))
            if loss is not None and ppl not in (None, 0):
                try:
                    expected_ppl = math.exp(loss)
                except OverflowError:
                    expected_ppl = math.inf
                ppl_errors.append(abs(expected_ppl - ppl) / ppl)
        add_check(
            checks,
            f"{stem}_compute_identity",
            "pass" if ratios and 0.95 <= statistics.median(ratios) <= 1.05 else "warn",
            {
                "median_C_over_6ND": statistics.median(ratios),
                "min": min(ratios),
                "max": max(ratios),
                "formula": "C_FLOPs_1e21 / (0.006 * N_params_B * D_tokens_B)",
            },
            "N and D are in billions; C is in 1e21 FLOPs",
        )
        add_check(
            checks,
            f"{stem}_ppl_exp_loss",
            "pass" if ppl_errors and max(ppl_errors) <= 0.001 else "warn",
            {
                "median_relative_error": statistics.median(ppl_errors),
                "max_relative_error": max(ppl_errors),
            },
            "Checks ppl against exp(val_loss), allowing source rounding",
        )

    trajectory_results = []
    for relative, rows in rows_by_relative.items():
        if not relative.startswith("training_trajectories/"):
            continue
        n_values = [parse_finite(row.get("N_params_B", "")) for row in rows]
        d_values = [parse_finite(row.get("D_tokens_B", "")) for row in rows]
        steps = [parse_finite(row.get("step", "")) for row in rows]
        numeric_ok = all(value is not None for value in n_values + d_values + steps)
        trajectory_results.append(
            {
                "path": relative,
                "constant_N": numeric_ok and len(set(n_values)) == 1,
                "nondecreasing_D": numeric_ok and monotone(d_values),
                "nondecreasing_step": numeric_ok and monotone(steps),
                "interpolated_values": sorted(
                    {row.get("interpolated", "") for row in rows}
                ),
            }
        )
    trajectory_ok = bool(trajectory_results) and all(
        item["constant_N"]
        and item["nondecreasing_D"]
        and item["nondecreasing_step"]
        and item["interpolated_values"] == ["1"]
        for item in trajectory_results
    )
    add_check(
        checks,
        "B3_trajectory_structure",
        "pass" if trajectory_ok else "fail",
        trajectory_results,
        "Each interpolated trajectory keeps N fixed and orders D and step monotonically",
    )

    nq_ids = {
        dataset_id: {
            row["experiment_id"]
            for relative, rows in rows_by_relative.items()
            if any(
                report["dataset_id"] == dataset_id and report["path"].endswith(relative)
                for report in file_reports
            )
            for row in rows
            if "experiment_id" in row
        }
        for dataset_id in ("B6", "B7", "B8")
    }
    add_check(
        checks,
        "B6_subset_B7_experiment_ids",
        "pass" if nq_ids["B6"] <= nq_ids["B7"] else "warn",
        {
            "B6_ids": len(nq_ids["B6"]),
            "B7_ids": len(nq_ids["B7"]),
            "B6_not_in_B7": sorted(nq_ids["B6"] - nq_ids["B7"])[:20],
        },
        "Checks whether the expanded N-Q table retains all base experiment IDs",
    )
    b8_rows = rows_by_relative.get("supplementary_NQ_experiment_large.csv", [])
    b8_labels_present = bool(b8_rows) and all("data_type" in row for row in b8_rows)
    add_check(
        checks,
        "B8_data_type_counts",
        "pass" if b8_labels_present else "fail",
        dict(
            sorted(Counter(row.get("data_type", "") for row in b8_rows).items())
        ),
        "Reported as labels only; these categories are not reclassified by the audit",
    )

    large_models = {
        row["model_name"]
        for row in rows_by_relative.get("supplementary_large_models.csv", [])
        if "model_name" in row
    }
    large_baseline = {
        row["family"]
        for row in rows_by_relative.get("supplementary_large_baseline.csv", [])
        if "family" in row
    }
    add_check(
        checks,
        "B9_B10_model_key_coverage",
        "pass"
        if large_models and large_baseline and large_baseline <= large_models
        else "fail",
        {
            "B9_unique_model_names": len(large_models),
            "B10_unique_families": len(large_baseline),
            "B10_not_in_B9": sorted(large_baseline - large_models),
            "B9_without_B10": sorted(large_models - large_baseline),
        },
        "Compares B10 estimated-loss keys with B9 reported model metadata",
    )
    b2_rows = rows_by_relative.get("cerebras_training_log.csv", [])
    operational_columns = ("gpu_days", "step_time_ms", "grad_norm_avg")
    b2_missing_operational_columns = [
        column
        for column in operational_columns
        if not b2_rows or any(column not in row for row in b2_rows)
    ]
    b2_empty_operational = {
        column: sum(row.get(column, "").strip() == "" for row in b2_rows)
        for column in operational_columns
        if column not in b2_missing_operational_columns
    }
    add_check(
        checks,
        "B2_optional_operational_columns",
        "fail"
        if b2_missing_operational_columns
        else ("warn" if any(b2_empty_operational.values()) else "pass"),
        {
            **b2_empty_operational,
            **(
                {"missing_columns": b2_missing_operational_columns}
                if b2_missing_operational_columns
                else {}
            ),
        },
        "These columns are not required for N-D-Loss fitting but cannot support runtime diagnostics",
    )
    b9_rows = rows_by_relative.get("supplementary_large_models.csv", [])
    b9_zero_d = sorted(
        row.get("model_name", "")
        for row in b9_rows
        if (parse_finite(row.get("D_tokens_B", "")) or math.inf) <= 0
    )
    b9_missing_flops = sorted(
        row.get("model_name", "")
        for row in b9_rows
        if row.get("FLOPs", "").strip() == ""
    )
    add_check(
        checks,
        "B9_modeling_readiness",
        "warn" if b9_zero_d or b9_missing_flops else "pass",
        {
            "nonpositive_D_tokens_B_models": b9_zero_d,
            "missing_FLOPs_models": b9_missing_flops,
        },
        "Nonpositive D is not treated as a measured zero; incomplete rows need exclusion or sourced repair",
    )
    b9_control_whitespace = sorted(
        repr(row.get("model_name", ""))
        for row in b9_rows
        if any(
            character in row.get("model_name", "")
            for character in ("\n", "\r", "\t")
        )
    )
    add_check(
        checks,
        "B9_model_name_control_whitespace",
        "warn" if b9_control_whitespace else "pass",
        b9_control_whitespace,
        "Model keys are reported verbatim; normalization must be explicit before joins",
    )

    status_counts = Counter(check["status"] for check in checks)
    output = {
        "schema_version": 1,
        "role": "cyj",
        "task": "P01 attachment B audit",
        "input_version": args.input_version,
        "data_root": data_root.relative_to(ROOT).as_posix(),
        "source_policy": {
            "observed_and_reported": ["B1", "B4", "B5", "B9", "B11", "B12"],
            "semi_synthetic": ["B2", "B6", "B7", "B8"],
            "estimated": ["B10"],
            "interpolated": ["B3"],
            "note": "Labels follow the visible data description; the audit does not upgrade evidence classes.",
        },
        "summary": {
            "csv_files": len(file_reports),
            "rows": sum(report["rows"] for report in file_reports),
            "bytes": sum(report["bytes"] for report in file_reports),
            "dataset_rows": dict(sorted(dataset_rows.items())),
            "check_status_counts": dict(sorted(status_counts.items())),
        },
        "files": file_reports,
        "checks": checks,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    outcome = "FAIL" if status_counts.get("fail", 0) else "PASS"
    print(
        f"{outcome}: audited "
        f"{output['summary']['csv_files']} CSV files / {output['summary']['rows']} rows; "
        f"checks={dict(sorted(status_counts.items()))}; output={args.output}"
    )
    return 1 if status_counts.get("fail", 0) else 0


if __name__ == "__main__":
    raise SystemExit(main())
