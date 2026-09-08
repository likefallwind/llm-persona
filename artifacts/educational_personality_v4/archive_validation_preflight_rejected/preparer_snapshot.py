#!/usr/bin/env python3
"""Select source-disjoint natural dialogues and freeze blinded event coding."""
from collections import defaultdict, Counter
import hashlib
import json
from pathlib import Path

from prepare_personality_judging_v2 import judge_messages
from prepare_personality_pilot_v2 import write_frozen
from run_personality_requests_v2 import digest, now, read_rows
from prepare_personality_cue_transfer_v4 import ROOT, RUBRIC, sha

BASE = ROOT / 'artifacts/educational_personality_v4/archive_validation'
BRIDGE = ROOT / 'artifacts/educational_personality_v4/archive_bridge'
REPO = ROOT.parent / 'edubenchmark'
MODELS = ['minimax-m3', 'minimax-m2.7', 'glm-5.2', 'deepseek-v4-pro',
          'doubao-seed-2.0-pro', 'qwen3.5-4b', 'qwen3.8-27b']
JUDGES = ['MiniMax-M3', 'deepseek-v4-pro', 'glm-5.3']


def candidates(materials, records):
    lookup = {r['material_id']: r for r in materials}
    by_cell = defaultdict(list)
    for row in records:
        if row['input_variant'] == 'standard' and row['model'] in MODELS:
            by_cell[(row['material_id'], row['model'])].append(row)
    eligible, exclusions = [], []
    for row in materials:
        if row['benchmark'] != 'mathtutorbench_scaffolding':
            continue
        partner = lookup.get('mathtutorbench_pedagogy:pedagogy-' + row['item_id'].split('-')[-1])
        reason = None
        if not row['problem'].strip() or row['reference_status'] != 'provided_unvalidated':
            reason = 'problem_or_reference_missing'
        elif partner is None or any(row[k] != partner[k] for k in ['problem', 'conversation', 'reference_solution', 'source_group']):
            reason = 'paired_context_mismatch'
        elif any(len(by_cell[(item['material_id'], model)]) != 1 for item in [row, partner] for model in MODELS):
            reason = 'incomplete_or_ambiguous_seven_model_cell'
        if reason:
            exclusions.append({'material_id': row['material_id'], 'reason': reason})
        else:
            eligible.append((row, partner))
    return eligible, exclusions, by_cell


def select(eligible, n=256):
    groups = defaultdict(list)
    for pair in eligible:
        groups[pair[0]['source_group']].append(pair)
    if len(groups) < n:
        raise ValueError('Insufficient complete source groups')
    chosen = sorted(groups, key=lambda g: digest('archive-natural-v4:' + g))[:n]
    return [min(groups[g], key=lambda pair: digest('archive-dialogue-v4:' + pair[0]['material_id'])) for g in chosen]


