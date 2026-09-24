"""CYJ v3 conditional B7 candidate and separate A-side p sensitivity."""
from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from pathlib import Path

from audit_b_scaling_laws import ROOT, sha256
from b7_formal_model import BOUNDS, FAMILY, OUTPUT as MODEL_OUTPUT, elasticities, predict_gradient, substitution_rates
from build_b7_frozen_uncertainty import OUTPUT as UNCERTAINTY_OUTPUT, interval
from chm_adapter_v2 import load_q1, number, unique_object
from q3_costs import CONTEXT_SCENARIOS, costs
from validate_b7_frozen_model import OUTPUT as VALIDATION_OUTPUT

VERSION = "cyj.chm.v3"
AXES = ("N_params_B", "D_tokens_B", "Q_score")
EXPECTED_B7 = "880fd265ca3e1d9bc93b4559af7ed7c18f89040634266c50bae03d88486e0f3a"
STATUS = "conditional_within_B7_pending_independent_test"


def checked_point(n, d, q):
    values = tuple(number(v, k) for k, v in zip(AXES, (n, d, q)))
    for name, value, (lo, hi) in zip(AXES, values, BOUNDS):
        if not lo <= value <= hi:
            raise ValueError(f"{name} outside B7 support [{lo}, {hi}]")
    return values


