"""Frozen, non-punitive review protocol for A-side quality conflicts."""
from pathlib import Path
import hashlib
import json
import lzma

import numpy as np
import pandas as pd

from q1_quality_analysis import (QUALITY_FIELDS, add_quality_scores, apply_robust_z,
                                 orient, read_jsonl_xz, resolve_default_paths)
from q1_conflict_aware import ROOT, conflict_degree

VERSION = "chm.q1.conflict_resolution.v1"
OUT = ROOT / "data/processed/Q1/conflict_resolution"


def decide(q, d, q_cut, d_cut):
    if not np.isfinite(q) and not np.isfinite(d):
        return "REVIEW_MISSING_Q_AND_D", "quality score unavailable; no usable conflict edge"
    if not np.isfinite(q):
        return "REVIEW_MISSING_Q", "quality score unavailable"
    if not np.isfinite(d):
        return "REVIEW_MISSING_D", "no usable conflict edge; do not impute zero"
    if d >= d_cut:
        return ("RETAIN_FLAG_REVIEW" if q >= q_cut else "LOW_PRIORITY_FLAG_REVIEW",
                "conflict degree above frozen A1 75th percentile")
    return ("RETAIN" if q >= q_cut else "LOW_PRIORITY",
            "conflict degree below frozen review threshold")


def score_and_decide(raw, params, orientation, qparams, edges, q_cut, d_cut):
    if set(QUALITY_FIELDS) - set(raw.columns):
        raise ValueError("all 22 quality fields and missing values must be represented")
    oriented = orient(apply_robust_z(raw, params), orientation)
    scored, _ = add_quality_scores(oriented, frozen_q=qparams)
    scored["D_conflict"] = conflict_degree(oriented, edges)
    scored["n_available_signals"] = oriented[QUALITY_FIELDS].notna().sum(axis=1)
    scored["n_usable_edges"] = sum(
        (oriented[r.metric_a].notna() & oriented[r.metric_b].notna()).astype(int)
        for r in edges.itertuples()) if len(edges) else 0
    decisions = [decide(q, d, q_cut, d_cut) for q, d in zip(scored.Q_z, scored.D_conflict)]
    scored["conflict_status"] = [x[0] for x in decisions]
    scored["review_reason"] = [x[1] for x in decisions]
    scored["decision_rule_version"] = VERSION
    return scored


def choose_cases(scored):
    """One predetermined hash-first record per domain and Q/D quadrant."""
    s = scored.copy()
    s["q_group"] = np.where(s.Q_z >= s.Q_z.median(), "high_Q", "low_Q")
    s["d_group"] = np.where(s.D_conflict >= s.D_conflict.median(), "high_D", "low_D")
    s["case_hash"] = [hashlib.sha256(f"{d}|{i}|20260925".encode()).hexdigest()
                      for d, i in zip(s._source_domain, s._id)]
    selected = (s.sort_values("case_hash").groupby(
        ["_source_domain", "q_group", "d_group"], as_index=False).head(1))
    return selected[["_source_domain", "_id", "_line", "case_hash", "q_group", "d_group",
                     "Q_z", "D_conflict", "n_available_signals", "n_usable_edges",
                     "conflict_status", "review_reason"]].sort_values(["_source_domain", "q_group", "d_group"])


