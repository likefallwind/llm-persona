#!/usr/bin/env python3
"""Freeze a post-v3 cue-transfer study using unchanged v3 probabilities."""
import hashlib
import json
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

from prepare_personality_formal_v3 import MODELS, scenario
from prepare_personality_pilot_v2 import write_frozen
from run_personality_formal_stage_v3 import verify_files
from run_personality_requests_v2 import digest, now, read_rows

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT / 'artifacts/educational_personality_v2/prospective_formal'
OUT = ROOT / 'artifacts/educational_personality_v4/cue_transfer'
BANK = ROOT / 'data/educational_personality_confirmation_templates_v3.json'
CUES = ROOT / 'data/educational_personality_cue_transfer_v4.json'
RUBRIC = ROOT / 'data/educational_personality_measurement_v2_2.json'
EVENTS = ['answer_reveal', 'reasoning_elicitation', 'affect_acknowledgement']
REGISTERS = ['canonical', 'explicit', 'implicit', 'peer_control']
FEATURES = ['domain', 'progress', 'affect', 'model', 'event', 'baseline']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(templates, cues):
    rows = []
    for domain in sorted({t['domain'] for t in templates}):
        bank = sorted([t for t in templates if t['domain'] == domain],
                      key=lambda t: digest('cue-transfer-v4:' + t['id']))
        for index, t in enumerate(bank):
            for register in REGISTERS:
                family = index % 4 if register == 'explicit' else (index + 1) % 4
                for progress in ['wrong_attempt', 'correct_partial']:
                    for pole in ['calm', 'frustrated']:
                        affect = 'calm' if register == 'peer_control' else pole
                        base = scenario(t, 'confirmation', 'canonical', progress, affect)
                        original = cues['canonical'][affect]
                        cue = (cues[register][family][pole] if register in ['explicit', 'implicit']
                               else cues[register][pole])
                        if register in ['explicit', 'implicit'] and any(
                                word in cue.lower() for word in ['calm', 'frustrat']):
                            raise ValueError('New cue contains original affect vocabulary')
                        text = base['messages'][1]['content']
                        if text.count(original) != 1:
                            raise ValueError('Canonical cue replacement is ambiguous')
                        student = [{'role': 'user', 'content': text.replace(original, cue)}]
                        sid = ':'.join(['cue_transfer_v4', t['id'], register, progress, pole])
                        rows.append({**base, 'sample_id': sid, 'partition': 'cue_transfer_v4',
                                     'panel': 'main', 'arm': register, 'cue_pole': pole,
                                     'cue_family': str(family) if register in ['explicit', 'implicit'] else 'fixed',
                                     'judge_conversation': student,
                                     'messages': [base['messages'][0], *student]})
    jobs = []
    for row in rows:
        for repeat in [0, 1]:
            for model in MODELS:
                jobs.append({'request_id': row['sample_id'] + f':repeat{repeat}:' + model,
                             'sample_id': row['sample_id'], 'model': model,
                             'repeat': repeat, 'messages': row['messages']})
    jobs.sort(key=lambda j: digest(j['request_id']))
    return rows, jobs


def transport_predictions(old, scenarios, jobs):
    """Map identical feature tuples; never fit or inspect any new label."""
    old = old[old.event.isin(EVENTS)].copy()
    grouped = old.groupby(FEATURES, dropna=False).probability
    if ((grouped.max() - grouped.min()) > 1e-12).any():
        raise ValueError('Old probabilities differ within a feature tuple')
    table = grouped.first().reset_index()
    samples = {row['sample_id']: row for row in scenarios}
    inputs = []
    for job in jobs:
        row = samples[job['sample_id']]
        inputs.append({**{k: row[k] for k in ['template', 'domain', 'source_family', 'progress',
                                            'affect', 'cue_pole', 'cue_family', 'arm']},
                       'model': job['model'], 'repeat': job['repeat'], 'request_id': job['request_id'],
                       'blind_id': hashlib.sha256(('personality-coding-v2:' + job['request_id']).encode()).hexdigest()[:20]})
    frame = pd.DataFrame(inputs)
    prediction = frame.merge(table, on=FEATURES[:4], validate='many_to_many')
    if len(prediction) != len(jobs) * 12 or prediction.request_id.nunique() != len(jobs):
        raise ValueError('Missing or extra frozen prediction cells')
    if prediction.duplicated(['request_id', 'event', 'baseline']).any():
        raise ValueError('Duplicated frozen predictions')
    if not np.isfinite(prediction.probability).all() or not prediction.probability.between(0, 1).all():
        raise ValueError('Invalid probability')
    return frame, prediction


