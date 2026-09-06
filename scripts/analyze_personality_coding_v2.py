#!/usr/bin/env python3
"""Validate quoted event codes before summarizing measurement diagnostics."""
import argparse
from itertools import combinations
import hashlib
import json
from pathlib import Path
import re

import numpy as np
import pandas as pd

from run_personality_requests_v2 import digest, read_rows


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON key')
        result[key] = value
    return result


def parse_codes(text, answer, events, evidence_format='exact_quote'):
    text = text.strip()
    if text.startswith('```'):
        match = re.fullmatch(r'```(?:json)?\s*\n(.*?)\n```', text, re.S)
        if not match:
            raise ValueError('Invalid JSON fence')
        text = match.group(1)
    data = json.loads(text, object_pairs_hook=unique_keys)
    if not isinstance(data, dict) or set(data) != {'events'} or not isinstance(data['events'], dict):
        raise ValueError('Invalid top-level schema')
    if set(data['events']) != set(events):
        raise ValueError('Missing or extra event')
    values = {}
    for name, value in data['events'].items():
        evidence_key = 'evidence_lines' if evidence_format == 'line_ids' else 'evidence'
        if not isinstance(value, dict) or set(value) != {'present', evidence_key}:
            raise ValueError('Invalid event schema')
        present, evidence = value['present'], value[evidence_key]
        if type(present) is not int or present not in (0, 1):
            raise ValueError('Invalid event type')
        if evidence_format == 'line_ids':
            lines = {i: line for i, line in enumerate(answer.splitlines(), start=1) if line.strip()}
            if not isinstance(evidence, list) or any(type(i) is not int or i not in lines for i in evidence):
                raise ValueError('Evidence references absent or empty source lines: ' + name)
            if len(set(evidence)) != len(evidence):
                raise ValueError('Duplicate evidence line IDs')
            if present and not evidence:
                raise ValueError('Positive event lacks source line evidence: ' + name)
            if not present and evidence:
                raise ValueError('Negative event has evidence: ' + name)
            values[name] = present
            continue
        if not isinstance(evidence, str):
            raise ValueError('Invalid quote evidence type')
        if present and (not evidence.strip() or evidence not in answer):
            raise ValueError('Positive event lacks exact response evidence: ' + name)
        if not present and evidence != '':
            raise ValueError('Negative event has evidence: ' + name)
        values[name] = present
    return values


def pair_agreement(a, b):
    a, b = np.asarray(a), np.asarray(b)
    pp = int(((a == 1) & (b == 1)).sum())
    nn = int(((a == 0) & (b == 0)).sum())
    mismatch = int((a != b).sum())
    return {'n': len(a), 'agreement': float((a == b).mean()),
            'positive_agreement': 2*pp/(2*pp+mismatch) if 2*pp+mismatch else None,
            'negative_agreement': 2*nn/(2*nn+mismatch) if 2*nn+mismatch else None}


