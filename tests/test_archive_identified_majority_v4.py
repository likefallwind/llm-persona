"""Exact partial identification checks; no empirical labels or API calls."""
import itertools
from pathlib import Path
import sys

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from analyze_archive_identified_majority_v4 import identify, majority_bounds


def test_bounds_equal_exhaustive_unknown_vote_completions():
    for n in range(4):
        for votes in itertools.product((0, 1), repeat=n):
            results = [int(sum(votes + rest) >= 2) for rest in itertools.product((0, 1), repeat=3 - n)]
            assert majority_bounds(votes) == (min(results), max(results))


@pytest.mark.parametrize('votes', [[0, 1, 0, 1], [2], [-1], [float('nan')]])
def test_invalid_votes_fail(votes):
    with pytest.raises(ValueError):
        majority_bounds(votes)


def fixture(votes):
    metadata = {k: 'fixed' for k in ['template', 'progress', 'affect', 'repeat',
                'model_requested', 'source_family', 'partition', 'panel', 'arm']}
    return pd.DataFrame([{**metadata, 'blind_id': 'x', 'event': 'answer_reveal',
                          'judge_requested': judge, 'present': value}
                         for judge, value in zip(['MiniMax-M3', 'glm-5.3', 'deepseek-v4-pro'], votes)])


def test_identified_majority_does_not_invent_third_vote_or_unanimity():
    frame = fixture([1, 1])
    result = identify(frame)
    assert len(frame) == 2 and len(result) == 1
    row = result.iloc[0]
    assert row.present == 1 and row.valid_coders == 2
    assert row.missing_coders == 'deepseek-v4-pro' and pd.isna(row.unanimous)


def test_disagreeing_available_votes_are_not_identified():
    with pytest.raises(ValueError, match='not identified'):
        identify(fixture([0, 1]))


def test_duplicate_coder_cannot_count_as_second_vote():
    frame = fixture([1, 1])
    frame['judge_requested'] = 'MiniMax-M3'
    with pytest.raises(ValueError, match='Duplicate'):
        identify(frame)
