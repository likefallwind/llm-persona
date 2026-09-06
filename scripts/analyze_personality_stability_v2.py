#!/usr/bin/env python3
"""Exploratory educational-personality stability with source-safe splitting.

This reanalysis retains the historical hypotheses and failures. It measures
predictability of relative model profiles in fixed task/prompt settings, not
human personality or prospective confirmation. No provider calls are made.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def attach_groups(frame, mapping, unknown_policy):
    frame = frame.copy()
    frame['pair_key_sha256'] = [sha(t + ':' + p) for t, p in zip(frame.task, frame.pair_id)]
    if mapping.duplicated(['task', 'pair_key_sha256']).any():
        raise ValueError('Duplicate source mapping')
    frame = frame.merge(mapping, on=['task', 'pair_key_sha256'], how='left', validate='many_to_one', indicator=True)
    if not frame['_merge'].eq('both').all():
        raise ValueError('Missing source mapping')
    frame = frame.drop(columns='_merge')
    unknown = frame.group_sha256.isna() | frame.group_sha256.eq('')
    if unknown_policy == 'exclude':
        frame = frame[~unknown].copy()
    elif unknown_policy == 'conservative_cohort':
        # All unresolved Bridge examples travel together across both task variants.
        # This does not claim their original dialogue identity has been recovered.
        frame.loc[unknown, 'group_sha256'] = sha('unresolved_bridge_cohort_v2')
    else:
        raise ValueError('Unknown missing-source policy')
    return frame


def matrices(frame):
    keys = ['task', 'pair_id', 'dimension']
    models = sorted(frame.model.unique())
    if frame.duplicated(keys + ['model']).any():
        raise ValueError('Duplicate response-level scores')
    if not frame.groupby(keys).model.nunique().eq(len(models)).all():
        raise ValueError('Incomplete model panel')
    frame = frame.copy()
    frame['centered'] = frame.score - frame.groupby(keys).score.transform('mean')
    result = {}
    for dimension, part in frame.groupby('dimension'):
        wide = part.pivot(index=['task', 'pair_id', 'group_sha256'], columns='model', values='centered')[models]
        result[dimension] = wide
    return result


def source_weights(tasks, groups):
    counts = pd.Series(list(zip(tasks, groups))).value_counts()
    return np.array([1.0 / counts[(t, g)] for t, g in zip(tasks, groups)])


def profile(y, mask, weights):
    if not np.any(mask):
        raise ValueError('Empty task split')
    return np.average(y[mask], axis=0, weights=weights[mask])


def source_fold(groups, repeat):
    return np.array([int(sha(f'personality-source-v2:{repeat}:{g}')[:8], 16) % 2 for g in groups])


def crossfit(wide, repetitions):
    task_values = wide.index.get_level_values('task').to_numpy()
    groups = wide.index.get_level_values('group_sha256').to_numpy()
    tasks = sorted(set(task_values))
    weights = source_weights(task_values, groups)
    y = wide.to_numpy(float)
    records = []
    for repeat in range(repetitions):
        side = source_fold(groups, repeat)
        losses = {t: [] for t in tasks}
        for test_side in (0, 1):
            train = side != test_side
            test = ~train
            overlap = set(groups[train]) & set(groups[test])
            if overlap:
                raise ValueError('Source leakage')
            means = np.stack([profile(y, train & (task_values == t), weights) for t in tasks])
            global_mean = means.mean(axis=0)
            for i, task in enumerate(tasks):
                mask = test & (task_values == task)
                local_y = y[mask]
                if not len(local_y):
                    raise ValueError('Empty test task')
                err = np.stack([np.mean(local_y**2, axis=1),
                                np.mean((local_y-global_mean)**2, axis=1),
                                np.mean((local_y-means[i])**2, axis=1)], axis=1)
                losses[task].append((float(weights[mask].sum()), np.average(err, axis=0, weights=weights[mask])))
        errors_by_task = []
        for task, values in losses.items():
            errors = np.average(np.stack([x[1] for x in values]), axis=0, weights=[x[0] for x in values])
            errors_by_task.append(errors)
            records.append({'repeat': repeat, 'task': task, 'null_mse': errors[0],
                            'global_model_mse': errors[1], 'task_model_mse': errors[2],
                            'train_test_source_overlap': 0})
        errors = np.mean(errors_by_task, axis=0)
        records.append({'repeat': repeat, 'task': 'ALL_EQUAL_TASK_WEIGHT', 'null_mse': errors[0],
                        'global_model_mse': errors[1], 'task_model_mse': errors[2],
                        'train_test_source_overlap': 0})
    return pd.DataFrame(records)


def leave_task_out(wide):
    tasks = wide.index.get_level_values('task').to_numpy()
    groups = wide.index.get_level_values('group_sha256').to_numpy()
    weights = source_weights(tasks, groups)
    y = wide.to_numpy(float)
    records = []
    for heldout in sorted(set(tasks)):
        test = tasks == heldout
        heldout_groups = set(groups[test])
        train = (tasks != heldout) & np.array([g not in heldout_groups for g in groups])
        retained_tasks = sorted(set(tasks[train]))
        means = np.stack([profile(y, train & (tasks == t), weights) for t in retained_tasks])
        prediction = means.mean(axis=0)
        null = np.average(np.mean(y[test]**2, axis=1), weights=weights[test])
        predicted = np.average(np.mean((y[test]-prediction)**2, axis=1), weights=weights[test])
        records.append({'heldout_task': heldout, 'train_contexts': int(train.sum()),
                        'test_contexts': int(test.sum()),
                        'purged_overlapping_train_contexts': int(((tasks != heldout) & ~train).sum()),
                        'train_test_source_overlap': len(set(groups[train]) & heldout_groups),
                        'null_mse': float(null), 'global_model_mse': float(predicted),
                        'relative_improvement_over_null': float(1-predicted/null) if null else None})
    return records


def analyze(consensus_path, mapping_path, ratings_path, output, repetitions, excluded_tasks=()):
    original = pd.read_csv(consensus_path, dtype={'pair_id': str, 'item_id': str})
    original = original[original.arm != 'pedagogy'].copy()
    unknown_tasks = set(excluded_tasks) - set(original.task.unique())
    if unknown_tasks:
        raise ValueError(f'Unknown excluded tasks: {sorted(unknown_tasks)}')
    original = original[~original.task.isin(excluded_tasks)].copy()
    if original.task.nunique() < 2:
        raise ValueError('At least two tasks are needed for task transfer')
    mapping = pd.read_csv(mapping_path, keep_default_na=False)
    variants = {'consensus': original}
    if ratings_path:
        ratings = pd.read_csv(ratings_path, dtype={'pair_id': str, 'item_id': str})
        ratings = ratings[(ratings.arm != 'pedagogy') & ~ratings.task.isin(excluded_tasks)]
        keys = ['task', 'arm', 'pair_id', 'item_id', 'model', 'dimension']
        for judge in sorted(ratings.judge.unique()):
            variants['without_' + judge] = ratings[ratings.judge != judge].groupby(keys, as_index=False).score.median()
    results, transfers, coverage = [], [], []
    for missing in ('exclude', 'conservative_cohort'):
        for variant, data in variants.items():
            frame = attach_groups(data, mapping, missing)
            coverage.append({'source_policy': missing, 'score_panel': variant,
                             'contexts': len(frame[['task', 'pair_id']].drop_duplicates()),
                             'source_groups': frame.group_sha256.nunique()})
            for dimension, wide in matrices(frame).items():
                row = crossfit(wide, repetitions)
                row['dimension'], row['score_panel'], row['source_policy'] = dimension, variant, missing
                results.append(row)
                for transfer in leave_task_out(wide):
                    transfers.append({**transfer, 'dimension': dimension, 'score_panel': variant, 'source_policy': missing})
    result = pd.concat(results, ignore_index=True)
    result['relative_mse_reduction'] = 1-result.task_model_mse/result.global_model_mse
    summary = result.groupby(['source_policy', 'score_panel', 'dimension', 'task'], as_index=False).agg(
        null_mse=('null_mse', 'mean'), global_model_mse=('global_model_mse', 'mean'),
        task_model_mse=('task_model_mse', 'mean'),
        relative_mse_reduction=('relative_mse_reduction', 'mean'),
        split_p05=('relative_mse_reduction', lambda x: x.quantile(.05)),
        split_p95=('relative_mse_reduction', lambda x: x.quantile(.95)),
        fraction_splits_improved=('relative_mse_reduction', lambda x: (x > 0).mean()))
    output.mkdir(parents=True, exist_ok=True)
    result.to_csv(output/'source_safe_splits.csv', index=False)
    summary.to_csv(output/'source_safe_summary.csv', index=False)
    pd.DataFrame(transfers).to_csv(output/'leave_task_out.csv', index=False)
    meta = {'status': 'outcome-aware exploratory reanalysis', 'repetitions': repetitions,
            'excluded_tasks': sorted(set(excluded_tasks)),
            'coverage': coverage, 'source_leakage_detected': int(result.train_test_source_overlap.sum()),
            'input_hashes': {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                             for p in [consensus_path, mapping_path, *([ratings_path] if ratings_path else [])]},
            'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'limitations': ['Fixed task/prompt settings; task and prompt remain confounded.',
                           'Source grouping covers exact normalized matches, not every paraphrase lineage.',
                           'Unknown Bridge sources are excluded primarily and grouped together in sensitivity.',
                           'Equal source-group weight within task; equal task weight across tasks.',
                           'Split quantiles are sensitivity ranges, not confidence intervals.',
                           'Leave-one-judge-out is robustness, not independent measurement validation.',
                           'No repeated generation or previously unseen confirmation set.',
                           'Within-item centering evaluates relative panel behavior, not absolute unseen answers.']}
    (output/'analysis_metadata.json').write_text(json.dumps(meta, indent=2)+'\n')
    print(summary[(summary.task=='ALL_EQUAL_TASK_WEIGHT') & (summary.score_panel=='consensus')].to_string(index=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--consensus', type=Path, default=Path('artifacts/semantic_panel/response_consensus.csv'))
    parser.add_argument('--mapping', type=Path, default=Path('artifacts/educational_personality_v2/source_audit/semantic_source_groups.csv'))
    parser.add_argument('--ratings', type=Path, default=Path('artifacts/semantic_panel/unblinded_ratings.csv'))
    parser.add_argument('--output-dir', type=Path, default=Path('artifacts/educational_personality_v2/stability'))
    parser.add_argument('--repetitions', type=int, default=100)
    parser.add_argument('--exclude-task', action='append', default=[],
                        help='Post-hoc sensitivity only; omit a task from both fitting and evaluation. Repeatable.')
    args = parser.parse_args()
    if args.repetitions < 1:
        parser.error('repetitions must be positive')
    analyze(args.consensus, args.mapping, args.ratings, args.output_dir, args.repetitions, args.exclude_task)
