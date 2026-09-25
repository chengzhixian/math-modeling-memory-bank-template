"""Q2 numerical consumer of versioned Q1 exports and the frozen v5 B7 model.

This module has no raw-A reader. Q1 exports are a separate upstream production
stage; all A-derived numbers here come from its hash-checked output bundle.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from scipy.optimize import linprog

from joint_ndqp_scenarios import BOUNDS, ROOT, ConditionalNDQP

BUNDLE = ROOT / "outputs/chm/q1_exports/q1_q2_bundle_v1"
MAIN_NDQ = (1.0, 100.0, 0.5)
MAIN_LAMBDA = 1.0
MAIN_ETA = 0.0
VERSION = "cyj.ndqp.scenario.v6"
TOL = 1e-7


def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _csv(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _sha(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Q2Final:
    def __init__(self, bundle: Path = BUNDLE):
        self.bundle = Path(bundle)
        self.manifest = _json(self.bundle / "export_manifest.json")
        if self.manifest.get("schema_version") != "chm.q1.q2_bundle.v1" or self.manifest.get("status") != "Q1_derived_export_pending_CHM_owner_signoff":
            raise ValueError("unexpected Q1 derived bundle schema/status")
        for name, digest in self.manifest["files_sha256"].items():
            if _sha(self.bundle / name) != digest:
                raise ValueError(f"Q1 derived bundle hash mismatch: {name}")
        self.recipe_manifest = _json(self.bundle / "recipe_manifest.json")
        self.domains = self.recipe_manifest["domain_order"]
        if len(self.domains) != 17 or len(set(self.domains)) != 17:
            raise ValueError("invalid Q1 domain order")
        rows = _csv(self.bundle / "recipes_512.csv")
        if len(rows) != 512 or len({r["index"] for r in rows}) != 512:
            raise ValueError("expected 512 unique Q1 recipe candidates")
        self.indices = [r["index"] for r in rows]
        self.matrix = np.array([[float(r[d]) for d in self.domains] for r in rows])
        if not np.isfinite(self.matrix).all() or np.min(self.matrix) < 0 or not np.allclose(self.matrix.sum(axis=1), 1, atol=1e-12):
            raise ValueError("invalid normalized Q1 recipe matrix")
        self.v5 = ConditionalNDQP()
        self.reference = np.array([self.v5.a["reference"][d] for d in self.domains])
        local_ref = {r["mixture_domain"]: float(r["p_ref"]) for r in _csv(self.bundle / "reference.csv")}
        if list(local_ref) != self.domains or not np.allclose(self.reference, [local_ref[d] for d in self.domains], atol=1e-13):
            raise ValueError("Q1 bundle reference disagrees with frozen v5 producer")
        local_coeff = {r["target"]: r for r in _csv(self.bundle / "coefficients.csv")}
        if set(local_coeff) != set(self.v5.a["coefficients"]):
            raise ValueError("Q1 bundle target set differs from frozen v5 producer")
        self.targets = list(self.v5.a["coefficients"])
        for target in self.targets:
            row = local_coeff[target]
            frozen = self.v5.a["coefficients"][target]
            if not all(math.isclose(float(row[k]), float(frozen[k]), abs_tol=1e-13) for k in ("intercept", *self.domains)):
                raise ValueError(f"Q1 coefficient mismatch: {target}")
        self.beta = np.array([[float(local_coeff[k][d]) for d in self.domains] for k in self.targets])
        self.reference_loss = np.array([self.v5.a["reference_loss"][k] for k in self.targets])
        self.relative_beta = self.beta / self.reference_loss[:, None]
        self.relative_recipe_effects = (self.matrix - self.reference) @ self.relative_beta.T
        qmap = _json(self.bundle / "qa_mapping.json")
        if qmap["coordinate"] != "A_composite_quality_proxy_z" or len(qmap["rows"]) != 17:
            raise ValueError("unexpected Q1 QA mapping")
        mapping = {r["mixture_domain"]: r for r in qmap["rows"]}
        self.qa = [mapping[d] for d in self.domains]

    def p_dict(self, point):
        a = np.asarray(point, dtype=float)
        if a.shape != (17,) or not np.isfinite(a).all() or np.min(a) < -TOL or abs(float(a.sum()) - 1) > TOL:
            raise ValueError("p must be a finite 17-domain simplex point")
        return dict(zip(self.domains, map(float, a)))

    def point(self, p):
        if not isinstance(p, dict) or set(p) != set(self.domains):
            raise ValueError("p must name exactly the 17 Q1 domains")
        return np.array([float(p[d]) for d in self.domains])

    def hull(self, p):
        point = self.point(p) if isinstance(p, dict) else np.asarray(p, dtype=float)
        self.p_dict(point)
        aeq = np.vstack([self.matrix.T, np.ones(len(self.matrix))])
        beq = np.r_[point, 1.0]
        result = linprog(np.zeros(len(self.matrix)), A_eq=aeq, b_eq=beq,
                         bounds=(0, None), method="highs")
        residual = float(np.max(np.abs(aeq @ result.x - beq))) if result.success else None
        ok = bool(result.success and residual <= TOL)
        return {"inside": ok, "status": "in_Q1_A4_convex_hull" if ok else "outside_Q1_A4_convex_hull",
                "max_residual": residual,
                "certificate": self._weights(result.x) if ok else []}

    def _weights(self, weights):
        return [{"index": self.indices[i], "weight": float(v)} for i, v in enumerate(weights) if v > 1e-8]

    def qa_stats(self, p, mapping_policy="direct"):
        if mapping_policy not in ("direct", "direct_and_near"):
            raise ValueError("invalid Q1 quality mapping policy")
        point = self.point(p) if isinstance(p, dict) else np.asarray(p, dtype=float)
        allowed = {"direct"} if mapping_policy == "direct" else {"direct", "near_direct"}
        mask = np.array([r["mapping_type"] in allowed and r["Q_A"] is not None for r in self.qa], bool)
        q = np.array([float(r["Q_A"]) if r["Q_A"] is not None else 0 for r in self.qa])
        coverage = float(point @ mask)
        numerator = float(point @ (mask * q))
        return {"mapping_policy": mapping_policy, "covered_mass": coverage,
                "unmapped_mass": float(point.sum()) - coverage,
                "weighted_Q_A": numerator, "mean_Q_A_on_mapped": numerator / coverage if coverage > 0 else None,
                "Q_A_coordinate": "Q1 family-balanced z-score; never B7 Q_score"}

    def qa_constraints(self, policy):
        """Two reference anchored *linear* restrictions on recipe convex weights."""
        allowed = {"direct"} if policy == "direct" else {"direct", "near_direct"}
        mask = np.array([r["mapping_type"] in allowed and r["Q_A"] is not None for r in self.qa], float)
        q = np.array([float(r["Q_A"]) if r["Q_A"] is not None else 0 for r in self.qa])
        ref_coverage = float(self.reference @ mask)
        ref_mean = float(self.reference @ (mask * q)) / ref_coverage
        candidate_coverage = self.matrix @ mask
        candidate_quality_margin = self.matrix @ (mask * (q - ref_mean))
        # Coverage >= reference; conditional mean Q_A >= reference. Unknown domains are not imputed.
        aub = np.vstack([-candidate_coverage, -candidate_quality_margin])
        bub = np.array([-ref_coverage, 0.0])
        return aub, bub, {"reference_covered_mass": ref_coverage, "reference_mean_Q_A": ref_mean}

    def weight_policy(self, name):
        if name == "equal_13":
            return {k: 1 / len(self.targets) for k in self.targets}
        if name in ("arxiv_only", "pile_cc_only"):
            return {name.removesuffix("_only"): 1.0}
        raise ValueError("unsupported preset target policy")

    def _target_weight_vector(self, weights):
        if not isinstance(weights, dict) or not weights or set(weights) - set(self.targets):
            raise ValueError("weights must name Q1 targets")
        values = np.array([float(weights.get(k, 0)) for k in self.targets])
        if not np.isfinite(values).all() or np.min(values) < 0 or abs(float(values.sum()) - 1) > 1e-10:
            raise ValueError("weights must be a nonnegative unit simplex")
        return values

    def _positivity_constraints(self, weights, lam, eta):
        if not math.isfinite(lam) or not math.isfinite(eta) or lam < 0:
            raise ValueError("invalid bridge scenario")
        effect = self.relative_recipe_effects @ weights
        rows, bounds = [], []
        for n in (BOUNDS[0][0], BOUNDS[0][1]):
            scale = (n ** -eta) * lam
            rows.append(-scale * effect)
            bounds.append(1 - 1e-9)
        return np.array(rows), np.array(bounds)

    def optimize(self, policy, *, weights=None, lam=MAIN_LAMBDA, eta=MAIN_ETA,
                 N=MAIN_NDQ[0], D=MAIN_NDQ[1], Q_B=MAIN_NDQ[2]):
        """Ridge conditional LP over 512 Q1 recipes; scenario is not B-calibrated."""
        if policy not in ("observed_512", "convex_hull", "quality_direct", "quality_direct_and_near", "minimax_13"):
            raise ValueError("unknown p policy")
        w = self._target_weight_vector(weights if weights is not None else self.weight_policy("equal_13"))
        if not math.isfinite(lam) or not math.isfinite(eta) or lam < 0:
            raise ValueError("invalid bridge scenario")
        if lam == 0:
            self.v5._point(N, D, Q_B)
            return {"status": "all_feasible_p_tied", "policy": policy, "unique_optimum": False,
                    "conditional_loss": self.v5.evaluate_ndq(N, D, Q_B)["loss"],
                    "reason": "lambda=0 removes every p term from the conditional loss"}
        effect = self.relative_recipe_effects @ w
        pos_a, pos_b = self._positivity_constraints(w, lam, eta)
        quality = None
        qa_a, qa_b = pos_a, pos_b
        if policy.startswith("quality_"):
            qa_a0, qa_b0, quality = self.qa_constraints("direct" if policy == "quality_direct" else "direct_and_near")
            qa_a, qa_b = np.vstack([pos_a, qa_a0]), np.r_[pos_b, qa_b0]
        if policy == "observed_512":
            feasible = np.where(np.all(pos_a <= pos_b[:, None] + 1e-12, axis=0))[0]
            if len(feasible) == 0:
                return {"status": "infeasible", "policy": policy}
            chosen = int(feasible[np.argmin(effect[feasible])])
            gamma = np.eye(1, len(self.matrix), chosen).ravel()
            solver = "enumerate_512"
        else:
            aeq = np.ones((1, len(self.matrix)))
            beq = np.ones(1)
            if policy == "minimax_13":
                # Auxiliary t bounds all 13 normalized target effects.
                objective = np.r_[np.zeros(len(self.matrix)), 1.0]
                aeq = np.c_[aeq, np.zeros(1)]
                aub = np.vstack([np.c_[qa_a, np.zeros(len(qa_a))],
                                 np.c_[self.relative_recipe_effects.T, -np.ones(len(self.targets))]])
                bub = np.r_[qa_b, np.zeros(len(self.targets))]
                bounds = [(0, None)] * len(self.matrix) + [(None, None)]
            else:
                objective, aub, bub = effect, qa_a, qa_b
                bounds = [(0, None)] * len(self.matrix)
            result = linprog(objective, A_ub=aub, b_ub=bub, A_eq=aeq, b_eq=beq,
                             bounds=bounds, method="highs")
            if not result.success:
                return {"status": "infeasible_or_solver_failed", "policy": policy,
                        "solver_message": result.message}
            gamma = result.x[:len(self.matrix)]
            solver = "HiGHS_linear_program"
        point = gamma @ self.matrix
        p = self.p_dict(point)
        targets = (point - self.reference) @ self.beta.T
        relative = targets / self.reference_loss
        prediction = self.v5.evaluate_ndqp_scenario(N, D, Q_B, p=p,
            weights=dict(zip(self.targets, map(float, w))), bridge_lambda=lam, eta=eta)
        out = {"status": "optimal_conditional", "policy": policy, "solver": solver,
               "p": p, "recipe_weights": self._weights(gamma),
               "target_absolute_A_loss_change": dict(zip(self.targets, map(float, targets))),
               "target_relative_A_loss_change": dict(zip(self.targets, map(float, relative))),
               "weighted_relative_A_effect": float(relative @ w),
               "conditional_loss": prediction["loss"], "factor": prediction["factor"],
               "qa_direct": self.qa_stats(p, "direct"),
               "qa_direct_and_near": self.qa_stats(p, "direct_and_near"),
               "simplex_residual": abs(float(point.sum()) - 1),
               "mixture_reconstruction_residual": float(np.max(np.abs(gamma @ self.matrix - point))),
               "min_factor_over_B7_N": prediction["minimum_factor_over_B7_N"],
               "quality_constraint": quality, "ready_for_Q3": False,
               "empirically_calibrated_A_to_B": False}
        if policy == "observed_512":
            out["selected_observed_Q1_index"] = self.indices[chosen]
        return out

    def evaluate(self, N, D, Q_B, p, weights, lam, eta, *, p_policy="convex_hull",
                 model_variant="ridge_main"):
        if model_variant != "ridge_main":
            raise ValueError("interaction_sensitivity has metrics only; full Q1 coefficients unavailable")
        point = self.point(p)
        self.p_dict(point)
        if p_policy == "observed_512":
            observed = bool(np.any(np.max(np.abs(self.matrix - point), axis=1) <= TOL))
            if not observed:
                raise ValueError("p is not one of the 512 Q1 observed recipes")
            membership = {"inside": True, "status": "observed_Q1_A4_recipe"}
        elif p_policy in ("convex_hull", "quality_direct", "quality_direct_and_near"):
            membership = self.hull(point)
            if not membership["inside"]:
                raise ValueError("p is outside the Q1 A4 recipe convex hull")
            if p_policy.startswith("quality_"):
                mapping = "direct" if p_policy == "quality_direct" else "direct_and_near"
                constraints, bounds, ref = self.qa_constraints(mapping)
                # The constraints are expressed on convex weights; direct p check is equivalent.
                stats = self.qa_stats(p, mapping)
                if stats["covered_mass"] + TOL < ref["reference_covered_mass"] or stats["mean_Q_A_on_mapped"] + TOL < ref["reference_mean_Q_A"]:
                    raise ValueError("p violates the Q1 quality coverage/mean policy")
        elif p_policy == "algebraic_reference_only":
            if not np.allclose(point, self.reference, atol=TOL):
                raise ValueError("algebraic reference mode permits p_ref only")
            membership = self.hull(point)
        else:
            raise ValueError("invalid p policy")
        if not isinstance(weights, dict):
            raise ValueError("weights must be an object")
        canonical_weights = {key: weights[key] for key in self.targets if key in weights}
        result = self.v5.evaluate_ndqp_scenario(N, D, Q_B, p=p, weights=canonical_weights,
                                                bridge_lambda=lam, eta=eta)
        result.update(schema_version=VERSION, p_policy=p_policy, p_support=membership,
                      model_variant=model_variant, qa_direct=self.qa_stats(p, "direct"),
                      qa_direct_and_near=self.qa_stats(p, "direct_and_near"),
                      q1_export_manifest_sha256=_sha(self.bundle / "export_manifest.json"),
                      q1_export_status=self.manifest["status"],
                      empirically_calibrated_A_to_B=False, scenario_solution_ready=True)
        return result
