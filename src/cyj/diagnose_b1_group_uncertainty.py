"""B1-only model-size cluster bootstrap for the classic N-D draft baseline."""

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
from scaling_common import (
    LOG_PARAMETER_BOUNDS,
    PARAMETER_NAMES,
    fit_classic,
    predict_classic,
)
from scaling_provenance import verify_code_files, verify_source_files


DEFAULT_PREPARED = ROOT / "outputs/cyj/classic/prepared_b1.csv"
DEFAULT_FIT = ROOT / "outputs/cyj/classic/classic_fit.json"
DEFAULT_OUTPUT = ROOT / "outputs/cyj/diagnostics/b1_group_bootstrap.json"
BASELINE_FIT_SHA256 = "9b0e381fbc0ea84bb37d63ccb273733f3a03a0c2a834e8ef52cdb75c45bc6ead"


def resample_groups(
    rows_by_group: dict[str, list[dict[str, str]]],
    selected_groups: list[str],
) -> tuple[list[dict[str, str]], list[str]]:
    """Duplicate whole trajectories, giving each sampled block its own weight."""
    sampled_rows: list[dict[str, str]] = []
    draw_labels: list[str] = []
    for draw_index, group in enumerate(selected_groups):
        block = rows_by_group[group]
        sampled_rows.extend(block)
        draw_labels.extend([f"draw_{draw_index}"] * len(block))
    return sampled_rows, draw_labels


