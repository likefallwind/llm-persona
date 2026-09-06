#!/usr/bin/env python3
"""Recover an interrupted first training-code pass using its two repair passes.

The original run remains immutable. This is a one-time recovery entry point,
not a restart loop: an already-started repair directory requires review.
"""
import fcntl
import hashlib
import json
from pathlib import Path

from finish_personality_training_v3 import BASE, ROOT, TRAIN, LOGS, state, run
from run_personality_formal_stage_v3 import validate_stage, verify_files
from run_personality_requests_v2 import now


def main():
    LOGS.mkdir(parents=True, exist_ok=True)
    with (TRAIN / 'run/training_pipeline.lock').open('a+') as pipeline_lock:
        fcntl.flock(pipeline_lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        policy = json.loads((BASE / 'training_execution_policy.json').read_text())
        verify_files(policy['files'])
        validate_stage('training')
        judge = TRAIN / 'judge/v2_2'
        original = judge / 'run'
        rubric = ROOT / 'data/educational_personality_measurement_v2_2.json'
        if (original / 'summary.json').exists() or (TRAIN / 'measurement_selection.json').exists():
            raise ValueError('This recovery is only for the interrupted first coding pass')
        if any((judge / f'run_repair{i}').exists() for i in [1, 2]):
            raise ValueError('A repair directory already exists; do not reset repair budgets')
        if json.loads((TRAIN / 'run/summary.json').read_text())['run_status'] != 'complete':
            raise ValueError('Training generation must already be complete')
        with (original / 'writer.lock').open('r') as original_lock:
            fcntl.flock(original_lock.fileno(), fcntl.LOCK_SH | fcntl.LOCK_NB)
            try:
                state('recovering_interrupted_first_coding_pass', status='running')
                run('generation_audit_after_interruption', 'audit_personality_generation_v2.py', '--base', TRAIN)
                diagnostics = TRAIN / 'measurement_diagnostics/pass0'
                run('judge_audit_0', 'analyze_personality_coding_v2.py', '--base', judge,
                    '--run', original, '--output', diagnostics, '--rubric', rubric)
                initial = json.loads((diagnostics / 'summary.json').read_text())
                receipt = {
                    'recorded_at': now(), 'reason': 'Original controller terminated before first coding pass completed.',
                    'source_run': str(original.relative_to(ROOT)),
                    'source_response_sha256': hashlib.sha256((original / 'responses.jsonl').read_bytes()).hexdigest(),
                    'valid_source_records': initial['valid_judge_requests'],
                    'missing_or_invalid_records': initial['invalid_or_missing'],
                    'remaining_repair_passes': [1, 2], 'rerun_first_pass': False,
                    'new_tutor_generations': 0, 'sampling_or_measurement_changes': False,
                    'limitation': 'Upstream work without a persisted completion at interruption is not counted as an observation.',
                    'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                }
                (TRAIN / 'run/interruption_recovery.json').write_text(json.dumps(receipt, indent=2) + '\n')
                current = original
                for repair in [1, 2]:
                    report = json.loads((diagnostics / 'summary.json').read_text())
                    if report['invalid_or_missing'] == 0:
                        break
                    target = judge / f'run_repair{repair}'
                    run(f'seed_repair_{repair}', 'seed_personality_judge_run_v2.py',
                        '--source-run', current, '--target-base', judge, '--target-run', target,
                        '--rubric', rubric, '--allow-incomplete-source')
                    verify_files(policy['files'])
                    run(f'judge_pass_{repair}', 'run_personality_requests_v2.py',
                        '--manifest', judge / 'manifest.jsonl', '--output-dir', target,
                        '--temperature', '0', '--max-tokens', '16384', '--timeout', '360',
                        '--retries', '2', '--allow-current-glm53', '--schedule', 'interleaved')
                    current = target
                    diagnostics = TRAIN / f'measurement_diagnostics/pass{repair}'
                    run(f'judge_audit_{repair}', 'analyze_personality_coding_v2.py', '--base', judge,
                        '--run', current, '--output', diagnostics, '--rubric', rubric)
                final = json.loads((diagnostics / 'summary.json').read_text())
                if final['invalid_or_missing'] or final['valid_judge_requests'] != 3840:
                    raise ValueError('Training coding remains incomplete after the two remaining repair passes')
                selection = dict(status='complete training measurement', final_run=str(current.relative_to(ROOT)),
                                 diagnostics=str(diagnostics.relative_to(ROOT)), completed_at=now(),
                                 coverage_sha256=hashlib.sha256((diagnostics / 'coverage.csv').read_bytes()).hexdigest(),
                                 original_and_repair_runs_retained=True,
                                 interruption_receipt='artifacts/educational_personality_v2/prospective_formal/training/run/interruption_recovery.json')
                (TRAIN / 'measurement_selection.json').write_text(json.dumps(selection, indent=2) + '\n')
                run('lock_predictions', 'lock_personality_predictions_v3.py', '--diagnostics', diagnostics,
                    '--judge-base', judge)
                run('verify_confirmation_gate', 'run_personality_formal_stage_v3.py',
                    '--stage', 'confirmation', '--check-only')
                state('training_measurement_and_prediction_lock_complete', status='complete', confirmation_started=False)
            except Exception as exc:
                state('stopped_for_review', status='failed', error=type(exc).__name__ + ': ' + str(exc)[:220])
                raise


if __name__ == '__main__':
    main()
