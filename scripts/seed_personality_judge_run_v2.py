#!/usr/bin/env python3
"""Reuse identical, validated preflight requests without counting new API calls.

Only seeds an unstarted target run. It never imports anchor rows that are absent
from the target manifest, changes prompts, or upgrades failed judge responses.
"""
import argparse
import fcntl
import hashlib
import json
from pathlib import Path

from analyze_personality_coding_v2 import parse_codes
from run_personality_requests_v2 import digest, read_rows


def seed(source, target_base, target_run, rubric_path, allow_incomplete_source=False):
    lock = (source/'writer.lock').open('a+')
    fcntl.flock(lock.fileno(), fcntl.LOCK_SH | fcntl.LOCK_NB)
    if not allow_incomplete_source and json.loads((source/'summary.json').read_text())['run_status'] != 'complete':
        raise ValueError('Source preflight is incomplete')
    rubric = json.loads(rubric_path.read_text())
    target_freeze = json.loads((target_base/'freeze.json').read_text())
    if target_freeze['rubric_sha256'] != hashlib.sha256(rubric_path.read_bytes()).hexdigest():
        raise ValueError('Rubric hash mismatch')
    if target_freeze['manifest_sha256'] != hashlib.sha256((target_base/'manifest.jsonl').read_bytes()).hexdigest():
        raise ValueError('Target manifest hash mismatch')
    items = {r['blind_id']: r for r in read_rows(target_base/'unblinding.jsonl')}
    jobs = {j['request_id']: j for j in read_rows(target_base/'manifest.jsonl')}
    responses = {r['request_id']: r for r in read_rows(source/'responses.jsonl')}
    imported, rejected = [], []
    for key in sorted(jobs):
        if key not in responses:
            continue
        job, row = jobs[key], responses[key]
        if row['error'] or not row.get('response') or row['finish_reason'] not in ('stop', 'end_turn'):
            if allow_incomplete_source:
                rejected.append({'request_id': key, 'reason': row.get('error') or 'incomplete_response'})
                continue
            raise ValueError('Preflight response incomplete')
        if row['temperature'] != target_freeze['temperature'] or row['max_tokens'] != target_freeze['max_tokens']:
            raise ValueError('Sampling parameters differ')
        if row['prompt_sha256'] != digest(job['messages']) or row['response_sha256'] != digest(row['response']):
            raise ValueError('Prompt or response hash differs')
        payload = {'model': job['model'], 'messages': job['messages'], 'temperature': row['temperature'],
                   'max_tokens': row['max_tokens'], 'stream': False}
        if row['payload_sha256'] != digest(payload):
            raise ValueError('Payload differs')
        if row['model'] != job['model'] or row.get('returned_model') != job['model']:
            raise ValueError('Deployment differs')
        item = items[job['blind_id']]
        try:
            parse_codes(row['response'], item['response'], list(rubric['events']), rubric.get('evidence_format', 'exact_quote'))
        except (ValueError, TypeError) as exc:
            if not allow_incomplete_source:
                raise
            rejected.append({'request_id': key, 'reason': str(exc)[:160]})
            continue
        # Preserve completion IDs and timestamps: these are the original calls,
        # never new independent observations or additional judge repetitions.
        imported.append(row)
    if not imported:
        raise ValueError('No identical completed requests to reuse')
    target_run.mkdir(parents=True, exist_ok=True)
    if (target_run/'responses.jsonl').exists() or (target_run/'contract.json').exists():
        raise ValueError('Target run has already started or was seeded')
    content = ''.join(json.dumps(row, ensure_ascii=False)+'\n' for row in imported)
    (target_run/'responses.jsonl').write_text(content)
    report = {'source_run': str(source), 'target_base': str(target_base), 'source_response_sha256':
              hashlib.sha256((source/'responses.jsonl').read_bytes()).hexdigest(),
              'target_seed_sha256': hashlib.sha256(content.encode()).hexdigest(),
              'target_manifest_sha256': target_freeze['manifest_sha256'],
              'target_rubric_sha256': target_freeze['rubric_sha256'], 'reused_request_rows': len(imported),
              'incomplete_source_explicitly_allowed': allow_incomplete_source,
              'rejected_source_rows': rejected,
              'selection_rule': 'Reuse every structurally valid response; no selection by event label or judge agreement.',
              'reused_judge_outputs_are_not_new_api_calls': True, 'new_api_calls_needed': len(jobs)-len(imported),
              'reused_request_ids': [r['request_id'] for r in imported]}
    (target_run/'reuse_receipt.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k != 'reused_request_ids'}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-run', type=Path, required=True)
    parser.add_argument('--target-base', type=Path, required=True)
    parser.add_argument('--target-run', type=Path, required=True)
    parser.add_argument('--rubric', type=Path, required=True)
    parser.add_argument('--allow-incomplete-source', action='store_true',
                        help='Explicit repair pass: reuse all valid rows and record every structurally invalid row.')
    args = parser.parse_args()
    seed(args.source_run, args.target_base, args.target_run, args.rubric, args.allow_incomplete_source)
