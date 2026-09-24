"""Consume pinned chm.q1.v1 and expose a guarded B1/p scenario API."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import re
import subprocess
import tempfile
from functools import lru_cache
from pathlib import Path

from audit_b_scaling_laws import ROOT, sha256
from scaling_provenance import verify_code_files

BUNDLE = ROOT / "outputs/cyj/interfaces/q3_bundle.json"
FIT = ROOT / "outputs/cyj/classic/classic_fit.json"
FIT_SHA = "9b0e381fbc0ea84bb37d63ccb273733f3a03a0c2a834e8ef52cdb75c45bc6ead"
PANEL = ("pile_cc", "wikipedia_en", "arxiv", "stackexchange", "github")
MANIFEST = "interfaces/chm/q1_interface_v1.json"


def finite(value, name):
    if isinstance(value, bool):
        raise ValueError(f"{name} must be a finite number")
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite")
    return value


@lru_cache(maxsize=4)
def load_chm(commit):
    """Load the reviewed producer reader from exact Git blobs, without a copy in the repo."""
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("CHM input must be a full immutable commit SHA")
    identities = {}

    def blob(path):
        raw = subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=ROOT)
        identities[path] = {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
        return raw

    manifest_bytes = blob(MANIFEST)
    manifest = json.loads(manifest_bytes)
    if manifest.get("schema_version") != "chm.q1.v1":
        raise ValueError("unsupported CHM manifest")
    with tempfile.TemporaryDirectory(prefix="cyj-chm-interface-") as temporary:
        root = Path(temporary)
        paths = [MANIFEST, "src/chm/q1_interface.py"] + [item["path"] for item in manifest["files"].values()]
        for relative in paths:
            if ".." in Path(relative).parts or not relative.startswith(("interfaces/chm/", "src/chm/", "outputs/chm/")):
                raise ValueError("unexpected producer path")
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(manifest_bytes if relative == MANIFEST else blob(relative))
        spec = importlib.util.spec_from_file_location("cyj_pinned_chm_q1", root / "src/chm/q1_interface.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        q1 = module.Q1Interface(root)
    for name in ("CONTRACT.md", "USAGE.md", "CYJ_REQUIRED_INTERFACE.md", "Q2_BRIDGE.md", "UNCERTAINTY.md", "OFFICIAL_DATA_REVIEW.md"):
        blob("interfaces/chm/" + name)
    return q1, identities


class Predictor:
    def __init__(self, bundle_path=BUNDLE):
        self.bundle = json.loads(Path(bundle_path).read_text(encoding="utf-8"))
        if self.bundle.get("schema_version") != "cyj.q3.v1" or self.bundle.get("ready_for_Q3") is not False:
            raise ValueError("unsupported CYJ bundle or unexpected validation state")
        self.q1, identities = load_chm(self.bundle["provenance"]["chm_commit"])
        if identities != self.bundle["provenance"]["chm_files"]:
            raise ValueError("pinned CHM identities do not match bundle")

    def predict(self, *, N_params_B, D_tokens_B, mode="formal", Q_score=None,
                p=None, target=None, lambda_loss=None, eta=None, allow_extrapolation=False):
        if mode not in ("diagnostic", "scenario"):
            raise ValueError("formal Q3 blocked: joint validation incomplete")
        if Q_score is not None:
            raise ValueError("B-native Q_score effect not fitted; Q_z substitution forbidden")
        n, d = finite(N_params_B, "N_params_B"), finite(D_tokens_B, "D_tokens_B")
        if n <= 0 or d <= 0:
            raise ValueError("N and D must be positive")
        scope = self.bundle["baseline"]["scope"]
        outside = [name for name, value in (("N_params_B", n), ("D_tokens_B", d))
                   if not scope[name][0] <= value <= scope[name][1]]
        params = self.bundle["baseline"]["parameters"]
        n_term = params["A"] * n ** -params["alpha"]
        d_term = params["B"] * d ** -params["beta"]
        base, correction, effect, p_gradient = params["E"] + n_term + d_term, 0.0, None, None
        if mode == "diagnostic":
            if any(v is not None for v in (p, target, lambda_loss, eta)):
                raise ValueError("p corrections require explicit scenario mode")
        else:
            if any(v is None for v in (p, target, lambda_loss, eta)):
                raise ValueError("scenario requires p, target, lambda_loss and eta")
            if target not in PANEL:
                raise ValueError("target outside adopted sensitivity panel")
            lam, decay = finite(lambda_loss, "lambda_loss"), finite(eta, "eta")
            if lam < 0 or decay < 0:
                raise ValueError("this scenario family requires nonnegative lambda_loss and eta")
            effect = self.q1.relative_effect(p, target, n_params=n * 1e9, eta=decay)
            if effect["scale_status"] == "extrapolated_model_scale":
                outside.append("CHM_model_scale")
            correction = lam * effect["delta_target_loss"]
            multiplier = lam * effect["scale_factor"]
            p_gradient = {name: multiplier * float(self.q1.coefficients[target][name]) for name in self.q1.reference}
        if outside and not allow_extrapolation:
            raise ValueError("explicit extrapolation opt-in required: " + ",".join(outside))
        loss = base + correction
        if not math.isfinite(loss) or loss <= 0:
            raise ValueError("invalid scenario Loss")
        return {
            "interface_version": "cyj.q3.v1", "mode": mode, "ready_for_Q3": False,
            "loss_value": loss, "loss_coordinate": self.bundle["baseline"]["loss_coordinate"],
            "N_params_B": n, "D_tokens_B": d, "Q_score": None, "mapping_status": "unidentified",
            "baseline_loss": base, "mixture_correction": correction, "p_effect": effect,
            "lambda_loss": lambda_loss, "p": p,
            "gradient": {"N_params_B": -params["alpha"] * n_term / n - (float(eta) * correction / n if effect else 0.0),
                         "D_tokens_B": -params["beta"] * d_term / d, "p_simplex_contrasts": p_gradient},
            "extrapolation_flags": outside,
            "uncertainty": {"total_interval": None, "B1_parameter_layer": "conditional_bootstrap_separate",
                            "cross_loss_lambda": "scenario" if effect else "not_used", "benchmark_bridge": "not_included"},
            "provenance": {key: self.bundle["provenance"][key] for key in ("cyj_code_commit", "chm_commit", "chm_manifest_sha256")},
        }


def build_bundle(chm_commit, input_version):
    verify_code_files(input_version, ("src/cyj/q3_interface.py", "src/cyj/scaling_provenance.py", "src/cyj/audit_b_scaling_laws.py"))
    q1, identities = load_chm(chm_commit)
    if sha256(FIT) != FIT_SHA:
        raise ValueError("reviewed B1 fit identity changed")
    fit = json.loads(FIT.read_text(encoding="utf-8"))
    return {
        "schema_version": "cyj.q3.v1", "ready_for_Q3": False,
        "status": "consumer_accepted_A_interface; B_bridge_scenario_only",
        "provenance": {"cyj_code_commit": input_version, "chm_commit": chm_commit,
                       "chm_branch": "integration/chm-q1-clean-20260923", "chm_files": identities,
                       "chm_manifest_sha256": identities[MANIFEST]["sha256"],
                       "baseline_fit_sha256": FIT_SHA, "baseline_input_version": fit["input_version"], "main_integrated": False},
        "baseline": {"parameters": fit["full_fit"]["parameters"],
                     "scope": {name: fit["data_scope"][name + "_range"] for name in ("N_params_B", "D_tokens_B")},
                     "loss_coordinate": {"field": "B1.val_loss", "kind": "validation_cross_entropy",
                                         "model_family": "attachment_B1_Pythia", "evaluation_corpus": None,
                                         "tokenizer": None, "log_base": None, "aggregation": None}},
        "adoption": {"Q_mapping_status": "unidentified", "Q_use": "A_native_relative_ranking",
                     "domains": list(q1.reference), "target_panel": list(PANEL), "primary_anchor": None,
                     "p_rule": "strict named simplex; CHM relative_effect; no silent normalization",
                     "lambda_loss_unit": "B1_loss / A_target_loss", "lambda_status": "explicit_scenario_only",
                     "eta_default_policy": "caller_must_supply", "eta_producer_estimate": q1.scale["pooled_eta"],
                     "eta_conditional_interval": q1.scale["calibration_sample_domain_bootstrap_95"]},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--chm-version")
    parser.add_argument("--input-version")
    parser.add_argument("--bundle", type=Path, default=BUNDLE)
    parser.add_argument("--request", type=Path)
    args = parser.parse_args()
    if args.build:
        if not args.chm_version or not args.input_version:
            parser.error("--build requires --chm-version and --input-version")
        result = build_bundle(args.chm_version, args.input_version)
        args.bundle.parent.mkdir(parents=True, exist_ok=True)
        args.bundle.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
        print(f"built {args.bundle}; ready_for_Q3=false")
    else:
        if not args.request:
            parser.error("provide --request JSON or --build")
        print(json.dumps(Predictor(args.bundle).predict(**json.loads(args.request.read_text(encoding="utf-8"))), ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
