#!/usr/bin/env python3
"""Fit only training sources and lock predictions before any confirmation answers.

The frozen v3 predictor is called unchanged. A parameter-export wrapper records
its optimizer result and independently verifies the resulting test probabilities;
this wrapper never changes the optimizer, features, penalties or predictions.
"""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
from scipy.special import expit
import predict_personality_events_v3 as predictor
import personality_style_competitor_v3 as style
from prepare_personality_pilot_v2 import write_frozen
from run_personality_requests_v2 import digest,read_rows,now
from run_personality_formal_stage_v3 import ROOT,BASE,verify_files


def predict_and_export(train,test,baseline,penalty):
    """Observe SciPy's fitted coefficients without altering the frozen solver."""
    original=predictor.minimize
    fits=[]
    def recording_minimize(*args,**kwargs):
        fitted=original(*args,**kwargs)
        fits.append(fitted)
        return fitted
    try:
        predictor.minimize=recording_minimize
        probabilities,info=predictor.fit_predict(train,test,baseline,penalty)
    finally:
        predictor.minimize=original
    x,z,w,ranks=predictor.design(train,test,baseline)
    if fits:
        coefficients=fits[-1].x.tolist()
        verified=expit(z@np.asarray(coefficients))
        constant=None
    else:
        coefficients=None
        constant=float(probabilities[0])
        verified=np.full(len(test),constant)
    np.testing.assert_allclose(verified,probabilities,rtol=0,atol=1e-12)
    return probabilities,{'baseline':baseline,'penalty':penalty,'coefficients':coefficients,
                           'constant_probability':constant,'block_ranks':ranks,
                           'design_reconstruction':'Frozen predictor.design using the locked training input order and metadata.',
                           'training_design_sha256':digest(x.tolist()),'test_design_sha256':digest(z.tolist()),
                           **info}


