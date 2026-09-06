#!/usr/bin/env python3
"""Publication figure for the completed measurement-development pilot only."""
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/llm-persona-matplotlib-v3')
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
PILOT=ROOT/'artifacts/educational_personality_v2/prospective_pilot'
OUT=ROOT/'paper/educational_personality_v3/figures'
EVENTS=[('answer_reveal','Answer revelation'),('reasoning_elicitation','Reasoning elicitation'),
        ('affect_acknowledgement','Affect acknowledgement'),('worked_explanation','Worked explanation'),
        ('learner_choice','Learner choice'),('epistemic_qualification','Epistemic qualification'),
        ('information_request','Missing-fact request'),('unsupported_ability_claim','Unsupported ability claim')]


def main():
    summary=json.loads((PILOT/'natural_diagnostics_v2_2_repaired/summary.json').read_text())
    if summary['valid_judge_requests']!=480 or summary['invalid_or_missing']:
        raise ValueError('Only the complete measurement pilot may be plotted')
    measurement=PILOT/'measurement_summary/event_measurement.csv'
    pair_path=PILOT/'natural_diagnostics_v2_2_repaired/pairwise_agreement.csv'
    frame=pd.read_csv(measurement).set_index('event')
    pairs=pd.read_csv(pair_path)
    if set(frame.index)!={k for k,_ in EVENTS} or not frame.n.eq(160).all(): raise ValueError('Wrong event coverage')
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,
                         'axes.spines.right':False,'axes.spines.left':False,'svg.fonttype':'none',
                         'pdf.fonttype':42,'ps.fonttype':42})
    fig,axes=plt.subplots(1,2,figsize=(8.1,4.6),sharey=True,gridspec_kw={'wspace':.12})
    primary='#21618C'; secondary='#7B8791'
    for ax,key,title in zip(axes,['positive_agreement','negative_agreement'],['Agreement on presence','Agreement on absence']):
        for i,(event,label) in enumerate(EVENTS):
            values=pairs.loc[pairs.event.eq(event),key].to_numpy()
            color=primary if i<3 else secondary
            valid=values[np.isfinite(values)]
            if len(valid):
                ax.hlines(i,float(valid.min()),float(valid.max()),color=color,linewidth=2.0,zorder=2)
                ax.scatter(valid,np.full(len(valid),i)+np.linspace(-.085,.085,len(valid)),s=26,
                           color=color,edgecolor='white',linewidth=.5,zorder=3)
        ax.set_xlim(-.035,1.045)
        ax.set_xticks([0,.25,.5,.75,1],['0','.25','.50','.75','1.00'])
        ax.set_ylim(len(EVENTS)-.5,-.5)
        ax.set_title(title,fontsize=10,pad=12)
        ax.grid(axis='x',alpha=.22,zorder=0)
        ax.axhline(2.5,color='#CBD2D8',linewidth=.7)
        ax.tick_params(axis='y',length=0,pad=8)
        ax.set_xlabel('Pairwise agreement')
    axes[0].set_yticks(range(len(EVENTS)),[label for _,label in EVENTS])
    for i,label in enumerate(axes[0].get_yticklabels()):
        if i<3: label.set_color(primary); label.set_fontweight('bold')
    for i,(event,_) in enumerate(EVENTS):
        n=int(frame.loc[event,'positive'])
        axes[1].text(1.075,i,f'{n}/160',va='center',ha='left',fontsize=8.5,
                     color=primary if i<3 else secondary,transform=axes[1].get_yaxis_transform())
    axes[1].text(1.075,-.72,'Majority\npositives',ha='left',va='bottom',fontsize=8,
                 transform=axes[1].get_yaxis_transform())
    fig.suptitle('Measurement-development pilot',x=.56,y=.98,fontsize=12,fontweight='bold')
    fig.text(.31,.02,'Dots: the three coder pairs. Lines: their range, not confidence intervals.',fontsize=8,color='#48535D')
    fig.subplots_adjust(left=.29,right=.89,bottom=.14,top=.85)
    OUT.mkdir(parents=True,exist_ok=True)
    for ext in ['png','svg','pdf']:
        fig.savefig(OUT/('measurement_pilot.'+ext),dpi=300,bbox_inches='tight',facecolor='white')
    plt.close(fig)
    caption=('Measurement-development pilot, not prospective confirmation. All 160 unchanged tutor responses have '
             'three structurally valid event codes. Dots are pairwise positive or negative agreement; connecting lines '
             'show the range across coder pairs, not sampling uncertainty. Blue rows are the three prospectively selected '
             'primary behavior endpoints. Counts show majority-positive responses. Missing-fact requests have only one '
             'majority positive, so their high total agreement cannot establish positive-case reliability. Unsupported '
             'ability claims have substantially weaker positive agreement. Events are not assumed to be independent personality factors.\n')
    (OUT/'measurement_pilot_caption.md').write_text(caption)
    meta={'status':'rendered completed pilot measurement; no confirmatory personality claim',
          'responses':160,'judge_outputs':480,'figure':'measurement_pilot',
          'inputs':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [measurement,pair_path,Path(__file__).resolve()]}}
    (OUT/'measurement_pilot_provenance.json').write_text(json.dumps(meta,indent=2)+'\n')
    print('Rendered measurement_pilot.png, .svg, .pdf and caption/provenance')

if __name__=='__main__': main()
