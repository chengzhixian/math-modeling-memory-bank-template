"""Versioned, read-only Q1 producer interface.

v1.3 deliberately exposes only quantities identifiable from Attachment A:
A-side composite quality proxies, the 17-domain reference composition,
13 target-specific 1M Ridge contrasts, and held-out ranking evidence.

No N/D-dependent mixture scale factor is supplied. Historical eta-based
calibration files remain in the repository for audit only and are not part of
this interface.
"""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import math


VERSION = "chm.q1.v1.3"
MANIFEST = Path("interfaces/chm/q1_interface_v1_3.json")
STATUS = "producer_validated_A_side_ready_scale_transfer_removed_B_bridge_unidentified"
FILES = {
    "quality": "outputs/chm/domain_quality.csv",
    "mapping": "outputs/chm/domain_mapping.csv",
    "coefficients": "outputs/chm/local_recheck_v1/mixture_effect_ridge_v0.csv",
    "reference": "outputs/chm/local_recheck_v1/mixture_reference_v0.csv",
    "validation": "outputs/chm/local_recheck_v1/q1_regmix_ridge_domainwise_metrics.csv",
}


def _normalized_text_bytes(path):
    text = Path(path).read_text(encoding="utf-8-sig")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text.encode("utf-8")


def _sha256(path):
    return hashlib.sha256(_normalized_text_bytes(path)).hexdigest()


