"""Consume the versioned Q1 second-order candidate without opening raw A data.

The reported interaction is a fitted, basis-specific 1M Q1 response contrast.
It is neither causal synergy nor a calibrated B7 cross-source effect.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from joint_ndqp_scenarios import ROOT
from q2_final_core import Q2Final

Q1_INTERACTION = ROOT / "outputs/chm/q1_exports/q1_interaction_bundle_v1"
OUT = ROOT / "outputs/cyj/q2_final"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def read_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def dump(path, obj):
    Path(path).write_bytes((json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n").encode())


def csv_out(path, rows):
    with Path(path).open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


class InteractionConsumer:
    def __init__(self):
        self.main = Q2Final()
        self.manifest = load_json(Q1_INTERACTION / "interaction_manifest.json")
        if (self.manifest.get("schema_version") != "chm.q1.interaction_bundle.v1"
                or self.manifest.get("status") != "Q1_upstream_reproduction_pending_CHM_owner_signoff"
                or self.manifest.get("upstream_Q1_export_manifest_sha256") != sha(self.main.bundle / "export_manifest.json")):
            raise ValueError("unexpected or mismatched Q1 interaction producer")
        for name, digest in self.manifest["files_sha256"].items():
            if sha(Q1_INTERACTION / name) != digest:
                raise ValueError(f"Q1 interaction hash mismatch: {name}")
        self.definition = load_json(Q1_INTERACTION / "interaction_feature_definition.json")
        self.coefficients = load_json(Q1_INTERACTION / "interaction_coefficients_13_targets.json")
        if (self.definition["domain_order"] != self.main.domains
                or set(self.definition["target_order"]) != set(self.main.targets)
                or len(self.definition["pairs_order"]) != 10
                or len(self.coefficients["targets"]) != 13):
            raise ValueError("Q1 interaction feature/target identity mismatch")
        self.pairs = [tuple(pair) for pair in self.definition["pairs_order"]]
        for target in self.main.targets:
            entry = self.coefficients["targets"][target]
            if set(entry["main"]) != set(self.main.domains) or [tuple(p["domains"]) for p in entry["pairs"]] != self.pairs:
                raise ValueError("Q1 interaction coefficient order mismatch")
            if entry["fitted_reference_loss"] <= 0:
                raise ValueError("nonpositive Q1 interaction reference loss")
        cv = {r["target"]: r for r in read_csv(Q1_INTERACTION / "interaction_cv_summary.csv")}
        prior = {r["target"]: r for r in read_csv(self.main.bundle / "mixture_model_selection.csv") if r["scope"] == "test_1m"}
        for target in self.main.targets:
            if (not math.isclose(float(cv[target]["cv_rmse"]), float(prior[target]["cv_rmse"]), abs_tol=1e-10)
                    or not math.isclose(float(cv[target]["alpha"]), float(prior[target]["alpha"]), abs_tol=1e-12)):
                raise ValueError("published CHM candidate CV or alpha mismatch")
        self.reference = self.main.reference
        self.beta = np.array([[self.coefficients["targets"][t]["main"][d] for d in self.main.domains]
                              for t in self.main.targets], dtype=float)
        self.gamma = np.array([[p["gamma"] for p in self.coefficients["targets"][t]["pairs"]]
                               for t in self.main.targets], dtype=float)
        self.intercept = np.array([self.coefficients["targets"][t]["intercept"] for t in self.main.targets])
        self.reference_loss = np.array([self.coefficients["targets"][t]["fitted_reference_loss"] for t in self.main.targets])
        self.pair_columns = [(self.main.domains.index(a), self.main.domains.index(b)) for a, b in self.pairs]
        if not np.allclose(self.predict(self.reference), self.reference_loss, atol=1e-10):
            raise ValueError("Q1 interaction reference prediction mismatch")

    def features(self, points):
        x = np.atleast_2d(np.asarray(points, dtype=float))
        if x.shape[1] != 17 or not np.isfinite(x).all():
            raise ValueError("expected finite 17-domain Q1 composition")
        return np.column_stack([x] + [(x[:, i] * x[:, j])[:, None] for i, j in self.pair_columns])

    def predict(self, points):
        phi = self.features(points)
        return self.intercept + phi[:, :17] @ self.beta.T + phi[:, 17:] @ self.gamma.T

    def relative(self, points):
        return (self.predict(points) - self.reference_loss) / self.reference_loss


def analyze():
    model = InteractionConsumer()
    main = model.main
    policies = load_json(OUT / "p_policy_details.json")
    policy_points = {
        "Q1_reference": main.reference,
        "ridge_equal_optimum": main.point(policies["convex_hull__equal_13"]["p"]),
        "ridge_QA_direct": main.point(policies["quality_direct__equal_13"]["p"]),
    }
    stability = {(r["target"], r["domain_i"], r["domain_j"]): r
                 for r in read_csv(Q1_INTERACTION / "interaction_fold_stability.csv")}
    rows, summaries = [], []
    equal = np.ones(13) / 13
    for pair_index, (a, b) in enumerate(model.pairs):
        i, j = model.pair_columns[pair_index]
        count = int(np.count_nonzero((main.matrix[:, i] > 0) & (main.matrix[:, j] > 0)))
        signs = []
        fold_count = 0
        for target_index, target in enumerate(main.targets):
            gamma = float(model.gamma[target_index, pair_index])
            stable = stability[(target, a, b)]
            if not math.isclose(gamma, float(stable["gamma_full"]), abs_tol=1e-10):
                raise ValueError("Q1 fold-stability coefficient mismatch")
            fold_count += int(stable["same_sign_fold_count"])
            signs.append(-1 if gamma < 0 else (1 if gamma > 0 else 0))
            row = {"domain_i": a, "domain_j": b, "target": target,
                   "gamma_cross_partial_A_loss": gamma,
                   "gamma_over_positive_A_reference_loss": gamma / model.reference_loss[target_index],
                   "model_relation": "complement_in_fitted_basis" if gamma < 0 else "competition_in_fitted_basis" if gamma > 0 else "zero",
                   "same_sign_training_folds": int(stable["same_sign_fold_count"]),
                   "training_fold_count": int(stable["fold_count"]),
                   "A4_both_domains_positive_rows": count}
            for point_name, point in policy_points.items():
                row[f"cross_partial_at_{point_name}"] = gamma
                row[f"pair_product_contribution_at_{point_name}"] = gamma * point[i] * point[j]
            rows.append(row)
        weighted_cross = float(equal @ (model.gamma[:, pair_index] / model.reference_loss))
        summaries.append({"domain_i": a, "domain_j": b,
            "negative_targets": signs.count(-1), "positive_targets": signs.count(1),
            "same_sign_training_folds_of_65": fold_count,
            "A4_both_domains_positive_rows": count,
            "equal_weight_normalized_cross_partial": weighted_cross,
            "arxiv_only_normalized_cross_partial": float(model.gamma[main.targets.index("arxiv"), pair_index] / model.reference_loss[main.targets.index("arxiv")]),
            "pile_cc_only_normalized_cross_partial": float(model.gamma[main.targets.index("pile_cc"), pair_index] / model.reference_loss[main.targets.index("pile_cc")]),
            "label": ("consistent_fitted_complement" if signs.count(-1) == 13 and fold_count >= 60 and count >= 10
                      else "mixed_or_fold_sensitive_fitted_relation")})
    csv_out(OUT / "domain_interactions.csv", rows)

    # Both model choices are enumerated on the same 512 *observed* Q1 recipes.
    # The existing Ridge full-hull optimum is separately recorded, not silently
    # treated as an observed vertex (notably for minimax).
    ridge_rel = main.relative_recipe_effects
    interaction_rel = model.relative(main.matrix)
    observed_rows = []
    base = main.v5.evaluate_ndq(1, 100, .5)["loss"]
    scenarios = {"equal_13": (equal, "convex_hull__equal_13"),
                 "arxiv_only": (np.eye(1, 13, main.targets.index("arxiv")).ravel(), "convex_hull__arxiv_only"),
                 "minimax_13": (equal, "minimax_13__equal_13")}
    for scenario, (weight, published_name) in scenarios.items():
        ridge_obj = ridge_rel.max(axis=1) if scenario == "minimax_13" else ridge_rel @ weight
        inter_obj = interaction_rel.max(axis=1) if scenario == "minimax_13" else interaction_rel @ weight
        ridge_idx, inter_idx = int(np.argmin(ridge_obj)), int(np.argmin(inter_obj))
        rp, ip = main.matrix[ridge_idx], main.matrix[inter_idx]
        ridge_at_rp, ridge_at_ip = float(ridge_obj[ridge_idx]), float(ridge_obj[inter_idx])
        inter_at_rp, inter_at_ip = float(inter_obj[ridge_idx]), float(inter_obj[inter_idx])
        if ridge_at_ip < ridge_at_rp - 1e-10 or inter_at_rp < inter_at_ip - 1e-10:
            raise AssertionError("enumeration regret should be nonnegative on the common 512 candidates")
        full_hull = policies[published_name]
        full_point = main.point(full_hull["p"])
        observed_rows.append({"scenario": scenario, "comparison_support": "same_512_observed_Q1_recipes",
            "ridge_full_hull_policy": published_name,
            "ridge_full_hull_recipe_count": len(full_hull["recipe_weights"]),
            "ridge_full_hull_conditional_loss": full_hull["conditional_loss"],
            "ridge_observed_index": main.indices[ridge_idx],
            "interaction_observed_index": main.indices[inter_idx],
            "ridge_objective_at_ridge_observed": ridge_at_rp,
            "ridge_objective_at_interaction_observed": ridge_at_ip,
            "interaction_objective_at_ridge_observed": inter_at_rp,
            "interaction_objective_at_interaction_observed": inter_at_ip,
            "ridge_regret_of_interaction_choice": max(0.0, ridge_at_ip - ridge_at_rp),
            "interaction_regret_of_ridge_choice": max(0.0, inter_at_rp - inter_at_ip),
            "ridge_conditional_loss_at_ridge_observed": base * (1 + float(ridge_rel[ridge_idx] @ weight)),
            "ridge_conditional_loss_at_interaction_observed": base * (1 + float(ridge_rel[inter_idx] @ weight)),
            "interaction_conditional_loss_at_ridge_observed": base * (1 + float(interaction_rel[ridge_idx] @ weight)),
            "interaction_conditional_loss_at_interaction_observed": base * (1 + float(interaction_rel[inter_idx] @ weight)),
            "ridge_full_hull_p_L1_to_interaction_observed": float(np.abs(full_point - ip).sum()),
            "observed_optima_p_L1": float(np.abs(rp - ip).sum()),
            "ridge_observed_p_json": json.dumps(main.p_dict(rp), sort_keys=True, separators=(",", ":")),
            "interaction_observed_p_json": json.dumps(main.p_dict(ip), sort_keys=True, separators=(",", ":")),
            "full_hull_p_json": json.dumps(full_hull["p"], sort_keys=True, separators=(",", ":")),
        })
    csv_out(OUT / "ridge_vs_interaction_policy.csv", observed_rows)
    published = read_csv(main.bundle / "mixture_model_selection.csv")
    design = model.features(main.matrix)
    pair_design = design[:, 17:]
    pair_residual = pair_design - main.matrix @ np.linalg.lstsq(main.matrix, pair_design, rcond=None)[0]
    heldout_counts = {scope: sum(float(row["candidate_rmse"]) < float(row["ridge_rmse"])
                      for row in published if row["scope"] == scope)
                      for scope in ("test_1m", "test_60m", "test_1B")}
    constant_1b = {r["target"]: float(r["constant_rmse"])
                   for r in read_csv(main.bundle / "heldout_target_metrics.csv") if r["scope"] == "test_1B"}
    candidate_beats_constant_1b = sum(float(r["candidate_rmse"]) < constant_1b[r["target"]]
                                      for r in published if r["scope"] == "test_1B")
    dump(OUT / "interaction_summary.json", {
        "schema_version": "cyj.q2.interactions.v1", "Q1_interaction_manifest_sha256": sha(Q1_INTERACTION / "interaction_manifest.json"),
        "Q1_status": model.manifest["status"], "pair_count": len(model.pairs), "target_count": len(main.targets),
        "domain_interaction_rows": len(rows), "policy_comparisons": len(observed_rows),
        "pairs": summaries, "published_candidate_RMSE_better_than_Ridge_target_counts": heldout_counts,
        "candidate_1B_absolute_RMSE_beats_constant_targets": candidate_beats_constant_1b,
        "A4_design": {"rows": len(design), "linear_feature_rank": int(np.linalg.matrix_rank(main.matrix)),
                      "full_feature_rank": int(np.linalg.matrix_rank(design)),
                      "pair_block_rank_after_linear_projection": int(np.linalg.matrix_rank(pair_residual)),
                      "full_design_condition_number": float(np.linalg.cond(design)),
                      "pair_block_condition_after_linear_projection": float(np.linalg.cond(pair_residual))},
        "screening_rule": "exploratory fitted-basis complement screen: gamma<0 in 13/13 targets, at least 60/65 matching training-fold signs, and both domains positive in at least 10/512 training recipes; rule is descriptive, not a significance test",
        "cross_partial_note": "Quadratic mixed partial gamma is constant across reference/Ridge/QA p in this fitted basis; pair-product contribution changes with p.",
        "simplex_note": "Composition proportions sum to one. Ambient gamma is basis-specific; a feasible simultaneous addition to pair i,j must remove mass elsewhere. A donor outside the selected five yields the same local mixed partial, but such perturbations may leave the Q1 convex hull and are not automatically supported.",
        "claim_limit": "Training-side Q1 1M association only. Fold sign stability and A4 co-occurrence do not identify causal complementarity, cross-scale transfer or the B7 bridge.",
        "ready_for_Q3": False})
    print(json.dumps({"rows": len(rows), "pair_count": len(summaries), "policies": len(observed_rows),
                      "consistent_pairs": [f'{r["domain_i"]}*{r["domain_j"]}' for r in summaries if r["label"] == "consistent_fitted_complement"],
                      "bundle_sha256": sha(Q1_INTERACTION / "interaction_manifest.json")}))


if __name__ == "__main__":
    analyze()
