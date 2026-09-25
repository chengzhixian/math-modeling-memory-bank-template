"""Verify published byte hashes, including Git's staged/committed objects.
python src/zhh/verify_q4_release.py [--index | --head]
"""
import argparse
import hashlib
import json
import subprocess
from q4_complete import ROOT, OUT


def main():
    parser=argparse.ArgumentParser()
    group=parser.add_mutually_exclusive_group()
    group.add_argument('--index',action='store_true')
    group.add_argument('--head',action='store_true')
    args=parser.parse_args()
    def read(path):
        if args.index or args.head:
            prefix=':' if args.index else 'HEAD:'
            return subprocess.check_output(['git','-C',str(ROOT),'show',prefix+path])
        return (ROOT/path).read_bytes()
    model=json.loads(read('outputs/zhh/q4_v2/manifest.json'))
    answer=json.loads(read('outputs/zhh/answer_manifest.json'))
    entries={**model['input_sha256'],**model['canonical_output_sha256'],**answer['files_sha256']}
    entries.update({'outputs/zhh/q4_v2/'+p:h for p,h in model['output_sha256'].items()})
    entries['outputs/zhh/q4_v2/manifest.json']=answer['numerical_manifest_sha256']
    for path,digest in entries.items():
        actual=hashlib.sha256(read(path)).hexdigest()
        if actual!=digest:raise ValueError(f'hash mismatch: {path} {actual} != {digest}')
    print(f'PASS: {len(entries)} input/code/output/answer byte hashes in '+('Git index' if args.index else 'Git HEAD' if args.head else 'working tree'))


if __name__=='__main__':main()
