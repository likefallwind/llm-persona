import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

spec = importlib.util.spec_from_file_location('event_prediction', Path(__file__).resolve().parents[1]/'scripts/predict_personality_events_v2.py')
analysis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analysis)


def planted():
    rows = []
    for source in range(40):
        for model in ('a', 'b'):
            for progress in ('early', 'late'):
                for affect in ('calm', 'frustrated'):
                    rows.append({'source_group': f'source{source}', 'model': model, 'domain': 'math',
                                 'progress': progress, 'affect': affect, 'event': 'action',
                                 'blind_id': f'{source}:{model}:{progress}:{affect}',
                                 'present': .9 if (model == 'a') == (progress == 'early') else .1})
    frame = pd.DataFrame(rows)
    return frame.iloc[:240], frame.iloc[240:]


def test_conditional_pattern_predicts_new_sources_beyond_model_means():
    train, test = planted()
    pooled, _ = analysis.fit_predict(train, test, 'default_profile')
    conditional, _ = analysis.fit_predict(train, test, 'conditional_profile')
    assert np.mean((conditional-test.present)**2) < .1*np.mean((pooled-test.present)**2)


def test_test_labels_do_not_enter_predictions_or_centering():
    train, test = planted()
    before, _ = analysis.fit_predict(train, test, 'conditional_profile')
    after, _ = analysis.fit_predict(train, test.assign(present=1-test.present), 'conditional_profile')
    np.testing.assert_array_equal(before, after)
    with pytest.raises(ValueError, match='source overlap'):
        analysis.fit_predict(train, train, 'context')


def test_constant_training_events_have_no_spurious_model_gain():
    train, test = planted()
    values = []
    for baseline in analysis.BASELINES:
        p, info = analysis.fit_predict(train.assign(present=0), test, baseline)
        assert info['constant_training_label'] == 0
        assert np.all((p > 0) & (p < 1))
        values.append(p)
    np.testing.assert_array_equal(values[0], values[1])
    np.testing.assert_array_equal(values[0], values[2])


def test_all_repeats_from_one_source_stay_together():
    groups = ['a', 'b', 'a', 'c', 'b', 'd', 'c']
    folds = analysis.group_folds(groups, 3)
    for group in set(groups):
        assert len({fold for g, fold in zip(groups, folds) if g == group}) == 1
