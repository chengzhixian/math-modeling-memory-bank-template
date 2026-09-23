from pathlib import Path
import argparse
import json
import lzma

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

import q1_quality_analysis as qa

SEED = qa.SEED


def audit_ids(df, scope):
    rows = []
    for domain, g in df.groupby("_source_domain", dropna=False):
        ids = g["_id"].fillna("").astype(str).str.strip()
        rows.append({
            "dataset_scope": scope,
            "quality_domain": domain,
            "n_rows": int(len(g)),
            "blank_ids": int((ids == "").sum()),
            "duplicate_ids": int(ids.duplicated().sum()),
            "unique_nonblank_ids": int(ids[ids != ""].nunique()),
        })
    return pd.DataFrame(rows)


def assert_id_integrity(audit):
    bad = audit[(audit["blank_ids"] > 0) | (audit["duplicate_ids"] > 0)]
    if not bad.empty:
        raise ValueError("Blank/duplicate IDs detected:\n" + bad.to_string(index=False))


def domain_medians(scored, col):
    return (
        scored.groupby("_source_domain")[col]
        .median()
        .sort_index()
        .rename(col)
    )


def score_subset(oriented, included, label):
    out = oriented.copy()
    included = set(included)
    families = {
        "rps": [c for c in qa.RPS_FIELDS if c in included],
        "dsir": [c for c in qa.DSIR_FIELDS if c in included],
        "model": [c for c in qa.MODEL_FIELDS if c in included],
    }
    dropped_families = [name for name, cols in families.items() if not cols]
    if len(dropped_families) == len(families):
        raise ValueError(f"{label}: no quality metrics survive the filter")
    fam_cols = []
    for fam, cols in families.items():
        if not cols:
            continue
        name = f"_{label}_{fam}"
        out[name] = out[cols].mean(axis=1, skipna=True)
        fam_cols.append(name)
    raw = out[fam_cols].mean(axis=1, skipna=True)
    mu = float(raw.mean())
    sd = float(raw.std(ddof=0))
    if not np.isfinite(sd) or sd <= 1e-12:
        sd = 1.0
    out[f"Q_{label}"] = (raw - mu) / sd
    return out, {
        "mean": mu, "std": sd, "included_metrics": sorted(included),
        "included_families": [name for name, cols in families.items() if cols],
        "dropped_families": dropped_families,
        "warning": "Family weights are rebalanced over surviving families; this is a stress test, not the primary Q definition." if dropped_families else "",
    }


def orientation_stability(z, primary_orientation):
    domains = sorted(z["_source_domain"].dropna().unique().tolist())
    loo = {}
    for held_out in domains:
        table = qa.domain_anchor_correlations(z[z["_source_domain"] != held_out])
        loo[held_out] = table.set_index("metric")

    primary = primary_orientation.set_index("metric")
    rows = []
    for metric in qa.QUALITY_FIELDS:
        full_orientation = int(primary.loc[metric, "orientation"])
        full_rho = primary.loc[metric, "pooled_rho"]
        sign_agreement = primary.loc[metric, "sign_agreement"]
        if metric in qa.MODEL_FIELDS:
            rows.append({
                "metric": metric,
                "full_pooled_rho": np.nan,
                "full_orientation": 1,
                "sign_agreement": np.nan,
                "loo_min_rho": np.nan,
                "loo_max_rho": np.nan,
                "loo_sign_consistent": True,
                "stable_loo": True,
                "stable_consensus_075": True,
            })
            continue

        loo_rhos = [float(loo[d].loc[metric, "pooled_rho"]) for d in domains]
        loo_orient = [int(loo[d].loc[metric, "orientation"]) for d in domains]
        loo_consistent = all(v == full_orientation for v in loo_orient)
        agreement = float(sign_agreement) if np.isfinite(sign_agreement) else np.nan
        rows.append({
            "metric": metric,
            "full_pooled_rho": float(full_rho),
            "full_orientation": full_orientation,
            "sign_agreement": agreement,
            "loo_min_rho": float(np.min(loo_rhos)),
            "loo_max_rho": float(np.max(loo_rhos)),
            "loo_sign_consistent": bool(loo_consistent),
            "stable_loo": bool(loo_consistent),
            "stable_consensus_075": bool(loo_consistent and np.isfinite(agreement) and agreement >= 0.75),
        })
    return pd.DataFrame(rows)


