"""Content supplement contracts and response-dependent selection, using synthetic labels only."""
import json
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import personality_content_sensitivity_v3 as content
from run_personality_requests_v2 import digest


def verdict(value='clear_error'):
    return {'verdict':value,'error_types':['wrong_final_answer'] if value=='clear_error' else [],
            'evidence_lines':[1] if value=='clear_error' else [],'explanation':'Short test rationale.'}


def test_evidence_and_uncertainty_contract():
    answer='The answer is five.\n\nPlease check it.'
    assert content.parse(json.dumps(verdict()),answer)['verdict']=='clear_error'
    assert content.parse(json.dumps(verdict('uncertain')),answer)['verdict']=='uncertain'
    for update in [{'evidence_lines':[2]},{'evidence_lines':[True]},{'evidence_lines':[]},
                   {'verdict':'no_clear_error'},{'verdict':'uncertain'},{'error_types':[]}]:
        value={**verdict(),**update}
        with pytest.raises(ValueError): content.parse(json.dumps(value),answer)
    with pytest.raises(ValueError,match='Duplicate'):
        content.parse('{"verdict":"clear_error","verdict":"no_clear_error"}',answer)


def test_blinding_and_completion_integrity():
    row={**content.anchors()[0],'model':'SECRET_GENERATOR','arm':'SECRET_ARM','repeat':100,
         'partition':'SECRET_PARTITION','expected_verdict':'SECRET_LABEL'}
    messages=content.messages(row)
    assert not any(secret in json.dumps(messages) for secret in ['SECRET_GENERATOR','SECRET_ARM','SECRET_PARTITION','SECRET_LABEL'])
    job={'model':'MiniMax-M3','messages':messages}
    payload={'model':job['model'],'messages':messages,'temperature':0,'max_tokens':16384,'stream':False}
    response=json.dumps(verdict('no_clear_error'))
    result={'model':job['model'],'returned_model':job['model'],'response':response,'error':None,
            'finish_reason':'stop','temperature':0,'max_tokens':16384,
            'prompt_sha256':digest(messages),'payload_sha256':digest(payload),'response_sha256':digest(response)}
    content.validate_result(job,result,row)
    for key,value in [('payload_sha256','bad'),('returned_model','different'),('finish_reason','length')]:
        with pytest.raises(ValueError): content.validate_result(job,{**result,key:value},row)


def full_grid():
    items,codes=[],[]
    for source in range(32):
        for model in range(5):
            for progress in ['wrong_attempt','correct_partial']:
                for affect in ['calm','frustrated']:
                    for repeat in range(2):
                        blind=f'{source}:{model}:{progress}:{affect}:{repeat}'
                        items.append(dict(blind_id=blind,behavior_blind_id='behavior:'+blind,source_family=f's{source}',
                            domain='mathematics' if source<8 else 'science',model=f'm{model}',progress=progress,affect=affect,repeat=repeat))
                        for judge in content.JUDGES:
                            value='no_clear_error'
                            if source==0 and model==0 and progress=='wrong_attempt' and affect=='calm' and repeat==0:
                                value='clear_error'
                            if source==1 and model==0 and progress=='wrong_attempt' and affect=='calm' and repeat==0:
                                value='uncertain' if judge==content.JUDGES[0] else 'no_clear_error'
                            codes.append(dict(blind_id=blind,judge=judge,anchor=False,verdict=value))
    return pd.DataFrame(codes),items


def test_full_grid_screening_keeps_model_pairs_and_uncertainty():
    codes,items=full_grid()
    flags=content.response_flags(codes,items)
    selected=content.retained_subsets(flags)
    assert len(selected['all_canonical'])==1280
    assert len(selected['mathematics'])==320
    assert len(selected['without_unanimous_error_slots'])==1275
    assert len(selected['without_any_error_slots'])==1275
    assert len(selected['without_error_or_uncertain_slots'])==1270
    # One error removes its matched five-model slot, not only the offending model.
    removed=flags[~flags.behavior_blind_id.isin(selected['without_unanimous_error_slots'])]
    assert removed.model.nunique()==5 and len(removed)==5
    assert flags.any_uncertain.sum()==1 and flags.any_clear_error.sum()==1
    with pytest.raises(ValueError): content.response_flags(codes.iloc[1:],items)
    with pytest.raises(ValueError): content.retained_subsets(flags.iloc[1:])


def test_source_equal_losses_and_empty_screened_target():
    rows=[]
    baselines=['context','default_profile','domain_profile','conditional_profile','training_style_profile']
    for source,n in [('large',10),('small',5)]:
        for item in range(n):
            for event in content.PRIMARY:
                for baseline in baselines:
                    value=.2 if source=='large' else .8
                    if baseline!='context': value-=.1
                    rows.append(dict(blind_id=f'{source}:{item}',source_group=source,event=event,baseline=baseline,brier=value))
    scored=pd.DataFrame(rows)
    losses,comparisons=content.subset_summary(scored,{'all':set(scored.blind_id),'empty':set()})
    assert losses[losses.baseline.eq('context')].brier.eq(.5).all()
    gains=comparisons[comparisons.subset.eq('all')&comparisons.comparison.eq('default_vs_context')]
    assert abs(gains.mean_difference.mean()-.1)<1e-12
    assert comparisons[comparisons.subset.eq('empty')].status.eq('insufficient retained sources').all()
    assert not any(name.startswith('p_') for name in comparisons.columns)


