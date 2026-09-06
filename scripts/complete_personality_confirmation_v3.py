#!/usr/bin/env python3
"""Continue the authorized frozen study after its existing training pipeline.

No outcome-dependent stopping or case replacement. New-source generation starts
only after main and sensitivity forecasts have been locked and verified.
"""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from run_personality_formal_stage_v3 import ROOT,BASE,validate_stage,verify_files
from run_personality_requests_v2 import now,read_rows

STAGE=BASE/'confirmation'
LOGS=STAGE/'run/pipeline_logs'
STATE=STAGE/'run/pipeline_state.json'


def state(stage,**extra):
    value={'pipeline_pid':os.getpid(),'stage':stage,'updated_at':now(),**extra}
    temporary=STATE.with_suffix('.tmp')
    temporary.write_text(json.dumps(value,indent=2)+'\n')
    temporary.replace(STATE)
    print(json.dumps(value),flush=True)


def run(name,script,*args):
    state(name,status='running')
    env=os.environ.copy()
    env['PYTHONDONTWRITEBYTECODE']='1'
    env['OPENBLAS_NUM_THREADS']='1'
    with (LOGS/(name+'.log')).open('a') as log:
        completed=subprocess.run([sys.executable,str(ROOT/'scripts'/script),*map(str,args)],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
    if completed.returncode: raise RuntimeError(f'{name} exited {completed.returncode}; inspect its durable log')
    state(name,status='complete')


def wait_training():
    path=BASE/'training/run/training_pipeline.lock'
    if not path.exists(): raise ValueError('No existing training pipeline to wait for')
    deadline=time.monotonic()+86400
    with path.open('a+') as lock:
        while True:
            try:
                fcntl.flock(lock.fileno(),fcntl.LOCK_SH|fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic()>deadline: raise TimeoutError('Training pipeline still held after 24 hours')
                state('waiting_for_existing_training_pipeline',status='running')
                time.sleep(30)
        report=json.loads((BASE/'training/run/pipeline_state.json').read_text())
        if report.get('status')!='complete' or report.get('stage')!='training_measurement_and_prediction_lock_complete':
            raise ValueError('Training pipeline released before successful completion: '+str(report.get('error',report.get('stage'))))
    validate_stage('confirmation')


def main():
    LOGS.mkdir(parents=True,exist_ok=True)
    lock=(STAGE/'run/confirmation_pipeline.lock').open('a+')
    fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
    policy=json.loads((BASE/'confirmation_execution_policy.json').read_text())
    verify_files(policy['files'])
    try:
        wait_training()
        train_judge=BASE/'training/judge/v2_2'
        run('verify_training_lineage','audit_personality_judge_lineage_v3.py','--generation-base',BASE/'training',
            '--judge-base',train_judge,'--output',BASE/'training/judge_lineage_audit.json')
        for name,filename,script in [
            ('lock_judge_sensitivities','judge_sensitivity_lock.json','lock_personality_judge_sensitivity_v3.py'),
            ('lock_generator_deletions','generator_deletion_lock.json','lock_personality_generator_deletion_v3.py')]:
            if not (BASE/filename).exists(): run(name,script)
            verify_files(json.loads((BASE/filename).read_text())['files'])
        # Verify the extension scripts before any confirmation calls, even if
        # training took many hours and the working tree could have changed.
        verify_files(policy['files'])
        validate_stage('confirmation')
        state('all_forecasts_verified_before_confirmation',status='complete')
        summary_path=STAGE/'run/summary.json'
        for attempt in range(3):
            if summary_path.exists() and json.loads(summary_path.read_text())['run_status']=='complete': break
            run(f'generation_pass_{attempt}','run_personality_formal_stage_v3.py','--stage','confirmation')
        if json.loads(summary_path.read_text())['run_status']!='complete':
            raise ValueError('Confirmation generation incomplete after fixed repair limit')
        run('generation_audit','audit_personality_generation_v2.py','--base',STAGE)
        generation=read_rows(STAGE/'run/responses.jsonl')
        first=min(r['started_at'] for r in generation)
        times={name:json.loads((BASE/name).read_text())['locked_at'] for name in
               ['prediction_lock.json','judge_sensitivity_lock.json','generator_deletion_lock.json']}
        if not all(value<first for value in times.values()):
            raise ValueError('A forecast lock does not precede confirmation generation')
        (STAGE/'forecast_timing_audit.json').write_text(json.dumps({'status':'pass','first_confirmation_request':first,
                                                                   'forecast_locks':times},indent=2)+'\n')
        judge=STAGE/'judge/v2_2'
        rubric=ROOT/'data/educational_personality_measurement_v2_2.json'
        run('prepare_judging','prepare_personality_judging_v2.py','--mode','generation','--generation-base',STAGE,
            '--rubric',rubric,'--output-dir',judge,'--judges','MiniMax-M3','deepseek-v4-pro','glm-5.3')
        run('verify_judge_lineage','audit_personality_judge_lineage_v3.py','--generation-base',STAGE,
            '--judge-base',judge,'--output',STAGE/'judge_lineage_audit.json')
        current=judge/'run'
        diagnostics=None
        for repair in range(3):
            run(f'judge_pass_{repair}','run_personality_requests_v2.py','--manifest',judge/'manifest.jsonl',
                '--output-dir',current,'--temperature','0','--max-tokens','16384','--timeout','360','--retries','2',
                '--allow-current-glm53','--schedule','interleaved')
            diagnostics=STAGE/f'measurement_diagnostics/pass{repair}'
            run(f'judge_audit_{repair}','analyze_personality_coding_v2.py','--base',judge,'--run',current,
                '--output',diagnostics,'--rubric',rubric)
            report=json.loads((diagnostics/'summary.json').read_text())
            if report['invalid_or_missing']==0: break
            if repair==2: raise ValueError('Confirmation measurement incomplete after fixed structural repair limit')
            target=judge/f'run_repair{repair+1}'
            run(f'seed_repair_{repair+1}','seed_personality_judge_run_v2.py','--source-run',current,
                '--target-base',judge,'--target-run',target,'--rubric',rubric,'--allow-incomplete-source')
            current=target
        (STAGE/'measurement_selection.json').write_text(json.dumps({'status':'complete confirmation measurement',
            'final_run':str(current.relative_to(ROOT)),'diagnostics':str(diagnostics.relative_to(ROOT)),
            'completed_at':now(),'coverage_sha256':hashlib.sha256((diagnostics/'coverage.csv').read_bytes()).hexdigest(),
            'original_and_repair_runs_retained':True},indent=2)+'\n')
        verify_files(policy['files'])
        run('primary_confirmation_analysis','analyze_personality_confirmation_v3.py','--diagnostics',diagnostics)
        run('confirmation_robustness','analyze_personality_robustness_v3.py','--diagnostics',diagnostics,'--training-resamples','200')
        state('confirmation_primary_and_robustness_calculations_complete',status='complete',
              scientific_synthesis_complete=False,paper_complete=False)
    except Exception as exc:
        state('stopped_for_review',status='failed',error=type(exc).__name__+': '+str(exc)[:220])
        raise

if __name__=='__main__': main()
