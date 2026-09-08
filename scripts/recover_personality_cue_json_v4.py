#!/usr/bin/env python3
"""Recover one absent outer brace as derived coding, never a new API response."""
import fcntl
import json
from pathlib import Path

import pandas as pd

from analyze_personality_coding_v2 import analyze, parse_codes, unique_keys
from complete_personality_training_budget_recovery_v3 import combine_validated
from prepare_personality_cue_transfer_v4 import OUT, ROOT, RUBRIC, EVENTS, sha
from prepare_personality_pilot_v2 import write_frozen
from run_personality_formal_stage_v3 import verify_files
from run_personality_requests_v2 import digest, now, read_rows

RID = '99db96883c0bb0d19f7f:glm-5.3'
DEST = OUT / 'json_recovery'


def close_outer_object(text, answer, events):
    original = text.strip()
    try:
        json.loads(original, object_pairs_hook=unique_keys)
    except json.JSONDecodeError as exc:
        if exc.pos != len(original) or not original.endswith('}'):
            raise ValueError('Only an EOF failure after a closed inner object is eligible') from exc
    else:
        raise ValueError('Already valid JSON must not be repaired')
    repaired = original + '}'
    # Original strict schema, duplicate keys and source-line validation apply.
    values = parse_codes(repaired, answer, events, 'line_ids')
    return repaired, values


