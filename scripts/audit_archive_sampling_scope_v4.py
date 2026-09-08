"""Audit selection scope using frozen inputs only, without reading coding results."""
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

import numpy as np

from prepare_archive_behavior_validation_v4 import candidates, select
from reconstruct_archive_tutor_inputs_v4 import normalized

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'artifacts/educational_personality_v4'
REPO=ROOT.parent/'edubenchmark'
OUT=BASE/'archive_sampling_scope'


def rows(path):
    return [json.loads(line) for line in path.open() if line.strip()]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def population(name, items):
    return {'population':name,'items':len(items),'source_groups':len({r['source_group'] for r in items}),
            'problem_char_quantiles':np.quantile([len(r['problem']) for r in items],[0,.25,.5,.75,1]).tolist(),
            'conversation_char_quantiles':np.quantile([len(r['conversation']) for r in items],[0,.25,.5,.75,1]).tolist(),
            'reference_status':dict(Counter(r['reference_status'] for r in items))}


def main():
    material_file=BASE/'archive_bridge/local/materials.jsonl'
    record_file=BASE/'archive_bridge/response_index.jsonl'
    index_file=BASE/'archive_validation/selected_response_index.jsonl'
    lock_file=BASE/'archive_validation/design_freeze.json'
    raw_file=REPO/'sources/datasets/mathtutorbench/datasets/mathdial_bridge.json'
    paper_file=REPO/'sources/text/mathtutorbench.txt'
    materials=rows(material_file);records=rows(record_file);index=rows(index_file)
    lock=json.loads(lock_file.read_text())
    for file in [material_file,record_file,index_file]:
        assert sha(file)==lock['files'][str(file.relative_to(ROOT))]
    eligible,excluded,_=candidates(materials,records);chosen=select(eligible)
    chosen_ids={r['material_id'] for pair in chosen for r in pair}
    assert chosen_ids=={r['material_id'] for r in index}
    selected=[pair[0] for pair in chosen]
    pool=[r for r in materials if r['benchmark']=='mathtutorbench_scaffolding']
    groups=Counter(pair[0]['source_group'] for pair in eligible)
    raw=json.loads(raw_file.read_text())
    assert len(raw)==len(pool) and all(r['dialog_history'] for r in raw)
    turn_counts=Counter()
    for row in selected:
        i=int(row['item_id'].split('-')[-1]);original=raw[i]
        assert normalized(original['problem'])==normalized(row['problem'])
        turns=original['dialog_history']
        used=turns[:-1] if len(turns)>1 else turns
        text='\n'.join(f"{'Student' if t.get('user')=='Student' else 'Teacher'}: {t['text']}" for t in used)
        assert text==row['conversation']
        turn_counts[len(used)]+=1
    known_questions=set()
    mathdial_files=[REPO/'sources/datasets/mathdial'/name for name in ['train.jsonl','test.jsonl']]
    for file in mathdial_files:
        for row in rows(file):known_questions.add(normalized(row['question']))
    # Question overlap is deliberately not promoted to exact dialogue provenance.
    matches=sum(normalized(r['problem']) in known_questions for r in selected)
    components=defaultdict(set)
    for row in selected:
        components[sha_text(normalized(row['problem']))].add(row['source_group'])
    report={'status':'input-only sampling scope audit complete','new_api_calls':0,'coding_results_read':False,
            'human_quality_labels_used':False,
            'selection_reproduced_exactly':True,'selected_teacher_responses':len(index),
            'populations':[population('all_scaffolding',pool),population('eligible_dialogues',[p[0] for p in eligible]),population('selected_sources',selected)],
            'exclusions':dict(Counter(r['reason'] for r in excluded)),
            'eligible_group_multiplicity':dict(sorted(Counter(groups.values()).items())),
            'selected_context_turn_counts':dict(sorted(turn_counts.items())),
            'distinct_selected_normalized_problems':len(components),
            'selected_problem_strings_shared_between_groups':sum(len(g)>1 for g in components.values()),
            'selected_mathdial_exact_question_matches':matches,
            'selected_verified_original_dataset_ids':sum(r['source_dataset']!='not_individually_verified' for r in selected),
            'interpretation':['A hash-selected subset of recoverable paired short mathematical benchmark contexts, not a sample of the million-record archive.',
                              'The source paper describes both real-dialogue snippets and teacher/simulated-student dialogue origins.',
                              'Question overlap with MathDial does not establish exact selected-dialogue lineage or real learner origin.',
                              'Input contexts and references may be human-authored; neither human quality labels nor held-out tutor golds are used as behavioral measurements.'],
            'inputs':{str(p):sha(p) for p in [material_file,record_file,index_file,lock_file,raw_file,paper_file,*mathdial_files,Path(__file__)]}}
    OUT.mkdir(exist_ok=True)
    (OUT/'summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ['inputs','interpretation']},ensure_ascii=False,indent=2))


def sha_text(text):return hashlib.sha256(text.encode()).hexdigest()


if __name__=='__main__':main()
