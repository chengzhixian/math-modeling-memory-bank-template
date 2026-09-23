"""Prepare leakage-aware B1 inputs and a local-evidence Loss comparability table."""

from __future__ import annotations

import argparse
import csv
import json
import math
import platform
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from audit_b_scaling_laws import (
    DEFAULT_DATA_ROOT,
    DEFAULT_MANIFEST,
    DEFAULT_SOURCE_MANIFEST,
    ROOT,
    sha256,
    validate_input_version,
)
from scaling_provenance import verify_code_files, verify_source_files


DEFAULT_OUTPUT_DIR = ROOT / "outputs/cyj/classic"
B1_FILENAME = "pythia_training_log_existing.csv"
B4_FILENAME = "scaling_baseline.csv"
B5_FILENAME = "published_scaling_data.csv"
TAIL_FRACTION = 0.30
COMPUTE_IDENTITY_REL_TOL = 0.05


def read_dict_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def prepare_b1_rows(
    source_rows: list[dict[str, str]], *, tail_fraction: float = TAIL_FRACTION
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not 0 < tail_fraction < 1:
        raise ValueError("tail_fraction must lie strictly between zero and one")
    grouped: dict[str, list[tuple[int, dict[str, str]]]] = defaultdict(list)
    for source_line, row in enumerate(source_rows, start=2):
        n_value = float(row["N_params_B"])
        d_value = float(row["D_tokens_B"])
        loss = float(row["val_loss"])
        if not all(math.isfinite(value) and value > 0 for value in (n_value, d_value, loss)):
            raise ValueError(f"nonpositive/nonfinite B1 core value at CSV line {source_line}")
        grouped[row["N_params_B"]].append((source_line, row))

    prepared: list[dict[str, Any]] = []
    group_manifest: list[dict[str, Any]] = []
    for group_index, (n_text, group_rows) in enumerate(
        sorted(grouped.items(), key=lambda item: float(item[0])), start=1
    ):
        ordered = sorted(group_rows, key=lambda item: (float(item[1]["D_tokens_B"]), int(item[1]["steps"])))
        if len({row["D_tokens_B"] for _, row in ordered}) != len(ordered):
            raise ValueError(f"duplicate D within B1 model-size group {n_text}")
        split_index = math.floor((1.0 - tail_fraction) * len(ordered))
        split_index = min(max(split_index, 1), len(ordered) - 1)
        train_rows = ordered[:split_index]
        tail_rows = ordered[split_index:]
        group_id = f"N={n_text}B"
        group_manifest.append(
            {
                "group_index": group_index,
                "group_id": group_id,
                "N_params_B": float(n_text),
                "rows": len(ordered),
                "token_tail_train_rows": len(train_rows),
                "token_tail_test_rows": len(tail_rows),
                "token_tail_last_train_D_tokens_B": float(train_rows[-1][1]["D_tokens_B"]),
                "token_tail_first_test_D_tokens_B": float(tail_rows[0][1]["D_tokens_B"]),
            }
        )
        for trajectory_rank, (source_line, row) in enumerate(ordered, start=1):
            n_value = float(row["N_params_B"])
            d_value = float(row["D_tokens_B"])
            c_value = float(row["C_FLOPs_1e21"])
            compute_ratio = c_value / (0.006 * n_value * d_value)
            prepared.append(
                {
                    "sample_id": f"B1:{n_text}:{row['steps']}",
                    "source_csv_line": source_line,
                    "source_run_id": row["run_id"],
                    "group_id": group_id,
                    "group_index": group_index,
                    "trajectory_rank": trajectory_rank,
                    "N_params_B": n_value,
                    "D_tokens_B": d_value,
                    "val_loss": float(row["val_loss"]),
                    "C_FLOPs_1e21": c_value,
                    "steps": int(row["steps"]),
                    "compute_ratio_C_over_6ND": compute_ratio,
                    "compute_identity_outlier": int(
                        abs(compute_ratio - 1.0) > COMPUTE_IDENTITY_REL_TOL
                    ),
                    "token_tail_split": "train"
                    if trajectory_rank <= split_index
                    else "test",
                }
            )

    sample_ids = [row["sample_id"] for row in prepared]
    if len(sample_ids) != len(set(sample_ids)):
        raise ValueError("prepared B1 sample_id values are not unique")
    return prepared, group_manifest


def comparability_rows(data_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for dataset, filename, stratum_column in (
        ("B4", B4_FILENAME, "family"),
        ("B5", B5_FILENAME, "source"),
    ):
        source_rows = read_dict_rows(data_root / filename)
        counts = Counter(row[stratum_column] for row in source_rows)
        for stratum, count in sorted(counts.items()):
            rows.append(
                {
                    "dataset": dataset,
                    "stratum_type": stratum_column,
                    "stratum": stratum,
                    "rows": count,
                    "tokenizer": "not_documented_in_local_attachment",
                    "evaluation_corpus": "not_documented_in_local_attachment",
                    "loss_definition": "validation_cross_entropy_label_only",
                    "unit": "not_documented_in_local_attachment",
                    "absolute_loss_comparable_to_B1": "not_established",
                    "evidence_scope": "visible_data_description_and_local_csv_only",
                    "allowed_current_use": "source_stratified_descriptive_prediction_only",
                    "note": "Do not pool external RMSE until tokenizer, corpus, loss definition, and unit are evidenced.",
                }
            )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--source-manifest", type=Path, default=DEFAULT_SOURCE_MANIFEST)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--input-version", required=True)
    parser.add_argument("--tail-fraction", type=float, default=TAIL_FRACTION)
    args = parser.parse_args()

    data_root = args.data_root.resolve()
    manifest_path = args.manifest.resolve()
    source_manifest_path = args.source_manifest.resolve()
    resolved_input_version = validate_input_version(
        args.input_version, manifest_path, source_manifest_path
    )
    verify_code_files(
        resolved_input_version,
        (
            "src/cyj/audit_b_scaling_laws.py",
            "src/cyj/scaling_provenance.py",
            "src/cyj/prepare_scaling_data.py",
        ),
    )
    source_files = verify_source_files(
        data_root,
        manifest_path,
        (B1_FILENAME, B4_FILENAME, B5_FILENAME),
    )
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    b1_path = data_root / B1_FILENAME
    prepared_rows, group_manifest = prepare_b1_rows(
        read_dict_rows(b1_path), tail_fraction=args.tail_fraction
    )
    prepared_path = output_dir / "prepared_b1.csv"
    prepared_fields = list(prepared_rows[0])
    write_csv(prepared_path, prepared_fields, prepared_rows)

    comparability_path = output_dir / "b4_b5_loss_comparability.csv"
    comparison_rows = comparability_rows(data_root)
    write_csv(comparability_path, list(comparison_rows[0]), comparison_rows)

    script_path = Path(__file__).resolve()
    split_counts = Counter(row["token_tail_split"] for row in prepared_rows)
    manifest = {
        "schema_version": 2,
        "status": "prepared_no_model_fit",
        "input_version": resolved_input_version,
        "provenance": {
            "git_commit": resolved_input_version,
            "code_files_verified_against_input_commit": True,
            "script_sha256": sha256(script_path),
            "source_files": source_files,
            "input_manifest_sha256": sha256(manifest_path),
            "source_manifest_sha256": sha256(source_manifest_path),
            "python_version": platform.python_version(),
        },
        "split_policy": {
            "group_key": "N_params_B",
            "group_rationale": "B1 has 1176 row-unique run_id values; model size is the evidenced repeated-trajectory grouping key.",
            "random_row_split_allowed": False,
            "token_tail_fraction_requested": args.tail_fraction,
            "token_tail_rule": "within each N group, sort by D then steps; floor((1-tail_fraction)*n) rows train, remaining rows test",
        },
        "summary": {
            "rows": len(prepared_rows),
            "groups": len(group_manifest),
            "token_tail_split_counts": dict(sorted(split_counts.items())),
            "compute_identity_outliers": sum(
                row["compute_identity_outlier"] for row in prepared_rows
            ),
        },
        "groups": group_manifest,
        "outputs": {
            "prepared_b1": {
                "path": prepared_path.relative_to(ROOT).as_posix(),
                "bytes": prepared_path.stat().st_size,
                "sha256": sha256(prepared_path),
            },
            "b4_b5_loss_comparability": {
                "path": comparability_path.relative_to(ROOT).as_posix(),
                "bytes": comparability_path.stat().st_size,
                "sha256": sha256(comparability_path),
                "rows": len(comparison_rows),
                "absolute_comparability": "not_established",
            },
        },
    }
    manifest_path_out = output_dir / "classic_data_manifest.json"
    with manifest_path_out.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")

    print(
        "PASS: prepared "
        f"{len(prepared_rows)} B1 rows / {len(group_manifest)} groups; "
        f"tail_split={dict(sorted(split_counts.items()))}; "
        "B4/B5 absolute comparability=not_established"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