def main():
    if (BASE / 'design_freeze.json').exists() or (BASE / 'judge/run').exists():
        raise ValueError('Archive validation already frozen or started')
    materials = read_rows(BRIDGE / 'local/materials.jsonl')
    records = read_rows(BRIDGE / 'response_index.jsonl')
    eligible, excluded, cells = candidates(materials, records)
    chosen = select(eligible)
    for p, expected in json.loads((BRIDGE / 'summary.json').read_text())['source_files'].items():
        if sha(REPO / p) != expected:
            raise ValueError('Source dataset changed after input reconstruction')
    census = json.loads((ROOT / 'artifacts/research_reassessment_20260905/archive_census.json').read_text())
    hashes = {r['path']: r['sha256'] for r in census['runs']}
    needed = defaultdict(list)
    for pair in chosen:
        for material in pair:
            for model in MODELS:
                rec = cells[(material['material_id'], model)][0]
                pointer = sorted(rec['record_pointers'], key=lambda x: (x['path'], x['line']))[0]
                needed[pointer['path']].append((pointer['line'], material, rec))
    rubric = json.loads(RUBRIC.read_text())
    jobs, mapping, selected_index = [], [], []
    for relative, wanted in sorted(needed.items()):
        source = REPO / 'reports/eval' / relative
        if sha(source) != hashes[relative]:
            raise ValueError('Archived response file differs from frozen census')
        wanted_lines = {entry[0] for entry in wanted}
        raw = {}
        for number, line in enumerate(source.open(), 1):
            if number in wanted_lines:
                raw[number] = json.loads(line)
        for number, material, record in wanted:
            row = raw[number]
            text = row.get('response')
            from audit_archive_coverage import canonical
            if (row.get('error') or not isinstance(text, str) or not text.strip() or
                hashlib.sha256(text.encode()).hexdigest() != record['response_sha256'] or
                str(row['item_id']) != material['item_id'] or canonical(row['model']) != record['model']):
                raise ValueError('Archive line pointer or response identity failed')
            sid = digest(['archive-behavior-v4', record['material_id'], record['model'], record['response_sha256']])
            blind = hashlib.sha256(('personality-coding-v2:' + sid).encode()).hexdigest()[:20]
            conversation = [{'role': 'user', 'content': material['conversation']}]
            item = {'sample_id': sid, 'blind_id': blind, 'model': record['model'],
                    'template': material['source_group'], 'source_family': material['source_group'],
                    'domain': 'mathematics', 'progress': 'archive_observed', 'affect': 'unstated', 'repeat': 0,
                    'partition': 'archive_validation_v4', 'panel': 'natural_dialogue',
                    'arm': material['benchmark'].removeprefix('mathtutorbench_'),
                    'judge_conversation': conversation, 'messages': conversation,
                    'target_resolution': 'Target problem:\n' + material['problem'] + '\nReference solution:\n' + material['reference_solution'],
                    'response': text}
            mapping.append(item)
            for judge in JUDGES:
                jobs.append({'request_id': blind + ':' + judge, 'blind_id': blind,
                             'model': judge, 'messages': judge_messages(item, rubric)})
            selected_index.append({'blind_id': blind, 'model': record['model'], 'source_family': material['source_group'],
                'arm': item['arm'], 'material_id': record['material_id'], 'response_sha256': record['response_sha256'],
                'prediction_path': relative, 'prediction_line': number,
                'current_reconstructed_messages_sha256': record['reconstructed_messages_sha256'],
                'input_provenance': record['input_evidence']})
    if len(mapping) != 3584 or len({r['blind_id'] for r in mapping}) != 3584:
        raise ValueError('Archive response panel coverage mismatch')
    jobs.sort(key=lambda j: digest(j['request_id']))
    judge_dir = BASE / 'judge'
    for path, rows in [(judge_dir / 'manifest.jsonl', jobs), (judge_dir / 'unblinding.jsonl', mapping),
                       (BASE / 'selected_response_index.jsonl', selected_index),
                       (BASE / 'excluded_materials.jsonl', excluded)]:
        write_frozen(path, ''.join(json.dumps(r, ensure_ascii=False, sort_keys=True) + '\n' for r in rows))
    freeze = {'mode': 'generation', 'items': 3584, 'expected_calls': 10752, 'judges': JUDGES,
              'rubric_sha256': sha(RUBRIC), 'manifest_sha256': sha(judge_dir / 'manifest.jsonl'),
              'temperature': 0.0, 'max_tokens': 32768, 'evidence_format': 'line_ids',
              'label_provenance': 'New blinded agent event codes on existing archived visible replies; no human annotation added.'}
    write_frozen(judge_dir / 'freeze.json', json.dumps(freeze, indent=2) + '\n')
    dependencies = [Path(__file__), RUBRIC, BRIDGE / 'summary.json', BRIDGE / 'local/materials.jsonl',
                    BRIDGE / 'response_index.jsonl', ROOT / 'research/75_archive_behavior_validation_protocol_v4.md',
                    *judge_dir.iterdir(), BASE / 'selected_response_index.jsonl', BASE / 'excluded_materials.jsonl']
    dependencies += [ROOT / 'scripts' / name for name in ['analyze_archive_behavior_validation_v4.py',
        'complete_archive_behavior_validation_v4.py', 'run_personality_requests_v2.py',
        'prepare_personality_judging_v2.py', 'analyze_personality_coding_v2.py',
        'seed_personality_judge_run_v2.py', 'recover_personality_cue_json_v4.py',
        'complete_personality_training_budget_recovery_v3.py']]
    lock = {'status': 'archive input selection and analysis frozen before new coding', 'locked_at': now(),
            'sources': 256, 'candidate_sources': len({p[0]['source_group'] for p in eligible}),
            'candidate_dialogues': len(eligible), 'answers': len(mapping), 'new_teacher_generation': 0,
            'planned_coding': len(jobs), 'models': MODELS, 'judges': JUDGES,
            'provider_caps': {'minimax': 4, 'gateway': 8},
            'source_kind': 'upstream benchmark dialogues/references and archived model replies, not synthetic-only v4 cue prompts',
            'selected_prediction_files': {p: hashes[p] for p in needed},
            'files': {str(p.relative_to(ROOT)): sha(p) for p in dependencies}}
    write_frozen(BASE / 'design_freeze.json', json.dumps(lock, indent=2) + '\n')
    print(json.dumps({k: v for k, v in lock.items() if k not in ['files', 'selected_prediction_files']}, indent=2))


if __name__ == '__main__':
    main()
