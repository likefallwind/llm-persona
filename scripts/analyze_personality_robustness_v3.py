#!/usr/bin/env python3
"""Evaluate judge-panel and training-source sensitivity around locked forecasts."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd

import predict_personality_events_v3 as predictor
import personality_style_competitor_v3 as style
from analyze_personality_confirmation_v3 import PRIMARY,COMPARISONS,losses_and_comparisons
from lock_personality_judge_sensitivity_v3 import panel_labels
from run_personality_formal_stage_v3 import ROOT,BASE,validate_stage,verify_files


def resample_sources(frame,selected):
    if not set(selected)<=set(frame.source_group): raise ValueError('Unknown source in resample')
    pieces=[]
    for draw,source in enumerate(selected):
        part=frame[frame.source_group.eq(source)].copy()
        part['original_source_group']=source
        # Distinct draws retain their bootstrap multiplicity even when the
        # primary predictor equalizes weights within each source cluster.
        part['source_group']=f'bootstrap_draw_{draw}'
        pieces.append(part)
    if not pieces: raise ValueError('Empty source resample')
    return pd.concat(pieces,ignore_index=True)


def evaluate_panels(diagnostics,output):
    lock_path=BASE/'judge_sensitivity_lock.json'
    lock=json.loads(lock_path.read_text())
    verify_files(lock['files'])
    labels=panel_labels(pd.read_csv(diagnostics/'event_codes.csv'))
    cf=pd.read_csv(diagnostics/'consensus.csv')
    eligible=set(cf[(cf.panel=='main')&cf.arm.eq('canonical')].blind_id)
    labels=labels[labels.blind_id.isin(eligible)&labels.event.isin(PRIMARY)]
    predictions=pd.read_csv(BASE/'locked_judge_sensitivity/predictions.csv')
    rows=[]
    for panel,forecasts in predictions.groupby('judge_panel'):
        observed=labels[labels.judge_panel.eq(panel)]
        _,source,comparisons=losses_and_comparisons(forecasts,observed)
        source['judge_panel']=panel
        source.to_csv(output/('source_losses_'+panel+'.csv'),index=False)
        # Sensitivities are not additional independent primary hypothesis tests.
        comparisons=comparisons.drop(columns=['p_one_sided_gain','p_holm_six','t_statistic'])
        comparisons['judge_panel']=panel
        rows.append(comparisons)
    combined=pd.concat(rows,ignore_index=True)
    combined.to_csv(output/'judge_sensitivity_comparisons.csv',index=False)
    combined.groupby(['event','comparison']).mean_difference.agg(['min','max']).to_csv(output/'judge_gain_ranges.csv')
    return combined


def training_resampling(diagnostics,output,repetitions):
    train=pd.read_csv(BASE/'locked_predictions/training_frame.csv')
    test=pd.read_csv(BASE/'locked_predictions/confirmation_input_frame.csv')
    observed=pd.read_csv(diagnostics/'consensus.csv')
    if set(train.source_group)&set(test.source_group): raise ValueError('Original train/test sources overlap')
    models=json.loads((BASE/'locked_predictions/models.json').read_text())
    style_models=json.loads((BASE/'locked_predictions/style_models.json').read_text())
    penalties={(m['event'],m['baseline']):m['penalty'] for m in models}
    penalties.update({(m['event'],'training_style_profile'):m['penalty'] for m in style_models})
    source_ids=sorted(train.source_group.unique())
    rng=np.random.default_rng(20260905)
    draws=[rng.choice(source_ids,size=len(source_ids),replace=True).tolist() for _ in range(repetitions)]
    rows=[]
    for event in PRIMARY:
        original=train[train.event.eq(event)]
        labels=observed[observed.event.eq(event)][['blind_id','present']]
        target=test.merge(labels,on='blind_id',how='left',validate='one_to_one')
        if target.present.isna().any() or len(target)!=1280: raise ValueError('Missing confirmation target')
        y=target.present.to_numpy(float)
        for index,draw in enumerate(draws):
            sampled=resample_sources(original,draw)
            risks={}
            for baseline in [*predictor.BASELINES,'training_style_profile']:
                # The frozen loss weights sum to the row count. Keep the
                # penalty/loss-weight ratio fixed when a cluster draw changes N.
                penalty=penalties[(event,baseline)]*len(sampled)/len(original)
                if baseline=='training_style_profile':
                    p,_=style.fit_predict(sampled,target,penalty)
                else:
                    p,_=predictor.fit_predict(sampled,target,baseline,penalty)
                risk=pd.DataFrame({'source':target.source_group,'brier':(p-y)**2}).groupby('source').brier.mean().mean()
                risks[baseline]=float(risk)
            for name,baseline,model in COMPARISONS:
                rows.append({'event':event,'replicate':index,'comparison':name,'gain':risks[baseline]-risks[model],
                             'training_rows':len(sampled),'unique_original_training_sources':len(set(draw)),
                             'default_minus_style_risk':risks['default_profile']-risks['training_style_profile']})
        print(json.dumps({'event':event,'training_source_resamples_completed':repetitions}),flush=True)
    frame=pd.DataFrame(rows)
    frame.to_csv(output/'training_resampling.csv',index=False)
    quantiles=frame.groupby(['event','comparison']).gain.quantile([.025,.5,.975]).unstack()
    quantiles.columns=['training_resampling_q025','training_resampling_median','training_resampling_q975']
    quantiles.to_csv(output/'training_resampling_quantiles.csv')
    (output/'training_source_draws.json').write_text(json.dumps(draws,indent=2)+'\n')
    return frame


def generator_deletion(diagnostics,output):
    lock=json.loads((BASE/'generator_deletion_lock.json').read_text())
    verify_files(lock['files'])
    predictions=pd.read_csv(BASE/'locked_generator_deletion/predictions.csv')
    observed=pd.read_csv(diagnostics/'consensus.csv')
    observed=observed[(observed.panel=='main')&observed.arm.eq('canonical')&observed.event.isin(PRIMARY)]
    rows=[]
    for deleted,forecasts in predictions.groupby('deleted_generator'):
        labels=observed[observed.model.ne(deleted)]
        if len(labels)!=3072 or labels.model.nunique()!=4:
            raise ValueError('Wrong generator-deletion confirmation grid')
        _,source,comparisons=losses_and_comparisons(forecasts,labels)
        comparisons=comparisons.drop(columns=['p_one_sided_gain','p_holm_six','t_statistic'])
        comparisons['deleted_generator']=deleted
        rows.append(comparisons)
    result=pd.concat(rows,ignore_index=True)
    result.to_csv(output/'generator_deletion_comparisons.csv',index=False)
    return result


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--diagnostics',type=Path,required=True)
    ap.add_argument('--output',type=Path,default=BASE/'confirmation_robustness')
    ap.add_argument('--training-resamples',type=int,default=200)
    args=ap.parse_args()
    if args.training_resamples<1: raise ValueError('At least one resample is required')
    validate_stage('confirmation')
    summary=json.loads((args.diagnostics/'summary.json').read_text())
    if summary['invalid_or_missing'] or summary['valid_judge_requests']!=12120:
        raise ValueError('Complete confirmation coding required')
    args.output.mkdir(parents=True,exist_ok=True)
    panels=evaluate_panels(args.diagnostics,args.output)
    deletions=generator_deletion(args.diagnostics,args.output)
    resampling=training_resampling(args.diagnostics,args.output,args.training_resamples)
    report={'status':'judge and training-source sensitivity calculations complete; not independent replications',
            'judge_panels':int(panels.judge_panel.nunique()),'training_resamples':args.training_resamples,
            'generator_deletion_panels':int(deletions.deleted_generator.nunique()),
            'training_resampling_comparisons':len(resampling),
            'input_hashes':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in
                            [BASE/'prediction_lock.json',BASE/'judge_sensitivity_lock.json',BASE/'generator_deletion_lock.json',args.diagnostics/'event_codes.csv',
                             args.diagnostics/'consensus.csv',Path(__file__).resolve()]},
            'limitations':['Judge panels reuse responses; alternative consensus does not create external validity.',
                           'Training resampling keeps the originally selected regularization ratio fixed, without reselecting hyperparameters.',
                           'Training quantiles condition on these confirmation labels and are not the primary source-bootstrap confidence intervals.',
                           'This analysis cannot remove unmeasured common biases shared by the judges.']}
    (args.output/'summary.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__': main()
