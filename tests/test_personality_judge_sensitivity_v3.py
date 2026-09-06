import sys
from pathlib import Path
import pandas as pd
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from lock_personality_judge_sensitivity_v3 import panel_labels


def fixture_codes():
    rows=[]
    for model in ['MiniMax-M2.7','MiniMax-M3','deepseek-v4-pro','glm-5.3','doubao-seed-2.0-lite']:
        for judge,y in [('MiniMax-M3',1),('deepseek-v4-pro',0),('glm-5.3',0)]:
            rows.append({'blind_id':model,'event':'answer_reveal','model_requested':model,'judge_returned':judge,'present':y})
    return pd.DataFrame(rows)


def test_disagreement_stays_fractional_and_minimax_family_is_excluded():
    labels=panel_labels(fixture_codes())
    assert labels.judge_panel.nunique()==8 and len(labels)==40
    foreign=labels[labels.judge_panel.eq('exclude_generator_family')].set_index('model')
    assert foreign.loc['MiniMax-M2.7','present']==0
    assert foreign.loc['MiniMax-M3','present']==0
    assert foreign.loc['deepseek-v4-pro','present']==.5
    assert foreign.loc['glm-5.3','present']==.5
    assert foreign.loc['doubao-seed-2.0-lite','present']==pytest.approx(1/3)
    assert foreign.loc['doubao-seed-2.0-lite','coders']==3
    tied=labels[labels.judge_panel.eq('without_glm-5.3')]
    assert tied.present.eq(.5).all()


def test_missing_or_duplicated_coders_cannot_become_sensitivity_evidence():
    codes=fixture_codes()
    with pytest.raises(ValueError,match='Missing individual coder'): panel_labels(codes.iloc[1:])
    with pytest.raises(ValueError,match='Duplicate coder'): panel_labels(pd.concat([codes,codes.iloc[:1]]))
