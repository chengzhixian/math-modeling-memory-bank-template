"""Explicit, uncalibrated A-to-B mixture scenarios on the frozen B7 surface.

N and D are in billions.  No default bridge coefficient is provided.  This
module reads only the immutable CHM Q1 producer objects, never raw A tables.
"""
from __future__ import annotations

import csv
import argparse
import hashlib
import io
import json
import math
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHM_COMMIT = "cdda1ad62c5c7eb72b413c4228caeff87d2bad30"
MANIFEST_PATH = "interfaces/chm/q1_interface_v1_3.json"
N_REF = 1.0  # billion parameters; inside B7 support
VERSION = "cyj.ndqp.scenario.v5"
BOUNDS = ((0.07, 11.97), (10.0, 600.0), (0.1, 1.0))


def _finite(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite numeric value")
    return float(value)


def _blob(path):
    if not path.startswith(("interfaces/chm/", "outputs/chm/")) or ".." in Path(path).parts:
        raise ValueError("invalid producer path")
    return subprocess.check_output(["git", "show", f"{CHM_COMMIT}:{path}"], cwd=ROOT)


def _normalized(raw):
    return raw.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


@lru_cache(maxsize=1)
def producer():
    manifest_raw = _blob(MANIFEST_PATH)
    manifest = json.loads(manifest_raw)
    if (manifest.get("schema_version") != "chm.q1.v1.3"
            or manifest.get("scale_transfer_status") != "not_identified_from_attachment_A"
            or set(manifest.get("files", {})) != {"quality", "mapping", "coefficients", "reference", "validation"}):
        raise ValueError("unexpected CHM Q1 producer")
    tables = {}
    for name, item in manifest["files"].items():
        raw = _blob(item["path"])
        if hashlib.sha256(_normalized(raw)).hexdigest() != item["sha256"]:
            raise ValueError(f"CHM Q1 file hash mismatch: {name}")
        rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
        if len(rows) != item["rows"]:
            raise ValueError(f"CHM Q1 row count mismatch: {name}")
        tables[name] = rows
    reference = {r["mixture_domain"]: float(r["p_ref"]) for r in tables["reference"]}
    if len(reference) != 17 or not math.isclose(sum(reference.values()), 1, abs_tol=1e-6):
        raise ValueError("invalid reference composition")
    coefficients = {r["target"]: r for r in tables["coefficients"]}
    if len(coefficients) != 13:
        raise ValueError("expected 13 target coefficients")
    # The fitted Ridge intercept plus beta dot p_ref is a model prediction,
    # not a measured B val_loss or a mean across heterogeneous targets.
    reference_loss = {}
    for target, row in coefficients.items():
        value = float(row["intercept"]) + math.fsum(float(row[d]) * p for d, p in reference.items())
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"nonpositive fitted A reference Loss: {target}")
        reference_loss[target] = value
    return {"manifest_sha256": hashlib.sha256(manifest_raw).hexdigest(),
            "manifest": manifest, "reference": reference, "coefficients": coefficients,
            "reference_loss": reference_loss, "validation": tables["validation"],
            "mapping_type": {r["mixture_domain"]: r["mapping_type"] for r in tables["mapping"]}}


