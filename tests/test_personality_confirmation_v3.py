import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import analyze_personality_confirmation_v3 as analysis


def test_holm_protects_the_entire_predeclared_family():
    p=[.04,.001,.02,.9,.08,.03]
    np.testing.assert_allclose(analysis.holm(p),[.12,.006,.10,.9,.16,.12])


def test_source_uncertainty_does_not_treat_repeated_answers_as_new_sources():
    predictions=[]
    labels=[]
    for source in range(32):
        for event in analysis.PRIMARY:
            for repeat in range(2):
                blind=f'{source}:{repeat}'
                y=int(source%3==0)
                labels.append({'blind_id':blind,'event':event,'present':y})
                for baseline,p in [('context',.5),('default_profile',.2),('domain_profile',.2),('conditional_profile',.25)]:
                    predictions.append({'blind_id':blind,'event':event,'baseline':baseline,'source_group':f's{source}','probability':p})
    predictions=pd.DataFrame(predictions); labels=pd.DataFrame(labels)
    _,_,a=analysis.losses_and_comparisons(predictions,labels)
    more_predictions=pd.concat([predictions,predictions.assign(blind_id=predictions.blind_id+'extra')])
    more_labels=pd.concat([labels,labels.assign(blind_id=labels.blind_id+'extra')])
    _,_,b=analysis.losses_and_comparisons(more_predictions,more_labels)
    np.testing.assert_allclose(a.source_standard_error,b.source_standard_error)
    assert set(a.sources)=={32}
    with pytest.raises(ValueError,match='lacks a confirmation label'):
        analysis.losses_and_comparisons(predictions,labels.iloc[1:])


def test_zero_variance_does_not_receive_automatic_significance():
    result=analysis.paired_stats(np.full(32,.02),bootstrap=100)
    assert result['p_one_sided_gain']==1
    assert result['test_note']
