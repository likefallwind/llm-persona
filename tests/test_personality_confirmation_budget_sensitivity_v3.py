"""Missing coder bounds must not silently change agreement or source weights."""
from itertools import product
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from audit_personality_confirmation_budget_sensitivity_v3 import label_bounds, primary_ranges
from analyze_personality_confirmation_v3 import holm


@pytest.mark.parametrize('known,expected', [([0, 0], (0, 0)), ([0, 1], (0, 1)), ([1, 1], (1, 1))])
def test_missing_third_vote_bounds(known, expected):
    frame = pd.DataFrame([dict(blind_id='x', event='e', present=expected[0])])
    codes = pd.DataFrame([dict(blind_id='x', event='e', judge_requested=j, present=v)
                          for j, v in zip(['MiniMax-M3', 'deepseek-v4-pro'], known)])
    result = label_bounds(frame, codes, ['x'])
    assert tuple(result.loc[0, ['lower', 'upper']]) == expected
    with pytest.raises(ValueError, match='two fixed original coders'):
        label_bounds(frame, codes.iloc[:1], ['x'])


def test_enumeration_matches_direct_brier_algebra_and_repetition():
    rows = []
    for source, model, progress, affect, repeat in product(range(32), range(5), range(2), range(2), range(2)):
        blind = f'{source}_{model}_{progress}_{affect}_{repeat}'
        value = int((source + model + progress + affect) % 2)
        rows.append(dict(blind_id=blind, event='answer_reveal', model=f'm{model}',
                         source_family=f's{source}', progress=progress, affect=affect,
                         repeat=repeat, panel='main', arm='canonical', present=value,
                         lower=value, upper=value))
    frame = pd.DataFrame(rows)
    missing = ['0_0_0_0_0', '1_0_0_0_0']
    frame.loc[frame.blind_id.isin(missing), ['lower', 'upper']] = [0, 1]
    forecasts = []
    probabilities = dict(context=.5, default_profile=.8, domain_profile=.3, conditional_profile=.6)
    for row in rows:
        for baseline, probability in probabilities.items():
            forecasts.append(dict(blind_id=row['blind_id'], event='answer_reveal',
                                  source_group=row['source_family'], baseline=baseline, probability=probability))
    variants, repeats = primary_ranges(pd.DataFrame(forecasts), frame, missing)
    assert len(variants) == 8 and len(repeats) == 20
    for bits in product([0, 1], repeat=2):
        values = frame.present.to_numpy().copy()
        for blind, bit in zip(missing, bits):
            values[np.flatnonzero(frame.blind_id.eq(blind))] = bit
        expected = np.mean((.5 - values) ** 2 - (.8 - values) ** 2)
        case = 'case_' + ''.join(map(str, bits))
        got = variants[(variants.assignment == case) & variants.comparison.eq('default_vs_context')]
        assert got.iloc[0].mean_difference == pytest.approx(expected, abs=1e-14)
        agreement = 1 - (int(bits[0] != 0) + int(bits[1] != 1)) / 128
        got_repeat = repeats[repeats.assignment.eq(case) & repeats.model.eq('m0')]
        assert got_repeat.iloc[0].agreement == pytest.approx(agreement)


def test_holm_of_componentwise_maxima_bounds_every_joint_assignment():
    alternatives = np.array([[.001, .03], [.009, .002], [.015, .7], [.06, .01], [.4, .2], [.12, .07]])
    upper = holm(alternatives.max(axis=1))
    for bits in product([0, 1], repeat=6):
        assert np.all(holm(alternatives[np.arange(6), bits]) <= upper + 1e-15)
