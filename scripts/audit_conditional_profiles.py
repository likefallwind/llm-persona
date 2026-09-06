#!/usr/bin/env python3
"""Exploratory held-out-context audit of existing semantic scores.

Tests task-specific profiles against a single model profile. This is NOT unseen
task transfer, temporal repeatability, a new trait-validation gate, or a causal
test of context. Task and prompt are confounded in these archived settings.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


def analyze(source: Path, output: Path, repetitions: int):
    data = pd.read_csv(source, dtype={'item_id': str, 'pair_id': str})
    output.mkdir(parents=True, exist_ok=True)
    paired = data[data.arm.isin(['generic', 'pedagogy'])]
    if set(paired.arm) == {'generic', 'pedagogy'}:
        paired = paired.pivot(index=['task', 'pair_id', 'model', 'dimension'],
                              columns='arm', values='score').dropna()
        direction = {}
        for dimension in sorted(paired.index.get_level_values('dimension').unique()):
            values = paired.xs(dimension, level='dimension')
            delta = values.pedagogy - values.generic
            direction[dimension] = {'paired_model_contexts': len(delta),
                                    'positive': int((delta > 0).sum()),
                                    'zero': int((delta == 0).sum()),
                                    'negative': int((delta < 0).sum())}
        (output / 'prompt_direction_audit.json').write_text(json.dumps(direction, indent=2) + '\n')
    data = data[data.arm != 'pedagogy'].copy()
    models = sorted(data.model.unique())
    tasks = sorted(data.task.unique())
    data['context_group'] = [
        ('mathdial' if task.startswith('mathdial') else task) + ':' + pair
        for task, pair in zip(data.task, data.pair_id)]
    keys = ['task', 'pair_id', 'dimension']
    if not data.groupby(keys).model.nunique().eq(len(models)).all():
        raise ValueError('Incomplete paired model panel')
    if data.duplicated(keys + ['model']).any():
        raise ValueError('Duplicate semantic rows')
    data['centered'] = data.score - data.groupby(keys).score.transform('mean')
    groups = sorted(data.context_group.unique())
    frames = {}
    for dimension, subset in data.groupby('dimension'):
        wide = subset.pivot(index=['task', 'context_group'], columns='model', values='centered')[models]
        frames[dimension] = wide
    rows = []
    for repeat in range(repetitions):
        # Shared context assignments across all dimensions and both MathDial arms.
        fold = {g: hashlib.sha256(f'20260905:{repeat}:{g}'.encode()).digest()[0] % 2 for g in groups}
        for dimension, wide in frames.items():
            side = np.array([fold[g] for t, g in wide.index])
            task_values = wide.index.get_level_values('task').to_numpy()
            y = wide.to_numpy()
            per_task = {t: [] for t in tasks}
            for test_side in (0, 1):
                training_profiles = np.stack([
                    y[(side != test_side) & (task_values == t)].mean(axis=0) for t in tasks])
                if not np.isfinite(training_profiles).all():
                    raise ValueError('Empty task training split')
                common_profile = training_profiles.mean(axis=0)
                for i, task in enumerate(tasks):
                    test_y = y[(side == test_side) & (task_values == task)]
                    if len(test_y) == 0:
                        raise ValueError('Empty task test split')
                    per_task[task].append((len(test_y),
                        float(np.mean(test_y ** 2)),
                        float(np.mean((test_y - common_profile) ** 2)),
                        float(np.mean((test_y - training_profiles[i]) ** 2))))
            task_errors = []
            for task, values in per_task.items():
                weights = np.array([v[0] for v in values])
                errors = np.average(np.array([v[1:] for v in values]), axis=0, weights=weights)
                task_errors.append(errors)
                rows.append({'repeat': repeat, 'dimension': dimension, 'task': task,
                             'null_mse': errors[0], 'global_model_mse': errors[1],
                             'task_model_mse': errors[2]})
            errors = np.mean(task_errors, axis=0)
            rows.append({'repeat': repeat, 'dimension': dimension, 'task': 'ALL_EQUAL_TASK_WEIGHT',
                         'null_mse': errors[0], 'global_model_mse': errors[1],
                         'task_model_mse': errors[2]})
    results = pd.DataFrame(rows)
    results['relative_mse_reduction'] = 1 - results.task_model_mse / results.global_model_mse
    summary = results.groupby(['dimension', 'task'], as_index=False).agg(
        null_mse=('null_mse', 'mean'), global_model_mse=('global_model_mse', 'mean'),
        task_model_mse=('task_model_mse', 'mean'),
        relative_mse_reduction_mean=('relative_mse_reduction', 'mean'),
        relative_mse_reduction_split_p05=('relative_mse_reduction', lambda x: x.quantile(.05)),
        relative_mse_reduction_split_p95=('relative_mse_reduction', lambda x: x.quantile(.95)),
        fraction_splits_improved=('relative_mse_reduction', lambda x: (x > 0).mean()))
    output.mkdir(parents=True, exist_ok=True)
    summary.to_csv(output / 'conditional_profile_summary.csv', index=False)
    results.to_csv(output / 'conditional_profile_splits.csv', index=False)
    metadata = {
        'status': 'outcome-aware exploratory internal diagnostic',
        'input_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'repeated_two_fold_splits': repetitions, 'models': models, 'tasks': tasks,
        'context_arms': int(data[['task', 'pair_id']].drop_duplicates().shape[0]),
        'split_groups': len(groups),
        'response_units': int(data[['task', 'pair_id', 'model']].drop_duplicates().shape[0]),
        'limitations': [
            'All data and dimensions were previously analyzed; no confirmatory holdout.',
            'Repeated split quantiles are sensitivity ranges, NOT confidence intervals.',
            'Scores are within-item contrasts using the entire observed model panel.',
            'Equal task weighting; model profiles learned only from training contexts.',
            'Prediction is within the same four task/prompt settings, not unseen tasks.',
            'Socratic/longitudinal/generic settings confound task and prompt.',
            'Split groups use context IDs, not verified underlying problem/dialogue lineage.',
            'Shared standard/hard MathDial context IDs stay in the same split.',
            'Common judge and six-candidate-slate artifacts can explain some structure.',
            'Failed historical reliability and trait-validation decisions remain unchanged.',
        ]}
    (output / 'conditional_profile_metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
    print(summary[summary.task == 'ALL_EQUAL_TASK_WEIGHT'].to_string(index=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=Path('artifacts/semantic_panel/response_consensus.csv'))
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--repetitions', type=int, default=100)
    args = parser.parse_args()
    if args.repetitions < 1:
        parser.error('--repetitions must be positive')
    analyze(args.input, args.output_dir, args.repetitions)


if __name__ == '__main__':
    main()
