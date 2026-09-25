"""B7-native quality candidates; no implied bridge to B1 or attachment A."""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
from pathlib import Path

import numpy as np

from audit_b_scaling_laws import ROOT, DEFAULT_DATA_ROOT, DEFAULT_MANIFEST, DEFAULT_SOURCE_MANIFEST, sha256, validate_input_version
from diagnose_b_quality import FILES, AXES, coordinate_map, read_data
from scaling_common import nelder_mead
from scaling_provenance import verify_source_files, verify_code_files

OUTPUT = ROOT / "outputs/cyj/quality/b7_quality_fit.json"
FAMILIES = ("no_quality", "linear_quality", "log_quality")
CODE = ("src/cyj/quality_scaling.py", "src/cyj/diagnose_b_quality.py",
        "src/cyj/scaling_common.py", "src/cyj/scaling_provenance.py", "src/cyj/audit_b_scaling_laws.py")


def design(x, exponents, family):
    if family not in FAMILIES:
        raise ValueError("unknown quality family")
    n, d, q = np.asarray(x, dtype=float).T
    columns = [np.ones(len(n)), n ** -exponents[0], d ** -exponents[1]]
    if family == "linear_quality":
        columns.append(1 - q)
    elif family == "log_quality":
        columns.append(-np.log(q))
    return np.column_stack(columns)


def evaluate(parameters, x, family):
    amplitudes = [parameters[k] for k in ("E", "A", "B")]
    if family != "no_quality":
        amplitudes.append(parameters["G"])
    return design(x, [parameters["alpha"], parameters["beta"]], family) @ amplitudes


