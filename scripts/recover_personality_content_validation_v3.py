#!/usr/bin/env python3
"""Disclosed 0-versus-0.0 payload validation correction and bounded repairs.

The frozen content implementation remains intact. This adapter reconstructs
the payload with the actual, verified zero-valued numeric representation used
by the frozen request runner. Parsing, verdicts, prompts, models and repair
allowances remain unchanged.
"""
import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import personality_content_sensitivity_v3 as content
from run_personality_requests_v2 import digest, now
from run_personality_formal_stage_v3 import verify_files

ROOT, BASE, OUT = content.ROOT, content.BASE, content.OUT
REC = OUT / 'validation_recovery'
AMENDMENT = BASE / 'content_validation_amendment.json'


def validate_result(job, row, item):
    if row.get('error') or not row.get('response') or row.get('finish_reason') not in ('stop', 'end_turn'):
        raise ValueError(row.get('error') or 'missing_or_incomplete_response')
    if row.get('model') != job['model'] or row.get('returned_model') != job['model']:
        raise ValueError('Deployment differs')
    temperature, max_tokens = row.get('temperature'), row.get('max_tokens')
    if (type(temperature) not in (int, float) or temperature != 0
            or type(max_tokens) is not int or max_tokens != 16384):
        raise ValueError('Sampling parameters differ')
    payload = {'model': job['model'], 'messages': job['messages'],
               'temperature': temperature, 'max_tokens': max_tokens, 'stream': False}
    if (row.get('prompt_sha256') != digest(job['messages'])
            or row.get('payload_sha256') != digest(payload)
            or row.get('response_sha256') != digest(row['response'])):
        raise ValueError('Prompt, payload or response hash differs')
    return content.parse(row['response'], item['response'])


@contextmanager
def corrected_validation():
    original = content.validate_result
    content.validate_result = validate_result
    try:
        yield
    finally:
        content.validate_result = original


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify():
    content.policy()
    verify_files(json.loads((OUT / 'freeze.json').read_text())['files'])
    policy = json.loads(AMENDMENT.read_text())
    verify_files(policy['files'])
    if (policy['remaining_structural_repair_passes'] != 2
            or policy['expected_initial_valid'] != 2577
            or len(policy['initial_pending_request_ids']) != 7):
        raise ValueError('Unexpected correction or repair scope')
    return policy


def audit(run, output):
    verify()
    with corrected_validation():
        content.audit(run, output)
    report_path = output / 'summary.json'
    report = json.loads(report_path.read_text())
    report['validation_amendment'] = str(AMENDMENT.relative_to(ROOT))
    report['files'].update({str(p.relative_to(ROOT)): sha(p) for p in [AMENDMENT, Path(__file__).resolve()]})
    report_path.write_text(json.dumps(report, indent=2) + '\n')
    return report


def state(stage, **extra):
    value = {'pipeline_pid': os.getpid(), 'stage': stage, 'updated_at': now(),
             'validation_amendment': str(AMENDMENT.relative_to(ROOT)), **extra}
    for path in [REC / 'pipeline_state.json', OUT / 'pipeline_state.json']:
        temp = path.with_suffix('.tmp')
        temp.write_text(json.dumps(value, indent=2) + '\n')
        temp.replace(path)
    print(json.dumps(value), flush=True)


def run():
    policy = verify()
    REC.mkdir(exist_ok=True)
    with (OUT / 'content_pipeline.lock').open('a+') as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        started = REC / 'started.json'
        if started.exists():
            raise ValueError('Recovery already started; review its history before any restart')
        prior = OUT / 'pipeline_state.json'
        if json.loads(prior.read_text()).get('status') != 'failed':
            raise ValueError('Expected the preserved stopped original controller')
        content.write_frozen(REC / 'original_pipeline_state.json', prior.read_text())
        started.write_text(json.dumps({'started_at': now(), 'pid': os.getpid(),
                                      'amendment_sha256': sha(AMENDMENT)}, indent=2) + '\n')
        try:
            current = OUT / 'run'
            diagnostics = REC / 'diagnostics/pass0'
            state('corrected_initial_content_audit', status='running')
            report = audit(current, diagnostics)
            coverage = content.pd.read_csv(diagnostics / 'coverage.csv')
            pending = set(coverage.loc[~coverage.valid, 'request_id'])
            if report['valid_requests'] != policy['expected_initial_valid'] or pending != set(policy['initial_pending_request_ids']):
                raise ValueError('Initial corrected coverage differs from the disclosed scope')
            for repair in (1, 2):
                if not report['invalid_or_missing']:
                    break
                target = REC / f'run_repair{repair}'
                state(f'seed_content_repair_{repair}', status='running')
                with corrected_validation():
                    content.seed(current, target)
                state(f'content_repair_{repair}', status='running', pending=report['invalid_or_missing'])
                env = os.environ.copy()
                env.update(PYTHONDONTWRITEBYTECODE='1', OPENBLAS_NUM_THREADS='1')
                with (REC / f'repair{repair}.log').open('a') as log:
                    subprocess.run([sys.executable, str(ROOT / 'scripts/run_personality_requests_v2.py'),
                                    '--manifest', str(OUT / 'manifest.jsonl'), '--output-dir', str(target),
                                    '--temperature', '0', '--max-tokens', '16384', '--timeout', '360',
                                    '--retries', '2', '--schedule', 'interleaved'], cwd=ROOT, env=env,
                                   stdout=log, stderr=subprocess.STDOUT, check=True)
                current = target
                diagnostics = REC / f'diagnostics/pass{repair}'
                report = audit(current, diagnostics)
            if report['invalid_or_missing']:
                raise ValueError('Content measurement incomplete after original two structural repair passes')
            selection = {'status': 'complete secondary content coding',
                         'diagnostics': str(diagnostics.relative_to(ROOT)),
                         'final_run': str(current.relative_to(ROOT)), 'completed_at': now(),
                         'all_original_runs_retained': True,
                         'validation_amendment': str(AMENDMENT.relative_to(ROOT)),
                         'coverage_sha256': sha(diagnostics / 'coverage.csv')}
            (OUT / 'measurement_selection.json').write_text(json.dumps(selection, indent=2) + '\n')
            state('content_sensitivity_analysis', status='running')
            content.analyze(diagnostics)
            state('content_sensitivity_complete', status='complete', paper_complete=False)
        except Exception as exc:
            state('stopped_for_review', status='failed', error=type(exc).__name__ + ': ' + str(exc)[:220])
            raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['audit', 'run'])
    args = parser.parse_args()
    if args.stage == 'audit':
        print(json.dumps(audit(OUT / 'run', REC / 'preflight_diagnostics')))
    else:
        run()
