from pathlib import Path
import argparse
import json
import lzma
import math
import os
import hashlib
import platform

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

SEED = 20260923
EXPECTED_ROWS = {"A1": 51230, "A2": 17523, "A3": 203752}
EXPECTED_LIST_LENGTH = {
    "fineweb_edu": 1,
    "ad_en": 2,
    "fluency_en": 2,
    "qurater": 4,
    "modernbert_professionalism": 6,
    "modernbert_readability": 6,
    "modernbert_reasoning": 6,
    "modernbert_cleanliness": 6,
}

QUALITY_FIELDS = [
    "fineweb_edu",
    "fluency_en",
    "modernbert_cleanliness",
    "modernbert_readability",
    "modernbert_reasoning",
    "modernbert_professionalism",
    "dsir_books",
    "dsir_wiki",
    "dsir_math",
    "qurater",
    "ad_en",
    "rps_doc_word_count",
    "rps_doc_num_sentences",
    "rps_doc_unigram_entropy",
    "rps_doc_frac_unique_words",
    "rps_doc_frac_no_alph_words",
    "rps_doc_frac_chars_top_2gram",
    "rps_doc_frac_chars_top_3gram",
    "rps_lines_uppercase_letter_fraction",
    "rps_lines_ending_with_terminal_punctution_mark",
    "rps_lines_numerical_chars_fraction",
    "rps_doc_mean_word_length",
]

MODEL_FIELDS = list(EXPECTED_LIST_LENGTH)
DSIR_FIELDS = ["dsir_books", "dsir_wiki", "dsir_math"]
RPS_FIELDS = [x for x in QUALITY_FIELDS if x not in MODEL_FIELDS + DSIR_FIELDS]
COUNT_FIELDS = {"rps_doc_word_count", "rps_doc_num_sentences"}
SIGNED_LOG_FIELDS = set(DSIR_FIELDS)


def softmax(v):
    a = np.asarray(v, dtype=float)
    a = a - np.nanmax(a)
    e = np.exp(a)
    return e / np.nansum(e)


def validate_list(field, value):
    if value is None:
        return
    if not isinstance(value, (list, tuple)):
        raise TypeError(f"{field} is not a list/tuple")
    expected = EXPECTED_LIST_LENGTH[field]
    if len(value) != expected:
        raise ValueError(f"{field} length={len(value)}, expected={expected}")


def expected_rating(v):
    p = softmax(v)
    return float(np.dot(np.arange(len(p), dtype=float), p))


def compress_list(field, value, mode="expectation"):
    if value is None:
        return np.nan
    validate_list(field, value)
    # Missing logits must remain missing in both compression modes. In
    # particular np.argmax([nan, nan]) would otherwise fabricate class 0.
    if not np.isfinite(np.asarray(value, dtype=float)).all():
        return np.nan
    if field == "fineweb_edu":
        return float(value[0])
    if field == "qurater":
        a = np.asarray(value, dtype=float)
        return float(np.nanmean(a))
    if field in {"ad_en", "fluency_en"}:
        a = np.asarray(value, dtype=float)
        if mode == "argmax":
            return float(np.argmax(a))
        return float(softmax(a)[1])
    if field.startswith("modernbert_"):
        a = np.asarray(value, dtype=float)
        if mode == "argmax":
            return float(np.argmax(a))
        return expected_rating(a)
    raise KeyError(field)


def scalar_transform(field, x):
    if not np.isfinite(x):
        return np.nan
    if field in COUNT_FIELDS:
        return math.log1p(max(float(x), 0.0))
    if field in SIGNED_LOG_FIELDS:
        x = float(x)
        return math.copysign(math.log1p(abs(x)), x)
    return float(x)


