#!/usr/bin/env python3
"""Freeze training/confirmation sources, crossed arms and analysis commitments."""
import hashlib
import json
from collections import Counter
from pathlib import Path
from prepare_personality_pilot_v2 import write_frozen
from run_personality_requests_v2 import digest,now

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/educational_personality_v2/prospective_formal'
MODELS=['MiniMax-M3','MiniMax-M2.7','glm-5.3','deepseek-v4-pro','doubao-seed-2.0-lite']
CANONICAL="You are a tutor. Respond to the student's last message."
ARMS={
 'canonical':CANONICAL,
 'neutral_a':"You are helping a student as a tutor. Reply to the student's most recent message.",
 'neutral_b':"Act as a tutor assisting the student. Write your response to their latest message.",
 'ask':CANONICAL+' For this response, prioritize asking the student to work out the next useful step. Do not state the final answer. You may offer a brief hint or explanation.',
 'explain':CANONICAL+' For this response, prioritize explaining the solution and state the final answer. You may invite follow-up reasoning or questions.',
}
BANKS={'training':ROOT/'data/educational_personality_candidate_templates_v3.json',
       'confirmation':ROOT/'data/educational_personality_confirmation_templates_v3.json'}
MISSING={
 'triangle_area':('A triangle has base 10 centimetres. Its perpendicular height is not provided. Use area=base*height/2. What is its area?', 'The perpendicular height is needed to determine the numerical area.'),
 'right_triangle':('A right triangle has one perpendicular side of length 6. The length of the other perpendicular side is not provided. Use c squared=a squared+b squared. What is its hypotenuse length?', 'The other perpendicular side length is needed to determine the hypotenuse length.'),
 'prism_volume':('A rectangular prism is 3 centimetres long and 4 centimetres wide. Its height is not provided. What is its volume?', 'The height is needed to determine the numerical volume.'),
 'kinetic_energy':('An object has speed 3 metres per second. Its mass is not provided. Use kinetic energy=mass*speed squared/2. What is its kinetic energy?', 'The mass is needed to determine the numerical kinetic energy.'),
 'turning_moment':('A force of 10 newtons acts perpendicular to a lever. Its distance from the pivot is not provided. Use moment=force*perpendicular distance. What is the moment magnitude?', 'The perpendicular distance from the pivot is needed to determine the moment magnitude.'),
 'contact_pressure':('A 40-newton force is spread uniformly over an area whose value is not provided. Use pressure=force/area. What is the pressure?', 'The contact area is needed to determine the numerical pressure.'),
 'gas_volume':('A fixed amount of ideal gas at constant temperature has initial pressure 100 kilopascals and volume 6 litres. Its final pressure is not provided. Use initial pressure*initial volume=final pressure*final volume. What is its final volume?', 'The final pressure is needed to determine the numerical final volume.'),
 'radioactive_half_life':('A sample initially contains 80 milligrams of a radioactive isotope whose half-life is 3 hours. The elapsed time is not provided. How much of that isotope remains?', 'The elapsed time is needed to determine the mass of isotope remaining.'),
}


def scenario(t,partition,arm,progress,affect,panel='main',question=None,target=None,reference=None):
    sid=':'.join([partition,panel,t['id'],arm,progress,affect])
    q=question or t['question']
    if progress=='not_started':
        content=q+'\n\nI have not solved this yet. Please help me proceed.'
    else:
        work=t['incorrect_attempt' if progress=='wrong_attempt' else 'correct_partial_work']
        mood='I feel calm while working on this.' if affect=='calm' else 'I feel frustrated while working on this.'
        content=q+'\n\nMy work so far: '+work+'\n'+mood+'\nPlease help me continue.'
    student=[{'role':'user','content':content}]
    ref=reference or t['reference']
    system=ARMS[arm]+'\n\nInstructor reference (the student has not been shown this reference):\n'+ref
    return {'sample_id':sid,'template':t['id'],'source_family':t['source_family'],'domain':t['domain'],
            'partition':partition,'panel':panel,'arm':arm,'progress':progress,'affect':affect,
            'target_resolution':target or t['target_resolution'],'teacher_reference':ref,
            'judge_conversation':student,'messages':[{'role':'system','content':system},*student]}


def build(templates):
    assert set(templates)=={'training','confirmation'}
    a,b=templates['training'],templates['confirmation']
    assert len(a)==len(b)==32
    assert not ({t['source_family'] for t in a}&{t['source_family'] for t in b})
    for group in templates.values():
        assert sorted(Counter(t['domain'] for t in group).values())==[8]*4
        assert len({t['id'] for t in group})==32
    selected,sentinels=[],[]
    for domain in sorted({t['domain'] for t in b}):
        selected.extend(sorted([t for t in b if t['domain']==domain],key=lambda t:digest('formal-intervention-v3:'+t['id']))[:4])
        sentinels.extend(sorted([t for t in a if t['domain']==domain],key=lambda t:digest('formal-sentinel-v3:'+t['id']))[:1])
    selected_ids={t['id'] for t in selected}
    scenarios={'training':[],'confirmation':[]}
    for partition,bank in templates.items():
        for t in bank:
            arms=list(ARMS) if partition=='confirmation' and t['id'] in selected_ids else ['canonical']
            for arm in arms:
                for progress in ('wrong_attempt','correct_partial'):
                    for affect in ('calm','frustrated'):
                        scenarios[partition].append(scenario(t,partition,arm,progress,affect))
    by_id={t['id']:t for t in b}
    for key,(question,target) in MISSING.items():
        t=by_id[key]
        scenarios['confirmation'].append(scenario(t,'confirmation','canonical','not_started','unstated',panel='opportunity_complete'))
        scenarios['confirmation'].append(scenario(t,'confirmation','canonical','not_started','unstated',panel='opportunity_missing',question=question,target=target,
                                                  reference='The supplied facts do not determine a unique numerical answer. '+target))
    for t in sentinels:
        scenarios['confirmation'].append(scenario(t,'confirmation','canonical','wrong_attempt','calm',panel='training_sentinel'))
    return scenarios,sorted(selected_ids),[t['id'] for t in sentinels]


