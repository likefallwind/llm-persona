#!/usr/bin/env python3
"""Run the disclosed content supplement after the existing confirmation job."""
import fcntl
import json
import os
import subprocess
import sys
import time

from personality_content_sensitivity_v3 import BASE, ROOT, OUT, policy
from run_personality_requests_v2 import now


def state(stage, **extra):
    value={'pipeline_pid':os.getpid(),'stage':stage,'updated_at':now(),**extra}
    path=OUT/'pipeline_state.json'; temporary=path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value,indent=2)+'\n'); temporary.replace(path)
    print(json.dumps(value),flush=True)


def run(name, script, *args):
    state(name,status='running')
    env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1';env['OPENBLAS_NUM_THREADS']='1'
    with (OUT/'pipeline_logs'/f'{name}.log').open('a') as log:
        result=subprocess.run([sys.executable,str(ROOT/'scripts'/script),*map(str,args)],cwd=ROOT,
                              env=env,stdout=log,stderr=subprocess.STDOUT)
    if result.returncode: raise RuntimeError(f'{name} exited {result.returncode}; inspect its durable log')
    state(name,status='complete')


def wait_confirmation():
    path=BASE/'confirmation/run/confirmation_pipeline.lock'
    if not path.exists(): raise ValueError('No existing confirmation controller to wait for')
    with path.open('a+') as lock:
        while True:
            try:
                fcntl.flock(lock.fileno(),fcntl.LOCK_SH|fcntl.LOCK_NB)
                break
            except BlockingIOError:
                state('waiting_for_existing_confirmation_pipeline',status='running')
                time.sleep(30)
        report=json.loads((BASE/'confirmation/run/pipeline_state.json').read_text())
        if report.get('status')!='complete' or report.get('stage')!='confirmation_primary_and_robustness_calculations_complete':
            raise ValueError('Confirmation controller released before successful completion')


def main():
    (OUT/'pipeline_logs').mkdir(parents=True,exist_ok=True)
    lock=(OUT/'content_pipeline.lock').open('a+')
    fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
    policy()
    try:
        wait_confirmation(); policy()
        run('prepare_content_review','personality_content_sensitivity_v3.py','prepare')
        current=OUT/'run'
        for repair in range(3):
            run(f'content_pass_{repair}','run_personality_requests_v2.py','--manifest',OUT/'manifest.jsonl',
                '--output-dir',current,'--temperature','0','--max-tokens','16384',
                '--timeout','360','--retries','2','--schedule','interleaved')
            diagnostics=OUT/f'diagnostics/pass{repair}'
            run(f'content_audit_{repair}','personality_content_sensitivity_v3.py','audit','--run',current,'--output',diagnostics)
            report=json.loads((diagnostics/'summary.json').read_text())
            if report['invalid_or_missing']==0: break
            if repair==2: raise ValueError('Content measurement incomplete after fixed structural repair limit')
            target=OUT/f'run_repair{repair+1}'
            run(f'seed_content_repair_{repair+1}','personality_content_sensitivity_v3.py','seed','--run',current,'--output',target)
            current=target
        (OUT/'measurement_selection.json').write_text(json.dumps({'status':'complete secondary content coding',
            'diagnostics':str(diagnostics.relative_to(ROOT)),'final_run':str(current.relative_to(ROOT)),
            'completed_at':now(),'all_original_runs_retained':True},indent=2)+'\n')
        run('content_sensitivity_analysis','personality_content_sensitivity_v3.py','analyze','--diagnostics',diagnostics)
        state('content_sensitivity_complete',status='complete',paper_complete=False)
    except Exception as exc:
        state('stopped_for_review',status='failed',error=type(exc).__name__+': '+str(exc)[:220])
        raise


if __name__=='__main__':
    main()
