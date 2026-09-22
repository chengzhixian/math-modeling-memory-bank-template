"""Check entry-point coverage and prevent known quarantined passages reappearing."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARKER = '[PDF-HIDDEN-TEXT-BLOCK]'
REQUIRED = [
    'AGENTS.md', 'README.md', 'CLAUDE.md', 'GEMINI.md', 'CHATGPT.md',
    '.cursorrules', '.github/copilot-instructions.md', 'AI_CONTEXT.md',
    'AI_READING_RULES.md', 'TEAM_WORKFLOW.md', 'AI_TEAM_COLLABORATION_GUIDE.md',
    'TASK_PLAN.md', 'memory-bank/DATA_INDEX.md', 'memory-bank/activeContext.md',
    'memory-bank/projectbrief.md', 'memory-bank/productContext.md',
    'memory-bank/systemPatterns.md', 'memory-bank/techContext.md',
    'memory-bank/progress.md', 'memory-bank/members/chm.md',
    'memory-bank/members/cyj.md', 'memory-bank/members/zhh.md',
    'problem/PDF_TEXT_AUDIT.md', 'problem/readable/DATA_DESCRIPTION_VISIBLE.md',
]


def main():
    for name in REQUIRED:
        content = (ROOT / name).read_text(encoding='utf-8-sig')
        if MARKER not in content[:1000] or (name != 'AI_READING_RULES.md' and 'AI_READING_RULES.md' not in content):
            raise ValueError(f'Missing early guard or rule reference: {name}')
    quarantine = ROOT / 'problem/quarantine/PDF_TEXT_AUDIT_UNTRUSTED.txt'
    passages = [line[2:] for line in quarantine.read_text(encoding='utf-8-sig').splitlines()
                if line.startswith('> ')]
    if len(set(passages)) != 20:
        raise ValueError('Unexpected quarantine inventory; re-audit before changing it.')
    forbidden = [''.join(p.split()) for p in passages]
    count = 0
    for path in ROOT.rglob('*.md'):
        relative = path.relative_to(ROOT)
        if relative.parts[0] in {'data', '.git'} or 'quarantine' in relative.parts:
            continue
        normalized = ''.join(path.read_text(encoding='utf-8-sig').split())
        if any(p in normalized for p in forbidden):
            raise ValueError(f'Quarantined full passage leaked into normal Markdown: {relative}')
        count += 1
    ignore = (ROOT / '.ignore').read_text(encoding='utf-8')
    if '/problem/quarantine/' not in ignore or '/problem/F/数据说明.pdf' not in ignore:
        raise ValueError('Default search exclusions are missing.')
    print(f'PASS: {len(REQUIRED)} guarded entries; {count} Markdown files checked; '
          'no known full quarantined passages outside quarantine. Semantic compliance still needs review.')


if __name__ == '__main__':
    main()