def quantiles(values: list[float]) -> dict[str, float]:
    q025, q500, q975 = np.quantile(values, [0.025, 0.5, 0.975])
    return {"p025": float(q025), "median": float(q500), "p975": float(q975)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-version", required=True)
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--source-manifest", type=Path, default=DEFAULT_SOURCE_MANIFEST)
    parser.add_argument("--prepared", type=Path, default=DEFAULT_PREPARED)
    parser.add_argument("--fit", type=Path, default=DEFAULT_FIT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--replicates", type=int, default=80)
    parser.add_argument("--starts", type=int, default=8)
    parser.add_argument("--max-iterations", type=int, default=1200)
    parser.add_argument("--seed", type=int, default=20260924)
    args = parser.parse_args()
    if args.replicates < 20 or args.starts < 1 or args.max_iterations < 1:
        raise ValueError("invalid bootstrap run settings")
    version = validate_input_version(
        args.input_version, args.manifest.resolve(), args.source_manifest.resolve()
    )
    verify_code_files(
        version,
        (
            "src/cyj/diagnose_b1_group_uncertainty.py",
            "src/cyj/audit_b_scaling_laws.py",
            "src/cyj/scaling_provenance.py",
            "src/cyj/fit_classic_scaling.py",
            "src/cyj/prepare_scaling_data.py",
            "src/cyj/scaling_common.py",
        ),
    )
    sources = verify_source_files(
        args.data_root.resolve(), args.manifest.resolve(), (B1_FILENAME,)
    )
    if sha256(args.fit.resolve()) != BASELINE_FIT_SHA256:
        raise ValueError("baseline fit differs from reviewed classic_fit.json")
    fit = json.loads(args.fit.read_text(encoding="utf-8"))
    if fit["provenance"]["source_files"][B1_FILENAME] != sources[B1_FILENAME]:
        raise ValueError("baseline fit refers to a different B1 source")
    if sha256(args.prepared.resolve()) != fit["provenance"]["prepared_b1_sha256"]:
        raise ValueError("prepared B1 differs from baseline fit")
    rows = read_rows(args.prepared.resolve())
    if len(rows) != 1176:
        raise ValueError("unexpected prepared B1 row count")
    groups: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        groups.setdefault(row["group_id"], []).append(row)
    group_names = sorted(groups, key=lambda group: float(group[2:-1]))
    if len(group_names) != 8 or any(len(groups[group]) != 147 for group in group_names):
        raise ValueError("unexpected B1 group structure")

    rng = np.random.default_rng(args.seed)
    draws: list[dict[str, object]] = []
    accepted_parameters: list[dict[str, float]] = []
    for replicate in range(args.replicates):
        chosen = [str(group) for group in rng.choice(group_names, size=8, replace=True)]
        sampled_rows, draw_labels = resample_groups(groups, chosen)
        n_value, d_value, loss, _ = arrays(sampled_rows)
        result = fit_classic(
            n_value, d_value, loss, draw_labels,
            seed=args.seed + replicate + 1,
            starts=args.starts,
            max_iterations=args.max_iterations,
        )
        parameters = result.parameters
        at_bound = any(
            np.isclose(np.log(parameters[name]), LOG_PARAMETER_BOUNDS[index, edge], atol=1e-5)
            for index, name in enumerate(PARAMETER_NAMES)
            for edge in (0, 1)
        )
        accepted = bool(result.converged and not at_bound)
        draws.append(
            {
                "replicate": replicate + 1,
                "sampled_groups": chosen,
                "distinct_groups": len(set(chosen)),
                "fit": result.to_dict(),
                "any_parameter_at_bound": bool(at_bound),
                "accepted_for_quantiles": accepted,
            }
        )
        if accepted:
            accepted_parameters.append(parameters)
    if len(accepted_parameters) < 20:
        raise RuntimeError("fewer than 20 converged non-boundary bootstrap fits")

    parameter_intervals = {
        name: quantiles([values[name] for values in accepted_parameters])
        for name in PARAMETER_NAMES
    }
    prediction_grid = []
    for n_value in (0.070542, 1.416184, 11.965825):
        for d_value in (0.134, 100.0, 299.893):
            sample_n = np.array([n_value])
            sample_d = np.array([d_value])
            values = [
                float(predict_classic(parameters, sample_n, sample_d)[0])
                for parameters in accepted_parameters
            ]
            prediction_grid.append(
                {
                    "N_params_B": n_value,
                    "D_tokens_B": d_value,
                    "baseline_prediction": float(
                        predict_classic(fit["full_fit"]["parameters"], sample_n, sample_d)[0]
                    ),
                    "bootstrap_quantiles": quantiles(values),
                }
            )
    result = {
        "schema_version": 1,
        "status": "conditional_b1_group_bootstrap_not_validated_predictor",
        "input_version": version,
        "provenance": {
            "code_files_verified_against_input_commit": True,
            "source_b1": sources[B1_FILENAME],
            "prepared_b1_sha256": sha256(args.prepared.resolve()),
            "baseline_fit_sha256": sha256(args.fit.resolve()),
            "baseline_fit_input_version": fit["input_version"],
            "python_version": platform.python_version(),
            "numpy_version": np.__version__,
        },
        "protocol": {
            "resampling_unit": "whole B1 model-size trajectory, 147 checkpoints per group",
            "group_count": 8,
            "draws_per_replicate": 8,
            "replacement": True,
            "duplicated_draws_have_distinct_weight_groups": True,
            "replicates_requested": args.replicates,
            "fit_starts": args.starts,
            "fit_max_iterations": args.max_iterations,
            "seed": args.seed,
            "fit_objective": fit["fit_loss"],
            "acceptance_rule": "optimizer converged and no parameter at optimization bound",
        },
        "summary": {
            "accepted_replicates": len(accepted_parameters),
            "rejected_replicates": args.replicates - len(accepted_parameters),
            "parameter_percentiles_conditional": parameter_intervals,
            "prediction_grid_conditional": prediction_grid,
        },
        "draws": draws,
        "limitations": [
            "Only eight model-size clusters; percentile bounds are small-sample, conditional diagnostics, not calibrated coverage guarantees.",
            "Resampled B1 checkpoints may share a deterministic construction; this cannot establish independent generalization.",
            "Intervals omit model-form, B1 source, Q/p, cross-Loss-scale, extrapolation, and Loss-to-Benchmark uncertainty.",
            "No Q3-ready or joint-validated predictor is produced.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(
        f"wrote {args.output} "
        f"({len(accepted_parameters)}/{args.replicates} accepted bootstrap fits)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
