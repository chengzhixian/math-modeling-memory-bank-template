"""Conditional v8 N-D-Q_A-p predictor with a frozen B1 backbone and explicit quality proxy."""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

from chm_q1_v2_consumer import Q1V2Consumer, ROOT, sha256
from fit_b7_quality_extension_from_b1 import B1_FILE, B1_SHA, b1_parameters

VERSION = "cyj.ndqp.scenario.v8"
FIT = ROOT / "outputs/Q2/b7_quality_extension.json"
BOUNDS = ((.070542, 11.965825), (10.0, 299.893), (.1, 1.0))
MAPPING = {"direct": "quality_direct", "direct_and_near": "quality_direct_and_near"}


def finite(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number")
    return float(value)


def unique(pairs):
    output = {}
    for key, value in pairs:
        if key in output:
            raise ValueError(f"duplicate JSON key: {key}")
        output[key] = value
    return output


class ConditionalV8:
    def __init__(self, root: Path = ROOT):
        self.root = Path(root)
        self.q1 = Q1V2Consumer(self.root)
        self.b1 = b1_parameters()
        if sha256(B1_FILE) != B1_SHA:
            raise ValueError("B1 backbone identity mismatch")
        payload = json.loads((self.root / "outputs/Q2/b7_quality_extension.json").read_text(encoding="utf-8"))
        if payload["B1_fit_sha256"] != B1_SHA or payload["B1_parameters"] != self.b1:
            raise ValueError("v8 quality fit has a different B1 backbone")
        self.gamma = tuple(payload["quality_parameters"][key] for key in ("G0", "GN", "GD"))
        if len(self.gamma) != 3 or not all(math.isfinite(value) for value in self.gamma):
            raise ValueError("v8 quality parameters invalid")
        self.quality_fit_sha256 = sha256(self.root / "outputs/Q2/b7_quality_extension.json")

    def qa(self, p: dict, mapping_policy: str, scale: float = 1.0):
        if mapping_policy not in MAPPING:
            raise ValueError("quality_mapping_policy must be direct or direct_and_near")
        scale = finite(scale, "quality_bridge_scale")
        if scale <= 0 or scale > 2:
            raise ValueError("quality bridge scale must lie in (0,2]")
        stats = self.q1.qa_stats(p, MAPPING[mapping_policy])
        if stats["mean_Q_A_on_mapped"] is None or stats["covered_mass"] <= 1e-10:
            raise ValueError("Q_A bridge requires positive mapped coverage")
        mapped = [d for d in self.q1.domains if self.q1.qa_rows[d]["Q_A"] is not None and
                  self.q1.qa_rows[d]["mapping_type"] in ({"direct"} if mapping_policy == "direct"
                                                      else {"direct", "near_direct"})]
        q_values = [float(self.q1.qa_rows[d]["Q_A"]) for d in mapped]
        low, high = min(q_values), max(q_values)
        if high <= low:
            raise ValueError("Q_A anchors have no range")
        mean = float(stats["mean_Q_A_on_mapped"])
        ref = float(stats["reference_mean_Q_A"])
        coefficient = .9/(high-low)
        q_ref = .1+coefficient*(ref-low)
        raw = q_ref+scale*coefficient*(mean-ref)
        proxy = max(.1, min(1.0, raw))
        clipped = raw < .1 or raw > 1.0
        derivative = 0.0 if clipped else scale*coefficient
        point = self.q1.point(p)
        m = np.array([float(d in mapped) for d in self.q1.domains])
        values = np.array([float(self.q1.qa_rows[d]["Q_A"]) if d in mapped else 0.0
                           for d in self.q1.domains])
        covered = float(point @ m)
        qa_grad = m*(values-mean)/covered
        qa_hess = -(np.outer(m, m)*(values[:, None]+values[None, :]-2*mean))/covered**2
        return {"Q_A_mapped": mean, "mapped_coverage": covered,
                "unmapped_mass": float(point.sum()-covered),
                "Q_A_reference": ref, "Q_A_anchor_min": low, "Q_A_anchor_max": high,
                "Q_B_proxy": proxy, "Q_B_reference_proxy": q_ref,
                "quality_bridge_scale": scale, "quality_proxy_clipped": clipped,
                "dQproxy_dQA": derivative, "mapped_domain_count": len(mapped),
                "mapping_policy": mapping_policy,
                "assumption": "monotone_minmax_anchor_not_empirical_A_to_B_calibration",
                "qa_stats": stats, "_qa_grad": qa_grad, "_qa_hess": qa_hess}

    def base(self, n: float, d: float, q: float):
        n, d, q = finite(n, "N_params_B"), finite(d, "D_tokens_B"), finite(q, "Q_B_proxy")
        if any(not lo <= value <= hi for value, (lo, hi) in zip((n, d, q), BOUNDS)):
            raise ValueError("N/D/Q outside v8 common B1-B7 support")
        e, a, b, alpha, beta = (self.b1[key] for key in ("E", "A", "B", "alpha", "beta"))
        g0, gn, gd = self.gamma
        gain = g0+gn*math.log(n)+gd*math.log(d/100)
        scale = e+a*n**(-alpha)+b*d**(-beta)
        value = scale+(1-q)*gain
        grad = (-alpha*a*n**(-alpha-1)+(1-q)*gn/n,
                -beta*b*d**(-beta-1)+(1-q)*gd/d, -gain)
        if value <= 0 or not all(math.isfinite(v) for v in (value, *grad)):
            raise ValueError("v8 base Loss or gradient is invalid")
        return value, grad, gain

    def evaluate(self, n, d, p, weights, *, p_policy, quality_mapping_policy="direct_and_near",
                 quality_mode="q1_quality_baseline", native_QB=None, quality_bridge_scale=1.0,
                 mixture_bridge_lambda=1.0, mixture_bridge_eta=0.0, bridge_model="exp_bridge"):
        n, d = finite(n, "N_params_B"), finite(d, "D_tokens_B")
        if bridge_model not in ("exp_bridge", "linear_bridge"):
            raise ValueError("unknown mixture bridge model")
        lam, eta = finite(mixture_bridge_lambda, "mixture_bridge_lambda"), finite(mixture_bridge_eta, "mixture_bridge_eta")
        if lam < 0:
            raise ValueError("mixture bridge lambda must be nonnegative")
        support = self.q1.support(p, p_policy)
        self.q1.weight_vector(weights)
        qa = None
        if quality_mode in ("q1_quality_baseline", "q1_quality_bridge_sensitivity"):
            if native_QB is not None:
                raise ValueError("Q1 quality mode rejects native Q_B input")
            if quality_mode == "q1_quality_baseline" and quality_bridge_scale != 1.0:
                raise ValueError("baseline quality bridge scale is fixed at 1")
            qa = self.qa(p, quality_mapping_policy, quality_bridge_scale)
            q = qa["Q_B_proxy"]
            q_p = qa["dQproxy_dQA"]*qa["_qa_grad"]
        elif quality_mode == "native_QB_sensitivity":
            q = finite(native_QB, "native_QB")
            q_p = np.zeros(len(self.q1.domains))
        else:
            raise ValueError("unknown quality mode")
        base, base_grad, gain = self.base(n, d, q)
        r = self.q1.weighted_effect(p, weights)
        grad_r = self.q1.gradient(p, weights)
        try:
            amplitude = 0.0 if lam == 0 else lam*n**(-eta)
        except OverflowError as exc:
            raise ValueError("mixture bridge scale overflow") from exc
        if not math.isfinite(amplitude) or (lam > 0 and amplitude == 0):
            raise ValueError("mixture bridge scale outside finite nonzero range")
        z = amplitude*r
        if not math.isfinite(z):
            raise ValueError("mixture bridge exponent nonfinite")
        if bridge_model == "exp_bridge":
            if not -700 <= z <= 700:
                raise ValueError("mixture bridge exponent outside numerical range")
            factor = math.exp(z)
            loss = base*factor
            grad_n = factor*(base_grad[0]-base*eta*z/n)
            grad_d = factor*base_grad[1]
            grad_q = factor*base_grad[2]
            grad_p = factor*(base*amplitude*grad_r+base_grad[2]*q_p)
        else:
            factor = 1+z
            if factor <= 0:
                raise ValueError("linear mixture bridge factor nonpositive")
            loss = base*factor
            grad_n = factor*base_grad[0]-base*eta*z/n
            grad_d = factor*base_grad[1]
            grad_q = factor*base_grad[2]
            grad_p = base*amplitude*grad_r+factor*base_grad[2]*q_p
        if loss <= 0 or not all(math.isfinite(float(v)) for v in (loss, factor, grad_n, grad_d, grad_q, *grad_p)):
            raise ValueError("v8 prediction or gradient nonfinite")
        quality_gradient = grad_q*(qa["dQproxy_dQA"] if qa is not None else 1.0)
        result = {"schema_version": VERSION, "Loss": float(loss), "NDQ_loss": base,
                  "B1_backbone_loss": base-(1-q)*gain, "quality_gain_G": gain,
                  "Q_B_proxy_or_native": q, "quality_mode": quality_mode,
                  "quality_mapping_policy": quality_mapping_policy if qa is not None else None,
                  "Q_A_mapped": qa["Q_A_mapped"] if qa is not None else None,
                  "mapped_coverage": qa["mapped_coverage"] if qa is not None else None,
                  "unmapped_mass": qa["unmapped_mass"] if qa is not None else None,
                  "quality_bridge": {key: value for key, value in qa.items()
                                     if not key.startswith("_") and key != "qa_stats"} if qa is not None else None,
                  "Q1_weighted_effect": r, "mixture_bridge_factor": factor,
                  "mixture_bridge_lambda": lam, "mixture_bridge_eta": eta,
                  "bridge_model": bridge_model,
                  "gradients": {"N_B": float(grad_n), "D_B": float(grad_d),
                                "Q_B_proxy_or_native": float(grad_q),
                                "Q_A_mapped": float(quality_gradient) if qa is not None else None,
                                "p_ambient": dict(zip(self.q1.domains, map(float, grad_p)))},
                  "elasticities_signed": {"N": n*grad_n/loss, "D": d*grad_d/loss,
                                          "Q_B_proxy_or_native": q*grad_q/loss,
                                          "Q_A_mapped": qa["Q_A_mapped"]*quality_gradient/loss
                                          if qa is not None else None},
                  "p_support": support, "Q1_manifest_sha256": self.q1.manifest_sha256,
                  "B1_fit_sha256": B1_SHA, "B7_quality_fit_sha256": self.quality_fit_sha256,
                  "units": {"N": "billion_parameters", "D": "billion_tokens",
                            "Loss": "conditional_cross_entropy", "Q_A": "Q1_native_score",
                            "Q_B_proxy": "B7_native_score_proxy"},
                  "conditional_on_quality_and_mixture_bridges": True,
                  "empirically_calibrated_A_to_B": False,
                  "Q_A_equals_Q_B_empirical_fact": False,
                  "quality_and_mixture_double_counting_not_identified": True}
        return result

    def predict_baseline_v8(self, n, d, p, weights, *, p_policy,
                            quality_mapping_policy="direct_and_near"):
        result = self.evaluate(n, d, p, weights, p_policy=p_policy,
                               quality_mapping_policy=quality_mapping_policy)
        result["mode"] = "baseline"
        return result

    def p_hessian_baseline(self, n, d, p, weights, *, p_policy="convex_hull",
                           quality_mapping_policy="direct_and_near"):
        self.q1.support(p, p_policy)
        qa = self.qa(p, quality_mapping_policy)
        base, base_grad, _ = self.base(n, d, qa["Q_B_proxy"])
        r = self.q1.weighted_effect(p, weights)
        g = self.q1.gradient(p, weights)
        h = self.q1.hessian(weights)
        qp = qa["dQproxy_dQA"]*qa["_qa_grad"]
        qh = qa["dQproxy_dQA"]*qa["_qa_hess"]
        return math.exp(r)*(base*(h+np.outer(g, g))+
                            base_grad[2]*(np.outer(qp, g)+np.outer(g, qp)+qh))


def request(model: ConditionalV8, item: dict):
    if not isinstance(item, dict) or item.get("schema_version") != VERSION:
        raise ValueError("invalid v8 request schema")
    required = {"schema_version", "mode", "N_params_B", "D_tokens_B", "p", "weights", "p_policy",
                "quality_mapping_policy"}
    if not required <= set(item):
        raise ValueError("missing v8 request field")
    common = (item["N_params_B"], item["D_tokens_B"], item["p"], item["weights"])
    kwargs = {"p_policy": item["p_policy"], "quality_mapping_policy": item["quality_mapping_policy"]}
    if item["mode"] == "baseline":
        if set(item) != required:
            raise ValueError("baseline rejects native Q_B and bridge overrides")
        return model.predict_baseline_v8(*common, **kwargs)
    allowed = required | {"quality_mode", "native_QB", "quality_bridge_scale",
                          "mixture_bridge_lambda", "mixture_bridge_eta", "bridge_model"}
    if item["mode"] != "sensitivity" or set(item)-allowed:
        raise ValueError("invalid v8 sensitivity fields")
    if "quality_mode" not in item:
        raise ValueError("sensitivity requires quality_mode")
    if item["quality_mode"] == "native_QB_sensitivity" and "native_QB" not in item:
        raise ValueError("native Q_B sensitivity requires native_QB")
    return model.evaluate(*common, **kwargs,
                          quality_mode=item["quality_mode"], native_QB=item.get("native_QB"),
                          quality_bridge_scale=item.get("quality_bridge_scale", 1.0),
                          mixture_bridge_lambda=item.get("mixture_bridge_lambda", 1.0),
                          mixture_bridge_eta=item.get("mixture_bridge_eta", 0.0),
                          bridge_model=item.get("bridge_model", "exp_bridge"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", type=Path)
    parser.add_argument("--describe", action="store_true")
    args = parser.parse_args()
    try:
        model = ConditionalV8()
        if args.describe:
            result = {"schema_version": VERSION, "formal_baseline_quality_mode": "q1_quality_baseline",
                      "B1_fit_sha256": B1_SHA, "B7_quality_fit_sha256": model.quality_fit_sha256,
                      "Q1_manifest_sha256": model.q1.manifest_sha256,
                      "support": BOUNDS, "cross_source_empirically_calibrated": False}
        elif args.request:
            result = request(model, json.loads(args.request.read_text(encoding="utf-8-sig"),
                                              object_pairs_hook=unique))
        else:
            parser.error("specify --describe or --request")
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
        return 0
    except (ValueError, KeyError, TypeError, OSError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
