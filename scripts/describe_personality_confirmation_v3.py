#!/usr/bin/env python3
"""Complete the planned descriptive views; never fit or select a predictor.

These tables complement, rather than modify, the frozen primary comparisons.
Paired prompt dispersion always uses the same sixteen sources in all arms.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from analyze_personality_confirmation_v3 import PRIMARY
from run_personality_formal_stage_v3 import ROOT, BASE, validate_stage
from run_personality_requests_v2 import now


def joint_actions(frame):
    keys = ['blind_id', 'model', 'source_family', 'progress', 'affect', 'panel', 'arm', 'repeat']
    subset = frame[frame.event.isin(['answer_reveal', 'reasoning_elicitation'])]
    wide = subset.pivot(index=keys, columns='event', values='present')
    if wide.isna().any().any() or set(wide.columns) != {'answer_reveal', 'reasoning_elicitation'}:
        raise ValueError('Both action labels are required for every response')
    wide['joint_action'] = [
        {(0, 0): 'neither', (1, 0): 'reveal_only', (0, 1): 'elicit_only', (1, 1): 'both'}[(a, e)]
        for a, e in zip(wide.answer_reveal, wide.reasoning_elicitation)
    ]
    return wide.reset_index()


def prompt_profiles(frame):
    main = frame[frame.panel.eq('main') & frame.event.isin(PRIMARY)]
    counts = main.groupby('source_family').arm.nunique()
    sources = counts[counts.eq(5)].index
    if len(sources) != 16:
        raise ValueError('Expected sixteen sources with all five role arms')
    main = main[main.source_family.isin(sources)]
    cell = main.groupby(['source_family', 'model', 'event', 'progress', 'affect', 'arm']).present.mean()
    wide = cell.unstack('arm')
    if wide.isna().any().any() or len(wide) != 16 * 5 * 3 * 4:
        raise ValueError('Incomplete matched prompt grid')
    changes = wide.drop(columns='canonical').subtract(wide.canonical, axis=0).reset_index()
    long = changes.melt(id_vars=['source_family', 'model', 'event', 'progress', 'affect'],
                        var_name='arm', value_name='change_from_canonical')
    profiles = main.groupby(['model', 'event', 'arm']).present.mean().reset_index()
    dispersion = profiles.groupby(['event', 'arm']).present.agg(
        model_mean='mean', model_sd=lambda x: x.std(ddof=0), model_min='min', model_max='max').reset_index()
    # Population SD here describes the five fixed configurations, not an
    # estimate of dispersion over an unspecified population of model families.
    dispersion['matched_sources'] = 16
    return profiles, dispersion, long


def repetition_profiles(frame):
    main = frame[frame.panel.eq('main') & frame.arm.eq('canonical')]
    profiles = main.groupby(['event', 'model', 'repeat']).present.mean().unstack('repeat')
    if set(profiles.columns) != {0, 1} or profiles.isna().any().any():
        raise ValueError('Incomplete repeated profile')
    rows = []
    for event, data in profiles.groupby(level='event'):
        if len(data) != 5:
            raise ValueError('Expected five configurations')
        x, y = data[0].to_numpy(), data[1].to_numpy()
        nonconstant = np.ptp(x) > 0 and np.ptp(y) > 0
        rows.append({'event': event, 'configurations': 5,
                     'profile_mae': float(np.abs(x - y).mean()),
                     'profile_spearman': float(spearmanr(x, y).statistic) if nonconstant else None,
                     'note': 'descriptive five-configuration correlation; no population p-value' if nonconstant
                             else 'undefined rank correlation: at least one constant profile'})
    return profiles.rename(columns={0: 'repeat_0_rate', 1: 'repeat_1_rate'}).reset_index(), pd.DataFrame(rows)


def sentinel_comparison(training, confirmation):
    sentinel = confirmation[confirmation.panel.eq('training_sentinel')]
    old = training[training.panel.eq('main') & training.arm.eq('canonical') &
                   training.progress.eq('wrong_attempt') & training.affect.eq('calm') &
                   training.template.isin(sentinel.template.unique())]
    keys = ['template', 'source_family', 'model', 'event']
    a = old.groupby(keys).present.agg(['mean', 'size']).rename(columns={'mean': 'training_rate', 'size': 'training_n'})
    b = sentinel.groupby(keys).present.agg(['mean', 'size']).rename(columns={'mean': 'later_rate', 'size': 'later_n'})
    paired = a.join(b, how='outer', validate='one_to_one')
    if len(paired) != 4 * 5 * 8 or paired.isna().any().any():
        raise ValueError('Sentinel grid differs from four matched training templates')
    if not paired.training_n.eq(2).all() or not paired.later_n.eq(2).all():
        raise ValueError('Sentinel repetition count differs')
    paired['later_minus_training'] = paired.later_rate - paired.training_rate
    return paired.reset_index()


def opportunity_pairs(frame):
    subset = frame[frame.panel.isin(['opportunity_complete', 'opportunity_missing'])]
    keys = ['source_family', 'model', 'event']
    rates = subset.groupby(keys + ['panel']).present.mean().unstack('panel')
    if len(rates) != 8 * 5 * 8 or rates.isna().any().any():
        raise ValueError('Incomplete eight-source information opportunity panel')
    rates['missing_minus_complete'] = rates.opportunity_missing - rates.opportunity_complete
    return rates.reset_index()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--diagnostics', type=Path, required=True)
    ap.add_argument('--output', type=Path, default=BASE / 'confirmation_descriptive')
    args = ap.parse_args()
    validate_stage('confirmation')
    policy_path = BASE / 'descriptive_analysis_policy.json'
    policy = json.loads(policy_path.read_text())
    if policy['script_sha256'] != hashlib.sha256(Path(__file__).read_bytes()).hexdigest():
        raise ValueError('Descriptive analysis differs from its recorded pre-confirmation version')
    raw = BASE / 'confirmation/run/responses.jsonl'
    first = min(json.loads(line)['started_at'] for line in raw.open() if line.strip())
    if policy['fixed_at'] >= first:
        raise ValueError('Descriptive specification was not saved before confirmation calls')
    report = json.loads((args.diagnostics / 'summary.json').read_text())
    if report['invalid_or_missing'] or report['valid_judge_requests'] != 12120:
        raise ValueError('Full confirmation coding required')
    selection = json.loads((BASE / 'training/measurement_selection.json').read_text())
    train_path = ROOT / selection['diagnostics'] / 'consensus.csv'
    training = pd.read_csv(train_path)
    confirmation_path = args.diagnostics / 'consensus.csv'
    frame = pd.read_csv(confirmation_path)
    out = args.output
    out.mkdir(parents=True, exist_ok=True)
    actions = joint_actions(frame)
    actions.to_csv(out / 'joint_action_items.csv', index=False)
    actions.groupby(['model', 'panel', 'arm', 'joint_action']).size().rename('responses').to_csv(out / 'joint_action_counts.csv')
    profiles, dispersion, changes = prompt_profiles(frame)
    profiles.to_csv(out / 'matched_prompt_profiles.csv', index=False)
    dispersion.to_csv(out / 'matched_prompt_dispersion.csv', index=False)
    changes.to_csv(out / 'source_state_prompt_changes.csv', index=False)
    changes.groupby(['model', 'event', 'progress', 'affect', 'arm']).change_from_canonical.mean().to_csv(out / 'state_prompt_changes.csv')
    repeat, correspondence = repetition_profiles(frame)
    repeat.to_csv(out / 'repeated_default_profiles.csv', index=False)
    correspondence.to_csv(out / 'repeated_profile_correspondence.csv', index=False)
    sentinel_comparison(training, frame).to_csv(out / 'paired_stage_sentinels.csv', index=False)
    opportunity_pairs(frame).to_csv(out / 'paired_opportunity_probes.csv', index=False)
    summary = {'status': 'descriptive tables complete; no new primary tests or predictor fitting',
               'completed_at': now(), 'matched_prompt_sources': 16, 'new_primary_tests': 0,
               'input_hashes': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in [train_path, confirmation_path, policy_path, Path(__file__).resolve()]},
               'limitations': ['Joint actions do not identify temporal action order.',
                              'Prompt dispersion uses five fixed configurations on sixteen matched sources.',
                              'Sentinel changes mix generation variation, coding variation, and possible deployment drift.',
                              'Four sentinel templates with two requests cannot establish absence of drift.',
                              'Opportunity probes change available facts; eight sources do not establish a general trait.']}
    (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')


if __name__ == '__main__':
    main()
