"""Exact full-source sensitivity ranges; hypothetical votes never become observed codes."""
import sys,json,itertools
from pathlib import Path
import pandas as pd
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'scripts'))
from analyze_archive_behavior_validation_v4 import crossfit,gain_tables
from prepare_personality_cue_transfer_v4 import sha
b=root/'artifacts/educational_personality_v4/archive_validation';out=b/'full_coder_bounds';out.mkdir(exist_ok=True)
events=['answer_reveal','reasoning_elicitation','affect_acknowledgement']
codes=pd.read_csv(b/'measurement_diagnostics/transport_diagnostic/event_codes.csv')
frame=pd.read_csv(b/'analysis_identified/identified_consensus.csv');frame=frame[frame.event.isin(events)]
results=[];scenarios=[]
for judge in sorted(codes.judge_requested.unique()):
 actual=codes[(codes.judge_requested==judge)&codes.event.isin(events)][['blind_id','event','present']]
 panel=frame.drop(columns=['present']).merge(actual,on=['blind_id','event'],how='left',validate='one_to_one')
 for event,part in panel.groupby('event'):
  missing=part.loc[part.present.isna(),'blind_id'].tolist()
  assert len(part)==3584 and len(missing) in (0,2)
  for scenario,values in enumerate(itertools.product((0,1),repeat=len(missing))):
   hypothetical=part.copy()
   for blind_id,value in zip(missing,values):hypothetical.loc[hypothetical.blind_id==blind_id,'present']=value
   assert hypothetical.present.notna().all()
   prediction=crossfit(hypothetical)
   assert prediction.source_family.nunique()==256
   loss,gain=gain_tables(prediction)
   results.append(gain.assign(judge=judge,scenario=scenario,hypothetical_missing_votes=len(missing)))
   scenarios.append({'judge':judge,'event':event,'scenario':scenario,'hypothetical_values':dict(zip(missing,values)),'observed_labels_modified':False})
r=pd.concat(results);r.to_csv(out/'scenario_gains.csv',index=False)
g=r.groupby(['judge','arm','event','comparison'])
bounds=g.agg(scenarios=('scenario','size'),gain_min=('mean','min'),gain_max=('mean','max'),interval_low_min=('bootstrap_95_low','min'),interval_low_max=('bootstrap_95_low','max'),interval_high_min=('bootstrap_95_high','min'),interval_high_max=('bootstrap_95_high','max')).reset_index()
bounds.to_csv(out/'gain_bounds.csv',index=False)
(out/'scenario_definitions.json').write_text(json.dumps(scenarios,indent=2)+'\n')
inputs=[Path(__file__).resolve(),b/'measurement_diagnostics/transport_diagnostic/event_codes.csv',b/'analysis_identified/identified_consensus.csv',root/'scripts/analyze_archive_behavior_validation_v4.py']
summary={'status':'complete full-source individual-coder sensitivity bounds','sources':256,'judges':3,'events':3,'scalar_gain_comparisons':len(bounds),'eventwise_scenarios':len(scenarios),'actual_missing_labels_imputed':False,'hypothetical_scenarios_are_not_observed_data':True,'new_api_calls':0,'interpretation':'All four possible missing-vote assignments per event are evaluated for DeepSeek; events have separable forecasts and losses, so these cover all 64 joint assignments for the six missing primary labels. Each forecast uses the unchanged full 256-source fold rule.','limits':'Post-hoc exact range over missing votes, conditional on observed labels and original fixed-crossfit interval method; not a missingness model or semantic validity proof.','input_hashes':{str(p.relative_to(root)):sha(p) for p in inputs}}
(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(bounds[(bounds.arm=='scaffolding')&bounds.comparison.str.startswith('same')].round(6).to_string(index=False))
print('pedagogy');print(bounds[(bounds.arm=='pedagogy')&bounds.comparison.str.startswith('same')].round(6).to_string(index=False))
print('cross-instruction max reveal/elicit',bounds[(bounds.event!='affect_acknowledgement')&bounds.comparison.str.startswith('other')].gain_max.max())
