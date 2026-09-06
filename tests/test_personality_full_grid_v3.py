"""Integration rehearsal on the exact frozen input grid with synthetic labels.

No API calls or empirical labels. All temporary CSVs live under pytest tmp_path;
the test cannot create a prediction lock in the research artifact directory.
"""
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import analyze_personality_confirmation_v3 as confirmation
import describe_personality_confirmation_v3 as descriptive
import lock_personality_predictions_v3 as locking
from lock_personality_judge_sensitivity_v3 import panel_labels, JUDGES
import personality_style_competitor_v3 as style
import predict_personality_events_v3 as predictor
from run_personality_formal_stage_v3 import BASE

EVENTS = [*confirmation.PRIMARY, 'worked_explanation', 'learner_choice',
          'epistemic_qualification', 'information_request', 'unsupported_ability_claim']


def input_grid(stage):
    root = BASE / stage
    samples = {r['sample_id']: r for r in map(json.loads, (root / 'scenarios.jsonl').read_text().splitlines())}
    rows = []
    for job in map(json.loads, (root / 'generation_manifest.jsonl').read_text().splitlines()):
        source = samples[job['sample_id']]
        rows.append({**{k: source[k] for k in ['template', 'source_family', 'domain', 'progress',
                                              'affect', 'panel', 'arm', 'partition']},
                     'blind_id': hashlib.sha256(('personality-coding-v2:' + job['request_id']).encode()).hexdigest()[:20],
                     'model': job['model'], 'repeat': job['repeat']})
    return pd.DataFrame(rows)


def synthetic_labels(grid, configurations):
    rows = []
    for item in grid.to_dict('records'):
        m = configurations.index(item['model'])
        for event in EVENTS:
            if event == 'answer_reveal':
                p = [.95, .75, .5, .25, .05][m]
            elif event == 'reasoning_elicitation':
                p = .97 if (m % 2 == 0) == (item['progress'] == 'wrong_attempt') else .03
            elif event == 'affect_acknowledgement':
                p = .95 if item['affect'] == 'frustrated' else .05
            else:
                p = 0.0  # Exercise the frozen constant-label path as well.
            u = int(hashlib.sha256(('TEST-ONLY:' + item['blind_id'] + event).encode()).hexdigest()[:12], 16) / 16**12
            # Match the production consensus schema: domain joins from mapping.
            rows.append({**{k: v for k, v in item.items() if k != 'domain'}, 'event': event, 'present': int(u < p)})
    return pd.DataFrame(rows)


def test_full_frozen_grid_fits_scores_and_preserves_panels(tmp_path, monkeypatch):
    training_grid, confirmation_grid = input_grid('training'), input_grid('confirmation')
    configurations = sorted(training_grid.model.unique())
    training = synthetic_labels(training_grid, configurations)
    observed = synthetic_labels(confirmation_grid, configurations)
    diagnostics, judge = tmp_path / 'diagnostics', tmp_path / 'judge'
    diagnostics.mkdir(); judge.mkdir()
    (diagnostics / 'summary.json').write_text(json.dumps({'invalid_or_missing': 0, 'valid_judge_requests': 3840,
                                                        'synthetic_test_fixture_not_research_evidence': True}))
    training.to_csv(diagnostics / 'consensus.csv', index=False)
    training_grid[['blind_id', 'source_family', 'domain']].to_json(judge / 'unblinding.jsonl', orient='records', lines=True)
    temporary_base = tmp_path / 'formal'
    (temporary_base / 'confirmation').mkdir(parents=True)
    for name in ['scenarios.jsonl', 'generation_manifest.jsonl']:
        (temporary_base / 'confirmation' / name).write_bytes((BASE / 'confirmation' / name).read_bytes())
    monkeypatch.setattr(locking, 'BASE', temporary_base)
    train, test = locking.frames(diagnostics, judge)
    assert len(train) == 10240 and len(test) == 1280
    assert train.source_group.nunique() == 30 and test.source_group.nunique() == 32
    assert not (set(train.source_group) & set(test.source_group))
    train['raw_log_words'] = train.model.map({m: 2.0 + i / 2 for i, m in enumerate(configurations)})
    train['raw_structure'] = train.model.map({m: (i % 3) / 3 for i, m in enumerate(configurations)})
    forecasts = []
    for event in confirmation.PRIMARY:
        fitting = train[train.event.eq(event)]
        for baseline in [*predictor.BASELINES, 'training_style_profile']:
            if baseline == 'training_style_profile':
                penalty, _ = style.select_penalty(fitting)
                p, model = style.fit_predict(fitting, test, penalty)
            else:
                penalty, _ = predictor.select_penalty(fitting, baseline)
                p, model = locking.predict_and_export(fitting, test, baseline, penalty)
            assert np.isfinite(p).all() and ((0 <= p) & (p <= 1)).all()
            forecasts.append(test.assign(event=event, baseline=baseline, probability=p))
    canonical = observed[observed.panel.eq('main') & observed.arm.eq('canonical')]
    _, source_losses, comparisons = confirmation.losses_and_comparisons(pd.concat(forecasts), canonical)
    assert len(comparisons) == 6 and len(source_losses) == 32 * 3 * 5
    answer = comparisons[comparisons.event.eq('answer_reveal') & comparisons.comparison.eq('default_vs_context')]
    reasoning = comparisons[comparisons.event.eq('reasoning_elicitation') & comparisons.comparison.eq('student_state_vs_domain')]
    assert answer.mean_difference.item() > .03
    assert reasoning.mean_difference.item() > .10
    # Complete alternative panels use the production metadata spelling and
    # retain every target even for same-family exclusion.
    coding = training.rename(columns={'model': 'model_requested'})
    panels = panel_labels(pd.concat([coding.assign(judge_returned=j) for j in JUDGES]))
    assert len(panels) == 8 * 10240
    assert panels.groupby(['judge_panel', 'event']).size().eq(1280).all()
    assert len(confirmation.repeat_diagnostics(observed)) == 5 * 8
    _, effects = confirmation.prompt_effects(observed)
    assert len(effects) == 5 * 3 * 4
    assert len(descriptive.joint_actions(observed)) == 4040
    profiles, dispersion, changes = descriptive.prompt_profiles(observed)
    assert len(profiles) == 5 * 3 * 5 and len(dispersion) == 3 * 5
    assert changes.source_family.nunique() == 16
    assert len(descriptive.sentinel_comparison(training, observed)) == 4 * 5 * 8
    assert len(descriptive.opportunity_pairs(observed)) == 8 * 5 * 8
    assert not (temporary_base / 'prediction_lock.json').exists()
