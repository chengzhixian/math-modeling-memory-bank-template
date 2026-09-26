"""Fit and validate the classic positive N-D scaling-law baseline."""

from __future__ import annotations

import argparse
import csv
import json
import platform
from pathlib import Path
from typing import Any

import numpy as np

from audit_b_scaling_laws import (
    DEFAULT_DATA_ROOT,
    DEFAULT_MANIFEST,
    DEFAULT_SOURCE_MANIFEST,
    ROOT,
    display_path,
    sha256,
    validate_input_version,
)
from prepare_scaling_data import (
    B1_FILENAME,
    B4_FILENAME,
    B5_FILENAME,
    prepare_b1_rows,
    read_dict_rows,
)
from scaling_common import (
    extrapolation_distance,
    fit_classic,
    fit_log_linear_baseline,
    predict_classic,
    regression_metrics,
)
from scaling_provenance import verify_code_files, verify_source_files


DEFAULT_PREPARED = ROOT / "data/processed/Q2/classic/prepared_b1.csv"
DEFAULT_DATA_MANIFEST = ROOT / "data/processed/Q2/classic/classic_data_manifest.json"
DEFAULT_OUTPUT_DIR = ROOT / "outputs/Q2"


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"refusing to write empty CSV: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def arrays(rows: list[dict[str, str]]) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    n_values = np.array([float(row["N_params_B"]) for row in rows], dtype=float)
    d_values = np.array([float(row["D_tokens_B"]) for row in rows], dtype=float)
    losses = np.array([float(row["val_loss"]) for row in rows], dtype=float)
    groups = np.array([row["group_id"] for row in rows], dtype=str)
    return n_values, d_values, losses, groups


