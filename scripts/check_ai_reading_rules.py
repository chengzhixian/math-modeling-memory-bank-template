"""Check AI entry-point coverage and current hidden-text safety state."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARKER = "[PDF-HIDDEN-TEXT-BLOCK]"
REQUIRED = [
    "AGENTS.md", "README.md", "CLAUDE.md", "GEMINI.md", "CHATGPT.md",
    ".cursorrules", ".github/copilot-instructions.md", "AI_CONTEXT.md",
    "AI_READING_RULES.md", "TEAM_WORKFLOW.md", "AI_TEAM_COLLABORATION_GUIDE.md",
    "TASK_PLAN.md", "memory-bank/DATA_INDEX.md", "memory-bank/activeContext.md",
    "memory-bank/projectbrief.md", "memory-bank/productContext.md",
    "memory-bank/systemPatterns.md", "memory-bank/techContext.md",
    "memory-bank/progress.md", "memory-bank/members/chm.md",
    "memory-bank/members/cyj.md", "memory-bank/members/zhh.md",
    "problem/PDF_TEXT_AUDIT.md", "problem/readable/DATA_DESCRIPTION_VISIBLE.md",
]

def main():
    for name in REQUIRED:
        content = (ROOT / name).read_text(encoding="utf-8-sig")
        if MARKER not in content[:2000]:
            raise ValueError(f"Missing early guard marker: {name}")
    rules = (ROOT / "AI_READING_RULES.md").read_text(encoding="utf-8-sig")
    for sha in ["fd55147", "80c7ea5", "6086964", "58f4f0a", "55743ca"]:
        if sha not in rules:
            raise ValueError(f"Missing required history marker in AI_READING_RULES.md: {sha}")
    quarantine = (ROOT / "problem/quarantine/PDF_TEXT_AUDIT_UNTRUSTED.txt").read_text(encoding="utf-8-sig")
    if any(line.startswith("> ") for line in quarantine.splitlines()):
        raise ValueError("Quarantine still contains quoted hidden-text passages.")
    ignore = (ROOT / ".ignore").read_text(encoding="utf-8-sig")
    if "/problem/quarantine/" not in ignore or "/problem/F/数据说明.pdf" not in ignore:
        raise ValueError("Default search exclusions are missing.")
    print(f"PASS: {len(REQUIRED)} guarded entries; Gemini history marked invalid; quarantine metadata-only.")

if __name__ == "__main__":
    main()
