"""One identical-payload diagnostic attempt for each of two failed archive codes."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import urllib.error
import urllib.request

import pandas as pd

from analyze_personality_coding_v2 import analyze
from prepare_archive_behavior_validation_v4 import BASE, ROOT, RUBRIC
from run_personality_formal_stage_v3 import verify_files
from run_personality_requests_v2 import now, read_rows, request_one
from seed_personality_judge_run_v2 import seed

IDS = {'97c495a4d4eb3b96b91b:deepseek-v4-pro', '5fb91d284325462763d5:deepseek-v4-pro'}
OUT = BASE / 'judge/transport_diagnostic_run'
NOTE = ROOT / 'research/85_archive_transport_diagnostic_amendment_v4.md'


def main():
    verify_files(json.loads((BASE / 'design_freeze.json').read_text())['files'])
    coverage = pd.read_csv(BASE / 'measurement_diagnostics/pass2/coverage.csv')
    bad = coverage.loc[~coverage.valid]
    assert set(bad.request_id) == IDS and set(bad.error) == {'http_400'}
    assert len(coverage) == 10752 and int(coverage.valid.sum()) == 10750
    assert os.environ.get('API_GATEWAY'), 'Missing Gateway credential'
    provider_lock = (ROOT / 'artifacts/educational_personality_v2/runtime/gateway.lock').open('a+')
    fcntl.flock(provider_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    OUT.mkdir(exist_ok=True)
    # An exclusive start marker prevents accidental allowance resets on rerun.
    with (OUT / 'started.json').open('x') as f:
        json.dump({'started_at': now(), 'request_ids': sorted(IDS), 'max_new_http_attempts': 2,
                   'amendment_sha256': hashlib.sha256(NOTE.read_bytes()).hexdigest(),
                   'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}, f, indent=2)
    seed(BASE / 'judge/run_repair2', BASE / 'judge', OUT, RUBRIC, allow_incomplete_source=True)
    assert len(read_rows(OUT / 'responses.jsonl')) == 10750
    jobs = [j for j in read_rows(BASE / 'judge/manifest.jsonl') if j['request_id'] in IDS]
    assert len(jobs) == 2 and all(j['model'] == 'deepseek-v4-pro' for j in jobs)
    original_open = urllib.request.OpenerDirector.open
    active_id = None

    def capture_error(opener, *args, **kwargs):
        try:
            return original_open(opener, *args, **kwargs)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode('utf-8', errors='replace')
            with (OUT / 'provider_errors.jsonl').open('a') as f:
                f.write(json.dumps({'request_id': active_id, 'at': now(), 'http_status': exc.code,
                                    'body': body}, ensure_ascii=False) + '\n')
            raise

    urllib.request.OpenerDirector.open = capture_error
    try:
        for job in jobs:
            active_id = job['request_id']
            row = request_one(job, 0.0, 32768, 660, 1)
            with (OUT / 'responses.jsonl').open('a') as f:
                f.write(json.dumps(row, ensure_ascii=False) + '\n')
                f.flush()
                os.fsync(f.fileno())
            print(json.dumps({'request_id': active_id, 'error': row['error']}), flush=True)
    finally:
        urllib.request.OpenerDirector.open = original_open
    diagnostics = BASE / 'measurement_diagnostics/transport_diagnostic'
    analyze(BASE / 'judge', OUT, diagnostics, RUBRIC)
    summary = json.loads((diagnostics / 'summary.json').read_text())
    result = {'completed_at': now(), 'valid_judge_requests': summary['valid_judge_requests'],
              'invalid_or_missing': summary['invalid_or_missing'], 'new_http_attempts': 2,
              'research_quality_goal_complete': False}
    (OUT / 'finished.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
