#!/usr/bin/env python3
"""Source-held-out archive prediction and paired instruction contrasts."""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from prepare_archive_behavior_validation_v4 import BASE, ROOT
from prepare_personality_cue_transfer_v4 import EVENTS, sha
from run_personality_formal_stage_v3 import verify_files
from run_personality_requests_v2 import digest


def interval(values):
    x = np.asarray(values, float)
    if x.ndim != 1 or not len(x) or not np.isfinite(x).all():
        raise ValueError('Need finite source-level values')
    rng = np.random.default_rng(20260908)
    means = x[rng.integers(0, len(x), (10000, len(x)))].mean(axis=1)
    ci = np.quantile(means, [.025, .975])
    return {'sources': len(x), 'mean': float(x.mean()), 'bootstrap_95_low': float(ci[0]), 'bootstrap_95_high': float(ci[1])}


def crossfit(frame):
    keys = ['source_family', 'arm', 'model', 'event']
    if frame.duplicated(keys).any():
        raise ValueError('Duplicate source/arm/model/event observation')
    sources = sorted(frame.source_family.unique(), key=lambda x: digest('archive-fold-v4:' + x))
    folds = {source: index % 5 for index, source in enumerate(sources)}
    frame = frame.copy()
    frame['fold'] = frame.source_family.map(folds)
    output = []
    for event, part in frame.groupby('event'):
        for fold in range(5):
            train, test = part[part.fold != fold], part[part.fold == fold]
            if set(train.source_family) & set(test.source_family) or not len(test):
                raise ValueError('Source fold overlap or empty test')
            arm_rates = train.groupby('arm').present.agg(['sum', 'size'])
            cell_rates = train.groupby(['arm', 'model']).present.agg(['sum', 'size'])
            for row in test.to_dict('records'):
                other = 'pedagogy' if row['arm'] == 'scaffolding' else 'scaffolding'
                counts = {'instruction_only': arm_rates.loc[row['arm']],
                          'same_instruction_model': cell_rates.loc[(row['arm'], row['model'])],
                          'other_instruction_model': cell_rates.loc[(other, row['model'])]}
                for baseline, count in counts.items():
                    p = (float(count['sum']) + .5) / (float(count['size']) + 1)
                    output.append({**{k: row[k] for k in keys}, 'fold': fold, 'baseline': baseline,
                                   'observed': row['present'], 'probability': p,
                                   'brier': (p - row['present']) ** 2})
    return pd.DataFrame(output)


def gain_tables(predictions):
    losses = predictions.groupby(['source_family', 'arm', 'event', 'baseline']).brier.mean().reset_index()
    gains = []
    for (arm, event), part in losses.groupby(['arm', 'event']):
        wide = part.pivot(index='source_family', columns='baseline', values='brier')
        for baseline in ['same_instruction_model', 'other_instruction_model']:
            gains.append({'arm': arm, 'event': event, 'comparison': baseline + '_vs_instruction_only',
                          **interval(wide.instruction_only - wide[baseline])})
    return losses, pd.DataFrame(gains)


def main(diagnostics):
    diagnostics = diagnostics.resolve()
    verify_files(json.loads((BASE / 'design_freeze.json').read_text())['files'])
    summary = json.loads((diagnostics / 'summary.json').read_text())
    if summary['invalid_or_missing'] or summary['valid_judge_requests'] != 10752:
        raise ValueError('Requires all three coders on all 3584 archived answers')
    if any(v != [k] for k, v in summary['judge_requested_to_returned'].items()):
        raise ValueError('Unexpected coder deployment')
    frame = pd.read_csv(diagnostics / 'consensus.csv')
    frame = frame[frame.event.isin(EVENTS)].copy()
    if len(frame) != 10752 or frame.source_family.nunique() != 256:
        raise ValueError('Incomplete archival source panel')
    if not frame.groupby(['source_family', 'event']).size().eq(14).all():
        raise ValueError('Source lacks both instructions and seven models')
    out = BASE / 'analysis'
    out.mkdir(exist_ok=True)
    rates, effects = [], []
    for (model, event), part in frame.groupby(['model', 'event']):
        wide = part.pivot(index='source_family', columns='arm', values='present').sort_index()
        for arm in ['scaffolding', 'pedagogy']:
            rates.append({'model': model, 'event': event, 'arm': arm, **interval(wide[arm])})
        effects.append({'model': model, 'event': event, 'contrast': 'pedagogy_minus_scaffolding',
                        **interval(wide.pedagogy - wide.scaffolding)})
    pd.DataFrame(rates).to_csv(out / 'event_rates.csv', index=False)
    pd.DataFrame(effects).to_csv(out / 'paired_instruction_effects.csv', index=False)
    joint = frame.pivot(index=['source_family', 'model', 'arm'], columns='event', values='present').reset_index()
    joint['reveal_and_elicit'] = joint.answer_reveal * joint.reasoning_elicitation
    pd.DataFrame([{'model': model, 'arm': arm, **interval(part.reveal_and_elicit)}
                  for (model, arm), part in joint.groupby(['model', 'arm'])]).to_csv(out / 'joint_action_rates.csv', index=False)
    prediction = crossfit(frame)
    prediction.to_csv(out / 'source_cv_predictions.csv', index=False)
    losses, gains = gain_tables(prediction)
    losses.to_csv(out / 'source_losses.csv', index=False)
    gains.to_csv(out / 'prediction_gains.csv', index=False)
    prediction.groupby(['arm', 'event', 'baseline']).brier.mean().reset_index().to_csv(out / 'absolute_brier.csv', index=False)
    panels = []
    codes = pd.read_csv(diagnostics / 'event_codes.csv')
    codes = codes[codes.event.isin(EVENTS)].rename(columns={'model_requested': 'model'})
    for judge, part in codes.groupby('judge_requested'):
        _, comparison = gain_tables(crossfit(part))
        panels.append(comparison.assign(panel='single_coder:' + judge))
        pd.DataFrame([{'model': model, 'event': event, 'arm': arm, **interval(group.present)}
                      for (model, event, arm), group in part.groupby(['model', 'event', 'arm'])]).to_csv(
                          out / ('rates_' + judge + '.csv'), index=False)
    for model in sorted(frame.model.unique()):
        _, comparison = gain_tables(prediction[prediction.model != model])
        panels.append(comparison.assign(panel='drop_model_fixed_forecasts:' + model))
    pd.concat(panels).to_csv(out / 'sensitivity_gains.csv', index=False)
    report = {'status': 'archive behavior calculations complete; scientific synthesis pending',
              'sources': 256, 'archived_answers': 3584, 'new_teacher_generations': 0,
              'valid_coding_requests': 10752, 'models': sorted(frame.model.unique()),
              'input_hashes': {str(p.relative_to(ROOT)): sha(p) for p in [BASE / 'design_freeze.json',
                  diagnostics / 'consensus.csv', diagnostics / 'event_codes.csv']},
              'limits': ['Retrospective archive extension; not a new prospective teacher-generation experiment.',
                         'Current-adapter input reconstruction does not attest full historical requests or model weights.',
                         'Fixed-crossfit bootstrap omits model-fitting uncertainty; no confirmatory p values asserted.',
                         'Exact source grouping can miss paraphrased sources.',
                         'No human annotation added; coder agreement is not semantic ground truth.']}
    (out / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--diagnostics', type=Path, required=True)
    main(parser.parse_args().diagnostics)
