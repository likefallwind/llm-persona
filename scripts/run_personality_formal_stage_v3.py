#!/usr/bin/env python3
"""Run a frozen stage; confirmation requires predictions locked before generation."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'artifacts/educational_personality_v2/prospective_formal'


def verify_files(files):
    for name,expected in files.items():
        path=ROOT/name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
            raise ValueError('Frozen dependency differs: '+name)


def validate_stage(stage):
    design=json.loads((BASE/'design_freeze.json').read_text())
    verify_files(design['files'])
    if stage=='confirmation':
        lock_path=BASE/'prediction_lock.json'
        if not lock_path.exists(): raise ValueError('Confirmation forbidden before prediction lock')
        lock=json.loads(lock_path.read_text())
        if lock['status']!='training-fitted predictions frozen before confirmation generation':
            raise ValueError('Prediction lock not ready')
        if lock['design_sha256']!=hashlib.sha256((BASE/'design_freeze.json').read_bytes()).hexdigest():
            raise ValueError('Prediction lock references a different design')
        verify_files(lock['files'])
        audit=json.loads((BASE/'training/generation_audit.json').read_text())
        if audit['status']!='pass': raise ValueError('Training generation audit did not pass')
    return design


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stage',choices=['training','confirmation'],required=True)
    p.add_argument('--check-only',action='store_true')
    args=p.parse_args()
    design=validate_stage(args.stage)
    print(json.dumps({'stage':args.stage,'frozen_inputs_verified':True,'expected_requests':design['planned_generation_requests'][args.stage]}),flush=True)
    if args.check_only: return
    subprocess.run([sys.executable,str(ROOT/'scripts/run_personality_requests_v2.py'),
                    '--manifest',str(BASE/args.stage/'generation_manifest.jsonl'),
                    '--output-dir',str(BASE/args.stage/'run'),
                    '--temperature','0.7','--max-tokens','8192','--timeout','360','--retries','2',
                    '--allow-current-glm53','--schedule','interleaved'],check=True,cwd=ROOT)

if __name__=='__main__': main()
