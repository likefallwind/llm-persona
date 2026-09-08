#!/usr/bin/env python3
"""Evaluate locked cross-cue forecasts; no fitting and no outcome selection."""
import argparse
import json

import numpy as np
import pandas as pd
from scipy.stats import t as student_t

from analyze_personality_coding_v2 import pair_agreement
from prepare_personality_cue_transfer_v4 import OUT, ROOT, EVENTS, sha
from run_personality_formal_stage_v3 import verify_files

COMPARISONS = [('default', 'context', 'default_profile'),
               ('conditional', 'domain_profile', 'conditional_profile')]


def source_stats(frame, column):
    """One row per source; bootstrap sources within the four fixed domains."""
    frame = frame.sort_values(['domain', 'source_family']).reset_index(drop=True)
    if frame.source_family.duplicated().any() or len(frame) < 2:
        raise ValueError('Source statistics require unique paired sources')
    values = frame[column].to_numpy(float)
    if not np.isfinite(values).all():
        raise ValueError('Non-finite paired source values')
    se = values.std(ddof=1) / np.sqrt(len(values))
    rng = np.random.default_rng(20260907)
    indices = np.concatenate([rng.choice(np.asarray(list(ids)), (10000, len(ids)), replace=True)
                              for ids in frame.groupby('domain').groups.values()], axis=1)
    lower, upper = np.quantile(values[indices].mean(axis=1), [.025, .975])
    return {'sources': len(values), 'gain': float(values.mean()),
            'bootstrap_95_low': float(lower), 'bootstrap_95_high': float(upper),
            'source_standard_error': float(se),
            'p_one_sided': float(student_t.sf(values.mean() / se, len(values) - 1)) if se > 0 else 1.0,
            'test_note': '' if se > 0 else 'Zero source variance; no t-test decision'}


def holm(pvalues):
    p = np.asarray(pvalues, float)
    if not np.isfinite(p).all() or not ((p >= 0) & (p <= 1)).all():
        raise ValueError('Invalid p values')
    order = np.argsort(p, kind='stable')
    out = np.empty(len(p))
    out[order] = np.minimum(1, np.maximum.accumulate(p[order] * (len(p) - np.arange(len(p)))))
    return out


def score(predictions, labels):
    keys = ['blind_id', 'event']
    if labels.duplicated(keys).any() or predictions.duplicated(keys + ['baseline']).any():
        raise ValueError('Duplicate labels or predictions')
    expected = predictions[keys].drop_duplicates()
    labels = labels[labels.event.isin(EVENTS)]
    check = expected.merge(labels[keys], on=keys, how='outer', indicator=True, validate='one_to_one')
    if not check._merge.eq('both').all():
        raise ValueError('Incomplete or unexpected label panel')
    if not labels.present.isin([0, 1]).all():
        raise ValueError('Labels must be binary')
    scored = predictions.merge(labels[keys + ['present']], on=keys, validate='many_to_one')
    scored['brier'] = (scored.probability - scored.present) ** 2
    losses = scored.groupby(['source_family', 'domain', 'arm', 'event', 'baseline']).brier.mean().reset_index()
    wide = losses.pivot(index=['source_family', 'domain', 'arm', 'event'], columns='baseline', values='brier').reset_index()
    changes = []
    for name, base, model in COMPARISONS:
        one = wide[['source_family', 'domain', 'arm', 'event']].copy()
        one['comparison'] = name
        one['gain'] = wide[base] - wide[model]
        changes.append(one)
    return scored, losses, pd.concat(changes, ignore_index=True)


def comparison_table(changes):
    return pd.DataFrame([{'arm': arm, 'event': event, 'comparison': comparison, **source_stats(part, 'gain')}
                         for (arm, event, comparison), part in changes.groupby(['arm', 'event', 'comparison'])])


def primary(table):
    chosen = table[table.arm.isin(['explicit', 'implicit']) & (
        (table.event.isin(['answer_reveal', 'reasoning_elicitation']) & table.comparison.eq('default')) |
        (table.event.eq('affect_acknowledgement') & table.comparison.eq('conditional')))].copy()
    if len(chosen) != 6 or not chosen.sources.eq(32).all():
        raise ValueError('Primary family requires six comparisons and 32 complete sources')
    chosen['p_holm_six'] = holm(chosen.p_one_sided)
    return chosen


