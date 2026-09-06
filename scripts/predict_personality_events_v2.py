#!/usr/bin/env python3
"""Source-held-out prediction of absolute behavioral events, without test centering.

Pilot development utility. Formal inference requires a separately frozen design;
this script's cross-validation is not a substitute for a prospective holdout.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import expit
from sklearn.feature_extraction import DictVectorizer


BASELINES = ('context', 'default_profile', 'conditional_profile')


def feature_rows(frame, baseline):
    if baseline not in BASELINES:
        raise ValueError('Unknown baseline')
    result = []
    for row in frame.to_dict('records'):
        # Input-derived categorical values only. No answer length, observed
        # correctness, test item mean, or judge output is used as a feature.
        condition = '|'.join(str(row[key]) for key in ('progress', 'affect'))
        features = {'context': condition, 'domain': str(row['domain'])}
        if baseline != 'context':
            features['model'] = str(row['model'])
        if baseline == 'conditional_profile':
            features['model_context'] = str(row['model']) + '|' + condition
        result.append(features)
    return result


def fit_predict(train, test, baseline, penalty=1.0):
    if set(train.source_group) & set(test.source_group):
        raise ValueError('Train/test source overlap')
    if not len(train) or not len(test):
        raise ValueError('Empty train or test')
    vectorizer = DictVectorizer(sparse=False)
    x = vectorizer.fit_transform(feature_rows(train, baseline))
    z = vectorizer.transform(feature_rows(test, baseline))
    x = np.column_stack([np.ones(len(x)), x])
    z = np.column_stack([np.ones(len(z)), z])
    y = train.present.to_numpy(float)
    if not np.isfinite(y).all() or (y < 0).any() or (y > 1).any():
        raise ValueError('Labels must lie in [0, 1]')
    weights = 1/train.groupby('source_group').source_group.transform('size').to_numpy(float)
    weights *= len(weights)/weights.sum()
    if np.ptp(y) == 0:
        # No empirical class contrast: use the same finite smoothed constant for
        # every feature model, and explicitly report this degenerate training set.
        p = (np.sum(weights*y)+.5)/(weights.sum()+1)
        return np.full(len(test), p), {'constant_training_label': float(y[0]), 'converged': True}
    start = np.zeros(x.shape[1])
    rate = np.average(y, weights=weights)
    start[0] = np.log(rate/(1-rate))

    def objective(beta):
        eta = x@beta
        value = np.sum(weights*(np.logaddexp(0, eta)-y*eta)) + .5*penalty*np.sum(beta[1:]**2)
        gradient = x.T@(weights*(expit(eta)-y))
        gradient[1:] += penalty*beta[1:]
        return value, gradient

    fitted = minimize(objective, start, jac=True, method='L-BFGS-B', options={'maxiter': 1000, 'ftol': 1e-10})
    if not fitted.success:
        raise ValueError('Prediction fit did not converge')
    return expit(z@fitted.x), {'constant_training_label': None, 'converged': True}


def group_folds(groups, n_splits):
    unique = sorted(set(groups), key=lambda g: hashlib.sha256(('events-v2:'+g).encode()).hexdigest())
    if len(unique) < 2:
        raise ValueError('At least two independent source groups are required')
    n_splits = min(n_splits, len(unique))
    if n_splits < 2:
        raise ValueError('At least two folds are required')
    assignments = {group: index % n_splits for index, group in enumerate(unique)}
    return np.array([assignments[g] for g in groups])


def evaluate(frame, n_splits=5):
    required = {'source_group', 'model', 'domain', 'progress', 'affect', 'event', 'present', 'blind_id'}
    if not required <= set(frame):
        raise ValueError('Missing input metadata')
    if frame.duplicated(['blind_id', 'event']).any():
        raise ValueError('Duplicate item/event labels')
    rows = []
    for event, data in frame.groupby('event'):
        data = data.copy()
        data['fold'] = group_folds(data.source_group, n_splits)
        for fold in sorted(data.fold.unique()):
            train, test = data[data.fold != fold], data[data.fold == fold]
            for baseline in BASELINES:
                prediction, diagnostics = fit_predict(train, test, baseline)
                for (_, item), p in zip(test.iterrows(), prediction):
                    rows.append({'event': event, 'baseline': baseline, 'fold': int(fold),
                                 'blind_id': item.blind_id, 'source_group': item.source_group,
                                 'model': item.model, 'observed': item.present, 'predicted': float(p),
                                 'brier': float((p-item.present)**2), **diagnostics})
    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--consensus', type=Path, required=True)
    parser.add_argument('--mapping', type=Path, required=True)
    parser.add_argument('--deployment-audit', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    frame = pd.read_csv(args.consensus)
    mappings = [json.loads(line) for line in args.mapping.read_text().splitlines() if line.strip()]
    metadata = pd.DataFrame([{'blind_id': r['blind_id'], 'domain': r['domain'], 'source_group': r['template']} for r in mappings])
    frame = frame.merge(metadata, on='blind_id', validate='many_to_one')
    audit = json.loads(args.deployment_audit.read_text())
    if audit['status'] != 'pass' or any(len(v) != 1 for v in audit['requested_to_returned'].values()):
        raise ValueError('Unverified deployment panel')
    deploy = {k: v[0] for k,v in audit['requested_to_returned'].items()}
    frame['model'] = frame.model.map(deploy)
    if frame.model.isna().any():
        raise ValueError('Unknown deployment')
    result = evaluate(frame)
    args.output.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.output/'predictions.csv', index=False)
    source_means = result.groupby(['event', 'baseline', 'source_group']).brier.mean().reset_index()
    source_means.to_csv(args.output/'source_losses.csv', index=False)
    summary = source_means.groupby(['event', 'baseline']).brier.mean().unstack('baseline')
    summary['default_gain_absolute'] = summary.context-summary.default_profile
    summary['conditional_gain_absolute'] = summary.default_profile-summary.conditional_profile
    summary.to_csv(args.output/'prediction_summary.csv')
    (args.output/'limitations.json').write_text(json.dumps({
        'status': 'pilot model-development diagnostics; not confirmatory inference',
        'penalty': 1, 'source_groups': frame.source_group.nunique(),
        'scope': 'Absolute event probabilities predicted from training labels and input metadata only.',
        'limitations': ['Four pilot templates cannot establish cross-domain educational personality.',
                       'Domain and template coincide in this pilot.',
                       'No inference thresholds or confidence intervals are estimated here.',
                       'Source-equal evaluation does not make template variants independent.',
                       'Regularization and feature design require prospective freezing before formal data.']
    }, indent=2)+'\n')
    print(summary.to_string())


if __name__ == '__main__':
    main()
