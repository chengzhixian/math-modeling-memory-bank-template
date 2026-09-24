"""Describe B2 semi-synthetic and B3 interpolated trajectory shapes.

No cross-source absolute Loss error is computed: its measurement scale has
not been independently established as equivalent to B1 val_loss.
"""

from __future__ import annotations

import argparse
import json
import platform
from pathlib import Path

from audit_b_scaling_laws import (
    DEFAULT_DATA_ROOT,
    DEFAULT_MANIFEST,
    DEFAULT_SOURCE_MANIFEST,
    ROOT,
    validate_input_version,
)
from fit_classic_scaling import read_rows
from scaling_provenance import verify_code_files, verify_source_files


B2_FILENAME = "cerebras_training_log.csv"
B3_DIRECTORY = "training_trajectories"
DEFAULT_OUTPUT = ROOT / "outputs/cyj/diagnostics/b2_b3_shapes.json"


def describe_curve(rows: list[dict[str, str]]) -> dict[str, float | int | str]:
    if len(rows) < 2:
        raise ValueError("curve must have at least two points")
    is_b2 = "steps" in rows[0]
    step_field = "steps" if is_b2 else "step"
    ordered = sorted(
        rows,
        key=lambda row: float(row[step_field] if is_b2 else row["D_tokens_B"]),
    )
    n_values = {float(row["N_params_B"]) for row in ordered}
    if len(n_values) != 1:
        raise ValueError("curve mixes model sizes")
    d_values = [float(row["D_tokens_B"]) for row in ordered]
    steps = [float(row[step_field]) for row in ordered]
    losses = [float(row["val_loss"]) for row in ordered]
    if any(
        right < left or (is_b2 and right == left)
        for left, right in zip(steps, steps[1:])
    ):
        raise ValueError("checkpoint step order is invalid")
    if any(
        right < left or (not is_b2 and right == left)
        for left, right in zip(d_values, d_values[1:])
    ):
        raise ValueError("D must be nondecreasing within a trajectory")
    increments = [right - left for left, right in zip(losses, losses[1:])]
    return {
        "N_params_B": n_values.pop(),
        "rows": len(rows),
        "D_min_B": d_values[0],
        "D_max_B": d_values[-1],
        "distinct_D_values": len(set(d_values)),
        "adjacent_equal_D_pairs": sum(
            right == left for left, right in zip(d_values, d_values[1:])
        ),
        "distinct_step_values": len(set(steps)),
        "adjacent_equal_step_pairs": sum(
            right == left for left, right in zip(steps, steps[1:])
        ),
        "val_loss_first": losses[0],
        "val_loss_last": losses[-1],
        "val_loss_last_minus_first": losses[-1] - losses[0],
        "adjacent_loss_increases": sum(value > 0 for value in increments),
        "adjacent_loss_decreases": sum(value < 0 for value in increments),
        "adjacent_loss_ties": sum(value == 0 for value in increments),
        "maximum_adjacent_loss_increase": max(increments),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-version", required=True)
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--source-manifest", type=Path, default=DEFAULT_SOURCE_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    version = validate_input_version(
        args.input_version, args.manifest.resolve(), args.source_manifest.resolve()
    )
    verify_code_files(
        version,
        (
            "src/cyj/diagnose_b2_b3_shapes.py",
            "src/cyj/scaling_provenance.py",
            "src/cyj/audit_b_scaling_laws.py",
            "src/cyj/fit_classic_scaling.py",
        ),
    )
    b3_paths = sorted((args.data_root / B3_DIRECTORY).glob("*.csv"))
    if len(b3_paths) != 8:
        raise ValueError("expected exactly eight B3 interpolation files")
    filenames = (B2_FILENAME,) + tuple(
        f"{B3_DIRECTORY}/{path.name}" for path in b3_paths
    )
    sources = verify_source_files(
        args.data_root.resolve(), args.manifest.resolve(), filenames
    )

    b2_rows = read_rows(args.data_root / B2_FILENAME)
    if len(b2_rows) != 1029:
        raise ValueError("unexpected B2 row count")
    b2_groups: dict[float, list[dict[str, str]]] = {}
    for row in b2_rows:
        b2_groups.setdefault(float(row["N_params_B"]), []).append(row)
    if len(b2_groups) != 7 or any(len(rows) != 147 for rows in b2_groups.values()):
        raise ValueError("unexpected B2 trajectory grouping")
    b2_curves = [describe_curve(rows) for _, rows in sorted(b2_groups.items())]

    b3_curves = []
    for path in b3_paths:
        rows = read_rows(path)
        if len(rows) != 500 or {row["interpolated"] for row in rows} != {"1"}:
            raise ValueError(f"unexpected B3 interpolation markers: {path.name}")
        b3_curves.append({"file": path.name, **describe_curve(rows)})
    b3_curves.sort(key=lambda curve: float(curve["N_params_B"]))

    result = {
        "schema_version": 1,
        "status": "shape_diagnostic_only_not_independent_validation",
        "input_version": version,
        "provenance": {
            "code_files_verified_against_input_commit": True,
            "source_files": sources,
            "python_version": platform.python_version(),
        },
        "b2": {
            "nature": "semi_synthetic_calibrated_from_pythia_scaling",
            "rows": len(b2_rows),
            "curves": b2_curves,
            "total_adjacent_loss_increases": sum(
                int(curve["adjacent_loss_increases"]) for curve in b2_curves
            ),
            "use_boundary": "Descriptive within-curve shape check only; no B1-to-B2 absolute-loss RMSE or independent external-validation claim.",
        },
        "b3": {
            "nature": "interpolated_from_pythia_checkpoints",
            "rows": sum(int(curve["rows"]) for curve in b3_curves),
            "curves": b3_curves,
            "total_adjacent_loss_increases": sum(
                int(curve["adjacent_loss_increases"]) for curve in b3_curves
            ),
            "use_boundary": "Interpolation-shape check only; B3 is not an independent holdout from B1.",
        },
        "unverified": [
            "B2 generation code, calibration target, and evaluation loss comparability to B1",
            "B3 interpolation method and noise-generation procedure at row level",
            "B1 row-level original val_loss provenance",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(f"wrote {args.output} (B2 {len(b2_rows)} rows; B3 4000 rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
