"""Read one preselected A1 original text locally without exporting it to Git."""
import argparse
import hashlib
import json
import lzma

import pandas as pd
from q1_conflict_aware import ROOT
from q1_quality_analysis import resolve_default_paths


def read_selected(domain, sample_id, max_chars=600):
    index = pd.read_csv(ROOT / "outputs/chm/q1_conflict_resolution_v1/selected_cases_index.csv")
    hit = index[(index._source_domain == domain) & (index._id.astype(str) == sample_id)]
    if len(hit) != 1:
        raise ValueError("case must be one preselected (domain,id) pair")
    row = hit.iloc[0]
    a1, _, _ = resolve_default_paths()
    with lzma.open(ROOT / a1, "rt", encoding="utf-8") as source:
        for line_no, line in enumerate(source, 1):
            if line_no != int(row.source_line):
                continue
            obj = json.loads(line)
            if obj.get("_source_domain") != domain or str(obj.get("id")) != sample_id:
                raise ValueError("stored source line does not match selected identity")
            content = obj.get("content")
            if not isinstance(content, str) or hashlib.sha256(content.encode()).hexdigest() != row.content_sha256:
                raise ValueError("source text missing or content hash changed")
            return dict(domain=domain, id=sample_id, content_chars=len(content),
                        content_sha256=row.content_sha256, excerpt=content[:max_chars])
    raise ValueError("source line not found")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("domain")
    parser.add_argument("id")
    parser.add_argument("--max-chars", type=int, default=600)
    args = parser.parse_args()
    if not 1 <= args.max_chars <= 2000:
        parser.error("max-chars must be between 1 and 2000")
    print(json.dumps(read_selected(args.domain, args.id, args.max_chars), ensure_ascii=True, indent=2))
