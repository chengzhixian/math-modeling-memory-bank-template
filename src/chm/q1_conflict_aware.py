"""Reproducible, conflict-aware analysis of the A1--A3 quality signals."""
from pathlib import Path
import json
from itertools import combinations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from q1_quality_analysis import (QUALITY_FIELDS, SEED, read_jsonl_xz, robust_params,
                                 apply_robust_z, global_anchor_correlations, orient,
                                 add_quality_scores, resolve_default_paths)

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/chm/conflict_aware_v1"
MIN_N = 30
ALPHA = 0.05


def correlation(frame, a, b):
    pair = frame[[a, b]].dropna()
    if len(pair) < MIN_N or pair[a].nunique() < 2 or pair[b].nunique() < 2:
        return len(pair), np.nan, np.nan
    result = spearmanr(pair[a], pair[b])
    return len(pair), float(result.statistic), float(result.pvalue)


def bh_adjust(pvalues):
    p = np.asarray(pvalues, dtype=float)
    out = np.full(len(p), np.nan)
    valid = np.flatnonzero(np.isfinite(p))
    order = valid[np.argsort(p[valid])]
    if len(order):
        ranked = p[order] * len(order) / np.arange(1, len(order) + 1)
        out[order] = np.minimum.accumulate(ranked[::-1])[::-1].clip(0, 1)
    return out


def pair_table(frame, scope):
    rows = []
    for a, b in combinations(QUALITY_FIELDS, 2):
        n, rho, p = correlation(frame, a, b)
        rows.append(dict(scope=scope, metric_a=a, metric_b=b, n=n, rho=rho, p=p))
    result = pd.DataFrame(rows)
    result["q_bh"] = bh_adjust(result.p)
    result["significant_negative"] = (result.rho < 0) & (result.q_bh < ALPHA)
    return result


def conflict_degree(frame, edges):
    values = np.zeros(len(frame), dtype=float)
    weights = np.zeros(len(frame), dtype=float)
    for row in edges.itertuples():
        left = frame[row.metric_a].to_numpy(float)
        right = frame[row.metric_b].to_numpy(float)
        valid = np.isfinite(left) & np.isfinite(right)
        weight = abs(row.rho)
        values[valid] += weight * np.abs(left[valid] - right[valid])
        weights[valid] += weight
    return np.divide(values, weights, out=np.full(len(frame), np.nan), where=weights > 0)


