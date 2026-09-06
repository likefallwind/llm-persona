#!/usr/bin/env python3
"""One bounded, disclosed completion-budget amendment before forecast locking.

The frozen auditor validates each budget group separately. Only its validated
codes are combined; original requests, outputs, budgets and failures survive.
"""
import fcntl
import hashlib
from itertools import combinations
import json
from pathlib import Path

import pandas as pd

from analyze_personality_coding_v2 import analyze, pair_agreement
from finish_personality_training_v3 import BASE, ROOT, TRAIN, LOGS, run, state
from prepare_personality_pilot_v2 import write_frozen
from run_personality_formal_stage_v3 import verify_files, validate_stage
from run_personality_requests_v2 import now, read_rows

POLICY = BASE / 'training_budget_amendment.json'
OUT = TRAIN / 'budget_recovery'


def combine_validated(jobs, items, events, original_coverage, original_codes,
                      extra_coverage, extra_codes, allowed):
    """Require an exact disjoint partition, then reproduce three-coder rules."""
    expected = {j['request_id'] for j in jobs}
    if len(expected) != len(jobs):
        raise ValueError('Duplicate original job')
    if original_coverage.request_id.duplicated().any() or set(original_coverage.request_id) != expected:
        raise ValueError('Original coverage does not match all jobs')
    if original_coverage.valid.dtype != bool or extra_coverage.valid.dtype != bool:
        raise ValueError('Coverage validity must be boolean')
    missing = set(original_coverage.loc[~original_coverage.valid, 'request_id'])
    if missing != set(allowed):
        raise ValueError('Missing requests differ from the amendment')
    if (extra_coverage.request_id.duplicated().any() or
            set(extra_coverage.request_id) != missing or not extra_coverage.valid.all()):
        raise ValueError('Amended coverage must fill exactly the missing requests')
    valid_ids = expected - missing
    for ids, codes in [(valid_ids, original_codes), (missing, extra_codes)]:
        wanted = {(j['blind_id'], j['model'], e) for j in jobs if j['request_id'] in ids for e in events}
        keys = list(codes[['blind_id', 'judge_requested', 'event']].itertuples(index=False, name=None))
        if len(keys) != len(set(keys)) or set(keys) != wanted:
            raise ValueError('Event codes are missing, duplicated, or outside their validated group')
        if not codes.present.isin([0, 1]).all():
            raise ValueError('Invalid binary event code')
    frame = pd.concat([original_codes, extra_codes], ignore_index=True)
    identities = frame.groupby('judge_requested').judge_returned.apply(lambda x: sorted(set(x))).to_dict()
    if any(names != [judge] for judge, names in identities.items()):
        raise ValueError('Requested and returned deployments differ')
    coverage = pd.concat([original_coverage.loc[original_coverage.valid], extra_coverage], ignore_index=True)
    consensus, agreement = [], []
    judges = {j['model'] for j in jobs}
    if len(judges) != 3:
        raise ValueError('Requires the original three-coder panel')
    for event, part in frame.groupby('event'):
        wide = part.pivot(index='blind_id', columns='judge_requested', values='present')
        if set(wide.columns) != judges or wide.isna().any().any() or set(wide.index) != set(items):
            raise ValueError('Incomplete three-coder event panel')
        for a, b in combinations(wide.columns, 2):
            agreement.append({'event': event, 'judge_a': a, 'judge_b': b,
                              **pair_agreement(wide[a], wide[b])})
        for blind, row in wide.iterrows():
            item = items[blind]
            consensus.append({'blind_id': blind, 'event': event, 'present': int(row.sum() > 1.5),
                              'unanimous': int(row.nunique() == 1),
                              **{k: item[k] for k in ('template', 'progress', 'affect', 'repeat', 'model',
                                                      'source_family', 'partition', 'panel', 'arm') if k in item}})
    return coverage, frame, pd.DataFrame(consensus), pd.DataFrame(agreement), identities