def main(diagnostics):
    lock = json.loads((OUT / 'design_freeze.json').read_text())
    verify_files(lock['files'])
    summary = json.loads((diagnostics / 'summary.json').read_text())
    if summary['invalid_or_missing'] or summary['valid_judge_requests'] != 15360:
        raise ValueError('Requires all 5120 responses with all three valid coders')
    if any(v != [k] for k, v in summary['judge_requested_to_returned'].items()):
        raise ValueError('Coding deployment mismatch')
    for name in ['generation_audit.json', 'judge_lineage_audit.json', 'forecast_timing_audit.json']:
        if json.loads((OUT / name).read_text())['status'] != 'pass':
            raise ValueError('Required audit did not pass: ' + name)
    prediction = pd.read_csv(OUT / 'predictions.csv')
    labels = pd.read_csv(diagnostics / 'consensus.csv')
    scored, losses, changes = score(prediction, labels)
    table = comparison_table(changes)
    result = OUT / 'analysis'
    result.mkdir(exist_ok=True)
    losses.to_csv(result / 'source_losses.csv', index=False)
    changes.to_csv(result / 'source_gains.csv', index=False)
    table.to_csv(result / 'all_forecast_comparisons.csv', index=False)
    primary(table).to_csv(result / 'primary_transfer.csv', index=False)
    scored.groupby(['arm', 'event', 'baseline']).agg(
        brier=('brier', 'mean'), mean_forecast=('probability', 'mean'),
        observed_rate=('present', 'mean'), answers=('present', 'size')).reset_index().to_csv(
            result / 'absolute_predictions.csv', index=False)
    differences = []
    for (event, comparison), part in changes.groupby(['event', 'comparison']):
        wide = part.pivot(index=['source_family', 'domain'], columns='arm', values='gain').reset_index()
        for arm in ['explicit', 'implicit']:
            wide['difference'] = wide[arm] - wide.canonical
            differences.append({'event': event, 'comparison': comparison, 'arm': arm,
                                **source_stats(wide, 'difference')})
    pd.DataFrame(differences).to_csv(result / 'transfer_minus_contemporary_canonical.csv', index=False)
    inputs = pd.read_csv(OUT / 'input_frame.csv')
    observed = inputs.merge(labels[['blind_id', 'event', 'present']], on='blind_id', validate='one_to_many')
    observed = observed[observed.event.isin(EVENTS)]
    observed.groupby(['arm', 'model', 'event', 'progress', 'cue_pole']).present.agg(
        ['size', 'mean']).reset_index().to_csv(result / 'event_rates.csv', index=False)
    observed.groupby(['arm', 'cue_family', 'model', 'event']).present.agg(
        ['size', 'mean']).reset_index().to_csv(result / 'finite_phrase_rates.csv', index=False)
    effects = []
    rates = observed.groupby(['source_family', 'domain', 'arm', 'model', 'event', 'cue_pole']).present.mean().reset_index()
    for (arm, model, event), part in rates.groupby(['arm', 'model', 'event']):
        wide = part.pivot(index=['source_family', 'domain'], columns='cue_pole', values='present').reset_index()
        wide['pole_difference'] = wide.frustrated - wide.calm
        effects.append({'arm': arm, 'model': model, 'event': event,
                        'interpretation': 'peer quote contrast; own affect fixed calm' if arm == 'peer_control' else 'student cue contrast',
                        **source_stats(wide, 'pole_difference')})
    pd.DataFrame(effects).to_csv(result / 'cue_pole_contrasts.csv', index=False)
    repetitions = []
    for (arm, model, event), part in observed.groupby(['arm', 'model', 'event']):
        wide = part.pivot(index=['source_family', 'progress', 'cue_pole'], columns='repeat', values='present')
        if set(wide.columns) != {0, 1} or wide.isna().any().any():
            raise ValueError('Incomplete repeated-response pairs')
        repetitions.append({'arm': arm, 'model': model, 'event': event, **pair_agreement(wide[0], wide[1])})
    pd.DataFrame(repetitions).to_csv(result / 'repeat_agreement.csv', index=False)
    sensitivity = []
    codes = pd.read_csv(diagnostics / 'event_codes.csv')
    for judge, part in codes.groupby('judge_requested'):
        _, _, values = score(prediction, part)
        sensitivity.append(comparison_table(values).assign(panel='single_coder:' + judge))
    for model in sorted(prediction.model.unique()):
        selected = prediction[prediction.model != model]
        selected_labels = labels[labels.blind_id.isin(selected.blind_id)]
        _, _, values = score(selected, selected_labels)
        sensitivity.append(comparison_table(values).assign(panel='drop_generator_fixed_forecasts:' + model))
    pd.concat(sensitivity, ignore_index=True).to_csv(result / 'sensitivity_comparisons.csv', index=False)
    report = {'status': 'cue-transfer calculations complete; research-quality goal remains active',
              'answers': 5120, 'sources_reused_from_v3_confirmation': 32, 'new_source_problems': 0,
              'primary_test_family': 6, 'new_fitting_calls': 0, 'human_annotations_added': 0,
              'diagnostics': str(diagnostics.relative_to(ROOT)),
              'input_hashes': {str(p.relative_to(ROOT)): sha(p) for p in [OUT / 'design_freeze.json',
                  OUT / 'predictions.csv', diagnostics / 'consensus.csv', diagnostics / 'event_codes.csv']},
              'limits': ['Designed after v3 results; not an independent original preregistration.',
                         'Same confirmation sources and four fixed phrase pairs per new register.',
                         'Source intervals condition on fixed material/design assumptions.',
                         'Agent agreement is not semantic ground truth; implicit cues are not human state labels.',
                         'No transfer equivalence or absence of a peer effect inferred from nonsignificance.']}
    (result / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--diagnostics', type=type(OUT), required=True)
    main(parser.parse_args().diagnostics)
