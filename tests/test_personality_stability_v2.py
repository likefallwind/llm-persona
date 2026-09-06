import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


spec = importlib.util.spec_from_file_location('personality_stability_v2', Path(__file__).resolve().parents[1]/'scripts/analyze_personality_stability_v2.py')
analysis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analysis)


def test_shared_source_in_two_tasks_never_crosses_fold():
    groups = np.array(['shared', 'a', 'shared', 'b'])
    for repeat in range(20):
        fold = analysis.source_fold(groups, repeat)
        assert fold[0] == fold[2]
        assert not set(groups[fold == 0]) & set(groups[fold == 1])


def test_unknown_sources_are_excluded_or_one_conservative_cohort():
    frame = pd.DataFrame({'task': ['a', 'b', 'a'], 'pair_id': ['1', '2', '3']})
    mapping = frame.assign(pair_key_sha256=[analysis.sha(t+':'+p) for t,p in zip(frame.task, frame.pair_id)],
                           group_sha256=['', '', 'known']).drop(columns='pair_id')
    assert len(analysis.attach_groups(frame, mapping, 'exclude')) == 1
    result = analysis.attach_groups(frame, mapping, 'conservative_cohort')
    assert result.group_sha256.iloc[0] == result.group_sha256.iloc[1]
    assert result.group_sha256.iloc[0] != result.group_sha256.iloc[2]
    with pytest.raises(ValueError, match='Missing source mapping'):
        analysis.attach_groups(frame, mapping.iloc[:2], 'exclude')


def test_source_weight_does_not_multiply_repeated_contexts():
    weights = analysis.source_weights(['a', 'a', 'a', 'b'], ['x', 'x', 'y', 'x'])
    np.testing.assert_allclose(weights, [.5, .5, 1, 1])


def test_known_crossing_profiles_generalize_within_task_but_fail_transfer():
    rng = np.random.default_rng(417)
    rows, index = [], []
    for task, sign in [('a', 1), ('b', -1)]:
        for i in range(100):
            index.append((task, str(i), f'shared-{i}'))
            values = sign*np.array([-1., 0., 1.]) + rng.normal(0, .05, 3)
            rows.append(values-values.mean())
    wide = pd.DataFrame(rows, index=pd.MultiIndex.from_tuples(index, names=['task', 'pair_id', 'group_sha256']))
    result = analysis.crossfit(wide, 10)
    total = result[result.task == 'ALL_EQUAL_TASK_WEIGHT']
    assert (total.task_model_mse < total.global_model_mse * .05).all()
    # Every source in a is reused in b: a valid leave-task-out fit must not silently
    # train on those same sources. There is no training data after the purge.
    with pytest.raises(ValueError):
        analysis.leave_task_out(wide)


def test_leave_task_out_purges_shared_sources():
    index = pd.MultiIndex.from_tuples([('a','0','shared'),('a','1','a_only'),
                                      ('b','0','shared'),('b','1','b_only')],
                                     names=['task','pair_id','group_sha256'])
    wide = pd.DataFrame([[-1,1]]*4, index=index)
    rows = analysis.leave_task_out(wide)
    assert all(r['train_contexts']==1 and r['purged_overlapping_train_contexts']==1 for r in rows)
    assert all(r['train_test_source_overlap']==0 for r in rows)
    assert all(r['global_model_mse']==0 for r in rows)
