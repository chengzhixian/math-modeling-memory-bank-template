"""Fast source checks for the collaborative LaTeX draft (not a TeX compiler)."""

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "main.tex"
main_text = MAIN.read_text(encoding="utf-8")

inputs = re.findall(r"\\input\{([^}]+)\}", main_text)
expected = {
    "sections/chm/q1.tex", "sections/chm/q3_numerical.tex",
    "sections/cyj/q2.tex", "sections/cyj/q3_theory.tex",
    "sections/zhh/abstract.tex", "sections/zhh/problem_statement.tex",
    "sections/zhh/assumptions_symbols.tex", "sections/zhh/q4.tex",
    "sections/zhh/discussion.tex",
}
assert set(inputs) == expected, f"Unexpected section manifest: {set(inputs) ^ expected}"

for item in inputs:
    assert (ROOT / item).is_file(), f"Missing input: {item}"


def check_braces(path):
    depth = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        line = re.split(r"(?<!\\)%", line, maxsplit=1)[0]
        for match in re.finditer(r"(?<!\\)[{}]", line):
            depth += 1 if match.group() == "{" else -1
            assert depth >= 0, f"Extra closing brace in {path}"
    assert depth == 0, f"Unbalanced braces in {path}: {depth}"


for path in [MAIN, *(ROOT / item for item in inputs)]:
    check_braces(path)

q1 = (ROOT / "sections/chm/q1.tex").read_text(encoding="utf-8")
figures = re.findall(r"\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}", q1)
assert len(figures) == 5, f"Expected five Q1 figures, got {len(figures)}"
for name in figures:
    assert (ROOT / "figures/chm" / name).is_file(), f"Missing figure: {name}"

labels = re.findall(r"\\label\{([^}]+)\}", q1)
assert len(labels) == len(set(labels)), "Duplicate Q1 labels"
refs = re.findall(r"\\ref\{([^}]+)\}", q1)
assert set(refs) <= set(labels), f"Undefined Q1 references: {set(refs) - set(labels)}"

bib = (ROOT / "references.bib").read_text(encoding="utf-8")
cites = set(re.findall(r"\\cite\{([^}]+)\}", q1))
bibkeys = set(re.findall(r"@\w+\{([^,]+),", bib))
assert cites <= bibkeys, f"Undefined citations: {cites - bibkeys}"

assert (ROOT / "template_source/gmcmthesis.cls").is_file()
assert (ROOT / "gmcmthesis.cls").is_file()
assert (ROOT / "gmcm.bst").is_file()
assert "\\fi % local fix:" in (ROOT / "gmcmthesis.cls").read_text(encoding="utf-8")
print(f"PASS: {len(inputs)} section inputs, {len(figures)} Q1 figures, {len(labels)} Q1 labels, {len(cites)} citations")
