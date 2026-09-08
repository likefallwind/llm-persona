"""Analyze identified majorities while preserving two blocked coder labels as missing."""
import json
from pathlib import Path

import pandas as pd

from analyze_archive_behavior_validation_v4 import crossfit, gain_tables, interval
from prepare_archive_behavior_validation_v4 import BASE, ROOT
from prepare_personality_cue_transfer_v4 import EVENTS, sha
from run_personality_formal_stage_v3 import verify_files

DIAGNOSTICS = BASE / 'measurement_diagnostics/transport_diagnostic'
OUT = BASE / 'analysis_identified'
JUDGES = {'MiniMax-M3', 'glm-5.3', 'deepseek-v4-pro'}


def majority_bounds(votes):
    votes = list(votes)
    if len(votes) > 3 or any(v not in (0, 1) for v in votes):
        raise ValueError('Expected up to three binary votes')
    positives = sum(votes)
    return int(positives >= 2), int(positives + 3 - len(votes) >= 2)


def identify(codes):
    metadata = ['template', 'progress', 'affect', 'repeat', 'model_requested',
                'source_family', 'partition', 'panel', 'arm']
    rows = []
    for (blind_id, event), group in codes.groupby(['blind_id', 'event']):
        if group.judge_requested.duplicated().any() or not set(group.judge_requested) <= JUDGES:
            raise ValueError('Duplicate or unknown coder')
        if any(group[k].nunique(dropna=False) != 1 for k in metadata):
            raise ValueError('Coder metadata disagree')
        low, high = majority_bounds(group.present)
        if low != high:
            raise ValueError('Majority not identified: ' + blind_id + ':' + event)
        row = {k: group.iloc[0][k] for k in metadata}
        row['model'] = row.pop('model_requested')
        row.update(blind_id=blind_id, event=event, present=low, majority_lower=low,
                   majority_upper=high, valid_coders=len(group),
                   missing_coders=';'.join(sorted(JUDGES - set(group.judge_requested))),
                   unanimous=int(group.present.nunique() == 1) if len(group) == 3 else None)
        rows.append(row)
    return pd.DataFrame(rows)


def tables(frame):
    rates, effects = [], []
    for (model, event), part in frame.groupby(['model', 'event']):
        wide = part.pivot(index='source_family', columns='arm', values='present').sort_index()
        for arm in ['scaffolding', 'pedagogy']:
            rates.append({'model': model, 'event': event, 'arm': arm, **interval(wide[arm])})
        effects.append({'model': model, 'event': event, 'contrast': 'pedagogy_minus_scaffolding',
                        **interval(wide.pedagogy - wide.scaffolding)})
    return pd.DataFrame(rates), pd.DataFrame(effects)