def fit(x, y, family):
    """Profile OLS amplitudes; optimize two exponents from four fixed starts."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    if x.ndim != 2 or x.shape != (len(y), 3) or len(y) < 8:
        raise ValueError("expected at least eight N,D,Q rows")
    if not np.all(np.isfinite(x)) or not np.all(np.isfinite(y)) or np.any(x <= 0) or np.any(x[:, 2] > 1) or np.any(y <= 0):
        raise ValueError("nonfinite or invalid training values")

    def profile(log_exp, details=False):
        exponents = np.exp(log_exp)
        if np.any(exponents < .02) or np.any(exponents > 1.5):
            return float("inf")
        matrix = design(x, exponents, family)
        coef, _, rank, _ = np.linalg.lstsq(matrix, y, rcond=None)
        if rank != matrix.shape[1] or np.any(coef <= 0):
            return float("inf")
        value = float(np.mean((matrix @ coef - y) ** 2))
        return (value, coef) if details else value

    candidates = [nelder_mead(profile, np.log(start), max_iterations=600)
                  for start in ((.15, .15), (.15, .6), (.6, .15), (.6, .6))]
    point, objective, iterations, converged = min(candidates, key=lambda c: c[1])
    if not np.isfinite(objective):
        raise ValueError(f"no admissible positive fit: {family}")
    _, coef = profile(point, details=True)
    exponents = np.exp(point)
    parameters = dict(zip(("E", "A", "B", "G"), map(float, coef)))
    parameters.update(alpha=float(exponents[0]), beta=float(exponents[1]))
    return {"parameters": parameters, "mse": objective, "converged": bool(converged),
            "iterations": iterations, "starts": 4,
            "at_exponent_boundary": bool(np.any(exponents < .02001) or np.any(exponents > 1.49999))}


def folds(x):
    for axis, name in enumerate(AXES):
        for value in np.unique(x[:, axis]):
            test = x[:, axis] == value
            yield name, float(value), ~test, test


def source_data():
    identity = verify_source_files(DEFAULT_DATA_ROOT, DEFAULT_MANIFEST, (FILES["B6"], FILES["B7"]))
    base = coordinate_map(read_data(DEFAULT_DATA_ROOT / FILES["B6"]))
    expanded = coordinate_map(read_data(DEFAULT_DATA_ROOT / FILES["B7"]))
    if not base.keys() <= expanded.keys() or any(base[k]["val_loss"] != expanded[k]["val_loss"] for k in base):
        raise ValueError("B6 is no longer an exact subset of B7; review deduplication")
    rows = [expanded[k] for k in sorted(expanded)]
    x = np.array([[r[a] for a in AXES] for r in rows])
    y = np.array([r["val_loss"] for r in rows])
    return identity, x, y, rows


def experiment(version):
    identity, x, y, rows = source_data()
    models = {}
    for family in FAMILIES:
        results = []
        for axis, value, train, test in folds(x):
            fitted = fit(x[train], y[train], family)
            predicted = evaluate(fitted["parameters"], x[test], family)
            results.append({"axis": axis, "held_value": value, "train_rows": int(train.sum()),
                            "test_rows": int(test.sum()), "test_source_lines": [rows[i]["source_line"] for i in np.flatnonzero(test)],
                            "rmse": float(np.sqrt(np.mean((predicted - y[test]) ** 2))),
                            "fit": fitted})
        axis_rmse = {a: float(np.mean([r["rmse"] for r in results if r["axis"] == a])) for a in AXES}
        models[family] = {"full_fit": fit(x, y, family), "folds": results, "axis_mean_rmse": axis_rmse,
                          "selection_score": float(np.mean(list(axis_rmse.values())))}
        print(json.dumps({"family": family, "axis_mean_rmse": axis_rmse}), flush=True)
    selected = min(models, key=lambda f: models[f]["selection_score"])
    if any(not r["fit"]["converged"] or r["fit"]["at_exponent_boundary"] for r in models[selected]["folds"]):
        raise ValueError("selected model has unsuccessful validation fits")
    rng = np.random.default_rng(20260924)
    clusters = np.unique(x[:, :2], axis=0)
    indices = [np.flatnonzero(np.all(x[:, :2] == cluster, axis=1)) for cluster in clusters]
    samples, rejected = [], []
    for sample_id in range(50):
        draw = rng.integers(0, len(indices), len(indices))
        selected_rows = np.concatenate([indices[i] for i in draw])
        try:
            fitted = fit(x[selected_rows], y[selected_rows], selected)
            if not fitted["converged"] or fitted["at_exponent_boundary"]:
                raise ValueError("nonconverged or boundary fit")
            samples.append({"sample_id": sample_id, "parameters": fitted["parameters"]})
        except ValueError as exc:
            rejected.append({"sample_id": sample_id, "reason": str(exc)})
    return {"schema_version": "cyj.b7_quality.v1", "input_version": version,
            "source_files": identity, "code_files": {p: hashlib.sha256((ROOT / p).read_bytes().replace(b"\r\n", b"\n")).hexdigest() for p in CODE},
            "code_hash_encoding": "UTF-8 bytes with CRLF normalized to LF",
            "environment": {"python": platform.python_version(), "numpy": np.__version__},
            "rows": len(y), "B6_duplicate_rows_excluded": len(read_data(DEFAULT_DATA_ROOT / FILES["B6"])),
            "support": {a: sorted(map(float, np.unique(x[:, i]))) for i, a in enumerate(AXES)},
            "protocol": {"objective": "unweighted original-Loss MSE; equal Q rows per N,D cluster",
                         "exponent_bounds": [.02, 1.5], "positive_amplitudes": True,
                         "selection": "lowest mean of three axis-mean held-level RMSE; descriptive model selection, not nested unbiased evaluation",
                         "excluded": ["B8 calibrated", "B8 extrapolated", "B1", "attachment A"]},
            "models": models, "selected_family": selected,
            "bootstrap": {"unit": "N,D cluster, all Q kept together", "seed": 20260924,
                          "requested": 50, "samples": samples, "rejected": rejected,
                          "scope": "conditional on selected model and semi-synthetic B7; not independent training runs or total prediction uncertainty"},
            "loss_coordinate": {"id": "attachment_B7_native_val_loss", "nature": "semi_synthetic",
                                "evaluation_corpus": None, "tokenizer": None, "log_base": None,
                                "B1_bridge": "not_established", "A_Q_mapping": "unidentified"},
            "ready_for_Q3": False, "ready_for_Q4": False}


class QualityPredictor:
    def __init__(self, path=OUTPUT, *, expected_sha256):
        path = Path(path)
        if sha256(path) != expected_sha256:
            raise ValueError("quality fit hash mismatch")
        self.data = json.loads(path.read_text(encoding="utf-8"))
        if self.data["schema_version"] != "cyj.b7_quality.v1" or self.data["ready_for_Q3"] is not False:
            raise ValueError("unsupported quality release")
        self.sha = expected_sha256
        self.family = self.data["selected_family"]
        self.parameters = self.data["models"][self.family]["full_fit"]["parameters"]

    def predict(self, N_params_B, D_tokens_B, Q_score, *, mode="formal"):
        if mode != "diagnostic":
            raise ValueError("only explicit B7 diagnostic mode is supported; no B1/A/Benchmark bridge")
        values = (N_params_B, D_tokens_B, Q_score)
        if any(isinstance(v, bool) for v in values):
            raise ValueError("boolean is not a model input")
        point = np.array(values, dtype=float)
        if not np.all(np.isfinite(point)):
            raise ValueError("nonfinite input")
        for axis, value in zip(AXES, point):
            support = self.data["support"][axis]
            if not support[0] <= value <= support[-1]:
                raise ValueError(f"outside B7 support: {axis}")
        n, d, q = point
        p = self.parameters
        ln = -p["alpha"] * p["A"] * n ** (-p["alpha"] - 1)
        ld = -p["beta"] * p["B"] * d ** (-p["beta"] - 1)
        lq = 0 if self.family == "no_quality" else -p["G"] if self.family == "linear_quality" else -p["G"] / q
        samples = self.data["bootstrap"]["samples"]
        draws = [float(evaluate(s["parameters"], point[None, :], self.family)[0]) for s in samples]
        return {"loss_value": float(evaluate(p, point[None, :], self.family)[0]),
                "loss_coordinate": self.data["loss_coordinate"], "family": self.family,
                "gradient": dict(zip(AXES, map(float, (ln, ld, lq)))),
                "equal_loss_dN_dQ": float(-lq / ln),
                "uncertainty": {"sample_ids": [s["sample_id"] for s in samples],
                                "conditional_mean_samples": draws,
                                "conditional_mean_percentile_95": np.quantile(draws, [.025, .975]).tolist() if len(draws) >= 40 else None,
                                "scope": self.data["bootstrap"]["scope"], "total_prediction_interval": None},
                "source_sha256": self.sha, "input_version": self.data["input_version"],
                "ready_for_Q3": False, "ready_for_Q4": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-version", required=True)
    args = parser.parse_args()
    version = validate_input_version(args.input_version, DEFAULT_MANIFEST, DEFAULT_SOURCE_MANIFEST)
    verify_code_files(version, CODE)
    result = experiment(version)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"sha256": sha256(OUTPUT), "selected_family": result["selected_family"],
                      "accepted_bootstrap": len(result["bootstrap"]["samples"])}))


if __name__ == "__main__":
    main()
