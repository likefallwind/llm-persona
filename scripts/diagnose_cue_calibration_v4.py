"""Post-result, source-held-out calibration diagnosis; no external calls."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import expit, logit

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'artifacts/educational_personality_v4/cue_transfer'
OUT = BASE / 'calibration_diagnosis'
METHODS = ('identity', 'global_logistic', 'per_model_logistic')
BASELINES = ('domain_profile', 'conditional_profile')


def fit_calibration(probability, labels):
    p, y = np.asarray(probability, float), np.asarray(labels, float)
    if not len(p) or p.shape != y.shape or not np.isfinite(p).all() or not np.isin(y,[0,1]).all():
        raise ValueError('Calibration requires complete binary training observations')
    if not ((p >= 0) & (p <= 1)).all():
        raise ValueError('Invalid forecast')
    x=logit(np.clip(p,1e-6,1-1e-6))
    def objective(theta):
        a,b=theta;z=a+b*x;r=expit(z)-y
        return (np.logaddexp(0,z)-y*z).sum()+.5*(a*a+(b-1)**2), np.array([r.sum()+a,(r*x).sum()+b-1])
    result=minimize(objective,np.array([0.,1.]),jac=True,method='L-BFGS-B',bounds=[(-10,10),(0,5)],
                    options={'ftol':1e-12,'gtol':1e-8,'maxiter':2000})
    if not result.success:
        raise ValueError('Calibration optimization failed: '+str(result.message))
    a,b=map(float,result.x)
    return {'intercept':a,'slope':b,'converged':True,'training_answers':len(y),
            'boundary_hit':bool(abs(a)>=10-1e-6 or b<=1e-6 or b>=5-1e-6)}


def predict_calibration(probability, parameters):
    return expit(parameters['intercept']+parameters['slope']*logit(np.clip(probability,1e-6,1-1e-6)))


def assign_folds(frame):
    sources=frame[['source_family','domain']].drop_duplicates()
    if sources.source_family.duplicated().any():
        raise ValueError('Source assigned to multiple domains')
    mapping={}
    for _,part in sources.groupby('domain'):
        names=sorted(part.source_family,key=lambda s:hashlib.sha256(('cue-calibration-v4:'+s).encode()).hexdigest())
        if len(names)!=8:
            raise ValueError('Each domain requires exactly eight source families')
        mapping.update({name:i%4 for i,name in enumerate(names)})
    return frame.assign(fold=frame.source_family.map(mapping))


def heldout_predictions(frame, target_arm, training_arm, method, fold):
    train=frame[(frame.arm==training_arm)&(frame.fold!=fold)]
    test=frame[(frame.arm==target_arm)&(frame.fold==fold)].copy()
    if train.empty or test.empty or set(train.source_family)&set(test.source_family):
        raise ValueError('Invalid source split')
    rows=[]
    if method=='identity':
        test['calibrated_probability']=test.probability
        return test,rows
    if method not in METHODS:
        raise ValueError('Unknown calibration method')
    models=sorted(test.model.unique()) if method=='per_model_logistic' else ['all']
    test['calibrated_probability']=np.nan
    for model in models:
        selected=train if model=='all' else train[train.model==model]
        mask=np.ones(len(test),dtype=bool) if model=='all' else test.model.eq(model)
        params=fit_calibration(selected.probability,selected.present)
        test.loc[mask,'calibrated_probability']=predict_calibration(test.loc[mask,'probability'],params)
        rows.append({'model_group':model,'training_arm':training_arm,'target_arm':target_arm,
                     'method':method,'fold':fold,**params})
    if test.calibrated_probability.isna().any():
        raise ValueError('Incomplete calibrated predictions')
    return test,rows


def source_interval(part):
    part=part.sort_values(['domain','source_family']).reset_index(drop=True)
    if part.source_family.duplicated().any():raise ValueError('Duplicate source gain')
    rng=np.random.default_rng(20260908)
    ids=np.concatenate([rng.choice(np.asarray(list(ids)),(10000,len(ids)),replace=True)
                        for ids in part.groupby('domain').groups.values()],axis=1)
    lo,hi=np.quantile(part.gain.to_numpy()[ids].mean(axis=1),[.025,.975])
    return {'gain':part.gain.mean(),'bootstrap_95_low':lo,'bootstrap_95_high':hi,'sources':len(part)}


def main():
    files=[BASE/'predictions.csv',BASE/'json_recovery/combined_diagnostics/consensus.csv',
           ROOT/'research/79_cue_calibration_protocol_v4.md',Path(__file__)]
    forecasts=pd.read_csv(files[0]);labels=pd.read_csv(files[1])
    forecasts=forecasts[forecasts.event.eq('affect_acknowledgement') & forecasts.baseline.isin(BASELINES)
                        & forecasts.arm.isin(['canonical','explicit','implicit'])]
    frame=forecasts.merge(labels[['blind_id','event','present']],on=['blind_id','event'],how='left',validate='many_to_one')
    if len(frame)!=7680 or frame.duplicated(['blind_id','baseline']).any() or not frame.present.isin([0,1]).all():
        raise ValueError('Incomplete acknowledgement panel')
    frame=assign_folds(frame)
    output,parameters=[],[]
    for regime,targets in [('canonical_only',['canonical','explicit','implicit']),('target_arm',['explicit','implicit'])]:
        for target in targets:
            training='canonical' if regime=='canonical_only' else target
            for baseline in BASELINES:
                part=frame[frame.baseline==baseline]
                for method in METHODS:
                    for fold in range(4):
                        pred,params=heldout_predictions(part,target,training,method,fold)
                        pred=pred.assign(regime=regime,method=method)
                        output.append(pred)
                        parameters += [dict(r,regime=regime,baseline=baseline) for r in params]
    scored=pd.concat(output,ignore_index=True)
    scored['brier']=(scored.calibrated_probability-scored.present)**2
    group=['regime','arm','method','baseline']
    absolute=scored.groupby(group).agg(brier=('brier','mean'),answers=('brier','size')).reset_index()
    if not absolute.answers.eq(1280).all():raise ValueError('Unequal prediction coverage')
    sources=scored.groupby(group+['domain','source_family']).brier.mean().unstack('baseline').reset_index()
    sources['gain']=sources.domain_profile-sources.conditional_profile
    comparison=pd.DataFrame([{'regime':regime,'arm':arm,'method':method,**source_interval(part)}
                             for (regime,arm,method),part in sources.groupby(['regime','arm','method'])])
    reference=comparison[comparison.method=='identity'][['regime','arm','gain']].rename(columns={'gain':'identity_gain'})
    comparison=comparison.merge(reference,on=['regime','arm'],validate='many_to_one')
    comparison['gain_change_from_identity']=comparison.gain-comparison.identity_gain
    OUT.mkdir(exist_ok=True)
    scored[['regime','arm','method','baseline','source_family','domain','model','blind_id','fold',
            'probability','calibrated_probability','present','brier']].to_csv(OUT/'crossfit_predictions.csv',index=False)
    pd.DataFrame(parameters).to_csv(OUT/'parameters.csv',index=False)
    absolute.to_csv(OUT/'absolute_losses.csv',index=False)
    sources.to_csv(OUT/'source_gains.csv',index=False)
    comparison.to_csv(OUT/'comparisons.csv',index=False)
    frame[['source_family','domain','fold']].drop_duplicates().sort_values(['domain','fold','source_family']).to_csv(OUT/'folds.csv',index=False)
    report={'status':'post-result calibration diagnosis complete','new_api_calls':0,'new_human_annotations':0,
            'new_hypothesis_tests':0,'fitted_calibrators':len(parameters),'boundary_hits':sum(r['boundary_hit'] for r in parameters),
            'prediction_rows':len(scored),'quality_goal_complete':False,
            'interpretation':'Target-arm calibration uses target-expression labels; it is not zero-shot transfer. Intervals condition on crossfit forecasts.',
            'input_hashes':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}}
    (OUT/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
    print(comparison.to_string(index=False))


if __name__=='__main__':main()
