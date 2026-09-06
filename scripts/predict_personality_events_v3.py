#!/usr/bin/env python3
"""Nested source-held-out behavioral prediction with orthogonal feature blocks.

Training-only block orthogonalization preserves the common ridge geometry when
new interactions are added. All model selection uses training source groups.
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

from predict_personality_events_v2 import group_folds

BASELINES = ('context', 'default_profile', 'domain_profile', 'conditional_profile')
PENALTIES = (0.1, 1.0, 10.0, 100.0)


def raw_blocks(frame):
    rows = frame.to_dict('records')
    conditions = ['|'.join(str(row[k]) for k in ('progress', 'affect')) for row in rows]
    return [
        [{'domain_state': str(r['domain'])+'|'+c} for r,c in zip(rows,conditions)],
        [{'model': str(r['model'])} for r in rows],
        [{'model_domain': str(r['model'])+'|'+str(r['domain'])} for r in rows],
        [{'model_state': str(r['model'])+'|'+c} for r,c in zip(rows,conditions)],
    ]


def weights_for(frame):
    weights = 1/frame.groupby('source_group').source_group.transform('size').to_numpy(float)
    return weights*len(weights)/weights.sum()


def design(train, test, baseline):
    if baseline not in BASELINES:
        raise ValueError('Unknown baseline')
    if set(train.source_group) & set(test.source_group):
        raise ValueError('Train/test source overlap')
    w = weights_for(train)
    x, z = np.ones((len(train), 1)), np.ones((len(test), 1))
    ranks = []
    for i,(a,b) in enumerate(zip(raw_blocks(train),raw_blocks(test))):
        if i > BASELINES.index(baseline):
            break
        vec = DictVectorizer(sparse=False)
        a = vec.fit_transform(a)
        b = vec.transform(b)
        # Earlier columns have weighted Gram matrix sum(w)*I. Residualization
        # removes duplicated main effects from each later categorical block.
        projection = (x.T@(w[:,None]*a))/w.sum()
        residual = a-x@projection
        residual_test = b-z@projection
        _, singular, vt = np.linalg.svd(np.sqrt(w[:,None])*residual, full_matrices=False)
        keep = singular > max(1e-9, (singular[0] if len(singular) else 0)*1e-9)
        transform = vt[keep].T*(np.sqrt(w.sum())/singular[keep])
        x = np.column_stack([x,residual@transform])
        z = np.column_stack([z,residual_test@transform])
        ranks.append(int(keep.sum()))
    return x,z,w,ranks


def fit_predict(train, test, baseline, penalty=1.0):
    if not len(train) or not len(test):
        raise ValueError('Empty train or test')
    x,z,w,ranks = design(train,test,baseline)
    y = train.present.to_numpy(float)
    if not np.isfinite(y).all() or (y<0).any() or (y>1).any():
        raise ValueError('Labels must lie in [0, 1]')
    if np.ptp(y) == 0:
        p = (np.sum(w*y)+.5)/(w.sum()+1)
        return np.full(len(test),p), {'constant_training_label':float(y[0]),'converged':True,'block_ranks':ranks}
    start = np.zeros(x.shape[1])
    rate = np.average(y,weights=w)
    start[0] = np.log(rate/(1-rate))
    def objective(beta):
        eta = x@beta
        loss = np.sum(w*(np.logaddexp(0,eta)-y*eta))+.5*penalty*np.sum(beta[1:]**2)
        gradient = x.T@(w*(expit(eta)-y))
        gradient[1:] += penalty*beta[1:]
        return loss,gradient
    fit = minimize(objective,start,jac=True,method='L-BFGS-B',options={'maxiter':2000,'ftol':1e-12,'gtol':1e-8})
    if not fit.success:
        def hessian(beta):
            p=expit(x@beta)
            h=x.T@((w*p*(1-p))[:,None]*x)
            h[1:,1:]+=penalty*np.eye(x.shape[1]-1)
            return h
        fit=minimize(objective,fit.x,jac=True,hess=hessian,method='trust-exact',
                     options={'maxiter':1000,'gtol':1e-7})
    gradient_inf=float(np.max(np.abs(objective(fit.x)[1])))
    if not fit.success and gradient_inf>1e-6:
        raise ValueError(f'Prediction fit did not converge: {fit.message}; gradient={gradient_inf}')
    return expit(z@fit.x), {'constant_training_label':None,'converged':True,
                           'gradient_inf':gradient_inf,'block_ranks':ranks}


def select_penalty(train, baseline):
    if train.source_group.nunique()<3:
        return 1.0, {'selection':'insufficient training groups; fixed penalty', 'scores':{}}
    folds = group_folds(train.source_group,3)
    scores = {}
    for penalty in PENALTIES:
        losses = []
        for fold in sorted(set(folds)):
            fit,validation = train[folds!=fold],train[folds==fold]
            p,_ = fit_predict(fit,validation,baseline,penalty)
            losses.extend(zip(validation.source_group,(p-validation.present.to_numpy())**2))
        scores[penalty] = float(pd.DataFrame(losses,columns=['source','loss']).groupby('source').loss.mean().mean())
    # Prefer stronger regularization for numerical ties, without looking at test labels.
    best = min(scores.values())
    selected = max(p for p,s in scores.items() if s <= best+1e-10)
    return selected, {'selection':'three source-fold training-only Brier CV','scores':scores}


def evaluate(frame,n_splits=5):
    if frame.duplicated(['blind_id','event']).any():
        raise ValueError('Duplicate item/event labels')
    records, tuning = [],[]
    for event,data in frame.groupby('event'):
        fold_ids = group_folds(data.source_group,n_splits)
        for fold in sorted(set(fold_ids)):
            train,test = data[fold_ids!=fold],data[fold_ids==fold]
            for baseline in BASELINES:
                penalty,selection = select_penalty(train,baseline)
                prediction,info = fit_predict(train,test,baseline,penalty)
                tuning.append({'event':event,'fold':int(fold),'baseline':baseline,'penalty':penalty,**selection,**info})
                for row,p in zip(test.to_dict('records'),prediction):
                    records.append({'event':event,'fold':int(fold),'baseline':baseline,'penalty':penalty,
                                    'blind_id':row['blind_id'],'source_group':row['source_group'],
                                    'model':row['model'],'observed':row['present'],'predicted':float(p),
                                    'brier':float((p-row['present'])**2)})
    return pd.DataFrame(records),tuning


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--consensus',type=Path,required=True)
    ap.add_argument('--mapping',type=Path,required=True)
    ap.add_argument('--deployment-audit',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args()
    frame=pd.read_csv(args.consensus)
    mapping=[json.loads(s) for s in args.mapping.read_text().splitlines() if s.strip()]
    metadata=pd.DataFrame([{'blind_id':r['blind_id'],'domain':r['domain'],'source_group':r.get('source_family',r['template'])} for r in mapping])
    frame=frame.merge(metadata,on='blind_id',validate='many_to_one')
    audit=json.loads(args.deployment_audit.read_text())
    if audit['status']!='pass' or any(len(v)!=1 for v in audit['requested_to_returned'].values()):
        raise ValueError('Unverified deployment panel')
    frame['model']=frame.model.map({k:v[0] for k,v in audit['requested_to_returned'].items()})
    if frame.model.isna().any():
        raise ValueError('Unknown deployment')
    result,tuning=evaluate(frame)
    args.output.mkdir(parents=True,exist_ok=True)
    result.to_csv(args.output/'predictions.csv',index=False)
    losses=result.groupby(['event','baseline','source_group']).brier.mean().reset_index()
    losses.to_csv(args.output/'source_losses.csv',index=False)
    summary=losses.groupby(['event','baseline']).brier.mean().unstack('baseline')
    summary['default_gain_absolute']=summary.context-summary.default_profile
    summary['domain_gain_absolute']=summary.default_profile-summary.domain_profile
    summary['student_state_gain_absolute']=summary.domain_profile-summary.conditional_profile
    summary.to_csv(args.output/'prediction_summary.csv')
    (args.output/'fit_diagnostics.json').write_text(json.dumps(tuning,indent=2)+'\n')
    (args.output/'provenance.json').write_text(json.dumps({
        'status':'development source CV; not prospective confirmation',
        'source_groups':int(frame.source_group.nunique()),'penalty_grid':PENALTIES,
        'inputs':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (args.consensus,args.mapping,args.deployment_audit,Path(__file__))},
        'features':'domain x student state; model main; model x domain; model x student state, in nested order',
        'limitations':['Pilot has four source templates and domain is confounded with template.',
                       'Small-fold model selection is unstable; no inferential thresholds are asserted.',
                       'L2 does not eliminate finite-sample interaction overfitting; assess held-out loss.',
                       'No held-out labels or response-derived features enter the predictor.']
    },indent=2)+'\n')
    print(summary.to_string())

if __name__=='__main__':
    main()
