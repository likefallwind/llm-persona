# Prompt-contingent pedagogical policy signatures: results

Snapshot: 2026-08-26. This is an outcome-aware secondary analysis of already
frozen outputs, not a preregistration. The executable protocol and decision gates
are in `research/31_prompt_contingent_policy_signature_protocol.md`; machine-readable
results are in `artifacts/prompt_contingent_signatures_v1/`.

## Research question

The useful version of “different models have different educational personalities”
is not whether a model has a human-like latent trait. It is whether educational
behavior can be decomposed into:

1. a model-conditioned default policy;
2. a shared causal displacement under the same high-priority pedagogy prompt; and
3. model-specific prompt elasticity that survives task transfer and the most
   direct floor/ceiling explanation.

## Decision

Verdict: `prompt_contingent_policy_signatures_supported`.

All six prespecified secondary-analysis gates pass. The retained construct is a
**prompt-contingent policy response surface**, not fixed model personality.

## Main evidence

The analysis contains 11,424 paired semantic rows from six frozen deployed-model
configurations, two MathDial task variants, two prompt arms, and eight semantic
dimensions. Three dimensions are reliable in the frozen panel: cognitive load,
elicitation, and help directness.

### The prompt is usually larger than the default model contrast

For the three reliable dimensions, exact-context prompt/model sums-of-squares
ratios are 3.987--7.532 in standard and 4.837--6.685 in hard contexts. Mean
prompt movement is 0.848--1.148 times the generic-arm cross-model range. In
particular:

| Dimension | Standard prompt change / default range | Hard prompt change / default range |
|---|---:|---:|
| Cognitive load | 1.111 | 0.848 |
| Elicitation | 1.148 | 0.987 |
| Help directness | 1.000 | 1.011 |

This supports the user's intuition that prompt wording strongly conditions the
visible teaching style. It also rejects a universal effect: warmth and
personalization have small prompt main effects in these arms.

### Prompting does not erase model identity

Training a semantic model-identity classifier on one prompt arm and testing on
the other gives 0.301 accuracy for generic-to-pedagogy and 0.297 for the reverse,
versus 0.167 chance. The respective bootstrap intervals are [0.264, 0.335] and
[0.266, 0.326]. All four harder cross-task/cross-prompt transfer directions also
have lower confidence limits above chance; accuracies range from 0.263 to 0.300.

Therefore, the prompt produces a large common displacement but does not collapse
all models onto one response geometry.

### Models differ in how they respond to the prompt

Raw model-by-prompt heterogeneity is widespread. Because a bounded 1--5 score can
create artificial elasticity differences when a model starts near a floor or
ceiling, the sensitivity analysis divides movement by the available directional
headroom and retains only contexts where all six models have nonzero headroom.
After this adjustment, model-specific elasticity replicates in both task variants
for:

- elicitation (BH q = 0.0003 standard; 0.0016 hard), and
- help directness (BH q = 0.0003 standard; 0.0155 hard).

Cognitive-load heterogeneity does not replicate after this stricter adjustment.
Model ordering is also not fixed: help-directness ranks reverse for 33.3% of
model pairs in standard and 42.9% in hard contexts.

## What the model differences look like

On the headroom-adjusted scale, the fixed aliases differ meaningfully in prompt
responsiveness. For elicitation, Doubao-Seed-2.0-Pro shows the largest mean
elasticity (0.982 standard, 0.908 hard), while Qwen3.5-4B is lower (0.622, 0.461).
For help directness, Doubao again moves more (0.774, 0.632), whereas Qwen is lower
(0.346, 0.371); GLM-5.2 is especially low in hard contexts (0.226). MiniMax-M2.7
and MiniMax-M3 are intermediate, but not identical: M2.7/M3 are 0.762/0.787 on
standard elicitation and 0.829/0.518 on hard elicitation.

These are descriptive properties of fixed provider aliases under the archived
harness. They are not estimates of model-family traits or immutable weights.

## Relationship to prior work

- Gupta et al. (BlackboxNLP 2024) show that semantically equivalent prompts and
  option order can destabilize LLM personality-test scores. This supports moving
  away from self-report personality labels toward behavior under interventions.
- Kucheria et al. (BEA 2025) report systematic differences in actions and
  response complexity among three LLM tutors and human tutors. Our analysis adds
  cross-task recurrence, a shared same-context prompt intervention, generic-domain
  falsification, and model-specific elasticity.
- The August 2026 PSI study compares standard and defective student prompts and
  reports almost no aggregate PSI change despite subscore trade-offs. Our results
  likewise show why aggregate scores can conceal policy movement, while testing a
  different intervention level: an explicit system pedagogy instruction rather
  than a lower-priority learner utterance.

## Is further research worthwhile?

Yes, as a bounded extension, not as a new broad “LLM personality” program. It
materially strengthens the paper by explaining both apparent stability and strong
prompt dependence with one estimand. The next high-value study would cross
multiple semantically equivalent system prompts, learner requests, and task
contexts on a larger versioned model panel, then test whether elasticity predicts
action appropriateness or learner outcomes. Repeating more aliases with the same
single prompt would add less value.

No new provider calls were made for this result. The frozen data passed the
cross-task, cross-prompt, scale-headroom, and identity-transfer gates, so extra API
spend was not needed to answer the present question. New calls are justified only
for the stronger confirmatory extension above.

The full result is integrated into `paper/draft.md`. The archived ACL submission
TeX/PDF was deliberately left unchanged: rebuilding an untouched `HEAD` snapshot
with the pinned ACL style on this machine also produces 10 pages instead of the
already audited 9-page PDF, identifying a local TeX layout drift rather than a
research-content regression. The finalizer rebuilt this analysis, passed all 83
claim checks, and passed the frozen 9-page anonymous-package audit. It then failed
the existing public-privacy gate because this development checkout contains
Git-tracked private run files with response and raw-judge fields plus one absolute
home path. None is a new analysis output, and none was deleted or hidden. The run
is therefore a successful research/claim verification, not a clean full-release
pass.

## Claim boundary

The analysis supports observable, prompt-contingent tutor policies. It does not
establish human-like personality, empathy, learner-state understanding, teaching
quality, or learning gain. It cannot upgrade the frozen paper-level disposition
decision because it was designed after outcomes were available.