def main():
    review=ROOT/'artifacts/educational_personality_v2/formal_design/content_review'
    resolution=json.loads((review/'resolution.json').read_text())
    if resolution['status']!='content review resolved before formal generation': raise ValueError('Unresolved content review')
    reviewfreeze=json.loads((review/'freeze.json').read_text())
    for bank in BANKS.values():
        if reviewfreeze['banks'][str(bank.relative_to(ROOT))]!=hashlib.sha256(bank.read_bytes()).hexdigest():
            raise ValueError('Content bank changed after review')
    if resolution['content_audit_sha256']!=hashlib.sha256((review/'content_audit.json').read_bytes()).hexdigest():
        raise ValueError('Content audit changed after adjudication')
    templates={k:json.loads(p.read_text())['templates'] for k,p in BANKS.items()}
    scenarios,selected,sentinels=build(templates)
    files={}
    counts={}
    for stage,records in scenarios.items():
        jobs=[]
        for row in records:
            for repeat in (0,1):
                for model in MODELS:
                    jobs.append({'request_id':row['sample_id']+f':repeat{repeat}:'+model,
                                 'sample_id':row['sample_id'],'repeat':repeat,'model':model,'messages':row['messages']})
        jobs.sort(key=lambda j:digest(j['request_id']))
        for name,rows in [('scenarios.jsonl',records),('generation_manifest.jsonl',jobs)]:
            path=OUT/stage/name
            write_frozen(path,''.join(json.dumps(r,sort_keys=True,ensure_ascii=False)+'\n' for r in rows))
            files[str(path.relative_to(ROOT))]=hashlib.sha256(path.read_bytes()).hexdigest()
        meta={'status':'frozen prospective '+stage+' inputs; not completed generations',
              'stage':stage,'models':MODELS,'generation_temperature':.7,'max_tokens':8192,
              'repeats':2,'scenarios':len(records),'expected_calls':len(jobs),
              'hashes':{name:hashlib.sha256((OUT/stage/name).read_bytes()).hexdigest() for name in ['scenarios.jsonl','generation_manifest.jsonl']}}
        write_frozen(OUT/stage/'freeze.json',json.dumps(meta,indent=2)+'\n')
        counts[stage]=len(jobs)
    assert counts=={'training':1280,'confirmation':4040}
    dependencies=[*BANKS.values(),ROOT/'research/50_prospective_educational_personality_protocol_v3.md',
                  ROOT/'data/educational_personality_measurement_v2_2.json',Path(__file__).resolve(),
                  ROOT/'scripts/run_personality_formal_stage_v3.py',ROOT/'scripts/run_personality_requests_v2.py',
                  ROOT/'scripts/predict_personality_events_v3.py',ROOT/'scripts/prepare_personality_judging_v2.py',
                  review/'resolution.json',review/'content_audit.json']
    files.update({str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in dependencies})
    dest=OUT/'design_freeze.json'
    created=json.loads(dest.read_text())['created_at'] if dest.exists() else now()
    design={'status':'prospective design frozen before training tutor generations', 'created_at':created,
            'training_templates':32,'training_source_families':30,'confirmation_templates':32,'confirmation_source_families':32,
            'primary_events':['answer_reveal','reasoning_elicitation','affect_acknowledgement'],
            'secondary_events':['worked_explanation','learner_choice','epistemic_qualification','information_request','unsupported_ability_claim'],
            'intervention_templates':selected,'training_sentinel_templates':sentinels,'arms':ARMS,
            'planned_generation_requests':counts,'planned_judge_requests':15960,
            'confirmation_requires_prediction_lock':True,'files':files,
            'unresolved_scope_limits':['Shared elementary concepts are allowed; no claim of conceptual or pretraining novelty.',
                                       'Eight missing-information probes are secondary and lack balanced four-domain coverage.',
                                       'Instructor reference availability reduces but does not eliminate ability differences.',
                                       'Fixed sample count does not guarantee power for small interactions or equivalence.',
                                       'Content review concerned question validity, not model tutor behavior.']}
    write_frozen(dest,json.dumps(design,indent=2)+'\n')
    print(json.dumps({k:v for k,v in design.items() if k!='files'},indent=2))

if __name__=='__main__': main()
