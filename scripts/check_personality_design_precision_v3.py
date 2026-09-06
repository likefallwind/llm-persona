#!/usr/bin/env python3
"""Synthetic precision/coverage diagnostics; never read tutor responses or labels."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import brentq
from scipy.stats import binomtest, nct, t

from analyze_personality_confirmation_v3 import paired_stats
from prepare_personality_pilot_v2 import write_frozen
from run_personality_formal_stage_v3 import ROOT, BASE, validate_stage

SEED=20260905
TRIALS=100000
SOURCES=16
STATES=4
REPEATS=2
FAMILY=30
MARGIN=.10
ALPHA=.05/FAMILY


def intervals(differences):
    values=np.asarray(differences,float)
    if values.ndim!=2 or values.shape[1]!=SOURCES or not np.isfinite(values).all():
        raise ValueError('Expected finite simulation rows with sixteen sources')
    mean=values.mean(axis=1)
    se=values.std(axis=1,ddof=1)/np.sqrt(SOURCES)
    half=t.ppf(1-ALPHA/2,SOURCES-1)*se
    return mean,se,mean-half,mean+half


def rate_summary(flag):
    count=int(np.asarray(flag).sum())
    ci=binomtest(count,len(flag)).proportion_ci(confidence_level=.95,method='exact')
    return float(count/len(flag)),float(ci.low),float(ci.high)


def simulate(name,p,q,trials=TRIALS):
    p,q=np.asarray(p,float),np.asarray(q,float)
    if p.shape!=(STATES,) or q.shape!=(STATES,) or np.any(p<0) or np.any(p>1) or np.any(q<0) or np.any(q>1):
        raise ValueError('Four valid probabilities required in each role arm')
    key=int(hashlib.sha256(name.encode()).hexdigest()[:8],16)
    rng=np.random.default_rng(np.random.SeedSequence([SEED,key]))
    shape=(trials,SOURCES,STATES)
    canonical=rng.binomial(REPEATS,p,size=shape).sum(axis=-1)/(STATES*REPEATS)
    alternative=rng.binomial(REPEATS,q,size=shape).sum(axis=-1)/(STATES*REPEATS)
    differences=alternative-canonical
    mean,se,low,high=intervals(differences)
    delta=float((q-p).mean())
    numeric=(low>-MARGIN)&(high<MARGIN)
    guarded=numeric&(se>1e-12)
    support,mc_low,mc_high=rate_summary(guarded)
    expected_variance=float(np.sum(p*(1-p)+q*(1-q))/(REPEATS*STATES**2))
    observed_variance=float(differences.var())
    if not np.isclose(observed_variance,expected_variance,rtol=.02,atol=1e-12):
        raise ValueError('Simulation variance does not recover the specified Bernoulli model')
    # Check the vectorized interval against the unchanged production routine.
    for i in range(min(20,trials)):
        frozen=paired_stats(differences[i],alpha=ALPHA,bootstrap=2)
        np.testing.assert_allclose([low[i],high[i]],[frozen['t_interval_low'],frozen['t_interval_high']],rtol=0,atol=1e-14)
    return {'scenario':name,'canonical_state_probabilities':json.dumps(p.tolist()),
            'alternative_state_probabilities':json.dumps(q.tolist()),'true_mean_difference':delta,
            'canonical_mean_probability':float(p.mean()),'trials':trials,
            't_interval_noncoverage_rate':float(((low>delta)|(high<delta)).mean()),
            'numerical_equivalence_rate':float(numeric.mean()),'nondegenerate_equivalence_rate':support,
            'simulation_rate_mc_95_low':mc_low,'simulation_rate_mc_95_high':mc_high,
            'degenerate_source_interval_rate':float((se<=1e-12).mean()),
            'expected_source_variance':expected_variance,'simulated_source_variance':observed_variance}


def main():
    validate_stage('training')
    cases=[(f'no_shift_p{p:g}',[p]*4,[p]*4) for p in [0,.01,.05,.1,.25,.5]]
    cases += [('no_shift_strong_state_cues',[.05,.95,.05,.95],[.05,.95,.05,.95]),
              ('boundary_from_zero',[0]*4,[.1]*4),('boundary_to_zero',[.1]*4,[0]*4),
              ('boundary_interior_low',[.05]*4,[.15]*4),('boundary_interior_mid',[.4]*4,[.5]*4)]
    table=pd.DataFrame([simulate(*case) for case in cases])
    critical=float(t.ppf(1-.05/6,31))
    standardized=float(brentq(lambda d:nct.sf(critical,31,d*np.sqrt(32))-.8,0,2))
    rng=np.random.default_rng(SEED)
    gaussian=rng.normal(standardized,1,size=(TRIALS,32))
    gaussian_stat=gaussian.mean(axis=1)/(gaussian.std(axis=1,ddof=1)/np.sqrt(32))
    gaussian_power=float((gaussian_stat>critical).mean())
    if abs(gaussian_power-.8)>.005: raise ValueError('Gaussian simulation does not recover noncentral-t power')
    summary={'status':'synthetic design diagnostic; no empirical personality findings',
        'actual_responses_or_labels_used':0,'api_calls':0,'sample_size_changes':0,'primary_test_changes':0,
        'seed':SEED,'trials_per_scenario':TRIALS,'scenarios':len(cases),
        'neutral_sources':SOURCES,'states_per_source':STATES,'requests_per_state_per_arm':REPEATS,
        'neutral_comparison_family':FAMILY,'nominal_per_comparison_noncoverage':ALPHA,
        'neutral_t_critical':float(t.ppf(1-ALPHA/2,15)),
        'maximum_observed_source_sd_for_centered_tolerance':float(MARGIN*np.sqrt(SOURCES)/t.ppf(1-ALPHA/2,15)),
        'gaussian_standardized_effect_for_80_percent_power':standardized,
        'gaussian_monte_carlo_power':gaussian_power,
        'gaussian_scope':'Illustrative normal source differences and conservative first Holm threshold; not estimated power of the actual Brier comparisons.',
        'checks':['Simulated Bernoulli source variances match their analytic values.',
                  'Vectorized t intervals match the unchanged frozen calculation.',
                  'Gaussian simulation matches the noncentral-t calculation.'],
        'limits':['The probability profiles are constructed examples, not fitted model profiles.',
                  'Per-comparison simulations do not estimate familywise error for the actual dependent events.',
                  'Simulation-rate intervals describe Monte Carlo uncertainty, not educational-population uncertainty.'],
        'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    out=BASE/'design_precision'
    write_frozen(out/'synthetic_neutral_precision.csv',table.to_csv(index=False))
    write_frozen(out/'summary.json',json.dumps(summary,indent=2)+'\n')
    print(table[['scenario','true_mean_difference','nondegenerate_equivalence_rate','t_interval_noncoverage_rate']].to_string(index=False))
    print(json.dumps({k:summary[k] for k in ['neutral_t_critical','maximum_observed_source_sd_for_centered_tolerance','gaussian_standardized_effect_for_80_percent_power','gaussian_monte_carlo_power']}))


if __name__=='__main__':
    main()
