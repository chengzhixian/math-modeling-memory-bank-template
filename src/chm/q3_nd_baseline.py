"""Analytic N-D diagnostic baseline for Q3.

This intentionally excludes performance gains from Q and p. Q is fixed at Q0 so
quality cost is zero, and p is fixed at the producer reference composition. The
purpose is solver/cost validation and support-boundary detection, not a formal Q3
answer.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

DEFAULT_PARAMS = {
    "E": 1.6898377713152422,
    "A": 0.3539687193311042,
    "B": 1.2402746295202214,
    "alpha": 0.33998542577775076,
    "beta": 0.2798924656094203,
}
N_RANGE = (0.070542, 11.965825)
D_RANGE = (0.134, 299.893)
BUDGETS = (1e19, 1e22, 1e24)
CONTEXTS = (2048, 8192, 131072)

def base_loss(N, D, p=DEFAULT_PARAMS):
    return p["E"] + p["A"] * N ** (-p["alpha"]) + p["B"] * D ** (-p["beta"])

def compute_coeff(L_ctx):
    # C_train + C_attn = coeff * N_B * D_B when Q=Q0.
    return 6e18 + 2e-4 * 1e18 * L_ctx

def unconstrained_product_optimum(product, p=DEFAULT_PARAMS):
    ratio = p["alpha"] * p["A"] / (p["beta"] * p["B"])
    N = (ratio * product ** p["beta"]) ** (1.0 / (p["alpha"] + p["beta"]))
    D = product / N
    return N, D

def bounded_optimum(budget, L_ctx, p=DEFAULT_PARAMS):
    coeff = compute_coeff(L_ctx)
    product = budget / coeff
    n0, d0 = unconstrained_product_optimum(product, p)
    nmin, nmax = N_RANGE
    dmin, dmax = D_RANGE

    # Loss decreases monotonically in both N and D. Candidates are the interior
    # equality solution and intersections of ND=product with support boundaries,
    # plus the support upper corner when budget is slack.
    candidates = []
    def add(n, d, label):
        if nmin <= n <= nmax and dmin <= d <= dmax and coeff*n*d <= budget*(1+1e-12):
            candidates.append((base_loss(n,d,p), n, d, label))

    add(n0, d0, "interior")
    add(nmin, min(dmax, product/nmin), "N_min")
    add(nmax, min(dmax, product/nmax), "N_max")
    add(min(nmax, product/dmin), dmin, "D_min")
    add(min(nmax, product/dmax), dmax, "D_max")
    add(nmax, dmax, "N_max+D_max")

    if not candidates:
        raise ValueError("No feasible point inside declared B1 support")
    loss, N, D, source = min(candidates)
    cost = coeff*N*D
    flags = []
    tol=1e-8
    if abs(N-nmin) <= tol*max(1,nmin): flags.append("N_min")
    if abs(N-nmax) <= tol*max(1,nmax): flags.append("N_max")
    if abs(D-dmin) <= tol*max(1,dmin): flags.append("D_min")
    if abs(D-dmax) <= tol*max(1,dmax): flags.append("D_max")
    if cost < budget*(1-1e-9): flags.append("support_limited_budget_slack")
    return {
        "budget_FLOPs": budget,
        "context_tokens": L_ctx,
        "N_params_B": N,
        "D_tokens_B": D,
        "diagnostic_loss": loss,
        "C_train_plus_attn_FLOPs": cost,
        "budget_utilization": cost/budget,
        "candidate_source": source,
        "support_flags": ";".join(flags) if flags else "none",
        "Q_policy": "Q=Q0; C_Q=0; no Q performance term",
        "p_policy": "p=p_ref; no cross-Loss correction",
    }

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, default=Path("outputs/chm/q3_nd_diagnostic.csv"))
    parser.add_argument("--json", type=Path, default=Path("outputs/chm/q3_nd_diagnostic_manifest.json"))
    args=parser.parse_args()
    rows=[bounded_optimum(b,c) for b in BUDGETS for c in CONTEXTS]
    args.csv.parent.mkdir(parents=True, exist_ok=True)
    with args.csv.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    manifest={
      "schema_version":"chm.q3.nd_diagnostic.v1",
      "status":"diagnostic_only",
      "ready_for_Q3":False,
      "cyj_source_commit":"6c17cb4e387e1ac047f8fe0e9ecb6fe42fc5ef3b",
      "cyj_baseline_fit_sha256":"9b0e381fbc0ea84bb37d63ccb273733f3a03a0c2a834e8ef52cdb75c45bc6ead",
      "zhh_context_source_commit":"d47cd2dc921333caecfcb95f09eb5a2f2714d0db",
      "formula":"E+A*N_B^-alpha+B*D_B^-beta",
      "parameters":DEFAULT_PARAMS,
      "support":{"N_params_B":N_RANGE,"D_tokens_B":D_RANGE},
      "budgets_FLOPs":BUDGETS,
      "contexts_tokens":CONTEXTS,
      "excluded":["Q performance term","p cross-Loss term","Loss-Benchmark bridge"],
      "purpose":"validate cost algebra, analytic optimizer, and support-boundary handling before formal upstream interface exists",
    }
    args.json.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(rows,ensure_ascii=False))
if __name__=="__main__":
    main()