def main():
    a1_path, a2_path, a3_path = resolve_default_paths()
    a1 = read_jsonl_xz(ROOT / a1_path)
    a2 = read_jsonl_xz(ROOT / a2_path, source_domain="arxiv")
    a3 = read_jsonl_xz(ROOT / a3_path, source_domain="github")
    params = robust_params(a1)
    orientation = global_anchor_correlations(apply_robust_z(a1, params))
    sample = orient(apply_robust_z(a1, params), orientation)
    ext = {"arxiv": orient(apply_robust_z(a2, params), orientation),
           "github": orient(apply_robust_z(a3, params), orientation)}
    scored, frozen_q = add_quality_scores(sample)
    OUT.mkdir(parents=True, exist_ok=True)

    tables = [pair_table(sample, "A1_pooled")]
    for domain, group in sample.groupby("_source_domain"):
        tables.append(pair_table(group, f"A1_{domain}"))
    for domain, group in ext.items():
        tables.append(pair_table(group, f"{domain}_extended"))
        ids = set(sample.loc[sample._source_domain == domain, "_id"])
        tables.append(pair_table(group.loc[~group._id.isin(ids)], f"{domain}_nonoverlap"))
    all_pairs = pd.concat(tables, ignore_index=True)
    all_pairs.to_csv(OUT / "pair_correlations.csv", index=False)
    pooled = tables[0].copy()
    domains = all_pairs[all_pairs.scope.str.startswith("A1_") & (all_pairs.scope != "A1_pooled")]
    summary = domains.groupby(["metric_a", "metric_b"]).agg(
        n_domain_negative=("rho", lambda x: int((x < 0).sum())),
        n_domain_significant_negative=("significant_negative", "sum"),
        n_domain_valid=("rho", "count"),
    ).reset_index()
    pooled = pooled.merge(summary, on=["metric_a", "metric_b"])
    for domain in ext:
        check = all_pairs[all_pairs.scope == f"{domain}_nonoverlap"][
            ["metric_a", "metric_b", "rho", "q_bh", "significant_negative"]].copy()
        check.columns = ["metric_a", "metric_b", f"{domain}_rho", f"{domain}_q", f"{domain}_replicated"]
        pooled = pooled.merge(check, on=["metric_a", "metric_b"])
    pooled["replicated"] = pooled.arxiv_replicated | pooled.github_replicated
    pooled["stable_conflict"] = pooled.significant_negative & pooled.replicated
    pooled["cause_pattern"] = np.select(
        [pooled.n_domain_significant_negative >= 4,
         pooled.n_domain_significant_negative == 0,
         pooled.n_domain_significant_negative.between(1, 3)],
        ["multi_domain", "pooled_only", "domain_specific"], default="undetermined")
    pooled.to_csv(OUT / "conflict_graph.csv", index=False)
    edges = pooled[pooled.stable_conflict].copy()
    diagnostics = []
    for row in edges.nsmallest(10, "rho").itertuples():
        pair = sample[[row.metric_a, row.metric_b]].dropna()
        bounds = pair.quantile([0.01, 0.99])
        central = (pair.ge(bounds.loc[0.01]) & pair.le(bounds.loc[0.99])).all(axis=1)
        diagnostics.append(dict(metric_a=row.metric_a, metric_b=row.metric_b,
                                n_full=len(pair), n_central=int(central.sum()),
                                rho_full=row.rho,
                                rho_central=correlation(pair.loc[central], row.metric_a, row.metric_b)[1]))
    pd.DataFrame(diagnostics).to_csv(OUT / "extreme_value_diagnostic.csv", index=False)

    scored["D_conflict"] = conflict_degree(scored, edges)
    scored["D_all22"] = scored[QUALITY_FIELDS].std(axis=1, ddof=0)
    q_cut, d_cut = scored.Q_z.median(), scored.D_conflict.median()
    scored["quadrant"] = np.where(scored.Q_z >= q_cut, "high_Q", "low_Q") + "_" + np.where(
        scored.D_conflict >= d_cut, "high_D", "low_D")
    scored[["_source_domain", "_id", "Q_z", "D_conflict", "D_all22", "quadrant"]].to_csv(
        OUT / "sample_quality_conflict.csv", index=False)
    domain_rows = []
    for scope, frame in [("A1", scored)] + [
            (f"{d}_nonoverlap", add_quality_scores(e.loc[~e._id.isin(
                set(sample.loc[sample._source_domain == d, "_id"]))], frozen_q=frozen_q)[0])
            for d, e in ext.items()]:
        if scope != "A1":
            frame["D_conflict"] = conflict_degree(frame, edges)
        for domain, group in frame.groupby("_source_domain"):
            domain_rows.append(dict(scope=scope, domain=domain, n=len(group),
                                    Q_median=group.Q_z.median(), D_median=group.D_conflict.median(),
                                    D_mean=group.D_conflict.mean()))
    domain_table = pd.DataFrame(domain_rows)
    domain_table.to_csv(OUT / "domain_quality_conflict.csv", index=False)
    fig, ax = plt.subplots(figsize=(7, 5))
    for row in domain_table[domain_table.scope == "A1"].itertuples():
        ax.scatter(row.Q_median, row.D_median)
        ax.annotate(row.domain, (row.Q_median, row.D_median), xytext=(4, 4), textcoords="offset points", fontsize=8)
    ax.set(xlabel="Median Q_A (A1 coordinate)", ylabel="Median conflict-edge D", title="Quality and indicator disagreement")
    fig.tight_layout()
    fig.savefig(OUT / "domain_quality_conflict.png", dpi=180)
    plt.close(fig)
    manifest = dict(seed=SEED, min_pair_n=MIN_N, bh_fdr=ALPHA,
                    multiplicity="BH within each scope over 231 pairs",
                    edge_rule="A1 pooled significant negative and A2/A3 nonoverlap significant negative",
                    n_edges=len(edges), n_pooled_significant_negative=int(pooled.significant_negative.sum()),
                    n_a1_rows=len(sample), n_a2_rows=len(a2), n_a3_rows=len(a3),
                    D_weight="absolute pooled Spearman rho; pairwise available edges only",
                    caveat="Q and D are A-side proxies; observational correlations do not establish causes")
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