def main():
    verify_files(json.loads((BASE / 'design_freeze.json').read_text())['files'])
    summary = json.loads((DIAGNOSTICS / 'summary.json').read_text())
    assert summary['valid_judge_requests'] == 10750 and summary['invalid_or_missing'] == 2
    codes = pd.read_csv(DIAGNOSTICS / 'event_codes.csv')
    assert len(codes) == 10750 * 8
    consensus = identify(codes)
    assert len(consensus) == 3584 * 8
    unresolved = consensus[consensus.valid_coders < 3]
    assert len(unresolved) == 16 and unresolved.blind_id.nunique() == 2
    affected = set(unresolved.source_family)
    assert len(affected) == 2
    frame = consensus[consensus.event.isin(EVENTS)].copy()
    assert len(frame) == 10752 and frame.source_family.nunique() == 256
    assert frame.groupby(['source_family', 'event']).size().eq(14).all()
    OUT.mkdir(exist_ok=True)
    consensus.to_csv(OUT / 'identified_consensus.csv', index=False)
    unresolved.to_csv(OUT / 'missing_vote_identification.csv', index=False)
    rates, effects = tables(frame)
    rates.to_csv(OUT / 'event_rates.csv', index=False)
    effects.to_csv(OUT / 'paired_instruction_effects.csv', index=False)
    joint = frame.pivot(index=['source_family', 'model', 'arm'], columns='event', values='present').reset_index()
    joint['reveal_and_elicit'] = joint.answer_reveal * joint.reasoning_elicitation
    pd.DataFrame([{'model': model, 'arm': arm, **interval(part.reveal_and_elicit)}
                  for (model, arm), part in joint.groupby(['model', 'arm'])]).to_csv(OUT / 'joint_action_rates.csv', index=False)
    prediction = crossfit(frame)
    prediction.to_csv(OUT / 'source_cv_predictions.csv', index=False)
    losses, gains = gain_tables(prediction)
    losses.to_csv(OUT / 'source_losses.csv', index=False)
    gains.to_csv(OUT / 'prediction_gains.csv', index=False)
    prediction.groupby(['arm', 'event', 'baseline']).brier.mean().reset_index().to_csv(OUT / 'absolute_brier.csv', index=False)
    panels = []
    for model in sorted(frame.model.unique()):
        _, comparison = gain_tables(prediction[prediction.model != model])
        panels.append(comparison.assign(panel='drop_model_fixed_forecasts:' + model))
    pd.concat(panels).to_csv(OUT / 'drop_model_gains.csv', index=False)
    common = frame[~frame.source_family.isin(affected)]
    primary_codes = codes[codes.event.isin(EVENTS) & ~codes.source_family.isin(affected)].rename(columns={'model_requested': 'model'})
    common_panels = [('majority', common)] + list(primary_codes.groupby('judge_requested'))
    gain_rows, rate_rows, effect_rows = [], [], []
    for panel, part in common_panels:
        assert len(part) == 254 * 14 * 3 and part.source_family.nunique() == 254
        predictions = crossfit(part)
        predictions.to_csv(OUT / ('common254_predictions_' + panel + '.csv'), index=False)
        _, comparison = gain_tables(predictions)
        panel_rates, panel_effects = tables(part)
        gain_rows.append(comparison.assign(panel=panel))
        rate_rows.append(panel_rates.assign(panel=panel))
        effect_rows.append(panel_effects.assign(panel=panel))
    pd.concat(gain_rows).to_csv(OUT / 'common254_gains.csv', index=False)
    pd.concat(rate_rows).to_csv(OUT / 'common254_rates.csv', index=False)
    pd.concat(effect_rows).to_csv(OUT / 'common254_effects.csv', index=False)
    inputs = [BASE / 'design_freeze.json', DIAGNOSTICS / 'summary.json', DIAGNOSTICS / 'coverage.csv',
              DIAGNOSTICS / 'event_codes.csv', Path(__file__),
              ROOT / 'research/86_archive_identified_majority_amendment_v4.md']
    report = {'status': 'identified-majority calculations complete; manuscript synthesis pending',
              'sources': 256, 'archived_answers': 3584, 'valid_coding_requests': 10750,
              'expected_coding_requests': 10752, 'missing_coding_requests': 2,
              'original_complete_coding_gate_passed': False, 'identified_majority_event_items': len(consensus),
              'missing_vote_majority_invariant_event_items': 16, 'additional_diagnostic_http_attempts': 2,
              'missing_labels_imputed': False, 'new_teacher_generations': 0, 'human_annotation_added': False,
              'affected_sources': sorted(affected), 'complete_coder_common_sources': 254,
              'input_hashes': {str(p.resolve().relative_to(ROOT)): sha(p) for p in inputs},
              'limitations': ['Post-hoc missing-coder amendment after inspecting agreement of the two available votes.',
                             'SensitiveContentDetected provider refusal; no rewritten input or alternative route.',
                             'Fixed-crossfit bootstrap does not cover all fitting uncertainty or shared-training dependence.',
                             'Common-source sensitivity refits all panels with the hash fold rule applied to 254 sources.',
                             'Historical requests reconstructed, not attested; benchmark dialogue is not classroom validation.',
                             'Identified majority does not establish semantic truth or complete three-coder unanimity.'],
              'research_quality_goal_complete': False}
    (OUT / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
