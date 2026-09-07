"""Exercise the serialization boundary with a response from the actual runner."""
import io
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import personality_content_sensitivity_v3 as original
import recover_personality_content_validation_v3 as recovery
import run_personality_requests_v2 as runner


def run_synthetic(monkeypatch):
    job = {'request_id': 'synthetic', 'model': 'MiniMax-M3',
           'messages': [{'role': 'user', 'content': 'Synthetic content review.'}]}
    verdict = {'verdict': 'no_clear_error', 'error_types': [], 'evidence_lines': [],
               'explanation': 'No clear error in this synthetic example.'}
    completion = {'model': job['model'], 'id': 'synthetic',
                  'choices': [{'finish_reason': 'stop', 'message': {'content': json.dumps(verdict)}}]}
    transmitted = []
    class Opener:
        def open(self, request, timeout):
            transmitted.append(json.loads(request.data))
            return io.StringIO(json.dumps(completion))
    monkeypatch.setenv('MINIMAX_API_KEY', 'synthetic-test-only')
    monkeypatch.setattr(runner.urllib.request, 'build_opener', lambda *args: Opener())
    row = runner.request_one(job, temperature=0.0, max_tokens=16384, timeout=1, retries=1)
    return job, row, {'response': 'The answer is four.'}, transmitted


def test_real_runner_float_zero_is_valid_and_original_hash_bug_is_reproduced(monkeypatch):
    job, row, item, transmitted = run_synthetic(monkeypatch)
    assert type(transmitted[0]['temperature']) is float
    assert row['payload_sha256'] == runner.digest(transmitted[0])
    with pytest.raises(ValueError, match='hash differs'):
        original.validate_result(job, row, item)
    assert recovery.validate_result(job, row, item)['verdict'] == 'no_clear_error'


@pytest.mark.parametrize('change', [
    {'temperature': .1}, {'temperature': False}, {'max_tokens': 32768},
    {'returned_model': 'different'}, {'finish_reason': 'length'},
    {'prompt_sha256': 'tampered'}, {'payload_sha256': 'tampered'},
    {'response_sha256': 'tampered'},
])
def test_other_integrity_checks_are_not_relaxed(monkeypatch, change):
    job, row, item, _ = run_synthetic(monkeypatch)
    with pytest.raises(ValueError):
        recovery.validate_result(job, {**row, **change}, item)


def test_structurally_invalid_evidence_is_still_rejected(monkeypatch):
    job, row, item, _ = run_synthetic(monkeypatch)
    response = json.dumps({'verdict': 'clear_error', 'error_types': ['wrong_final_answer'],
                           'evidence_lines': [999], 'explanation': 'Invalid line.'})
    row.update(response=response, response_sha256=runner.digest(response))
    with pytest.raises(ValueError, match='Evidence'):
        recovery.validate_result(job, row, item)
