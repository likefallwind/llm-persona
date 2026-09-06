"""Known data-generating laws and invariances for the prospective predictor."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.special import expit

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import predict_personality_events_v3 as prediction


def fixture_frame():
    rows=[]
    for source in range(12):
        for domain in ('math','science'):
            for model in ('a','b','c'):
                for progress in ('wrong','partial'):
                    for affect in ('calm','frustrated'):
                        rows.append(dict(source_group=f's{source}',domain=domain,model=model,
                                         progress=progress,affect=affect,present=.5,
                                         blind_id=f'{source}-{domain}-{model}-{progress}-{affect}',event='test'))
    return pd.DataFrame(rows)


def split(frame):
    return frame[frame.source_group.isin(['s0','s1','s2','s3','s4','s5'])],frame[~frame.source_group.isin(['s0','s1','s2','s3','s4','s5'])]


def test_nested_feature_blocks_preserve_common_penalty_geometry():
    train,test=split(fixture_frame())
    full,_,w,ranks=prediction.design(train,test,'conditional_profile')
    np.testing.assert_allclose(full.T@(w[:,None]*full)/w.sum(),np.eye(full.shape[1]),atol=1e-10)
    assert ranks==[7,2,2,6]
    for baseline in prediction.BASELINES:
        x,_,_,_=prediction.design(train,test,baseline)
        np.testing.assert_allclose(x,full[:,:x.shape[1]],atol=1e-10)


def test_exact_additive_law_has_no_manufactured_conditional_gain():
    frame=fixture_frame()
    frame['present']=expit(.2+frame.model.map({'a':-.7,'b':.2,'c':.8})+.4*frame.progress.eq('partial')-.3*frame.affect.eq('frustrated'))
    train,test=split(frame)
    simple,_=prediction.fit_predict(train,test,'default_profile',penalty=0)
    complex_,_=prediction.fit_predict(train,test,'conditional_profile',penalty=0)
    np.testing.assert_allclose(simple,test.present,atol=2e-5)
    np.testing.assert_allclose(complex_,simple,atol=2e-5)


def test_student_state_pattern_must_beat_model_by_domain_competitor():
    frame=fixture_frame()
    eta=np.where(frame.model.eq('a')==frame.progress.eq('partial'),2.,-2.)
    frame['present']=expit(eta+.2*frame.domain.eq('science'))
    train,test=split(frame)
    domain,_=prediction.fit_predict(train,test,'domain_profile')
    conditional,_=prediction.fit_predict(train,test,'conditional_profile')
    assert np.mean((conditional-test.present)**2)<.01*np.mean((domain-test.present)**2)
    changed,_=prediction.fit_predict(train,test.assign(present=1-test.present),'conditional_profile')
    np.testing.assert_array_equal(conditional,changed)


def test_constant_labels_and_category_renaming_do_not_create_evidence():
    train,test=split(fixture_frame())
    predictions=[prediction.fit_predict(train.assign(present=0),test,b)[0] for b in prediction.BASELINES]
    for p in predictions[1:]: np.testing.assert_array_equal(p,predictions[0])
    frame=fixture_frame()
    frame['present']=expit(frame.model.map({'a':-.8,'b':.3,'c':1.})+.6*frame.progress.eq('partial'))
    train,test=split(frame)
    p,_=prediction.fit_predict(train,test,'conditional_profile')
    renamed=frame.replace({'model':{'a':'zeta','b':'alpha','c':'beta'}})
    a,b=split(renamed)
    q,_=prediction.fit_predict(a,b,'conditional_profile')
    np.testing.assert_allclose(p,q,atol=2e-7)
