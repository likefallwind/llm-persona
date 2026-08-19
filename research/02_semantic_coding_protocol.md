# Frozen semantic-coding protocol (v1)

Frozen before any semantic-judge results were inspected.

## Purpose

The deterministic pilot establishes that model-specific signatures exist, but
lexical proxies cannot establish a pedagogical construct.  This confirmatory
stage uses three distinct agent judges to code behavior on a deterministic,
paired sample.  No new human annotation is introduced.

## Sampling

Seed: `20260819`.

- LongTutor teaching: 40 contexts.
- MathDial standard: 80 contexts, each observed under both the generic caring
  teacher prompt and the explicit LearnLM-style pedagogy prompt.
- MathDial hard: 40 contexts, again under both prompts.
- Socratic question generation: 80 contexts.

Within every selected context, all six core-model responses are included.  Items
are selected by sorting a SHA-256 hash of `(seed, task family, item id)`, not by
their content or outcomes.  Candidate model names are hidden and candidate order
is independently randomized for each item and judge.

The first two contexts per family are a parser/API smoke test and are excluded
from confirmatory estimates if their prompt or parser changes afterward.

## Judges

- MiniMax-M3 (official MiniMax endpoint, concurrency <= 4)
- GLM-5.2 (API gateway, concurrency <= 8)
- DeepSeek-V4-Pro (API gateway, concurrency <= 8)

No single judge is treated as ground truth.  Primary scores are the per-response
median across valid judges.  Agreement and judge-specific effects are mandatory
results.  Because each judge is also one of the candidate model identities, the
analysis tests self-family preference explicitly despite blinding.

The three judges are not methodologically independent merely because their model
names differ.  Shared alignment and LLM-judge variance remain a construct threat;
agreement is evidence of judge-model robustness only.  Deterministic behavioral
criteria and the existing exact-item outcome analysis provide separate methods.

## Bipolar behavior dimensions

All dimensions are descriptive rather than “higher is better.”

1. `help_directness`: hint/question only (1) to full solution/answer (5).
2. `elicitation`: tutor exposition (1) to learner reasoning elicitation (5).
3. `autonomy_support`: fixed/directive path (1) to choice and self-monitoring (5).
4. `affective_warmth`: neutral/transactional (1) to strongly warm/encouraging (5).
5. `diagnostic_specificity`: generic/no diagnosis (1) to specific committed
   diagnosis of the learner state or error (5).
6. `personalization`: generic response (1) to specific use of learner history or
   context (5).
7. `cognitive_load`: one manageable next step (1) to many simultaneous steps or
   dense information (5).
8. `epistemic_caution`: unqualified certainty (1) to explicit calibrated
   uncertainty/need for more information (5).

Judges are told not to reward desirable behavior and not to score correctness.
Quality remains a separate external criterion from existing benchmark outputs.

## Confirmatory tests

1. Ordinal inter-judge agreement and pairwise rank agreement for every dimension.
2. Model variance after item and task-arm control; cluster/bootstrap uncertainty
   is computed at the item level, never at the individual response level alone.
3. Leave-task-family-out prediction from semantic dimensions, compared with
   length-only and lexical-policy baselines.
4. Within-model, within-item prompt effects with multiplicity correction and
   model-by-intervention heterogeneity.
5. Associations with existing quality outcomes after controlling for model,
   task, and response length.
6. Judge self-preference sensitivity, single-judge leave-out analysis, and
   response-order checks.

No dimension will be called a disposition unless it shows cross-task stability,
held-out predictive validity, and nontrivial intervention behavior.
