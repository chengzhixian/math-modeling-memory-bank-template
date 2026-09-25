"""Pinned, derived-output-only consumer for CHM's signed Q1 interaction release."""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
CHM_SOURCE = ROOT / "src/chm"
if str(CHM_SOURCE) not in sys.path:
    sys.path.insert(0, str(CHM_SOURCE))
from q1_interface_v2 import Q1Interface  # noqa: E402

EXPECTED_SHA = "c621f7e405106e42720f918f490235b5e8becefb0f7c8cb997736e96337117a9"
EXPECTED_BOUNDS_SHA = "969f810c0bf54f03492afc243091c339aaf4b27aed5c2164c186e651c7589acc"
SOURCE_COMMIT = "333b1f0bbed65da43f6be2f197d9582555dc755d"
POLICY_TOL = 1e-10


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


class Q1V2Consumer:
    def __init__(self, root: Path = ROOT, expected_sha: str = EXPECTED_SHA):
        self.root = Path(root)
        path = self.root / "interfaces/chm/q1_interface_v2.json"
        actual = sha256(path)
        if actual != expected_sha:
            raise ValueError(f"Q1 v2 manifest identity mismatch: {actual}")
        self.upstream = Q1Interface(self.root)  # verifies schema and each referenced file
        if self.upstream.manifest_sha256 != actual:
            raise ValueError("Q1 manifest verification disagrees")
        self.manifest_sha256 = actual
        self.domains = tuple(self.upstream.domains)
        self.targets = tuple(self.upstream.targets)
        self.reference = self.upstream.reference.copy()
        self.ref_vector = self.upstream.ref.copy()
        self.recipes = self.upstream.recipes.copy()
        self.recipe_ids = tuple(self.upstream.recipe_ids)
        self.reference_loss = self.upstream.reference_loss.copy()
        self.qa_rows = self.upstream.qa_rows
        if len(self.qa_rows) != 17 or sum(row["Q_A"] is None for row in self.qa_rows.values()) != 11:
            raise ValueError("Q1 v2 QA mapping does not match signed primary scope")
        self.bounds_path = self.root / "outputs/chm/q1_v2_hull_bounds/bounds.json"
        if sha256(self.bounds_path) != EXPECTED_BOUNDS_SHA:
            raise ValueError("CHM hull bounds identity mismatch")
        self.bounds = json.loads(self.bounds_path.read_text(encoding="utf-8"))
        if len(self.bounds) != 4 or any(row["Q1_manifest_sha256"] != actual for row in self.bounds):
            raise ValueError("CHM hull bounds do not match pinned Q1 release")

    def point(self, p: dict) -> np.ndarray:
        if not isinstance(p, dict) or set(p) != set(self.domains) or any(
            isinstance(value, bool) or not isinstance(value, (int, float)) for value in p.values()
        ):
            raise ValueError("p must contain exactly 17 numeric named proportions")
        return self.upstream._vector(p)

    def p_dict(self, point: np.ndarray) -> dict[str, float]:
        return dict(zip(self.domains, map(float, point)))

    def weight_vector(self, weights: dict) -> np.ndarray:
        if not isinstance(weights, dict) or not weights or set(weights) - set(self.targets):
            raise ValueError("weights must name one or more known Q1 targets")
        if any(isinstance(value, bool) or not isinstance(value, (int, float)) for value in weights.values()):
            raise ValueError("weights must be numeric")
        result = np.asarray([weights.get(target, 0.0) for target in self.targets], dtype=float)
        if not np.isfinite(result).all() or np.min(result) < 0 or not math.isclose(float(result.sum()), 1, abs_tol=1e-10, rel_tol=0):
            raise ValueError("weights must form a finite nonnegative unit simplex")
        return result

    def effect_vector(self, p: dict) -> np.ndarray:
        point = self.point(p)
        return self.upstream._predict(point[None, :])[0] / self.reference_loss - 1.0

    def relative_effect(self, p: dict, target: str) -> float:
        if target not in self.targets:
            raise ValueError("unknown target")
        return float(self.effect_vector(p)[self.targets.index(target)])

    def weighted_effect(self, p: dict, weights: dict) -> float:
        return float(self.effect_vector(p) @ self.weight_vector(weights))

    def gradient(self, p: dict, weights: dict) -> np.ndarray:
        w = self.weight_vector(weights) / self.reference_loss
        return w @ self.upstream.gradient(p)

    def hessian(self, weights: dict) -> np.ndarray:
        w = self.weight_vector(weights) / self.reference_loss
        h = np.zeros((len(self.domains), len(self.domains)))
        for index, (a, b) in enumerate(self.upstream.pairs):
            value = float(w @ self.upstream.gamma[:, index])
            h[a, b] += value
            h[b, a] += value
        return h

    def qa_stats(self, p: dict, policy: str) -> dict:
        if policy not in ("quality_direct", "quality_direct_and_near"):
            raise ValueError("unknown quality policy")
        allowed = {"direct"} if policy == "quality_direct" else {"direct", "near_direct"}
        mask = np.array([self.qa_rows[d]["mapping_type"] in allowed and self.qa_rows[d]["Q_A"] is not None
                         for d in self.domains], dtype=bool)
        quality = np.array([float(self.qa_rows[d]["Q_A"]) if mask[i] else 0.0
                            for i, d in enumerate(self.domains)])
        point = self.point(p)
        covered = float(point @ mask)
        reference_covered = float(self.ref_vector @ mask)
        if reference_covered <= POLICY_TOL:
            raise ValueError("quality policy reference has zero coverage")
        reference_mean = float(self.ref_vector @ quality / reference_covered)
        numerator = float(point @ quality)
        margin = numerator - reference_mean * covered
        return {"policy": policy, "covered_mass": covered, "unmapped_mass": float(point.sum()) - covered,
                "weighted_Q_A_numerator": numerator,
                "mean_Q_A_on_mapped": numerator / covered if covered > POLICY_TOL else None,
                "reference_covered_mass": reference_covered, "reference_mean_Q_A": reference_mean,
                "coverage_margin": covered - reference_covered, "quality_margin": margin,
                "eligible": covered > POLICY_TOL and covered + POLICY_TOL >= reference_covered
                and margin >= -POLICY_TOL, "unknown_Q_A_count": int(sum(row["Q_A"] is None for row in self.qa_rows.values())),
                "Q_A_to_Q_B_mapping": "unidentified"}

    def support(self, p: dict, policy: str = "convex_hull") -> dict:
        point = self.point(p)
        if policy == "algebraic_reference_only":
            if np.max(np.abs(point - self.ref_vector)) > POLICY_TOL:
                raise ValueError("algebraic reference mode accepts p_ref only")
            result = self.upstream.support(p)
            return {**result, "mode": policy, "algebraic_only": not result["in_A4_hull"]}
        if policy == "observed_512":
            distances = np.max(np.abs(self.recipes - point), axis=1)
            index = int(np.argmin(distances))
            if distances[index] > POLICY_TOL:
                raise ValueError("p is not an observed A4 recipe")
            return {"in_A4_hull": True, "observed_index": self.recipe_ids[index],
                    "residual": float(distances[index]), "mode": policy}
        if policy not in ("convex_hull", "quality_direct", "quality_direct_and_near"):
            raise ValueError("unsupported p policy")
        result = self.upstream.support(p)
        if not result["in_A4_hull"]:
            raise ValueError("p outside Q1 A4 convex hull")
        if policy.startswith("quality_"):
            quality = self.qa_stats(p, policy)
            if not quality["eligible"]:
                raise ValueError("p violates Q1 quality policy")
            result["quality"] = quality
        return {**result, "mode": policy}
