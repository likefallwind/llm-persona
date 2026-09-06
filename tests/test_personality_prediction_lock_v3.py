import sys
from pathlib import Path
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from test_personality_prediction_v3 import fixture_frame,split
from lock_personality_predictions_v3 import predict_and_export
import personality_style_competitor_v3 as style
import predict_personality_events_v3 as primary


def test_parameter_export_preserves_frozen_predictions():
    frame=fixture_frame()
    frame['present']=np.where(frame.model.eq('a')==frame.progress.eq('partial'),.9,.1)
    train,test=split(frame)
    original=primary.minimize
    for baseline in primary.BASELINES:
        p,model=predict_and_export(train,test,baseline,1.)
        reference,_=primary.fit_predict(train,test,baseline,1.)
        np.testing.assert_array_equal(p,reference)
        assert primary.minimize is original
        assert model['coefficients'] is not None
    p,model=predict_and_export(train.assign(present=0),test,'conditional_profile',1.)
    assert model['coefficients'] is None and 0<model['constant_probability']<1


def test_style_competitor_uses_no_test_text_or_labels():
    frame=fixture_frame()
    frame['raw_log_words']=frame.model.map({'a':2.,'b':3.,'c':4.})
    frame['raw_structure']=frame.model.map({'a':.8,'b':.2,'c':.4})
    frame['present']=frame.model.map({'a':.2,'b':.4,'c':.8})
    train,test=split(frame)
    p,model=style.fit_predict(train,test,1.)
    altered=test.assign(raw_log_words=9999,raw_structure=-9999,present=1-test.present)
    q,_=style.fit_predict(train,altered,1.)
    np.testing.assert_array_equal(p,q)
    assert set(model['profiles'])=={'a','b','c'}
    with pytest.raises(ValueError,match='source overlap'):
        style.fit_predict(train,train,1.)
