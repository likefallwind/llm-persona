import importlib.util
from pathlib import Path
import sys

import pandas as pd

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
import describe_personality_confirmation_v3 as descriptive


def test_joint_actions_keep_both_and_neither():
    rows = []
    for i, (a, e) in enumerate([(0, 0), (1, 0), (0, 1), (1, 1)]):
        for event, present in [('answer_reveal', a), ('reasoning_elicitation', e)]:
            rows.append(dict(blind_id=str(i), model='m', source_family='q', progress='p',
                             affect='calm', panel='main', arm='canonical', repeat=0,
                             event=event, present=present))
    result = descriptive.joint_actions(pd.DataFrame(rows)).set_index('blind_id')
    assert result.joint_action.to_dict() == {'0': 'neither', '1': 'reveal_only', '2': 'elicit_only', '3': 'both'}


def test_prompt_dispersion_excludes_unmatched_canonical_sources():
    rows = []
    for q in range(32):
        arms = ['canonical', 'neutral_a', 'neutral_b', 'ask', 'explain'] if q < 16 else ['canonical']
        for m in range(5):
            for event in descriptive.PRIMARY:
                for progress in ['wrong_attempt', 'correct_partial']:
                    for affect in ['calm', 'frustrated']:
                        for arm in arms:
                            for repeat in [0, 1]:
                                rows.append(dict(source_family=f'q{q}', model=f'm{m}', event=event,
                                                 progress=progress, affect=affect, arm=arm, repeat=repeat,
                                                 panel='main', present=int(q >= 16)))
    profiles, dispersion, changes = descriptive.prompt_profiles(pd.DataFrame(rows))
    assert profiles.present.eq(0).all()
    assert dispersion.model_sd.eq(0).all()
    assert changes.change_from_canonical.eq(0).all()
    assert changes.source_family.nunique() == 16