def main():
    if (OUT / 'design_freeze.json').exists() or (OUT / 'run/responses.jsonl').exists():
        raise ValueError('Study already frozen or started; do not regenerate')
    for name in ['design_freeze.json', 'prediction_lock.json']:
        verify_files(json.loads((OLD / name).read_text())['files'])
    templates = json.loads(BANK.read_text())['templates']
    cues = json.loads(CUES.read_text())
    scenarios, jobs = build(templates, cues)
    assert len(scenarios) == 512 and len(jobs) == 5120
    assert len({r['source_family'] for r in scenarios}) == 32
    assert Counter(r['arm'] for r in scenarios) == {k: 128 for k in REGISTERS}
    previous = {digest(r['messages']) for r in read_rows(OLD / 'confirmation/scenarios.jsonl')
                if r['panel'] == 'main' and r['arm'] == 'canonical'}
    assert {digest(r['messages']) for r in scenarios if r['arm'] == 'canonical'} == previous
    old = pd.read_csv(OLD / 'locked_predictions/predictions.csv')
    frame, predictions = transport_predictions(old, scenarios, jobs)
    for filename, rows in [('scenarios.jsonl', scenarios), ('generation_manifest.jsonl', jobs)]:
        write_frozen(OUT / filename, ''.join(json.dumps(r, ensure_ascii=False, sort_keys=True) + '\n' for r in rows))
    write_frozen(OUT / 'input_frame.csv', frame.to_csv(index=False))
    write_frozen(OUT / 'predictions.csv', predictions.to_csv(index=False))
    freeze = {'stage': 'cue_transfer_v4', 'generation_temperature': 0.7, 'max_tokens': 8192,
              'hashes': {name: sha(OUT / name) for name in ['scenarios.jsonl', 'generation_manifest.jsonl']},
              'expected_calls': len(jobs), 'models': MODELS}
    write_frozen(OUT / 'freeze.json', json.dumps(freeze, indent=2) + '\n')
    dependencies = [BANK, CUES, RUBRIC, ROOT / 'research/71_cue_transfer_protocol_v4.md',
                    OLD / 'design_freeze.json', OLD / 'prediction_lock.json',
                    OLD / 'locked_predictions/predictions.csv', *OUT.iterdir()]
    dependencies += [ROOT / 'scripts' / name for name in [
        'prepare_personality_cue_transfer_v4.py', 'analyze_personality_cue_transfer_v4.py',
        'complete_personality_cue_transfer_v4.py', 'prepare_personality_formal_v3.py',
        'run_personality_requests_v2.py', 'run_personality_formal_stage_v3.py',
        'prepare_personality_pilot_v2.py', 'prepare_personality_judging_v2.py',
        'analyze_personality_coding_v2.py', 'audit_personality_generation_v2.py',
        'audit_personality_judge_lineage_v3.py', 'seed_personality_judge_run_v2.py']]
    lock = {'status': 'post-v3 extension frozen before new generations', 'locked_at': now(),
            'sources': 32, 'new_source_problems': 0, 'generation_requests': 5120, 'judge_requests': 15360,
            'prediction_rows': len(predictions), 'prediction_fitting_calls': 0,
            'provider_caps': {'minimax': 4, 'gateway': 8},
            'files': {str(p.relative_to(ROOT)): sha(p) for p in dependencies}}
    write_frozen(OUT / 'design_freeze.json', json.dumps(lock, indent=2) + '\n')
    print(json.dumps({k: v for k, v in lock.items() if k != 'files'}, indent=2))


if __name__ == '__main__':
    main()
