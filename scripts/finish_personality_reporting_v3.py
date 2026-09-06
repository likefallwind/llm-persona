#!/usr/bin/env python3
"""Run the existing local reporting supplements after successful confirmation.

This controller adds no API calls, statistical rules, or manuscript claims.
Content-review completion and final scientific/visual review remain separate.
"""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from run_personality_formal_stage_v3 import BASE, ROOT, verify_files
from run_personality_requests_v2 import now

OUT = BASE / 'confirmation_reporting'
SCRIPTS = (
    'describe_personality_confirmation_v3.py',
    'audit_personality_inference_edges_v3.py',
    'audit_personality_neutral_bounds_v3.py',
    'plot_personality_confirmation_v3.py',
)


def write_json(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.replace(path)


def state(stage, status='running', **extra):
    value = dict(pipeline_pid=os.getpid(), stage=stage, status=status,
                 updated_at=now(), **extra)
    write_json(OUT / 'run/pipeline_state.json', value)
    print(json.dumps(value), flush=True)


def main():
    (OUT / 'run/logs').mkdir(parents=True, exist_ok=True)
    with (OUT / 'run/reporting_pipeline.lock').open('a+') as own_lock:
        fcntl.flock(own_lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        paths = [ROOT / 'scripts' / name for name in SCRIPTS] + [Path(__file__).resolve()]
        files = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in paths}
        inputs = OUT / 'run/execution_inputs.json'
        if inputs.exists():
            verify_files(json.loads(inputs.read_text())['files'])
        else:
            write_json(inputs, dict(recorded_at=now(), files=files,
                                    new_api_calls=0, new_statistical_rules=0))
        try:
            dependency = BASE / 'confirmation/run'
            lock_path = dependency / 'confirmation_pipeline.lock'
            if not lock_path.exists():
                raise ValueError('No existing confirmation controller to wait for')
            with lock_path.open('r') as dependency_lock:
                while True:
                    try:
                        fcntl.flock(dependency_lock.fileno(), fcntl.LOCK_SH | fcntl.LOCK_NB)
                        break
                    except BlockingIOError:
                        state('waiting_for_existing_confirmation_pipeline')
                        time.sleep(30)
                completion = json.loads((dependency / 'pipeline_state.json').read_text())
                if (completion.get('status') != 'complete' or completion.get('stage') !=
                        'confirmation_primary_and_robustness_calculations_complete'):
                    raise ValueError('Confirmation released before successful completion')
                selection = json.loads((BASE / 'confirmation/measurement_selection.json').read_text())
                diagnostics = ROOT / selection['diagnostics']
                env = os.environ.copy()
                env.update(PYTHONDONTWRITEBYTECODE='1', OPENBLAS_NUM_THREADS='1',
                           MPLBACKEND='Agg', MPLCONFIGDIR='/tmp/personality_reporting_mpl')
                for name in SCRIPTS:
                    verify_files(files)
                    state(name)
                    args = ['--diagnostics', str(diagnostics)] if name == SCRIPTS[0] else []
                    with (OUT / 'run/logs' / (name + '.log')).open('a') as log:
                        result = subprocess.run([sys.executable, str(ROOT / 'scripts' / name), *args],
                                                cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
                    if result.returncode:
                        raise RuntimeError(f'{name} exited {result.returncode}; inspect durable log')
                reports = [BASE / folder / 'summary.json' for folder in
                           ['confirmation_descriptive', 'confirmation_inference_edges',
                            'confirmation_neutral_bounds']]
                reports.append(ROOT / 'paper/educational_personality_v3/figures/confirmation_figures_provenance.json')
                output_hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in reports}
                write_json(OUT / 'summary.json', dict(
                    status='local reporting supplements complete; scientific and visual review required',
                    completed_at=now(), scripts=files, report_hashes=output_hashes,
                    content_review_completion_required=True, paper_complete=False, new_api_calls=0))
                state('local_reporting_supplements_complete', status='complete', paper_complete=False)
        except Exception as exc:
            state('stopped_for_review', status='failed', error=type(exc).__name__ + ': ' + str(exc)[:220])
            raise


if __name__ == '__main__':
    main()
