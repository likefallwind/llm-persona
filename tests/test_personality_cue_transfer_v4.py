"""Check treatment attribution, frozen forecast transport, and failure closure."""
import json
from pathlib import Path
import sys

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from prepare_personality_cue_transfer_v4 import BANK, CUES, OLD, build, transport_predictions
from analyze_personality_cue_transfer_v4 import holm, primary, score, source_stats
from complete_personality_cue_transfer_v4 import api_pass
import complete_personality_cue_transfer_v4 as controller
import analyze_personality_cue_transfer_v4 as analysis


@pytest.fixture(scope='module')
def design():
    return build(json.loads(BANK.read_text())['templates'], json.loads(CUES.read_text()))


def test_peer_state_does_not_follow_quoted_emotion(design):
    scenarios, jobs = design
    peers = [r for r in scenarios if r['arm'] == 'peer_control']
    assert len(peers) == 128 and {r['affect'] for r in peers} == {'calm'}
    assert {r['cue_pole'] for r in peers} == {'calm', 'frustrated'}
    assert len(jobs) == len({j['request_id'] for j in jobs}) == 5120


def test_domain_balanced_phrases_and_exact_canonical_inputs(design):
    scenarios, _ = design
    frame = pd.DataFrame(scenarios)
    new = frame[frame.arm.isin(['explicit', 'implicit'])]
    assert set(new.groupby(['arm', 'domain', 'cue_family']).source_family.nunique()) == {2}
    original = [json.loads(s) for s in (OLD / 'confirmation/scenarios.jsonl').read_text().splitlines()]
    originals = {(r['template'], r['progress'], r['affect']): r['messages'] for r in original
                 if r['panel'] == 'main' and r['arm'] == 'canonical'}
    for row in scenarios:
        old = originals[(row['template'], row['progress'], row['affect'])]
        assert row['messages'][0] == old[0]
        if row['arm'] == 'canonical':
            assert row['messages'] == old


def test_probabilities_transport_without_new_fit_and_peer_uses_calm(design):
    rows, jobs = design
    old = pd.read_csv(OLD / 'locked_predictions/predictions.csv')
    _, prediction = transport_predictions(old, rows, jobs)
    peers = prediction[prediction.arm == 'peer_control']
    wide = peers.pivot(index=['template', 'progress', 'model', 'repeat', 'event', 'baseline'],
                       columns='cue_pole', values='probability')
    assert (wide.calm == wide.frustrated).all()
    changed = old.copy()
    changed.loc[0, 'probability'] += .05
    with pytest.raises(ValueError, match='within a feature tuple'):
        transport_predictions(changed, rows, jobs)


def test_missing_old_feature_cell_is_rejected(design):
    rows, jobs = design
    old = pd.read_csv(OLD / 'locked_predictions/predictions.csv')
    with pytest.raises(ValueError, match='Missing or extra'):
        transport_predictions(old[old.model != 'MiniMax-M3'], rows, jobs)


def test_missing_and_duplicate_labels_do_not_enter_analysis():
    predictions = pd.DataFrame([{'blind_id': 'a', 'event': 'answer_reveal', 'baseline': 'context',
                                 'probability': .5}])
    absent = pd.DataFrame(columns=['blind_id', 'event', 'present'])
    with pytest.raises(ValueError, match='Incomplete'):
        score(predictions, absent)
    duplicated = pd.DataFrame([{'blind_id': 'a', 'event': 'answer_reveal', 'present': 1}] * 2)
    with pytest.raises(ValueError, match='Duplicate'):
        score(predictions, duplicated)


def test_source_statistics_reject_pseudoreplication_and_zero_variance_is_conservative():
    frame = pd.DataFrame({'source_family': ['a', 'b', 'c', 'd'],
                          'domain': ['one', 'one', 'two', 'two'], 'gain': [.2] * 4})
    result = source_stats(frame, 'gain')
    assert result['gain'] == pytest.approx(.2) and result['p_one_sided'] == 1.0
    assert result['sources'] == 4
    with pytest.raises(ValueError, match='unique paired sources'):
        source_stats(pd.concat([frame, frame]), 'gain')


def test_primary_family_does_not_include_control_or_secondary_comparisons():
    table = pd.DataFrame([{'arm': arm, 'event': event, 'comparison': comparison,
                           'sources': 32, 'p_one_sided': .01}
                          for arm in ['canonical', 'explicit', 'implicit', 'peer_control']
                          for event in ['answer_reveal', 'reasoning_elicitation', 'affect_acknowledgement']
                          for comparison in ['default', 'conditional']])
    result = primary(table)
    assert len(result) == 6 and set(result.arm) == {'explicit', 'implicit'}
    assert all(result.p_holm_six == .06)
    assert list(holm([.03, .001, .02])) == pytest.approx([.04, .003, .04])


def test_interrupted_api_pass_cannot_reset_attempt_allowance(tmp_path, monkeypatch):
    monkeypatch.setattr(controller, 'RUNTIME', tmp_path)
    (tmp_path / 'pass.json').write_text(json.dumps({'status': 'started'}))
    with pytest.raises(ValueError, match='Interrupted API pass'):
        api_pass('pass', tmp_path / 'missing_manifest', tmp_path / 'output', 0.7, 8192)


def test_complete_analysis_with_synthetic_outcomes_has_full_paired_panel(design, tmp_path, monkeypatch):
    """Exercise every output path before real outcomes exist; no API calls."""
    rows, jobs = design
    inputs, predictions = transport_predictions(pd.read_csv(OLD / 'locked_predictions/predictions.csv'), rows, jobs)
    base = tmp_path / 'study'
    diagnostics = base / 'measurement'
    diagnostics.mkdir(parents=True)
    monkeypatch.setattr(analysis, 'OUT', base)
    monkeypatch.setattr(analysis, 'ROOT', tmp_path)
    inputs.to_csv(base / 'input_frame.csv', index=False)
    predictions.to_csv(base / 'predictions.csv', index=False)
    labels = predictions[['blind_id', 'event']].drop_duplicates().copy()
    labels['present'] = [int(i % 3 == 0) for i in range(len(labels))]
    labels.to_csv(diagnostics / 'consensus.csv', index=False)
    pd.concat([labels.assign(judge_requested=j) for j in ['MiniMax-M3', 'deepseek-v4-pro', 'glm-5.3']]).to_csv(
        diagnostics / 'event_codes.csv', index=False)
    (base / 'design_freeze.json').write_text(json.dumps({'files': {}}))
    for name in ['generation_audit.json', 'judge_lineage_audit.json', 'forecast_timing_audit.json']:
        (base / name).write_text(json.dumps({'status': 'pass'}))
    (diagnostics / 'summary.json').write_text(json.dumps({'invalid_or_missing': 0,
        'valid_judge_requests': 15360, 'judge_requested_to_returned': {
            j: [j] for j in ['MiniMax-M3', 'deepseek-v4-pro', 'glm-5.3']}}))
    analysis.main(diagnostics)
    table = pd.read_csv(base / 'analysis/primary_transfer.csv')
    assert len(table) == 6 and table.sources.eq(32).all()
    repetitions = pd.read_csv(base / 'analysis/repeat_agreement.csv')
    assert len(repetitions) == 60
    assert json.loads((base / 'analysis/summary.json').read_text())['new_fitting_calls'] == 0
