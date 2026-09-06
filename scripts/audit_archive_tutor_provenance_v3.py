#!/usr/bin/env python3
"""Inspect archived tutor-record provenance without reading out response content.

Verifies selected prediction and summary bytes against the frozen census. Output
contains aggregate metadata coverage and candidate ID intersections only.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

from audit_archive_coverage import canonical, CORE_MODELS
from audit_archive_roles_v3 import CENSUS, ROOT

FIELDS = {
    'stored_messages': ['messages'],
    'stored_prompt_text': ['prompt', 'text', 'input'],
    'generation_prompt_hash': ['prompt_sha256', 'generation_prompt_sha256', 'input_sha256'],
    'provider_request_id': ['provider_completion_id', 'completion_id', 'request_id'],
    'returned_model_identity': ['returned_model', 'model_returned'],
    'generation_timestamp': ['started_at', 'completed_at', 'created_at', 'timestamp'],
    'finish_reason': ['finish_reason'],
    'usage': ['usage'],
}


def digest(value):
    return hashlib.sha256(value).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--eval-root', type=Path, default=ROOT.parent / 'edubenchmark/reports/eval')
    ap.add_argument('--output', type=Path, default=ROOT / 'artifacts/educational_personality_v2/archive_roles')
    args = ap.parse_args()
    census = json.loads(CENSUS.read_text())
    role_path = args.output / 'role_coverage.json'
    roles = json.loads(role_path.read_text())
    names = {r['benchmark'] for r in roles['benchmarks'] if r['reviewed_current_role'] == 'tutor_response'}
    runs = [r for r in census['runs'] if r['benchmark'] in names]
    per_benchmark = defaultdict(Counter)
    unique = defaultdict(set)
    overlap = defaultdict(lambda: defaultdict(set))
    file_reports = []
    for run in runs:
        path = args.eval_root / run['path']
        raw = path.read_bytes()
        if digest(raw) != run['sha256']:
            raise ValueError('Prediction file differs from census: ' + run['path'])
        sp = path.with_name('summary.json')
        sb = sp.read_bytes() if sp.exists() else b''
        if (digest(sb) if sb else None) != run['summary_sha256']:
            raise ValueError('Summary differs from census: ' + run['path'])
        summary = json.loads(sb) if sb else {}
        fields, latest = Counter(), {}
        for line in raw.splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            item = str(row.get('item_id') or '')
            if not item:
                continue
            model = canonical(row.get('model') or summary.get('model') or path.parent.name)
            response = row.get('response')
            success = isinstance(response, str) and bool(response.strip()) and not row.get('error')
            latest[(model, item)] = (row, digest(response.encode())) if success else None
        for (model, item), record in latest.items():
            if record is None:
                continue
            row, response_hash = record
            fields['latest_successful_file_items'] += 1
            for group, possible in FIELDS.items():
                fields[group] += any(row.get(name) not in (None, '', [], {}) for name in possible)
            key = (run['benchmark'], run['input_variant'], model, item)
            unique[key].add(response_hash)
            overlap[(run['benchmark'], run['input_variant'])][model].add(item)
        fields['prediction_files'] = 1
        fields['summary_generation_parameters'] = int(bool(summary.get('generation_params')))
        fields['summary_generation_prompt_hash'] = int(bool(summary.get('generation_prompt_sha256') or summary.get('prompt_sha256')))
        fields['summary_judge_prompt_hash'] = int(bool(summary.get('judge_prompt_sha256')))
        per_benchmark[run['benchmark']].update(fields)
        file_reports.append({'path': run['path'], 'prediction_sha256': run['sha256'],
                             'summary_sha256': run['summary_sha256'], 'benchmark': run['benchmark'],
                             'input_variant': run['input_variant'], 'coverage': dict(fields),
                             'generation_parameter_keys': sorted(summary.get('generation_params', {}))})
    intersections = []
    for (name, variant), groups in sorted(overlap.items()):
        shared = set.intersection(*(groups[m] for m in CORE_MODELS)) if all(m in groups for m in CORE_MODELS) else set()
        intersections.append({'benchmark': name, 'input_variant': variant,
                              'models_with_records': len(groups), 'legacy_core_six_shared_item_ids': len(shared),
                              'per_model_item_ids': {m: len(v) for m, v in sorted(groups.items())}})
    distinct = sum(len(v) for v in unique.values())
    expected = roles['role_totals']['tutor_response']['variant_preserving_records']
    if distinct != expected:
        raise ValueError('Tutor records do not reproduce role coverage count')
    totals = Counter()
    for group in per_benchmark.values():
        totals.update(group)
    report = {'status': 'selected archive bytes and provenance coverage audited; full historic inputs not reconstructed',
              'census_sha256': digest(CENSUS.read_bytes()), 'role_coverage_sha256': digest(role_path.read_bytes()),
              'script_sha256': digest(Path(__file__).read_bytes()),
              'all_selected_prediction_and_summary_hashes_match_census': True,
              'tutor_benchmarks': len(names), 'variant_preserving_text_records': distinct,
              'totals': dict(totals), 'per_benchmark': {k: dict(v) for k, v in sorted(per_benchmark.items())},
              'candidate_id_intersections': intersections, 'files': file_reports,
              'limitations': ['Metadata coverage counts use latest-successful file items before cross-directory deduplication.',
                             'Only named provenance fields are checked; missing fields can require external logs or source reconstruction.',
                             'Summary generation parameters may describe a later scoring run and do not prove original request settings.',
                             'Judge prompt hashes describe evaluation, not tutor-generation prompts.',
                             'Shared item IDs are candidates for comparison, not verified common input messages or independent sources.',
                             'Identical model/item/response text across directories is not proof of the same generation event.',
                             'No archived reasoning field is treated as an observable tutor answer or used for behavior coding.']}
    (args.output / 'tutor_provenance.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ['files', 'candidate_id_intersections', 'per_benchmark', 'limitations']}, indent=2))


if __name__ == '__main__':
    main()
