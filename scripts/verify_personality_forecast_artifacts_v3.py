#!/usr/bin/env python3
"""Reconstruct every locked probability without reading confirmation outputs.

Checks serialization, panel coverage, selected penalties and coefficient export.
This is numerical reproducibility evidence, not independent scientific evidence.
It calls the frozen design builders, but never an optimizer or an API.
"""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import expit

import predict_personality_events_v3 as predictor
import personality_style_competitor_v3 as style
from run_personality_formal_stage_v3 import ROOT, BASE, verify_files
from run_personality_requests_v2 import now


def reconstruct(train, target, model, baseline):
    if baseline == 'training_style_profile':
        x, z, w, profiles = style.style_design(train, target)
        saved = pd.DataFrame.from_dict(model['profiles'], orient='index').loc[profiles.index, profiles.columns]
        np.testing.assert_allclose(profiles.to_numpy(), saved.to_numpy(), rtol=0, atol=1e-12)
    else:
        x, z, w, ranks = predictor.design(train, target, baseline)
        if list(ranks) != model['block_ranks']:
            raise ValueError('Reconstructed design ranks differ')
    scores = model['tuning'] if baseline == 'training_style_profile' else model['tuning']['scores']
    tuning = {float(k): float(v) for k, v in scores.items()}
    best = min(tuning.values())
    selected = max(p for p, loss in tuning.items() if loss <= best + 1e-10)
    if selected != model['penalty'] or set(tuning) != set(predictor.PENALTIES):
        raise ValueError('Saved penalty is not the frozen strongest-tie choice')
    beta = model['coefficients']
    y = train.present.to_numpy(float)
    if beta is None:
        if np.ptp(y) != 0:
            raise ValueError('Constant forecast has nonconstant training labels')
        probability = (np.sum(w * y) + .5) / (w.sum() + 1)
        np.testing.assert_allclose(probability, model['constant_probability'], rtol=0, atol=1e-12)
        return np.full(len(target), probability), None
    beta = np.asarray(beta)
    if len(beta) != z.shape[1] or not np.isfinite(beta).all():
        raise ValueError('Coefficient dimensions or finiteness failed')
    gradient = x.T @ (w * (expit(x @ beta) - y))
    gradient[1:] += model['penalty'] * beta[1:]
    norm = float(np.max(np.abs(gradient)))
    np.testing.assert_allclose(norm, model['gradient_inf'], rtol=1e-5, atol=1e-10)
    return expit(z @ beta), norm


