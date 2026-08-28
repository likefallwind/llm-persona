# Targeted affiliation stability pilot: results

Snapshot: 2026-08-28. Status: **complete prospective targeted pilot**.

## Bottom line

The pilot separates three claims that had previously been conflated:

1. A stable default interpersonal behavior profile exists in the fixed panel.
2. Explicit affiliation prompts can move it strongly and with model-specific
   elasticity.
3. The profile does not converge with questionnaire and forced-choice measures
   well enough to be called a Big Five-like general personality trait.

The best-supported object is therefore a **prompt-contingent affiliation
behavior policy**: a locally stable default plus large, asymmetric prompt
displacement. This is narrower than human personality but broader than an
education-only style.

## Complete panel

All 280 generator calls and 144 blinded judge calls completed successfully. The
five generator configurations were MiniMax-M3, MiniMax-M2.7, GLM-5.2,
DeepSeek-V4-Pro, and Doubao-Seed-2.0-Lite. MiniMax-M3, GLM-5.2, and
DeepSeek-V4-Pro independently judged the open responses. No one-judge result
drives the model profile: leaving out any judge preserves the default profile at
rho=1.000.

## Frozen stability gates

All five preregistered gates pass:

| Requirement | Estimate | Gate | Result |
|---|---:|---:|---|
| Open-behavior ICC(3,k) | 0.931 | >=0.70 | pass |
| Default education/non-education rho | 0.900 | >=0.70 | pass |
| Default/irrelevant-context rho | 0.718 | >=0.70 | pass |
| Mean irrelevant displacement | -0.050 | abs <=0.25 | pass |
| Default between-model SD | 0.445 | >=0.15 | pass |

The education/non-education exact permutation p-value is 0.091 and the
default/irrelevant p-value is 0.174 because the fixed panel contains only five
models. The inference is therefore a gate-based fixed-panel result, not a
population-level trait estimate. The irrelevant-context rank result also only
narrowly clears its threshold and one model moves 0.278 points, so broader
irrelevant perturbations remain necessary for a stronger stability claim.

## Prompt displacement and residual identity

The high-minus-low affiliation effect is 1.689 points on the 1--5 scale and is
positive for all five models, passing both steerability gates. Model-specific
effects range from 0.444 to 2.917, directly demonstrating different elasticities.

The default profile is highly preserved under the high-affiliation condition
(rho=0.900) but not under the low-affiliation condition (rho=0.200). High
affiliation also compresses between-model SD from 0.445 to 0.201, whereas low
affiliation expands it to 0.879. Thus prompts do not merely translate every model
by the same amount: one direction creates a common ceiling, while the other
reveals sharply different resistance or compliance.

This directly refines the user's intuition. A default ordering can be stable and
remain recognizable after some prompts, but this does not make the policy
immutable. Model identity and prompt intervention jointly define the response.

## Self-report--behavior separation

General-trait convergence fails both frozen gates:

- default agreeableness self-reports range only from 4.2 to 4.9 and correlate
  -0.200 with open behavior;
- all five models choose the affiliative option on all twelve default
  forced-choice items, leaving zero between-model variance and an undefined
  behavior correlation.

The forced-choice ceiling is itself informative: socially obvious inventories
can report universal niceness while open conflicts still distinguish model
behavior. High/low prompts move both self-report and open responses, but shared
inducibility is not default-trait validity.

## Discriminant boundary

Default open affiliation correlates 0.900 with judged surface warmth and 0.800
with benevolent cost acceptance; it is unrelated to assertive dominance
(rho=-0.051) and moderately related to task effectiveness (rho=0.600). The
primary score therefore contains more than simple dominance, but its model
ordering cannot yet be separated cleanly from warm expression. This post-hoc
control result prevents us from promoting it to a distinctive latent trait.

## Integrated conclusion

The archive-plus-pilot evidence now supports:

> Model configurations can have stable default affiliation behavior across
> educational and non-educational conflicts, but that behavior is strongly
> prompt-contingent and does not converge with questionnaire or forced-choice
> personality measures.

It does not support “models have Big Five personalities.” It also rejects the
stronger null that all apparent character is merely random task noise. The
paper's central response-surface framing—default policy, shared displacement,
and model-specific elasticity—extends beyond pedagogy for this one
interpersonal cluster.

No broad Dark Triad, Schwartz, or remaining Big Five experiment is triggered.
The next scientifically useful step, if this becomes a main paper claim, is a
larger independent model panel and more varied irrelevant perturbations, plus an
open behavioral task whose affiliation endpoint is less coupled to warmth.

## Reproducibility

Frozen design: `data/affiliation_stability_pilot_spec_v1.json`. Aggregate
decision: `artifacts/affiliation_stability_pilot_v1/analysis/decision.json`.
Raw provider responses and judge payloads remain local; released tables contain
scores, hashes, conditions, and aggregate profiles only.
