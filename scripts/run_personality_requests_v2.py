#!/usr/bin/env python3
"""Run an immutable public/synthetic request manifest against trusted endpoints.

No raw error bodies, credentials, or hidden reasoning are written. Visible
responses and mutable run state remain local under ignored run directories.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import time
import urllib.error
import urllib.request


ENDPOINTS = {
    'minimax': ('https://api.minimaxi.com/v1/text/chatcompletion_v2', 'MINIMAX_API_KEY', 4),
    'gateway': ('http://127.0.0.1:8111/v1/chat/completions', 'API_GATEWAY', 8),
}
MODELS = {'MiniMax-M3': 'minimax', 'MiniMax-M2.7': 'minimax',
          'glm-5.2': 'gateway', 'deepseek-v4-pro': 'gateway', 'doubao-seed-2.0-lite': 'gateway'}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def read_rows(path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def validate_jobs(jobs):
    if not jobs or len({j['request_id'] for j in jobs}) != len(jobs):
        raise ValueError('Empty manifest or duplicate request IDs')
    for job in jobs:
        if job['model'] not in MODELS:
            raise ValueError('Model is not in the authorized panel')
        if not job['messages'] or any(m['role'] not in ('system', 'user', 'assistant') for m in job['messages']):
            raise ValueError('Invalid messages')


def parse_response(data):
    base = data.get('base_resp', {})
    if base.get('status_code', 0) != 0:
        raise ValueError('provider_status_' + str(base.get('status_code')))
    choices = data.get('choices') or []
    if len(choices) != 1:
        raise ValueError('Expected one completion')
    choice = choices[0]
    content = choice.get('message', {}).get('content')
    if not isinstance(content, str) or not content.strip():
        raise ValueError('Empty visible completion')
    # A provider that embeds thinking in the visible field requires an explicit
    # adapter audit; do not accidentally send that text to behavioral judges.
    if '<think>' in content or '</think>' in content:
        raise ValueError('Embedded reasoning requires adapter review')
    finish = choice.get('finish_reason')
    if finish not in ('stop', 'end_turn'):
        raise ValueError('Unverified completion finish_' + str(finish))
    return {'response': content.strip(), 'response_sha256': digest(content.strip()),
            'returned_model': data.get('model'), 'provider_completion_id': data.get('id'),
            'finish_reason': finish, 'usage': data.get('usage', {})}


def request_one(job, temperature, max_tokens, timeout, retries):
    provider = MODELS[job['model']]
    url, key_name, _ = ENDPOINTS[provider]
    key = os.environ.get(key_name)
    if not key:
        raise ValueError('Missing credential environment variable ' + key_name)
    payload = {'model': job['model'], 'messages': job['messages'], 'temperature': temperature,
               'max_tokens': max_tokens, 'stream': False}
    start = time.monotonic()
    row = {'request_id': job['request_id'], 'model': job['model'], 'provider': provider,
           'endpoint': url, 'prompt_sha256': digest(job['messages']), 'payload_sha256': digest(payload),
           'temperature': temperature, 'max_tokens': max_tokens, 'seed': None,
           'seed_note': 'Not supplied; independent API requests, not guaranteed independent RNG streams.',
           'started_at': now(), 'response': '', 'error': ''}
    attempts = []
    for attempt in range(1, retries + 1):
        attempt_start = time.monotonic()
        attempt_usage, returned_model, finish_reason = {}, None, None
        req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                     headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
        try:
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
            with opener.open(req, timeout=timeout) as response:
                data = json.load(response)
            attempt_usage = data.get('usage', {})
            returned_model = data.get('model')
            choices = data.get('choices') or []
            finish_reason = choices[0].get('finish_reason') if choices else None
            row['usage'] = attempt_usage
            row['returned_model'] = returned_model
            row['finish_reason'] = finish_reason
            row.update(parse_response(data))
            row['error'] = ''
            attempts.append({'attempt': attempt, 'status': 'complete', 'usage': attempt_usage,
                             'returned_model': returned_model, 'finish_reason': finish_reason,
                             'elapsed_seconds': round(time.monotonic()-attempt_start, 3)})
            break
        except urllib.error.HTTPError as exc:
            row['error'] = 'http_' + str(exc.code)
        except ValueError as exc:
            row['error'] = 'invalid_completion_' + str(exc)[:120]
        except Exception as exc:
            row['error'] = type(exc).__name__
        attempts.append({'attempt': attempt, 'status': row['error'], 'usage': attempt_usage,
                         'returned_model': returned_model, 'finish_reason': finish_reason,
                         'elapsed_seconds': round(time.monotonic()-attempt_start, 3)})
        if attempt < retries:
            time.sleep(min(5, attempt))
    row.update(attempts=attempts, completed_at=now(), elapsed_seconds=round(time.monotonic()-start, 3))
    return row


def main():
    script_sha256_at_start = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--temperature', type=float, default=.7)
    parser.add_argument('--max-tokens', type=int, default=8192)
    parser.add_argument('--timeout', type=int, default=240)
    parser.add_argument('--retries', type=int, default=2)
    parser.add_argument('--allow-current-glm53', action='store_true',
                        help='Explicitly enable the separately audited current GLM-5.3 deployment.')
    parser.add_argument('--schedule', choices=['model_blocks', 'interleaved'], default='model_blocks')
    args = parser.parse_args()
    if args.allow_current_glm53:
        MODELS['glm-5.3'] = 'gateway'
    jobs = read_rows(args.manifest)
    validate_jobs(jobs)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    lock = (args.output_dir/'writer.lock').open('a+')
    fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    # Enforce the repository-wide provider cap for this runner across output dirs.
    provider_locks = []
    root = Path(__file__).resolve().parents[1]/'artifacts/educational_personality_v2/runtime'
    root.mkdir(parents=True, exist_ok=True)
    for provider in sorted({MODELS[j['model']] for j in jobs}):
        handle = (root/(provider+'.lock')).open('a+')
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        provider_locks.append(handle)
    contract = {'manifest_sha256': hashlib.sha256(args.manifest.read_bytes()).hexdigest(),
                'temperature': args.temperature, 'max_tokens': args.max_tokens, 'endpoints': ENDPOINTS,
                'models': MODELS, 'stream': False, 'seed': None}
    if args.schedule != 'model_blocks':
        contract['schedule'] = args.schedule
    contract_path = args.output_dir/'contract.json'
    normalized = json.loads(json.dumps(contract))
    if contract_path.exists() and json.loads(contract_path.read_text()) != normalized:
        raise ValueError('Run contract changed; use a separate output directory')
    contract_path.write_text(json.dumps(contract, indent=2)+'\n')
    output = args.output_dir/'responses.jsonl'
    latest = {r['request_id']: r for r in read_rows(output)}
    done = {k for k, r in latest.items() if r.get('response') and not r.get('error')}
    completed_before_execution = len(done & {j['request_id'] for j in jobs})
    attempts_this_execution = 0
    # In block mode models run serially. Interleaved mode uses one pool per
    # provider, shared across all its models, so 4 and 8 remain provider totals.
    with output.open('a') as sink:
        def save(row):
            nonlocal attempts_this_execution
            attempts_this_execution += len(row.get('attempts', []))
            sink.write(json.dumps(row, ensure_ascii=False)+'\n'); sink.flush()
            os.fsync(sink.fileno())
            latest[row['request_id']] = row
            print(json.dumps({'request_id': row['request_id'], 'ok': not bool(row['error']),
                              'error': row['error']}), flush=True)

        if args.schedule == 'interleaved':
            from contextlib import ExitStack
            with ExitStack() as stack:
                pools = {provider: stack.enter_context(ThreadPoolExecutor(max_workers=ENDPOINTS[provider][2]))
                         for provider in sorted({MODELS[j['model']] for j in jobs})}
                pending = [j for j in jobs if j['request_id'] not in done]
                # Manifest ordering is already randomized before the freeze.
                futures = [pools[MODELS[j['model']]].submit(request_one, j, args.temperature,
                           args.max_tokens, args.timeout, args.retries) for j in pending]
                for future in as_completed(futures):
                    save(future.result())
        for model in sorted({j['model'] for j in jobs}):
            if args.schedule != 'model_blocks':
                break
            pending = [j for j in jobs if j['model'] == model and j['request_id'] not in done]
            workers = ENDPOINTS[MODELS[model]][2]
            with ThreadPoolExecutor(max_workers=workers) as pool:
                futures = [pool.submit(request_one, j, args.temperature, args.max_tokens, args.timeout, args.retries) for j in pending]
                for future in as_completed(futures):
                    save(future.result())
    completed = sum(bool(latest.get(j['request_id'], {}).get('response')) and
                    not latest[j['request_id']].get('error') for j in jobs)
    summary = {'run_status': 'complete' if completed == len(jobs) else 'incomplete',
               'expected': len(jobs), 'completed': completed, 'updated_at': now(),
               'completed_before_execution': completed_before_execution,
               'completed_this_execution': completed-completed_before_execution,
               'http_attempts_this_execution': attempts_this_execution,
               'contract_sha256': digest(contract), 'script_sha256': script_sha256_at_start}
    (args.output_dir/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    print(json.dumps(summary), flush=True)


if __name__ == '__main__':
    main()
