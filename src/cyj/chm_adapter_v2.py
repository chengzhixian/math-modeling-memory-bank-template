"""cyj.chm.v2: B7-native NDQ diagnostics and separate CHM v1.2 contrasts."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from numbers import Real
from pathlib import Path
import subprocess
import sys
import tempfile
from functools import lru_cache

from audit_b_scaling_laws import ROOT
from quality_scaling import QualityPredictor
from q3_costs import costs, CONTEXT_SCENARIOS

VERSION = "cyj.chm.v2"
CHM_COMMIT = "a5525935b37f873235d2f650e4810a787b9a8788"
CHM_MANIFEST = "interfaces/chm/q1_interface_v1_2.json"
CHM_MANIFEST_SHA = "5885317d072739b02cdbb434fc730dde07510eb284dc857e35863adc877e914d"
CHM_FILES_SHA = {
    CHM_MANIFEST: CHM_MANIFEST_SHA,
    "src/chm/q1_interface.py": "73f4ea5f7eaa33202634e334af6da7ed6deb90a5c1aa68dcc73943acd35cfc65",
    "outputs/chm/domain_quality.csv": "458e42669bab460f5cc446c873e0e1275b9eb9b4304675363a4dc604a08197b7",
    "outputs/chm/domain_mapping.csv": "960ff8094339473b0fd72c774774dbba3cae438f3fcb5b0fb4fdc8bf9e20006a",
    "outputs/chm/local_recheck_v1/mixture_effect_ridge_v0.csv": "39e7661d1ec2b4c552715ff39d11ea32416afa3cd4013436d9f6351288a194fd",
    "outputs/chm/local_recheck_v1/mixture_reference_v0.csv": "ee3e623419982d5cce284509d014954ca436e95445ff444c7c870bed42beafe8",
    "outputs/chm/local_recheck_v1/q1_regmix_ridge_domainwise_metrics.csv": "2d22d5b98dfe27c643b2f8ca3a29834b68767c08e0dc91fcaa06f2efcb694b20",
}
B7_SHA = "e676bfb06da81c02ad968591aa9ae09da5c7cd6b56def49d59a82c371465b025"
AXES = ("N_params_B", "D_tokens_B", "Q_score")
BOUNDS = ((0.07, 11.97), (10.0, 600.0), (0.1, 1.0))


def number(value, name):
    if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number, not a string or boolean")
    return float(value)


def point(n, d, q):
    values = tuple(number(v, k) for k, v in zip(AXES, (n, d, q)))
    for k, v, (lo, hi) in zip(AXES, values, BOUNDS):
        if not lo <= v <= hi:
            raise ValueError(f"{k} outside B7 support [{lo}, {hi}]")
    return values


@lru_cache(maxsize=1)
def load_q1():
    """Materialize the pinned producer in a temporary directory, never old eta files."""
    def blob(path):
        raw = subprocess.check_output(["git", "show", f"{CHM_COMMIT}:{path}"], cwd=ROOT)
        if hashlib.sha256(raw).hexdigest() != CHM_FILES_SHA[path]:
            raise ValueError(f"pinned Q1 source hash mismatch: {path}")
        return raw

    raw_manifest = blob(CHM_MANIFEST)
    manifest = json.loads(raw_manifest)
    if (manifest.get("schema_version") != "chm.q1.v1.2"
            or manifest.get("scale_transfer_status") != "not_identified_from_attachment_A"
            or set(manifest["files"]) != {"quality", "mapping", "coefficients", "reference", "validation"}
            or {v["path"] for v in manifest["files"].values()} != set(CHM_FILES_SHA) - {CHM_MANIFEST, "src/chm/q1_interface.py"}):
        raise ValueError("unexpected Q1 producer manifest")
    with tempfile.TemporaryDirectory(prefix="cyj-q1-v12-") as directory:
        root = Path(directory)
        paths = [CHM_MANIFEST, "src/chm/q1_interface.py"] + [v["path"] for v in manifest["files"].values()]
        for relative in paths:
            if ".." in Path(relative).parts or not relative.startswith(("interfaces/chm/", "src/chm/", "outputs/chm/")):
                raise ValueError("unexpected producer path")
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw_manifest if relative == CHM_MANIFEST else blob(relative))
        spec = importlib.util.spec_from_file_location("cyj_chm_v12", root / "src/chm/q1_interface.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        producer = module.Q1Interface(root)  # producer checks normalized hashes and rows
    return producer, hashlib.sha256(raw_manifest).hexdigest()


class CHMAdapter:
    """Explicit diagnostic opt-in; implements CHM LossModel.value_grad in B7 units."""
    bounds = BOUNDS

    def __init__(self, *, mode):
        if mode != "diagnostic":
            raise ValueError("v2 is diagnostic_only; formal NDQ validation remains incomplete")
        self.model = QualityPredictor(expected_sha256=B7_SHA)
        if self.model.family != "linear_quality":
            raise ValueError("unexpected pinned B7 family")

    def value_grad(self, N_B, D_B, Q):
        n, d, q = point(N_B, D_B, Q)
        p = self.model.parameters
        nt, dt = p["A"] * n ** -p["alpha"], p["B"] * d ** -p["beta"]
        return (p["E"] + nt + dt + p["G"] * (1-q),
                (-p["alpha"] * nt/n, -p["beta"] * dt/d, -p["G"]))

    def capabilities(self):
        q1, manifest_sha = load_q1()
        return {
            "schema_version": VERSION, "status": "diagnostic_only", "ready_for_Q3": False,
            "quality_policy": {"coordinate": "B_native_Q_score", "performance_status": "diagnostic",
                "joint_NDQ_status": "diagnostic", "loss_coordinate_id": "attachment_B7_native_val_loss",
                "A_Q_mapping_status": "unidentified"},
            "p_policy": {"mode": "sensitivity_only", "unique_p_claim_allowed": False,
                "target_panel": list(q1.coefficients), "coordinate": "A4_A5_1M_target_cross_entropy_contrast",
                "cross_scale_transfer": "not_identified_from_attachment_A", "B_loss_addition_allowed": False},
            "bounds": dict(zip(AXES, BOUNDS)), "units": {"N_params_B": "1e9 parameters", "D_tokens_B": "1e9 tokens", "cost": "FLOPs"},
            "context_tokens": list(CONTEXT_SCENARIOS), "domains": list(q1.reference),
            "reference_p": dict(q1.reference), "B7_fit_sha256": B7_SHA,
            "chm_commit": CHM_COMMIT, "chm_schema": "chm.q1.v1.2", "chm_manifest_sha256": manifest_sha,
            "chm_consumed_files_sha256": CHM_FILES_SHA,
            "formal_blockers": ["B7 semi-synthetic and model-selection validation incomplete",
                "total prediction uncertainty unavailable", "team acceptance pending"],
            "uncertainty_policy": {"U1_parameter_estimation": "conditional B7 fixed-family group bootstrap only",
                "U2_model_form": "unquantified; exploratory B7 interaction comparison is not a calibrated interval",
                "U3_prediction_residual": "unquantified",
                "U4_cross_source": "unidentified; B1/B7/A loss and Q bridges absent",
                "U5_benchmark_bridge": "external zhh interface; no compatible validated bridge consumed"},
            "solver_note": "Use these B7 bounds; CHM legacy solve_generic hardcodes B1 D_min=0.134 and is not directly compatible.",
        }

    def p_sensitivity(self, mixture):
        q1, _ = load_q1()
        if not isinstance(mixture, dict) or set(mixture) != set(q1.reference):
            raise ValueError("p must contain exactly the 17 producer domains")
        values = {k: number(v, k) for k, v in mixture.items()}
        if min(values.values()) < 0 or abs(math.fsum(values.values())-1) > 1e-6:
            raise ValueError("p must be nonnegative and sum to one within 1e-6")
        return {**q1.effect_vector(values), "mode": "sensitivity_only",
                "unique_p_claim_allowed": False, "B_loss_addition_allowed": False,
                "mixture_support_status": "simplex_checked_training_convex_hull_not_checked"}

    def evaluate(self, *, N_params_B, D_tokens_B, Q_score, Q0, context_tokens,
                 quality_family, budget_FLOPs, p=None):
        n, d, q = point(N_params_B, D_tokens_B, Q_score)
        q0 = number(Q0, "Q0")
        if not BOUNDS[2][0] <= q0 <= BOUNDS[2][1] or q < q0:
            raise ValueError("Q0 must be in B7 support and Q_score >= Q0")
        context = number(context_tokens, "context_tokens")
        budget = number(budget_FLOPs, "budget_FLOPs")
        if budget <= 0:
            raise ValueError("budget_FLOPs must be positive")
        prediction = self.model.predict(n, d, q, mode="diagnostic")
        cost = costs(N_params_B=n, D_tokens_B=d, Q_score=q, Q0=q0, L_ctx=context,
                     quality_family=quality_family, budget_FLOPs=budget)
        minimum = costs(N_params_B=BOUNDS[0][0], D_tokens_B=BOUNDS[1][0], Q_score=q0,
                        Q0=q0, L_ctx=context, quality_family=quality_family)["total"]
        sensitivity = None if p is None else self.p_sensitivity(p)
        return {"schema_version": VERSION, "status": "diagnostic_only", "ready_for_Q3": False,
                "inputs": dict(zip(AXES, (n,d,q))), "prediction": prediction, "cost": cost,
                "loss_coordinate": prediction["loss_coordinate"],
                "support": {"bounds": dict(zip(AXES, BOUNDS)), "point_inside_declared_bounds": True,
                            "observed_grid_point": None, "rectangular_interpolation_assumption": True},
                "uncertainty": {"conditional_mean_interval": prediction["uncertainty"]["conditional_mean_percentile_95"],
                                "prediction_interval": None, "model_form_uncertainty": "not_quantified",
                                "cross_source_uncertainty": None,
                                "benchmark_bridge_uncertainty": None,
                                "coverage_scope": "fixed constant-G B7 semi-synthetic conditional mean only",
                                "components": {"U1_parameter_estimation": "conditional_only",
                                    "U2_model_form": "not_quantified", "U3_prediction_residual": "not_quantified",
                                    "U4_cross_source": "not_identified", "U5_benchmark_bridge": "not_consumed"}},
                "constraints": {"NDQ_support_satisfied": True, "Q_ge_Q0": True,
                    "budget_feasible": cost["budget_feasible"], "budget_residual_FLOPs": cost["budget_residual"],
                    "minimum_supported_cost_FLOPs": minimum, "budget_support_nonempty": budget >= minimum},
                "p_sensitivity": sensitivity, "B7_fit_sha256": B7_SHA,
                "chm_commit": CHM_COMMIT if p is not None else None}


def unique_object(pairs):
    out = {}
    for k,v in pairs:
        if k in out:
            raise ValueError(f"duplicate JSON key: {k}")
        out[k] = v
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--describe", action="store_true")
    group.add_argument("--request", type=Path)
    args = parser.parse_args()
    try:
        model = CHMAdapter(mode="diagnostic")
        if args.describe:
            result = model.capabilities()
        else:
            payload = json.loads(args.request.read_text(encoding="utf-8-sig"), object_pairs_hook=unique_object)
            if not isinstance(payload, dict) or set(payload) != {"schema_version", "mode", "requests"}:
                raise ValueError("expected schema_version, mode, requests")
            if payload["schema_version"] != VERSION or payload["mode"] != "diagnostic":
                raise ValueError("expected cyj.chm.v2 and explicit diagnostic mode")
            if not isinstance(payload["requests"], list) or not payload["requests"]:
                raise ValueError("requests must be a nonempty list")
            rows, seen = [], set()
            required = {"request_id", *AXES, "Q0", "context_tokens", "quality_family", "budget_FLOPs"}
            for request in payload["requests"]:
                if not isinstance(request, dict) or not required <= set(request) or set(request)-required-{"p"}:
                    raise ValueError("incorrect request fields")
                identifier = request["request_id"]
                if not isinstance(identifier, str) or not identifier.strip() or identifier in seen:
                    raise ValueError("request_id must be nonempty and unique")
                seen.add(identifier)
                rows.append({"request_id": identifier, **model.evaluate(**{k:v for k,v in request.items() if k != "request_id"})})
            result = {"schema_version": VERSION, "status": "diagnostic_only", "ready_for_Q3": False, "results": rows}
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
        return 0
    except (ValueError, TypeError, KeyError, OSError, subprocess.CalledProcessError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
