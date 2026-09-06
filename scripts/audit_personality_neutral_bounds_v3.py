#!/usr/bin/env python3
"""Add bounded-source intervals; retain frozen nominal t outputs separately."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from audit_personality_inference_edges_v3 import neutral_interpretation
from run_personality_formal_stage_v3 import BASE, ROOT, validate_stage, verify_files
from run_personality_requests_v2 import read_rows


def bounded_interpretation(effects):
    data=neutral_interpretation(effects)
    if not np.isfinite(data.mean_difference).all() or not data.mean_difference.between(-1,1).all():
        raise ValueError('Event-probability differences must be in [-1,1]')
    # For X in [-1,1], Hoeffding gives two-sided noncoverage <=
    # 2 exp(-n*h^2/2). Allocate .05/30 to each comparison via the union bound.
    half=np.sqrt(2*np.log(2*30/.05)/data.sources)
    data['bounded_source_half_width']=half
    data['bounded_source_95_low']=(data.mean_difference-half).clip(lower=-1)
    data['bounded_source_95_high']=(data.mean_difference+half).clip(upper=1)
    data['nondegenerate_t_equivalence_flag']=data.equivalence_support_for_narrative
    data['bounded_source_equivalence_support']=(data.bounded_source_95_low.gt(-.10)&data.bounded_source_95_high.lt(.10))
    data['equivalence_support_for_narrative']=(data.nondegenerate_t_equivalence_flag&data.bounded_source_equivalence_support)
    data['interpretation_note']='Nominal paired-t output retained. Population equivalence requires the bounded-source check as well; small observed shifts alone are descriptive.'
    return data


def main():
    validate_stage('confirmation')
    policy_path=BASE/'neutral_bounds_policy.json'
    policy=json.loads(policy_path.read_text());verify_files(policy['files'])
    first=min(r['started_at'] for r in read_rows(BASE/'confirmation/run/responses.jsonl'))
    if policy['fixed_at']>=first: raise ValueError('Bounded interpretation was not fixed before confirmation')
    effects_path=BASE/'confirmation_analysis/paired_prompt_effects.csv'
    frame=bounded_interpretation(pd.read_csv(effects_path))
    out=BASE/'confirmation_neutral_bounds';out.mkdir(exist_ok=True)
    target=out/'neutral_equivalence_interpretation.csv';frame.to_csv(target,index=False)
    report={'status':'bounded-source neutral sensitivity complete; frozen numerical results retained',
        'comparisons':30,'sources_per_comparison':16,'simultaneous_nominal_level':.95,
        'bounded_source_half_width':float(frame.bounded_source_half_width.iloc[0]),
        'nondegenerate_t_flags':int(frame.nondegenerate_t_equivalence_flag.sum()),
        'bounded_equivalence_flags':int(frame.bounded_source_equivalence_support.sum()),
        'narrative_equivalence_flags':int(frame.equivalence_support_for_narrative.sum()),
        'primary_prediction_tests_changed':0,'new_api_calls':0,
        'assumption':'Independent bounded source-level differences under the source-sampling approximation; no normality assumption. Authored sources are not a representative probability sample.',
        'limitation':'The bound is deliberately conservative. Failure to support equivalence is not evidence of a prompt effect.',
        'effects_sha256':hashlib.sha256(effects_path.read_bytes()).hexdigest(),
        'policy_sha256':hashlib.sha256(policy_path.read_bytes()).hexdigest(),
        'table_sha256':hashlib.sha256(target.read_bytes()).hexdigest()}
    (out/'summary.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
