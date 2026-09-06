#!/usr/bin/env python3
"""Describe complete pilot measurement, preserving rare-event and judge caveats."""
import argparse
import hashlib
import json
from pathlib import Path
import pandas as pd

FAMILIES={'MiniMax-M3':'minimax','MiniMax-M2.7':'minimax','glm-5.3':'glm',
          'deepseek-v4-pro':'deepseek','doubao-seed-2.0-lite':'doubao'}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--base',type=Path,required=True)
    ap.add_argument('--deployment-audit',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args()
    summary=json.loads((a.base/'summary.json').read_text())
    if summary['invalid_or_missing'] or summary['valid_judge_requests']!=480:
        raise ValueError('Requires the complete 160-response, three-judge measurement pilot')
    audit=json.loads(a.deployment_audit.read_text())
    if audit['status']!='pass' or any(len(v)!=1 for v in audit['requested_to_returned'].values()):
        raise ValueError('Unverified generator deployment identity')
    names={k:v[0] for k,v in audit['requested_to_returned'].items()}
    codes=pd.read_csv(a.base/'event_codes.csv')
    codes['model']=codes.model_requested.map(names)
    cf=pd.read_csv(a.base/'consensus.csv')
    cf['model']=cf.model.map(names)
    if codes.model.isna().any() or cf.model.isna().any(): raise ValueError('Unknown model')
    agreement=pd.read_csv(a.base/'pairwise_agreement.csv')
    pooled=cf.groupby('event').agg(n=('present','size'),positive=('present','sum'),prevalence=('present','mean'),unanimity=('unanimous','mean'))
    for key in ['agreement','positive_agreement','negative_agreement']:
        pooled[key+'_min']=agreement.groupby('event')[key].min()
        pooled[key+'_max']=agreement.groupby('event')[key].max()
    pooled['opportunity_warning']=pooled.positive.apply(lambda n:'rare positive; aggregate agreement is insufficient' if n<10 else '')
    a.output.mkdir(parents=True,exist_ok=True)
    pooled.to_csv(a.output/'event_measurement.csv')
    cf.groupby(['event','model']).present.agg(['size','mean']).to_csv(a.output/'model_prevalence.csv')
    repeats=pd.read_csv(a.base/'repeat_agreement.csv')
    repeats['model']=repeats.model_requested.map(names)
    repeats.drop(columns='model_requested').to_csv(a.output/'repeat_agreement.csv',index=False)
    # Fractional judge means keep two-judge disagreement as 0.5, never silently
    # classify tied panels as absence. Every leave-one panel retains all models.
    panels=[]
    for omit in [None,*sorted(codes.judge_returned.unique())]:
        part=codes if omit is None else codes[codes.judge_returned!=omit]
        means=part.groupby(['blind_id','event','model']).present.mean().reset_index()
        means['panel']='all_three' if omit is None else 'without_'+omit
        panels.append(means)
    long=pd.concat(panels)
    long.to_csv(a.output/'judge_panel_soft_labels.csv',index=False)
    long.groupby(['panel','model','event']).present.mean().to_csv(a.output/'judge_panel_prevalence.csv')
    codes['same_family']=codes.model.map(FAMILIES).eq(codes.judge_returned.map(FAMILIES))
    foreign=codes[~codes.same_family].groupby(['blind_id','event','model']).agg(
        present=('present','mean'),judges=('judge_returned','nunique')).reset_index()
    foreign.groupby(['model','event']).agg(prevalence=('present','mean'),judges_per_answer=('judges','min')).to_csv(a.output/'exclude_generator_family.csv')
    cf.groupby(['model','event','progress','affect']).present.agg(['size','mean']).to_csv(a.output/'student_state_prevalence.csv')
    joint=cf.pivot(index=['blind_id','model','template','progress','affect','repeat'],columns='event',values='present').reset_index()
    joint['action_combination']=[('answer_and_elicit' if e else 'answer_only') if r else ('elicit_only' if e else 'neither') for r,e in zip(joint.answer_reveal,joint.reasoning_elicitation)]
    joint.groupby(['model','action_combination']).size().to_csv(a.output/'answer_elicitation_combinations.csv')
    metadata={'status':'measurement-development pilot; no confirmatory personality claim',
              'responses':160,'source_templates':4,'models_actual':sorted(cf.model.unique()),'judges':3,
              'rubric_sha256':summary['rubric_sha256'],
              'inputs':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [a.base/'event_codes.csv',a.base/'consensus.csv',a.deployment_audit,Path(__file__)]},
              'limitations':['Four templates do not support stable population or cross-domain inference.',
                             'Different generators sharing a family with a judge can induce measurement bias.',
                             'Excluding generator-family judges changes the judge panel; this is sensitivity, not truth.',
                             'Joint answer/elicitation categories contain no evidence about event order.',
                             'Repeated event agreement may reflect constant behavior rather than reliability.',
                             'Pilot-informed endpoint choices must be disclosed and frozen before confirmation.']}
    (a.output/'summary.json').write_text(json.dumps(metadata,indent=2)+'\n')
    print(pooled.to_string())

if __name__=='__main__': main()
