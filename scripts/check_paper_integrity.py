"""Check the integrated LaTeX source tree without requiring a TeX installation."""
from __future__ import annotations

import re
from pathlib import Path

BASE = Path(__file__).resolve().parents[1] / "paper/latex"


def uncomment(value: str) -> str:
    return "\n".join(re.split(r"(?<!\\)%", line, 1)[0] for line in value.splitlines())


def main() -> None:
    pending = [BASE / "main.tex"]
    seen: set[Path] = set()
    parts: list[str] = []
    missing: list[str] = []
    while pending:
        path = pending.pop()
        if path in seen:
            continue
        if not path.is_file():
            missing.append(str(path.relative_to(BASE)))
            continue
        seen.add(path)
        content = uncomment(path.read_text(encoding="utf-8"))
        parts.append(content)
        pending.extend(BASE / item for item in re.findall(r"\\input\{([^}]+)\}", content))
    if missing:
        raise ValueError(f"missing paper sections: {missing}")
    text = "\n".join(parts)
    paths = re.findall(r"\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}", text)
    for name in paths:
        if not any((BASE / prefix / name).is_file() for prefix in ("", "figures", "figures/Q1", "figures/Q2", "figures/Q3", "figures/Q4")):
            missing.append(name)
    labels = re.findall(r"\\label\{([^}]+)\}", text)
    duplicate = sorted({name for name in labels if labels.count(name) > 1})
    if duplicate:
        raise ValueError(f"duplicate LaTeX labels: {duplicate}")
    unknown_refs = sorted(set(re.findall(r"\\(?:ref|eqref|autoref)\{([^}]+)\}", text)) - set(labels))
    bib = (BASE / "references.bib").read_text(encoding="utf-8")
    bib_keys = set(re.findall(r"@\w+\s*\{\s*([^,\s]+)", bib))
    cited = set().union(*(set(item.split(",")) for item in re.findall(r"\\cite(?:\[[^]]*\])?\{([^}]+)\}", text)))
    unknown_cites = sorted(cited - bib_keys)
    if missing or unknown_refs or unknown_cites:
        raise ValueError(f"paper integrity: missing figures={missing}, unknown refs={unknown_refs}, unknown cites={unknown_cites}")
    required = {f"sections/Q{i}/main.tex" for i in (1, 2, 4)} | {"sections/Q3/theory.tex", "sections/Q3/numerical.tex"}
    present = {path.relative_to(BASE).as_posix() for path in seen}
    if not required.issubset(present):
        raise ValueError(f"question sections absent from total paper: {sorted(required - present)}")
    print(f"PASS: {len(seen)} LaTeX files, {len(paths)} figures, {len(labels)} labels, {len(cited)} citations, Q1-Q4 present")


if __name__ == "__main__":
    main()
