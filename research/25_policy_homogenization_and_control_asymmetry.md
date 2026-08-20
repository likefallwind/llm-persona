# Policy homogenization, learner agency, and prospective confirmation

Date frozen locally: 2026-08-20.  This note separates two discoveries made in
already observed responses from the prospective experiment intended to test one
mechanism.  It is deliberately stricter than the manuscript narrative.

## Strongest current discovery: average gain can hide adaptive-policy collapse

The most defensible new finding is not merely that model systems have different
styles.  It is that a shared, ostensibly pedagogical prompt can simultaneously:

1. improve average agreement with the human teacher's next action;
2. make nine model systems choose more similar action types; and
3. systematically suppress direct `telling` exactly where a human teacher chose
   `telling`.

This uses the existing paired MathDial-derived intervention panel, the original
human teacher action, and three conventional TF--IDF/linear-SVM variants trained
on 18,541 human-labelled teacher turns.  Generated response text is not judged
by an LLM in this analysis.  Context, model, and response are identical across
the three classifier variants.

For the 1,004 standard contexts and nine models, the pedagogy arm improves
aggregate action match by 0.091--0.114 across the three classifier variants
(context-clustered 95% intervals exclude zero for every variant).  The aggregate
hides a sign reversal:

- on 410 human-`probing` contexts, match increases by 0.144--0.206; every one of
  the nine models is positive under every classifier variant;
- on 48 human-`telling` contexts, match decreases by 0.282--0.317; every one of
  the nine models is negative under every classifier variant; and
- the context-clustered 95% interval is wholly positive for every probing
  estimate and wholly negative for every telling estimate.

At the same time, normalized cross-model action entropy decreases in all six
classifier-by-difficulty analyses by 0.035--0.048, with all six upper confidence
bounds below zero.  This is evidence of policy homogenization, not evidence that
homogenization itself caused the telling failure.

The exact artifacts are:

- `artifacts/policy_homogenization_v1/overall_prompt_effects.csv`;
- `artifacts/policy_homogenization_v1/target_action_effects.csv`;
- `artifacts/policy_homogenization_v1/target_action_model_effects.csv`;
- `artifacts/policy_homogenization_v1/target_action_sign_robustness.csv`;
- `artifacts/policy_homogenization_v1/consensus_prompt_effects.csv`; and
- `artifacts/policy_homogenization_v1/policy_homogenization_report.json`.

### What this does and does not show

This supports an **average-improvement / contextual-harm reversal** in a fixed
model panel.  It does not show a learning loss, establish that the observed human
move is uniquely optimal, or make nine convenience-sampled models a population.
Classifier variants are robustness analyses over the same responses, not three
independent replications.  The classifier's grouped-CV macro F1 of 0.559--0.571
also bounds how literally the action labels should be read.

The joint estimand combining average gain, target-specific harm, and cross-model
homogenization was specified after the response outcomes were inspected.  The
analysis is therefore explicitly post hoc even though the response panel and
human labels predate it.  A future prospective action-routing trial must confirm
the pattern before it becomes a confirmatory headline.

## Secondary mechanism clue: system--learner control asymmetry

The frozen 2x2x2 policy intervention contains ordinary, non-adversarial learner
requests that sometimes conflict with the system teaching policy.  A post-hoc
contrast asks how much each information source changes the realized action:

- **system conflict effect:** system-policy high minus low inside the learner
  request that asks for the opposite behavior;
- **learner override effect:** learner-request high minus low inside the system
  condition that prescribes the opposite behavior; and
- **control gap:** system conflict effect minus learner override effect.

In the 2,560-response parent panel, question and answer system-conflict effects
are 0.803 and 0.823, learner-override effects are 0.000 and 0.002, and control
gaps are 0.803 and 0.822.  In the independently ordered 640-response subset, the
corresponding system effects are 0.825 and 0.856, learner effects are both 0,
and gaps are 0.825 and 0.856.  All five models have positive system effects and
gaps, though magnitudes vary substantially.

