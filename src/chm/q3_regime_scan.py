"""Continuous budget-regime scan and multi-start validation for Q3 diagnostics."""
from __future__ import annotations
import argparse, csv, json, math
from pathlib import Path
import numpy as np
from scipy.optimize import minimize

from q3_nd_baseline import (
    BUDGETS, CONTEXTS, DEFAULT_PARAMS, D_RANGE, N_RANGE,
    base_loss, compute_coeff, unconstrained_product_optimum,
)

SEED = 20260924

def _ratio(p=DEFAULT_PARAMS):
    return p["alpha"] * p["A"] / (p["beta"] * p["B"])

def _product_at_N(N, p=DEFAULT_PARAMS):
    r = _ratio(p)
    return (N ** (p["alpha"] + p["beta"]) / r) ** (1.0 / p["beta"])

def _product_at_D(D, p=DEFAULT_PARAMS):
    r = _ratio(p)
    return (D * r ** (1.0 / (p["alpha"] + p["beta"]))) ** (
        (p["alpha"] + p["beta"]) / p["alpha"]
    )

def regime_thresholds(context_tokens):
    c = compute_coeff(context_tokens)
    nmin, nmax = N_RANGE
    dmin, dmax = D_RANGE
    return {
        "min_feasible_budget": c * nmin * dmin,
        "Nmin_release_budget": c * _product_at_N(nmin),
        "Dmax_activation_budget": c * _product_at_D(dmax),
        "support_saturation_budget": c * nmax * dmax,
    }

def regime_solution(budget, context_tokens):
    c = compute_coeff(context_tokens)
    P = budget / c
    nmin, nmax = N_RANGE
    dmin, dmax = D_RANGE
    t = regime_thresholds(context_tokens)
    if budget < t["min_feasible_budget"] * (1 - 1e-12):
        return {"feasible": False, "phase": "infeasible"}
    if budget <= t["Nmin_release_budget"] * (1 + 1e-12):
        N, D, phase = nmin, P / nmin, "N_min_bound"
    elif budget <= t["Dmax_activation_budget"] * (1 + 1e-12):
        N, D = unconstrained_product_optimum(P)
        phase = "interior"
    elif budget <= t["support_saturation_budget"] * (1 + 1e-12):
        N, D, phase = P / dmax, dmax, "D_max_bound"
    else:
        N, D, phase = nmax, dmax, "support_corner"
    used = c * N * D
    return {
        "feasible": True, "phase": phase, "N_params_B": N, "D_tokens_B": D,
        "diagnostic_loss": base_loss(N, D), "cost_FLOPs": used,
        "budget_utilization": used / budget,
    }

def scan_budgets(points=301, max_budget=1e24):
    out = []
    for ctx in CONTEXTS:
        t = regime_thresholds(ctx)
        base = np.logspace(math.log10(t["min_feasible_budget"]), math.log10(max_budget), points)
        budgets = sorted(set(map(float, np.r_[base, list(t.values()), BUDGETS])))
        for budget in budgets:
            out.append({"context_tokens": ctx, "budget_FLOPs": budget,
                        **regime_solution(budget, ctx)})
    return out

def reduced_multistart(budget, context_tokens, starts=25, seed=SEED):
    c = compute_coeff(context_tokens)
    P = budget / c
    nmin, nmax = N_RANGE
    dmin, dmax = D_RANGE
    if P < nmin * dmin:
        raise ValueError("infeasible budget")
    if P >= nmax * dmax:
        lo, hi = nmin, nmax
        def d_for_n(_n): return dmax
    else:
        lo, hi = max(nmin, P / dmax), min(nmax, P / dmin)
        def d_for_n(n): return P / n
    rng = np.random.default_rng(seed)
    z0s = [math.log(lo), math.log(hi), 0.5*(math.log(lo)+math.log(hi))]
    z0s += list(rng.uniform(math.log(lo), math.log(hi), starts-len(z0s)))
    rows = []
    for i, z0 in enumerate(z0s):
        res = minimize(
            lambda z: base_loss(math.exp(float(z[0])), d_for_n(math.exp(float(z[0])))),
            np.array([z0]), method="L-BFGS-B",
            bounds=[(math.log(lo), math.log(hi))],
            options={"ftol": 1e-15, "gtol": 1e-12, "maxiter": 500},
        )
        N = math.exp(float(res.x[0])); D = d_for_n(N)
        rows.append({"start_id": i, "success": bool(res.success), "loss": float(res.fun),
                     "N_params_B": N, "D_tokens_B": D})
    return rows

def threshold_rows():
    return [{"context_tokens": c, "attention_train_ratio": c/30000.0,
             **regime_thresholds(c)} for c in CONTEXTS]

def validation_rows():
    out = []
    for ctx in CONTEXTS:
        t = regime_thresholds(ctx)
        for budget in sorted(set(BUDGETS + tuple(t.values()))):
            exact = regime_solution(budget, ctx)
            trials = reduced_multistart(budget, ctx)
            best = min(trials, key=lambda r: r["loss"])
            out.append({
                "context_tokens": ctx, "budget_FLOPs": budget, "phase": exact["phase"],
                "starts": len(trials), "success_count": sum(r["success"] for r in trials),
                "max_abs_loss_gap": max(abs(r["loss"]-exact["diagnostic_loss"]) for r in trials),
                "best_abs_loss_gap": abs(best["loss"]-exact["diagnostic_loss"]),
                "best_N_rel_error": abs(best["N_params_B"]-exact["N_params_B"])/exact["N_params_B"],
                "best_D_rel_error": abs(best["D_tokens_B"]-exact["D_tokens_B"])/exact["D_tokens_B"],
            })
    return out

def _write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/chm/q3_regime_v1"))
    a=ap.parse_args()
    a.output_dir.mkdir(parents=True, exist_ok=True)
    th, scan, val = threshold_rows(), scan_budgets(), validation_rows()
    _write_csv(a.output_dir/"regime_thresholds.csv", th)
    _write_csv(a.output_dir/"budget_scan.csv", scan)
    _write_csv(a.output_dir/"multistart_validation.csv", val)
    manifest={
        "schema_version":"chm.q3.regime_diagnostic.v1",
        "status":"diagnostic_only","ready_for_Q3":False,
        "cyj_ref":"6c17cb4e387e1ac047f8fe0e9ecb6fe42fc5ef3b",
        "zhh_ref":"d47cd2dc921333caecfcb95f09eb5a2f2714d0db",
        "critical_context_tokens_equal_attention_train":30000,
        "transition_definition":["minimum feasible support","N_min releases","interior",
                                 "D_max activates","support saturation"],
        "validation":{"method":"25-start L-BFGS-B reduced feasible problem","seed":SEED},
        "p_identifiability_note":"linear p ranking is invariant to budget/context/N for fixed target and positive lambda",
    }
    (a.output_dir/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

if __name__=="__main__":
    main()
