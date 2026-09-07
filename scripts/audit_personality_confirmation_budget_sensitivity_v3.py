#!/usr/bin/env python3
"""Enumerate missing-code uncertainty without changing frozen primary results."""
import hashlib
from itertools import product
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import t as student_t

from analyze_personality_confirmation_v3 import PRIMARY, COMPARISONS, holm
from analyze_personality_coding_v2 import pair_agreement
from run_personality_formal_stage_v3 import ROOT, BASE, verify_files
from run_personality_requests_v2 import now, read_rows


def label_bounds(frame, old_codes, missing_blinds):
    """Keep observed labels elsewhere; allow either bit for the missing coder."""
    result = frame.copy()
    result['lower'] = result.present
    result['upper'] = result.present
    for blind in missing_blinds:
        for event in result.event.unique():
            known = old_codes[(old_codes.blind_id == blind) & (old_codes.event == event)]
            if len(known) != 2 or set(known.judge_requested) != {'MiniMax-M3', 'deepseek-v4-pro'}:
                raise ValueError('Each missing GLM event must have the two fixed original coders')
            total = int(known.present.sum())
            mask = result.blind_id.eq(blind) & result.event.eq(event)
            if mask.sum() != 1:
                raise ValueError('Missing or duplicated consensus item-event')
            result.loc[mask, ['lower', 'upper']] = [int(total > 1), int(total > 0)]
    if not ((result.lower <= result.present) & (result.present <= result.upper)).all():
        raise ValueError('Observed amended label outside possible fixed-panel majority')
    return result


def primary_ranges(predictions, bounded, canonical_blinds):
    rows, repetitions = [], []
    for event in bounded.event.unique():
        labels = bounded[(bounded.event == event) & bounded.panel.eq('main') & bounded.arm.eq('canonical')].copy()
        if len(labels) != 1280 or labels.source_family.nunique() != 32:
            raise ValueError('Canonical coverage changed')
        for bits in product([0, 1], repeat=len(canonical_blinds)):
            variant = labels.copy()
            for blind, bit in zip(canonical_blinds, bits):
                mask = variant.blind_id.eq(blind)
                variant.loc[mask, 'present'] = variant.loc[mask, 'upper' if bit else 'lower']
            case = 'case_' + ''.join(map(str, bits))
            for model, part in variant.groupby('model'):
                wide = part.pivot(index=['source_family', 'progress', 'affect'], columns='repeat', values='present')
                if wide.shape != (128, 2) or wide.isna().any().any():
                    raise ValueError('Incomplete repetition panel')
                repetitions.append(dict(event=event, model=model, assignment=case, **pair_agreement(wide[0], wide[1])))
            if event not in PRIMARY:
                continue
            scored = predictions[predictions.event == event].merge(
                variant[['blind_id', 'present']], on='blind_id', validate='many_to_one')
            if len(scored) != len(predictions[predictions.event == event]):
                raise ValueError('A locked forecast lost its label')
            scored['loss'] = (scored.probability - scored.present) ** 2
            source = scored.groupby(['source_group', 'baseline']).loss.mean().unstack()
            if len(source) != 32 or source.isna().any().any():
                raise ValueError('Source-level forecast comparison incomplete')
            for name, baseline, model in COMPARISONS:
                values = (source[baseline] - source[model]).to_numpy()
                mean = float(values.mean())
                se = float(values.std(ddof=1) / np.sqrt(len(values)))
                p = 1.0 if se == 0 else float(student_t.sf(mean / se, len(values) - 1))
                rows.append(dict(event=event, comparison=name, assignment=case, sources=32,
                                 mean_difference=mean, source_standard_error=se, p_one_sided_gain=p))
    return pd.DataFrame(rows), pd.DataFrame(repetitions)


