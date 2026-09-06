"""Budget groups cannot silently replace valid codes or manufacture coverage."""
import sys
import json
import hashlib
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from complete_personality_training_budget_recovery_v3 import combine_validated
from analyze_personality_coding_v2 import analyze
from run_personality_requests_v2 import digest


def fixture():
    jobs = [{'request_id': f'x:{j}', 'blind_id': 'x', 'model': j} for j in ['a', 'b', 'c']]
    old_cov = pd.DataFrame([{'request_id': j['request_id'], 'valid': j['model'] != 'c'} for j in jobs])
    extra_cov = pd.DataFrame([{'request_id': 'x:c', 'valid': True}])
    def code(j, value):
        return {'blind_id': 'x', 'judge_requested': j, 'judge_returned': j, 'event': 'e', 'present': value}
    old = pd.DataFrame([code('a', 1), code('b', 0)])
    extra = pd.DataFrame([code('c', 1)])
    return [jobs, {'x': {'model': 'tutor'}}, ['e'], old_cov, old, extra_cov, extra, ['x:c']]


def test_exact_partition_reconstructs_majority_and_disagreement():
    coverage, codes, consensus, agreement, identities = combine_validated(*fixture())
    assert len(coverage) == len(codes) == 3
    assert consensus.iloc[0]['present'] == 1 and consensus.iloc[0]['unanimous'] == 0
    assert len(agreement) == 3 and identities['c'] == ['c']


@pytest.mark.parametrize('kind', ['replace_valid', 'missing_event', 'duplicate_event', 'invalid_extra', 'wrong_identity'])
def test_rejects_unvalidated_or_overlapping_merge(kind):
    args = fixture()
    if kind == 'replace_valid': args[5].loc[0, 'request_id'] = 'x:a'
    if kind == 'missing_event': args[6] = args[6].iloc[:0]
    if kind == 'duplicate_event': args[6] = pd.concat([args[6], args[6]])
    if kind == 'invalid_extra': args[5].loc[0, 'valid'] = False
    if kind == 'wrong_identity': args[6].loc[0, 'judge_returned'] = 'different'
    with pytest.raises(ValueError): combine_validated(*args)


def test_separate_budget_audits_match_frozen_consensus_and_reject_wrong_budget(tmp_path):
    rubric = tmp_path / 'rubric.json'
    rubric.write_text(json.dumps({'events': {'e': {}}, 'evidence_format': 'line_ids'}))
    item = {'blind_id': 'x', 'response': 'Answer is 4.', 'model': 'tutor', 'template': 't',
            'progress': 'wrong_attempt', 'affect': 'calm', 'repeat': 0}
    jobs = [{'request_id': 'x:' + j, 'blind_id': 'x', 'model': j,
             'messages': [{'role': 'user', 'content': 'synthetic'}]} for j in ['a', 'b', 'c']]

    def base(name, subset, budget):
        path = tmp_path / name
        path.mkdir()
        (path / 'manifest.jsonl').write_text(''.join(json.dumps(j) + '\n' for j in subset))
        (path / 'unblinding.jsonl').write_text(json.dumps(item) + '\n')
        (path / 'freeze.json').write_text(json.dumps({'mode': 'generation', 'temperature': 0, 'max_tokens': budget,
            'rubric_sha256': hashlib.sha256(rubric.read_bytes()).hexdigest(),
            'manifest_sha256': hashlib.sha256((path / 'manifest.jsonl').read_bytes()).hexdigest()}))
        return path

    def response(job, budget):
        positive = job['model'] != 'b'
        answer = json.dumps({'events': {'e': {'present': int(positive), 'evidence_lines': [1] if positive else []}}})
        payload = {'model': job['model'], 'messages': job['messages'], 'temperature': 0, 'max_tokens': budget, 'stream': False}
        return {'request_id': job['request_id'], 'returned_model': job['model'], 'response': answer,
                'response_sha256': digest(answer), 'prompt_sha256': digest(job['messages']),
                'payload_sha256': digest(payload), 'temperature': 0, 'max_tokens': budget, 'finish_reason': 'stop'}

    original = base('original', jobs, 16384)
    expanded = base('expanded', jobs[2:], 32768)
    (original / 'responses.jsonl').write_text(''.join(json.dumps(response(j, 16384)) + '\n' for j in jobs[:2]))
    (expanded / 'responses.jsonl').write_text(json.dumps(response(jobs[2], 32768)) + '\n')
    analyze(original, original, tmp_path / 'old', rubric)
    analyze(expanded, expanded, tmp_path / 'extra', rubric)
    read = lambda part, name: pd.read_csv(tmp_path / part / (name + '.csv'))
    result = combine_validated(jobs, {'x': item}, ['e'], read('old', 'coverage'), read('old', 'event_codes'),
                               read('extra', 'coverage'), read('extra', 'event_codes'), ['x:c'])
    # Counterfactual reference checks the unchanged consensus algorithm, not an
    # empirical claim about what either budget would have generated.
    reference = base('reference', jobs, 16384)
    (reference / 'responses.jsonl').write_text(''.join(json.dumps(response(j, 16384)) + '\n' for j in jobs))
    analyze(reference, reference, tmp_path / 'ref', rubric)
    pd.testing.assert_frame_equal(result[2], read('ref', 'consensus'))
    pd.testing.assert_frame_equal(result[3], read('ref', 'pairwise_agreement'))
    # An expanded-budget output under the original freeze must fail, even when
    # its JSON, evidence and content are otherwise identical.
    (original / 'responses.jsonl').write_text(json.dumps(response(jobs[2], 32768)) + '\n')
    analyze(original, original, tmp_path / 'wrong_budget', rubric)
    row = read('wrong_budget', 'coverage').set_index('request_id').loc['x:c']
    assert not row['valid'] and row['error'] == 'sampling_parameters_differ_from_freeze'
