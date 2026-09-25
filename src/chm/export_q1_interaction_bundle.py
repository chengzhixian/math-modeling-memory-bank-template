"""Q1 upstream export of CHM's already evaluated 13-target interaction candidate.

Only this upstream stage reads original A4/A5. It reproduces the candidate in
CHM q1_mixture_final_audit.py@2450971; it does not modify chm.q1.v1.3.
"""
from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / "outputs/chm/q1_exports/q1_interaction_bundle_v1"
Q1 = ROOT / "outputs/chm/q1_exports/q1_q2_bundle_v1"
RAW = ROOT / "data/raw/real_attachments/A_data_value/regmix_tables"
SOURCE_COMMIT = "2450971d15b7f6516d6db408759bf1b22f497808"
EXPECTED = {"train_mixture_1m.csv": "04a32ef4ab594376bf90e11404c033668f887c351d6a03ad3744824c7296a2d8",
            "train_pile_loss_1m.csv": "49a959aa07ce5c20831d5abe3a7896ff0cd90a398bd407c8913fd5588be0465a"}
ALPHAS = (1e-3, 1e-2, 1e-1, 1.0, 10.0, 100.0, 1000.0)


def sha(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def dump(path: Path, obj):
    path.write_bytes((json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n").encode())


def ridge_fit(x, y, alpha):
    """Equivalent to sklearn Ridge(fit_intercept=True) on dense X, positive alpha."""
    xm, ym = x.mean(axis=0), float(y.mean())
    centered = x - xm
    beta = np.linalg.solve(centered.T @ centered + alpha * np.eye(x.shape[1]), centered.T @ (y - ym))
    intercept = ym - float(xm @ beta)
    return intercept, beta


def cv_candidate(x, y):
    folds = np.array_split(np.arange(len(x)), 5)  # KFold(5, shuffle=False)
    scores = []
    for alpha in ALPHAS:
        fold_errors = []
        for va in folds:
            train = np.ones(len(x), dtype=bool)
            train[va] = False
            intercept, beta = ridge_fit(x[train], y[train], alpha)
            fold_errors.append(float(np.sqrt(np.mean((intercept + x[va] @ beta - y[va]) ** 2))))
        scores.append((float(np.mean(fold_errors)), alpha, fold_errors))
    best = min(scores, key=lambda item: (item[0], item[1]))
    return best, scores


def export():
    for name, expected in EXPECTED.items():
        if sha(RAW / name) != expected:
            raise ValueError(f"original Q1 training input hash mismatch: {name}")
    q1_manifest = json.loads((Q1 / "export_manifest.json").read_text(encoding="utf-8"))
    if q1_manifest["schema_version"] != "chm.q1.q2_bundle.v1":
        raise ValueError("unexpected upstream Q1 export")
    for name, digest in q1_manifest["files_sha256"].items():
        if sha(Q1 / name) != digest:
            raise ValueError(f"upstream Q1 output hash mismatch: {name}")
    recipe = rows(Q1 / "recipes_512.csv")
    loss = rows(RAW / "train_pile_loss_1m.csv")
    domains = json.loads((Q1 / "recipe_manifest.json").read_text(encoding="utf-8"))["domain_order"]
    targets = [key.removeprefix("metric/the_pile_").removesuffix("_val_loss") for key in loss[0] if key != "index"]
    if len(recipe) != 512 or len(loss) != 512:
        raise ValueError("expected 512 rows")
    if [r["index"] for r in recipe] != [r["index"] for r in loss]:
        raise ValueError("A4/A5 index order differs")
    if len(domains) != 17 or len(targets) != 13:
        raise ValueError("unexpected Q1 domain or target count")
    x = np.array([[float(r[d]) for d in domains] for r in recipe])
    if not np.isfinite(x).all() or np.min(x) < 0 or not np.allclose(x.sum(axis=1), 1, atol=1e-12):
        raise ValueError("invalid Q1 normalized recipes")
    selected = np.argsort(np.var(x, axis=0))[-5:].tolist()
    pairs = list(itertools.combinations(selected, 2))
    if len(pairs) != 10:
        raise ValueError("expected ten fixed Q1 candidate pair features")
    xx = np.column_stack([x] + [(x[:, a] * x[:, b])[:, None] for a, b in pairs])
    published = rows(Q1 / "mixture_model_selection.csv")
    published_1m = {r["target"]: r for r in published if r["scope"] == "test_1m"}
    selected_string = "|".join(domains[i] for i in selected)
    if set(published_1m) != set(targets) or any(r["selected_domains"] != selected_string for r in published_1m.values()):
        raise ValueError("candidate feature set differs from CHM published audit")
    ref_rows = rows(Q1 / "reference.csv")
    reference = np.array([float(r["p_ref"]) for r in ref_rows])
    if [r["mixture_domain"] for r in ref_rows] != domains:
        raise ValueError("reference domain order mismatch")
    reference_x = np.r_[reference, [reference[a] * reference[b] for a, b in pairs]]
    model = {}
    cv_rows = []
    stability_rows = []
    selected_names = [domains[i] for i in selected]
    for target in targets:
        key = f"metric/the_pile_{target}_val_loss"
        y = np.array([float(r[key]) for r in loss])
        if not np.isfinite(y).all() or np.min(y) <= 0:
            raise ValueError(f"invalid Q1 train target: {target}")
        best, all_cv = cv_candidate(xx, y)
        published_row = published_1m[target]
        if not math.isclose(best[1], float(published_row["alpha"]), abs_tol=1e-15):
            raise ValueError(f"alpha differs from frozen CHM candidate: {target}")
        if not math.isclose(best[0], float(published_row["cv_rmse"]), rel_tol=1e-10, abs_tol=1e-10):
            raise ValueError(f"CV differs from frozen CHM candidate: {target}: {best[0]}")
        intercept, beta = ridge_fit(xx, y, best[1])
        reference_loss = float(intercept + reference_x @ beta)
        if not math.isfinite(reference_loss) or reference_loss <= 0:
            raise ValueError(f"nonpositive fitted Q1 reference Loss: {target}")
        model[target] = {"intercept": float(intercept),
                         "main": dict(zip(domains, map(float, beta[:17]))),
                         "pairs": [{"domains": [domains[a], domains[b]], "gamma": float(beta[17 + i])}
                                   for i, (a, b) in enumerate(pairs)],
                         "alpha": best[1], "cv_rmse": best[0], "fitted_reference_loss": reference_loss}
        folds = np.array_split(np.arange(len(xx)), 5)
        fold_betas = []
        for va in folds:
            train = np.ones(len(xx), dtype=bool)
            train[va] = False
            fold_betas.append(ridge_fit(xx[train], y[train], best[1])[1])
        for i, (a, b) in enumerate(pairs):
            values = [float(coeff[17 + i]) for coeff in fold_betas]
            full = float(beta[17 + i])
            stability_rows.append({"target": target, "domain_i": domains[a], "domain_j": domains[b],
                                   "gamma_full": full, "fold_gamma_json": json.dumps(values, separators=(",", ":")),
                                   "fold_min": min(values), "fold_max": max(values),
                                   "same_sign_fold_count": sum(math.copysign(1, v) == math.copysign(1, full) for v in values),
                                   "fold_count": 5, "alpha": best[1]})
        cv_rows.append({"target": target, "alpha": best[1], "cv_rmse": best[0],
                        "published_cv_rmse": published_row["cv_rmse"],
                        "max_abs_cv_diff": abs(best[0] - float(published_row["cv_rmse"])),
                        "fold_rmse_json": json.dumps(best[2], separators=(",", ":")),
                        "all_alpha_cv_json": json.dumps({str(alpha): score for score, alpha, _ in all_cv}, separators=(",", ":")),
                        "fitted_reference_loss": reference_loss})
    DEST.mkdir(parents=True, exist_ok=True)
    dump(DEST / "interaction_feature_definition.json", {
        "schema_version": "chm.q1.interaction_features.v1", "candidate_source_commit": SOURCE_COMMIT,
        "domain_order": domains, "target_order": targets, "selected_domain_order": selected_names,
        "pairs_order": [[domains[a], domains[b]] for a, b in pairs],
        "feature_order": domains + [f"{domains[a]}*{domains[b]}" for a, b in pairs],
        "selection": "five largest A4 normalized composition variances; numpy.argsort order; target-free",
        "cv": "KFold(5, shuffle=False), mean fold RMSE, seven frozen ridge alphas",
        "alpha_grid": ALPHAS, "intercept_penalized": False,
        "Q1_reference_p": dict(zip(domains, map(float, reference))),
        "reference_loss_kind": "positive fitted 1M training model prediction at p_ref; not B7 loss",
    })
    dump(DEST / "interaction_coefficients_13_targets.json", {
        "schema_version": "chm.q1.interaction_13_targets.v1", "status": "Q1_upstream_reproduction_pending_CHM_owner_signoff",
        "model": "intercept + 17 linear proportions + ten selected pair products; targetwise Ridge",
        "targets": model})
    with (DEST / "interaction_cv_summary.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(cv_rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(cv_rows)
    with (DEST / "interaction_fold_stability.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(stability_rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(stability_rows)
    files = {path.name: sha(path) for path in sorted(DEST.iterdir()) if path.is_file() and path.name != "interaction_manifest.json"}
    dump(DEST / "interaction_manifest.json", {
        "schema_version": "chm.q1.interaction_bundle.v1",
        "status": "Q1_upstream_reproduction_pending_CHM_owner_signoff",
        "candidate_source_commit": SOURCE_COMMIT,
        "generation_command": "python -B src/chm/export_q1_interaction_bundle.py",
        "source_A4_A5_sha256": EXPECTED,
        "upstream_Q1_export_manifest_sha256": sha(Q1 / "export_manifest.json"),
        "published_candidate_metrics_sha256": sha(Q1 / "mixture_model_selection.csv"),
        "normalization": "consume Q1 published normalized 512x17 recipes; verify original A4 hash and original A5 identity",
        "algorithm": "exact CHM selected-feature definition and unshuffled five-fold CV; dense centered Ridge equivalent to sklearn fit_intercept=True",
        "python_version": sys.version.split()[0], "numpy_version": np.__version__,
        "files_sha256": files})
    print(json.dumps({"targets": len(model), "features": xx.shape[1], "pairs": len(pairs),
                      "max_published_cv_difference": max(float(r["max_abs_cv_diff"]) for r in cv_rows),
                      "manifest_sha256": sha(DEST / "interaction_manifest.json")}))


if __name__ == "__main__":
    export()
