"""Verify the cleaned PDF and the frozen historical readable-text artifact."""
import argparse
import hashlib
import json
from pathlib import Path

import pdfplumber

ROOT = Path(__file__).resolve().parents[1]
CURRENT_PDF = ROOT / "problem/F/数据说明.pdf"
READABLE = ROOT / "problem/readable/DATA_DESCRIPTION_VISIBLE.md"
MANIFEST = ROOT / "problem/readable/extraction_manifest.json"
CURRENT_SHA = "daa8479decf578ec5f0b165683ac5715fed445ba8c148f386e7b071f5c27dfdc"
CURRENT_BYTES = 13207231
HISTORICAL_SHA = "f5c851bbe4b3d8c9079609c37f2c3b0835244067711d6d761c66adeaa8357835"

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.parse_args()
    if CURRENT_PDF.stat().st_size != CURRENT_BYTES or digest(CURRENT_PDF) != CURRENT_SHA:
        raise ValueError("Current cleaned PDF bytes/hash mismatch.")
    with pdfplumber.open(CURRENT_PDF) as pdf:
        if len(pdf.pages) != 13:
            raise ValueError("Unexpected current PDF page count.")
        chars = sum(len(page.chars) for page in pdf.pages)
        if chars != 0:
            raise ValueError(f"Current PDF unexpectedly contains {chars} extractable text chars.")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("source_sha256") != HISTORICAL_SHA:
        raise ValueError("Historical extraction source hash changed.")
    if manifest.get("current_pdf_sha256") != CURRENT_SHA:
        raise ValueError("Current PDF hash missing from extraction manifest.")
    if digest(READABLE) != manifest.get("output_sha256"):
        raise ValueError("Readable historical extraction hash mismatch.")
    print("PASS: cleaned PDF hash/size/pages/text-layer verified; historical readable artifact frozen.")

if __name__ == "__main__":
    main()
