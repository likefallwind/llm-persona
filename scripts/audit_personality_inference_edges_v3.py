#!/usr/bin/env python3
"""Flag degenerate source intervals without altering frozen primary calculations."""
import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

from run_personality_formal_stage_v3 import BASE


def neutral_interpretation(effects):
    neutral = effects[effects.arm.isin(['neutral_a', 'neutral_b'])].copy()
    if len(neutral) != 30 or neutral.duplicated(['model', 'event', 'arm']).any():
        raise ValueError('Expected thirty unique neutral comparisons')
    if not neutral.sources.eq(16).all():
        raise ValueError('Expected sixteen sources per neutral comparison')
    # A constant discrete sample can collapse the paired-t/bootstrap interval.
    # Preserve the predeclared numerical output, but do not interpret that
    # collapse as evidence that an unseen source has no possible displacement.
    neutral['degenerate_source_interval'] = neutral.source_standard_error.abs().le(1e-12)
    neutral['frozen_numerical_equivalence_flag'] = neutral.supports_neutral_equivalence
    if not neutral.supports_neutral_equivalence.isin([True, False]).all():
        raise ValueError('Equivalence flags must be parsed booleans')
    neutral['equivalence_support_for_narrative'] = (
        neutral.supports_neutral_equivalence & ~neutral.degenerate_source_interval)
    neutral['interpretation_note'] = neutral.degenerate_source_interval.map({
        True: 'Constant observed source differences; the zero-width interval cannot establish population equivalence.',
        False: 'Paired-t source approximation; the interval tolerance is +/-0.10, not exact equality.'})
    return neutral


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--effects', type=Path, default=BASE / 'confirmation_analysis/paired_prompt_effects.csv')
    ap.add_argument('--output', type=Path, default=BASE / 'confirmation_inference_edges')
    args = ap.parse_args()
    policy_path = BASE / 'inference_edge_policy.json'
    policy = json.loads(policy_path.read_text())
    if policy['script_sha256'] != hashlib.sha256(Path(__file__).read_bytes()).hexdigest():
        raise ValueError('Inference interpretation differs from its recorded version')
    first = min(json.loads(line)['started_at'] for line in (BASE / 'confirmation/run/responses.jsonl').open() if line.strip())
    if policy['fixed_at'] >= first:
        raise ValueError('Interpretation rule does not precede confirmation generation')
    data = neutral_interpretation(pd.read_csv(args.effects))
    args.output.mkdir(parents=True, exist_ok=True)
    data.to_csv(args.output / 'neutral_equivalence_interpretation.csv', index=False)
    summary = {'status': 'degenerate-interval interpretation audit complete; frozen calculations retained',
               'degenerate_neutral_comparisons': int(data.degenerate_source_interval.sum()),
               'numerical_flags_withheld_from_equivalence_claim': int((data.frozen_numerical_equivalence_flag & data.degenerate_source_interval).sum()),
               'effects_sha256': hashlib.sha256(args.effects.read_bytes()).hexdigest(),
               'policy_sha256': hashlib.sha256(policy_path.read_bytes()).hexdigest(),
               'new_hypothesis_tests': 0,
               'limitation': 'Nondegenerate intervals still rely on source-sampling and paired-t approximations.'}
    (args.output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')


if __name__ == '__main__':
    main()
