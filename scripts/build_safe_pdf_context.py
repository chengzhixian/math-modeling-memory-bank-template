"""Derive a readable text copy, rejecting any unreviewed source or filter drift."""
import argparse
import hashlib
import json
from pathlib import Path

import pdfplumber

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'problem/F/数据说明.pdf'
EXPECTED_SHA = 'f5c851bbe4b3d8c9079609c37f2c3b0835244067711d6d761c66adeaa8357835'
OUTPUT = ROOT / 'problem/readable/DATA_DESCRIPTION_VISIBLE.md'
MANIFEST = ROOT / 'problem/readable/extraction_manifest.json'
EXPECTED_ROWS = {3.7, 9.2, 14.7, 20.2, 732.7, 738.7, 744.7, 750.7}


def hidden_char(char, page_number):
    color = char.get('non_stroking_color')
    return (2 <= page_number <= 13
            and abs(char.get('size', 0) - 5) < 1e-6
            and isinstance(color, (tuple, list)) and len(color) == 3
            and all(abs(value - .988) < 1e-6 for value in color)
            and round(char['top'], 2) in EXPECTED_ROWS)


def build():
    source_sha = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    if source_sha != EXPECTED_SHA:
        raise ValueError('Source PDF changed. Re-audit it; do not reuse this filter.')
    chunks = ['# 数据说明可提取正文', '', '[PDF-HIDDEN-TEXT-BLOCK]', '',
              '用户禁止参考原件的隐藏页边文字。本派生文本仅移除已核实的隐藏字符，'
              '其余可提取字符保留；复杂表格、公式和排版仍须核对可见页面。'
              '使用前先读 AI_READING_RULES.md。', '']
    records = []
    forbidden_lines = []
    with pdfplumber.open(SOURCE) as pdf:
        if len(pdf.pages) != 13:
            raise ValueError('Unexpected page count.')
        for number, page in enumerate(pdf.pages, 1):
            removed = [c for c in page.chars if hidden_char(c, number)]
            rows = sorted({round(c['top'], 2) for c in removed})
            expected = [] if number == 1 else sorted(EXPECTED_ROWS)
            if rows != expected:
                raise ValueError(f'Unexpected hidden rows on page {number}.')
            for row in rows:
                chars = sorted((c for c in removed if round(c['top'], 2) == row),
                               key=lambda c: c['x0'])
                forbidden_lines.append(''.join(c['text'] for c in chars))
            filtered = page.filter(lambda obj: obj.get('object_type') != 'char'
                                   or not hidden_char(obj, number))
            expected_chars = [c for c in page.chars if not hidden_char(c, number)]
            if filtered.chars != expected_chars:
                raise ValueError(f'Visible character preservation failed: {number}')
            chunks.extend([f'## 原 PDF 第 {number} 页', '',
                           filtered.extract_text(x_tolerance=3, y_tolerance=3) or '', ''])
            records.append({'page': number, 'original_chars': len(page.chars),
                            'retained_chars': len(filtered.chars),
                            'removed_chars': len(removed), 'removed_rows_top_pt': rows})
    if len(forbidden_lines) != 96 or len(set(forbidden_lines)) != 20:
        raise ValueError('Unexpected hidden text signature count.')
    content = '\n'.join(chunks)
    normalized = ''.join(content.split())
    if any(''.join(line.split()) in normalized for line in forbidden_lines):
        raise ValueError('Known hidden passage survived extraction.')
    raw = content.encode('utf-8')
    manifest = {'schema_version': 1, 'source': 'problem/F/数据说明.pdf',
                'source_sha256': source_sha, 'pdfplumber_version': pdfplumber.__version__,
                'output_sha256': hashlib.sha256(raw).hexdigest(),
                'pages': records, 'removed_line_occurrences': 96,
                'unique_hidden_passages': 20,
                'note': 'Only reviewed hidden characters removed; layout still needs visual review.'}
    return raw, (json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    text, manifest = build()
    if args.check:
        if OUTPUT.read_bytes() != text or MANIFEST.read_bytes() != manifest:
            raise ValueError('Derived reading files differ; regenerate with the recorded environment.')
    else:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_bytes(text)
        MANIFEST.write_bytes(manifest)
    print('PASS: source SHA256; 13 pages; 96 hidden lines removed; other characters preserved.')


if __name__ == '__main__':
    main()
