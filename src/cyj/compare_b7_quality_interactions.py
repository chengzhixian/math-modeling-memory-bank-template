"""Exploratory nested grouped CV of preregistered B7 quality interactions."""
from __future__ import annotations

import hashlib
import json
import platform
from collections import Counter

import numpy as np

from audit_b_scaling_laws import ROOT, sha256
from quality_scaling import fit as fit_base, source_data

OUTPUT = ROOT / "outputs/cyj/quality/b7_interaction_comparison.json"
PROTOCOL = ROOT / "experiments/cyj/20260924-b7-interaction-preregistered-protocol.md"
FAMILIES = ("no_Q", "constant_G", "Q_x_logN", "Q_x_logD", "Q_x_logN_logD")
AXES = ("N_params_B", "D_tokens_B", "Q_score")


def design(x, alpha, beta, family):
    n, d, q = np.asarray(x, float).T
    base = [np.ones(len(n)), n**-alpha, d**-beta]
    if family != "no_Q":
        base.append(1-q)
    if family in ("Q_x_logN", "Q_x_logN_logD"):
        base.append(np.log(n)*(1-q))
    if family in ("Q_x_logD", "Q_x_logN_logD"):
        base.append(np.log(d/100)*(1-q))
    return np.column_stack(base)


def gain(n, d, coefficients, family):
    if family == "no_Q":
        return np.zeros_like(np.asarray(n, float))
    value = np.full_like(np.asarray(n, float), coefficients[3], dtype=float)
    offset = 4
    if family in ("Q_x_logN", "Q_x_logN_logD"):
        value += coefficients[offset]*np.log(n)
        offset += 1
    if family in ("Q_x_logD", "Q_x_logN_logD"):
        value += coefficients[offset]*np.log(d/100)
    return value


def base_exponents(x, y):
    result = fit_base(x, y, "no_quality")
    if not result["converged"] or result["at_exponent_boundary"]:
        raise ValueError("base exponent fit did not converge away from boundary")
    return result["parameters"]["alpha"], result["parameters"]["beta"]


def fit_candidates(x, y):
    alpha, beta = base_exponents(x, y)
    fitted = {}
    for family in FAMILIES:
        matrix = design(x, alpha, beta, family)
        coef, _, rank, _ = np.linalg.lstsq(matrix, y, rcond=None)
        if rank != matrix.shape[1] or not np.all(np.isfinite(coef)) or np.any(coef[:3] <= 0):
            fitted[family] = {"valid": False, "reason": "rank or positive base amplitudes"}
            continue
        g = gain(x[:,0], x[:,1], coef, family)
        if np.any(g < -1e-10):
            fitted[family] = {"valid": False, "reason": "negative quality gain on training grid"}
            continue
        fitted[family] = {"valid": True, "alpha": float(alpha), "beta": float(beta),
                          "coefficients": list(map(float, coef)),
                          "training_rmse": float(np.sqrt(np.mean((matrix@coef-y)**2))),
                          "training_quality_gain_range": [float(np.min(g)),float(np.max(g))]}
    return fitted


def predict(model, x, family):
    return design(x, model["alpha"], model["beta"], family) @ model["coefficients"]


def score(predicted, observed):
    residual = np.asarray(predicted)-np.asarray(observed)
    return {"rmse": float(np.sqrt(np.mean(residual**2))),
            "mae": float(np.mean(np.abs(residual))),
            "mean_bias_prediction_minus_observed": float(np.mean(residual))}


def gradient_range(model, family, support):
    n = np.array([support["N_params_B"][0], support["N_params_B"][-1]]*2)
    d = np.array([support["D_tokens_B"][0]]*2+[support["D_tokens_B"][-1]]*2)
    gain_values = gain(n, d, np.asarray(model["coefficients"]), family)
    return [float(-np.max(gain_values)), float(-np.min(gain_values))]


def inner_select(x, y, axis):
    scores = {f: [] for f in FAMILIES}
    failures = {f: [] for f in FAMILIES}
    for level in np.unique(x[:,axis]):
        held = x[:,axis] == level
        try:
            candidates = fit_candidates(x[~held], y[~held])
        except ValueError as exc:
            for family in FAMILIES:
                failures[family].append({"level": float(level), "reason": str(exc)})
            continue
        for family, model in candidates.items():
            if model["valid"]:
                scores[family].append(score(predict(model,x[held],family),y[held])["rmse"])
            else:
                failures[family].append({"level": float(level), "reason": model["reason"]})
    means = {f: float(np.mean(scores[f])) if scores[f] and not failures[f] else None for f in FAMILIES}
    valid = [f for f in FAMILIES if means[f] is not None]
    if not valid:
        raise ValueError("all candidates invalid in inner selection")
    selected = min(valid, key=lambda f: (means[f], FAMILIES.index(f)))
    return selected, means, failures


