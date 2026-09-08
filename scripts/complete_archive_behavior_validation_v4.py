#!/usr/bin/env python3
"""Run frozen archived-response coding in background with bounded repairs."""
import argparse
import fcntl
import json
import os
import subprocess
import sys

import pandas as pd

from analyze_personality_coding_v2 import analyze
from complete_personality_training_budget_recovery_v3 import combine_validated
from prepare_archive_behavior_validation_v4 import BASE, JUDGES, ROOT, RUBRIC
from prepare_personality_cue_transfer_v4 import sha
from prepare_personality_judging_v2 import judge_messages
from prepare_personality_pilot_v2 import write_frozen
from recover_personality_cue_json_v4 import close_outer_object
from run_personality_formal_stage_v3 import verify_files
from run_personality_requests_v2 import read_rows, now, digest
from seed_personality_judge_run_v2 import seed

RUNTIME = BASE / 'runtime'


def state(stage, status, **extra):
    report = {'stage': stage, 'status': status, 'at': now(), 'research_quality_goal_complete': False, **extra}
    target = RUNTIME / 'pipeline_state.json'
    temporary = target.with_suffix('.tmp')
    temporary.write_text(json.dumps(report, indent=2) + '\n')
    temporary.replace(target)
    print(json.dumps(report), flush=True)


def preflight():
    lock = json.loads((BASE / 'design_freeze.json').read_text())
    verify_files(lock['files'])
    judge = BASE / 'judge'
    mapping = {r['blind_id']: r for r in read_rows(judge / 'unblinding.jsonl')}
    rubric = json.loads(RUBRIC.read_text())
    jobs = read_rows(judge / 'manifest.jsonl')
    if len(jobs) != 10752 or len({j['request_id'] for j in jobs}) != 10752 or len(mapping) != 3584:
        raise ValueError('Frozen coding panel dimensions differ')
    for job in jobs:
        if job['model'] not in JUDGES or job['messages'] != judge_messages(mapping[job['blind_id']], rubric):
            raise ValueError('Frozen coding payload does not match source mapping')
    for name in ['MINIMAX_API_KEY', 'API_GATEWAY']:
        if not os.environ.get(name):
            raise ValueError('Missing credential variable: ' + name)
    return lock


