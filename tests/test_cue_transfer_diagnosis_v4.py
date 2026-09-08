import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from diagnose_cue_transfer_v4 import decompose, paired_panel


def test_constant_increment_attributes_pure_rate_shift():
    r=decompose([.2,.4],[.3,.5],[0,0],[1,1])
    assert r['overall_rate_term']==pytest.approx(.2)
    assert r['centered_covariation_term']==pytest.approx(0)


def test_unchanged_prevalence_can_reverse_conditional_gain():
    r=decompose([.5,.5],[.8,.2],[1,0],[0,1])
    assert r['overall_rate_change']==0
    assert r['overall_rate_term']==0
    # Base loss stays .25; expanded loss changes from .04 to .64.
    assert r['gain_change']==pytest.approx(-.6)


def test_group_accounting_matches_direct_losses():
    rng=np.random.default_rng(10)
    b,e=rng.uniform(size=(2,30)); y0,y1=rng.integers(0,2,size=(2,30))
    full=decompose(b,e,y0,y1)
    summed=sum(decompose(b[s],e[s],y0[s],y1[s])['gain_change']*len(b[s])/len(b)
               for s in [slice(0,7),slice(7,18),slice(18,30)])
    assert summed==pytest.approx(full['gain_change'])


def panel():
    rows=[]
    for arm in ['canonical','explicit','implicit']:
        for baseline in ['context','default_profile','domain_profile','conditional_profile']:
            rows.append(dict(source_family='s',domain='d',model='m',progress='wrong',cue_pole='calm',
                             repeat=0,event='ack',arm=arm,baseline=baseline,probability=.4,blind_id=arm))
    return pd.DataFrame(rows),pd.DataFrame([dict(blind_id=a,event='ack',present=1)
                                          for a in ['canonical','explicit','implicit']])


@pytest.mark.parametrize('failure',['missing','changed','duplicate','label'])
def test_invalid_panel_rejected(failure):
    p,y=panel()
    if failure=='missing':p=p.iloc[:-1]
    elif failure=='changed':p.loc[0,'probability']=.8
    elif failure=='duplicate':p=pd.concat([p,p.iloc[:1]])
    else:y=y.iloc[:-1]
    with pytest.raises(ValueError):paired_panel(p,y)


def test_complete_panel_accepted():
    assert len(paired_panel(*panel()))==12