def family_weight_grid(scored, step=0.05):
    units = int(round(1.0 / step))
    grid_rows = []
    rank_rows = []
    grid_id = 0
    for i in range(units + 1):
        for j in range(units - i + 1):
            k = units - i - j
            w_rps, w_dsir, w_model = i / units, j / units, k / units
            q = (
                w_rps * scored["Q_rps"]
                + w_dsir * scored["Q_dsir"]
                + w_model * scored["Q_model"]
            )
            tmp = pd.DataFrame({
                "domain": scored["_source_domain"],
                "q": q,
            })
            med = tmp.groupby("domain")["q"].median()
            ranks = med.rank(ascending=False, method="average")
            for domain in med.index:
                grid_rows.append({
                    "grid_id": grid_id,
                    "w_rps": w_rps,
                    "w_dsir": w_dsir,
                    "w_model": w_model,
                    "quality_domain": domain,
                    "Q_raw_median": float(med.loc[domain]),
                    "rank_high_is_good": float(ranks.loc[domain]),
                })
            grid_id += 1

    grid = pd.DataFrame(grid_rows)
    summary = (
        grid.groupby("quality_domain")
        .agg(
            rank_min=("rank_high_is_good", "min"),
            rank_max=("rank_high_is_good", "max"),
            rank_median=("rank_high_is_good", "median"),
            Q_raw_median_min=("Q_raw_median", "min"),
            Q_raw_median_max=("Q_raw_median", "max"),
        )
        .reset_index()
    )
    top2 = (
        grid.assign(top2=grid["rank_high_is_good"] <= 2)
        .groupby("quality_domain")["top2"].mean()
        .rename("top2_share")
    )
    bottom2 = (
        grid.assign(bottom2=grid["rank_high_is_good"] >= 6)
        .groupby("quality_domain")["bottom2"].mean()
        .rename("bottom2_share")
    )
    summary = summary.merge(top2, on="quality_domain").merge(bottom2, on="quality_domain")
    return grid, summary


def domain_balanced_params(scored):
    domains = sorted(scored["_source_domain"].dropna().unique())
    vals = []
    weights = []
    for domain in domains:
        q = scored.loc[scored["_source_domain"] == domain, "Q_raw"].to_numpy(float)
        q = q[np.isfinite(q)]
        if len(q) == 0:
            continue
        vals.append(q)
        weights.append(np.full(len(q), 1.0 / (len(domains) * len(q))))
    x = np.concatenate(vals)
    w = np.concatenate(weights)
    w = w / w.sum()
    mu = float(np.sum(w * x))
    sd = float(np.sqrt(np.sum(w * (x - mu) ** 2)))
    if not np.isfinite(sd) or sd <= 1e-12:
        sd = 1.0
    return {"mean": mu, "std": sd, "definition": "equal total weight per A1 domain"}