def fit_and_predict(
    train_rows: list[dict[str, str]],
    test_rows: list[dict[str, str]],
    *,
    seed: int,
    starts: int,
    max_iterations: int,
) -> tuple[dict[str, Any], np.ndarray, dict[str, float]]:
    train_n, train_d, train_loss, train_groups = arrays(train_rows)
    result = fit_classic(
        train_n,
        train_d,
        train_loss,
        train_groups,
        seed=seed,
        starts=starts,
        max_iterations=max_iterations,
    )
    test_n, test_d, test_loss, _ = arrays(test_rows)
    predictions = predict_classic(result.parameters, test_n, test_d)
    metrics = regression_metrics(test_loss, predictions)
    return result.to_dict(), predictions, metrics


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepared", type=Path, default=DEFAULT_PREPARED)
    parser.add_argument("--data-manifest", type=Path, default=DEFAULT_DATA_MANIFEST)
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--source-manifest", type=Path, default=DEFAULT_SOURCE_MANIFEST)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--input-version", default="main-frozen-raw-v1")
    parser.add_argument("--seed", type=int, default=20260924)
    parser.add_argument("--full-starts", type=int, default=24)
    parser.add_argument("--cv-starts", type=int, default=8)
    parser.add_argument("--max-iterations", type=int, default=1600)
    args = parser.parse_args()

    resolved_input_version = validate_input_version(
        args.input_version, args.manifest.resolve(), args.source_manifest.resolve()
    )
    verify_code_files(
        resolved_input_version,
        (
            "src/cyj/audit_b_scaling_laws.py",
            "src/cyj/scaling_provenance.py",
            "src/cyj/prepare_scaling_data.py",
            "src/cyj/scaling_common.py",
            "src/cyj/fit_classic_scaling.py",
        ),
    )
    source_files = verify_source_files(
        args.data_root.resolve(),
        args.manifest.resolve(),
        (B1_FILENAME, B4_FILENAME, B5_FILENAME),
    )
    prepared_path = args.prepared.resolve()
    data_manifest_path = args.data_manifest.resolve()
    data_manifest = json.loads(data_manifest_path.read_text(encoding="utf-8"))
    if data_manifest["input_version"] != resolved_input_version:
        raise ValueError("prepared-data input version does not match requested version")
    expected_prepared_hash = data_manifest["outputs"]["prepared_b1"]["sha256"]
    if sha256(prepared_path) != expected_prepared_hash:
        raise ValueError("prepared B1 hash does not match classic_data_manifest.json")
    if data_manifest["provenance"]["source_files"] != source_files:
        raise ValueError("prepared-data source files do not match current verified sources")

    rows = read_rows(prepared_path)
    expected_rows, _ = prepare_b1_rows(
        read_dict_rows(args.data_root.resolve() / B1_FILENAME),
        tail_fraction=data_manifest["split_policy"]["token_tail_fraction_requested"],
    )
    if len(rows) != len(expected_rows) or any(
        actual != {key: str(value) for key, value in expected.items()}
        for actual, expected in zip(rows, expected_rows, strict=True)
    ):
        raise ValueError("prepared B1 rows do not match verified B1 source and split policy")
    n_values, d_values, losses, groups = arrays(rows)
    group_names = sorted(set(groups), key=lambda value: float(value[2:-1]))

    full_result = fit_classic(
        n_values,
        d_values,
        losses,
        groups,
        seed=args.seed,
        starts=args.full_starts,
        max_iterations=args.max_iterations,
    )
    full_predictions = predict_classic(full_result.parameters, n_values, d_values)
    full_metrics = regression_metrics(losses, full_predictions)
    m0_parameters, m0_predictions = fit_log_linear_baseline(
        n_values, d_values, losses, groups
    )
    m0_metrics = regression_metrics(losses, m0_predictions)

    predictions_rows: list[dict[str, Any]] = []
    for row, prediction, m0_prediction in zip(
        rows, full_predictions, m0_predictions, strict=True
    ):
        actual = float(row["val_loss"])
        predictions_rows.append(
            {
                **row,
                "classic_prediction": float(prediction),
                "classic_residual_pred_minus_actual": float(prediction - actual),
                "m0_prediction": float(m0_prediction),
                "m0_residual_pred_minus_actual": float(m0_prediction - actual),
            }
        )

    cv_rows: list[dict[str, Any]] = []
    loso_prediction_rows: list[dict[str, Any]] = []
    for fold_index, held_out_group in enumerate(group_names, start=1):
        train_rows = [row for row in rows if row["group_id"] != held_out_group]
        test_rows = [row for row in rows if row["group_id"] == held_out_group]
        result, predictions, metrics = fit_and_predict(
            train_rows,
            test_rows,
            seed=args.seed + fold_index,
            starts=args.cv_starts,
            max_iterations=args.max_iterations,
        )
        cv_rows.append(
            {
                "protocol": "leave_one_model_size_out",
                "fold": fold_index,
                "held_out_group": held_out_group,
                "train_rows": len(train_rows),
                "test_rows": len(test_rows),
                **metrics,
                "optimizer_converged": result["converged"],
                "optimizer_objective": result["objective"],
                **{
                    f"parameter_{name}": value
                    for name, value in result["parameters"].items()
                },
            }
        )
        for row, prediction in zip(test_rows, predictions, strict=True):
            loso_prediction_rows.append(
                {
                    "protocol": "leave_one_model_size_out",
                    "fold": fold_index,
                    "held_out_group": held_out_group,
                    "sample_id": row["sample_id"],
                    "N_params_B": row["N_params_B"],
                    "D_tokens_B": row["D_tokens_B"],
                    "actual_loss": row["val_loss"],
                    "predicted_loss": float(prediction),
                    "residual_pred_minus_actual": float(
                        prediction - float(row["val_loss"])
                    ),
                }
            )

    tail_train = [row for row in rows if row["token_tail_split"] == "train"]
    tail_test = [row for row in rows if row["token_tail_split"] == "test"]
    tail_result, tail_predictions, tail_metrics = fit_and_predict(
        tail_train,
        tail_test,
        seed=args.seed + 100,
        starts=args.cv_starts,
        max_iterations=args.max_iterations,
    )
    cv_rows.append(
        {
            "protocol": "token_tail_70_30",
            "fold": 1,
            "held_out_group": "all_groups_tail",
            "train_rows": len(tail_train),
            "test_rows": len(tail_test),
            **tail_metrics,
            "optimizer_converged": tail_result["converged"],
            "optimizer_objective": tail_result["objective"],
            **{
                f"parameter_{name}": value
                for name, value in tail_result["parameters"].items()
            },
        }
    )
    tail_prediction_rows = [
        {
            "protocol": "token_tail_70_30",
            "sample_id": row["sample_id"],
            "group_id": row["group_id"],
            "N_params_B": row["N_params_B"],
            "D_tokens_B": row["D_tokens_B"],
            "actual_loss": row["val_loss"],
            "predicted_loss": float(prediction),
            "residual_pred_minus_actual": float(
                prediction - float(row["val_loss"])
            ),
        }
        for row, prediction in zip(tail_test, tail_predictions, strict=True)
    ]

    data_root = args.data_root.resolve()
    n_min, n_max = float(n_values.min()), float(n_values.max())
    d_min, d_max = float(d_values.min()), float(d_values.max())
    external_rows: list[dict[str, Any]] = []
    for dataset, filename in (
        ("B4", B4_FILENAME),
        ("B5", B5_FILENAME),
    ):
        source_rows = read_rows(data_root / filename)
        external_n = np.array([float(row["N_params_B"]) for row in source_rows])
        external_d = np.array([float(row["D_tokens_B"]) for row in source_rows])
        external_predictions = predict_classic(
            full_result.parameters, external_n, external_d
        )
        distances = extrapolation_distance(
            external_n,
            external_d,
            n_min=n_min,
            n_max=n_max,
            d_min=d_min,
            d_max=d_max,
        )
        for row, prediction, distance in zip(
            source_rows, external_predictions, distances, strict=True
        ):
            external_rows.append(
                {
                    "dataset": dataset,
                    "family": row.get("family", ""),
                    "source": row.get("source", ""),
                    "N_params_B": row["N_params_B"],
                    "D_tokens_B": row["D_tokens_B"],
                    "reported_val_loss": row["val_loss"],
                    "classic_prediction": float(prediction),
                    "raw_difference_not_a_validated_error": float(
                        prediction - float(row["val_loss"])
                    ),
                    "is_ND_extrapolation": bool(distance > 0),
                    "ND_extrapolation_distance_log_space": float(distance),
                    "comparison_status": "descriptive_only_absolute_loss_comparability_not_established",
                }
            )

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    output_paths = {
        "classic_predictions": output_dir / "classic_predictions.csv",
        "classic_cv": output_dir / "classic_cv.csv",
        "classic_loso_predictions": output_dir / "classic_loso_predictions.csv",
        "classic_token_tail_predictions": output_dir
        / "classic_token_tail_predictions.csv",
        "external_predictions_unvalidated": output_dir
        / "external_predictions_unvalidated.csv",
    }
    write_csv(output_paths["classic_predictions"], predictions_rows)
    write_csv(output_paths["classic_cv"], cv_rows)
    write_csv(output_paths["classic_loso_predictions"], loso_prediction_rows)
    write_csv(
        output_paths["classic_token_tail_predictions"], tail_prediction_rows
    )
    write_csv(output_paths["external_predictions_unvalidated"], external_rows)

    loso_metrics = {
        metric: {
            "mean": float(np.mean([row[metric] for row in cv_rows[:-1]])),
            "std": float(np.std([row[metric] for row in cv_rows[:-1]], ddof=0)),
            "min": float(np.min([row[metric] for row in cv_rows[:-1]])),
            "max": float(np.max([row[metric] for row in cv_rows[:-1]])),
        }
        for metric in ("rmse", "mae", "mape", "r2", "log_rmse")
    }
    near_exact_threshold = 0.001
    near_exact_reconstruction = bool(
        full_metrics["rmse"] < near_exact_threshold
        and loso_metrics["rmse"]["mean"] < near_exact_threshold
        and tail_metrics["rmse"] < near_exact_threshold
    )
    external_descriptive_summary = {
        dataset: {
            "rows": len(dataset_rows),
            "ND_extrapolation_rows": sum(
                row["is_ND_extrapolation"] for row in dataset_rows
            ),
            "raw_difference_min": float(
                min(
                    row["raw_difference_not_a_validated_error"]
                    for row in dataset_rows
                )
            ),
            "raw_difference_max": float(
                max(
                    row["raw_difference_not_a_validated_error"]
                    for row in dataset_rows
                )
            ),
            "raw_absolute_difference_max": float(
                max(
                    abs(row["raw_difference_not_a_validated_error"])
                    for row in dataset_rows
                )
            ),
        }
        for dataset in ("B4", "B5")
        if (dataset_rows := [row for row in external_rows if row["dataset"] == dataset])
    }
    script_path = Path(__file__).resolve()
    result_document = {
        "schema_version": 2,
        "status": "draft_classic_baseline_not_validated_predictor",
        "input_version": resolved_input_version,
        "model": "L(N,D) = E + A*N^(-alpha) + B*D^(-beta)",
        "fit_loss": "group-equal weighted Huber loss on log(predicted_loss)-log(actual_loss)",
        "provenance": {
            "git_commit": resolved_input_version,
            "code_files_verified_against_input_commit": True,
            "script_sha256": sha256(script_path),
            "prepared_b1_sha256": sha256(prepared_path),
            "classic_data_manifest_sha256": sha256(data_manifest_path),
            "source_files": source_files,
            "python_version": platform.python_version(),
            "numpy_version": np.__version__,
        },
        "data_scope": {
            "rows": len(rows),
            "groups": group_names,
            "N_params_B_range": [n_min, n_max],
            "D_tokens_B_range": [d_min, d_max],
            "val_loss_range": [float(losses.min()), float(losses.max())],
            "group_weighting": "each N_params_B group has equal total fit weight",
            "compute_identity_outliers_retained": True,
            "reason": "classic fit uses N,D,Loss; C-identity warnings remain flagged for sensitivity and were not silently deleted",
        },
        "full_fit": {
            **full_result.to_dict(),
            "metrics": full_metrics,
        },
        "m0_log_linear_baseline": {
            "model": "Loss = intercept + b_N*log(N) + b_D*log(D)",
            "parameters": m0_parameters,
            "metrics": m0_metrics,
        },
        "validation": {
            "leave_one_model_size_out": {
                "folds": len(group_names),
                "aggregate": loso_metrics,
                "random_row_split_used": False,
            },
            "token_tail_70_30": {
                "train_rows": len(tail_train),
                "test_rows": len(tail_test),
                "metrics": tail_metrics,
                "fit": tail_result,
            },
            "B4_B5": {
                "absolute_loss_comparability": "not_established",
                "aggregate_error_metrics_reported": False,
                "predictions_status": "descriptive_only",
                "descriptive_summary_not_error_metrics": external_descriptive_summary,
            },
        },
        "diagnostics": {
            "near_exact_reconstruction_threshold_rmse": near_exact_threshold,
            "near_exact_reconstruction_triggered": near_exact_reconstruction,
            "interpretation": (
                "Near-exact B1 reconstruction across in-sample, leave-one-size-out, and token-tail checks may indicate shared deterministic construction or strong preprocessing. It is not evidence of independent real-world generalization."
                if near_exact_reconstruction
                else "Near-exact reconstruction diagnostic not triggered."
            ),
            "ready_for_Q3": False,
            "ready_for_Q3_reason": "Classic B1-only draft lacks evidenced B4/B5 absolute Loss comparability, Q/p calibration, and uncertainty intervals.",
        },
        "outputs": {
            name: {
                "path": display_path(path),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
            for name, path in output_paths.items()
        },
    }
    result_path = output_dir / "classic_fit.json"
    with result_path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(result_document, ensure_ascii=False, indent=2) + "\n")

    print(
        "PASS: classic draft fitted; "
        f"in_sample_rmse={full_metrics['rmse']:.6f}; "
        f"loso_rmse_mean={loso_metrics['rmse']['mean']:.6f}; "
        f"token_tail_rmse={tail_metrics['rmse']:.6f}; "
        "B4/B5 metrics withheld (absolute Loss comparability not established)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
