#!/usr/bin/env python3
"""Disclosed, one-time completion of six structurally missing GLM codes.

Original measurements are immutable. Budgets are audited separately before
their exact disjoint union enters the unchanged frozen confirmation analysis.
"""
import argparse
import fcntl
import hashlib
import json
from pathlib import Path

import pandas as pd

from analyze_personality_coding_v2 import analyze
from complete_personality_training_budget_recovery_v3 import combine_validated
from complete_personality_confirmation_v3 import BASE, ROOT, STAGE, LOGS, run, state
from prepare_personality_pilot_v2 import write_frozen
from run_personality_formal_stage_v3 import verify_files, validate_stage
from run_personality_requests_v2 import now, read_rows

POLICY = BASE / 'confirmation_budget_amendment.json'
OUT = STAGE / 'budget_recovery'


def preflight(policy):
    verify_files(policy['files'])
    for name in ['design_freeze.json', 'confirmation_execution_policy.json',
                 'prediction_lock.json', 'judge_sensitivity_lock.json',
                 'generator_deletion_lock.json']:
        verify_files(json.loads((BASE / name).read_text())['files'])
    validate_stage('confirmation')
    source = ROOT / policy['source_run']
    coverage = pd.read_csv(STAGE / 'measurement_diagnostics/pass2/coverage.csv')
    missing = set(coverage.loc[~coverage.valid, 'request_id'])
    if missing != set(policy['allowed_request_ids']) or len(missing) != 6:
        raise ValueError('Frozen six-request failure set changed')
    if len(coverage) != 12120 or int(coverage.valid.sum()) != 12114:
        raise ValueError('Original measurement coverage changed')
    for name in ['run_repair1', 'run_repair2']:
        rows = {r['request_id']: r for r in read_rows(STAGE / 'judge/v2_2' / name / 'responses.jsonl')}
        for rid in missing:
            row = rows[rid]
            if (row['model'] != 'glm-5.3' or row.get('returned_model') != 'glm-5.3'
                    or row.get('error') != 'invalid_completion_Empty visible completion'
                    or row.get('response') or row.get('finish_reason') != 'length'
                    or row['max_tokens'] != 16384 or len(row['attempts']) != 2):
                raise ValueError('Failure does not meet recorded budget-exhaustion rule')
            if any(a.get('finish_reason') != 'length' or
                   a.get('usage', {}).get('completion_tokens') != 16384 for a in row['attempts']):
                raise ValueError('Attempt history differs from the amendment')
    if OUT.exists() or (STAGE / 'measurement_selection.json').exists():
        raise ValueError('One-time amendment already started; do not reset allowance')
    if (BASE / 'confirmation_analysis/summary.json').exists():
        raise ValueError('Amendment must be recorded before primary result computation')
    return source, missing


