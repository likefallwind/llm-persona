import sys
from pathlib import Path
import pandas as pd
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from analyze_personality_robustness_v3 import resample_sources
from predict_personality_events_v3 import weights_for


def test_source_draw_multiplicity_survives_source_equal_weighting():
    original=pd.DataFrame({'source_group':['a']*4+['b']*8,'present':[1]*4+[0]*8})
    sampled=resample_sources(original,['a','a','b'])
    w=weights_for(sampled)
    assert (w*sampled.present).sum()/w.sum()==pytest.approx(2/3)
    assert sampled.source_group.nunique()==3
    assert sampled.original_source_group.nunique()==2
    assert original.source_group.tolist()==['a']*4+['b']*8
    with pytest.raises(ValueError,match='Unknown source'): resample_sources(original,['c'])