def read_jsonl_xz(path, source_domain=None, list_mode="expectation"):
    rows = []
    with lzma.open(path, "rt", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            obj = json.loads(line)
            domain = obj.get("_source_domain") or source_domain
            rec = {"_source_domain": domain, "_line": line_no, "_id": str(obj.get("id", ""))}
            for field in QUALITY_FIELDS:
                val = obj.get(field)
                try:
                    if field in MODEL_FIELDS:
                        rec[field] = compress_list(field, val, mode=list_mode)
                    else:
                        rec[field] = scalar_transform(field, float(val)) if val is not None else np.nan
                except Exception as exc:
                    raise ValueError(f"{path}:{line_no} field={field}: {exc}") from exc
            rows.append(rec)
    return pd.DataFrame(rows)


def robust_params(df):
    rows = []
    for c in QUALITY_FIELDS:
        x = pd.to_numeric(df[c], errors="coerce").to_numpy(float)
        x = x[np.isfinite(x)]
        if len(x) == 0:
            raise ValueError(f"No finite values for {c}")
        med = float(np.median(x))
        mad = float(np.median(np.abs(x - med)))
        scale = 1.4826 * mad
        if not np.isfinite(scale) or scale <= 1e-12:
            scale = float(np.std(x))
        if not np.isfinite(scale) or scale <= 1e-12:
            scale = 1.0
        rows.append({"metric": c, "median": med, "scale": scale})
    return pd.DataFrame(rows)


def apply_robust_z(df, params):
    out = df[["_source_domain", "_line", "_id"]].copy()
    p = params.set_index("metric")
    for c in QUALITY_FIELDS:
        z = (pd.to_numeric(df[c], errors="coerce") - p.loc[c, "median"]) / p.loc[c, "scale"]
        out[c] = z.clip(-5, 5)
    return out


def domain_anchor_correlations(z):
    anchor = z[MODEL_FIELDS].mean(axis=1, skipna=True)
    records = []
    for metric in QUALITY_FIELDS:
        if metric in MODEL_FIELDS:
            records.append({
                "metric": metric,
                "pooled_rho": np.nan,
                "orientation": 1,
                "sign_agreement": np.nan,
                "heterogeneity": np.nan,
                "n_domains": int(z["_source_domain"].nunique()),
            })
            continue
        per = []
        for domain, g in z.groupby("_source_domain"):
            idx = g.index[g[metric].notna() & anchor.loc[g.index].notna()]
            n = int(len(idx))
            if n < 4:
                continue
            if g.loc[idx, metric].nunique() < 2 or anchor.loc[idx].nunique() < 2:
                continue
            rho = float(spearmanr(g.loc[idx, metric], anchor.loc[idx]).statistic)
            if np.isfinite(rho):
                per.append((domain, n, rho))
        if not per:
            records.append({
                "metric": metric, "pooled_rho": np.nan, "orientation": 1,
                "sign_agreement": np.nan, "heterogeneity": np.nan, "n_domains": 0,
            })
            continue
        num = 0.0
        den = 0.0
        signs = []
        for _, n, rho in per:
            rho_clip = float(np.clip(rho, -0.999999, 0.999999))
            w = max(n - 3, 1)
            num += w * np.arctanh(rho_clip)
            den += w
            signs.append(np.sign(rho))
        pooled = float(np.tanh(num / den))
        orientation = 1 if pooled >= 0 else -1
        sign_agreement = float(np.mean([s == orientation for s in signs]))
        heterogeneity = float(1 - abs(np.mean(signs)))
        records.append({
            "metric": metric,
            "pooled_rho": pooled,
            "orientation": orientation,
            "sign_agreement": sign_agreement,
            "heterogeneity": heterogeneity,
            "n_domains": len(per),
        })
    return pd.DataFrame(records)


def orient(z, orientation):
    out = z.copy()
    omap = orientation.set_index("metric")["orientation"].to_dict()
    for c in QUALITY_FIELDS:
        out[c] = out[c] * float(omap.get(c, 1))
    return out


def add_quality_scores(z_oriented, frozen_q=None):
    out = z_oriented.copy()
    out["Q_rps"] = out[RPS_FIELDS].mean(axis=1, skipna=True)
    out["Q_dsir"] = out[DSIR_FIELDS].mean(axis=1, skipna=True)
    out["Q_model"] = out[MODEL_FIELDS].mean(axis=1, skipna=True)
    out["Q_raw"] = out[["Q_rps", "Q_dsir", "Q_model"]].mean(axis=1, skipna=True)
    out["Q_equal22"] = out[QUALITY_FIELDS].mean(axis=1, skipna=True)
    if frozen_q is None:
        mu = float(out["Q_raw"].mean())
        sd = float(out["Q_raw"].std(ddof=0))
        if not np.isfinite(sd) or sd <= 1e-12:
            sd = 1.0
        frozen_q = {"Q_raw_mean": mu, "Q_raw_std": sd}
    out["Q_z"] = (out["Q_raw"] - frozen_q["Q_raw_mean"]) / frozen_q["Q_raw_std"]
    return out, frozen_q


def trimmed_mean(x, proportion=0.1):
    a = np.asarray(x, dtype=float)
    a = np.sort(a[np.isfinite(a)])
    if len(a) == 0:
        return np.nan
    k = int(np.floor(proportion * len(a)))
    return float(np.mean(a[k:len(a)-k])) if 2 * k < len(a) else float(np.mean(a))


def bootstrap_median_ci(x, rng, reps):
    a = np.asarray(x, dtype=float)
    a = a[np.isfinite(a)]
    if len(a) == 0:
        return np.nan, np.nan
    vals = np.empty(reps)
    for i in range(reps):
        vals[i] = np.median(rng.choice(a, size=len(a), replace=True))
    lo, hi = np.quantile(vals, [0.025, 0.975])
    return float(lo), float(hi)


def domain_summary(scored, scope, rng, reps):
    rows = []
    for domain, g in scored.groupby("_source_domain"):
        q = g["Q_z"].to_numpy(float)
        lo, hi = bootstrap_median_ci(q, rng, reps)
        rows.append({
            "dataset_scope": scope,
            "quality_domain": domain,
            "n_rows": int(len(g)),
            "Q_z_median": float(np.nanmedian(q)),
            "Q_z_trimmed_mean": trimmed_mean(q),
            "Q_equal22_median": float(np.nanmedian(g["Q_equal22"])),
            "Q_ci_low": lo,
            "Q_ci_high": hi,
        })
    return pd.DataFrame(rows)


def conflict_pairs(oriented):
    rows = []
    matrices = [g[QUALITY_FIELDS].corr(method="spearman", min_periods=4)
                for _, g in oriented.groupby("_source_domain")]
    for i, a in enumerate(QUALITY_FIELDS):
        for b in QUALITY_FIELDS[i + 1:]:
            vals = [float(m.loc[a, b]) for m in matrices if np.isfinite(m.loc[a, b])]
            if vals:
                mean_rho = float(np.mean(vals))
                rows.append({
                    "metric_a": a,
                    "metric_b": b,
                    "mean_domain_spearman": mean_rho,
                    "conflict_strength": max(0.0, -mean_rho),
                    "min_domain_spearman": float(np.min(vals)),
                    "max_domain_spearman": float(np.max(vals)),
                    "n_domains": len(vals),
                })
    return pd.DataFrame(rows).sort_values(
        ["conflict_strength", "mean_domain_spearman"], ascending=[False, True]
    )


def missingness_audit(df, scope):
    rows = []
    for domain, g in df.groupby("_source_domain"):
        for c in QUALITY_FIELDS:
            miss = int(g[c].isna().sum())
            rows.append({
                "dataset_scope": scope,
                "quality_domain": domain,
                "metric": c,
                "n_rows": int(len(g)),
                "missing": miss,
                "missing_rate": miss / len(g),
            })
    return pd.DataFrame(rows)


def assert_domain_id_integrity(df, label):
    rows = []
    for domain, g in df.groupby("_source_domain", dropna=False):
        ids = g["_id"].fillna("").astype(str).str.strip()
        blank = int((ids == "").sum())
        duplicate = int(ids.duplicated().sum())
        rows.append({
            "dataset": label,
            "quality_domain": domain,
            "n_rows": int(len(g)),
            "blank_ids": blank,
            "duplicate_ids": duplicate,
            "unique_nonblank_ids": int(ids[ids != ""].nunique()),
        })
        if blank or duplicate:
            raise ValueError(
                f"{label}/{domain}: blank_ids={blank}, duplicate_ids={duplicate}"
            )
    return rows


def resolve_default_paths():
    root = Path(os.environ.get("F_DATA_ROOT", "data/raw/real_attachments"))
    base = root / "A_data_value"
    return (
        base / "slimpajama_quality_signal_sample.jsonl.xz",
        base / "slimpajama_quality_extended/arxiv_part-6777d8857c6e-000486.jsonl.xz",
        base / "slimpajama_quality_extended/github_part-6777d8857c6e-000275.jsonl.xz",
    )


def main():
    a1_default, a2_default, a3_default = resolve_default_paths()
    parser = argparse.ArgumentParser()
    parser.add_argument("--a1", type=Path, default=a1_default)
    parser.add_argument("--a2", type=Path, default=a2_default)
    parser.add_argument("--a3", type=Path, default=a3_default)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/chm"))
    parser.add_argument("--bootstrap", type=int, default=1000)
    args = parser.parse_args()
    if args.bootstrap < 1:
        parser.error("--bootstrap must be positive")

    for p in [args.a1, args.a2, args.a3]:
        if not p.exists():
            raise FileNotFoundError(f"{p} missing; run git lfs pull first.")

    rng = np.random.default_rng(SEED)

    a1 = read_jsonl_xz(args.a1, list_mode="expectation")
    a2 = read_jsonl_xz(args.a2, source_domain="arxiv", list_mode="expectation")
    a3 = read_jsonl_xz(args.a3, source_domain="github", list_mode="expectation")
    print("Loaded all A1-A3 records", flush=True)

    id_integrity_rows = []
    id_integrity_rows.extend(assert_domain_id_integrity(a1, "A1"))
    id_integrity_rows.extend(assert_domain_id_integrity(a2, "A2"))
    id_integrity_rows.extend(assert_domain_id_integrity(a3, "A3"))

    actual = {"A1": len(a1), "A2": len(a2), "A3": len(a3)}
    for key, expected in EXPECTED_ROWS.items():
        if actual[key] != expected:
            raise ValueError(f"{key} rows={actual[key]}, expected={expected}")
    if a1["_source_domain"].nunique() != 7:
        raise ValueError(f"A1 domain count={a1['_source_domain'].nunique()}, expected=7")

    params = robust_params(a1)
    z1 = apply_robust_z(a1, params)
    orientation = domain_anchor_correlations(z1)
    oz1 = orient(z1, orientation)
    s1, qparams = add_quality_scores(oz1)

    z2 = orient(apply_robust_z(a2, params), orientation)
    z3 = orient(apply_robust_z(a3, params), orientation)
    s2, _ = add_quality_scores(z2, frozen_q=qparams)
    s3, _ = add_quality_scores(z3, frozen_q=qparams)

    args.output_dir.mkdir(parents=True, exist_ok=True)

    prep = params.merge(orientation, on="metric", how="left")
    prep["family"] = prep["metric"].map(
        lambda x: "model" if x in MODEL_FIELDS else ("dsir" if x in DSIR_FIELDS else "rps")
    )
    prep.to_csv(args.output_dir / "quality_metric_preprocessing_v0.csv", index=False)
    orientation.to_csv(args.output_dir / "quality_orientation_v0.csv", index=False)
    conflict_pairs(oz1).to_csv(args.output_dir / "quality_conflict_pairs_v0.csv", index=False)
    # Compare the same domains with frozen A1 orientations, not pooled A1 vs one domain.
    conflict_checks, drift_checks, overlap_checks, direction_checks = [], [], [], []
    for domain, ext, raw_ext in [("arxiv", z2, a2), ("github", z3, a3)]:
        sample = oz1[oz1["_source_domain"] == domain]
        comparison = conflict_pairs(sample).merge(
            conflict_pairs(ext), on=["metric_a", "metric_b"], suffixes=("_sample", "_extended")
        )
        comparison.insert(0, "quality_domain", domain)
        comparison["negative_in_both"] = ((comparison["mean_domain_spearman_sample"] < 0)
                                            & (comparison["mean_domain_spearman_extended"] < 0))
        conflict_checks.append(comparison)
        for metric in QUALITY_FIELDS:
            drift_checks.append({"quality_domain": domain, "metric": metric,
                                 "sample_oriented_z_median": sample[metric].median(),
                                 "extended_oriented_z_median": ext[metric].median(),
                                 "delta_oriented_z_median": ext[metric].median() - sample[metric].median()})
        for scope, frame in [("sample", sample), ("extended", ext)]:
            anchor = frame[MODEL_FIELDS].mean(axis=1)
            for metric in RPS_FIELDS + DSIR_FIELDS:
                direction_checks.append({"quality_domain": domain, "scope": scope, "metric": metric,
                                         "oriented_anchor_spearman": frame[metric].corr(anchor, method="spearman")})
        sample_ids = set(a1.loc[a1["_source_domain"] == domain, "_id"])
        ext_ids = set(raw_ext["_id"])
        overlap_checks.append({"quality_domain": domain, "sample_unique_ids": len(sample_ids),
                               "extended_unique_ids": len(ext_ids), "overlap_unique_ids": len(sample_ids & ext_ids)})
    pd.concat(conflict_checks, ignore_index=True).to_csv(args.output_dir / "quality_conflict_extended_v0.csv", index=False)
    pd.DataFrame(drift_checks).to_csv(args.output_dir / "quality_metric_drift_v0.csv", index=False)
    pd.DataFrame(direction_checks).to_csv(args.output_dir / "quality_orientation_extended_v0.csv", index=False)
    pd.DataFrame(overlap_checks).to_csv(args.output_dir / "quality_sample_overlap_v0.csv", index=False)
    print("Completed frozen-parameter conflict and overlap checks", flush=True)

    domain_primary = pd.concat([
        domain_summary(s1, "sample", rng, args.bootstrap),
        domain_summary(s2, "arxiv_extended", rng, args.bootstrap),
        domain_summary(s3, "github_extended", rng, args.bootstrap),
    ], ignore_index=True)
    domain_primary.to_csv(args.output_dir / "domain_quality_v0.csv", index=False)
    remainder_summaries, remainder_conflicts = [], []
    for domain, scored_ext in [("arxiv", s2), ("github", s3)]:
        sample_ids = set(s1.loc[s1["_source_domain"] == domain, "_id"])
        remainder = scored_ext[~scored_ext["_id"].isin(sample_ids)]
        remainder_summaries.append(domain_summary(remainder, domain + "_nonoverlap", rng, args.bootstrap))
        pairs = conflict_pairs(remainder)
        pairs.insert(0, "quality_domain", domain)
        remainder_conflicts.append(pairs)
    pd.concat(remainder_summaries, ignore_index=True).to_csv(
        args.output_dir / "quality_nonoverlap_validation_v0.csv", index=False)
    pd.concat(remainder_conflicts, ignore_index=True).to_csv(
        args.output_dir / "quality_conflict_nonoverlap_v0.csv", index=False)

    pd.concat([
        missingness_audit(a1, "sample"),
        missingness_audit(a2, "arxiv_extended"),
        missingness_audit(a3, "github_extended"),
    ], ignore_index=True).to_csv(
        args.output_dir / "quality_data_audit_v0.csv", index=False
    )

    pd.DataFrame(id_integrity_rows).to_csv(
        args.output_dir / "quality_id_integrity_v0.csv", index=False
    )

    sample_ext = []
    for d, ext, label in [("arxiv", s2, "arxiv_extended"), ("github", s3, "github_extended")]:
        sample = s1[s1["_source_domain"] == d]["Q_z"].to_numpy(float)
        ex = ext["Q_z"].to_numpy(float)
        sample_ext.append({
            "quality_domain": d,
            "sample_n": int(len(sample)),
            "extended_n": int(len(ex)),
            "sample_Q_median": float(np.nanmedian(sample)),
            "extended_Q_median": float(np.nanmedian(ex)),
            "delta_Q_median": float(np.nanmedian(ex) - np.nanmedian(sample)),
            "extended_scope": label,
        })
    pd.DataFrame(sample_ext).to_csv(
        args.output_dir / "quality_sample_extended_v0.csv", index=False
    )

    # Sensitivity: official data card suggests argmax for classifier/PRRC logits.
    a1_arg = read_jsonl_xz(args.a1, list_mode="argmax")
    p_arg = robust_params(a1_arg)
    z_arg = apply_robust_z(a1_arg, p_arg)
    o_arg = domain_anchor_correlations(z_arg)
    s_arg, _ = add_quality_scores(orient(z_arg, o_arg))
    domain_arg = domain_summary(s_arg, "sample_argmax", rng, args.bootstrap)
    domain_arg.to_csv(args.output_dir / "domain_quality_argmax_v0.csv", index=False)

    primary_rank = domain_primary[domain_primary["dataset_scope"] == "sample"][
        ["quality_domain", "Q_z_median"]
    ].copy()
    arg_rank = domain_arg[["quality_domain", "Q_z_median"]].copy()
    merged = primary_rank.merge(arg_rank, on="quality_domain", suffixes=("_expectation", "_argmax"))
    rank_rho = float(spearmanr(
        merged["Q_z_median_expectation"], merged["Q_z_median_argmax"]
    ).statistic)
    merged["domain_rank_spearman_all7"] = rank_rho
    merged.to_csv(
        args.output_dir / "quality_list_compression_sensitivity_v0.csv", index=False
    )

    manifest = {
        "seed": SEED,
        "rows": actual,
        "list_compression_primary": "probability_or_expected_rating; qurater=mean4",
        "list_compression_sensitivity": "argmax for binary/PRRC logits",
        "normalization": "A1 median/MAD robust z, clip [-5,5]; A2/A3 reuse A1 parameters",
        "orientation": "8 model metrics positive anchors; remaining 14 use within-domain Spearman + Fisher-z pooling",
        "quality_aggregation": "equal within RPS/DSIR/model families, then equal across three families",
        "bootstrap_reps": args.bootstrap,
        "q_standardization": qparams,
        "versions": {"python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__},
        "input_sha256": {key: hashlib.sha256(path.read_bytes()).hexdigest()
                         for key, path in [("A1", args.a1), ("A2", args.a2), ("A3", args.a3)]},
        "inputs": {"A1": str(args.a1), "A2": str(args.a2), "A3": str(args.a3)},
        "id_integrity": id_integrity_rows,
        "warning": "Descriptive quality index, not causal utility or B6 Q_score. Bootstrap CIs condition on fitted A1 preprocessing and assume iid rows; overlapping sample/extended data are not independent validation.",
    }
    (args.output_dir / "quality_analysis_manifest_v0.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