def test_full_pipeline_prepare_repair_and_secondary_analysis(tmp_path,monkeypatch):
    """All canonical positions, synthetic text/codes, no API or real forecast lock."""
    base=tmp_path/'formal'; out=base/'content_sensitivity'
    monkeypatch.setattr(content,'ROOT',tmp_path);monkeypatch.setattr(content,'BASE',base)
    monkeypatch.setattr(content,'OUT',out);monkeypatch.setattr(content,'policy',lambda:{})
    monkeypatch.setattr(content,'validate_stage',lambda stage:None)
    def verify(files):
        for name,expected in files.items(): assert content.sha(tmp_path/name)==expected
    monkeypatch.setattr(content,'verify_files',verify)
    def write_json(path,value):
        path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value)+'\n')
    def write_rows(path,rows):
        path.parent.mkdir(parents=True,exist_ok=True);path.write_text(''.join(json.dumps(r)+'\n' for r in rows))
    write_json(base/'content_sensitivity_policy.json',{'test':'synthetic only'})
    write_json(base/'confirmation/run/pipeline_state.json',
               {'status':'complete','stage':'confirmation_primary_and_robustness_calculations_complete'})
    _,grid=full_grid(); originals=[]; generated=[]; scores=[]
    for item in grid:
        answer='The answer is 4.'
        row={**item,'sample_id':item['blind_id'],'blind_id':item['behavior_blind_id'],
             'response':answer,'panel':'main','arm':'canonical','messages':[{'role':'user','content':'What is 2 + 2?'}],
             'target_resolution':'4'}
        originals.append(row)
        generated.append({'request_id':row['sample_id'],'response':answer,'response_sha256':digest(answer)})
        for event in content.PRIMARY:
            for baseline in ['context','default_profile','domain_profile','conditional_profile','training_style_profile']:
                probability=.5 if baseline in ['context','training_style_profile'] else .4
                scores.append({'blind_id':row['blind_id'],'source_group':row['source_family'],'event':event,
                               'baseline':baseline,'probability':probability,'present':0,'brier':probability**2})
    write_rows(base/'confirmation/judge/v2_2/unblinding.jsonl',originals)
    write_rows(base/'confirmation/run/responses.jsonl',generated)
    analysis=base/'confirmation_analysis';analysis.mkdir()
    scored=pd.DataFrame(scores);scored.to_csv(analysis/'scored_locked_predictions.csv',index=False)
    scored.groupby(['event','baseline']).brier.mean().to_csv(analysis/'prediction_brier.csv')
    write_json(analysis/'summary.json',{'inputs':{}})
    content.prepare()
    jobs=content.read_rows(out/'manifest.jsonl');items={r['blind_id']:r for r in content.read_rows(out/'unblinding.jsonl')}
    assert len(jobs)==2584 and len(items)==1292
    completed=[]
    for job in jobs:
        item=items[job['blind_id']]
        value=verdict(item['expected_verdict'] if item['anchor'] else 'no_clear_error')
        response=json.dumps(value)
        payload={'model':job['model'],'messages':job['messages'],'temperature':0,'max_tokens':16384,'stream':False}
        completed.append({'request_id':job['request_id'],'model':job['model'],'returned_model':job['model'],
            'response':response,'error':None,'finish_reason':'stop','temperature':0,'max_tokens':16384,
            'prompt_sha256':digest(job['messages']),'payload_sha256':digest(payload),'response_sha256':digest(response)})
    run=out/'run';write_rows(run/'responses.jsonl',[{**completed[0],'response':'','error':'synthetic transport failure'},*completed[1:]])
    diagnostics=out/'diagnostics/pass0';content.audit(run,diagnostics)
    assert json.loads((diagnostics/'summary.json').read_text())['invalid_or_missing']==1
    with pytest.raises(ValueError,match='Complete content coding'): content.analyze(diagnostics)
    repaired=out/'run_repair1';content.seed(run,repaired)
    assert len(content.read_rows(repaired/'responses.jsonl'))==2583
    with (repaired/'responses.jsonl').open('a') as handle: handle.write(json.dumps(completed[0])+'\n')
    final=out/'diagnostics/pass1';content.audit(repaired,final);content.analyze(final)
    summary=json.loads((out/'analysis/summary.json').read_text())
    assert summary['diagnostic_anchor_rule_met']
    assert summary['new_hypothesis_tests']==0
    assert summary['selected_responses']['mathematics']==320
    assert summary['selected_responses']['without_any_error_slots']==1280
