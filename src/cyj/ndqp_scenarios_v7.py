"""Conditional Q2 v7 predictor. Cross-source bridge is a stated scenario."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

from chm_q1_v2_consumer import Q1V2Consumer, ROOT, SOURCE_COMMIT, sha256

VERSION = "cyj.ndqp.scenario.v7"
BOUNDS = ((0.07, 11.97), (10.0, 600.0), (0.1, 1.0))
THETA = (1.735386135541723, 0.3575829483248725, 1.2653732503568877,
         0.339266809084349, 0.3203945700462738, 0.3701472576630735,
         -0.059492064169103916, -0.015805197892510177)
PARAMETER_SOURCE = ROOT / "outputs/cyj/q2_final/model_coefficients.json"


def _number(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number")
    return float(value)


def b7(n, d, q):
    point = tuple(_number(v, name) for v, name in zip((n, d, q), ("N", "D", "Q_B")))
    if any(not lo <= x <= hi for x, (lo, hi) in zip(point, BOUNDS)):
        raise ValueError("N/D/Q_B outside frozen B7 bounds")
    n, d, q = point
    e, a, b, alpha, beta, g0, gn, gd = THETA
    gain = g0 + gn * math.log(n) + gd * math.log(d / 100.0)
    loss = e + a * n ** -alpha + b * d ** -beta + (1.0 - q) * gain
    gradient = (-alpha * a * n ** (-alpha-1) + (1-q) * gn/n,
                -beta * b * d ** (-beta-1) + (1-q) * gd/d, -gain)
    if loss <= 0 or not all(map(math.isfinite, (loss, *gradient))):
        raise ValueError("nonpositive or nonfinite B7 prediction")
    return loss, gradient


class ConditionalV7:
    def __init__(self, root: Path = ROOT):
        self.root = Path(root)
        self.q1 = Q1V2Consumer(self.root)
        frozen = json.loads((self.root / "outputs/cyj/q2_final/model_coefficients.json").read_text(encoding="utf-8"))
        if tuple(frozen["theta_B7"]) != THETA:
            raise ValueError("frozen B7 coefficients changed")
        self.b7_sha256 = sha256(self.root / "outputs/cyj/q2_final/model_coefficients.json")

    def evaluate(self, n, d, q, p, weights, *, p_policy, bridge_lambda=1.0, eta=0.0,
                 bridge_model="exp_bridge"):
        if bridge_model not in ("exp_bridge", "linear_bridge"):
            raise ValueError("unsupported bridge model")
        lam = _number(bridge_lambda, "bridge_lambda")
        eta = _number(eta, "eta")
        if lam < 0:
            raise ValueError("bridge_lambda must be nonnegative")
        base, base_grad = b7(n, d, q)
        support = self.q1.support(p, p_policy)
        w = self.q1.weight_vector(weights)
        r = self.q1.weighted_effect(p, weights)
        grad_r = self.q1.gradient(p, weights)
        try:
            a = 0.0 if lam == 0 else lam * float(n) ** -eta
        except OverflowError as exc:
            raise ValueError("bridge scale overflows numerical range") from exc
        if not math.isfinite(a) or (lam > 0 and a == 0):
            raise ValueError("bridge scale outside finite nonzero numerical range")
        z = a * r
        if not math.isfinite(z):
            raise ValueError("nonfinite bridge exponent")
        if bridge_model == "exp_bridge":
            if z > 700 or z < -700:
                raise ValueError("bridge exponent outside finite numerical range")
            factor = math.exp(z)
            loss = base * factor
            grad = [factor * (base_grad[0] - base * eta * z / n),
                    factor * base_grad[1], factor * base_grad[2]]
            grad_p = factor * base * a * grad_r
        else:
            factor = 1.0 + z
            if factor <= 0:
                raise ValueError("linear bridge factor is nonpositive")
            loss = base * factor
            grad = [base_grad[0] * factor - base * eta * z / n,
                    base_grad[1] * factor, base_grad[2] * factor]
            grad_p = base * a * grad_r
        if loss <= 0 or not all(math.isfinite(v) for v in (loss, factor, *grad, *grad_p)):
            raise ValueError("nonfinite conditional prediction or gradient")
        qa = {key: self.q1.qa_stats(p, key) for key in ("quality_direct", "quality_direct_and_near")}
        return {"schema_version": VERSION, "Loss": float(loss), "B7_loss": float(base),
                "Q1_weighted_effect": float(r), "bridge_factor": float(factor),
                "bridge_model": bridge_model, "bridge_lambda": lam, "eta": eta,
                "gradients": {"N_B": float(grad[0]), "D_B": float(grad[1]),
                              "Q_B": float(grad[2]), "p_ambient": dict(zip(self.q1.domains, map(float, grad_p)))},
                "elasticities_signed": {"N": n*grad[0]/loss, "D": d*grad[1]/loss,
                                         "Q_B": q*grad[2]/loss},
                "p_support": support, "qa_stats": qa,
                "Q1_manifest_sha256": self.q1.manifest_sha256, "Q1_source_commit": SOURCE_COMMIT,
                "B7_parameters_sha256": self.b7_sha256,
                "units": {"N": "billion_parameters", "D": "billion_tokens", "Loss": "conditional_cross_entropy"},
                "conditional_on_bridge_assumptions": True, "scenario_only": True,
                "not_empirically_calibrated": True, "empirically_calibrated_A_to_B": False,
                "bridge_status": "sensitivity-only"}

    def predict_baseline(self, n, d, q, p, weights, *, p_policy):
        result = self.evaluate(n, d, q, p, weights, p_policy=p_policy)
        result["mode"] = "baseline"
        result["baseline_loss"] = result["Loss"]
        return result

    def predict_sensitivity(self, n, d, q, p, weights, *, p_policy, bridge_lambda, eta,
                            bridge_model):
        result = self.evaluate(n, d, q, p, weights, p_policy=p_policy,
                               bridge_lambda=bridge_lambda, eta=eta, bridge_model=bridge_model)
        baseline = self.predict_baseline(n, d, q, p, weights, p_policy=p_policy)
        result["mode"] = "bridge_sensitivity"
        result["scenario_loss"] = result["Loss"]
        result["difference_from_baseline"] = result["Loss"] - baseline["Loss"]
        return result


def _unique(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError(f"duplicate JSON key: {key}")
        out[key] = value
    return out


def request(model: ConditionalV7, item: dict):
    if not isinstance(item, dict):
        raise ValueError("request must be an object")
    required = {"schema_version", "mode", "N_params_B", "D_tokens_B", "Q_score", "p", "weights", "p_policy"}
    if item.get("schema_version") != VERSION or not required <= set(item):
        raise ValueError("invalid v7 schema or missing required field")
    mode = item["mode"]
    common = (item["N_params_B"], item["D_tokens_B"], item["Q_score"], item["p"], item["weights"])
    if mode == "baseline":
        if set(item) != required:
            raise ValueError("baseline does not accept bridge overrides or unknown fields")
        return model.predict_baseline(*common, p_policy=item["p_policy"])
    extra = {"bridge_lambda", "eta", "bridge_model"}
    if mode != "bridge_sensitivity" or set(item) != required | extra:
        raise ValueError("sensitivity requires explicit bridge fields and no unknown fields")
    return model.predict_sensitivity(*common, p_policy=item["p_policy"],
                                     bridge_lambda=item["bridge_lambda"], eta=item["eta"],
                                     bridge_model=item["bridge_model"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", type=Path)
    parser.add_argument("--describe", action="store_true")
    args = parser.parse_args()
    try:
        model = ConditionalV7()
        if args.describe:
            result = {"schema_version": VERSION, "Q1_manifest_sha256": model.q1.manifest_sha256,
                      "conditional_on_bridge_assumptions": True, "bridge_status": "sensitivity-only",
                      "p_policies": ["observed_512", "convex_hull", "quality_direct",
                                     "quality_direct_and_near", "algebraic_reference_only"]}
        elif args.request:
            result = request(model, json.loads(args.request.read_text(encoding="utf-8-sig"), object_pairs_hook=_unique))
        else:
            parser.error("specify --describe or --request")
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
        return 0
    except (ValueError, TypeError, KeyError, OSError) as exc:
        import sys
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
