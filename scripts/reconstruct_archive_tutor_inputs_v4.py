#!/usr/bin/env python3
"""Recover current-adapter inputs and archive joins locally, without API calls.

Hashes/pointers are publishable audit outputs; actual reconstructed source text
remains in an ignored local directory. Reconstruction is not historic request
attestation. No old human annotations or hidden reasoning are exported.
"""
import argparse
import ast
from collections import Counter, defaultdict
import hashlib
import importlib
import json
from pathlib import Path
import re
import subprocess
import sys
import types
import unicodedata

from audit_archive_coverage import canonical, CORE_MODELS
from audit_archive_roles_v3 import CENSUS, ROOT
from run_personality_requests_v2 import digest, now

SPECS = [('mrbench', 'MRBenchTutorAdapter'), ('bea2025', 'BEA2025TutorAdapter'),
         ('mathtutorbench', 'MTBScaffolding'), ('mathtutorbench', 'MTBPedagogy'),
         ('mathtutorbench', 'MTBScaffoldingHard'), ('mathtutorbench', 'MTBPedagogyHard')]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized(text):
    # Keep case and punctuation: do not equate variable A with a or alter math.
    return ' '.join(unicodedata.normalize('NFC', text).split())


def reference_status(text):
    if not text.strip():
        return 'absent'
    if text.strip().casefold() in {'n/a', 'na', 'none', 'not available', 'no solution provided', 'unknown'}:
        return 'placeholder'
    return 'provided_unvalidated'


def problem_from_conversation(text):
    first = re.split(r'\n\s*(?:Student|Tutor|Teacher):', text, maxsplit=1)[0]
    marker = 'The question is:'
    if first.count(marker) != 1:
        return '', 'unrecovered_question_boundary'
    problem = first.split(marker, 1)[1].strip()
    return (problem, 'explicit_first_turn_question_marker') if problem else ('', 'empty_question')


def assign_source_groups(materials):
    """Join only exact normalized questions or exact normalized conversations."""
    parent = list(range(len(materials)))
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    seen = {}
    edges = []
    for i, row in enumerate(materials):
        for kind, text in [('question', row['problem']), ('conversation', row['conversation'])]:
            value = normalized(text)
            if not value:
                continue
            key = (kind, digest(value))
            if key in seen:
                j = seen[key]
                parent[find(i)] = find(j)
                edges.append({'left': materials[j]['material_id'], 'right': row['material_id'],
                              'evidence': 'exact_normalized_' + kind, 'text_sha256': key[1]})
            else:
                seen[key] = i
    components = defaultdict(list)
    for i, row in enumerate(materials):
        components[find(i)].append(row)
    for group in components.values():
        ident = digest(sorted(r['material_id'] for r in group))[:24]
        for row in group:
            row['source_group'] = ident
    return edges


def method_digest(source, cls, method):
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == cls:
            for entry in node.body:
                if isinstance(entry, (ast.FunctionDef, ast.AsyncFunctionDef)) and entry.name == method:
                    return digest(ast.dump(entry, include_attributes=False))
    return None


def method_history(repo, path, cls, method):
    current = method_digest((repo / path).read_text(), cls, method)
    commits = subprocess.check_output(['git', '-C', str(repo), 'log', '--format=%H', '--', path], text=True).splitlines()
    records = []
    for commit in commits:
        result = subprocess.run(['git', '-C', str(repo), 'show', commit + ':' + path], capture_output=True, text=True)
        value = method_digest(result.stdout, cls, method) if result.returncode == 0 else None
        records.append({'commit': commit, 'method_sha256': value, 'matches_current': value is not None and value == current})
    return {'path': path, 'class': cls, 'method': method, 'current_method_sha256': current,
            'historical_versions': records,
            'limit': 'AST stability of this method is not execution provenance, data identity, or a complete client/provider audit.'}


