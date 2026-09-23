"""Diagnose displayed B1 compute precision and eight-row fit sensitivity."""

from __future__ import annotations

import argparse
import json
import platform
from pathlib import Path

import numpy as np

from audit_b_scaling_laws import (
    DEFAULT_DATA_ROOT,
    DEFAULT_MANIFEST,
    DEFAULT_SOURCE_MANIFEST,
    ROOT,
    sha256,
    validate_input_version,
)
from fit_classic_scaling import arrays, read_rows
from prepare_scaling_data import B1_FILENAME
from scaling_common import fit_classic, predict_classic, regression_metrics
from scaling_provenance import verify_code_files, verify_source_files


DEFAULT_FIT = ROOT / "outputs/cyj/classic/classic_fit.json"
DEFAULT_PREPARED = ROOT / "outputs/cyj/classic/prepared_b1.csv"
DEFAULT_OUTPUT = ROOT / "outputs/cyj/diagnostics/b1_precision_sensitivity.json"


def compute_identity(rows: list[dict[str, str]]) -> dict[str, object]:
    """Check the displayed four-decimal C column, not unobserved raw FLOPs."""
    outliers = []
    matching = 0
    max_absolute = 0.0
    for row in rows:
        n_value = float(row["N_params_B"])
        d_value = float(row["D_tokens_B"])
        displayed = float(row["C_FLOPs_1e21"])
        theoretical = 0.006 * n_value * d_value
        matching += round(theoretical, 4) == displayed
        absolute = abs(displayed - theoretical)
        max_absolute = max(max_absolute, absolute)
        relative = (displayed - theoretical) / theoretical
        if abs(relative) > 0.05:
            outliers.append(
                {
                    "run_id": row["run_id"],
                    "N_params_B": n_value,
                    "D_tokens_B": d_value,
                    "displayed_C_FLOPs_1e21": displayed,
                    "formula_C_FLOPs_1e21": theoretical,
                    "relative_error_displayed_minus_formula": relative,
                    "absolute_error_C_FLOPs_1e21": absolute,
                    "matches_four_decimal_rounding": round(theoretical, 4) == displayed,
                }
            )
    return {
        "formula": "C_FLOPs_1e21 = 0.006*N_params_B*D_tokens_B",
        "displayed_decimal_places": 4,
        "rows": len(rows),
        "rows_matching_four_decimal_rounding": matching,
        "max_absolute_error_C_FLOPs_1e21": max_absolute,
        "relative_warning_threshold": 0.05,
        "relative_warning_rows": outliers,
        "interpretation": "Four-decimal display explains these relative warnings; underlying unrounded compute provenance is not independently established.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-version", required=True)
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--source-manifest", type=Path, default=DEFAULT_SOURCE_MANIFEST)
    parser.add_argument("--prepared", type=Path, default=DEFAULT_PREPARED)
    parser.add_argument("--fit", type=Path, default=DEFAULT_FIT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    version = validate_input_version(
        args.input_version, args.manifest.resolve(), args.source_manifest.resolve()
    )
    verify_code_files(
        version,
        (
            "src/cyj/diagnose_b1_precision.py",
            "src/cyj/fit_classic_scaling.py",
            "src/cyj/prepare_scaling_data.py",
            "src/cyj/scaling_common.py",
            "src/cyj/scaling_provenance.py",
            "src/cyj/audit_b_scaling_laws.py",
        ),
    )
    source = verify_source_files(
        args.data_root.resolve(), args.manifest.resolve(), (B1_FILENAME,)
    )
    fit = json.loads(args.fit.read_text(encoding="utf-8"))
    if fit["input_version"] != "cf297a4ad47e235acf5a9b6e890a5df5e05b07e5":
        raise ValueError("unexpected baseline fit input version")
    if fit["provenance"]["source_files"][B1_FILENAME] != source[B1_FILENAME]:
        raise ValueError("baseline fit refers to a different B1 source")
    prepared = read_rows(args.prepared.resolve())
    if len(prepared) != 1176 or len({row["source_run_id"] for row in prepared}) != len(prepared):
        raise ValueError("unexpected prepared B1 row count or duplicate run_id")
    if sha256(args.prepared.resolve()) != fit["provenance"]["prepared_b1_sha256"]:
        raise ValueError("prepared B1 differs from baseline fit")
    raw = read_rows(args.data_root.resolve() / B1_FILENAME)
    if {row["run_id"] for row in raw} != {row["source_run_id"] for row in prepared}:
        raise ValueError("raw and prepared B1 row identities differ")
    identity = compute_identity(raw)
    if identity["rows_matching_four_decimal_rounding"] != len(raw):
        raise ValueError("some displayed compute values do not follow four-decimal rounding")
    excluded = {item["run_id"] for item in identity["relative_warning_rows"]}
    retained = [row for row in prepared if row["source_run_id"] not in excluded]
    n_value, d_value, loss, groups = arrays(prepared)
    retained_n, retained_d, retained_loss, retained_groups = arrays(retained)
    refit = fit_classic(
        retained_n, retained_d, retained_loss, retained_groups,
        seed=20260924, starts=24, max_iterations=1600,
    )
    baseline_parameters = fit["full_fit"]["parameters"]
    baseline_prediction = predict_classic(baseline_parameters, n_value, d_value)
    refit_prediction = predict_classic(refit.parameters, n_value, d_value)
    result = {
        "schema_version": 1,
        "status": "diagnostic_not_independent_validation",
        "input_version": version,
        "provenance": {
            "code_files_verified_against_input_commit": True,
            "source_b1": source[B1_FILENAME],
            "prepared_b1_sha256": sha256(args.prepared.resolve()),
            "baseline_fit_sha256": sha256(args.fit.resolve()),
            "baseline_fit_input_version": fit["input_version"],
            "python_version": platform.python_version(),
            "numpy_version": np.__version__,
        },
        "compute_identity": identity,
        "sensitivity": {
            "policy": "exclude only eight rows whose displayed C has >5% relative deviation from 0.006*N*D; no rows removed from the baseline artifact",
            "excluded_run_ids": sorted(excluded, key=int),
            "retained_rows": len(retained),
            "baseline_parameters": baseline_parameters,
            "refit": refit.to_dict(),
            "baseline_metrics_all_rows": regression_metrics(loss, baseline_prediction),
            "refit_metrics_all_rows": regression_metrics(loss, refit_prediction),
            "refit_metrics_retained_rows": regression_metrics(
                retained_loss,
                predict_classic(refit.parameters, retained_n, retained_d),
            ),
            "maximum_absolute_prediction_change_all_rows": float(
                np.max(np.abs(refit_prediction - baseline_prediction))
            ),
            "interpretation": "This is an in-sample sensitivity check, not an external or Q3 validation.",
        },
        "unverified": [
            "row-level original Pythia val_loss evaluation records and preprocessing",
            "underlying unrounded compute measurements",
            "Q/p mapping and Q1 domain Loss to B1 val_loss anchor",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"wrote {args.output} ({len(raw)} B1 rows, {len(excluded)} warnings)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
