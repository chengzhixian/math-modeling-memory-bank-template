"""Frozen B7 interaction candidate; no cross-source or causal claim."""
from __future__ import annotations

import json
import math

from audit_b_scaling_laws import ROOT, sha256
from compare_b7_quality_interactions import fit_candidates
from quality_scaling import source_data

FAMILY = "Q_x_logN_logD"
AXES = ("N_params_B", "D_tokens_B", "Q_score")
BOUNDS = ((0.07, 11.97), (10.0, 600.0), (0.1, 1.0))
OUTPUT = ROOT / "outputs/cyj/quality/b7_frozen_model.json"
SOURCE = ROOT / "data/raw/real_attachments/B_scaling_laws/supplementary_NQ_experiment_expanded.csv"


def gain(n: float, d: float, c: list[float]) -> float:
    return c[3] + c[4] * math.log(n) + c[5] * math.log(d / 100.0)


def predict_gradient(n: float, d: float, q: float, model: dict) -> tuple[float, tuple[float, float, float]]:
    point = (n, d, q)
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v)
           or not (lo <= v <= hi) for v, (lo, hi) in zip(point, BOUNDS)):
        raise ValueError("point outside finite B7 support")
    c = model["coefficients"]
    alpha, beta = model["alpha"], model["beta"]
    g = gain(n, d, c)
    value = c[0] + c[1] * n ** -alpha + c[2] * d ** -beta + (1.0 - q) * g
    grad = (-alpha * c[1] * n ** (-alpha - 1.0) + (1.0 - q) * c[4] / n,
            -beta * c[2] * d ** (-beta - 1.0) + (1.0 - q) * c[5] / d,
            -g)
    if not math.isfinite(value) or not all(map(math.isfinite, grad)):
        raise ValueError("nonfinite prediction")
    return float(value), tuple(map(float, grad))


def elasticities(n: float, d: float, q: float, model: dict) -> tuple[float, float, float]:
    value, grad = predict_gradient(n, d, q, model)
    return tuple(x * derivative / value for x, derivative in zip((n, d, q), grad))


def substitution_rates(n: float, d: float, q: float, model: dict) -> dict[str, float]:
    _, (ln, ld, lq) = predict_gradient(n, d, q, model)
    if ld == 0 or lq == 0:
        raise ValueError("undefined substitution rate")
    return {"dD_dN_at_LQ": -ln / ld, "dQ_dN_at_LD": -ln / lq,
            "dQ_dD_at_LN": -ld / lq}


def build() -> dict:
    sources, x, y, _ = source_data()
    if len(x) != 450 or sha256(SOURCE) != sources[SOURCE.name]["sha256"]:
        raise ValueError("B7 source identity changed")
    model = fit_candidates(x, y)[FAMILY]
    if not model["valid"]:
        raise ValueError("frozen family failed full B7 fit")
    corners = [gain(n, d, model["coefficients"])
               for n in BOUNDS[0] for d in BOUNDS[1]]
    if min(corners) <= 0:
        raise ValueError("quality gradient violates declared support")
    result = {"schema_version": "cyj.b7_frozen_candidate.v1",
              "status": "conditional_within_B7_pending_independent_test",
              "ready_for_Q3": False, "family": FAMILY,
              "formula": "E+A*N**(-alpha)+B*D**(-beta)+(1-Q)*(G0+GN*ln(N)+GD*ln(D/100))",
              "parameters": model, "support": dict(zip(AXES, BOUNDS)),
              "source_files": sources, "B7_sha256": sha256(SOURCE),
              "quality_gain_full_rectangle_corners": corners,
              "validation_caveat": "The family was proposed after inspection of all B7; fixed-family grouped CV is conditional within-source assessment, not an untouched test.",
              "claim_level": "L2_conditional_within_B7_semi_synthetic"}
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    return result


if __name__ == "__main__":
    result = build()
    print(json.dumps({"output_sha256": sha256(OUTPUT),
                      "min_gain": min(result["quality_gain_full_rectangle_corners"]),
                      "ready_for_Q3": result["ready_for_Q3"]}))