def materialize(repo):
    package = types.ModuleType('_persona_archive_eval')
    package.__path__ = [str(repo / 'scripts/eval')]
    sys.modules[package.__name__] = package
    materials, sources = [], set()
    for module, cls in SPECS:
        loaded = importlib.import_module(package.__name__ + '.benchmarks.' + module)
        adapter = getattr(loaded, cls)()
        if module == 'mrbench':
            raw = json.loads(loaded.DATA.read_text())
            sources.add(loaded.DATA)
        elif module == 'bea2025':
            sources.add(loaded.DEV_PATH)
        else:
            sources.add(loaded.BRIDGE_DIR / adapter.SOURCE)
        for item in adapter.load_items():
            meta = item['meta']
            if item['image_paths']:
                raise ValueError('Text-only reconstruction encountered images')
            conversation = meta.get('conversation_history') or meta.get('dialog_history') or ''
            if 'problem' in meta:
                problem = meta['problem']
                boundary = 'explicit_problem_field' if problem.strip() else 'empty_explicit_problem_field'
            else:
                problem, boundary = problem_from_conversation(conversation)
            reference = (raw[int(item['item_id'][1:])].get('Ground_Truth_Solution', '') if module == 'mrbench'
                         else meta.get('reference_solution', ''))
            materials.append({'material_id': adapter.name + ':' + item['item_id'], 'benchmark': adapter.name,
                              'item_id': item['item_id'], 'messages': adapter.build_messages(item),
                              'conversation': conversation, 'problem': problem, 'question_boundary': boundary,
                              'reference_solution': reference,
                              'reference_status': reference_status(reference),
                              'source_conversation_id': str(meta.get('conversation_id', '')),
                              'source_dataset': meta.get('data') or 'not_individually_verified',
                              'adapter_class': cls})
    if len({r['material_id'] for r in materials}) != len(materials):
        raise ValueError('Duplicate benchmark/item IDs')
    dependencies = {Path(m.__file__) for name, m in sys.modules.items()
                    if name.startswith(package.__name__) and getattr(m, '__file__', None)}
    return materials, sources, dependencies


