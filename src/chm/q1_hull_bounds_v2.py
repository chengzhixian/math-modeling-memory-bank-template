"""Spatial branch-and-bound LP bounds for interaction optimization over conv(A4).

McCormick envelopes bound the ten bilinear terms. Each node's LP is a valid
global lower bound; its convex weights provide a feasible upper candidate.
Reported gaps are numerical certificates within declared solver tolerances,
not interval-arithmetic proofs.
"""
from pathlib import Path
import heapq
import json
import math
import numpy as np
from scipy.optimize import linprog
from q1_interface import Q1Interface
from q1_mixture_decision_v2 import choose, POLICIES

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/processed/Q1/hull_bounds"


def data(q1, policy, weights, mode):
    n = len(q1.recipes)
    P = q1.recipes
    feature_dims = sorted({j for pair in q1.pairs for j in pair})
    lo = P[:, feature_dims].min(axis=0)
    hi = P[:, feature_dims].max(axis=0)
    w = np.array([weights[t] for t in q1.targets])
    scaled_main = q1.main / q1.reference_loss[:, None]
    scaled_pair = q1.gamma / q1.reference_loss[:, None]
    constants = q1.intercepts / q1.reference_loss - 1
    means = q1.ref
    base_rows = []
    base_rhs = []
    if policy != "unconstrained":
        accepted = {"direct"} if policy == "quality_direct" else {"direct","near_direct"}
        mask = np.array([q1.qa_rows[d]["mapping_type"] in accepted for d in q1.domains], float)
        qa = np.array([0 if q1.qa_rows[d]["Q_A"] is None else float(q1.qa_rows[d]["Q_A"]) for d in q1.domains])
        coverage = float(means @ mask)
        qmean = float(means @ (mask * qa) / coverage)
        base_rows += [-P @ mask, -P @ (mask * (qa-qmean))]
        base_rhs += [-coverage, 0.]
    return P, feature_dims, lo, hi, w, scaled_main, scaled_pair, constants, base_rows, base_rhs


def solve_node(q1, prepared, bounds, mode):
    P, dims, _, _, w, main, pair, constants, base_rows, base_rhs = prepared
    n, m = len(P), len(q1.pairs)
    epigraph = int(mode == "minimax")
    size = n + m + epigraph
    A, b = [], []
    for row, rhs in zip(base_rows, base_rhs):
        v = np.zeros(size); v[:n] = row; A.append(v); b.append(rhs)
    box = dict(zip(dims, bounds))
    for j, (lo, hi) in box.items():
        upper = np.zeros(size); upper[:n] = P[:,j]
        lower = -upper
        A.extend((upper, lower)); b.extend((hi, -lo))
    for t, (a, c) in enumerate(q1.pairs):
        la, ua = box[a]; lc, uc = box[c]
        # Four McCormick inequalities in (omega,z) coordinates.
        terms = ((lc,la,-1,la*lc),(uc,ua,-1,ua*uc),
                 (-lc,-ua,1,-ua*lc),(-uc,-la,1,-la*uc))
        for coeff_a, coeff_c, coeff_z, rhs in terms:
            row = np.zeros(size)
            row[:n] = coeff_a * P[:,a] + coeff_c * P[:,c]
            row[n+t] = coeff_z
            A.append(row); b.append(rhs)
    if mode == "weighted":
        c = np.r_[P @ (w @ main), w @ pair]
        constant = float(w @ constants)
    else:
        c = np.zeros(size); c[-1] = 1
        constant = 0.
        for k in np.flatnonzero(w > 0):
            row = np.zeros(size)
            row[:n] = P @ main[k]
            row[n:n+m] = pair[k]
            row[-1] = -1
            A.append(row); b.append(-constants[k])
    lp_bounds = [(0,None)] * n + [(0,1)] * m + ([(None,None)] if epigraph else [])
    result = linprog(c, A_ub=np.asarray(A), b_ub=np.asarray(b),
                     A_eq=np.r_[np.ones(n),np.zeros(m+epigraph)][None,:],
                     b_eq=[1.], bounds=lp_bounds, method="highs")
    if not result.success:
        if result.status == 2:
            return None
        raise RuntimeError(f"LP relaxation failed: {result.message}")
    omega = result.x[:n]
    x = omega @ P
    true_relative = q1._predict(x[None])[0] / q1.reference_loss - 1
    upper = float(true_relative @ w if mode == "weighted" else true_relative[w > 0].max())
    lower = float(result.fun + constant)
    return lower, upper, omega, x, result.x[n:n+m]


