"""Meaningful source-leakage, pairing and full-analysis regression checks."""
import json
from pathlib import Path
import sys

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from prepare_archive_behavior_validation_v4 import BASE, BRIDGE, RUBRIC, candidates, select
from prepare_personality_judging_v2 import judge_messages
from analyze_archive_behavior_validation_v4 import crossfit, gain_tables, interval
import analyze_archive_behavior_validation_v4 as analysis
from run_personality_requests_v2 import read_rows


def test_source_panel_has_exact_pairs_and_no_repeated_source():
    eligible, excluded, cells = candidates(read_rows(BRIDGE / 'local/materials.jsonl'), read_rows(BRIDGE / 'response_index.jsonl'))
    pairs = select(eligible)
    assert len(pairs) == len({a['source_group'] for a, _ in pairs}) == 256
    assert len(eligible) == 1002
    for a, b in pairs:
        assert a['conversation'] == b['conversation'] and a['problem'] == b['problem']
        assert a['reference_status'] == b['reference_status'] == 'provided_unvalidated'
    assert {r['reason'] for r in excluded} == {'problem_or_reference_missing'}


def test_frozen_payload_reconstructs_after_mapping_json_round_trip():
    mapping = {r['blind_id']: r for r in read_rows(BASE / 'judge/unblinding.jsonl')}
    rubric = json.loads(RUBRIC.read_text())
    jobs = read_rows(BASE / 'judge/manifest.jsonl')
    assert len(jobs) == 10752
    for job in jobs:
        assert job['messages'] == judge_messages(mapping[job['blind_id']], rubric)


def small_frame(n=20, models=('A', 'B')):
    return pd.DataFrame([{'source_family': f'source_{i}', 'arm': arm, 'model': model,
                          'event': event, 'present': int((model == models[0]) != (i % 3 == 0)),
                          'blind_id': f'{i}_{arm}_{model}'}
                         for i in range(n) for arm in ['scaffolding', 'pedagogy'] for model in models
                         for event in ['answer_reveal', 'reasoning_elicitation', 'affect_acknowledgement']])


def test_heldout_labels_do_not_change_their_own_predictions():
    frame = small_frame()
    first = crossfit(frame)
    heldout = set(first.loc[first.fold == 0, 'source_family'])
    changed = frame.copy()
    mask = changed.source_family.isin(heldout)
    changed.loc[mask, 'present'] = 1 - changed.loc[mask, 'present']
    second = crossfit(changed)
    pd.testing.assert_series_equal(first.loc[first.fold == 0, 'probability'], second.loc[second.fold == 0, 'probability'])
    assert set(first.groupby('source_family').fold.nunique()) == {1}


def test_duplicate_source_cells_are_rejected():
    frame = small_frame()
    with pytest.raises(ValueError, match='Duplicate'):
        crossfit(pd.concat([frame, frame.iloc[:1]]))


def test_opposite_instruction_profiles_have_hand_calculated_transfer_losses():
    # Five sources put one entire paired source in each test fold. With four
    # training sources per model/arm, Jeffreys predictions are 0.9 or 0.1.
    # Reversing model preferences between arms must hurt cross-arm transfer.
    frame = small_frame(5)
    frame['present'] = ((frame.model == 'A') == (frame.arm == 'scaffolding')).astype(int)
    predictions = crossfit(frame)
    for baseline, expected in [('instruction_only', .25),
                               ('same_instruction_model', .01),
                               ('other_instruction_model', .81)]:
        losses = predictions.loc[predictions.baseline == baseline, 'brier']
        assert losses.tolist() == pytest.approx([expected] * len(losses))
    _, gains = gain_tables(predictions)
    for row in gains.to_dict('records'):
        expected = .24 if row['comparison'].startswith('same_instruction') else -.56
        assert row['sources'] == 5
        assert row['mean'] == pytest.approx(expected)
        assert row['bootstrap_95_low'] == pytest.approx(expected)
        assert row['bootstrap_95_high'] == pytest.approx(expected)


def test_target_arm_training_labels_do_not_change_other_arm_forecasts():
    frame = small_frame(10)
    first = crossfit(frame)
    heldout = set(first.loc[first.fold == 0, 'source_family'])
    changed = frame.copy()
    mask = ~changed.source_family.isin(heldout) & (changed.arm == 'scaffolding')
    changed.loc[mask, 'present'] = 1 - changed.loc[mask, 'present']
    second = crossfit(changed)
    target = (first.fold == 0) & (first.arm == 'scaffolding')
    other = target & (first.baseline == 'other_instruction_model')
    same = target & (first.baseline == 'same_instruction_model')
    pd.testing.assert_series_equal(first.loc[other, 'probability'], second.loc[other, 'probability'])
    assert (first.loc[same, 'probability'] != second.loc[same, 'probability']).all()


def test_complete_archive_analysis_on_synthetic_labels(tmp_path, monkeypatch):
    base = tmp_path / 'archive'
    diagnostics = base / 'diagnostics'
    diagnostics.mkdir(parents=True)
    monkeypatch.setattr(analysis, 'BASE', base)
    monkeypatch.setattr(analysis, 'ROOT', tmp_path)
    frame = small_frame(256, tuple('ABCDEFG'))
    frame.to_csv(diagnostics / 'consensus.csv', index=False)
    pd.concat([frame.rename(columns={'model': 'model_requested'}).assign(judge_requested=judge)
               for judge in ['MiniMax-M3', 'glm-5.3', 'deepseek-v4-pro']]).to_csv(diagnostics / 'event_codes.csv', index=False)
    (base / 'design_freeze.json').write_text(json.dumps({'files': {}}))
    (diagnostics / 'summary.json').write_text(json.dumps({'invalid_or_missing': 0, 'valid_judge_requests': 10752,
        'judge_requested_to_returned': {j: [j] for j in ['MiniMax-M3', 'glm-5.3', 'deepseek-v4-pro']}}))
    analysis.main(diagnostics)
    assert len(pd.read_csv(base / 'analysis/paired_instruction_effects.csv')) == 21
    assert len(pd.read_csv(base / 'analysis/source_cv_predictions.csv')) == 32256
    assert json.loads((base / 'analysis/summary.json').read_text())['sources'] == 256