def main(repo, output):
    materials, sources, dependencies = materialize(repo)
    edges = assign_source_groups(materials)
    lookup = {(r['benchmark'], r['item_id']): r for r in materials}
    census = json.loads(CENSUS.read_text())
    names = {r['benchmark'] for r in materials}
    runs = [r for r in census['runs'] if r['benchmark'] in names]
    records, counts, unmatched = {}, Counter(), []
    for run in runs:
        path = repo / 'reports/eval' / run['path']
        if sha(path) != run['sha256']:
            raise ValueError('Archive prediction differs from frozen census: ' + run['path'])
        sp = path.with_name('summary.json')
        if (sha(sp) if sp.exists() else None) != run['summary_sha256']:
            raise ValueError('Archive summary differs from frozen census')
        summary = json.loads(sp.read_text()) if sp.exists() else {}
        latest = {}
        with path.open() as stream:
            for line_number, line in enumerate(stream, 1):
                if not line.strip():
                    continue
                row = json.loads(line)
                item = str(row.get('item_id') or '')
                if not item:
                    continue
                model = canonical(row.get('model') or summary.get('model') or path.parent.name)
                response = row.get('response')
                latest[(model, item)] = (row, line_number) if isinstance(response, str) and response.strip() and not row.get('error') else None
        for (model, item), value in latest.items():
            if value is None:
                continue
            counts['latest_successful_file_items'] += 1
            if (run['benchmark'], item) not in lookup:
                unmatched.append({'path': run['path'], 'item_id': item, 'model': model})
                continue
            row, line_number = value
            source = lookup[(run['benchmark'], item)]
            key = (run['benchmark'], run['input_variant'], model, item, hashlib.sha256(row['response'].encode()).hexdigest())
            if key not in records:
                records[key] = {'benchmark': key[0], 'input_variant': key[1], 'model': model,
                                'item_id': item, 'response_sha256': key[4], 'material_id': source['material_id'],
                                'source_group': source['source_group'], 'record_pointers': [],
                                'reconstructed_messages_sha256': digest(source['messages']),
                                'input_evidence': 'current_adapter_reconstruction_not_historic_attestation'}
            records[key]['record_pointers'].append({'path': run['path'], 'line': line_number})
    intersections = []
    for benchmark in sorted(names):
        for variant in sorted({k[1] for k in records if k[0] == benchmark}):
            per_model = defaultdict(set)
            multiplicity = Counter()
            for key in records:
                if key[:2] == (benchmark, variant):
                    per_model[key[2]].add(key[3])
                    multiplicity[(key[2], key[3])] += 1
            shared = set.intersection(*(per_model[m] for m in CORE_MODELS)) if all(m in per_model for m in CORE_MODELS) else set()
            intersections.append({'benchmark': benchmark, 'input_variant': variant,
                'six_model_shared_items': len(shared),
                'six_model_shared_source_groups': len({lookup[(benchmark, i)]['source_group'] for i in shared}),
                'per_model_items': {m: len(v) for m, v in sorted(per_model.items())},
                'model_item_cells_with_multiple_distinct_texts': sum(v > 1 for v in multiplicity.values())})
    history = [method_history(repo, 'scripts/eval/benchmarks/' + module + '.py', cls, 'load_items')
               for module, cls in [('mrbench', 'MRBenchTutorAdapter'), ('bea2025', 'BEA2025TutorAdapter'),
                                   ('mathtutorbench', '_WinRateBase')]]
    history.append(method_history(repo, 'scripts/eval/base.py', 'BenchmarkAdapter', 'build_messages'))
    index = [{k: v for k, v in r.items() if k not in ['messages', 'conversation', 'problem', 'reference_solution', 'source_conversation_id']}
             | {'reconstructed_messages_sha256': digest(r['messages']), 'conversation_sha256': digest(normalized(r['conversation'])),
                'problem_sha256': digest(normalized(r['problem'])) if r['problem'] else None,
                'reference_available': r['reference_status'] == 'provided_unvalidated'} for r in materials]
    components = defaultdict(list)
    for row in materials:
        components[row['source_group']].append(row)
    report = {'status': 'local archive reconstruction and source grouping complete; behavior validation not performed',
              'created_at': now(), 'api_calls': 0, 'human_annotations_added': 0,
              'task_items': len(materials), 'exact_match_source_groups': len(components),
              'cross_benchmark_source_groups': sum(len({r['benchmark'] for r in group}) > 1 for group in components.values()),
              'question_boundaries': dict(Counter(r['question_boundary'] for r in materials)),
              'reference_status_counts': dict(Counter(r['reference_status'] for r in materials)),
              'items_without_separately_recovered_question': sum(not r['problem'] for r in materials),
              'source_groups_with_unrecovered_questions': len({r['source_group'] for r in materials if not r['problem']}),
              'source_groups_without_any_recovered_question': sum(not any(r['problem'] for r in group) for group in components.values()),
              'per_benchmark_materials': {name: {
                  'items': sum(r['benchmark'] == name for r in materials),
                  'source_groups': len({r['source_group'] for r in materials if r['benchmark'] == name}),
                  'items_without_separately_recovered_question': sum(r['benchmark'] == name and not r['problem'] for r in materials),
                  'items_with_nonempty_unvalidated_reference': sum(r['benchmark'] == name and bool(r['reference_solution']) for r in materials),
                  'items_with_nonplaceholder_unvalidated_reference': sum(r['benchmark'] == name and r['reference_status'] == 'provided_unvalidated' for r in materials)
                  } for name in sorted(names)},
              'prediction_files_verified': len(runs), **dict(counts), 'variant_preserving_text_records': len(records),
              'unmatched_records': len(unmatched), 'candidate_intersections': intersections,
              'source_files': {str(p.relative_to(repo)): sha(p) for p in sorted(sources)},
              'loaded_adapter_dependencies': {str(p.relative_to(repo)): sha(p) for p in sorted(dependencies)},
              'audit_script_sha256': sha(Path(__file__)), 'census_sha256': sha(CENSUS),
              'edubenchmark_commit': subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip(),
              'limits': ['Reconstructed messages are current-adapter inputs, not stored historical provider requests.',
                         'Historical adapter AST comparisons cover named methods only, not full data/client/version lineage.',
                         'Exact question/conversation grouping misses paraphrased or otherwise shared conceptual sources.',
                         'Same-item distinct responses are retained; neither copies nor different texts prove independent calls.',
                         'All six tasks impose pedagogy instructions; they cannot alone validate unconstrained defaults.',
                         'Human-authored source dialogues/solutions can exist in the upstream datasets; no human annotation added here.',
                         'No original benchmark annotation, tutor gold response, hidden reasoning, or credential is exported.',
                         'No historical GLM-5.2 response is relabeled as current GLM-5.3.']}
    output.mkdir(parents=True, exist_ok=True)
    (output / 'local').mkdir(exist_ok=True)
    for filename, rows in [('local/materials.jsonl', materials), ('materials_index.jsonl', index),
                           ('response_index.jsonl', list(records.values())), ('source_group_edges.jsonl', edges),
                           ('unmatched_records.jsonl', unmatched)]:
        (output / filename).write_text(''.join(json.dumps(r, ensure_ascii=False, sort_keys=True) + '\n' for r in rows))
    (output / 'method_history.json').write_text(json.dumps(history, indent=2) + '\n')
    (output / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ['source_files', 'loaded_adapter_dependencies',
                                                               'candidate_intersections', 'limits']}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--benchmark-repo', type=Path, default=ROOT.parent / 'edubenchmark')
    parser.add_argument('--output', type=Path, default=ROOT / 'artifacts/educational_personality_v4/archive_bridge')
    args = parser.parse_args()
    main(args.benchmark_repo, args.output)
