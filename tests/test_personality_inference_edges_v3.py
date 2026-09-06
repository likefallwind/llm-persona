import sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from audit_personality_inference_edges_v3 import neutral_interpretation


def test_zero_variance_is_not_promoted_to_equivalence():
    rows = [dict(model=f'm{m}', event=f'e{e}', arm=arm, sources=16,
                 source_standard_error=0.0 if m == 0 else .01,
                 supports_neutral_equivalence=True)
            for m in range(5) for e in range(3) for arm in ['neutral_a', 'neutral_b']]
    result = neutral_interpretation(pd.DataFrame(rows))
    assert result.frozen_numerical_equivalence_flag.sum() == 30
    assert result.degenerate_source_interval.sum() == 6
    assert result.equivalence_support_for_narrative.sum() == 24
    assert not result[result.model.eq('m0')].equivalence_support_for_narrative.any()
