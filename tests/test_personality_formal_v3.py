"""Verify source separation, crossed interventions and blinded coding inputs."""
import json
from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import prepare_personality_formal_v3 as formal
from prepare_personality_judging_v2 import judge_messages
import run_personality_formal_stage_v3 as runner


def build():
    return formal.build({k:json.loads(p.read_text())['templates'] for k,p in formal.BANKS.items()})


def test_independent_sources_and_prescribed_crossing():
    stages,selected,sentinels=build()
    train=stages['training']
    main=[r for r in stages['confirmation'] if r['panel']=='main']
    assert len(train)==128
    assert len(main)==384
    assert len(selected)==16 and len(sentinels)==4
    assert len(stages['confirmation'])==404
    assert not ({r['source_family'] for r in train}&{r['source_family'] for r in main})
    for template in selected:
        assert len([r for r in main if r['template']==template])==20
    for t in {r['template'] for r in main}-set(selected):
        assert len([r for r in main if r['template']==t])==4


def test_coders_cannot_read_policy_assignment_or_teacher_system():
    stages,selected,_=build()
    cells=[r for r in stages['confirmation'] if r['template']==selected[0] and r['panel']=='main' and r['progress']=='wrong_attempt' and r['affect']=='calm']
    rubric=json.loads((formal.ROOT/'data/educational_personality_measurement_v2_2.json').read_text())
    messages=[judge_messages({**r,'response':'Try calculating the next step.'},rubric) for r in cells]
    assert len(messages)==5
    assert all(m==messages[0] for m in messages)
    payload=json.loads(messages[0][1]['content'])
    assert all(r['role']=='user' for r in payload['student_conversation'])
    assert len({r['messages'][0]['content'] for r in cells})==5
    assert len({r['teacher_reference'] for r in cells})==1


def test_sentinels_repeat_training_inputs_without_becoming_new_sources():
    stages,_,_=build()
    for sentinel in [r for r in stages['confirmation'] if r['panel']=='training_sentinel']:
        matches=[r for r in stages['training'] if r['template']==sentinel['template'] and r['progress']==sentinel['progress'] and r['affect']==sentinel['affect']]
        assert len(matches)==1
        assert matches[0]['messages']==sentinel['messages']
        assert matches[0]['source_family']==sentinel['source_family']


def test_confirmation_stage_rejects_absent_prediction_lock(tmp_path,monkeypatch):
    monkeypatch.setattr(runner,'BASE',tmp_path)
    (tmp_path/'design_freeze.json').write_text(json.dumps({'files':{}}))
    with pytest.raises(ValueError,match='before prediction lock'):
        runner.validate_stage('confirmation')
