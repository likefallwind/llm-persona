"""Training-only length/structure profiles as a competing behavioral forecast.

No confirmation text is used. This is a competing description, not causal
adjustment: teaching policy can itself influence length and formatting.
"""
import re
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import expit
import predict_personality_events_v3 as primary

STYLE_COLUMNS=['raw_log_words','raw_structure']


def extract_style(text):
    lines=[s for s in text.splitlines() if s.strip()]
    marked=sum(bool(re.match(r'^\s*(?:#{1,6}\s|[-*+]\s|\d+[.)]\s)',s)) for s in lines)
    return {'raw_log_words':float(np.log1p(len(re.findall(r'\S+',text)))),
            'raw_structure':marked/max(1,len(lines))}


def style_design(train,test):
    x,z,w,_=primary.design(train,test,'context')
    # Every source contributes equally to each generator's profile. All
    # validation/confirmation answers are excluded from profile estimation.
    profiles=train.groupby(['model','source_group'])[STYLE_COLUMNS].mean().groupby('model').mean()
    if set(test.model)-set(profiles.index): raise ValueError('Unknown generator in style forecast')
    a=profiles.loc[train.model].to_numpy()
    b=profiles.loc[test.model].to_numpy()
    projection=x.T@(w[:,None]*a)/w.sum()
    residual=a-x@projection
    residual_test=b-z@projection
    _,s,vt=np.linalg.svd(np.sqrt(w[:,None])*residual,full_matrices=False)
    keep=s>max(1e-9,(s[0] if len(s) else 0)*1e-9)
    transform=vt[keep].T*(np.sqrt(w.sum())/s[keep])
    return np.column_stack([x,residual@transform]),np.column_stack([z,residual_test@transform]),w,profiles


def fit_predict(train,test,penalty):
    x,z,w,profiles=style_design(train,test)
    y=train.present.to_numpy(float)
    model={'penalty':penalty,'profiles':profiles.to_dict('index'),'style_columns':STYLE_COLUMNS}
    if np.ptp(y)==0:
        p=float((np.sum(w*y)+.5)/(w.sum()+1))
        return np.full(len(test),p),{**model,'constant_probability':p,'coefficients':None}
    start=np.zeros(x.shape[1])
    rate=np.average(y,weights=w)
    start[0]=np.log(rate/(1-rate))
    def objective(beta):
        eta=x@beta
        loss=np.sum(w*(np.logaddexp(0,eta)-y*eta))+.5*penalty*np.sum(beta[1:]**2)
        gradient=x.T@(w*(expit(eta)-y))
        gradient[1:]+=penalty*beta[1:]
        return loss,gradient
    def hessian(beta):
        p=expit(x@beta)
        h=x.T@((w*p*(1-p))[:,None]*x)
        h[1:,1:]+=penalty*np.eye(x.shape[1]-1)
        return h
    fitted=minimize(objective,start,jac=True,method='L-BFGS-B',options={'maxiter':2000,'ftol':1e-12,'gtol':1e-8})
    if not fitted.success:
        fitted=minimize(objective,fitted.x,jac=True,hess=hessian,method='trust-exact',options={'maxiter':1000,'gtol':1e-7})
    gradient=float(np.max(np.abs(objective(fitted.x)[1])))
    if not fitted.success and gradient>1e-6: raise ValueError('Style fit did not converge')
    return expit(z@fitted.x),{**model,'constant_probability':None,'coefficients':fitted.x.tolist(),'gradient_inf':gradient}


def select_penalty(train):
    folds=primary.group_folds(train.source_group,3)
    scores={}
    for penalty in primary.PENALTIES:
        losses=[]
        for fold in sorted(set(folds)):
            a,b=train[folds!=fold],train[folds==fold]
            p,_=fit_predict(a,b,penalty)
            losses.extend(zip(b.source_group,(p-b.present.to_numpy())**2))
        scores[penalty]=float(pd.DataFrame(losses,columns=['source','loss']).groupby('source').loss.mean().mean())
    best=min(scores.values())
    return max(p for p,s in scores.items() if s<=best+1e-10),scores