def main(check_only=False):
    policy = json.loads(POLICY.read_text())
    with (STAGE / 'run/confirmation_pipeline.lock').open('a+') as pipeline:
        fcntl.flock(pipeline.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        source, missing = preflight(policy)
        with (source / 'writer.lock').open('r') as source_lock:
            fcntl.flock(source_lock.fileno(), fcntl.LOCK_SH | fcntl.LOCK_NB)
            if check_only:
                print(json.dumps(dict(status='preflight_pass', missing_requests=len(missing), new_api_calls=0)))
                return
            OUT.mkdir()
            LOGS.mkdir(parents=True, exist_ok=True)
            try:
                state('auditing_before_confirmation_budget_amendment', status='running')
                judge = STAGE / 'judge/v2_2'
                rubric = ROOT / 'data/educational_personality_measurement_v2_2.json'
                original_diag = OUT / 'original_diagnostics'
                analyze(judge, source, original_diag, rubric)
                old_cov = pd.read_csv(original_diag / 'coverage.csv')
                if set(old_cov.loc[~old_cov.valid, 'request_id']) != missing:
                    raise ValueError('Fresh original audit differs from recorded failure set')
                jobs = read_rows(judge / 'manifest.jsonl')
                selected = [j for j in jobs if j['request_id'] in missing]
                extra = OUT / 'judge'
                extra.mkdir()
                write_frozen(extra / 'manifest.jsonl', ''.join(json.dumps(j, ensure_ascii=False) + '\n' for j in selected))
                write_frozen(extra / 'unblinding.jsonl', (judge / 'unblinding.jsonl').read_text())
                freeze = json.loads((judge / 'freeze.json').read_text())
                freeze.update(items=len({j['blind_id'] for j in selected}), judges=['glm-5.3'],
                              expected_calls=6, max_tokens=policy['max_tokens'],
                              amendment=str(POLICY.relative_to(ROOT)),
                              manifest_sha256=hashlib.sha256((extra / 'manifest.jsonl').read_bytes()).hexdigest())
                write_frozen(extra / 'freeze.json', json.dumps(freeze, indent=2) + '\n')
                verify_files(policy['files'])
                run('six_request_confirmation_budget_amendment', 'run_personality_requests_v2.py',
                    '--manifest', extra / 'manifest.jsonl', '--output-dir', extra / 'run',
                    '--temperature', '0', '--max-tokens', policy['max_tokens'], '--timeout', policy['timeout'],
                    '--retries', policy['attempts'], '--allow-current-glm53', '--schedule', 'interleaved')
                verify_files(policy['files'])
                extra_diag = OUT / 'expanded_budget_diagnostics'
                analyze(extra, extra / 'run', extra_diag, rubric)
                extra_summary = json.loads((extra_diag / 'summary.json').read_text())
                if extra_summary['invalid_or_missing']:
                    raise ValueError('Bounded six-request amendment incomplete; no automatic additional attempts')
                events = list(json.loads(rubric.read_text())['events'])
                items = {r['blind_id']: r for r in read_rows(judge / 'unblinding.jsonl')}
                merged = combine_validated(jobs, items, events, old_cov,
                    pd.read_csv(original_diag / 'event_codes.csv'), pd.read_csv(extra_diag / 'coverage.csv'),
                    pd.read_csv(extra_diag / 'event_codes.csv'), policy['allowed_request_ids'])
                if len(merged[0]) != 12120 or len(merged[2]) != 32320:
                    raise ValueError('Combined coverage must exactly restore the full original panel')
                final = OUT / 'combined_diagnostics'
                final.mkdir()
                for name, frame in zip(['coverage', 'event_codes', 'consensus', 'pairwise_agreement'], merged[:4]):
                    frame.to_csv(final / (name + '.csv'), index=False)
                inputs = [POLICY, source / 'responses.jsonl', extra / 'manifest.jsonl', extra / 'freeze.json',
                          extra / 'run/responses.jsonl', Path(__file__).resolve(),
                          *original_diag.glob('*.csv'), original_diag / 'summary.json',
                          *extra_diag.glob('*.csv'), extra_diag / 'summary.json']
                summary = json.loads((original_diag / 'summary.json').read_text())
                summary.update(valid_judge_requests=12120, invalid_or_missing=0,
                               complete_consensus_event_items=32320, judge_requested_to_returned=merged[4],
                               original_budget_valid_requests=12114, expanded_budget_valid_requests=6,
                               amendment=str(POLICY.relative_to(ROOT)),
                               input_hashes={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs})
                summary['limitations'].append('Six structurally missing GLM codes used a disclosed larger completion budget after the frozen repair limit. This is a protocol deviation; dependence of primary conclusions on the amended codes requires separate sensitivity analysis.')
                write_frozen(final / 'summary.json', json.dumps(summary, indent=2) + '\n')
                selection = dict(status='complete confirmation measurement', diagnostics=str(final.relative_to(ROOT)),
                    final_run=None, source_runs=[str(source.relative_to(ROOT)), str((extra / 'run').relative_to(ROOT))],
                    completed_at=now(), original_and_repair_runs_retained=True,
                    coverage_sha256=hashlib.sha256((final / 'coverage.csv').read_bytes()).hexdigest(),
                    budget_amendment=str(POLICY.relative_to(ROOT)))
                write_frozen(STAGE / 'measurement_selection.json', json.dumps(selection, indent=2) + '\n')
                verify_files(policy['files'])
                run('primary_confirmation_analysis', 'analyze_personality_confirmation_v3.py', '--diagnostics', final)
                run('confirmation_robustness', 'analyze_personality_robustness_v3.py',
                    '--diagnostics', final, '--training-resamples', '200')
                state('confirmation_primary_and_robustness_calculations_complete', status='complete',
                      scientific_synthesis_complete=False, paper_complete=False,
                      budget_amendment=str(POLICY.relative_to(ROOT)))
            except Exception as exc:
                state('stopped_for_review', status='failed', error=type(exc).__name__ + ': ' + str(exc)[:220])
                raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-only', action='store_true')
    main(parser.parse_args().check_only)
