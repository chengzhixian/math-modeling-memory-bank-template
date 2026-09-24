"""Separate record-sampling and quality-rule uncertainty for Q1."""
from pathlib import Path
import json

import numpy as np
import pandas as pd

from q1_quality_analysis import (DSIR_FIELDS, MODEL_FIELDS, QUALITY_FIELDS, RPS_FIELDS,
                                 SEED, add_quality_scores, apply_robust_z,
                                 global_anchor_correlations, orient, read_jsonl_xz,
                                 resolve_default_paths)

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/chm/q1_quality_robustness_final"
REPS = 100
TRAIN_FRACTION = 0.7


def stratified_split(z, rng):
    train, holdout = [], []
    for _, group in z.groupby("_source_domain"):
        indices = rng.permutation(group.index.to_numpy())
        cut = max(1, min(len(indices) - 1, int(round(TRAIN_FRACTION * len(indices)))))
        train.extend(indices[:cut])
        holdout.extend(indices[cut:])
    return z.loc[train], z.loc[holdout]


def domain_rank(scores):
    med = scores.groupby("_source_domain").Q_z.median()
    return med.rank(ascending=False, method="min").astype(int)


def main():
    base = ROOT / "outputs/chm"
    quality_manifest = json.loads((base / "quality_analysis_manifest_v0.json").read_text(encoding="utf-8"))
    a1, _, _ = resolve_default_paths()
    raw = read_jsonl_xz(ROOT / a1)
    params = pd.read_csv(base / "quality_metric_preprocessing_v0.csv")[["metric", "median", "scale"]]
    primary = pd.read_csv(base / "quality_orientation_primary_v1.csv")
    domain_signs = pd.read_csv(base / "quality_orientation_by_domain_v1.csv")
    loo = pd.read_csv(base / "quality_orientation_robustness_v1.csv")
    z = apply_robust_z(raw, params)
    rng = np.random.default_rng(SEED + 2)
    train, holdout = stratified_split(z, rng)
    qparams = quality_manifest["q_standardization"]
    baseline, _ = add_quality_scores(orient(holdout, primary), frozen_q=qparams)
    base_ranks = domain_rank(baseline)
    rows, ranks = [], []
    train_groups = {d: g for d, g in train.groupby("_source_domain")}
    for rep in range(REPS):
        bootstrap = pd.concat([g.iloc[rng.integers(0, len(g), len(g))]
                               for g in train_groups.values()], ignore_index=True)
        direction = global_anchor_correlations(bootstrap)
        rows.extend(dict(rep=rep, metric=r.metric, orientation=int(r.orientation),
                         global_rho=r.global_rho) for r in direction.itertuples())
        scores, _ = add_quality_scores(orient(holdout, direction), frozen_q=qparams)
        medians = scores.groupby("_source_domain").Q_z.median()
        this_rank = medians.rank(ascending=False, method="min").astype(int)
        ranks.extend(dict(rep=rep, domain=d, Q_median=float(medians[d]), rank=int(this_rank[d]),
                          rank_primary_holdout=int(base_ranks[d])) for d in medians.index)
    OUT.mkdir(parents=True, exist_ok=True)
    orientation_boot = pd.DataFrame(rows)
    orientation_boot.to_csv(OUT / "orientation_bootstrap.csv", index=False)
    rank_boot = pd.DataFrame(ranks)
    rank_boot.to_csv(OUT / "domain_rank_bootstrap.csv", index=False)
    flips = orientation_boot.merge(primary[["metric", "orientation"]], on="metric", suffixes=("_bootstrap", "_primary"))
    flips = flips.groupby("metric").apply(lambda x: float((x.orientation_bootstrap != x.orientation_primary).mean()),
                                          include_groups=False).rename("bootstrap_flip_rate").reset_index()
    weights = {m: 1 / (3 * len(MODEL_FIELDS if m in MODEL_FIELDS else DSIR_FIELDS if m in DSIR_FIELDS else RPS_FIELDS))
               for m in QUALITY_FIELDS}
    rules = primary.merge(loo[["metric", "loo_sign_flip", "loo_min_rho", "loo_max_rho"]], on="metric")
    rules = rules.merge(domain_signs.groupby("metric").agrees_with_primary.mean().rename(
        "domain_sign_agreement").reset_index(), on="metric")
    rules = rules.merge(flips, on="metric")
    rules["missing_rate_A1"] = rules.metric.map(raw[QUALITY_FIELDS].isna().mean())
    rules["nominal_family_balanced_weight"] = rules.metric.map(weights)
    rules["weak_or_unstable"] = (rules.abs_global_rho.fillna(1) < 0.05) | rules.loo_sign_flip | (rules.bootstrap_flip_rate > 0.05)
    rules.to_csv(OUT / "quality_rule_22.csv", index=False)
    envelope = rank_boot.groupby("domain").agg(rank_min=("rank", "min"), rank_max=("rank", "max"),
        rank_median=("rank", "median"), Q_median_min=("Q_median", "min"),
        Q_median_max=("Q_median", "max")).reset_index()
    envelope["n_A1"] = envelope.domain.map(raw.groupby("_source_domain").size())
    envelope.to_csv(OUT / "direction_rank_envelope.csv", index=False)
    # Existing sensitivity files are kept on their own score scales; combine ranks only.
    panels = []
    old = pd.read_csv(base / "quality_orientation_sensitivity_v1.csv")
    panels.append(old[["variant", "domain", "rank"]])
    for file, variants in [
        ("quality_review_v1/quality_orientation_filter_sensitivity_v1.csv",
         {"rank_stable_loo": "stable_loo", "rank_stable_consensus": "stable_consensus"}),
        ("quality_review_v1/quality_qurater_component_sensitivity_v1.csv",
         {"rank_qurater_component": "qurater_component_standardized"}),
        ("quality_review_v1/quality_domain_balanced_standardization_v1.csv",
         {"rank_domain_balanced": "domain_balanced_standardization"})]:
        source = pd.read_csv(base / file).rename(columns={"_source_domain": "domain"})
        for column, label in variants.items():
            panels.append(source[["domain", column]].rename(columns={column: "rank"}).assign(variant=label))
    rule_panel = pd.concat(panels, ignore_index=True)
    rule_panel.to_csv(OUT / "rule_ensemble_rank.csv", index=False)
    rule_envelope = rule_panel.groupby("domain").agg(rank_min=("rank", "min"), rank_max=("rank", "max"),
                                                    n_variants=("variant", "nunique")).reset_index()
    rule_envelope.to_csv(OUT / "rule_rank_envelope.csv", index=False)
    manifest = dict(seed=SEED + 2, reps=REPS, split="per-domain 70% train / 30% fixed holdout",
        bootstrap="resample training records within each domain; refit 14 statistical signs",
        holdout_is_not_used_for_direction_fit=True, primary_Q_unchanged=True,
        ranking_envelope_is_not_confidence_interval=True,
        input_sha256_A1=quality_manifest["input_sha256"]["A1"],
        limitations="Q preprocessing and Q scale are frozen from full A1; holdout is independent only of bootstrap sign fits, not of original Q rule selection")
    (OUT / "quality_robustness_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
