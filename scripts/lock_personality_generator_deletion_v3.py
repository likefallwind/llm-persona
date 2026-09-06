#!/usr/bin/env python3
"""Pre-confirmation sensitivity to one generator dominating the aggregate gain.

Each deleted generator is removed from BOTH fitting and evaluation. This is not
prediction for an unseen model and not a causal attribution of the full gain.
"""
import hashlib
import json
from pathlib import Path
import pandas as pd
import predict_personality_events_v3 as predictor
import personality_style_competitor_v3 as style
from lock_personality_predictions_v3 import predict_and_export
from prepare_personality_pilot_v2 import write_frozen
from run_personality_requests_v2 import now
from run_personality_formal_stage_v3 import ROOT,BASE,validate_stage

PRIMARY=['answer_reveal','reasoning_elicitation','affect_acknowledgement']


def main():
    validate_stage('confirmation')
    if (BASE/'confirmation/run/responses.jsonl').exists(): raise ValueError('Confirmation outputs already exist')
    lock_path=BASE/'generator_deletion_lock.json'
    if lock_path.exists(): raise ValueError('Deletion forecasts already locked')
    train=pd.read_csv(BASE/'locked_predictions/training_frame.csv')
    test=pd.read_csv(BASE/'locked_predictions/confirmation_input_frame.csv')
    configurations=sorted(train.model.unique())
    if len(configurations)!=5 or set(test.model)!=set(configurations): raise ValueError('Wrong generator panel')
    models,rows=[],[]
    for deleted in configurations:
        fitting=train[train.model.ne(deleted)&train.event.isin(PRIMARY)]
        target=test[test.model.ne(deleted)]
        if target.model.nunique()!=4 or len(target)!=1024: raise ValueError('Deletion evaluation grid incomplete')
        for event,data in fitting.groupby('event'):
            if len(data)!=1024 or data.model.nunique()!=4: raise ValueError('Deletion training grid incomplete')
            for baseline in [*predictor.BASELINES,'training_style_profile']:
                if baseline=='training_style_profile':
                    penalty,tuning=style.select_penalty(data)
                    probability,model=style.fit_predict(data,target,penalty)
                else:
                    penalty,tuning=predictor.select_penalty(data,baseline)
                    probability,model=predict_and_export(data,target,baseline,penalty)
                models.append({'deleted_generator':deleted,'event':event,'baseline':baseline,**model,'tuning':tuning})
                for item,p in zip(target.to_dict('records'),probability):
                    rows.append({**item,'deleted_generator':deleted,'event':event,'baseline':baseline,'probability':float(p)})
        print(json.dumps({'deleted_generator':deleted,'models_complete':len(models)}),flush=True)
    if len(models)!=75 or len(rows)!=76800: raise ValueError('Wrong deletion forecast count')
    out=BASE/'locked_generator_deletion'
    out.mkdir(parents=True,exist_ok=True)
    write_frozen(out/'predictions.csv',pd.DataFrame(rows).to_csv(index=False))
    write_frozen(out/'models.json',json.dumps(models,indent=2)+'\n')
    source=[*out.iterdir(),BASE/'prediction_lock.json',Path(__file__).resolve()]
    lock={'status':'generator-deletion forecasts locked before confirmation generation','locked_at':now(),
          'deleted_configurations':configurations,'fitted_models':len(models),'prediction_rows':len(rows),
          'primary_prediction_lock_sha256':hashlib.sha256((BASE/'prediction_lock.json').read_bytes()).hexdigest(),
          'files':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in source},
          'limitations':['The omitted generator is not evaluated; this is not unseen-generator generalization.',
                         'Removing a generator changes the target mixture, so the difference is not a causal contribution.',
                         'The five-generator majority-label comparisons remain primary regardless of these results.']}
    write_frozen(lock_path,json.dumps(lock,indent=2)+'\n')

if __name__=='__main__': main()
