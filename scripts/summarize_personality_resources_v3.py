#!/usr/bin/env python3
"""Account for persisted API attempts without double-counting reused records.

Reads a byte-prefix snapshot of each append-only response file. This is reported
usage, not provider billing, and excludes work that never produced a saved row.
"""
import collections
import hashlib
import json
from pathlib import Path

import pandas as pd

from run_personality_requests_v2 import now

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'artifacts/educational_personality_v2'


def phase(path):
    parts = path.parts
    if parts[0] == 'formal_design': return 'material_review'
    if parts[0] == 'runtime': return 'runtime_diagnostic'
    if parts[0] == 'prospective_pilot':
        return 'pilot_generation' if parts[1] == 'run' else 'pilot_measurement_development'
    if parts[0] == 'prospective_formal':
        if parts[1] == 'content_sensitivity': return 'confirmation_content_review'
        if parts[1] in ['training', 'confirmation']:
            return parts[1] + ('_generation' if parts[2] == 'run' else '_coding')
    raise ValueError('Unclassified response-file scope: ' + str(path))


def signature(row):
    fields = ['provider', 'endpoint', 'model', 'request_id', 'payload_sha256', 'started_at']
    if any(not row.get(k) for k in fields) or not isinstance(row.get('attempts'), list) or not row['attempts']:
        raise ValueError('Saved origin/attempt metadata incomplete; do not invent a call count')
    value = [row[k] for k in fields]
    return hashlib.sha256(json.dumps(value, ensure_ascii=False).encode()).hexdigest()


def account(snapshots):
    seen, copies, result = {}, 0, []
    for source, rows in snapshots:
        category = phase(source)
        for ordinal, row in enumerate(rows, start=1):
            origin = signature(row)
            fingerprint = hashlib.sha256(json.dumps(row, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
            if origin in seen:
                if seen[origin] != (fingerprint, category):
                    raise ValueError('Conflicting copies of a saved request origin')
                copies += 1
                continue
            seen[origin] = fingerprint, category
            attempts = row['attempts']
            numbers = [a['attempt'] for a in attempts]
            if numbers != list(range(1, len(attempts) + 1)):
                raise ValueError('Attempt sequence is incomplete or duplicated')
            record = {'origin_sha256': origin, 'first_snapshot_file': str(source), 'row_in_snapshot': ordinal,
                      'phase': category, 'provider': row['provider'], 'requested_model': row['model'],
                      'max_tokens': row['max_tokens'], 'saved_attempts': len(attempts),
                      'complete_attempts': sum(a.get('status') == 'complete' for a in attempts),
                      'failed_attempts': sum(a.get('status') != 'complete' for a in attempts),
                      'started_at': row['started_at'], 'completed_at': row['completed_at']}
            # The earlier runner stored sole-success usage only at top level.
            # That field cannot safely recover separate usage for multiple tries.
            fallback = (len(attempts) == 1 and attempts[0].get('status') == 'complete'
                        and 'usage' not in attempts[0] and not row.get('error')
                        and isinstance(row.get('usage'), dict))
            usages = [row['usage']] if fallback else [(a.get('usage') or {}) for a in attempts]
            record['single_attempt_top_level_usage_used'] = int(fallback)
            for key in ['prompt_tokens', 'completion_tokens', 'total_tokens']:
                known = [usage.get(key) for usage in usages]
                if any(v is not None and (type(v) is not int or v < 0) for v in known):
                    raise ValueError('Invalid reported usage count')
                record['reported_' + key] = sum(v for v in known if v is not None)
                record[key + '_unknown_attempts'] = sum(v is None for v in known)
            result.append(record)
    return pd.DataFrame(result), copies


def main():
    snapshots, files = [], []
    for path in sorted(BASE.rglob('responses.jsonl')):
        content = path.read_bytes()
        end = content.rfind(b'\n') + 1
        prefix = content[:end]
        rows = [json.loads(line) for line in prefix.splitlines() if line.strip()]
        snapshots.append((path.relative_to(BASE), rows))
        files.append({'path': str(path.relative_to(ROOT)), 'bytes_read': len(content),
                      'complete_prefix_bytes': end, 'trailing_partial_bytes_ignored': len(content) - end,
                      'complete_prefix_sha256': hashlib.sha256(prefix).hexdigest(), 'snapshot_rows': len(rows)})
    frame, copies = account(snapshots)
    metrics = ['saved_attempts', 'complete_attempts', 'failed_attempts',
               'single_attempt_top_level_usage_used',
               'reported_prompt_tokens', 'reported_completion_tokens', 'reported_total_tokens',
               'prompt_tokens_unknown_attempts', 'completion_tokens_unknown_attempts', 'total_tokens_unknown_attempts']
    grouped = frame.groupby(['phase', 'provider', 'requested_model', 'max_tokens'])[metrics].sum().reset_index()
    grouped['unique_saved_records'] = frame.groupby(['phase', 'provider', 'requested_model', 'max_tokens']).size().to_numpy()
    out = BASE / 'resource_accounting'
    out.mkdir(exist_ok=True)
    frame.to_csv(out / 'unique_saved_records.csv', index=False)
    grouped.to_csv(out / 'reported_usage_by_phase.csv', index=False)
    (out / 'input_prefixes.json').write_text(json.dumps(files, indent=2) + '\n')
    result = {'status': 'persisted-usage snapshot; active jobs and unsaved work prevent final resource totals',
              'snapshot_at': now(), 'input_files': len(files), 'raw_saved_row_copies': sum(f['snapshot_rows'] for f in files),
              'unique_saved_records': len(frame), 'reused_row_copies_excluded': copies,
              **{k: int(frame[k].sum()) for k in metrics},
              'phases': dict(collections.Counter(frame.phase)),
              'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'input_prefix_manifest_sha256': hashlib.sha256((out / 'input_prefixes.json').read_bytes()).hexdigest(),
              'limitations': ['Snapshot input files are read sequentially, not as a simultaneous transaction.',
                             'Only complete persisted JSONL rows are counted; in-flight or interrupted unsaved attempts are not measurable here.',
                             'Per-attempt usage is summed once. Sole-success legacy records may use top-level usage when their only attempt has no usage field; this fallback is counted explicitly.',
                             'Top-level usage is never added to existing per-attempt usage or used to impute separate costs for multiple attempts. Reused row copies are excluded.',
                             'Provider-reported total tokens are reported separately; reasoning tokens are not added on top of completion tokens.',
                             'Missing usage is explicitly counted, not imputed as zero cost. Tokenization and billing conventions vary by provider.',
                             'Model groups identify requested configurations for accounting; returned deployment identities are governed by the separate generation/coding audits.',
                             'Pilot measurement includes anchors, failed measurement protocols and preflight development, not just final valid pilot labels.',
                             'This snapshot is not a dollar-cost estimate, invoice reconciliation, final wall-clock total or independent-observation count.']}
    (out / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