def main():
    sources, x, y, rows = source_data()
    if len(x) != 450:
        raise ValueError("expected 450 unique B7 points")
    support = {axis: sorted(map(float,np.unique(x[:,i]))) for i,axis in enumerate(AXES)}
    outer = []
    selected_predictions = []
    for axis, name in enumerate(AXES):
        for level in np.unique(x[:,axis]):
            held = x[:,axis] == level
            selected, means, failures = inner_select(x[~held],y[~held],axis)
            candidates = fit_candidates(x[~held],y[~held])
            all_scores = {}
            for family, model in candidates.items():
                all_scores[family] = (score(predict(model,x[held],family),y[held]) if model["valid"]
                                      else {"invalid": model["reason"]})
            model = candidates[selected]
            if not model["valid"]:
                raise ValueError("inner selected model invalid on outer train")
            pred = predict(model,x[held],selected)
            selected_predictions.extend({"outer_axis": name, "held_level": float(level),
                                         "source_line": rows[i]["source_line"],
                                         "N_params_B": float(x[i,0]), "D_tokens_B": float(x[i,1]),
                                         "Q_score": float(x[i,2]), "observed": float(y[i]),
                                         "predicted": float(value), "selected_family": selected}
                                        for i,value in zip(np.flatnonzero(held),pred))
            outer.append({"axis": name, "held_level": float(level), "train_rows": int((~held).sum()),
                          "test_rows": int(held.sum()), "inner_selected": selected,
                          "inner_mean_rmse": means, "inner_failures": failures,
                          "candidate_outer_scores": all_scores,
                          "selected_score": score(pred,y[held]),
                          "selected_model": model,
                          "selected_gradient_range_full_support": gradient_range(model,selected,support)})
    full_models = fit_candidates(x,y)
    rng = np.random.default_rng(20260924)
    clusters = np.unique(x[:,:2],axis=0)
    indices = [np.flatnonzero(np.all(x[:,:2]==pair,axis=1)) for pair in clusters]
    bootstrap = {f: {"accepted": [], "rejected": []} for f in FAMILIES}
    for sample_id in range(100):
        draw = rng.integers(0,len(indices),len(indices))
        chosen = np.concatenate([indices[i] for i in draw])
        try:
            models = fit_candidates(x[chosen],y[chosen])
        except ValueError as exc:
            for family in FAMILIES:
                bootstrap[family]["rejected"].append({"sample_id":sample_id,"reason":str(exc)})
            continue
        for family, model in models.items():
            if model["valid"]:
                bootstrap[family]["accepted"].append({"sample_id":sample_id,
                    "alpha":model["alpha"],"beta":model["beta"],
                    "coefficients":model["coefficients"],
                    "gradient_range_full_support":gradient_range(model,family,support)})
            else:
                bootstrap[family]["rejected"].append({"sample_id":sample_id,"reason":model["reason"]})
    selections = Counter(row["inner_selected"] for row in outer)
    by_axis = {axis: {family: {"mean_outer_rmse": float(np.mean([r["selected_score"]["rmse"]
                  for r in outer if r["axis"]==axis and r["inner_selected"]==family])) if selections[family] and
                  any(r["axis"]==axis and r["inner_selected"]==family for r in outer) else None,
                  "selected_folds": sum(r["axis"]==axis and r["inner_selected"]==family for r in outer)}
                  for family in FAMILIES} for axis in AXES}
    output = {"schema_version":"cyj.b7_interaction_exploratory.v1", "status":"exploratory_semi_synthetic",
              "ready_for_Q3":False, "source_files":sources,
              "code_sha256_utf8_lf":hashlib.sha256((ROOT/"src/cyj/compare_b7_quality_interactions.py").read_bytes().replace(b"\r\n",b"\n")).hexdigest(),
              "protocol_sha256":sha256(PROTOCOL),
              "environment":{"python":platform.python_version(),"numpy":np.__version__},
              "seed":20260924,"support":support,"families":FAMILIES,
              "validation_caveat":"candidate ideas were informed by all B7 in prior diagnosis; nested CV is within-source exploratory, not an untouched final test",
              "outer_folds":outer,"selected_predictions":selected_predictions,
              "selection_counts":dict(selections),"by_axis":by_axis,
              "full_models":full_models,"bootstrap_ND_clusters":bootstrap}
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(output,indent=2,allow_nan=False)+"\n",encoding="utf-8",newline="\n")
    print(json.dumps({"output_sha256":sha256(OUTPUT),"outer_folds":len(outer),
                      "selection_counts":dict(selections),
                      "bootstrap_accepts":{k:len(v["accepted"]) for k,v in bootstrap.items()}}))


if __name__=="__main__":
    main()
