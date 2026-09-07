#!/usr/bin/env python3
"""Use the complete main panel while an auxiliary probe is still unresolved.

Runs the original frozen estimators on every main-panel item, never imputes a
missing code, and never writes the full-study completion or official outputs.
"""
import fcntl
import hashlib
import json
from contextlib import ExitStack
from pathlib import Path

import pandas as pd

from analyze_personality_coding_v2 import analyze
from analyze_personality_confirmation_v3 import losses_and_comparisons, prompt_effects, repeat_diagnostics
from analyze_personality_robustness_v3 import evaluate_panels, generator_deletion
from run_personality_formal_stage_v3 import ROOT, BASE, validate_stage, verify_files
from run_personality_requests_v2 import read_rows, now

OUT = BASE / 'complete_main_checkpoint'


def main():
    with ExitStack() as stack:
        original = BASE / 'confirmation/judge/v2_2'
        expanded = BASE / 'confirmation/budget_recovery/judge'
        sources = [(original, original / 'run_repair2'), (expanded, expanded / 'run')]
        for _, source in sources:
            lock = stack.enter_context((source / 'writer.lock').open('r'))
            fcntl.flock(lock.fileno(), fcntl.LOCK_SH | fcntl.LOCK_NB)
        validate_stage('confirmation')
        for name in ['confirmation_execution_policy.json', 'prediction_lock.json',
                     'judge_sensitivity_lock.json', 'generator_deletion_lock.json',
                     'confirmation_budget_amendment.json']:
            verify_files(json.loads((BASE / name).read_text())['files'])
        if OUT.exists():
            raise ValueError('Checkpoint already exists; preserve its first computation')
        OUT.mkdir()
        rubric = ROOT / 'data/educational_personality_measurement_v2_2.json'
        coded, coverages = [], []
        for index, (judge, source) in enumerate(sources):
            diagnostics = OUT / ('input_audit_' + str(index))
            analyze(judge, source, diagnostics, rubric)
            coded.append(pd.read_csv(diagnostics / 'event_codes.csv'))
            coverages.append(pd.read_csv(diagnostics / 'coverage.csv'))
        codes = pd.concat(coded, ignore_index=True)
        valid = pd.concat([part[part.valid] for part in coverages], ignore_index=True)
        if valid.request_id.duplicated().any() or codes.duplicated(['blind_id', 'judge_requested', 'event']).any():
            raise ValueError('Budget groups overlap')
        items = {r['blind_id']: r for r in read_rows(original / 'unblinding.jsonl')}
        wanted = {k: item for k, item in items.items() if item['panel'] == 'main'}
        if len(wanted) != 3840:
            raise ValueError('Main manifest changed')
        events = list(json.loads(rubric.read_text())['events'])
        judges = {'MiniMax-M3', 'deepseek-v4-pro', 'glm-5.3'}
        main = codes[codes.blind_id.isin(wanted)].copy()
        expected = {(blind, judge, event) for blind in wanted for judge in judges for event in events}
        actual = set(main[['blind_id', 'judge_requested', 'event']].itertuples(index=False, name=None))
        if actual != expected or len(main) != len(expected):
            raise ValueError('Main panel is not completely measured by all three original coders')
        if not main.judge_requested.eq(main.judge_returned).all():
            raise ValueError('Returned deployment mismatch')
        rows = []
        for (blind, event), part in main.groupby(['blind_id', 'event']):
            item = wanted[blind]
            rows.append(dict(blind_id=blind, event=event, present=int(part.present.sum() > 1.5),
                             unanimous=int(part.present.nunique() == 1),
                             **{k: item[k] for k in ['model', 'template', 'progress', 'affect', 'repeat',
                                                     'source_family', 'partition', 'panel', 'arm']}))
        frame = pd.DataFrame(rows)
        if len(frame) != 30720:
            raise ValueError('Incomplete main consensus')
        diag = OUT / 'main_measurement'
        diag.mkdir()
        main.to_csv(diag / 'event_codes.csv', index=False)
        frame.to_csv(diag / 'consensus.csv', index=False)
        canonical = frame[frame.arm.eq('canonical')]
        if canonical.blind_id.nunique() != 1280 or canonical.source_family.nunique() != 32:
            raise ValueError('Canonical prediction panel changed')
        predictions = pd.concat([pd.read_csv(BASE / 'locked_predictions/predictions.csv'),
                                 pd.read_csv(BASE / 'locked_predictions/style_predictions.csv')])
        primary = OUT / 'primary'
        primary.mkdir()
        scored, losses, comparisons = losses_and_comparisons(predictions, canonical)
        scored.to_csv(primary / 'scored_locked_predictions.csv', index=False)
        losses.to_csv(primary / 'source_prediction_losses.csv', index=False)
        losses.groupby(['event', 'baseline']).brier.mean().to_csv(primary / 'prediction_brier.csv')
        comparisons.to_csv(primary / 'primary_prediction_comparisons.csv', index=False)
        source_effects, effects = prompt_effects(frame)
        source_effects.to_csv(primary / 'source_prompt_rates.csv', index=False)
        effects.to_csv(primary / 'paired_prompt_effects.csv', index=False)
        repeat_diagnostics(frame).to_csv(primary / 'repeat_diagnostics.csv', index=False)
        canonical.groupby(['model', 'event']).present.agg(['size', 'mean']).to_csv(primary / 'default_profiles.csv')
        canonical.groupby(['model', 'event', 'progress', 'affect']).present.agg(['size', 'mean']).to_csv(primary / 'student_state_profiles.csv')
        robustness = OUT / 'locked_panel_sensitivities'
        robustness.mkdir()
        panels = evaluate_panels(diag, robustness)
        deletions = generator_deletion(diag, robustness)
        files = [Path(__file__).resolve(), rubric, original / 'manifest.jsonl', original / 'unblinding.jsonl',
                 *[source / 'responses.jsonl' for _, source in sources],
                 BASE / 'prediction_lock.json', BASE / 'judge_sensitivity_lock.json',
                 BASE / 'generator_deletion_lock.json', ROOT / 'scripts/analyze_personality_confirmation_v3.py',
                 ROOT / 'scripts/analyze_personality_robustness_v3.py']
        receipt = dict(completed_at=now(), status='complete main-panel checkpoint; full study remains incomplete',
            valid_main_judge_codes=11520, main_answers=3840, canonical_answers=1280, main_consensus_events=30720,
            canonical_source_families=32, paired_prompt_source_families=16,
            primary_tests=6, judge_sensitivity_panels=int(panels.judge_panel.nunique()),
            generator_deletion_panels=int(deletions.deleted_generator.nunique()),
            new_models_fitted=0, new_api_calls=0, missing_values_imputed=0,
            original_estimator_functions_reused=True, official_results_written=False, paper_complete=False,
            pending=['Auxiliary probe completion', '200 training-source resamples', 'Content sensitivity',
                     'Budget sensitivity', 'Full scientific synthesis and paper review'],
            inputs={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files})
        (OUT / 'summary.json').write_text(json.dumps(receipt, indent=2) + '\n')
        print(comparisons.to_string(index=False), flush=True)
        print(json.dumps(receipt), flush=True)


if __name__ == '__main__':
    main()