def content_fingerprints(path, selected):
    wanted = set(zip(selected._source_domain, selected._id))
    records = {}
    with lzma.open(path, "rt", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            obj = json.loads(line)
            key = (obj.get("_source_domain"), str(obj.get("id", "")))
            if key in wanted:
                content = obj.get("content")
                if not isinstance(content, str):
                    raise ValueError(f"missing original content for {key}")
                records[key] = dict(source_line=line_no, content_sha256=hashlib.sha256(
                    content.encode("utf-8")).hexdigest(), content_chars=len(content))
    if set(records) != wanted:
        raise ValueError(f"missing {len(wanted - set(records))} selected original texts")
    return records


def main():
    base = ROOT / "data/processed/Q1/quality"
    manifest = json.loads((base / "quality_analysis_manifest_v0.json").read_text(encoding="utf-8"))
    params = pd.read_csv(base / "quality_metric_preprocessing_v0.csv")[["metric", "median", "scale"]]
    orientation = pd.read_csv(base / "quality_orientation_primary_v1.csv")
    edges = pd.read_csv(ROOT / "data/processed/Q1/conflict_aware/conflict_graph.csv").query("stable_conflict == True")
    if len(edges) != 55:
        raise ValueError("frozen conflict graph must have 55 edges")
    a1, a2, a3 = resolve_default_paths()
    raw = read_jsonl_xz(ROOT / a1)
    actual_a1_sha = hashlib.sha256((ROOT / a1).read_bytes()).hexdigest()
    if actual_a1_sha != manifest["input_sha256"]["A1"]:
        raise ValueError("A1 file SHA differs from frozen quality analysis input")
    qparams = manifest["q_standardization"]
    orient_a1 = orient(apply_robust_z(raw, params), orientation)
    q, _ = add_quality_scores(orient_a1, frozen_q=qparams)
    d = conflict_degree(orient_a1, edges)
    q_cut = float(q.Q_z.median())
    d_cut = float(np.nanquantile(d, 0.75))
    scored = score_and_decide(raw, params, orientation, qparams, edges, q_cut, d_cut)
    OUT.mkdir(parents=True, exist_ok=True)
    cols = ["_source_domain", "_id", "_line", "Q_z", "D_conflict", "n_available_signals",
            "n_usable_edges", "conflict_status", "review_reason", "decision_rule_version"]
    scored[cols].to_csv(OUT / "conflict_decisions.csv", index=False)
    selected = choose_cases(scored)
    signal_cols = ["_source_domain", "_id", "_line"] + QUALITY_FIELDS
    selected_signals = selected[["_source_domain", "_id", "_line"]].merge(
        scored[signal_cols], on=["_source_domain", "_id", "_line"], validate="one_to_one")
    selected_signals.to_csv(OUT / "selected_case_oriented_signals.csv", index=False)
    edge_details = []
    for _, case in selected_signals.iterrows():
        values = case.to_dict()
        contributions = []
        for edge in edges.itertuples():
            left, right = values.get(edge.metric_a), values.get(edge.metric_b)
            if pd.notna(left) and pd.notna(right):
                contributions.append((abs(edge.rho) * abs(left - right), edge.metric_a, edge.metric_b))
        contributions.sort(reverse=True)
        edge_details.append(dict(top_edge_a=contributions[0][1] if contributions else None,
                                 top_edge_b=contributions[0][2] if contributions else None,
                                 top_edge_weighted_gap=contributions[0][0] if contributions else np.nan))
    selected = pd.concat([selected.reset_index(drop=True), pd.DataFrame(edge_details)], axis=1)
    fingerprints = content_fingerprints(ROOT / a1, selected)
    for key in ["source_line", "content_sha256", "content_chars"]:
        selected[key] = [fingerprints[d, i][key] for d, i in zip(selected._source_domain, selected._id)]
    selected.to_csv(OUT / "selected_cases_index.csv", index=False)
    missing = scored.groupby("_source_domain").agg(n=("_id", "size"),
        missing_q=("Q_z", lambda x: int(x.isna().sum())),
        missing_d=("D_conflict", lambda x: int(x.isna().sum())),
        median_available_signals=("n_available_signals", "median"),
        median_usable_edges=("n_usable_edges", "median")).reset_index()
    missing["missing_d_rate"] = missing.missing_d / missing.n
    missing.to_csv(OUT / "missingness_by_domain.csv", index=False)
    validation = []
    for name, path, domain in [("A2_nonoverlap", a2, "arxiv"), ("A3_nonoverlap", a3, "github")]:
        ext = read_jsonl_xz(ROOT / path, source_domain=domain)
        ext = ext.loc[~ext._id.isin(set(raw.loc[raw._source_domain == domain, "_id"]))]
        result = score_and_decide(ext, params, orientation, qparams, edges, q_cut, d_cut)
        validation.append(dict(scope=name, n=len(result), q_median=float(result.Q_z.median()),
                               d_median=float(result.D_conflict.median()),
                               review_rate=float(result.conflict_status.str.contains("REVIEW").mean()),
                               missing_d=int(result.D_conflict.isna().sum())))
    pd.DataFrame(validation).to_csv(OUT / "frozen_threshold_validation.csv", index=False)
    release = dict(version=VERSION, q_threshold=q_cut, d_review_threshold=d_cut,
        threshold_source="A1 75th percentile of D; A1 median of Q", edge_count=len(edges),
        n_cases=len(selected), raw_content_exported=False,
        selection="hash-first per domain and A1-median Q/D quadrant; no quality-based manual cherry-picking",
        q_is_unchanged=True, review_is_not_a_quality_label=True,
        selection_limit="A1 selected graph and A1 thresholds are descriptive; A2/A3 nonoverlap test is only for two domains",
        input_sha256={name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in {
            "A1": ROOT / a1,
            "conflict_graph": ROOT / "data/processed/Q1/conflict_aware/conflict_graph.csv",
            "preprocessing": base / "quality_metric_preprocessing_v0.csv",
            "orientation": base / "quality_orientation_primary_v1.csv"}.items()})
    (OUT / "manifest.json").write_text(json.dumps(release, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(release, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
