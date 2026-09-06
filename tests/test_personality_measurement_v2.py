import importlib.util
import json
from pathlib import Path
import sys

import pytest

SCRIPTS = Path(__file__).resolve().parents[1]/'scripts'


def module(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS/(name+'.py'))
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


runner = module('run_personality_requests_v2')
coding = module('analyze_personality_coding_v2')


def test_truncation_and_provider_error_are_not_success():
    response = {'choices': [{'message': {'content': 'A partial answer'}, 'finish_reason': 'length'}]}
    with pytest.raises(ValueError, match='finish_length'):
        runner.parse_response(response)
    response['choices'][0]['finish_reason'] = 'stop'
    response['base_resp'] = {'status_code': 1002}
    with pytest.raises(ValueError, match='provider_status_1002'):
        runner.parse_response(response)


def test_requested_and_reported_identity_are_not_conflated():
    parsed = runner.parse_response({'model': 'glm-5.3', 'choices': [
        {'message': {'content': '5', 'reasoning_content': 'private reasoning'}, 'finish_reason': 'stop'}]})
    assert parsed['returned_model'] == 'glm-5.3'
    assert parsed['response'] == '5'
    assert 'private reasoning' not in json.dumps(parsed)


def test_duplicate_jobs_cannot_silently_replace_a_repeat():
    job = {'request_id': 'repeat0', 'model': 'MiniMax-M3', 'messages': [{'role': 'user', 'content': 'Hi'}]}
    with pytest.raises(ValueError, match='duplicate'):
        runner.validate_jobs([job, job])


def test_coding_requires_exact_evidence_from_visible_answer():
    code = {'events': {'answer_reveal': {'present': 1, 'evidence': 'x = 4'}}}
    assert coding.parse_codes(json.dumps(code), 'The answer is x = 4.', ['answer_reveal']) == {'answer_reveal': 1}
    with pytest.raises(ValueError, match='exact response evidence'):
        coding.parse_codes(json.dumps(code), 'Please try the next step.', ['answer_reveal'])
    code['events']['answer_reveal']['present'] = 0
    with pytest.raises(ValueError, match='Negative event has evidence'):
        coding.parse_codes(json.dumps(code), 'The answer is x = 4.', ['answer_reveal'])


def test_duplicate_json_keys_and_missing_events_fail_closed():
    with pytest.raises(ValueError, match='Duplicate JSON key'):
        coding.parse_codes('{"events":{},"events":{}}', 'answer', [])
    with pytest.raises(ValueError, match='Missing or extra event'):
        coding.parse_codes('{"events":{}}', 'answer', ['answer_reveal'])


def test_all_negative_agreement_does_not_claim_positive_reliability():
    result = coding.pair_agreement([0, 0], [0, 0])
    assert result['agreement'] == 1
    assert result['positive_agreement'] is None
    assert result['negative_agreement'] == 1


def test_line_evidence_preserves_original_ids_and_rejects_blank_lines():
    answer = 'Try dividing by 2.\n\nx = 4.'
    code = {'events': {'answer_reveal': {'present': 1, 'evidence_lines': [3]}}}
    assert coding.parse_codes(json.dumps(code), answer, ['answer_reveal'], 'line_ids') == {'answer_reveal': 1}
    for invalid in ([2], [4], [0], [3, 3], ['3'], [], [True]):
        code['events']['answer_reveal']['evidence_lines'] = invalid
        with pytest.raises(ValueError):
            coding.parse_codes(json.dumps(code), answer, ['answer_reveal'], 'line_ids')


def test_negative_line_event_cannot_cite_support():
    code = {'events': {'answer_reveal': {'present': 0, 'evidence_lines': [1]}}}
    with pytest.raises(ValueError, match='Negative event has evidence'):
        coding.parse_codes(json.dumps(code), 'x = 4.', ['answer_reveal'], 'line_ids')


def test_interleaved_execution_obeys_provider_total_caps(tmp_path, monkeypatch):
    from collections import defaultdict
    import threading
    import time
    # Isolate the runtime lock directory from real API jobs.
    fake_script = tmp_path/'scripts/run_personality_requests_v2.py'
    fake_script.parent.mkdir(parents=True)
    fake_script.write_text('test execution identity')
    monkeypatch.setattr(runner, '__file__', str(fake_script))
    jobs = []
    for i in range(12):
        for model in ['MiniMax-M3', 'MiniMax-M2.7', 'deepseek-v4-pro', 'glm-5.2', 'doubao-seed-2.0-lite']:
            jobs.append({'request_id': f'{model}:{i}', 'model': model,
                         'messages': [{'role': 'user', 'content': 'synthetic prompt'}]})
    manifest = tmp_path/'jobs.jsonl'
    manifest.write_text(''.join(json.dumps(j)+'\n' for j in jobs))
    state, peak = defaultdict(int), defaultdict(int)
    lock = threading.Lock()
    overlapping_providers = []

    def request(job, *args):
        provider = runner.MODELS[job['model']]
        with lock:
            state[provider] += 1
            peak[provider] = max(peak[provider], state[provider])
            if state['minimax'] and state['gateway']:
                overlapping_providers.append(True)
        time.sleep(.02)
        with lock:
            state[provider] -= 1
        return {'request_id': job['request_id'], 'model': job['model'], 'response': 'complete', 'error': ''}

    monkeypatch.setattr(runner, 'request_one', request)
    output = tmp_path/'run'
    monkeypatch.setattr(sys, 'argv', ['runner', '--manifest', str(manifest), '--output-dir', str(output), '--schedule', 'interleaved'])
    runner.main()
    assert peak['minimax'] <= 4 and peak['gateway'] <= 8
    assert peak['minimax'] > 1 and peak['gateway'] > 1 and overlapping_providers
    assert json.loads((output/'summary.json').read_text())['completed'] == len(jobs)
    assert json.loads((output/'contract.json').read_text())['schedule'] == 'interleaved'
