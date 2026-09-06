#!/usr/bin/env python3
"""Evaluate previously locked forecasts and paired prompt changes on new sources.

Requires the complete confirmation panel. No model fitting or feature selection
occurs here. Source, not response, is the unit for uncertainty estimates.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import t as student_t

from run_personality_formal_stage_v3 import ROOT,BASE,validate_stage
from run_personality_requests_v2 import read_rows
from analyze_personality_coding_v2 import pair_agreement

PRIMARY=['answer_reveal','reasoning_elicitation','affect_acknowledgement']
COMPARISONS=[('default_vs_context','context','default_profile'),
             ('student_state_vs_domain','domain_profile','conditional_profile')]
SEED=20260905
BOOTSTRAPS=10000


def paired_stats(values,alpha=.05,bootstrap=BOOTSTRAPS):
    x=np.asarray(values,dtype=float)
    if x.ndim!=1 or len(x)<2 or not np.isfinite(x).all():
        raise ValueError('Need at least two finite source-level paired differences')
    n=len(x)
    mean=float(x.mean())
    se=float(x.std(ddof=1)/np.sqrt(n))
    if se==0:
        statistic=None
        p=1.0 # Conservative: no t-test decision from a degenerate sample.
        reason='zero source variance; no t-test decision'
    else:
        statistic=mean/se
        p=float(student_t.sf(statistic,n-1))
        reason=''
    half=float(student_t.ppf(1-alpha/2,n-1)*se)
    rng=np.random.default_rng(SEED)
    samples=x[rng.integers(0,n,size=(bootstrap,n))].mean(axis=1)
    ci=np.quantile(samples,[.025,.975])
    return {'sources':n,'mean_difference':mean,'source_standard_error':se,
            't_statistic':statistic,'p_one_sided_gain':p,'test_note':reason,
            'bootstrap_95_low':float(ci[0]),'bootstrap_95_high':float(ci[1]),
            't_interval_alpha':alpha,'t_interval_low':mean-half,'t_interval_high':mean+half}


def holm(pvalues):
    p=np.asarray(pvalues,float)
    if not np.isfinite(p).all() or (p<0).any() or (p>1).any(): raise ValueError('Invalid p-values')
    order=np.argsort(p,kind='stable')
    adjusted=np.maximum.accumulate(p[order]*(len(p)-np.arange(len(p))))
    result=np.empty(len(p))
    result[order]=np.minimum(1,adjusted)
    return result


def losses_and_comparisons(predictions,labels):
    key=['blind_id','event']
    if labels.duplicated(key).any(): raise ValueError('Duplicate observed item/event')
    scored=predictions.merge(labels[key+['present']],on=key,how='left',validate='many_to_one')
    if scored.present.isna().any(): raise ValueError('A locked forecast lacks a confirmation label')
    if scored.duplicated(key+['baseline']).any(): raise ValueError('Duplicate forecast')
    scored['brier']=(scored.probability-scored.present)**2
    source=scored.groupby(['event','baseline','source_group']).brier.mean().reset_index()
    comparisons=[]
    for event in PRIMARY:
        wide=source[source.event==event].pivot(index='source_group',columns='baseline',values='brier')
        if len(wide)!=32 or wide.isna().any().any(): raise ValueError('Primary comparison lacks 32 complete sources')
        for name,baseline,model in COMPARISONS:
            comparisons.append({'event':event,'comparison':name,'baseline':baseline,'model':model,
                                **paired_stats(wide[baseline]-wide[model])})
    comparisons=pd.DataFrame(comparisons)
    comparisons['p_holm_six']=holm(comparisons.p_one_sided_gain)
    return scored,source,comparisons


def prompt_effects(frame):
    main=frame[(frame.panel=='main')&frame.event.isin(PRIMARY)]
    source=main.groupby(['source_family','model','event','arm']).present.mean().reset_index()
    effects=[]
    for (model,event),data in source.groupby(['model','event']):
        wide=data.pivot(index='source_family',columns='arm',values='present')
        for arm in ['neutral_a','neutral_b','ask','explain']:
            paired=wide[['canonical',arm]].dropna()
            if len(paired)!=16: raise ValueError('Prompt contrast lacks its 16 complete paired sources')
            values=paired[arm]-paired.canonical
            # Simultaneous 95% intervals across five models x three primary
            # events x two neutral arms. Policy arms are descriptive intervals.
            alpha=.05/30 if arm.startswith('neutral') else .05
            result=paired_stats(values,alpha=alpha)
            effects.append({'model':model,'event':event,'arm':arm,**result,
                            'neutral_equivalence_margin':.10 if arm.startswith('neutral') else None,
                            'supports_neutral_equivalence':bool(result['t_interval_low']>-.10 and result['t_interval_high']<.10) if arm.startswith('neutral') else None})
    return source,pd.DataFrame(effects)


def repeat_diagnostics(frame):
    rows=[]
    main=frame[(frame.panel=='main')&frame.arm.eq('canonical')]
    for (model,event),data in main.groupby(['model','event']):
        wide=data.pivot(index=['source_family','progress','affect'],columns='repeat',values='present')
        if wide.isna().any().any() or set(wide.columns)!={0,1} or len(wide)!=128:
            raise ValueError('Incomplete canonical repetition grid')
        source_agreement=wide[0].eq(wide[1]).groupby(level='source_family').mean()
        summary=paired_stats(source_agreement)
        rows.append({'model':model,'event':event,**pair_agreement(wide[0],wide[1]),
                     'source_clusters':len(source_agreement),'agreement_bootstrap_95_low':summary['bootstrap_95_low'],
                     'agreement_bootstrap_95_high':summary['bootstrap_95_high']})
    return pd.DataFrame(rows)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--diagnostics',type=Path,required=True)
    p.add_argument('--output',type=Path,default=BASE/'confirmation_analysis')
    args=p.parse_args()
    validate_stage('confirmation')
    audit=json.loads((BASE/'confirmation/generation_audit.json').read_text())
    if audit['status']!='pass': raise ValueError('Confirmation generation audit failed')
    diagnostics=json.loads((args.diagnostics/'summary.json').read_text())
    if diagnostics['invalid_or_missing'] or diagnostics['valid_judge_requests']!=12120:
        raise ValueError('Requires all 4040 confirmation-stage answers with three valid coders')
    lock=json.loads((BASE/'prediction_lock.json').read_text())
    raw=read_rows(BASE/'confirmation/run/responses.jsonl')
    if min(r['started_at'] for r in raw)<=lock['locked_at']:
        raise ValueError('Confirmation generation began before prediction locking')
    frame=pd.read_csv(args.diagnostics/'consensus.csv')
    if len(frame)!=32320: raise ValueError('Wrong number of confirmation event items')
    canonical=frame[(frame.panel=='main')&frame.arm.eq('canonical')]
    if canonical.blind_id.nunique()!=1280 or canonical.source_family.nunique()!=32:
        raise ValueError('Main confirmation panel differs')
    predictions=pd.read_csv(BASE/'locked_predictions/predictions.csv')
    style=pd.read_csv(BASE/'locked_predictions/style_predictions.csv')
    scored,sources,comparisons=losses_and_comparisons(pd.concat([predictions,style]),canonical)
    out=args.output
    out.mkdir(parents=True,exist_ok=True)
    scored.to_csv(out/'scored_locked_predictions.csv',index=False)
    sources.to_csv(out/'source_prediction_losses.csv',index=False)
    sources.groupby(['event','baseline']).brier.mean().to_csv(out/'prediction_brier.csv')
    comparisons.to_csv(out/'primary_prediction_comparisons.csv',index=False)
    source_effects,effects=prompt_effects(frame)
    source_effects.to_csv(out/'source_prompt_rates.csv',index=False)
    effects.to_csv(out/'paired_prompt_effects.csv',index=False)
    repeat_diagnostics(frame).to_csv(out/'repeat_diagnostics.csv',index=False)
    canonical.groupby(['model','event']).present.agg(['size','mean']).to_csv(out/'default_profiles.csv')
    canonical.groupby(['model','event','progress','affect']).present.agg(['size','mean']).to_csv(out/'student_state_profiles.csv')
    frame[frame.panel.str.startswith('opportunity')].groupby(['model','event','panel']).present.agg(['size','mean']).to_csv(out/'opportunity_probe_rates.csv')
    sentinel=frame[frame.panel.eq('training_sentinel')]
    sentinel.groupby(['model','event','template']).present.mean().to_csv(out/'training_sentinel_rates.csv')
    summary={'status':'complete primary calculations on prospective confirmation; scientific synthesis and sensitivity analyses still required',
             'prediction_sources':32,'prompt_sources':16,'source_bootstrap_repetitions':BOOTSTRAPS,'seed':SEED,
             'primary_hypothesis_tests':6,'primary_p_adjustment':'Holm; one-sided positive Brier gain',
             'neutral_equivalence':'Bonferroni simultaneous 95% paired-t intervals across 30 comparisons inside +/-0.10',
             'prediction_lock_precedes_all_confirmation_requests':True,
             'inputs':{str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest() for path in
                       [BASE/'prediction_lock.json',args.diagnostics/'consensus.csv',Path(__file__).resolve()]},
             'limitations':['Intervals condition on the fitted training profiles and use source sampling approximations.',
                            'The 32 authored confirmation sources are not a representative random sample of education.',
                            'Two source-level observations of zero variance do not establish equality or statistical power.',
                            'Style competition is descriptive and does not establish causal separation from style or ability.',
                            'Single/leave-one judge, training-resampling, content-error and version-drift sensitivities remain separate requirements.']}
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(comparisons.to_string(index=False))

if __name__=='__main__': main()