def certify(q1, policy, weights, mode="weighted", max_nodes=600, tolerance=1e-3):
    if mode not in {"weighted","minimax"} or policy not in POLICIES or tolerance <= 0 or max_nodes < 1:
        raise ValueError("invalid bound settings")
    if not isinstance(weights,dict) or set(weights) != set(q1.targets):
        raise ValueError("all 13 target weights required")
    w = np.array([float(weights[k]) for k in q1.targets])
    if not np.isfinite(w).all() or np.any(w < 0) or not np.isclose(w.sum(),1,atol=1e-12):
        raise ValueError("weights must be finite, nonnegative and sum to one")
    prepared = data(q1, policy, weights, mode)
    _, dims, lo, hi, *_ = prepared
    first = tuple((float(a), float(b)) for a,b in zip(lo,hi))
    initial = solve_node(q1, prepared, first, mode)
    if initial is None:
        raise ValueError("quality policy infeasible over convex hull")
    observed = choose(q1, weights, policy, mode)
    best = min([(observed["objective_relative"], np.array(list(observed["composition"].values())),
                 "observed_A4_"+observed["selected_index"]),
                (initial[1],initial[3],"LP_relaxation_feasible_composition")], key=lambda z:z[0])
    heap = [(initial[0],0,first,initial)]
    serial = 1
    solved = 1
    while heap and solved < max_nodes and best[0] - heap[0][0] > tolerance:
        lower, _, box, result = heapq.heappop(heap)
        if lower >= best[0]-tolerance:
            continue
        # Split the widest selected interaction dimension, while preserving
        # the entire feasible hull through complementary half boxes.
        widths = [b-a for a,b in box]
        split = int(np.argmax(widths))
        midpoint = (box[split][0] + box[split][1]) / 2
        for child_bounds in ((box[split][0],midpoint),(midpoint,box[split][1])):
            child = list(box); child[split] = child_bounds; child = tuple(child)
            answer = solve_node(q1, prepared, child, mode)
            solved += 1
            if answer is None:
                continue
            if answer[1] < best[0]:
                best = (answer[1],answer[3],"convex_hull_feasible")
            if answer[0] < best[0]-tolerance:
                heapq.heappush(heap,(answer[0],serial,child,answer)); serial += 1
    lower_bound = min(best[0],heap[0][0]) if heap else best[0]
    return {"schema_version":"chm.q1.hull_bounds.v2",
            "Q1_version":q1.manifest["schema_version"],"Q1_manifest_sha256":q1.manifest_sha256,
            "policy":policy,"mode":mode,"weights":weights,"support":"convex_hull_A4",
            "lower_bound_relative":float(lower_bound),
            "feasible_upper_bound_relative":float(best[0]),
            "absolute_gap_relative":float(best[0]-lower_bound),
            "gap_at_or_below_tolerance":bool(best[0]-lower_bound<=tolerance+1e-9),
            "tolerance":tolerance,"nodes_solved":solved,"nodes_open":len(heap),
            "feasible_composition":dict(zip(q1.domains,map(float,best[1]))),
            "feasible_solution_source":best[2],
            "best_observed_A4_index":observed["selected_index"],
            "best_observed_A4_objective_relative":observed["objective_relative"],
            "certificate_kind":"McCormick_LP_relaxation_numerical_bounds",
            "continuous_optimum_exact_claim":False,
            "ready_for_Q3_empirical_absolute_loss":False}


def release():
    q1 = Q1Interface(ROOT)
    weights = {k:1/len(q1.targets) for k in q1.targets}
    cases = [(p,"weighted") for p in ("unconstrained","quality_direct","quality_direct_and_near")]
    cases += [("unconstrained","minimax")]
    records = [certify(q1,p,weights,mode) for p,mode in cases]
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"bounds.json").write_text(json.dumps(records,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return records


if __name__=="__main__":
    print(json.dumps(release(),ensure_ascii=False,indent=2))