def main():
    LOGS.mkdir(parents=True, exist_ok=True)
    with (TRAIN / 'run/training_pipeline.lock').open('a+') as pipeline:
        fcntl.flock(pipeline.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        policy = json.loads(POLICY.read_text())
        verify_files(policy['files'])
        for name in ['design_freeze.json', 'training_execution_policy.json', 'confirmation_execution_policy.json']:
            verify_files(json.loads((BASE / name).read_text())['files'])
        validate_stage('training')
        if (BASE / 'prediction_lock.json').exists() or (BASE / 'confirmation/run/responses.jsonl').exists():
            raise ValueError('This amendment must precede primary forecasts and confirmation answers')
        if OUT.exists() or (TRAIN / 'measurement_selection.json').exists():
            raise ValueError('One-time amendment already started; do not reset its attempt allowance')
        source = ROOT / policy['source_run']
        judge = TRAIN / 'judge/v2_2'
        rubric = ROOT / 'data/educational_personality_measurement_v2_2.json'
        # All preceding runs must have released their writers. Hold the final
        # source shared lock throughout recovery so it cannot change underneath us.
        with (source / 'writer.lock').open('r') as source_lock:
            fcntl.flock(source_lock.fileno(), fcntl.LOCK_SH | fcntl.LOCK_NB)
            OUT.mkdir()
            try:
                state('auditing_before_budget_amendment', status='running')
                original_diag = OUT / 'original_diagnostics'
                analyze(judge, source, original_diag, rubric)
                old_cov = pd.read_csv(original_diag / 'coverage.csv')
                missing = set(old_cov.loc[~old_cov.valid, 'request_id'])
                if missing != set(policy['allowed_request_ids']) or len(missing) != 1:
                    raise ValueError('Actual failure set differs from the recorded single-request amendment')
                old_rows = {r['request_id']: r for r in read_rows(source / 'responses.jsonl')}
                for rid in missing:
                    row = old_rows[rid]
                    if row.get('error') != 'invalid_completion_Empty visible completion' or row.get('finish_reason') != 'length':
                        raise ValueError('Budget expansion requires the recorded empty length failure')
                jobs = read_rows(judge / 'manifest.jsonl')
                selected = [j for j in jobs if j['request_id'] in missing]
                extra = OUT / 'judge'
                extra.mkdir()
                write_frozen(extra / 'manifest.jsonl', ''.join(json.dumps(j, ensure_ascii=False) + '\n' for j in selected))
                write_frozen(extra / 'unblinding.jsonl', (judge / 'unblinding.jsonl').read_text())
                freeze = json.loads((judge / 'freeze.json').read_text())
                freeze.update(items=1, judges=[selected[0]['model']], expected_calls=1,
                              max_tokens=policy['max_tokens'], amendment=str(POLICY.relative_to(ROOT)),
                              manifest_sha256=hashlib.sha256((extra / 'manifest.jsonl').read_bytes()).hexdigest())
                write_frozen(extra / 'freeze.json', json.dumps(freeze, indent=2) + '\n')
                verify_files(policy['files'])
                run('single_request_budget_amendment', 'run_personality_requests_v2.py',
                    '--manifest', extra / 'manifest.jsonl', '--output-dir', extra / 'run',
                    '--temperature', '0', '--max-tokens', policy['max_tokens'], '--timeout', policy['timeout'],
                    '--retries', policy['attempts'], '--allow-current-glm53', '--schedule', 'interleaved')
                verify_files(policy['files'])
                extra_diag = OUT / 'expanded_budget_diagnostics'
                analyze(extra, extra / 'run', extra_diag, rubric)
                events = list(json.loads(rubric.read_text())['events'])
                items = {r['blind_id']: r for r in read_rows(judge / 'unblinding.jsonl')}
                merged = combine_validated(jobs, items, events, old_cov,
                    pd.read_csv(original_diag / 'event_codes.csv'), pd.read_csv(extra_diag / 'coverage.csv'),
                    pd.read_csv(extra_diag / 'event_codes.csv'), policy['allowed_request_ids'])
                final = OUT / 'combined_diagnostics'
                final.mkdir()
                for name, frame in zip(['coverage', 'event_codes', 'consensus', 'pairwise_agreement'], merged[:4]):
                    frame.to_csv(final / (name + '.csv'), index=False)
                inputs = [POLICY, source / 'responses.jsonl', extra / 'manifest.jsonl', extra / 'freeze.json',
                          extra / 'run/responses.jsonl', Path(__file__).resolve(),
                          *original_diag.glob('*.csv'), original_diag / 'summary.json',
                          *extra_diag.glob('*.csv'), extra_diag / 'summary.json']
                summary = json.loads((original_diag / 'summary.json').read_text())
                summary.update(valid_judge_requests=len(merged[0]), invalid_or_missing=0,
                               complete_consensus_event_items=len(merged[2]), judge_requested_to_returned=merged[4],
                               original_budget_valid_requests=3839, expanded_budget_valid_requests=1,
                               amendment=str(POLICY.relative_to(ROOT)),
                               input_hashes={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs})
                summary['limitations'].append('One structurally missing training code used a disclosed larger completion budget; budgets were audited separately. This is a protocol deviation, not an original frozen-design result.')
                write_frozen(final / 'summary.json', json.dumps(summary, indent=2) + '\n')
                selection = {'status': 'complete training measurement', 'diagnostics': str(final.relative_to(ROOT)),
                             'final_run': None, 'source_runs': [str(source.relative_to(ROOT)), str((extra / 'run').relative_to(ROOT))],
                             'completed_at': now(), 'original_and_repair_runs_retained': True,
                             'coverage_sha256': hashlib.sha256((final / 'coverage.csv').read_bytes()).hexdigest(),
                             'budget_amendment': str(POLICY.relative_to(ROOT))}
                write_frozen(TRAIN / 'measurement_selection.json', json.dumps(selection, indent=2) + '\n')
                run('lock_predictions', 'lock_personality_predictions_v3.py', '--diagnostics', final, '--judge-base', judge)
                run('verify_confirmation_gate', 'run_personality_formal_stage_v3.py', '--stage', 'confirmation', '--check-only')
                state('training_measurement_and_prediction_lock_complete', status='complete',
                      confirmation_started=False, budget_amendment=str(POLICY.relative_to(ROOT)))
            except Exception as exc:
                state('stopped_for_review', status='failed', error=type(exc).__name__ + ': ' + str(exc)[:220])
                raise


if __name__ == '__main__':
    main()
