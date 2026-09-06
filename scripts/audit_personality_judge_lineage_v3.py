#!/usr/bin/env python3
"""Trace every blinded coding input to its frozen source and visible generation."""
import argparse
import hashlib
import json
from pathlib import Path
from run_personality_requests_v2 import read_rows,digest,now
from prepare_personality_judging_v2 import judge_messages


def audit(generation_base,judge_base,rubric_path):
    rubric=json.loads(rubric_path.read_text())
    freeze=json.loads((judge_base/'freeze.json').read_text())
    if hashlib.sha256(rubric_path.read_bytes()).hexdigest()!=freeze['rubric_sha256']:
        raise ValueError('Rubric differs from judge freeze')
    if hashlib.sha256((judge_base/'manifest.jsonl').read_bytes()).hexdigest()!=freeze['manifest_sha256']:
        raise ValueError('Judge manifest differs from freeze')
    generation_jobs={r['request_id']:r for r in read_rows(generation_base/'generation_manifest.jsonl')}
    generated={r['request_id']:r for r in read_rows(generation_base/'run/responses.jsonl')}
    scenarios={r['sample_id']:r for r in read_rows(generation_base/'scenarios.jsonl')}
    mapping=read_rows(judge_base/'unblinding.jsonl')
    items={r['blind_id']:r for r in mapping}
    if len(items)!=len(mapping) or len(mapping)!=len(generation_jobs):
        raise ValueError('Unblinding/generation coverage mismatch')
    for blind,item in items.items():
        request=item['sample_id']
        job=generation_jobs[request]
        result=generated[request]
        original=scenarios[job['sample_id']]
        expected_blind=hashlib.sha256(('personality-coding-v2:'+request).encode()).hexdigest()[:20]
        if expected_blind!=blind: raise ValueError('Blinding ID mismatch')
        if result.get('error') or not result.get('response'): raise ValueError('Missing visible generation')
        if digest(item['response'])!=result['response_sha256'] or item['response']!=result['response']:
            raise ValueError('Unblinding answer differs from generation')
        if item['messages']!=job['messages'] or digest(job['messages'])!=result['prompt_sha256']:
            raise ValueError('Unblinding prompt differs from generation')
        for key in ['template','source_family','domain','partition','panel','arm','progress','affect',
                    'target_resolution','teacher_reference','judge_conversation']:
            if item[key]!=original[key]: raise ValueError('Source metadata mismatch: '+key)
        if item['model']!=job['model'] or item['repeat']!=job['repeat']:
            raise ValueError('Generation identity/repetition mismatch')
    jobs=read_rows(judge_base/'manifest.jsonl')
    observed=set()
    for job in jobs:
        item=items[job['blind_id']]
        if judge_messages(item,rubric)!=job['messages']:
            raise ValueError('Frozen coder payload differs from its source mapping')
        pair=(job['blind_id'],job['model'])
        if pair in observed: raise ValueError('Duplicate item/judge assignment')
        observed.add(pair)
    expected={(blind,judge) for blind in items for judge in freeze['judges']}
    if observed!=expected: raise ValueError('Missing or unexpected item/judge assignments')
    inputs=[generation_base/'generation_manifest.jsonl',generation_base/'scenarios.jsonl',
            generation_base/'run/responses.jsonl',judge_base/'manifest.jsonl',judge_base/'unblinding.jsonl',rubric_path]
    report={'status':'pass','checked_at':now(),'visible_generation_items':len(items),'judge_requests':len(jobs),
            'mapping_matches_frozen_source_and_visible_output':True,'coder_payload_reconstructed_exactly':True,
            'input_hashes':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
            'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'limitation':'Input lineage and explicit blinding are verified; this does not prove semantic code accuracy or unguessable model identity.'}
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--generation-base',type=Path,required=True)
    p.add_argument('--judge-base',type=Path,required=True)
    p.add_argument('--rubric',type=Path,default=Path('data/educational_personality_measurement_v2_2.json'))
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    report=audit(args.generation_base,args.judge_base,args.rubric)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ['input_hashes']},indent=2))

if __name__=='__main__': main()
