import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from diagnose_cue_calibration_v4 import assign_folds, fit_calibration, heldout_predictions, predict_calibration


def fixture_panel():
    rows=[]
    for domain in ['d0','d1','d2','d3']:
        for i in range(8):
            for arm in ['canonical','explicit','implicit']:
                for model in ['m0','m1']:
                    for pole in [0,1]:
                        rows.append(dict(domain=domain,source_family=f'{domain}s{i}',arm=arm,model=model,
                                         probability=.25 if pole==0 else .75,present=(i+pole)%2))
    return assign_folds(pd.DataFrame(rows))


def test_folds_are_balanced_and_source_disjoint():
    frame=fixture_panel()
    unique=frame[['domain','source_family','fold']].drop_duplicates()
    assert len(unique)==32
    assert unique.groupby(['domain','fold']).size().eq(2).all()
    assert frame.groupby('source_family').fold.nunique().eq(1).all()


@pytest.mark.parametrize('method',['identity','global_logistic','per_model_logistic'])
def test_test_source_labels_cannot_change_predictions(method):
    frame=fixture_panel()
    original,_=heldout_predictions(frame,'explicit','explicit',method,0)
    frame.loc[frame.fold==0,'present']=1-frame.loc[frame.fold==0,'present']
    changed,_=heldout_predictions(frame,'explicit','explicit',method,0)
    np.testing.assert_allclose(original.calibrated_probability,changed.calibrated_probability,rtol=0,atol=0)


@pytest.mark.parametrize('method',['global_logistic','per_model_logistic'])
def test_canonical_training_never_uses_target_labels(method):
    frame=fixture_panel()
    original,_=heldout_predictions(frame,'explicit','canonical',method,0)
    frame.loc[frame.arm!='canonical','present']=1-frame.loc[frame.arm!='canonical','present']
    changed,_=heldout_predictions(frame,'explicit','canonical',method,0)
    np.testing.assert_allclose(original.calibrated_probability,changed.calibrated_probability,rtol=0,atol=0)


def test_calibration_can_correct_underconfident_forecasts():
    p=np.tile([.3,.7],100);y=np.tile([0,1],100)
    params=fit_calibration(p,y)
    assert params['converged'] and 1<params['slope']<=5
    q=predict_calibration(p,params)
    assert ((q-y)**2).mean()<((p-y)**2).mean()
    assert np.isfinite(q).all() and ((q>=0)&(q<=1)).all()


@pytest.mark.parametrize('p,y',[([],[]),([.2],[np.nan]),([1.2],[1])])
def test_invalid_fit_inputs_rejected(p,y):
    with pytest.raises(ValueError):fit_calibration(p,y)


def test_duplicate_domain_membership_rejected():
    frame=fixture_panel()
    extra=frame.iloc[:1].assign(domain='wrong')
    with pytest.raises(ValueError):assign_folds(pd.concat([frame,extra]))
