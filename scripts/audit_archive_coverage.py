#!/usr/bin/env python3
"""Read-only archive census; counts are coverage, not a matched research panel.

Handles both benchmark/model and benchmark/judge/model layouts. Response-text
deduplication does not establish independent calls or equivalent input prompts.
Only aggregate counts and file provenance are written; no response text or IDs.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from build_corpus_inventory import ALIASES, CORE_MODELS


def canonical(value):
    value = str(value).casefold()
    if value.startswith('qwen/'):
        value = value.split('/', 1)[1]
    return ALIASES.get(value, value)


def census(eval_root: Path, frozen_path: Path):
    paths = sorted(eval_root.rglob('predictions.jsonl'))
    active = [p for p in paths if not any(
        part.startswith('_') for part in p.relative_to(eval_root).parts)]
    # The input variant is retained: distinct input conditions must not collapse.
    unique = defaultdict(set)
    complete_unique = defaultdict(set)
    runs = []
    for index, path in enumerate(active):
        relative = path.relative_to(eval_root)
        summary_path = path.with_name('summary.json')
        summary_bytes = summary_path.read_bytes() if summary_path.exists() else b''
        try:
            summary = json.loads(summary_bytes) if summary_bytes else {}
        except (ValueError, UnicodeError):
            summary = {}
        if not isinstance(summary, dict):
            summary = {}
        complete = summary.get('run_status') == 'complete'
        variant = str(summary.get('input_variant') or 'unspecified')
        before = path.stat()
        digest = hashlib.sha256()
        counts = Counter()
        latest = {}
        model_counts = Counter()
        with path.open('rb') as handle:
            for line in handle:
                digest.update(line)
                if not line.strip():
                    continue
                counts['rows'] += 1
                try:
                    row = json.loads(line)
                except (ValueError, UnicodeError):
                    counts['malformed_rows'] += 1
                    continue
                if not isinstance(row, dict):
                    counts['malformed_rows'] += 1
                    continue
                item = row.get('item_id')
                if item is None or str(item) == '':
                    counts['missing_id_rows'] += 1
                    continue
                model = canonical(row.get('model') or summary.get('model') or path.parent.name)
                model_counts[model] += 1
                response = row.get('response')
                success = isinstance(response, str) and bool(response.strip()) and not row.get('error')
                key = (model, str(item))
                if key in latest:
                    counts['repeated_item_rows'] += 1
                latest[key] = hashlib.sha256(response.encode()).digest() if success else None
                counts['successful_rows' if success else 'unsuccessful_rows'] += 1
        after = path.stat()
        changed = (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns)
        summary_changed = summary_bytes != (summary_path.read_bytes() if summary_path.exists() else b'')
        for (model, item), response_hash in latest.items():
            if response_hash is not None:
                counts['latest_successful_items'] += 1
                key = (relative.parts[0], variant, model, item)
                unique[key].add(response_hash)
                if complete and not changed and not summary_changed:
                    complete_unique[key].add(response_hash)
        runs.append({
            'path': relative.as_posix(), 'sha256': digest.hexdigest(),
            'bytes': before.st_size, 'mtime_ns': before.st_mtime_ns,
            'changed_during_scan': changed or summary_changed,
            'summary_sha256': hashlib.sha256(summary_bytes).hexdigest() if summary_bytes else None,
            'benchmark': relative.parts[0], 'input_variant': variant,
            'models': sorted(model_counts), 'depth': len(relative.parts),
            'run_status': summary.get('run_status', 'unspecified'),
            'summary_total_items': summary.get('total_items'),
            'summary_scored': summary.get('scored'),
            'generation_params_present': bool(summary.get('generation_params')),
            **dict(counts),
        })
        if (index + 1) % 50 == 0:
            print(f'Scanned {index + 1}/{len(active)} prediction files', flush=True)

    def aggregate(mapping):
        models = defaultdict(Counter)
        benchmarks = defaultdict(Counter)
        overlap = defaultdict(lambda: defaultdict(set))
        for (benchmark, variant, model, item), hashes in mapping.items():
            for counter in (models[model], benchmarks[benchmark]):
                counter['model_item_keys'] += 1
                counter['distinct_response_texts'] += len(hashes)
                counter['keys_with_multiple_texts'] += len(hashes) > 1
            overlap[(benchmark, variant)][model].add(item)
        paired = []
        for (benchmark, variant), groups in sorted(overlap.items()):
            shared = set.intersection(*(groups[m] for m in CORE_MODELS)) if all(m in groups for m in CORE_MODELS) else set()
            paired.append({'benchmark': benchmark, 'input_variant': variant,
                           'models': len(groups), 'core_six_shared_ids': len(shared)})
        return {'model_item_keys': len(mapping),
                'distinct_response_texts': sum(len(v) for v in mapping.values()),
                'keys_with_multiple_texts': sum(len(v) > 1 for v in mapping.values()),
                'per_model': dict(sorted(models.items())),
                'per_benchmark': dict(sorted(benchmarks.items())),
                'id_overlap_not_protocol_verified': paired}

    frozen = json.loads(frozen_path.read_text())
    source_root = eval_root.parent.parent
    old_paths = [source_root / r['predictions_path'] for r in frozen['selected_runs']]
    existing = [p for p in old_paths if p.exists()]
    frozen_check = {'selected_paths': len(old_paths), 'existing_paths': len(existing),
                    'missing_paths': len(old_paths) - len(existing),
                    'note': 'Path existence only; missing paths can reflect relocation.'}
    variant_agnostic = defaultdict(set)
    for (benchmark, variant, model, item), hashes in unique.items():
        variant_agnostic[(benchmark, 'variant_agnostic_text_census', model, item)].update(hashes)
    return {
        'schema_version': 1, 'generated_at': datetime.now(timezone.utc).isoformat(),
        'scope': 'Active paths only; excludes every underscore-prefixed path component.',
        'dedup_key': 'benchmark, input_variant, canonical row model, item_id, exact response-text SHA256',
        'limitations': [
            'No generation-event deduplication: identical texts can arise from independent calls.',
            'Shared IDs are coverage candidates, not proof of identical prompts or harnesses.',
            'Latest row per model/item within a file; a later failure invalidates that file item.',
            'Complete summary status does not by itself prove item-level scoring completeness.',
            'No global atomic snapshot; per-file and end-of-scan metadata changes are checked.',
            'Missing input_variant remains distinct from explicitly recorded variants.',
        ],
        'all_prediction_files': len(paths), 'active_prediction_files': len(active),
        'excluded_prediction_files': len(paths) - len(active),
        'active_bytes': sum(r['bytes'] for r in runs),
        'raw_rows': sum(r.get('rows', 0) for r in runs),
        'latest_successful_file_items': sum(r.get('latest_successful_items', 0) for r in runs),
        'depth_counts': dict(Counter(r['depth'] for r in runs)),
        'run_status_counts': dict(Counter(r['run_status'] for r in runs)),
        'changed_paths': [r['path'] for r in runs if r['changed_during_scan'] or
                          (eval_root / r['path']).stat().st_mtime_ns != r['mtime_ns']],
        'frozen_inventory_path_check': frozen_check,
        'active_coverage': aggregate(unique),
        'variant_agnostic_text_coverage': aggregate(variant_agnostic),
        'complete_summary_coverage': aggregate(complete_unique), 'runs': runs,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--eval-root', type=Path, required=True)
    parser.add_argument('--frozen-inventory', type=Path, default=Path('artifacts/inventory/corpus_inventory.json'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = census(args.eval_root, args.frozen_inventory)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in
                      ('runs', 'active_coverage', 'complete_summary_coverage')}, ensure_ascii=False, indent=2))
    print('ACTIVE', json.dumps(result['active_coverage']['per_model'], ensure_ascii=False))


if __name__ == '__main__':
    main()
