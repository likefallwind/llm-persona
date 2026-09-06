#!/usr/bin/env python3
"""Audit source overlap for educational-personality research, without APIs.

Normalized exact text matches identify some dependence. Non-matches do not prove
independence. Outputs contain hashes and counts, never source conversation text.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
from itertools import combinations
import json
from pathlib import Path
import re
import unicodedata


def digest(value: str) -> str:
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def normalized(value: str) -> str:
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFKC', value)).strip().casefold()


def audit(root: Path, semantic: Path, output: Path):
    paths = {
        'mathdial_standard': root / 'mathtutorbench/datasets/mathdial_bridge.json',
        'mathdial_hard': root / 'mathtutorbench/datasets/mathdial_bridge_hard.json',
        'socratic': root / 'mathtutorbench/data/gsm8k_socratic.jsonl',
        'bea2025_tutor': root / 'bea2025/mrbench_v3_devset.json',
        'mrbench_tutor': root / 'mrbench/MRBench_V2.json',
    }
    datasets = {}
    rows = []
    groups_by_task = {}
    for task, path in paths.items():
        raw = path.read_bytes()
        entries = ([json.loads(line) for line in raw.splitlines() if line.strip()]
                   if path.suffix == '.jsonl' else json.loads(raw))
        if task.startswith('mathdial'):
            # Mirrors adapter _format_bridge filtering before it assigns indices.
            entries = [e for e in entries if e.get('dialog_history')]
        texts = []
        for entry in entries:
            if task.startswith('mathdial'):
                text = entry['problem']
            elif task == 'socratic':
                text = entry['question']
            else:
                text = entry.get('conversation_history') or entry.get('conversation history') or ''
            texts.append(normalized(str(text or '')))
        kind = 'problem' if task in ('mathdial_standard', 'mathdial_hard', 'socratic') else 'conversation'
        hashes = [digest(kind + ':' + t) if t else '' for t in texts]
        groups_by_task[task] = hashes
        datasets[task] = {'source_path': path.relative_to(root).as_posix(),
                          'source_sha256': hashlib.sha256(raw).hexdigest(),
                          'rows_after_adapter_filter': len(entries),
                          'group_kind': kind, 'unresolved_source_rows': hashes.count(''),
                          'unique_normalized_groups': len(set(hashes) - {''})}
        for index, group in enumerate(hashes):
            rows.append({'task': task, 'source_row_index': index,
                         'group_kind': kind, 'group_sha256': group})
    overlaps = []
    for left, right in combinations(datasets, 2):
        if datasets[left]['group_kind'] != datasets[right]['group_kind']:
            continue
        a, b = set(groups_by_task[left]) - {''}, set(groups_by_task[right]) - {''}
        overlaps.append({'left': left, 'right': right, 'shared_normalized_groups': len(a & b),
                         'left_unique': len(a), 'right_unique': len(b)})
    with semantic.open() as handle:
        contexts = sorted({(r['task'], r['pair_id']) for r in csv.DictReader(handle)})
    semantic_rows = []
    for task, pair_id in contexts:
        if task == 'longtutor':
            if '||' not in pair_id:
                raise ValueError('Unknown LongTutor history key format')
            group = digest('learner:' + pair_id.split('||', 1)[0])
            kind = 'learner_identifier'
        elif task in groups_by_task:
            index = int(pair_id.removeprefix('soc-'))
            group = groups_by_task[task][index]
            kind = 'normalized_problem' if group else 'unresolved_missing_problem'
        else:
            raise ValueError(f'Unmapped semantic task {task}')
        semantic_rows.append({'task': task, 'pair_key_sha256': digest(task + ':' + pair_id),
                              'group_kind': kind, 'group_sha256': group})
    selected = {task: {r['group_sha256'] for r in semantic_rows if r['task'] == task and r['group_sha256']}
                for task in sorted({r['task'] for r in semantic_rows})}
    semantic_overlap = [{'left': a, 'right': b, 'shared_groups': len(selected[a] & selected[b])}
                        for a, b in combinations(selected, 2)]
    result = {
        'status': 'exploratory source-dependence audit; not a confirmatory split',
        'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'semantic_input_sha256': hashlib.sha256(semantic.read_bytes()).hexdigest(),
        'normalization': 'Unicode NFKC, whitespace collapse, strip, casefold; punctuation and numbers retained',
        'datasets': datasets, 'source_overlap': overlaps,
        'semantic_contexts': len(semantic_rows),
        'semantic_unique_source_groups': len({r['group_sha256'] for r in semantic_rows} - {''}),
        'semantic_unresolved_contexts': sum(not r['group_sha256'] for r in semantic_rows),
        'semantic_contexts_per_task': dict(Counter(r['task'] for r in semantic_rows)),
        'semantic_source_groups_per_task': {t: len(v) for t, v in selected.items()},
        'semantic_source_overlap': semantic_overlap,
        'limitations': [
            'Source overlap concerns inputs, not duplicates of generated responses.',
            'Exact normalization misses paraphrases, prefixes, and related conversation turns.',
            'Matching whole problem text is not the same as matching full model input.',
            'Current adapters supply index reconstruction; historical source/adapter versions still need verification.',
            'BEA/MR overlap can establish dependence; unmatched records are not automatically independent.',
            'No model output was used to define source groups.',
            'Missing problem fields remain unresolved; empty strings never form a shared source group.',
        ],
    }
    output.mkdir(parents=True, exist_ok=True)
    for filename, records in [('source_groups.csv', rows), ('semantic_source_groups.csv', semantic_rows)]:
        with (output / filename).open('w') as handle:
            writer = csv.DictWriter(handle, fieldnames=list(records[0]))
            writer.writeheader()
            writer.writerows(records)
    (output / 'source_audit.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'datasets'}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--datasets-root', type=Path, required=True)
    parser.add_argument('--semantic', type=Path, default=Path('artifacts/semantic_panel/response_consensus.csv'))
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    audit(args.datasets_root, args.semantic, args.output_dir)
