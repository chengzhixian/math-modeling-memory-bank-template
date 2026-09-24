"""Within-B7 empirical uncertainty; no external calibration claim."""
from __future__ import annotations

import hashlib
import json
import platform

import numpy as np

from audit_b_scaling_laws import ROOT, sha256
from b7_formal_model import FAMILY, OUTPUT as MODEL_OUTPUT
from compare_b7_quality_interactions import predict
from quality_scaling import source_data
from validate_b7_frozen_model import OUTPUT as VALIDATION_OUTPUT, fit_fixed

OUTPUT = ROOT / "outputs/cyj/quality/b7_frozen_uncertainty.json"
SEED = 20260925
BOOTSTRAP_DRAWS = 500


def build() -> dict:
    sources, x, y, _ = source_data()
    validation = json.loads(VALIDATION_OUTPUT.read_text(encoding="utf-8"))
    frozen = json.loads(MODEL_OUTPUT.read_text(encoding="utf-8"))
    if validation["source_sha256"] != frozen["B7_sha256"] or len(y) != 450:
        raise ValueError("model, validation or B7 identity mismatch")
    clusters = np.unique(x[:, :2], axis=0)
    if len(clusters) != 45:
        raise ValueError("expected 45 ND clusters")
    cluster_indices = [np.flatnonzero(np.all(x[:, :2] == cluster, axis=1)) for cluster in clusters]
    rng = np.random.default_rng(SEED)
    samples, rejected = [], []
    for draw_id in range(BOOTSTRAP_DRAWS):
        ids = rng.integers(0, len(cluster_indices), len(cluster_indices))
        selected = np.concatenate([cluster_indices[i] for i in ids])
        try:
            model = fit_fixed(x[selected], y[selected], FAMILY)
            samples.append({"draw_id": draw_id, "alpha": model["alpha"], "beta": model["beta"],
                            "coefficients": model["coefficients"],
                            "gain_range_full_rectangle": model["gain_range_full_rectangle"]})
        except ValueError as exc:
            rejected.append({"draw_id": draw_id, "reason": str(exc)})
    if len(samples) < 450:
        raise ValueError("too many bootstrap fits failed")
    residuals = {axis: [r["residual_observed_minus_predicted"] for r in validation["oof_residuals"]
                         if r["axis"] == axis] for axis in ("N_params_B", "D_tokens_B", "Q_score")}
    if any(len(v) != 450 or not np.all(np.isfinite(v)) for v in residuals.values()):
        raise ValueError("invalid OOF residual pool")
    comparison = json.loads((ROOT / "outputs/cyj/quality/b7_interaction_comparison.json").read_text(encoding="utf-8"))
    constant = comparison["full_models"]["constant_G"]
    if not constant["valid"] or comparison["source_files"] != sources:
        raise ValueError("constant-G baseline provenance mismatch")
    result = {"schema_version": "cyj.b7_frozen_uncertainty.v1",
              "status": "empirical_conditional_within_B7_not_independent_calibration",
              "source_sha256": frozen["B7_sha256"],
              "frozen_model_sha256": sha256(MODEL_OUTPUT),
              "validation_sha256": sha256(VALIDATION_OUTPUT),
              "support": frozen["support"], "family": FAMILY,
              "seed": SEED, "requested_ND_cluster_bootstrap": BOOTSTRAP_DRAWS,
              "accepted_bootstrap": len(samples), "rejected_bootstrap": rejected,
              "parameter_samples": samples,
              "oof_residuals_by_axis": residuals,
              "primary_residual_axis": "N_params_B",
              "residual_rationale": "Leave-N has the largest mean fold RMSE of the three fixed-family axes; D and Q pools remain separate sensitivity checks.",
              "model_form_sensitivity": {"primary_family": FAMILY, "baseline_family": "constant_G",
                                          "baseline_parameters": constant,
                                          "interpretation": "pointwise prediction difference; no probability assigned"},
              "cross_source_uncertainty": None, "benchmark_bridge_uncertainty": None,
              "coverage_caveat": "Bootstrap and residual pool both reuse B7; empirical interval is not calibrated on untouched or real training data.",
              "ready_for_Q3": False,
              "environment": {"python": platform.python_version(), "numpy": np.__version__},
              "code_sha256_utf8_lf": hashlib.sha256((ROOT / "src/cyj/build_b7_frozen_uncertainty.py").read_bytes().replace(b"\r\n", b"\n")).hexdigest()}
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    return result


def interval(n: float, d: float, q: float, frozen: dict, uncertainty: dict) -> dict:
    from b7_formal_model import predict_gradient
    central, _ = predict_gradient(n, d, q, frozen)
    samples = uncertainty["parameter_samples"]
    residuals = np.asarray(uncertainty["oof_residuals_by_axis"][uncertainty["primary_residual_axis"]])
    if len(samples) < 450 or len(residuals) != 450:
        raise ValueError("insufficient empirical uncertainty samples")
    point = np.array([[n, d, q]])
    rng = np.random.default_rng(SEED)
    selected_residuals = residuals[rng.integers(0, len(residuals), len(samples))]
    means = np.array([predict(s, point, FAMILY)[0] for s in samples])
    draws = means + selected_residuals
    if not np.all(np.isfinite(draws)):
        raise ValueError("nonfinite predictive draws")
    return {"central_estimate": float(central),
            "conditional_mean_percentile_95": list(map(float, np.quantile(means, [.025, .975]))),
            "empirical_prediction_percentile_95": list(map(float, np.quantile(draws, [.025, .975]))),
            "median_predictive_draw": float(np.median(draws)),
            "model_form_difference_primary_minus_constant_G": float(
                central - predict(uncertainty["model_form_sensitivity"]["baseline_parameters"],
                                  point, "constant_G")[0]),
            "scope": uncertainty["status"], "calibrated_coverage_claim": False}


if __name__ == "__main__":
    result = build()
    frozen = json.loads(MODEL_OUTPUT.read_text(encoding="utf-8"))["parameters"]
    print(json.dumps({"sha256": sha256(OUTPUT), "accepted": result["accepted_bootstrap"],
                      "example": interval(.7, 150., .5, frozen, result)}))