def analyze(base, run, output, rubric_path):
    rubric = json.loads(rubric_path.read_text())
    freeze = json.loads((base/'freeze.json').read_text())
    rubric_hash = hashlib.sha256(rubric_path.read_bytes()).hexdigest()
    if freeze['rubric_sha256'] != rubric_hash:
        raise ValueError('Rubric differs from frozen judge manifest')
    if freeze['manifest_sha256'] != hashlib.sha256((base/'manifest.jsonl').read_bytes()).hexdigest():
        raise ValueError('Judge manifest differs from its frozen hash')
    events = list(rubric['events'])
    jobs = read_rows(base/'manifest.jsonl')
    items = {r['blind_id']: r for r in read_rows(base/'unblinding.jsonl')}
    responses = {r['request_id']: r for r in read_rows(run/'responses.jsonl')}
    codes, coverage, identities = [], [], {}
    for job in jobs:
        result = responses.get(job['request_id'], {})
        error = result.get('error') or ('missing_response' if not result.get('response') else '')
        if not error and result.get('prompt_sha256') != digest(job['messages']):
            error = 'prompt_hash_mismatch'
        if not error and result.get('response_sha256') != digest(result['response']):
            error = 'response_hash_mismatch'
        if not error and result.get('finish_reason') not in ('stop', 'end_turn'):
            error = 'unverified_finish_reason'
        if not error and (result.get('temperature') != freeze['temperature'] or
                          result.get('max_tokens') != freeze['max_tokens']):
            error = 'sampling_parameters_differ_from_freeze'
        if not error:
            expected_payload = {'model': job['model'], 'messages': job['messages'],
                                'temperature': result['temperature'], 'max_tokens': result['max_tokens'], 'stream': False}
            if result.get('payload_sha256') != digest(expected_payload):
                error = 'payload_hash_mismatch'
        returned = result.get('returned_model')
        if returned:
            identities.setdefault(job['model'], set()).add(returned)
        elif not error:
            error = 'missing_returned_model_metadata'
        item = items[job['blind_id']]
        if not error:
            try:
                values = parse_codes(result['response'], item['response'], events,
                                     rubric.get('evidence_format', 'exact_quote'))
            except (ValueError, TypeError) as exc:
                error = str(exc)[:160]
        coverage.append({'request_id': job['request_id'], 'judge_requested': job['model'],
                         'judge_returned': returned, 'valid': not bool(error), 'error': error})
        if error:
            continue
        for event, present in values.items():
            row = {'blind_id': job['blind_id'], 'judge_requested': job['model'], 'judge_returned': returned,
                   'event': event, 'present': present}
            if 'expected_present' in item:
                row.update(anchor=item['sample_id'], expected=int(event in item['expected_present']),
                           anchor_group=item.get('anchor_group', 'original_development_anchors'))
            else:
                row.update(model_requested=item['model'], template=item['template'], progress=item['progress'],
                           affect=item['affect'], repeat=item['repeat'])
                row.update({k: item[k] for k in ('source_family', 'partition', 'panel', 'arm') if k in item})
            codes.append(row)
    if any(len(names) != 1 for names in identities.values()):
        raise ValueError('Judge deployment changed within this run; stratify before analysis')
    output.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(coverage).to_csv(output/'coverage.csv', index=False)
    frame = pd.DataFrame(codes)
    frame.to_csv(output/'event_codes.csv', index=False)
    expected_judges = len({j['model'] for j in jobs})
    agreement, consensus = [], []
    if len(frame):
        for event, part in frame.groupby('event'):
            wide = part.pivot(index='blind_id', columns='judge_requested', values='present').dropna()
            if len(wide.columns) != expected_judges or len(wide) == 0:
                continue
            for a, b in combinations(wide.columns, 2):
                agreement.append({'event': event, 'judge_a': a, 'judge_b': b,
                                  **pair_agreement(wide[a], wide[b])})
            for blind, row in wide.iterrows():
                item = items[blind]
                consensus.append({'blind_id': blind, 'event': event, 'present': int(row.sum() > expected_judges/2),
                                  'unanimous': int(row.nunique() == 1),
                                  **{k: item[k] for k in ('template', 'progress', 'affect', 'repeat', 'model',
                                                        'source_family', 'partition', 'panel', 'arm') if k in item}})
        if 'expected' in frame:
            frame.assign(matches_expected=frame.present.eq(frame.expected)).groupby(
                ['judge_requested', 'judge_returned', 'anchor_group', 'event']).agg(
                    n=('present', 'size'), matches=('matches_expected', 'sum')).reset_index().to_csv(output/'anchor_agreement.csv', index=False)
            frame[frame.present.ne(frame.expected)].to_csv(output/'anchor_disagreements.csv', index=False)
    pd.DataFrame(agreement).to_csv(output/'pairwise_agreement.csv', index=False)
    cf = pd.DataFrame(consensus)
    cf.to_csv(output/'consensus.csv', index=False)
    if len(cf) and 'model' in cf and not freeze.get('natural_response_preflight') and freeze.get('mode') != 'generation':
        # Names here explicitly refer to request configurations; a separate
        # deployment audit must map them before any publication/model claim.
        cf.groupby(['model', 'event']).agg(n=('present', 'size'), prevalence=('present', 'mean'),
                                          unanimity=('unanimous', 'mean')).reset_index().rename(
                                              columns={'model': 'model_requested'}).to_csv(output/'pilot_prevalence.csv', index=False)
        repeat_rows = []
        for (model, event), part in cf.groupby(['model', 'event']):
            wide = part.pivot(index=['template', 'progress', 'affect'], columns='repeat', values='present').dropna()
            if set(wide.columns) == {0, 1} and len(wide):
                repeat_rows.append({'model_requested': model, 'event': event, **pair_agreement(wide[0], wide[1])})
        pd.DataFrame(repeat_rows).to_csv(output/'repeat_agreement.csv', index=False)
    summary = {'status': 'measurement diagnostics, not confirmatory personality inference',
               'natural_response_preflight': freeze.get('natural_response_preflight', False),
               'evidence_format': rubric.get('evidence_format', 'exact_quote'),
               'rubric_sha256': rubric_hash,
               'expected_judge_requests': len(jobs), 'valid_judge_requests': sum(r['valid'] for r in coverage),
               'invalid_or_missing': sum(not r['valid'] for r in coverage),
               'judge_requested_to_returned': {k: sorted(v) for k,v in identities.items()},
               'complete_consensus_event_items': len(cf),
               'limitations': ['Evidence references validate provenance, not semantic truth.',
                               'Only items with all three valid coders contribute to consensus.',
                               'Agent-authored anchor agreement is not human gold accuracy.',
                               'Pilot repetition agreement can be high from near-constant event prevalence.']}
    (output/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, required=True)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--rubric', type=Path, default=Path('data/educational_personality_measurement_v2.json'))
    args = parser.parse_args()
    analyze(args.base, args.run, args.output, args.rubric)