def frames(diagnostics,judge_base):
    summary=json.loads((diagnostics/'summary.json').read_text())
    if summary['invalid_or_missing'] or summary['valid_judge_requests']!=3840:
        raise ValueError('Requires all 1280 training answers with three valid judges')
    cf=pd.read_csv(diagnostics/'consensus.csv')
    mapping=read_rows(judge_base/'unblinding.jsonl')
    meta=pd.DataFrame([{'blind_id':r['blind_id'],'domain':r['domain'],'source_group':r['source_family']} for r in mapping])
    cf=cf.merge(meta,on='blind_id',validate='many_to_one').sort_values(['event','blind_id']).reset_index(drop=True)
    if len(cf)!=10240 or set(cf.panel)!={'main'} or set(cf.arm)!={'canonical'}:
        raise ValueError('Training panel is not the frozen complete canonical grid')
    samples={s['sample_id']:s for s in read_rows(BASE/'confirmation/scenarios.jsonl')}
    test=[]
    for job in read_rows(BASE/'confirmation/generation_manifest.jsonl'):
        row=samples[job['sample_id']]
        if row['panel']!='main' or row['arm']!='canonical': continue
        blind=hashlib.sha256(('personality-coding-v2:'+job['request_id']).encode()).hexdigest()[:20]
        test.append({'blind_id':blind,'source_group':row['source_family'],'template':row['template'],
                     'domain':row['domain'],'progress':row['progress'],'affect':row['affect'],
                     'model':job['model'],'repeat':job['repeat'],'request_id':job['request_id']})
    test=pd.DataFrame(test).sort_values('blind_id').reset_index(drop=True)
    if len(test)!=1280 or test.source_group.nunique()!=32:
        raise ValueError('Confirmation prediction grid differs from protocol')
    if set(test.source_group)&set(cf.source_group): raise ValueError('Source overlap')
    return cf,test


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--diagnostics',type=Path,required=True)
    ap.add_argument('--judge-base',type=Path,required=True)
    args=ap.parse_args()
    design=json.loads((BASE/'design_freeze.json').read_text())
    verify_files(design['files'])
    if (BASE/'confirmation/run/responses.jsonl').exists():
        raise ValueError('Confirmation generation already has records; cannot create a prospective lock')
    if (BASE/'prediction_lock.json').exists():
        raise ValueError('Prediction lock already exists; do not refit')
    audit=json.loads((BASE/'training/generation_audit.json').read_text())
    if audit['status']!='pass' or any(v!=[k] for k,v in audit['requested_to_returned'].items()):
        raise ValueError('Training generator deployment audit failed')
    train,test=frames(args.diagnostics,args.judge_base)
    style_inputs=pd.DataFrame([{'blind_id':r['blind_id'],**style.extract_style(r['response'])}
                               for r in read_rows(args.judge_base/'unblinding.jsonl')])
    train=train.merge(style_inputs,on='blind_id',validate='many_to_one')
    all_predictions,models=[],[]
    style_predictions,style_models=[],[]
    for event,data in train.groupby('event'):
        for baseline in predictor.BASELINES:
            penalty,tuning=predictor.select_penalty(data,baseline)
            p,model=predict_and_export(data,test,baseline,penalty)
            models.append({'event':event,**model,'tuning':tuning})
            for item,probability in zip(test.to_dict('records'),p):
                all_predictions.append({**item,'event':event,'baseline':baseline,'probability':float(probability)})
        penalty,tuning=style.select_penalty(data)
        p,model=style.fit_predict(data,test,penalty)
        style_models.append({'event':event,**model,'tuning':tuning})
        for item,probability in zip(test.to_dict('records'),p):
            style_predictions.append({**item,'event':event,'baseline':'training_style_profile','probability':float(probability)})
    out=BASE/'locked_predictions'
    out.mkdir(parents=True,exist_ok=True)
    write_frozen(out/'predictions.csv',pd.DataFrame(all_predictions).to_csv(index=False))
    write_frozen(out/'models.json',json.dumps(models,indent=2)+'\n')
    write_frozen(out/'style_predictions.csv',pd.DataFrame(style_predictions).to_csv(index=False))
    write_frozen(out/'style_models.json',json.dumps(style_models,indent=2)+'\n')
    write_frozen(out/'training_frame.csv',train.to_csv(index=False))
    write_frozen(out/'confirmation_input_frame.csv',test.to_csv(index=False))
    sources=[*out.iterdir(),BASE/'training/generation_audit.json',args.diagnostics/'consensus.csv',
             args.diagnostics/'summary.json',args.judge_base/'unblinding.jsonl',Path(__file__).resolve(),
             ROOT/'scripts/analyze_personality_coding_v2.py',ROOT/'scripts/personality_style_competitor_v3.py']
    lock={'status':'training-fitted predictions frozen before confirmation generation','locked_at':now(),
          'design_sha256':hashlib.sha256((BASE/'design_freeze.json').read_bytes()).hexdigest(),
          'training_sources':int(train.source_group.nunique()),'confirmation_sources':int(test.source_group.nunique()),
          'training_answers':int(train.blind_id.nunique()),'confirmation_answers_predicted':len(test),
          'prediction_rows':len(all_predictions),'fitted_models':len(models),
          'secondary_style_models':len(style_models),'secondary_style_predictions':len(style_predictions),
          'files':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
          'environment':{'python':sys.version,'numpy':importlib.metadata.version('numpy'),
                         'scipy':importlib.metadata.version('scipy'),'pandas':importlib.metadata.version('pandas'),
                         'scikit-learn':importlib.metadata.version('scikit-learn')},
          'limits':['These are fixed training-fitted forecasts of known model configurations on new source problems.',
                    'No confirmation labels or outputs were used to fit or select these primary predictors.',
                    'The secondary style competitor uses only training source means of log word count and marked-line fraction.',
                    'Length/formatting can be consequences of teaching policy; style competition is not causal adjustment.']}
    write_frozen(BASE/'prediction_lock.json',json.dumps(lock,indent=2)+'\n')
    print(json.dumps({k:v for k,v in lock.items() if k!='files'},indent=2))

if __name__=='__main__': main()