def main():
    verify_files(json.loads((OUT / 'design_freeze.json').read_text())['files'])
    if DEST.exists() or (OUT / 'measurement_selection.json').exists():
        raise ValueError('Recovery already started or selected; do not overwrite')
    judge = OUT / 'judge'
    source = judge / 'run_repair2'
    original = OUT / 'measurement_diagnostics/pass2'
    with (OUT / 'runtime/pipeline.lock').open('a+') as pipeline, (source / 'writer.lock').open('r') as writer:
        fcntl.flock(pipeline.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        fcntl.flock(writer.fileno(), fcntl.LOCK_SH | fcntl.LOCK_NB)
        coverage = pd.read_csv(original / 'coverage.csv')
        if set(coverage.loc[~coverage.valid, 'request_id']) != {RID} or int(coverage.valid.sum()) != 15359:
            raise ValueError('Failure partition differs from the documented single JSON failure')
        jobs = read_rows(judge / 'manifest.jsonl')
        job = next(j for j in jobs if j['request_id'] == RID)
        raw = {r['request_id']: r for r in read_rows(source / 'responses.jsonl')}[RID]
        items = {r['blind_id']: r for r in read_rows(judge / 'unblinding.jsonl')}
        item = items[job['blind_id']]
        freeze = json.loads((judge / 'freeze.json').read_text())
        payload = {'model': job['model'], 'messages': job['messages'],
                   'temperature': raw['temperature'], 'max_tokens': raw['max_tokens'], 'stream': False}
        if (raw.get('error') or raw['finish_reason'] != 'stop' or raw['returned_model'] != job['model'] or
            raw['model'] != job['model'] or raw['prompt_sha256'] != digest(job['messages']) or
            raw['response_sha256'] != digest(raw['response']) or raw['payload_sha256'] != digest(payload) or
            raw['temperature'] != freeze['temperature'] or raw['max_tokens'] != freeze['max_tokens']):
            raise ValueError('Raw completion provenance failed')
        events = list(json.loads(RUBRIC.read_text())['events'])
        repaired, values = close_outer_object(raw['response'], item['response'], events)
        dependencies = [Path(__file__), ROOT / 'research/73_cue_json_recovery_amendment_v4.md', RUBRIC,
                        OUT / 'design_freeze.json', source / 'responses.jsonl', judge / 'manifest.jsonl',
                        judge / 'unblinding.jsonl', judge / 'freeze.json', original / 'coverage.csv',
                        original / 'event_codes.csv', ROOT / 'scripts/complete_personality_training_budget_recovery_v3.py',
                        ROOT / 'scripts/analyze_personality_coding_v2.py']
        policy = {'status': 'post-result mechanical syntax amendment; original strict parser unchanged',
                  'created_at': now(), 'allowed_request_ids': [RID], 'new_api_calls': 0,
                  'operation': "Append exactly one ASCII '}' after stripping outer whitespace; no other edits.",
                  'raw_response_sha256': digest(raw['response']), 'derived_text_sha256': digest(repaired),
                  'is_new_provider_response': False,
                  'files': {str(p.relative_to(ROOT)): sha(p) for p in dependencies}}
        write_frozen(OUT / 'json_recovery_amendment.json', json.dumps(policy, indent=2) + '\n')
        DEST.mkdir()
        fresh = DEST / 'original_diagnostics'
        analyze(judge, source, fresh, RUBRIC)
        old_cov = pd.read_csv(fresh / 'coverage.csv')
        old_codes = pd.read_csv(fresh / 'event_codes.csv')
        extra = pd.DataFrame([{'blind_id': job['blind_id'], 'judge_requested': job['model'],
            'judge_returned': raw['returned_model'], 'event': event, 'present': value,
            'model_requested': item['model'], **{k: item[k] for k in
              ['template', 'progress', 'affect', 'repeat', 'source_family', 'partition', 'panel', 'arm']}}
            for event, value in values.items()])
        extra_cov = pd.DataFrame([{'request_id': RID, 'judge_requested': job['model'],
                                   'judge_returned': raw['returned_model'], 'valid': True, 'error': ''}])
        merged = combine_validated(jobs, items, events, old_cov, old_codes, extra_cov, extra, [RID])
        final = DEST / 'combined_diagnostics'
        final.mkdir()
        for name, frame in zip(['coverage', 'event_codes', 'consensus', 'pairwise_agreement'], merged[:4]):
            frame.to_csv(final / (name + '.csv'), index=False)
        extra.to_csv(DEST / 'derived_event_codes.csv', index=False)
        other = old_codes[old_codes.blind_id == job['blind_id']]
        bounds = []
        for event in events:
            votes = other[other.event == event].present.tolist()
            if len(votes) != 2:
                raise ValueError('Requires exactly two other valid original coders')
            bounds.append({'event': event, 'other_valid_coder_votes': votes,
                           'majority_if_missing_vote_zero': int(sum(votes) > 1.5),
                           'majority_if_missing_vote_one': int(sum(votes) + 1 > 1.5),
                           'invariant_to_missing_vote': votes[0] == votes[1]})
        sensitivity = {'status': 'exhaustive binary bound for the absent coder vote', 'request_id': RID,
                       'primary_consensus_invariant_for_all_possible_missing_votes': all(
                           r['invariant_to_missing_vote'] for r in bounds if r['event'] in EVENTS), 'events': bounds}
        write_frozen(DEST / 'missing_vote_bounds.json', json.dumps(sensitivity, indent=2) + '\n')
        report = json.loads((fresh / 'summary.json').read_text())
        report.update(valid_judge_requests=len(merged[0]), invalid_or_missing=0,
                      complete_consensus_event_items=len(merged[2]), judge_requested_to_returned=merged[4],
                      unmodified_strict_valid_requests=15359, mechanically_recovered_requests=1,
                      new_api_calls=0, amendment=str((OUT / 'json_recovery_amendment.json').relative_to(ROOT)))
        report['limitations'].append('One original JSON response lacks its outer closing brace. A disclosed one-character derived repair passed the unchanged schema/evidence parser. Raw provider output is unchanged.')
        write_frozen(final / 'summary.json', json.dumps(report, indent=2) + '\n')
        verify_files(policy['files'])
        selection = {'status': 'complete cue-transfer measurement with disclosed syntax amendment',
                     'completed_at': now(), 'diagnostics': str(final.relative_to(ROOT)), 'final_run': None,
                     'source_runs': [str(source.relative_to(ROOT))], 'valid_judge_requests': 15360,
                     'coverage_sha256': sha(final / 'coverage.csv'), 'original_and_repair_runs_retained': True,
                     'mechanical_recovery': str(DEST.relative_to(ROOT)), 'new_api_calls': 0}
        write_frozen(OUT / 'measurement_selection.json', json.dumps(selection, indent=2) + '\n')
        print(json.dumps(selection, indent=2))
        print(json.dumps(sensitivity, indent=2))


if __name__ == '__main__':
    main()