def load_qurater_components(path, source_domain=None):
    rows = []
    with lzma.open(path, "rt", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            obj = json.loads(line)
            domain = obj.get("_source_domain") or source_domain
            value = obj.get("qurater")
            rec = {
                "_source_domain": domain,
                "_line": line_no,
                "_id": str(obj.get("id", "")),
            }
            if value is None:
                for j in range(4):
                    rec[f"qurater_{j}"] = np.nan
            else:
                qa.validate_list("qurater", value)
                a = np.asarray(value, dtype=float)
                for j in range(4):
                    rec[f"qurater_{j}"] = float(a[j]) if np.isfinite(a[j]) else np.nan
            rows.append(rec)
    return pd.DataFrame(rows)


def robust_component_mean(a1_components, other_components=None):
    cols = [f"qurater_{j}" for j in range(4)]
    params = {}
    for c in cols:
        x = pd.to_numeric(a1_components[c], errors="coerce").to_numpy(float)
        x = x[np.isfinite(x)]
        med = float(np.median(x))
        mad = float(np.median(np.abs(x - med)))
        scale = 1.4826 * mad
        if not np.isfinite(scale) or scale <= 1e-12:
            scale = float(np.std(x))
        if not np.isfinite(scale) or scale <= 1e-12:
            scale = 1.0
        params[c] = {"median": med, "scale": scale}

    def apply(df):
        z = []
        for c in cols:
            a = (pd.to_numeric(df[c], errors="coerce") - params[c]["median"]) / params[c]["scale"]
            z.append(a.clip(-5, 5))
        return pd.concat(z, axis=1).mean(axis=1, skipna=True)

    return apply(a1_components if other_components is None else other_components), params


def main():
    a1_default, a2_default, a3_default = qa.resolve_default_paths()
    parser = argparse.ArgumentParser()
    parser.add_argument("--a1", type=Path, default=a1_default)
    parser.add_argument("--a2", type=Path, default=a2_default)
    parser.add_argument("--a3", type=Path, default=a3_default)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/chm/quality_review_v1"))
    parser.add_argument("--family-weight-step", type=float, default=0.05)
    args = parser.parse_args()

    for p in [args.a1, args.a2, args.a3]:
        if not p.exists():
            raise FileNotFoundError(f"{p} missing; run git lfs pull first.")

    outdir = args.output_dir
    outdir.mkdir(parents=True, exist_ok=True)

    a1 = qa.read_jsonl_xz(args.a1, list_mode="expectation")
    a2 = qa.read_jsonl_xz(args.a2, source_domain="arxiv", list_mode="expectation")
    a3 = qa.read_jsonl_xz(args.a3, source_domain="github", list_mode="expectation")

    id_audit = pd.concat([
        audit_ids(a1, "A1"),
        audit_ids(a2, "A2"),
        audit_ids(a3, "A3"),
    ], ignore_index=True)
    assert_id_integrity(id_audit)
    id_audit.to_csv(outdir / "quality_id_integrity_v1.csv", index=False)

    params = qa.robust_params(a1)
    z1 = qa.apply_robust_z(a1, params)
    primary_orientation = qa.domain_anchor_correlations(z1)
    oz1 = qa.orient(z1, primary_orientation)
    s1, qparams = qa.add_quality_scores(oz1)

    stability = orientation_stability(z1, primary_orientation)
    stability.to_csv(outdir / "quality_orientation_stability_v1.csv", index=False)

    include_loo = stability.loc[stability["stable_loo"], "metric"].tolist()
    include_consensus = stability.loc[stability["stable_consensus_075"], "metric"].tolist()
    s_loo, loo_params = score_subset(oz1, include_loo, "stable_loo")
    s_cons, consensus_params = score_subset(oz1, include_consensus, "stable_consensus")

    primary_med = domain_medians(s1, "Q_z")
    loo_med = domain_medians(s_loo, "Q_stable_loo")
    consensus_med = domain_medians(s_cons, "Q_stable_consensus")
    sens = pd.concat([primary_med, loo_med, consensus_med], axis=1).reset_index()
    sens["rank_primary"] = sens["Q_z"].rank(ascending=False, method="average")
    sens["rank_stable_loo"] = sens["Q_stable_loo"].rank(ascending=False, method="average")
    sens["rank_stable_consensus"] = sens["Q_stable_consensus"].rank(ascending=False, method="average")
    sens["spearman_primary_vs_loo"] = float(spearmanr(sens["Q_z"], sens["Q_stable_loo"]).statistic)
    sens["spearman_primary_vs_consensus"] = float(
        spearmanr(sens["Q_z"], sens["Q_stable_consensus"]).statistic
    )
    sens.to_csv(outdir / "quality_orientation_filter_sensitivity_v1.csv", index=False)

    grid, grid_summary = family_weight_grid(s1, step=args.family_weight_step)
    grid.to_csv(outdir / "quality_family_weight_grid_v1.csv", index=False)
    grid_summary.to_csv(outdir / "quality_family_weight_summary_v1.csv", index=False)

    balanced = domain_balanced_params(s1)
    s1_bal = s1.copy()
    s1_bal["Q_z_domain_balanced"] = (
        s1_bal["Q_raw"] - balanced["mean"]
    ) / balanced["std"]
    bal = pd.concat([
        domain_medians(s1, "Q_z"),
        domain_medians(s1_bal, "Q_z_domain_balanced"),
    ], axis=1).reset_index()
    bal["rank_primary"] = bal["Q_z"].rank(ascending=False, method="average")
    bal["rank_domain_balanced"] = bal["Q_z_domain_balanced"].rank(
        ascending=False, method="average"
    )
    bal["spearman_rank"] = float(
        spearmanr(bal["Q_z"], bal["Q_z_domain_balanced"]).statistic
    )
    bal.to_csv(outdir / "quality_domain_balanced_standardization_v1.csv", index=False)

    qcomp = load_qurater_components(args.a1)
    qcomp_mean, qcomp_params = robust_component_mean(qcomp)
    if len(qcomp_mean) != len(z1):
        raise ValueError("Qurater component rows do not align with A1.")
    z1_q = z1.copy()
    z1_q["qurater"] = qcomp_mean.to_numpy(float)
    orientation_q = qa.domain_anchor_correlations(z1_q)
    sq, _ = qa.add_quality_scores(qa.orient(z1_q, orientation_q))
    qmed = pd.concat([
        domain_medians(s1, "Q_z"),
        domain_medians(sq, "Q_z").rename("Q_z_qurater_component_standardized"),
    ], axis=1).reset_index()
    qmed["rank_primary"] = qmed["Q_z"].rank(ascending=False, method="average")
    qmed["rank_qurater_component"] = qmed["Q_z_qurater_component_standardized"].rank(
        ascending=False, method="average"
    )
    qmed["spearman_rank"] = float(
        spearmanr(qmed["Q_z"], qmed["Q_z_qurater_component_standardized"]).statistic
    )
    qmed.to_csv(outdir / "quality_qurater_component_sensitivity_v1.csv", index=False)

    manifest = {
        "seed": SEED,
        "status": "review_sensitivity_not_primary",
        "primary_quality_definition_unchanged": True,
        "orientation_sensitivity": {
            "stable_loo": "full pooled sign unchanged after leaving out each of 7 A1 domains",
            "stable_consensus_075": "stable_loo and sign_agreement >= 0.75",
            "loo_included_metrics": include_loo,
            "consensus_included_metrics": include_consensus,
            "loo_standardization": loo_params,
            "consensus_standardization": consensus_params,
        },
        "family_weight_grid": {
            "step": args.family_weight_step,
            "simplex": "w_rps+w_dsir+w_model=1; zero weights allowed for stress testing",
        },
        "domain_balanced_standardization": balanced,
        "primary_record_weighted_standardization": qparams,
        "qurater_component_standardization": qcomp_params,
        "warning": "Sensitivity outputs do not replace the primary Q until reviewed and frozen.",
    }
    (outdir / "quality_review_manifest_v1.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