This is a mechanism clue for why a configured tutor policy can look consistent
without being learner-responsive.  It is not by itself surprising enough to be
the paper's main novelty: system-over-user priority is expected under standard
instruction hierarchies, as formalized by
[IHEval](https://aclanthology.org/2025.naacl-long.425/).  The educationally
important question is whether evaluation mistakes such consistency for
personalization, and whether an adaptive routing policy can retain the probing
benefit without the telling harm.

The exact exploratory artifacts are:

- `artifacts/factorial_control_asymmetry_exploratory_v1/`; and
- `artifacts/factorial_order_replication_control_asymmetry_exploratory_v1/`.

Both reports carry the status
`post_hoc_exploratory_on_existing_responses`.

## Closest-work boundary

The paper must not claim to introduce instruction conflicts, answer withholding,
or behavior-first persona evaluation.  Persona consistency across task formats
has already been directly studied by
[Reusens et al.](https://aclanthology.org/2025.findings-emnlp.603/).
[SHAPE](https://aclanthology.org/2026.acl-long.529/) and
[Answer Leakage Robustness](https://aclanthology.org/2026.acl-long.1412/) study
answer-inducing pressure and withholding defenses.  A preregistered audit already
shows that generic helpfulness is not a valid proxy for pedagogy
([Fan et al.](https://arxiv.org/abs/2607.28128)).

The narrower contribution supported here is the conjunction of:

- identical-context causal prompting across a nine-model tutoring panel;
- human-action validation independent of LLM judges;
- a robust average-gain / target-specific-harm reversal;
- direct measurement of cross-model policy homogenization; and
- a prospective test of whether apparent tutor consistency is controlled by the
  configured policy rather than the learner signal.

## Frozen prospective wording-transport experiment

The next experiment is a post-result prospective replication, not a clean
outcome-blind replication of the original panel.  It crosses eight new synthetic
base problems, two learner needs, eight question-by-answer-by-tone policy cells,
and two fully rewritten policy-clause sets.  The five available API models each
receive 256 prompts, for 1,280 calls total.  Each model's request queue is divided
into eight blocks containing every one of the 32
wording-by-learner-by-policy strata exactly once.

Both wording sets must independently pass the original target-effect,
every-model-sign, and selectivity gates.  The control-asymmetry estimand adds
these frozen thresholds for both question and answer:

- system conflict effect at least 0.60 and lower 95% bound at least 0.50;
- learner override 95% interval strictly inside [-0.10, 0.10];
- control gap at least 0.50 and lower 95% bound at least 0.40; and
- positive system-conflict effect and control gap in every model.

Failure of either wording set downgrades the corresponding claim.  Tone remains
a literal encouragement-marker endpoint regardless of numerical success.  The
experiment does not measure learning benefit.

### Frozen payload and code hashes

No paraphrase-response API call may occur until these files are committed and
published in a method PR.  At the local freeze represented by this note:

| File | SHA-256 |
|---|---|
| `data/factorial_paraphrase_replication_spec_v1.json` | `fd531ede42b80a581667bd543f978fecb210e309c6daf7d52d33e84c55806a9b` |
| `scripts/generate_factorial_paraphrase_replication.py` | `4a92ab00ac0c7b8210b481f237686d1488097a5a97b1e5b23d91be0b01d81f62` |
| `scripts/run_factorial_paraphrase_replication.py` | `74d3d58f4c7f87b0961d0b3f13da8682ea966fae4bd6052f25f3c620710728ce` |
| `scripts/analyze_factorial_paraphrase_replication.py` | `c14e1e38975c4f65952db799a1fb8604ef79d1a93ea8c03f25015eb07b1d2242` |
| `scripts/analyze_factorial_control_asymmetry.py` | `6c9a1a98c58841fa242cd7ac0f6f0f0ca39cc6a7fa4e5ce3087c9566cfff6179` |
| `artifacts/factorial_paraphrase_replication_v1/sample_manifest.jsonl` | `24bae58887c9806bf2338635ad2be57c716e86ae6f66ad8c59bafbe0c4e79c4f` |
| `artifacts/factorial_paraphrase_replication_v1/request_order_plan.jsonl` | `47f50c9cc662fe9554d7c33f04d3642d600ed9d433da5e8820949d918560c203` |

The payload audit contains 256 unique prompt hashes, zero hits for the original
policy-clause fragments, zero email/URL/phone-like flags, and balanced clause
positions (84--86 occurrences per policy-position cell).  Only synthetic
problems, deliberately wrong work, learner requests, and frozen policy clauses
are transmitted.

## Scientific decision

The control-asymmetry replication is worth running as a mechanism test, but a
top-tier paper should not be sold on that expected hierarchy effect alone.  The
primary research direction is the policy-homogenization paradox: an aggregate
pedagogy improvement can be produced by a one-size policy that becomes less
responsive exactly where direct instruction is appropriate.  A subsequent
prospective action-routing experiment must test whether context-conditioned
policy selection can remove that reversal without sacrificing average match.