def api_pass(index, current):
    marker = RUNTIME / ('coding_pass_' + str(index) + '.json')
    if marker.exists():
        if json.loads(marker.read_text())['status'] == 'complete':
            return
        raise ValueError('Interrupted invocation requires recovery audit; no automatic allowance reset')
    verify_files(json.loads((BASE / 'design_freeze.json').read_text())['files'])
    receipt = {'status': 'started', 'started_at': now(), 'attempt_limit_per_request': 2}
    with marker.open('x') as stream:
        stream.write(json.dumps(receipt, indent=2) + '\n')
    state('coding_pass_' + str(index), 'running')
    with (RUNTIME / ('coding_pass_' + str(index) + '.log')).open('a') as log:
        result = subprocess.run([sys.executable, str(ROOT / 'scripts/run_personality_requests_v2.py'),
            '--manifest', str(BASE / 'judge/manifest.jsonl'), '--output-dir', str(current),
            '--temperature', '0.0', '--max-tokens', '32768', '--timeout', '660', '--retries', '2',
            '--allow-current-glm53', '--schedule', 'interleaved'], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError('Coding runner exited ' + str(result.returncode))
    receipt.update(status='complete', completed_at=now(), summary_sha256=sha(current / 'summary.json'))
    marker.write_text(json.dumps(receipt, indent=2) + '\n')


def mechanical_recovery(judge, current, diagnostics):
    coverage = pd.read_csv(diagnostics / 'coverage.csv')
    missing = set(coverage.loc[~coverage.valid, 'request_id'])
    jobs = read_rows(judge / 'manifest.jsonl')
    items = {r['blind_id']: r for r in read_rows(judge / 'unblinding.jsonl')}
    responses = {r['request_id']: r for r in read_rows(current / 'responses.jsonl')}
    events = list(json.loads(RUBRIC.read_text())['events'])
    derived, extra_cov, receipts = [], [], []
    for job in jobs:
        if job['request_id'] not in missing:
            continue
        row = responses.get(job['request_id'], {})
        payload = {'model': job['model'], 'messages': job['messages'], 'temperature': 0.0, 'max_tokens': 32768, 'stream': False}
        if (row.get('error') or row.get('finish_reason') not in ['stop', 'end_turn'] or
            row.get('model') != job['model'] or row.get('returned_model') != job['model'] or
            row.get('temperature') != 0.0 or row.get('max_tokens') != 32768 or
            row.get('prompt_sha256') != digest(job['messages']) or
            row.get('payload_sha256') != digest(payload) or row.get('response_sha256') != digest(row.get('response'))):
            raise ValueError('Unresolved non-syntax coding failure after fixed pass limit')
        item = items[job['blind_id']]
        repaired, values = close_outer_object(row['response'], item['response'], events)
        receipts.append({'request_id': job['request_id'], 'raw_response_sha256': digest(row['response']),
                         'derived_text_sha256': digest(repaired), 'operation': 'append one outer closing brace',
                         'new_api_response': False})
        extra_cov.append({'request_id': job['request_id'], 'judge_requested': job['model'],
                          'judge_returned': row['returned_model'], 'valid': True, 'error': ''})
        for event, value in values.items():
            derived.append({'blind_id': job['blind_id'], 'judge_requested': job['model'],
                'judge_returned': row['returned_model'], 'event': event, 'present': value,
                'model_requested': item['model'], **{k: item[k] for k in
                    ['template', 'progress', 'affect', 'repeat', 'source_family', 'partition', 'panel', 'arm']}})
    merged = combine_validated(jobs, items, events, coverage, pd.read_csv(diagnostics / 'event_codes.csv'),
                               pd.DataFrame(extra_cov), pd.DataFrame(derived), missing)
    final = BASE / 'measurement_diagnostics/mechanical_final'
    final.mkdir()
    for name, frame in zip(['coverage', 'event_codes', 'consensus', 'pairwise_agreement'], merged[:4]):
        frame.to_csv(final / (name + '.csv'), index=False)
    summary = json.loads((diagnostics / 'summary.json').read_text())
    summary.update(valid_judge_requests=10752, invalid_or_missing=0, complete_consensus_event_items=len(merged[2]),
                   mechanically_recovered_requests=len(missing))
    summary['limitations'].append('Disclosed outer-brace-only derived JSON repairs; provider records are unchanged.')
    write_frozen(final / 'summary.json', json.dumps(summary, indent=2) + '\n')
    write_frozen(final / 'syntax_repair_receipts.json', json.dumps(receipts, indent=2) + '\n')
    return final


def main(check_only=False):
    lock = preflight()
    if check_only:
        print(json.dumps({'status': 'preflight_pass', 'new_api_calls': 0, 'planned_coding': 10752,
                          'new_teacher_generations': 0, 'provider_caps': lock['provider_caps']}))
        return
    RUNTIME.mkdir(parents=True, exist_ok=True)
    with (RUNTIME / 'pipeline.lock').open('a+') as pipeline:
        fcntl.flock(pipeline.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        if (BASE / 'analysis/summary.json').exists():
            raise ValueError('Archive analysis already complete; do not rerun')
        try:
            judge = BASE / 'judge'
            current = judge / 'run'
            for index in range(3):
                api_pass(index, current)
                results = read_rows(current / 'responses.jsonl')
                expected = {j['request_id'] for j in read_rows(judge / 'manifest.jsonl')}
                if {r['request_id'] for r in results} - expected:
                    raise ValueError('Unexpected archived-response coding request ID')
                if not results or min(r['started_at'] for r in results) <= lock['locked_at']:
                    raise ValueError('Archive coding precedes its design lock')
                for row in results:
                    if not row.get('error') and row.get('returned_model') != row.get('model'):
                        raise ValueError('Unexpected returned coder deployment')
                diagnostics = BASE / 'measurement_diagnostics' / ('pass' + str(index))
                analyze(judge, current, diagnostics, RUBRIC)
                report = json.loads((diagnostics / 'summary.json').read_text())
                if not report['invalid_or_missing']:
                    break
                if index == 2:
                    diagnostics = mechanical_recovery(judge, current, diagnostics)
                    break
                if not report['valid_judge_requests']:
                    raise ValueError('Systemic coding failure; do not spend another batch')
                target = judge / ('run_repair' + str(index + 1))
                if not target.exists():
                    seed(current, judge, target, RUBRIC, allow_incomplete_source=True)
                current = target
            selection = {'status': 'complete archived-response coding', 'completed_at': now(),
                         'diagnostics': str(diagnostics.relative_to(ROOT)), 'last_raw_run': str(current.relative_to(ROOT)),
                         'coverage_sha256': sha(diagnostics / 'coverage.csv'), 'original_runs_preserved': True}
            (BASE / 'measurement_selection.json').write_text(json.dumps(selection, indent=2) + '\n')
            verify_files(lock['files'])
            state('source_grouped_analysis', 'running')
            subprocess.run([sys.executable, str(ROOT / 'scripts/analyze_archive_behavior_validation_v4.py'),
                            '--diagnostics', str(diagnostics)], cwd=ROOT, check=True)
            state('archive_behavior_calculations_complete', 'complete', scientific_synthesis_complete=False)
        except Exception as exc:
            state('stopped_for_review', 'failed', error=type(exc).__name__ + ': ' + str(exc)[:220])
            raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-only', action='store_true')
    main(parser.parse_args().check_only)