def main():
    policy_path = BASE / 'confirmation_budget_amendment.json'
    policy = json.loads(policy_path.read_text())
    verify_files(policy['files'])
    selection_path = BASE / 'confirmation/measurement_selection.json'
    selection = json.loads(selection_path.read_text())
    diagnostics = ROOT / selection['diagnostics']
    report = json.loads((diagnostics / 'summary.json').read_text())
    if report['invalid_or_missing'] or report['valid_judge_requests'] != 12120:
        raise ValueError('Complete audited measurement required')
    verify_files(report['input_hashes'])
    frame = pd.read_csv(diagnostics / 'consensus.csv')
    if len(frame) != 32320 or frame.duplicated(['blind_id', 'event']).any():
        raise ValueError('Invalid full confirmation frame')
    old_path = BASE / 'confirmation/budget_recovery/original_diagnostics/event_codes.csv'
    old = pd.read_csv(old_path)
    jobs = read_rows(BASE / 'confirmation/judge/v2_2/manifest.jsonl')
    allowed = set(policy['allowed_request_ids'])
    missing = sorted(j['blind_id'] for j in jobs if j['request_id'] in allowed)
    if len(missing) != 6 or len(set(missing)) != 6:
        raise ValueError('Amendment does not contain exactly six unique answers')
    bounded = label_bounds(frame, old, missing)
    canonical_blinds = sorted(set(bounded.loc[bounded.blind_id.isin(missing) & bounded.panel.eq('main') & bounded.arm.eq('canonical'), 'blind_id']))
    if len(canonical_blinds) != 2:
        raise ValueError('Recorded two-canonical-answer sensitivity scope changed')
    pred_path = BASE / 'locked_predictions/predictions.csv'
    verify_files(json.loads((BASE / 'prediction_lock.json').read_text())['files'])
    variants, repeats = primary_ranges(pd.read_csv(pred_path), bounded, canonical_blinds)
    summary = variants.groupby(['event', 'comparison']).agg(
        assignments=('assignment', 'size'), effect_min=('mean_difference', 'min'),
        effect_max=('mean_difference', 'max'), raw_p_min=('p_one_sided_gain', 'min'),
        raw_p_max=('p_one_sided_gain', 'max')).reset_index()
    if len(summary) != 6 or not summary.assignments.eq(4).all():
        raise ValueError('Expected four assignments for each of the six tests')
    summary['holm_upper_bound'] = holm(summary.raw_p_max)
    summary['positive_gain_for_all_assignments'] = summary.effect_min > 0
    summary['significant_for_all_assignments_conservative'] = summary.holm_upper_bound < .05
    observed_path = BASE / 'confirmation_analysis/primary_prediction_comparisons.csv'
    observed = pd.read_csv(observed_path)
    summary = summary.merge(observed[['event', 'comparison', 'mean_difference', 'p_holm_six']],
                            on=['event', 'comparison'], validate='one_to_one')
    if not ((summary.mean_difference >= summary.effect_min - 1e-12) &
            (summary.mean_difference <= summary.effect_max + 1e-12) &
            (summary.p_holm_six <= summary.holm_upper_bound + 1e-12)).all():
        raise ValueError('Observed primary calculations fail enumeration bounds')
    prompt_rows = []
    main = bounded[bounded.panel.eq('main') & bounded.event.isin(PRIMARY)]
    rates = main.groupby(['source_family', 'model', 'event', 'arm'])[['lower', 'upper']].mean().reset_index()
    for (model, event), part in rates.groupby(['model', 'event']):
        lo = part.pivot(index='source_family', columns='arm', values='lower')
        hi = part.pivot(index='source_family', columns='arm', values='upper')
        for arm in ['neutral_a', 'neutral_b', 'ask', 'explain']:
            idx = lo[['canonical', arm]].dropna().index
            if len(idx) != 16:
                raise ValueError('Prompt comparison lacks 16 paired sources')
            prompt_rows.append(dict(model=model, event=event, arm=arm, sources=16,
                effect_min=float((lo.loc[idx, arm] - hi.loc[idx, 'canonical']).mean()),
                effect_max=float((hi.loc[idx, arm] - lo.loc[idx, 'canonical']).mean())))
    out = BASE / 'confirmation_budget_sensitivity'
    out.mkdir(exist_ok=True)
    variants.to_csv(out / 'primary_assignments.csv', index=False)
    summary.to_csv(out / 'primary_ranges.csv', index=False)
    repeats.to_csv(out / 'repeat_assignments.csv', index=False)
    pd.DataFrame(prompt_rows).to_csv(out / 'prompt_effect_ranges.csv', index=False)
    for name, part, keys in [
        ('opportunity_rate_ranges', bounded[bounded.panel.str.startswith('opportunity')], ['model', 'event', 'panel']),
        ('default_rate_ranges', bounded[bounded.panel.eq('main') & bounded.arm.eq('canonical')], ['model', 'event'])]:
        part.groupby(keys).agg(n=('present', 'size'), observed=('present', 'mean'),
                              lower=('lower', 'mean'), upper=('upper', 'mean')).reset_index().to_csv(out / (name + '.csv'), index=False)
    bounded[bounded.blind_id.isin(missing)].to_csv(out / 'affected_consensus_bounds.csv', index=False)
    inputs = [policy_path, selection_path, diagnostics / 'consensus.csv', diagnostics / 'summary.json',
              old_path, pred_path, observed_path, Path(__file__).resolve()]
    receipt = dict(completed_at=now(), status='complete supplemental missing-code sensitivity',
        missing_judge_codes=6, affected_canonical_answers=2, assignments_per_primary_event=4,
        primary_effects=6, primary_effect_signs_all_unchanged=bool((
            ((summary.effect_min > 0) & (summary.mean_difference > 0)) |
            ((summary.effect_max < 0) & (summary.mean_difference < 0)) |
            ((summary.effect_min == 0) & (summary.effect_max == 0) & (summary.mean_difference == 0))).all()),
        holm_upper_bound_rule='Holm applied to per-test maximum raw p-values; monotonicity bounds all joint assignments conservatively.',
        primary_results_replaced=False, fitted_models_changed=False, new_api_calls=0,
        limitations=['Bounds allow either binary GLM code while fixing the other two coders. They do not validate semantic truth.',
                     'Descriptive ranges quantify coding uncertainty, not population sampling uncertainty.',
                     'This supplemental analysis follows the disclosed completion-budget amendment.'],
        input_hashes={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs})
    (out / 'summary.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(summary.to_string(index=False))


if __name__ == '__main__':
    main()
