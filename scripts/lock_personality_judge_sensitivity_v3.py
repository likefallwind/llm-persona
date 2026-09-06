#!/usr/bin/env python3
"""Lock judge-panel sensitivity forecasts without accessing confirmation output."""
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd

import predict_personality_events_v3 as predictor
import personality_style_competitor_v3 as style
from lock_personality_predictions_v3 import predict_and_export
from prepare_personality_pilot_v2 import write_frozen
from run_personality_requests_v2 import now
from run_personality_formal_stage_v3 import ROOT,BASE,validate_stage,verify_files

PRIMARY=['answer_reveal','reasoning_elicitation','affect_acknowledgement']
JUDGES=['MiniMax-M3','deepseek-v4-pro','glm-5.3']
FAMILIES={'MiniMax-M3':'minimax','MiniMax-M2.7':'minimax','deepseek-v4-pro':'deepseek',
          'glm-5.3':'glm','doubao-seed-2.0-lite':'doubao'}


def panel_labels(codes):
    required={'blind_id','event','model_requested','judge_returned','present'}
    if not required<=set(codes): raise ValueError('Missing coding metadata')
    if set(codes.judge_returned)!=set(JUDGES): raise ValueError('Unexpected judge deployments')
    if set(codes.model_requested)-set(FAMILIES): raise ValueError('Unknown generator family')
    key=['blind_id','event','model_requested']
    if codes.duplicated(key+['judge_returned']).any(): raise ValueError('Duplicate coder record')
    if not codes.present.isin([0,1]).all(): raise ValueError('Expected binary individual codes')
    counts=codes.groupby(key).judge_returned.nunique()
    if (counts!=3).any(): raise ValueError('Missing individual coder')
    selections={'all_three_soft':codes}
    for judge in JUDGES:
        selections['single_'+judge]=codes[codes.judge_returned.eq(judge)]
        selections['without_'+judge]=codes[~codes.judge_returned.eq(judge)]
    keep=codes.model_requested.map(FAMILIES).ne(codes.judge_returned.map(FAMILIES))
    selections['exclude_generator_family']=codes[keep]
    output=[]
    for name,part in selections.items():
        labels=part.groupby(key).agg(present=('present','mean'),coders=('judge_returned','nunique')).reset_index()
        if len(labels)!=len(counts): raise ValueError('Sensitivity drops a generator or item')
        labels=labels.rename(columns={'model_requested':'model'})
        labels['judge_panel']=name
        output.append(labels)
    return pd.concat(output,ignore_index=True)


def main():
    validate_stage('confirmation') # Verifies the primary prediction lock only; no API request.
    if (BASE/'confirmation/run/responses.jsonl').exists():
        raise ValueError('Cannot lock judge sensitivities after confirmation outputs exist')
    lock_path=BASE/'judge_sensitivity_lock.json'
    if lock_path.exists(): raise ValueError('Judge sensitivity predictions already locked')
    selection=json.loads((BASE/'training/measurement_selection.json').read_text())
    diagnostics=ROOT/selection['diagnostics']
    summary=json.loads((diagnostics/'summary.json').read_text())
    if summary['invalid_or_missing'] or summary['valid_judge_requests']!=3840:
        raise ValueError('Training measurement incomplete')
    codes=pd.read_csv(diagnostics/'event_codes.csv')
    labels=panel_labels(codes)
    train=pd.read_csv(BASE/'locked_predictions/training_frame.csv')
    test=pd.read_csv(BASE/'locked_predictions/confirmation_input_frame.csv')
    train=train[train.event.isin(PRIMARY)].drop(columns='present')
    labels=labels[labels.event.isin(PRIMARY)]
    out=BASE/'locked_judge_sensitivity'
    models,forecasts=[],[]
    for (panel,event),group in labels.groupby(['judge_panel','event']):
        fit=train[train.event.eq(event)].merge(group,on=['blind_id','event','model'],validate='one_to_one')
        if len(fit)!=1280 or fit.present.isna().any(): raise ValueError('Incomplete sensitivity training grid')
        for baseline in [*predictor.BASELINES,'training_style_profile']:
            if baseline=='training_style_profile':
                penalty,tuning=style.select_penalty(fit)
                probability,model=style.fit_predict(fit,test,penalty)
            else:
                penalty,tuning=predictor.select_penalty(fit,baseline)
                probability,model=predict_and_export(fit,test,baseline,penalty)
            models.append({'judge_panel':panel,'event':event,'baseline':baseline,**model,'tuning':tuning})
            for item,p in zip(test.to_dict('records'),probability):
                forecasts.append({**item,'judge_panel':panel,'event':event,'baseline':baseline,'probability':float(p)})
        print(json.dumps({'judge_panel':panel,'event':event,'models_complete':len(models)}),flush=True)
    if len(models)!=120 or len(forecasts)!=153600: raise ValueError('Wrong panel/model count')
    out.mkdir(parents=True,exist_ok=True)
    write_frozen(out/'predictions.csv',pd.DataFrame(forecasts).to_csv(index=False))
    write_frozen(out/'models.json',json.dumps(models,indent=2)+'\n')
    write_frozen(out/'training_panel_labels.csv',labels.to_csv(index=False))
    source=[*out.iterdir(),BASE/'prediction_lock.json',diagnostics/'event_codes.csv',Path(__file__).resolve()]
    report={'status':'judge-panel sensitivity forecasts locked before confirmation generation',
            'locked_at':now(),'primary_prediction_lock_sha256':hashlib.sha256((BASE/'prediction_lock.json').read_bytes()).hexdigest(),
            'judge_panels':sorted(labels.judge_panel.unique()),'primary_events':PRIMARY,
            'fitted_models':len(models),'prediction_rows':len(forecasts),
            'files':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in source},
            'limitations':['These panels reuse the same responses and are not independent replications.',
                           'Two-coder ties are 0.5; none is silently changed to absence.',
                           'Excluding the generator family changes the judge panel by generator and cannot be treated as ground truth.',
                           'Forecasts are evaluated against the corresponding confirmation judge panel, not automatically against majority labels.',
                           'The six primary comparisons remain the majority-label comparisons; sensitivity panels cannot replace them.']}
    write_frozen(lock_path,json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='files'},indent=2))

if __name__=='__main__': main()
