"""Publish the user-authorized interaction model as the default Q1 producer."""
from pathlib import Path
import hashlib
import json
import shutil
from q1_interface_v1_3 import Q1Interface as FrozenQ1

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/chm/q1_v2"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def dump(path, obj):
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def release():
    old = FrozenQ1(ROOT)
    source = ROOT / "outputs/chm/q1_exports/q1_interaction_bundle_v1"
    manifest = json.loads((source / "interaction_manifest.json").read_text(encoding="utf-8"))
    for name, sha in manifest["files_sha256"].items():
        if hashlib.sha256((source / name).read_bytes()).hexdigest() != sha:
            raise ValueError(f"interaction source identity failed: {name}")
    OUT.mkdir(parents=True, exist_ok=True)
    files = {}
    sources = {
        "model": source / "interaction_coefficients_13_targets.json",
        "features": source / "interaction_feature_definition.json",
        "recipes": ROOT / "outputs/chm/q1_exports/q1_q2_bundle_v1/recipes_512.csv",
        "quality": ROOT / "outputs/chm/domain_quality.csv",
        "mapping": ROOT / "outputs/chm/domain_mapping.csv",
        "validation": ROOT / "outputs/chm/q1_mixture_comparison_v1/targetwise_validation.csv",
        "nested_cv": ROOT / "outputs/chm/q1_nested_model_comparison_v1/targetwise_oof.csv",
        "fold_stability": source / "interaction_fold_stability.csv",
    }
    for key, path in sources.items():
        destination = OUT / path.name
        if key == "model":
            data = json.loads(path.read_text(encoding="utf-8"))
            data.update(schema_version="chm.q1.interaction_13_targets.v2", status="USER_AUTHORIZED_PRIMARY_MODEL")
            dump(destination, data)
        else:
            shutil.copyfile(path, destination)
        files[key] = {"path": destination.relative_to(ROOT).as_posix(), "sha256": digest(destination)}
    qa = json.loads((ROOT / "outputs/chm/q1_third_part_review/qa_mapping_primary_candidate.json").read_text(encoding="utf-8"))
    qa.update(schema_version="chm.q1.quality_mapping.v2", status="PRIMARY_A1_SAMPLE_EXTENDED_SENSITIVITY")
    for row in qa["rows"]:
        expected = old.mapped_quality(row["mixture_domain"])["quality"]
        assert row["Q_A"] == (None if expected is None else expected["Q_A_median"])
    dump(OUT / "qa_mapping.json", qa)
    files["qa_mapping"] = {"path": "outputs/chm/q1_v2/qa_mapping.json", "sha256": digest(OUT / "qa_mapping.json")}
    release = {
        "schema_version": "chm.q1.v2.0", "producer": "chm",
        "status": "USER_AUTHORIZED_PRIMARY_A_SIDE_MODEL", "hash_mode": "sha256_utf8_lf", "files": files,
        "model_family": "17_main_plus_10_pair_products_targetwise_L2_regularized",
        "predecessor": "chm.q1.v1.3", "breaking_change": True,
        "normalization": "delta divided by each interaction model's positive fitted reference Loss",
        "default_support": "convex_hull_of_normalized_A4_512_recipes",
        "quality_coordinate": "A1_sample_composite_proxy; extended_only_sensitivity; 11_unknown_null",
        "cross_scale_transfer": "unidentified", "A_B_bridge": "unidentified",
        "ready_for_Q3_empirical_absolute_loss": False,
        "authorization": "user explicitly requested primary-model replacement on 2026-09-25",
        "source_interaction_manifest_sha256": digest(source / "interaction_manifest.json"),
        "reproduce": "python -B src/chm/release_q1_v2.py",
    }
    dump(ROOT / "interfaces/chm/q1_interface_v2.json", release)
    return release


if __name__ == "__main__":
    print(json.dumps(release(), ensure_ascii=False, indent=2))
