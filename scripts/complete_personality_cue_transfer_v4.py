#!/usr/bin/env python3
"""Bounded, resumable cue-transfer controller with durable API-pass receipts."""
import argparse
import fcntl
import json
import os
import subprocess
import sys

from analyze_personality_coding_v2 import analyze
from audit_personality_generation_v2 import audit as audit_generation
from audit_personality_judge_lineage_v3 import audit as audit_lineage
from prepare_personality_cue_transfer_v4 import OUT, ROOT, RUBRIC, sha
from prepare_personality_pilot_v2 import write_frozen
from run_personality_formal_stage_v3 import verify_files
from run_personality_requests_v2 import now, read_rows
from seed_personality_judge_run_v2 import seed

RUNTIME = OUT / 'runtime'


def write_state(stage, status, **extra):
    value = {'stage': stage, 'status': status, 'at': now(),
             'research_quality_goal_complete': False, **extra}
    target = RUNTIME / 'pipeline_state.json'
    tmp = target.with_suffix('.tmp')
    tmp.write_text(json.dumps(value, indent=2) + '\n')
    tmp.replace(target)
    print(json.dumps(value), flush=True)


def api_pass(name, manifest, output, temperature, max_tokens):
    """A crashed API pass cannot silently reset its attempt allowance."""
    marker = RUNTIME / (name + '.json')
    if marker.exists():
        receipt = json.loads(marker.read_text())
        if receipt['status'] == 'complete':
            if not (output / 'summary.json').exists():
                raise ValueError('Completed pass lost its runner summary')
            return
        raise ValueError('Interrupted API pass needs explicit recovery audit: ' + name)
    verify_files(json.loads((OUT / 'design_freeze.json').read_text())['files'])
    receipt = {'status': 'started', 'started_at': now(), 'manifest_sha256': sha(manifest),
               'temperature': temperature, 'max_tokens': max_tokens, 'timeout': 660,
               'maximum_attempts_per_request': 2, 'output': str(output.relative_to(ROOT))}
    # Exclusive create before requests: interruption consumes this invocation.
    with marker.open('x') as stream:
        stream.write(json.dumps(receipt, indent=2) + '\n')
    write_state(name, 'running')
    command = [sys.executable, str(ROOT / 'scripts/run_personality_requests_v2.py'),
               '--manifest', str(manifest), '--output-dir', str(output),
               '--temperature', str(temperature), '--max-tokens', str(max_tokens),
               '--timeout', '660', '--retries', '2', '--allow-current-glm53', '--schedule', 'interleaved']
    with (RUNTIME / (name + '.log')).open('a') as log:
        completed = subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
    if completed.returncode:
        raise RuntimeError(name + ' exited ' + str(completed.returncode))
    receipt.update(status='complete', completed_at=now(), summary_sha256=sha(output / 'summary.json'))
    marker.write_text(json.dumps(receipt, indent=2) + '\n')


def verify_coder_identities(judge, run):
    jobs = {j['request_id']: j for j in read_rows(judge / 'manifest.jsonl')}
    rows = {r['request_id']: r for r in read_rows(run / 'responses.jsonl')}
    if set(rows) - set(jobs):
        raise ValueError('Unexpected coding request IDs')
    for key, row in rows.items():
        if not row.get('error') and (row.get('model') != jobs[key]['model'] or
                                     row.get('returned_model') != jobs[key]['model']):
            raise ValueError('Coder returned identity differs from requested deployment')


def preflight():
    lock = json.loads((OUT / 'design_freeze.json').read_text())
    verify_files(lock['files'])
    if lock['status'] != 'post-v3 extension frozen before new generations':
        raise ValueError('Wrong study lock')
    for name in ['MINIMAX_API_KEY', 'API_GATEWAY']:
        if not os.environ.get(name):
            raise ValueError('Required credential environment variable missing: ' + name)
    return lock


