#!/usr/bin/env python3
"""Validate two-provider synthetic-content review and preserve all objections."""
import argparse
import hashlib
import json
import re
from pathlib import Path
from run_personality_requests_v2 import digest,read_rows
from analyze_personality_coding_v2 import unique_keys

CHECKS=['question_valid','reference_correct','incorrect_attempt_has_error','partial_work_correct','partial_work_incomplete']

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base',type=Path,required=True)
    a=p.parse_args()
    freeze=json.loads((a.base/'freeze.json').read_text())
    if hashlib.sha256((a.base/'manifest.jsonl').read_bytes()).hexdigest()!=freeze['manifest_sha256']:
        raise ValueError('Content review manifest changed')
    responses={r['request_id']:r for r in read_rows(a.base/'run/responses.jsonl')}
    results=[]
    for job in read_rows(a.base/'manifest.jsonl'):
        row=responses.get(job['request_id'],{})
        error=row.get('error') or ('missing' if not row.get('response') else '')
        value={}
        if not error:
            if row['prompt_sha256']!=digest(job['messages']) or row['response_sha256']!=digest(row['response']):
                raise ValueError('Content hash differs')
            if row.get('returned_model')!=job['model']:
                raise ValueError('Content review deployment differs')
            if row['temperature']!=freeze['temperature'] or row['max_tokens']!=freeze['max_tokens']:
                raise ValueError('Content review parameters differ')
            text=row['response'].strip()
            if text.startswith('```'):
                match=re.fullmatch(r'```(?:json)?\s*\n(.*?)\n```',text,re.S)
                if match: text=match.group(1)
            try:
                value=json.loads(text,object_pairs_hook=unique_keys)
                if not isinstance(value,dict) or set(value)!=set(CHECKS+['issues']): raise ValueError('schema')
                if any(type(value[k]) is not bool for k in CHECKS): raise ValueError('non-boolean check')
                if not isinstance(value['issues'],list) or any(not isinstance(s,str) for s in value['issues']): raise ValueError('issues schema')
            except (ValueError,TypeError) as e: error=str(e)[:160]
        results.append({'request_id':job['request_id'],'template':job['template'],'partition':job['partition'],
                        'reviewer':job['model'],'valid':not bool(error),'error':error,'review':value})
    flagged=[r for r in results if not r['valid'] or r['review']['issues'] or not all(r['review'][k] for k in CHECKS)]
    report={'status':'content diagnostics; objections require resolution before formal freeze',
            'expected':len(results),'valid':sum(r['valid'] for r in results),'flagged':len(flagged),
            'flagged_reviews':flagged,'results':results,
            'source_hashes':{name:hashlib.sha256((a.base/name).read_bytes()).hexdigest() for name in ['manifest.jsonl','run/responses.jsonl','freeze.json']}}
    (a.base/'content_audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ['results','source_hashes']},indent=2))

if __name__=='__main__': main()