def _csv(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def build_manifest(root):
    root = Path(root)
    files = {}
    for key, relative in FILES.items():
        path = root / relative
        files[key] = {
            "path": relative,
            "sha256": _sha256(path),
            "rows": len(_csv(path)) if path.suffix == ".csv" else None,
        }
    return {
        "schema_version": VERSION,
        "producer": "chm",
        "status": STATUS,
        "hash_mode": "sha256_utf8_lf_normalized",
        "files": files,
        "quality_coordinate": "A_composite_quality_proxy_z",
        "mixture_effect_coordinate": "A4_A5_1M_target_cross_entropy_contrast",
        "scale_transfer_status": "not_identified_from_attachment_A",
        "compatibility": {
            "predecessor": "chm.q1.v1.2",
            "scientific_values_changed": True,
            "change": (
                "recompute A-side Q from all 22 signals with global Spearman signs; "
                "retain existing 1M mixture contrast and ranking interface"
            ),
        },
    }


class Q1Interface:
    def __init__(self, root):
        root = Path(root)
        manifest = json.loads((root / MANIFEST).read_text(encoding="utf-8"))
        if (
            manifest.get("schema_version") != VERSION
            or manifest.get("status") != STATUS
            or manifest.get("hash_mode") != "sha256_utf8_lf_normalized"
            or manifest.get("quality_coordinate") != "A_composite_quality_proxy_z"
            or manifest.get("mixture_effect_coordinate")
            != "A4_A5_1M_target_cross_entropy_contrast"
            or manifest.get("scale_transfer_status") != "not_identified_from_attachment_A"
            or set(manifest.get("files", {})) != set(FILES)
        ):
            raise ValueError("Unexpected Q1 interface version or file set")

        for key, expected in FILES.items():
            item = manifest["files"][key]
            path = root / expected
            if item["path"] != expected or _sha256(path) != item["sha256"]:
                raise ValueError(f"Q1 interface file identity mismatch: {key}")
            if path.suffix == ".csv" and len(_csv(path)) != item["rows"]:
                raise ValueError(f"Q1 interface row count mismatch: {key}")

        self.manifest = manifest
        self.quality_rows = {
            r["quality_domain"]: r
            for r in _csv(root / FILES["quality"])
            if r["dataset_scope"] == "sample"
        }
        self.mapping_rows = {
            r["mixture_domain"]: r for r in _csv(root / FILES["mapping"])
        }
        self.coefficients = {
            r["target"]: r for r in _csv(root / FILES["coefficients"])
        }
        self.reference = {
            r["mixture_domain"]: float(r["p_ref"])
            for r in _csv(root / FILES["reference"])
        }
        self.validation_rows = {
            r["target"]: r for r in _csv(root / FILES["validation"])
        }

        if (
            len(self.quality_rows) != 7
            or len(self.mapping_rows) != 17
            or len(self.coefficients) != 13
            or len(self.validation_rows) != 13
        ):
            raise ValueError("Unexpected Q1 quality, mapping or target count")

        kinds = [row["mapping_type"] for row in self.mapping_rows.values()]
        if (
            kinds.count("direct"),
            kinds.count("near_direct"),
            kinds.count("inferred"),
        ) != (3, 3, 11):
            raise ValueError("Unexpected Q1 mapping types")

        if set(self.reference) != set(self.mapping_rows) or not math.isclose(
            sum(self.reference.values()), 1, abs_tol=1e-6
        ):
            raise ValueError("Invalid 17-domain reference mixture")

        for domain, row in self.quality_rows.items():
            lo, point, hi = (
                float(row[key])
                for key in ("uncertainty_low", "Q", "uncertainty_high")
            )
            if not all(map(math.isfinite, (lo, point, hi))) or not lo <= point <= hi:
                raise ValueError(f"Invalid Q or conditional interval for {domain}")

        for target, row in self.coefficients.items():
            coeff = [float(row[domain]) for domain in self.reference]
            if not all(map(math.isfinite, coeff)) or not math.isclose(
                sum(coeff), 0, abs_tol=1e-6
            ):
                raise ValueError(f"Invalid zero-sum coefficient vector for {target}")

    def quality(self, domain):
        """Return A-side descriptive composite quality proxy, never B Q_score."""
        row = self.quality_rows[domain]
        return {
            "domain": domain,
            "Q_A_median": float(row["Q"]),
            "conditional_95": [
                float(row["uncertainty_low"]),
                float(row["uncertainty_high"]),
            ],
            "n_rows": int(row["n_rows"]),
            "coordinate": "A_composite_quality_proxy_z",
            "interpretation": "descriptive_composite_proxy_not_ground_truth",
            "B_Q_score_mapping": "unidentified",
            "direct_B_predictor_input_allowed": False,
        }

    def mapped_quality(self, mixture_domain):
        """Return observed/proxy A-side Q; inferred domains remain null."""
        row = self.mapping_rows[mixture_domain]
        kind = row["mapping_type"]
        if kind not in {"direct", "near_direct", "inferred"}:
            raise ValueError(f"Unknown mapping type: {kind}")
        return {
            "mixture_domain": mixture_domain,
            "mapping_type": kind,
            "quality_domain": None if kind == "inferred" else row["quality_domain"],
            "quality": (
                None
                if kind == "inferred"
                else self.quality(row["quality_domain"])
            ),
        }

    def relative_effect(self, mixture, target):
        """Return the centered A4+A5 1M target-loss contrast m_k(p).

        This method intentionally has no N or D argument. Attachment A does not
        identify a continuous cross-scale amplitude transfer. Downstream code
        must not silently attach an eta factor to this producer output.
        """
        if set(mixture) != set(self.reference):
            raise ValueError("Mixture must contain exactly the 17 named domains")
        values = {key: float(value) for key, value in mixture.items()}
        if any(not math.isfinite(v) or v < 0 for v in values.values()):
            raise ValueError("Mixture weights must be finite and nonnegative")
        if not math.isclose(sum(values.values()), 1.0, abs_tol=1e-6):
            raise ValueError("Mixture weights must sum to one; no silent normalization")
        if target not in self.coefficients:
            raise ValueError(f"Unknown target: {target}")

        row = self.coefficients[target]
        delta_1m = sum(
            float(row[d]) * (values[d] - self.reference[d])
            for d in self.reference
        )
        if not math.isfinite(delta_1m):
            raise ValueError("Nonfinite centered mixture effect")

        return {
            "target": target,
            "delta_target_loss_1m": delta_1m,
            "reference": "A4_mean_normalized_composition",
            "loss_coordinate": "A4_A5_1M_target_cross_entropy_contrast",
            "cross_scale_transfer": "not_identified_from_attachment_A",
            "bridge_to_B1_val_loss": "unidentified",
            "direct_B1_addition_allowed": False,
        }

    def effect_vector(self, mixture):
        """Return all 13 centered 1M target-loss contrasts for one mixture."""
        return {
            "schema_version": VERSION,
            "loss_coordinate": "A4_A5_1M_target_cross_entropy_contrast",
            "cross_scale_transfer": "not_identified_from_attachment_A",
            "effects": {
                target: self.relative_effect(mixture, target)["delta_target_loss_1m"]
                for target in self.coefficients
            },
        }

    def interaction_matrix(self):
        """Return the 13 x 17 zero-sum Ridge coefficient matrix B."""
        return {
            "targets": list(self.coefficients),
            "domains": list(self.reference),
            "matrix": [
                [float(self.coefficients[target][domain]) for domain in self.reference]
                for target in self.coefficients
            ],
            "coefficient_interpretation": (
                "simplex contrast coefficients; reallocation effects use beta_j-beta_r"
            ),
        }

    def ranking_validation(self, target):
        """Return held-out ranking evidence for the frozen 1M Ridge surrogate."""
        if target not in self.validation_rows:
            raise ValueError(f"Unknown target: {target}")
        row = self.validation_rows[target]
        return {
            "target": target,
            "test_1m_spearman": float(row["test_1m_spearman"]),
            "test_60m_spearman": float(row["test_60m_spearman"]),
            "test_1B_spearman": float(row["test_1B_spearman"]),
            "est_10B_spearman": float(row["est_10B_spearman"]),
            "est_70B_spearman": float(row["est_70B_spearman"]),
            "observed_sets": ["test_1m", "test_60m", "test_1B"],
            "estimated_sets": ["est_10B", "est_70B"],
            "interpretation": "rank_transfer_evidence_not_absolute_scale_calibration",
        }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--build-manifest", action="store_true")
    args = parser.parse_args()

    if args.build_manifest:
        path = args.root / MANIFEST
        path.write_text(
            json.dumps(
                build_manifest(args.root), ensure_ascii=False, indent=2
            )
            + "\n",
            encoding="utf-8",
        )

    interface = Q1Interface(args.root)
    print(
        f"{interface.manifest['schema_version']}: "
        "7 Q domains, 17 mixture domains, 13 loss targets; "
        "1M contrasts + ranking evidence; no scale transfer"
    )


if __name__ == "__main__":
    main()
