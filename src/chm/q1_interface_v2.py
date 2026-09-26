"""Q1 v2: nonlinear interactions, explicit support, and A1 primary quality."""
from pathlib import Path
import csv
import hashlib
import json
import math
import numpy as np
from scipy.optimize import linprog

VERSION = "chm.q1.v2.0"
MANIFEST = Path("interfaces/chm/q1_interface_v2.json")
FROZEN_BUNDLE = Path("outputs/chm/q1_v2")
CURATED_BUNDLE = Path("outputs/Q1")


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


class Q1Interface:
    def __init__(self, root):
        self.root = Path(root)
        self.manifest = json.loads((self.root / MANIFEST).read_text(encoding="utf-8"))
        if self.manifest["schema_version"] != VERSION:
            raise ValueError("Q1 v2 required; no fallback to a linear producer")
        required = {"model", "features", "recipes", "quality", "mapping", "qa_mapping",
                    "validation", "nested_cv", "fold_stability"}
        if set(self.manifest["files"]) != required:
            raise ValueError("invalid v2 file inventory")
        self.paths = {}
        for key, item in self.manifest["files"].items():
            frozen_path = (self.root / item["path"]).resolve()
            frozen_root = (self.root / FROZEN_BUNDLE).resolve()
            if not frozen_path.is_relative_to(frozen_root):
                raise ValueError("release path escapes frozen v2 directory")
            # Keep the published manifest byte-for-byte; main stores its checked
            # content under the question directory while the producer branch
            # retains the original paths.
            path = (self.root / CURATED_BUNDLE / frozen_path.relative_to(frozen_root)).resolve()
            if not path.is_relative_to((self.root / CURATED_BUNDLE).resolve()):
                raise ValueError("curated path escapes Q1 directory")
            if _sha(path) != item["sha256"]:
                raise ValueError(f"Q1 v2 identity mismatch: {key}")
            self.paths[key] = path
        features = json.loads(self.paths["features"].read_text(encoding="utf-8"))
        self.domains = features["domain_order"]
        self.targets = features["target_order"]
        self.reference = features["Q1_reference_p"]
        self.ref = np.array([self.reference[d] for d in self.domains])
        self.model = json.loads(self.paths["model"].read_text(encoding="utf-8"))["targets"]
        self.pairs = [tuple(self.domains.index(d) for d in pair) for pair in features["pairs_order"]]
        self.main = np.array([[self.model[k]["main"][d] for d in self.domains] for k in self.targets])
        self.gamma = np.array([[r["gamma"] for r in self.model[k]["pairs"]] for k in self.targets])
        self.intercepts = np.array([self.model[k]["intercept"] for k in self.targets])
        self.reference_loss = np.array([self.model[k]["fitted_reference_loss"] for k in self.targets])
        recipes = _csv(self.paths["recipes"])
        self.recipe_ids = [r["index"] for r in recipes]
        self.recipes = np.array([[float(r[d]) for d in self.domains] for r in recipes])
        self.quality_rows = {r["quality_domain"]: r for r in _csv(self.paths["quality"]) if r["dataset_scope"] == "sample"}
        self.mapping_rows = {r["mixture_domain"]: r for r in _csv(self.paths["mapping"])}
        self.qa_rows = {r["mixture_domain"]: r for r in json.loads(self.paths["qa_mapping"].read_text(encoding="utf-8"))["rows"]}
        if len(self.domains) != 17 or len(self.targets) != 13 or len(self.pairs) != 10 or self.recipes.shape != (512, 17):
            raise ValueError("invalid Q1 dimensions")
        arrays = (self.main, self.gamma, self.intercepts, self.reference_loss, self.recipes, self.ref)
        if any(not np.isfinite(a).all() for a in arrays) or np.any(self.reference_loss <= 0):
            raise ValueError("nonfinite coefficients or nonpositive reference Loss")
        if np.min(self.recipes) < 0 or not np.allclose(self.recipes.sum(axis=1), 1, atol=1e-12, rtol=0):
            raise ValueError("invalid normalized recipes")
        if not np.allclose(self._predict(self.ref[None])[0], self.reference_loss, atol=1e-10, rtol=0):
            raise ValueError("fitted reference Loss mismatch")
        self.manifest_sha256 = _sha(self.root / MANIFEST)

    def _predict(self, x):
        pair = np.column_stack([x[:, a] * x[:, b] for a, b in self.pairs])
        return self.intercepts + x @ self.main.T + pair @ self.gamma.T

    def _vector(self, mixture):
        if not isinstance(mixture, dict) or set(mixture) != set(self.domains):
            raise ValueError("mixture must contain exactly 17 named domains")
        x = np.array([float(mixture[d]) for d in self.domains])
        if not np.isfinite(x).all() or x.min() < 0 or not math.isclose(float(x.sum()), 1, abs_tol=1e-10, rel_tol=0):
            raise ValueError("invalid simplex; no silent normalization")
        return x

    def support(self, mixture):
        x = self._vector(mixture)
        distances = np.max(abs(self.recipes - x), axis=1)
        nearest = int(np.argmin(distances))
        if distances[nearest] <= 1e-10:
            return {"in_A4_hull": True, "observed_index": self.recipe_ids[nearest], "residual": float(distances[nearest])}
        matrix = np.vstack([self.recipes.T, np.ones(len(self.recipes))])
        res = linprog(np.zeros(len(self.recipes)), A_eq=matrix, b_eq=np.r_[x, 1], bounds=(0, None), method="highs")
        residual = None if not res.success else float(np.max(abs(matrix @ res.x - np.r_[x, 1])))
        return {"in_A4_hull": bool(res.success and residual <= 1e-7), "observed_index": None, "residual": residual}

    def predict(self, mixture, *, allow_extrapolation=False):
        x = self._vector(mixture)
        support = self.support(mixture)
        if not support["in_A4_hull"] and not allow_extrapolation:
            raise ValueError("outside A4 hull; extrapolation requires explicit opt-in")
        loss = self._predict(x[None])[0]
        return {"schema_version": VERSION, "support": support, "loss_coordinate": "A4_A5_1M_target_cross_entropy",
                "loss": dict(zip(self.targets, map(float, loss))),
                "delta": dict(zip(self.targets, map(float, loss - self.reference_loss))),
                "relative": dict(zip(self.targets, map(float, loss / self.reference_loss - 1))),
                "cross_scale_transfer": "unidentified", "direct_B1_addition_allowed": False}

    def relative_effect(self, mixture, target, *, allow_extrapolation=False):
        if target not in self.targets:
            raise ValueError("unknown target")
        result = self.predict(mixture, allow_extrapolation=allow_extrapolation)
        return {"schema_version": VERSION, "target": target, "delta_target_loss_1m": result["delta"][target],
                "relative_target_loss_1m": result["relative"][target], "support": result["support"],
                "cross_scale_transfer": "unidentified", "direct_B1_addition_allowed": False}

    def effect_vector(self, mixture, *, allow_extrapolation=False):
        result = self.predict(mixture, allow_extrapolation=allow_extrapolation)
        return {**result, "effects": result["delta"]}

    def gradient(self, mixture):
        """Ambient derivatives; feasible transfers use grad[j] - grad[donor]."""
        x = self._vector(mixture)
        grad = self.main.copy()
        for t, (a, b) in enumerate(self.pairs):
            grad[:, a] += self.gamma[:, t] * x[b]
            grad[:, b] += self.gamma[:, t] * x[a]
        return grad

    def interaction_matrix(self):
        raise ValueError("v2 has no fixed 13x17 effect matrix; use gradient(p) and pair coefficients")

    def quality(self, domain):
        r = self.quality_rows[domain]
        return {"domain": domain, "Q_A_median": float(r["Q"]),
                "conditional_95": [float(r["uncertainty_low"]), float(r["uncertainty_high"])],
                "n_rows": int(r["n_rows"]), "coordinate": "A_composite_quality_proxy_z",
                "interpretation": "descriptive_composite_proxy_not_ground_truth",
                "B_Q_score_mapping": "unidentified", "direct_B_predictor_input_allowed": False}

    def mapped_quality(self, domain):
        r = self.mapping_rows[domain]
        return {"mixture_domain": domain, "mapping_type": r["mapping_type"],
                "quality_domain": None if r["mapping_type"] == "inferred" else r["quality_domain"],
                "quality": None if r["mapping_type"] == "inferred" else self.quality(r["quality_domain"])}

    def ranking_validation(self, target):
        if target not in self.targets:
            raise ValueError("unknown target")
        return [{"scope":r["scope"], "support_group":r["support_group"],
                 "n":int(r["n"]), "spearman":None if not r["interaction_spearman"] else float(r["interaction_spearman"]),
                 "rmse":float(r["interaction_rmse"]),
                 "ridge_comparator_rmse":float(r["ridge_rmse"]),
                 "constant_baseline_rmse":float(r["constant_rmse"]),
                 "interpretation":"rank_transfer_evidence_not_absolute_scale_calibration"}
                for r in _csv(self.paths["validation"]) if r["target"] == target]
