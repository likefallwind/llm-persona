#!/usr/bin/env python3
"""Independently verify manifest/response identity, completeness and deployment."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re

from run_personality_requests_v2 import digest, read_rows


def audit(base):
    freeze = json.loads((base/'freeze.json').read_text())
    jobs = read_rows(base/'generation_manifest.jsonl')
    rows = read_rows(base/'run/responses.jsonl')
    latest = {r['request_id']: r for r in rows}
    failures, identity_mentions, deployments = [], [], defaultdict(set)
    summaries = defaultdict(list)
    for name, expected in freeze['hashes'].items():
        if hashlib.sha256((base/name).read_bytes()).hexdigest() != expected:
            failures.append({'reason': 'frozen_input_hash_mismatch', 'file': name})
    for job in jobs:
        row = latest.get(job['request_id'])
        if not row or row.get('error') or not row.get('response'):
            failures.append({'request_id': job['request_id'], 'reason': 'missing_or_failed'})
            continue
        if row['prompt_sha256'] != digest(job['messages']) or row['response_sha256'] != digest(row['response']):
            failures.append({'request_id': job['request_id'], 'reason': 'content_hash_mismatch'})
        if row['finish_reason'] not in ('stop', 'end_turn') or row['model'] != job['model']:
            failures.append({'request_id': job['request_id'], 'reason': 'completion_identity_mismatch'})
        if row.get('temperature') != freeze['generation_temperature'] or row.get('max_tokens') != freeze['max_tokens']:
            failures.append({'request_id': job['request_id'], 'reason': 'sampling_parameter_mismatch'})
        payload = {'model': job['model'], 'messages': job['messages'], 'temperature': freeze['generation_temperature'],
                   'max_tokens': freeze['max_tokens'], 'stream': False}
        if row.get('payload_sha256') != digest(payload):
            failures.append({'request_id': job['request_id'], 'reason': 'payload_hash_mismatch'})
        if freeze.get('stage') and row.get('returned_model') != job['model']:
            failures.append({'request_id': job['request_id'], 'reason': 'formal_deployment_differs_from_request'})
        if not row.get('returned_model'):
            failures.append({'request_id': job['request_id'], 'reason': 'unverified_returned_model'})
        deployments[job['model']].add(row.get('returned_model'))
        summaries[row.get('returned_model')].append(row)
        if re.search(r'\b(?:minimax|deepseek|glm|doubao|qwen|chatgpt|openai)\b', row['response'], re.I):
            identity_mentions.append(job['request_id'])
    for requested, returned in deployments.items():
        if len(returned) != 1:
            failures.append({'requested': requested, 'reason': 'multiple_returned_versions'})
    extra = set(latest)-{j['request_id'] for j in jobs}
    if extra:
        failures.append({'reason': 'unexpected_response_ids', 'n': len(extra)})
    per_model = []
    for name, results in sorted(summaries.items(), key=lambda x: str(x[0])):
        per_model.append({'deployment': name, 'n': len(results),
                          'identical_visible_response_count_beyond_first': len(results)-len({r['response_sha256'] for r in results}),
                          'prompt_tokens': sum(r.get('usage', {}).get('prompt_tokens', 0) for r in results),
                          'completion_tokens': sum(r.get('usage', {}).get('completion_tokens', 0) for r in results),
                          'first_request_at': min(r['started_at'] for r in results),
                          'last_response_at': max(r['completed_at'] for r in results)})
    report = {'status': 'pass' if not failures else 'fail', 'expected': len(jobs),
              'observed_unique_requests': len(latest), 'recorded_attempt_rows': len(rows),
              'failures': failures, 'requested_to_returned': {k: sorted(v, key=str) for k,v in deployments.items()},
              'identity_mentions_in_visible_answers': len(identity_mentions),
              'identity_mention_request_ids': identity_mentions,
              'models': per_model,
              'input_hashes': {name: hashlib.sha256((base/name).read_bytes()).hexdigest()
                               for name in ['generation_manifest.jsonl', 'scenarios.jsonl', 'run/responses.jsonl']},
              'limitations': ['Returned model aliases are provider metadata, not immutable weight attestations.',
                             'No match in a model-name scan does not prove judges cannot infer identity from style.',
                             'Duplicate texts do not prove duplicate generation events or independent RNG streams.']}
    (base/'generation_audit.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, default=Path('artifacts/educational_personality_v2/prospective_pilot'))
    audit(parser.parse_args().base)