class CHMAdapterV3:
    bounds = BOUNDS

    def __init__(self, *, mode: str):
        if mode != "conditional_diagnostic":
            raise ValueError("v3 scientific gate remains closed; use explicit conditional_diagnostic")
        self.frozen = json.loads(MODEL_OUTPUT.read_text(encoding="utf-8"))
        self.validation = json.loads(VALIDATION_OUTPUT.read_text(encoding="utf-8"))
        self.uncertainty = json.loads(UNCERTAINTY_OUTPUT.read_text(encoding="utf-8"))
        if (self.frozen["B7_sha256"] != EXPECTED_B7 or self.frozen["family"] != FAMILY
                or self.frozen["ready_for_Q3"] or self.validation["ready_for_Q3_candidate"]
                or self.validation["frozen_model_sha256"] != sha256(MODEL_OUTPUT)
                or self.uncertainty["frozen_model_sha256"] != sha256(MODEL_OUTPUT)
                or self.uncertainty["validation_sha256"] != sha256(VALIDATION_OUTPUT)
                or self.uncertainty["ready_for_Q3"]):
            raise ValueError("B7 frozen model / validation / uncertainty identity mismatch")
        self.parameters = self.frozen["parameters"]

    def value_grad(self, N_B, D_B, Q):
        return predict_gradient(*checked_point(N_B, D_B, Q), self.parameters)

    def elasticities(self, N_B, D_B, Q):
        return dict(zip(AXES, elasticities(*checked_point(N_B, D_B, Q), self.parameters)))

    def substitution_rates(self, N_B, D_B, Q):
        return substitution_rates(*checked_point(N_B, D_B, Q), self.parameters)

    def prediction_interval(self, N_B, D_B, Q):
        return interval(*checked_point(N_B, D_B, Q), self.parameters, self.uncertainty)

    def p_sensitivity(self, mixture):
        q1, _ = load_q1()
        if not isinstance(mixture, dict) or set(mixture) != set(q1.reference):
            raise ValueError("p must contain exactly the 17 producer domains")
        values = {k: number(v, k) for k, v in mixture.items()}
        if min(values.values()) < 0 or abs(math.fsum(values.values()) - 1) > 1e-6:
            raise ValueError("p must be nonnegative and sum to one within 1e-6")
        return {**q1.effect_vector(values), "mode": "sensitivity_only",
                "unique_p_claim_allowed": False, "B_loss_addition_allowed": False,
                "mixture_support_status": "simplex_checked_training_convex_hull_not_checked"}

    def capabilities(self):
        q1, q1_manifest_sha = load_q1()
        return {"schema_version": VERSION, "status": STATUS, "ready_for_Q3": False,
                "formal_result_scope": None, "candidate_result_scope": "NDQ_with_p_sensitivity",
                "quality_policy": {"coordinate": "B_native_Q_score",
                                   "performance_status": "conditional_within_B7",
                                   "joint_NDQ_status": "conditional_within_B7",
                                   "validation_scope": "within_official_attachment_B7_semi_synthetic",
                                   "loss_coordinate_id": "attachment_B7_native_val_loss",
                                   "A_Q_mapping_status": "unidentified"},
                "p_policy": {"mode": "sensitivity_only", "target_panel": list(q1.coefficients),
                             "unique_p_claim_allowed": False, "B_loss_addition_allowed": False,
                             "cross_scale_transfer": "not_identified_from_attachment_A"},
                "bounds": dict(zip(AXES, BOUNDS)),
                "units": {"N_params_B": "1e9 parameters", "D_tokens_B": "1e9 tokens",
                          "Q_score": "B-native unitless", "loss": "B7 native val_loss",
                          "gradient_N": "loss per 1e9 parameters",
                          "gradient_D": "loss per 1e9 tokens", "gradient_Q": "loss per Q unit",
                          "cost": "FLOPs"},
                "context_tokens": list(CONTEXT_SCENARIOS), "reference_p": dict(q1.reference),
                "B7_source_sha256": EXPECTED_B7,
                "frozen_model_sha256": sha256(MODEL_OUTPUT),
                "validation_sha256": sha256(VALIDATION_OUTPUT),
                "uncertainty_sha256": sha256(UNCERTAINTY_OUTPUT),
                "q1_schema": "chm.q1.v1.2", "q1_manifest_sha256": q1_manifest_sha,
                "uncertainty_policy": {"U1_parameter_estimation": "500 ND-cluster bootstrap fits",
                                       "U2_model_form": "pointwise difference from constant-G baseline",
                                       "U3_prediction_residual": "leave-N OOF empirical residual draw",
                                       "U4_cross_source": None, "U5_benchmark_bridge": None,
                                       "coverage_calibrated": False},
                "formal_blockers": ["B7 family proposed after full-source inspection; no untouched test",
                                    "empirical interval has no independent coverage calibration",
                                    "CHM owner consumer acceptance pending"]}

    def evaluate(self, *, N_params_B, D_tokens_B, Q_score, Q0, context_tokens,
                 quality_family, budget_FLOPs, p=None):
        n, d, q = checked_point(N_params_B, D_tokens_B, Q_score)
        q0, context, budget = (number(Q0, "Q0"), number(context_tokens, "context_tokens"),
                               number(budget_FLOPs, "budget_FLOPs"))
        if not BOUNDS[2][0] <= q0 <= BOUNDS[2][1] or q < q0 or budget <= 0:
            raise ValueError("invalid Q0, Q<Q0 or nonpositive budget")
        value, gradient = self.value_grad(n, d, q)
        prediction = self.prediction_interval(n, d, q)
        cost = costs(N_params_B=n, D_tokens_B=d, Q_score=q, Q0=q0,
                     L_ctx=context, quality_family=quality_family, budget_FLOPs=budget)
        minimum = costs(N_params_B=BOUNDS[0][0], D_tokens_B=BOUNDS[1][0], Q_score=q0,
                        Q0=q0, L_ctx=context, quality_family=quality_family)["total"]
        return {"schema_version": VERSION, "status": STATUS, "ready_for_Q3": False,
                "inputs": dict(zip(AXES, (n, d, q))),
                "prediction": {"loss_value": value, "gradient": dict(zip(AXES, gradient)),
                               "elasticities": self.elasticities(n, d, q),
                               "substitution_rates": self.substitution_rates(n, d, q),
                               "uncertainty": prediction,
                               "loss_coordinate": "attachment_B7_native_val_loss"},
                "cost": cost,
                "constraints": {"NDQ_support_satisfied": True, "Q_ge_Q0": True,
                                "budget_feasible": cost["budget_feasible"],
                                "minimum_supported_cost_FLOPs": minimum,
                                "budget_support_nonempty": budget >= minimum},
                "p_sensitivity": None if p is None else self.p_sensitivity(p),
                "cross_source_uncertainty": None, "benchmark_bridge_uncertainty": None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--describe", action="store_true")
    group.add_argument("--request", type=Path)
    args = parser.parse_args()
    try:
        model = CHMAdapterV3(mode="conditional_diagnostic")
        if args.describe:
            response = model.capabilities()
        else:
            request = json.loads(args.request.read_text(encoding="utf-8-sig"), object_pairs_hook=unique_object)
            if not isinstance(request, dict) or set(request) != {"schema_version", "mode", "requests"}:
                raise ValueError("expected schema_version, mode, requests")
            if request["schema_version"] != VERSION or request["mode"] != "conditional_diagnostic":
                raise ValueError("explicit conditional_diagnostic v3 mode required")
            rows, seen = [], set()
            required = {"request_id", *AXES, "Q0", "context_tokens", "quality_family", "budget_FLOPs"}
            if not isinstance(request["requests"], list) or not request["requests"]:
                raise ValueError("requests must be a nonempty list")
            for row in request["requests"]:
                if not isinstance(row, dict) or not required <= set(row) or set(row) - required - {"p"}:
                    raise ValueError("incorrect request fields")
                identifier = row["request_id"]
                if not isinstance(identifier, str) or not identifier.strip() or identifier in seen:
                    raise ValueError("request_id must be nonempty and unique")
                seen.add(identifier)
                rows.append({"request_id": identifier,
                             **model.evaluate(**{k: v for k, v in row.items() if k != "request_id"})})
            response = {"schema_version": VERSION, "status": STATUS,
                        "ready_for_Q3": False, "results": rows}
        print(json.dumps(response, ensure_ascii=False, allow_nan=False))
        return 0
    except (ValueError, TypeError, KeyError, OSError, subprocess.CalledProcessError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