def main():
    locks = ['prediction_lock.json', 'judge_sensitivity_lock.json', 'generator_deletion_lock.json']
    inputs = []
    for name in ['design_freeze.json', 'training_execution_policy.json', 'confirmation_execution_policy.json', *locks]:
        p = BASE / name
        verify_files(json.loads(p.read_text())['files'])
        inputs.append(p)
    train = pd.read_csv(BASE / 'locked_predictions/training_frame.csv')
    target = pd.read_csv(BASE / 'locked_predictions/confirmation_input_frame.csv')
    panel_labels = pd.read_csv(BASE / 'locked_judge_sensitivity/training_panel_labels.csv')
    configurations = set(train.model)
    if len(configurations) != 5 or len(target) != 1280 or target.blind_id.duplicated().any():
        raise ValueError('Wrong full confirmation input grid')
    if set(train.source_group) & set(target.source_group):
        raise ValueError('Training and target sources overlap')
    specs = [
        ('primary', 'locked_predictions/models.json', 'locked_predictions/predictions.csv', 32, 40960),
        ('style', 'locked_predictions/style_models.json', 'locked_predictions/style_predictions.csv', 8, 10240),
        ('judge', 'locked_judge_sensitivity/models.json', 'locked_judge_sensitivity/predictions.csv', 120, 153600),
        ('deletion', 'locked_generator_deletion/models.json', 'locked_generator_deletion/predictions.csv', 75, 76800),
    ]
    rows = []
    for kind, model_path, prediction_path, expected_models, expected_rows in specs:
        models = json.loads((BASE / model_path).read_text())
        predictions = pd.read_csv(BASE / prediction_path)
        inputs.extend([BASE / model_path, BASE / prediction_path])
        if len(models) != expected_models or len(predictions) != expected_rows:
            raise ValueError('Wrong locked artifact size: ' + kind)
        group_keys = ['event', 'baseline'] + ({'judge': ['judge_panel'], 'deletion': ['deleted_generator']}.get(kind, []))
        if predictions.duplicated([*group_keys, 'blind_id']).any():
            raise ValueError('Duplicated probability key')
        groups = predictions.groupby(group_keys, sort=False)
        seen = set()
        for model in models:
            event = model['event']
            baseline = 'training_style_profile' if kind == 'style' else model['baseline']
            identity = {'event': event, 'baseline': baseline,
                        **{k: model[k] for k in ['judge_panel', 'deleted_generator'] if k in model}}
            key = tuple(identity[k] for k in group_keys)
            if key in seen:
                raise ValueError('Duplicate fitted model key')
            seen.add(key)
            fitting = train[train.event.eq(event)]
            test = target
            if kind == 'judge':
                labels = panel_labels[panel_labels.event.eq(event) & panel_labels.judge_panel.eq(model['judge_panel'])]
                fitting = fitting.drop(columns='present').merge(labels, on=['blind_id', 'event', 'model'], validate='one_to_one')
            if kind == 'deletion':
                fitting = fitting[fitting.model.ne(model['deleted_generator'])]
                test = target[target.model.ne(model['deleted_generator'])]
            expected_n = 1024 if kind == 'deletion' else 1280
            if len(fitting) != expected_n or len(test) != expected_n:
                raise ValueError('Wrong reconstructed fitting/target grid')
            reconstructed, gradient = reconstruct(fitting, test, model, baseline)
            saved = groups.get_group(key)
            if set(saved.blind_id) != set(test.blind_id):
                raise ValueError('Probability cells differ from target inputs')
            saved = saved.set_index('blind_id').loc[test.blind_id]
            if not saved.probability.between(0, 1).all():
                raise ValueError('Invalid saved probability')
            for column in ['source_group', 'template', 'domain', 'progress', 'affect', 'model', 'repeat', 'request_id']:
                if saved[column].tolist() != test[column].tolist():
                    raise ValueError('Saved target metadata differs: ' + column)
            error = float(np.max(np.abs(reconstructed - saved.probability.to_numpy())))
            np.testing.assert_allclose(reconstructed, saved.probability, rtol=0, atol=1e-12)
            rows.append({'artifact_group': kind, **identity, 'predictions_checked': len(test),
                         'max_absolute_probability_error': error, 'reconstructed_gradient_inf': gradient,
                         'constant_training_labels': model['coefficients'] is None})
        if seen != set(groups.groups):
            raise ValueError('Orphan prediction group or missing model')
    output = BASE / 'forecast_reconstruction_audit'
    output.mkdir(exist_ok=True)
    frame = pd.DataFrame(rows)
    frame.to_csv(output / 'models.csv', index=False)
    inputs.extend([BASE / 'locked_predictions/training_frame.csv',
                   BASE / 'locked_predictions/confirmation_input_frame.csv',
                   BASE / 'locked_judge_sensitivity/training_panel_labels.csv', Path(__file__).resolve(),
                   ROOT / 'scripts/predict_personality_events_v3.py', ROOT / 'scripts/personality_style_competitor_v3.py'])
    result = {'status': 'all locked probabilities reconstructed without refitting', 'verified_at': now(),
              'fitted_models_checked': len(frame), 'probabilities_checked': int(frame.predictions_checked.sum()),
              'maximum_absolute_probability_error': float(frame.max_absolute_probability_error.max()),
              'maximum_reconstructed_gradient_inf': float(frame.reconstructed_gradient_inf.max()),
              'constant_label_models': int(frame.constant_training_labels.sum()),
              'confirmation_outputs_read': False, 'api_calls': 0, 'optimizer_calls': 0,
              'input_hashes': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
              'limitations': ['Reuses frozen design builders; this checks artifact export, not independent implementation of the scientific model.',
                             'Selected penalties are checked against saved CV losses; CV is not rerun.',
                             'Successful optimizer termination in the frozen code can have gradient above 1e-6; actual gradients are reported, not silently reclassified.',
                             'No predictive accuracy or personality inference follows from this numerical audit.']}
    (output / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'input_hashes'}, indent=2))


if __name__ == '__main__':
    main()
