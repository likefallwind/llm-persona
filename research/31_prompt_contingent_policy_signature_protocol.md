# Prompt-contingent pedagogical policy signature audit

Date frozen: 2026-08-26. Status: **outcome-aware secondary analysis of frozen
outputs**.

## Research question

The audit asks whether apparent educational "personality" is better represented
as a prompt-contingent policy response surface with three separable components:

1. a model-conditioned default on shared educational contexts;
2. a common causal displacement under the same system-level pedagogy prompt; and
3. a model-specific prompt response, or policy elasticity.

This is not a preregistration. The paired semantic outcomes, factorial results,
and nine-model convergence result were inspected before this protocol was
written. The analysis can organize and challenge the existing conclusion, but
cannot promote a failed dimension or create a new confirmatory disposition.

## Inputs and fixed panel

- `artifacts/semantic_panel/centered_response_scores.csv`: blinded three-judge
  response consensus for the six-model core panel. The audit uses only the exact-
  context generic/pedagogy pairs from MathDial standard and hard.
- `artifacts/submission_decision/dimension_decisions.csv`: frozen reliability,
  stability, validity, and disposition decisions. They remain authoritative.
- `artifacts/extended_analysis/prompt_convergence.csv`: the separately derived
  nine-model cross-profile dispersion ratio and context bootstrap interval.
- The prospective parent, order, and paraphrase factorial reports remain
  independent evidence about operational action control and wording transport;
  this audit does not relabel their literal tone marker as semantic warmth.

The deployed aliases form a fixed convenience panel. No model-family,
model-population, immutable-weight, or provider-intent inference is allowed.

## Analyses

### A. Default policy profile

For each task, model, and semantic dimension, report the generic-arm mean and the
mean after exact-item centering. Do not interpret dimensions that failed frozen
gates as validated traits.

### B. Shared prompt displacement versus model spread

For each task and dimension, compare the mean paired pedagogy-minus-generic
movement with the full generic-arm range across models. A ratio at or above 0.75
is treated as movement comparable in scale to the observed default model spread.
This threshold is an interpretive audit rule, not a confirmatory hypothesis.

Use a context-cluster bootstrap for prompt movement, model range, and their
ratio. A shared prompt effect is called directionally stable only when its 95%
interval excludes zero in the same direction in standard and hard.

### C. Balanced variance decomposition

Within each task and dimension, decompose the balanced response scores into
exact-context, model, prompt, model-by-prompt, and residual sums of squares.
Report total and partial eta squared descriptively. Provider aliases are fixed,
so these quantities do not estimate ecosystem-level variance.

### D. Model-specific policy elasticity

Compute the paired prompt delta for every context and model. Test heterogeneity
with the standard deviation of model mean deltas. The randomization null shuffles
model labels independently inside every paired context. Apply Benjamini-Hochberg
correction across the eight dimensions within each task. "Replicated semantic
elasticity" requires adjusted `q < 0.05` in both standard and hard for a dimension
that passed the frozen reliable-measurement gate.

Because semantic scores are bounded from 1 to 5, the decision uses a conservative
floor/ceiling sensitivity analysis. For a positive pooled effect, divide each
paired movement by `5 - generic`; for a negative effect, divide it by
`generic - 1`. Omit a context from this sensitivity only when any model has zero
directional headroom, preserving a complete within-context panel for permutation.
The unadjusted interaction remains descriptive; the replicated-elasticity gate
must pass after this headroom adjustment.

### E. Rank stability and residual model identity

- Report exact six-model Spearman tests and pairwise rank reversals between the
  generic and pedagogy arms.
- Train multinomial model attribution on the eight item-centered semantic scores
  under one prompt arm and test on the other arm. Report pooled, same-task, and
  cross-task transfers. Bootstrap test contexts as clusters. Residual identity is
  supported only if both pooled transfer directions and all four cross-task,
  cross-prompt directions have a 95% lower bound above the six-model chance level.

Above-chance attribution is a behavioral fingerprint test, not a disposition
criterion.

## Interpretive decision

The synthesis `prompt_contingent_policy_signatures_supported` requires all of:

1. at least two dimensions already passed the frozen cross-task signature gate;
2. the nine-model prompt-dispersion interval is wholly below 1;
3. at least two reliably measured dimensions shift in the same direction with
   intervals excluding zero in both paired tasks;
4. at least two reliable dimensions move by at least 0.75 of the default model
   range in both tasks;
5. pooled and cross-task model attribution transfer above chance in both prompt
   directions;
6. at least one reliable dimension has replicated model-specific semantic
   elasticity after floor/ceiling adjustment.

If only item 6 fails, conclude that stable defaults and strong shared prompt
deformation are supported, but that dimension-level model-specific elasticity
did not replicate. Any other failure rejects the full synthesis.

## Mandatory boundaries

- The word "personality" may appear only as an intuitive label or a rejected
  human-trait interpretation. The measured object is a pedagogical policy
  signature.
- System-level policy control is not ordinary learner-request responsiveness.
- Instruction compliance is not context-appropriate action selection. The
  existing `telling` harm and selection-execution gap remain central falsifiers.
- No result establishes empathy, learner-state understanding, educational
  effectiveness, or student learning gain.
- New API calls are justified only if this frozen-data audit leaves a decisive
  evidential gap that cannot be answered by the completed order and wording
  replications.

## Reproduction

```bash
.venv/bin/python scripts/analyze_prompt_contingent_signatures.py \
  --bootstrap-reps 5000 \
  --attribution-bootstrap-reps 2000
```