def main(check_only=False):
    lock = preflight()
    if check_only:
        print(json.dumps({'status': 'preflight_pass', 'new_api_calls': 0,
                          'planned_generation': 5120, 'planned_coding': 15360,
                          'provider_caps': lock['provider_caps']}))
        return
    RUNTIME.mkdir(parents=True, exist_ok=True)
    with (RUNTIME / 'pipeline.lock').open('a+') as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        if (OUT / 'analysis/summary.json').exists():
            raise ValueError('Analysis already exists; do not rerun completed study')
        try:
            for index in range(3):
                report_path = OUT / 'run/summary.json'
                if report_path.exists() and json.loads(report_path.read_text())['run_status'] == 'complete':
                    break
                api_pass('generation_pass_' + str(index), OUT / 'generation_manifest.jsonl',
                         OUT / 'run', 0.7, 8192)
            if json.loads((OUT / 'run/summary.json').read_text())['run_status'] != 'complete':
                raise ValueError('Teacher generation exhausted fixed three-pass limit')
            audit_generation(OUT)
            first = min(r['started_at'] for r in read_rows(OUT / 'run/responses.jsonl'))
            if not lock['locked_at'] < first:
                raise ValueError('Prediction lock does not precede first generation')
            timing = {'status': 'pass', 'locked_at': lock['locked_at'], 'first_request_at': first}
            write_frozen(OUT / 'forecast_timing_audit.json', json.dumps(timing, indent=2) + '\n')
            judge = OUT / 'judge'
            if not (judge / 'freeze.json').exists():
                write_state('preparing_blinded_coding', 'running')
                subprocess.run([sys.executable, str(ROOT / 'scripts/prepare_personality_judging_v2.py'),
                    '--mode', 'generation', '--generation-base', str(OUT), '--rubric', str(RUBRIC),
                    '--output-dir', str(judge), '--judges', 'MiniMax-M3', 'deepseek-v4-pro', 'glm-5.3'],
                    check=True, cwd=ROOT)
            lineage = audit_lineage(OUT, judge, RUBRIC)
            (OUT / 'judge_lineage_audit.json').write_text(json.dumps(lineage, indent=2) + '\n')
            current = judge / 'run'
            for repair in range(3):
                api_pass('coding_pass_' + str(repair), judge / 'manifest.jsonl', current, 0.0, 16384)
                verify_coder_identities(judge, current)
                diagnostics = OUT / 'measurement_diagnostics' / ('pass' + str(repair))
                analyze(judge, current, diagnostics, RUBRIC)
                report = json.loads((diagnostics / 'summary.json').read_text())
                if not report['invalid_or_missing']:
                    break
                if repair == 2:
                    raise ValueError('Coding exhausted fixed structural-repair limit')
                target = judge / ('run_repair' + str(repair + 1))
                if not target.exists():
                    if report['valid_judge_requests'] == 0:
                        raise ValueError('No valid coders; audit systemic failure before more calls')
                    seed(current, judge, target, RUBRIC, allow_incomplete_source=True)
                current = target
            selection = {'status': 'complete cue-transfer measurement', 'completed_at': now(),
                         'final_run': str(current.relative_to(ROOT)), 'diagnostics': str(diagnostics.relative_to(ROOT)),
                         'coverage_sha256': sha(diagnostics / 'coverage.csv'),
                         'valid_judge_requests': report['valid_judge_requests'],
                         'original_and_repair_runs_retained': True}
            (OUT / 'measurement_selection.json').write_text(json.dumps(selection, indent=2) + '\n')
            verify_files(lock['files'])
            write_state('locked_forecast_analysis', 'running')
            subprocess.run([sys.executable, str(ROOT / 'scripts/analyze_personality_cue_transfer_v4.py'),
                            '--diagnostics', str(diagnostics)], check=True, cwd=ROOT)
            write_state('cue_transfer_calculations_complete', 'complete',
                        scientific_synthesis_complete=False, archive_bridge_complete=False)
        except Exception as exc:
            write_state('stopped_for_review', 'failed', error=type(exc).__name__ + ': ' + str(exc)[:220])
            raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-only', action='store_true')
    main(parser.parse_args().check_only)
