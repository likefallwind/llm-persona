"""Saved retries and cache copies have different accounting semantics."""
import copy
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from summarize_personality_resources_v3 import account


def row():
    return {'provider': 'gateway', 'endpoint': 'synthetic', 'model': 'test', 'request_id': 'id',
            'payload_sha256': 'input', 'started_at': 'start', 'completed_at': 'end', 'max_tokens': 100,
            'usage': {'total_tokens': 9999},
            'attempts': [{'attempt': 1, 'status': 'length', 'usage': {'prompt_tokens': 2, 'completion_tokens': 3, 'total_tokens': 5}},
                         {'attempt': 2, 'status': 'complete', 'usage': {'prompt_tokens': 2, 'completion_tokens': 4, 'total_tokens': 6}}]}


def test_reused_row_counted_once_and_both_http_attempts_retained():
    value = row()
    frame, copies = account([(Path('prospective_formal/training/judge/run/responses.jsonl'), [value]),
                             (Path('prospective_formal/training/judge/run_repair1/responses.jsonl'), [copy.deepcopy(value)])])
    assert copies == 1 and len(frame) == 1
    assert frame.iloc[0].saved_attempts == 2 and frame.iloc[0].reported_total_tokens == 11
    assert frame.iloc[0].failed_attempts == 1


def test_separate_retry_execution_is_not_a_cache_copy():
    value, new = row(), row()
    new['started_at'] = 'later'
    frame, copies = account([(Path('prospective_formal/training/judge/run/responses.jsonl'), [value, new])])
    assert copies == 0 and len(frame) == 2 and frame.saved_attempts.sum() == 4


def test_conflicting_copies_fail_closed():
    value, changed = row(), row()
    changed['attempts'][0]['usage']['total_tokens'] = 8
    with pytest.raises(ValueError, match='Conflicting'):
        account([(Path('prospective_formal/training/judge/run/responses.jsonl'), [value, changed])])


def test_missing_usage_remains_explicit():
    value = row()
    value['attempts'][0]['usage'] = None
    frame, _ = account([(Path('prospective_formal/training/judge/run/responses.jsonl'), [value])])
    assert frame.iloc[0].reported_total_tokens == 6
    assert frame.iloc[0].total_tokens_unknown_attempts == 1


def test_legacy_single_success_top_level_usage_is_unambiguous():
    value = row()
    value['attempts'] = [{'attempt': 1, 'status': 'complete'}]
    value['usage'] = {'prompt_tokens': 2, 'completion_tokens': 4, 'total_tokens': 6}
    frame, _ = account([(Path('prospective_pilot/run/responses.jsonl'), [value])])
    assert frame.iloc[0].reported_total_tokens == 6
    assert frame.iloc[0].single_attempt_top_level_usage_used == 1
    assert frame.iloc[0].total_tokens_unknown_attempts == 0
