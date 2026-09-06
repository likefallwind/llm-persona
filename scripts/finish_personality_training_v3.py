#!/usr/bin/env python3
"""Complete frozen training measurement and prediction locking after generation.

Waits on the live writer's OS lock, never starts a duplicate active generation.
Every failure remains in the original run. At most two extra repair passes reuse
all valid records under identical inputs; event labels never select retries.
"""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from run_personality_requests_v2 import now
from run_personality_formal_stage_v3 import ROOT,BASE,validate_stage,verify_files

TRAIN=BASE/'training'
LOGS=TRAIN/'run/pipeline_logs'
STATE=TRAIN/'run/pipeline_state.json'


def state(stage,**extra):
    value={'pipeline_pid':os.getpid(),'stage':stage,'updated_at':now(),**extra}
    temp=STATE.with_suffix('.tmp')
    temp.write_text(json.dumps(value,indent=2)+'\n')
    temp.replace(STATE)
    print(json.dumps(value),flush=True)


def run(name,script,*args):
    state(name,status='running')
    env=os.environ.copy()
    env['PYTHONDONTWRITEBYTECODE']='1'
    env['OPENBLAS_NUM_THREADS']='1'
    with (LOGS/(name+'.log')).open('a') as sink:
        result=subprocess.run([sys.executable,str(ROOT/'scripts'/script),*map(str,args)],cwd=ROOT,env=env,stdout=sink,stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError(f'{name} exited {result.returncode}; inspect its durable log')
    state(name,status='complete')


def wait_for_generation():
    path=TRAIN/'run/writer.lock'
    if not path.exists(): raise ValueError('No generation writer was started')
    start=time.monotonic()
    with path.open('a+') as lock:
        while True:
            try:
                fcntl.flock(lock.fileno(),fcntl.LOCK_SH|fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic()-start>14400: raise TimeoutError('Generation writer still held after four hours')
                state('waiting_for_existing_generation_writer',status='running')
                time.sleep(30)
        # Lock acquired only after the writer exits. An absent summary is a
        # terminal incomplete run, not permission to silently duplicate work.
        if not (TRAIN/'run/summary.json').exists():
            raise ValueError('Generation writer released without completion summary')


def main():
    LOGS.mkdir(parents=True,exist_ok=True)
    pipeline_lock=(TRAIN/'run/training_pipeline.lock').open('a+')
    fcntl.flock(pipeline_lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
    policy=json.loads((BASE/'training_execution_policy.json').read_text())
    verify_files(policy['files'])
    validate_stage('training')
    try:
        wait_for_generation()
        for repair in range(3):
            summary=json.loads((TRAIN/'run/summary.json').read_text())
            if summary['run_status']=='complete': break
            if repair==2: raise ValueError('Generation still incomplete after two additional identical-input passes')
            run(f'generation_repair_{repair+1}','run_personality_formal_stage_v3.py','--stage','training')
        run('generation_audit','audit_personality_generation_v2.py','--base',TRAIN)
        judge=TRAIN/'judge/v2_2'
        rubric=ROOT/'data/educational_personality_measurement_v2_2.json'
        run('prepare_judging','prepare_personality_judging_v2.py','--mode','generation','--generation-base',TRAIN,
            '--rubric',rubric,'--output-dir',judge,'--judges','MiniMax-M3','deepseek-v4-pro','glm-5.3')
        current=judge/'run'
        diagnostics=TRAIN/'measurement_diagnostics/pass0'
        for repair in range(3):
            run(f'judge_pass_{repair}','run_personality_requests_v2.py','--manifest',judge/'manifest.jsonl',
                '--output-dir',current,'--temperature','0','--max-tokens','16384','--timeout','360','--retries','2',
                '--allow-current-glm53','--schedule','interleaved')
            diagnostics=TRAIN/f'measurement_diagnostics/pass{repair}'
            run(f'judge_audit_{repair}','analyze_personality_coding_v2.py','--base',judge,'--run',current,
                '--output',diagnostics,'--rubric',rubric)
            report=json.loads((diagnostics/'summary.json').read_text())
            if report['invalid_or_missing']==0: break
            if repair==2: raise ValueError('Measurement still incomplete after two additional structural repair passes')
            target=judge/f'run_repair{repair+1}'
            run(f'seed_repair_{repair+1}','seed_personality_judge_run_v2.py','--source-run',current,
                '--target-base',judge,'--target-run',target,'--rubric',rubric,'--allow-incomplete-source')
            current=target
        selection={'status':'complete training measurement','final_run':str(current.relative_to(ROOT)),
                   'diagnostics':str(diagnostics.relative_to(ROOT)),'completed_at':now(),
                   'coverage_sha256':hashlib.sha256((diagnostics/'coverage.csv').read_bytes()).hexdigest(),
                   'original_and_repair_runs_retained':True}
        (TRAIN/'measurement_selection.json').write_text(json.dumps(selection,indent=2)+'\n')
        run('lock_predictions','lock_personality_predictions_v3.py','--diagnostics',diagnostics,'--judge-base',judge)
        run('verify_confirmation_gate','run_personality_formal_stage_v3.py','--stage','confirmation','--check-only')
        state('training_measurement_and_prediction_lock_complete',status='complete',confirmation_started=False)
    except Exception as exc:
        state('stopped_for_review',status='failed',error=type(exc).__name__+': '+str(exc)[:220])
        raise

if __name__=='__main__': main()
