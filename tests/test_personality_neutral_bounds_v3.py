import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_personality_neutral_bounds_v3 import bounded_interpretation
from analyze_personality_confirmation_v3 import paired_stats


def test_sparse_boundary_counterexample_is_not_population_equivalence():
    # Five one-event source differences and eleven zeros: the nominal t rule
    # supports +/-0.10 even though these observations can arise at its boundary.
    values=np.array([.125]*5+[0.]*11)
    stats=paired_stats(values,alpha=.05/30,bootstrap=10)
    assert stats['t_interval_high']<.10 and stats['source_standard_error']>0
    effects=pd.DataFrame([dict(model=f'm{m}',event=f'e{e}',arm=a,
        supports_neutral_equivalence=True,**stats) for m in range(5) for e in range(3) for a in ['neutral_a','neutral_b']])
    result=bounded_interpretation(effects)
    assert result.nondegenerate_t_equivalence_flag.all()
    assert not result.equivalence_support_for_narrative.any()
    half=result.bounded_source_half_width.iloc[0]
    assert abs(30*2*np.exp(-16*half**2/2)-.05)<1e-12
    assert result.bounded_source_95_low.le(.10).all() and result.bounded_source_95_high.ge(.10).all()
    with pytest.raises(ValueError): bounded_interpretation(effects.assign(mean_difference=1.01))


def test_zero_variance_and_domain_clipping_are_retained():
    effects=pd.DataFrame([dict(model=f'm{m}',event=f'e{e}',arm=a,sources=16,
        mean_difference=1 if m==0 else 0,source_standard_error=0,
        supports_neutral_equivalence=m!=0) for m in range(5) for e in range(3) for a in ['neutral_a','neutral_b']])
    result=bounded_interpretation(effects)
    assert result.degenerate_source_interval.all()
    assert not result.equivalence_support_for_narrative.any()
    assert result.bounded_source_95_low.ge(-1).all() and result.bounded_source_95_high.le(1).all()
