"""Refit classic-law term ablations on the frozen B1 grouped validation folds."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from audit_b_scaling_laws import DEFAULT_DATA_ROOT, DEFAULT_MANIFEST, DEFAULT_SOURCE_MANIFEST, ROOT, sha256, validate_input_version
from fit_classic_scaling import arrays, read_rows
from prepare_scaling_data import B1_FILENAME
from scaling_common import LOG_PARAMETER_BOUNDS, PARAMETER_NAMES, group_equal_weights, huber, nelder_mead, predict_classic, regression_metrics
from scaling_provenance import verify_code_files, verify_source_files
from q3_interface import FIT, FIT_SHA

VARIANTS = {"no_E": (1, 2, 3, 4), "no_N": (0, 2, 4), "no_D": (0, 1, 3)}


def fit_reduced(n, d, y, groups, variant, *, seed, starts=8, max_iterations=1800):
    active = list(VARIANTS[variant])
    bounds = LOG_PARAMETER_BOUNDS[active]
    log_n, log_d, log_y = np.log(n), np.log(d), np.log(y)
    weights = group_equal_weights(groups)

    def unpack(point):
        values = dict.fromkeys(PARAMETER_NAMES, 0.0)
        values.update(zip((PARAMETER_NAMES[i] for i in active), np.exp(point), strict=True))
        return values

    def objective(point):
        if np.any(point < bounds[:, 0]) or np.any(point > bounds[:, 1]):
            return float("inf")
        p = unpack(point)
        prediction = p["E"] + p["A"] * np.exp(-p["alpha"] * log_n) + p["B"] * np.exp(-p["beta"] * log_d)
        return float(np.sum(weights * huber(np.log(prediction) - log_y, 0.05)))

    base = np.log([max(0.05, float(y.min()) * 0.75), max(0.05, float(np.ptp(y))), max(0.05, float(np.ptp(y))), 0.2, 0.2])[active]
    rng = np.random.default_rng(seed)
    initial = [np.clip(base, bounds[:, 0], bounds[:, 1])]
    initial += [rng.uniform(bounds[:, 0], bounds[:, 1]) for _ in range(starts - 1)]
    candidates = [nelder_mead(objective, start, max_iterations=max_iterations) for start in initial]
    point, value, iterations, converged = min(candidates, key=lambda result: result[1])
    parameters = {k: float(v) for k, v in unpack(point).items()}
    return {"parameters": parameters, "objective": value, "converged": converged,
            "iterations": iterations, "at_bound": bool(np.any(np.isclose(point[:, None], bounds, atol=1e-5))),
            "seed": seed, "starts": starts}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-version", required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "outputs/cyj/ablation/b1_terms.json")
    args = parser.parse_args()
    version = validate_input_version(args.input_version, DEFAULT_MANIFEST, DEFAULT_SOURCE_MANIFEST)
    verify_code_files(version, tuple("src/cyj/" + p for p in (
        "ablate_b1_terms.py", "q3_interface.py", "audit_b_scaling_laws.py", "scaling_provenance.py",
        "fit_classic_scaling.py", "prepare_scaling_data.py", "scaling_common.py")))
    sources = verify_source_files(DEFAULT_DATA_ROOT, DEFAULT_MANIFEST, (B1_FILENAME,))
    if sha256(FIT) != FIT_SHA:
        raise ValueError("reviewed full-model fit changed")
    fit = json.loads(FIT.read_text(encoding="utf-8"))
    prepared = ROOT / "outputs/cyj/classic/prepared_b1.csv"
    cv_path = ROOT / "outputs/cyj/classic/classic_cv.csv"
    if sha256(prepared) != fit["provenance"]["prepared_b1_sha256"] or sha256(cv_path) != fit["outputs"]["classic_cv"]["sha256"]:
        raise ValueError("frozen split or baseline CV file changed")
    if sources[B1_FILENAME] != fit["provenance"]["source_files"][B1_FILENAME]:
        raise ValueError("B1 identity differs from baseline")
    rows, baseline_cv, results = read_rows(prepared), read_rows(cv_path), []
    for fold in baseline_cv:
        is_tail = fold["protocol"] == "token_tail_70_30"
        train = [r for r in rows if (r["token_tail_split"] == "train" if is_tail else r["group_id"] != fold["held_out_group"])]
        test = [r for r in rows if (r["token_tail_split"] == "test" if is_tail else r["group_id"] == fold["held_out_group"])]
        assert not {r["sample_id"] for r in train} & {r["sample_id"] for r in test}
        n, d, y, groups = arrays(train)
        tn, td, ty, _ = arrays(test)
        parameters = {key: float(fold["parameter_" + key]) for key in PARAMETER_NAMES}
        baseline_metrics = regression_metrics(ty, predict_classic(parameters, tn, td))
        if not np.isclose(baseline_metrics["rmse"], float(fold["rmse"]), rtol=1e-10, atol=1e-12):
            raise ValueError("baseline fold failed prediction reproduction")
        result = {"protocol": fold["protocol"], "held_out_group": fold["held_out_group"],
                  "train_rows": len(train), "test_rows": len(test), "full": baseline_metrics}
        seed = 20260924 + (100 if is_tail else int(fold["fold"]))
        for variant in VARIANTS:
            reduced = fit_reduced(n, d, y, groups, variant, seed=seed)
            metrics = regression_metrics(ty, predict_classic(reduced["parameters"], tn, td))
            result[variant] = {"fit": reduced, "metrics": metrics, "rmse_minus_full": metrics["rmse"] - baseline_metrics["rmse"]}
        results.append(result)
        print(f"completed {fold['protocol']} {fold['held_out_group']}", flush=True)
    summary = {}
    for variant in ("full", *VARIANTS):
        loso = [(row["full"] if variant == "full" else row[variant]["metrics"])["rmse"] for row in results[:-1]]
        tail = results[-1]["full"] if variant == "full" else results[-1][variant]["metrics"]
        summary[variant] = {"LOSO_RMSE_mean": float(np.mean(loso)), "LOSO_RMSE_max": float(max(loso)), "tail_RMSE": tail["rmse"]}
    result = {"schema_version": 1, "status": "B1_only_term_ablation_not_independent_validation",
              "input_version": version, "provenance": {"source": sources, "baseline_fit_sha256": FIT_SHA,
              "prepared_sha256": sha256(prepared), "cv_sha256": sha256(cv_path)},
              "protocol": {"ablations": {"no_E": "E=0", "no_N": "A=0; alpha omitted", "no_D": "B=0; beta omitted"},
                           "refit": True, "loss": fit["fit_loss"], "huber_delta": 0.05,
                           "starts": 8, "max_iterations": 1800, "test_used_for_selection": False,
                           "full_model": "reproduce existing frozen fold fits; do not refit or retune"},
              "summary": summary, "folds": results,
              "limitations": ["Only B1 construction is tested; low error is not real-world generalization.",
                              "Q/p terms are not fitted and cannot be scientifically ablated on B1.",
                              "Boundary/nonconverged reduced fits must be reported when interpreting differences."]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
