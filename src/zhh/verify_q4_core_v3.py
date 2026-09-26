"""Verify v3 working-tree, staged or committed release bytes."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
REL='outputs/Q4/'


def main():
    parser=argparse.ArgumentParser()
    group=parser.add_mutually_exclusive_group()
    group.add_argument('--head',action='store_true')
    group.add_argument('--index',action='store_true')
    args=parser.parse_args()
    def read(path):
        if args.head or args.index:
            return subprocess.check_output(['git','-C',str(ROOT),'show',('HEAD:' if args.head else ':')+path])
        return (ROOT/path).read_bytes()
    manifest=json.loads(read(REL+'manifest.json'))
    entries=dict(manifest['input_sha256'])
    entries.update({REL+p:d for p,d in manifest['output_sha256'].items()})
    for path,digest in entries.items():
        if hashlib.sha256(read(path)).hexdigest()!=digest:
            raise ValueError('Q4 v3 release hash mismatch: '+path)
    print(f'PASS: {len(entries)} v3 input/code/output hashes in '+('Git HEAD' if args.head else 'Git index' if args.index else 'working tree'))


if __name__=='__main__':
    main()