class ConditionalNDQP:
    """A diagnostic interface; lambda, eta and target weights are explicit inputs."""

    def __init__(self):
        path = ROOT / "outputs/cyj/quality/b7_joint_fit.json"
        frozen = json.loads(path.read_text(encoding="utf-8"))
        identity = json.loads((ROOT / "outputs/cyj/quality/b7_identifiability.json").read_text(encoding="utf-8"))
        if (identity["model_hash"] != hashlib.sha256(path.read_bytes()).hexdigest()
                or frozen["source_hash"] != "880fd265ca3e1d9bc93b4559af7ed7c18f89040634266c50bae03d88486e0f3a"
                or frozen["ready_for_Q3"]):
            raise ValueError("frozen v4 B7 model identity changed")
        self.theta = tuple(frozen["model"]["theta"])
        self.a = producer()

    @staticmethod
    def _point(n, d, q):
        values = tuple(_finite(v, name) for name, v in zip(("N", "D", "Q_B"), (n, d, q)))
        if any(not lo <= value <= hi for value, (lo, hi) in zip(values, BOUNDS)):
            raise ValueError("NDQ point outside B7 support")
        return values

    def _base_value_grad(self, n, d, q):
        e, a, b, alpha, beta, g0, gn, gd = self.theta
        gain = g0 + gn * math.log(n) + gd * math.log(d / 100)
        value = e + a * n ** -alpha + b * d ** -beta + (1 - q) * gain
        gradient = (-alpha * a * n ** (-alpha - 1) + (1 - q) * gn / n,
                    -beta * b * d ** (-beta - 1) + (1 - q) * gd / d, -gain)
        return value, gradient

    def _scenario(self, p, weights, bridge_lambda, eta):
        lam = _finite(bridge_lambda, "bridge_lambda")
        exponent = _finite(eta, "eta")
        if lam < 0:
            raise ValueError("bridge_lambda must be nonnegative in this scenario family")
        ref = self.a["reference"]
        if not isinstance(p, dict) or set(p) != set(ref):
            raise ValueError("p must contain exactly the 17 CHM domains")
        mix = {d: _finite(p[d], d) for d in ref}
        if min(mix.values()) < 0 or abs(math.fsum(mix.values()) - 1) > 1e-6:
            raise ValueError("p must be a nonnegative unit simplex point")
        targets = self.a["coefficients"]
        if not isinstance(weights, dict) or not weights or set(weights) - set(targets):
            raise ValueError("weights must explicitly name CHM targets")
        w = {k: _finite(v, k) for k, v in weights.items()}
        if min(w.values()) < 0 or not math.isclose(math.fsum(w.values()), 1, abs_tol=1e-10):
            raise ValueError("target weights must form a unit simplex")
        relative = 0.0
        slope = {d: 0.0 for d in ref}
        for target, weight in w.items():
            row = targets[target]
            scale = self.a["reference_loss"][target]
            relative += weight * math.fsum(float(row[d]) * (mix[d] - ref[d]) for d in ref) / scale
            for d in ref:
                slope[d] += weight * float(row[d]) / scale
        return mix, w, lam, exponent, relative, slope

    def evaluate_ndq(self, N_params_B, D_tokens_B, Q_score):
        n, d, q = self._point(N_params_B, D_tokens_B, Q_score)
        value, gradient = self._base_value_grad(n, d, q)
        return {"loss": value, "gradient": dict(zip(("N", "D", "Q_B"), gradient)),
                "loss_coordinate": "attachment_B7_native_val_loss"}

    def evaluate_ndqp_scenario(self, N_params_B, D_tokens_B, Q_score, *, p, weights,
                               bridge_lambda, eta):
        n, d, q = self._point(N_params_B, D_tokens_B, Q_score)
        mix, w, lam, exponent, relative, slope = self._scenario(p, weights, bridge_lambda, eta)
        baseline, (bn, bd, bq) = self._base_value_grad(n, d, q)
        phi = (n / N_REF) ** -exponent
        h = 1 + lam * phi * relative
        # For fixed p and weights, phi is monotone in N.  Its minimum factor
        # over the entire declared B7 N interval is attained at an endpoint.
        support_factors = [1 + lam * (edge / N_REF) ** -exponent * relative
                           for edge in (BOUNDS[0][0], BOUNDS[0][1])]
        minimum_factor = min(support_factors)
        if not math.isfinite(h) or not math.isfinite(minimum_factor) or minimum_factor <= 0:
            raise ValueError("nonpositive conditional Loss factor somewhere on B7 N support")
        value = baseline * h
        grad = {"N": h * bn - baseline * lam * phi * exponent * relative / n,
                "D": h * bd, "Q_B": h * bq,
                "p": {domain: baseline * lam * phi * derivative for domain, derivative in slope.items()}}
        if not math.isfinite(value) or not all(map(math.isfinite, (grad["N"], grad["D"], grad["Q_B"], *grad["p"].values()))):
            raise ValueError("nonfinite conditional output")
        return {"loss": value, "baseline_loss": baseline, "factor": h,
                "minimum_factor_over_B7_N": minimum_factor, "relative_A_effect": relative,
                "gradient": grad, "improvement_elasticity": {
                    axis: -x * grad[axis] / value for axis, x in (("N", n), ("D", d), ("Q_B", q))},
                "assumptions": {"bridge_lambda": lam, "eta": exponent, "weights": w, "N_ref_B": N_REF},
                "support": "B7_rectangle_for_this_exact_p; p_simplex_checked; A_training_recipe_convex_hull_unverified",
                "ready_for_Q3": False}

    def transfer_derivative(self, result, donor, recipient):
        slopes = result["gradient"]["p"]
        if donor not in slopes or recipient not in slopes or donor == recipient:
            raise ValueError("invalid named transfer")
        return slopes[recipient] - slopes[donor]

    def gradient(self, N_params_B, D_tokens_B, Q_score, *, p, weights, bridge_lambda, eta):
        """Return N/D/Q partials and 17 ambient p partials for an explicit scenario."""
        return self.evaluate_ndqp_scenario(N_params_B, D_tokens_B, Q_score, p=p,
            weights=weights, bridge_lambda=bridge_lambda, eta=eta)["gradient"]

    def local_substitution(self, result, numerator, denominator):
        grad = result["gradient"]
        if numerator not in ("N", "D", "Q_B") or denominator not in ("N", "D", "Q_B") or numerator == denominator:
            raise ValueError("invalid substitution axes")
        if abs(grad[denominator]) <= 1e-14 or grad["N"] >= 0 or grad["D"] >= 0 or grad["Q_B"] >= 0:
            return {"status": "undefined", "value": None}
        return {"status": "defined_local_only", "value": -grad[numerator] / grad[denominator]}

    def equal_loss_root(self, *, baseline, axis, changed_axis, changed_value, p, weights, bridge_lambda, eta):
        """Bisection on one supported NDQ axis; never extrapolates a root."""
        keys = ("N", "D", "Q_B")
        if axis not in keys or changed_axis not in keys or axis == changed_axis or not isinstance(baseline, dict) or set(baseline) != set(keys):
            raise ValueError("invalid equal-loss request")
        reference = self.evaluate_ndqp_scenario(*(baseline[k] for k in keys), p=p, weights=weights,
            bridge_lambda=bridge_lambda, eta=eta)["loss"]
        point = baseline.copy()
        point[changed_axis] = changed_value
        lo, hi = BOUNDS[keys.index(axis)]

        def residual(x):
            point[axis] = x
            return self.evaluate_ndqp_scenario(*(point[k] for k in keys), p=p, weights=weights,
                bridge_lambda=bridge_lambda, eta=eta)["loss"] - reference

        f_lo, f_hi = residual(lo), residual(hi)
        if f_lo == 0 or f_hi == 0:
            return {"status": "supported", "value": lo if f_lo == 0 else hi}
        if f_lo * f_hi > 0:
            return {"status": "no_equal_loss_root_in_support", "value": None}
        values = [residual(lo + (hi - lo) * i / 32) for i in range(33)]
        if not (all(values[i] >= values[i + 1] for i in range(32))
                or all(values[i] <= values[i + 1] for i in range(32))):
            return {"status": "undefined_nonmonotone_conditional_curve", "value": None}
        for _ in range(65):
            mid = (lo + hi) / 2
            f_mid = residual(mid)
            if f_lo * f_mid <= 0:
                hi, f_hi = mid, f_mid
            else:
                lo, f_lo = mid, f_mid
        return {"status": "supported", "value": (lo + hi) / 2}

    def support(self):
        return {"B7": dict(zip(("N_params_B", "D_tokens_B", "Q_score"), BOUNDS)),
                "p": "exact supplied 17-domain simplex point; H>0 over B7 N checked for that point; training convex hull not certified"}

    def calibration_status(self):
        return {"identified_B_native": "conditional B7 semi-synthetic fit",
                "identified_A_native": "fitted 1M Ridge target contrasts and fitted positive reference Loss",
                "scenario_bridge": "lambda and eta unidentified; weights are decision scenarios",
                "formal_ready": False, "ready_for_Q3": False, "conditional_diagnostic": True}

    def assumptions(self):
        return {"formula": "L_B(N,D,Q_B)*(1+lambda*(N/1B)^(-eta)*sum_k w_k*m_k(p)/L_A_k_ref)",
                "N_ref_B": N_REF, "producer_commit": CHM_COMMIT,
                "producer_schema": "chm.q1.v1.3", "producer_manifest_sha256": self.a["manifest_sha256"],
                "A_reference_loss_kind": "fitted Ridge prediction at p_ref, not observed B loss",
                "quality_mapping": "Q_A to Q_B unidentified; Q_B independent input",
                **self.calibration_status()}


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--describe", action="store_true")
    group.add_argument("--request", type=Path)
    args = parser.parse_args()
    try:
        model = ConditionalNDQP()
        if args.describe:
            result = {"schema_version": VERSION, "assumptions": model.assumptions(),
                      "support": model.support(), "calibration_status": model.calibration_status()}
        else:
            request = json.loads(args.request.read_text(encoding="utf-8-sig"), object_pairs_hook=_unique_pairs)
            if (not isinstance(request, dict) or set(request) != {"schema_version", "mode", "requests"}
                    or request["schema_version"] != VERSION or request["mode"] != "conditional_diagnostic"
                    or not isinstance(request["requests"], list) or not request["requests"]):
                raise ValueError("expected explicit cyj.ndqp.scenario.v5 conditional_diagnostic batch")
            fields = {"request_id", "N_params_B", "D_tokens_B", "Q_score", "p",
                      "weights", "bridge_lambda", "eta"}
            seen, rows = set(), []
            for item in request["requests"]:
                if not isinstance(item, dict) or set(item) != fields:
                    raise ValueError("incorrect scenario fields")
                identity = item["request_id"]
                if not isinstance(identity, str) or not identity.strip() or identity in seen:
                    raise ValueError("empty or duplicate request_id")
                seen.add(identity)
                result = model.evaluate_ndqp_scenario(**{k: v for k, v in item.items() if k != "request_id"})
                rows.append({"request_id": identity, **result})
            result = {"schema_version": VERSION, "mode": "conditional_diagnostic",
                      "ready_for_Q3": False, "results": rows}
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
        return 0
    except (ValueError, TypeError, KeyError, OSError, subprocess.CalledProcessError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
