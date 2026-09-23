"""Versioned, read-only Q1 producer interface for downstream consumers."""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import math


VERSION = "chm.q1.v1"
MANIFEST = Path("interfaces/chm/q1_interface_v1.json")
FILES = {
    "quality": "outputs/chm/domain_quality.csv",
    "mapping": "outputs/chm/domain_mapping.csv",
    "coefficients": "outputs/chm/local_recheck_v1/mixture_effect_ridge_v0.csv",
    "reference": "outputs/chm/local_recheck_v1/mixture_reference_v0.csv",
    "scale": "outputs/chm/local_recheck_v1/mixture_scale_transfer_v0_manifest.json",
    "validation": "outputs/chm/local_recheck_v1/q1_regmix_ridge_domainwise_metrics.csv",
}


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _csv(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def build_manifest(root):
    root = Path(root)
    files = {}
    for key, relative in FILES.items():
        path = root / relative
        files[key] = {"path": relative, "sha256": _sha256(path),
                      "rows": len(_csv(path)) if path.suffix == ".csv" else None}
    return {"schema_version": VERSION, "producer": "chm",
            "status": "producer_validated_A_side_ready_B_bridge_unidentified",
            "files": files, "quality_coordinate": "A_native_Q_z",
            "mixture_effect_unit": "A_target_cross_entropy_delta",
            "scale_N_unit": "parameters"}


class Q1Interface:
    def __init__(self, root):
        root = Path(root)
        manifest = json.loads((root / MANIFEST).read_text(encoding="utf-8"))
        if (manifest.get("schema_version") != VERSION
                or manifest.get("status") != "producer_validated_A_side_ready_B_bridge_unidentified"
                or manifest.get("quality_coordinate") != "A_native_Q_z"
                or manifest.get("mixture_effect_unit") != "A_target_cross_entropy_delta"
                or manifest.get("scale_N_unit") != "parameters"
                or set(manifest.get("files", {})) != set(FILES)):
            raise ValueError("Unexpected Q1 interface version or file set")
        for key, expected in FILES.items():
            item = manifest["files"][key]
            path = root / expected
            if item["path"] != expected or _sha256(path) != item["sha256"]:
                raise ValueError(f"Q1 interface file identity mismatch: {key}")
            if path.suffix == ".csv" and len(_csv(path)) != item["rows"]:
                raise ValueError(f"Q1 interface row count mismatch: {key}")
        self.manifest = manifest
        self.quality_rows = {r["quality_domain"]: r for r in _csv(root / FILES["quality"])
                             if r["dataset_scope"] == "sample"}
        self.mapping_rows = {r["mixture_domain"]: r for r in _csv(root / FILES["mapping"])}
        self.coefficients = {r["target"]: r for r in _csv(root / FILES["coefficients"])}
        self.reference = {r["mixture_domain"]: float(r["p_ref"])
                          for r in _csv(root / FILES["reference"])}
        self.scale = json.loads((root / FILES["scale"]).read_text(encoding="utf-8"))
        if len(self.quality_rows) != 7 or len(self.mapping_rows) != 17 or len(self.coefficients) != 13:
            raise ValueError("Unexpected Q1 quality, mapping or target count")
        kinds = [row["mapping_type"] for row in self.mapping_rows.values()]
        if (kinds.count("direct"), kinds.count("near_direct"), kinds.count("inferred")) != (3, 3, 11):
            raise ValueError("Unexpected Q1 mapping types")
        if set(self.reference) != set(self.mapping_rows) or not math.isclose(sum(self.reference.values()), 1, abs_tol=1e-6):
            raise ValueError("Invalid 17-domain reference mixture")
        for domain, row in self.quality_rows.items():
            lo, point, hi = (float(row[key]) for key in ("uncertainty_low", "Q", "uncertainty_high"))
            if not all(map(math.isfinite, (lo, point, hi))) or not lo <= point <= hi:
                raise ValueError(f"Invalid Q or conditional interval for {domain}")
        for target, row in self.coefficients.items():
            coeff = [float(row[domain]) for domain in self.reference]
            if not all(map(math.isfinite, coeff)) or not math.isclose(sum(coeff), 0, abs_tol=1e-6):
                raise ValueError(f"Nonfinite coefficient for {target}")

    def quality(self, domain):
        """Return A-native descriptive domain Q; never a B-native Q_score."""
        row = self.quality_rows[domain]
        return {"domain": domain, "Q_z_median": float(row["Q"]),
                "conditional_95": [float(row["uncertainty_low"]), float(row["uncertainty_high"])],
                "n_rows": int(row["n_rows"]), "coordinate": "A_native_Q_z"}

    def mapped_quality(self, mixture_domain):
        """Return observed/proxy A-side Q; inferred domains remain null."""
        row = self.mapping_rows[mixture_domain]
        kind = row["mapping_type"]
        if kind not in {"direct", "near_direct", "inferred"}:
            raise ValueError(f"Unknown mapping type: {kind}")
        return {"mixture_domain": mixture_domain, "mapping_type": kind,
                "quality_domain": None if kind == "inferred" else row["quality_domain"],
                "quality": None if kind == "inferred" else self.quality(row["quality_domain"])}

    def relative_effect(self, mixture, target, n_params=1_000_000, eta=None):
        """Centered A-target loss delta; no B1 val_loss or absolute loss."""
        if set(mixture) != set(self.reference):
            raise ValueError("Mixture must contain exactly the 17 named domains")
        values = {key: float(value) for key, value in mixture.items()}
        if any(not math.isfinite(v) or v < 0 for v in values.values()):
            raise ValueError("Mixture weights must be finite and nonnegative")
        if not math.isclose(sum(values.values()), 1.0, abs_tol=1e-6):
            raise ValueError("Mixture weights must sum to one; no silent normalization")
        if target not in self.coefficients:
            raise ValueError(f"Unknown target: {target}")
        n_params = float(n_params)
        if not math.isfinite(n_params) or n_params <= 0:
            raise ValueError("n_params must be a positive finite parameter count")
        eta = float(self.scale["pooled_eta"] if eta is None else eta)
        if not math.isfinite(eta):
            raise ValueError("eta must be finite")
        row = self.coefficients[target]
        delta_1m = sum(float(row[d]) * (values[d] - self.reference[d]) for d in self.reference)
        factor = (n_params / 1_000_000) ** (-eta)
        if not math.isfinite(factor * delta_1m):
            raise ValueError("Nonfinite scaled mixture effect")
        return {"target": target, "delta_target_loss": delta_1m * factor,
                "n_params": n_params, "eta": eta, "scale_factor": factor,
                "scale_status": "observed_model_scale" if n_params in (1e6, 60e6, 1e9) else "extrapolated_model_scale",
                "mixture_support_status": "not_checked",
                "loss_coordinate": "A_target_cross_entropy_delta",
                "bridge_to_B1_val_loss": "unidentified"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--build-manifest", action="store_true")
    args = parser.parse_args()
    if args.build_manifest:
        path = args.root / MANIFEST
        path.write_text(json.dumps(build_manifest(args.root), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    interface = Q1Interface(args.root)
    print(f"{interface.manifest['schema_version']}: 7 Q domains, 17 mixture domains, 13 loss targets; hashes verified")


if __name__ == "__main__":
    main()
