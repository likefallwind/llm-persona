"""Post-result, descriptive decomposition of unchanged forecasts; no API or fit."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'artifacts/educational_personality_v4/cue_transfer'
OUT = BASE / 'competing_explanations'
KEYS = ['source_family', 'domain', 'model', 'progress', 'cue_pole', 'repeat', 'event']
COMPARISONS = [('default', 'context', 'default_profile'),
               ('conditional', 'domain_profile', 'conditional_profile')]


def decompose(base, expanded, original, changed):
    arrays = [np.asarray(x, dtype=float) for x in (base, expanded, original, changed)]
    if len({a.shape for a in arrays}) != 1 or arrays[0].ndim != 1 or arrays[0].size == 0:
        raise ValueError('Nonempty matching one-dimensional arrays required')
    if not all(np.isfinite(a).all() and ((a >= 0) & (a <= 1)).all() for a in arrays):
        raise ValueError('Probabilities and observations must be finite in [0,1]')
    b, e, y0, y1 = arrays
    delta, change = e-b, y1-y0
    mean_term = 2 * change.mean() * delta.mean()
    centered = 2 * ((change-change.mean()) * (delta-delta.mean())).mean()
    gb = ((b-y1)**2 - (b-y0)**2).mean()
    ge = ((e-y1)**2 - (e-y0)**2).mean()
    observed = gb-ge
    assert np.isclose(observed, mean_term+centered, atol=1e-12)
    return {'answers': len(b), 'base_brier_change': gb, 'expanded_brier_change': ge,
            'gain_change': observed, 'overall_rate_change': change.mean(),
            'mean_probability_increment': delta.mean(), 'overall_rate_term': mean_term,
            'centered_covariation_term': centered,
            'identity_residual': observed-mean_term-centered}


def paired_panel(predictions, labels):
    p = predictions[predictions.arm.isin(['canonical', 'explicit', 'implicit'])].copy()
    if p.duplicated(KEYS+['arm', 'baseline']).any():
        raise ValueError('Duplicate prediction cell')
    if labels.duplicated(['blind_id', 'event']).any():
        raise ValueError('Duplicate measurement')
    p = p.merge(labels[['blind_id', 'event', 'present']], on=['blind_id', 'event'],
                how='left', validate='many_to_one')
    if not p.present.isin([0, 1]).all():
        raise ValueError('Missing or nonbinary measurement')
    counts = p.groupby(KEYS).size()
    if not counts.eq(12).all():
        raise ValueError('Each cell needs three arms and four forecasts')
    w = p.pivot(index=KEYS, columns=['arm', 'baseline'], values='probability')
    if w.isna().any().any():
        raise ValueError('Incomplete prediction panel')
    for arm in ('explicit', 'implicit'):
        if not np.allclose(w['canonical'], w[arm], rtol=0, atol=1e-14):
            raise ValueError('Forecasts differ across arms; decomposition invalid')
    return p


def main():
    files = [BASE/'predictions.csv', BASE/'json_recovery/combined_diagnostics/consensus.csv',
             ROOT/'research/77_cue_transfer_competing_explanations_v4.md', Path(__file__)]
    p = paired_panel(pd.read_csv(files[0]), pd.read_csv(files[1]))
    p['brier'] = (p.probability-p.present)**2
    absolute = p.groupby(['arm', 'event', 'baseline']).agg(
        brier=('brier','mean'), observed_rate=('present','mean'),
        mean_forecast=('probability','mean'), answers=('present','size')).reset_index()
    results, groups = [], []
    for event, part in p.groupby('event'):
        w = part.pivot(index=KEYS, columns=['arm','baseline'], values='probability')
        y = part.drop_duplicates(KEYS+['arm']).pivot(index=KEYS, columns='arm', values='present')
        assert w.index.equals(y.index)
        for name, base, expanded in COMPARISONS:
            b, e = w['canonical'][base].to_numpy(), w['canonical'][expanded].to_numpy()
            for arm in ('explicit','implicit'):
                result = decompose(b,e,y.canonical.to_numpy(),y[arm].to_numpy())
                results.append({'event':event,'comparison':name,'arm':arm,**result})
                cells = w.index.to_frame(index=False)
                cells['contribution'] = 2*(y[arm].to_numpy()-y.canonical.to_numpy())*(e-b)
                for dimension in ('model','domain','progress','cue_pole'):
                    accumulated = 0.
                    for value, block in cells.groupby(dimension):
                        contribution = block.contribution.sum()/len(cells)
                        accumulated += contribution
                        groups.append({'event':event,'comparison':name,'arm':arm,
                                       'dimension':dimension,'value':value,
                                       'answers':len(block),'weighted_gain_change':contribution})
                    assert np.isclose(accumulated,result['gain_change'],atol=1e-12)
    ack = p[p.event.eq('affect_acknowledgement') & p.baseline.eq('conditional_profile')]
    rates = ack.groupby(['arm','model','cue_pole']).agg(
        observed=('present','mean'),forecast=('probability','mean'),answers=('present','size')).reset_index()
    contrasts = []
    for (arm,model), part in rates.groupby(['arm','model']):
        part=part.set_index('cue_pole')
        contrasts.append({'arm':arm,'model':model,
                          'observed_pole_difference':part.loc['frustrated','observed']-part.loc['calm','observed'],
                          'forecast_pole_difference':part.loc['frustrated','forecast']-part.loc['calm','forecast']})
    OUT.mkdir(exist_ok=True)
    absolute.to_csv(OUT/'absolute_losses.csv',index=False)
    pd.DataFrame(results).to_csv(OUT/'gain_change_decomposition.csv',index=False)
    pd.DataFrame(groups).to_csv(OUT/'group_contributions.csv',index=False)
    rates.to_csv(OUT/'acknowledgement_pole_rates.csv',index=False)
    pd.DataFrame(contrasts).to_csv(OUT/'acknowledgement_pole_contrasts.csv',index=False)
    summary = {'status':'post-result descriptive diagnosis complete', 'api_calls':0,'fitting_calls':0,
               'new_hypothesis_tests':0, 'quality_goal_complete':False,
               'comparison_rows':len(results),'group_rows':len(groups),
               'maximum_identity_residual':max(abs(r['identity_residual']) for r in results),
               'input_hashes':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}}
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(pd.DataFrame(results).query("event == 'affect_acknowledgement' and comparison == 'conditional'").to_string(index=False))


if __name__ == '__main__':
    main()
