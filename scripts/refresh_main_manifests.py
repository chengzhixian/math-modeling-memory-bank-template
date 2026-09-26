"""Write or verify main's question-oriented integration inventories.

Frozen member release manifests remain untouched. Run with --write after a
reviewed code/data change; without the flag this is a read-only release gate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "Q1": "integration/chm-q1-clean-20260923@c052b6918c3f77a2285622521d8abb1b429513be",
    "Q2": "team/cyj-scaling@fd2dbb3b2002983430329cdb2ec6a275c2eed4f6",
    "Q3": "integration/chm-q1-clean-20260923@c052b6918c3f77a2285622521d8abb1b429513be",
    "Q4": "team/zhh-frontier@ee23b200e9de7f78477d945b186233741bd3b8fd",
}
Q1_CODE = (
    "q1_quality_analysis.py", "q1_quality_delivery.py", "q1_quality_sensitivity.py",
    "q1_quality_robustness_final.py", "q1_conflict_aware.py", "q1_conflict_replication.py",
    "q1_conflict_resolution.py", "q1_regmix_domainwise.py", "q1_mixture_interface.py",
    "q1_mixture_final_audit.py", "reproduce_q1_v2_core.py",
    "q1_mixture_nested_model_comparison.py", "q1_mixture_comparative_validation.py",
    "q1_interface.py", "q1_interface_v2.py", "q1_mixture_decision_v2.py",
    "q1_hull_bounds_v2.py", "audit_q1_v2_signoff.py", "q1_v2_estimated_stress.py",
    "q1_v2_refit_stability.py", "q1_ablation.py", "q1_paper_figures.py", "q1_figures.py",
    "plot_q1_interaction.py", "plot_q1_v2_final.py", "test_q1_v2.py",
    "test_q1_conflict_resolution.py", "test_q1_quality_analysis.py",
)
Q2_EXCLUDE = {"build_v8_fixtures.py", "verify_q2_v8_release.py"}
PAPER = {
    "Q1": ("paper/latex/sections/Q1/main.tex",),
    "Q2": ("paper/latex/sections/Q2/main.tex",),
    "Q3": ("paper/latex/sections/Q3/theory.tex", "paper/latex/sections/Q3/numerical.tex"),
    "Q4": ("paper/latex/sections/Q4/main.tex",),
}
SOURCE_MANIFEST = {
    "Q1": "interfaces/Q1/q1_interface_v2.json",
    "Q2": "outputs/Q2/upstream_manifest.json",
    "Q3": "outputs/Q3/upstream_manifest.json",
    "Q4": "experiments/Q4/source_manifest_v3.json",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_or_check(path: Path, value: dict, write: bool) -> None:
    encoded = (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")
    if write:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(encoded)
    elif path.read_bytes() != encoded:
        raise ValueError(f"main integration inventory drift: {path.relative_to(ROOT)}")


def code_manifest(question: str, paths: list[Path], write: bool) -> None:
    expected = {p.relative_to(ROOT).as_posix(): sha(p) for p in paths}
    record = {"schema": f"main.{question.lower()}.integrated.code.v1",
              "source_release": SOURCES[question], "sha256": expected}
    write_or_check(ROOT / f"interfaces/{question}/code_manifest.json", record, write)


def main(write: bool = False) -> None:
    q1 = [ROOT / "src/chm" / name for name in Q1_CODE]
    q2 = sorted(p for p in (ROOT / "src/cyj").glob("*.py") if p.name not in Q2_EXCLUDE)
    q2 += sorted((ROOT / "src/cyj/tests").glob("test_ndqp_v8.py"))
    for question, paths in (("Q1", q1), ("Q2", q2)):
        if any(not p.is_file() for p in paths):
            raise ValueError(f"missing {question} source file")
        code_manifest(question, paths, write)

    for question in SOURCES:
        base = ROOT / "outputs" / question
        files = sorted(p for p in base.rglob("*") if p.is_file() and p.name != "curated_manifest.json")
        if question == "Q4":
            allowed = {"bridge_sample.csv", "c4_resource_audit.csv", "leaderboard_all_versions.csv",
                       "leaderboard_sample.csv", "manifest.json", "upstream_q3_fixed_policy_grid.csv",
                       "upstream_q3_manifest.json"}
            files = [p for p in files if p.parent != base / "prepared" or p.name in allowed]
        recorded = {p.relative_to(base).as_posix(): sha(p) for p in files}
        interface = ROOT / "interfaces" / question
        interfaces = {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(interface.rglob("*")) if p.is_file()} if interface.is_dir() else {}
        record = {
            "schema_version": "main.question_integration.v2",
            "question": question,
            "source_release": SOURCES[question],
            "source_manifest_path": SOURCE_MANIFEST[question],
            "source_manifest_sha256": sha(ROOT / SOURCE_MANIFEST[question]),
            "scope": "current main answer, production evidence, interface and paper; reproducible process tables excluded",
            "sha256": recorded,
            "interface_sha256": interfaces,
            "paper_sha256": {name: sha(ROOT / name) for name in PAPER[question]},
        }
        write_or_check(base / "curated_manifest.json", record, write)
    print("PASS: Q1-Q4 main integration inventories" if not write else "WROTE: Q1-Q4 main integration inventories")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    main(parser.parse_args().write)
