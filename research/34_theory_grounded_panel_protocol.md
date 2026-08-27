# Theory-grounded educational-character panel protocol

Snapshot: 2026-08-26. Status: **protocol executed; formal split complete**.
This is not represented as an outcome-blind preregistration: pilot results were
used for scale selection. Formal thresholds below were fixed before the
disjoint formal split was scored or inspected; results are recorded in
`research/36_confirmatory_character_results.md`.

## Research question

Can four theory-derived behavioral dimensions replace the weakest constructs in
the original flat eight-dimension panel while remaining distinguishable from
response quality and learning outcomes?

The new judge panel measures only the four axes that lack a suitable existing
source:

1. `instructional_agency`: learner-led to tutor-controlled next cognitive move;
2. `relational_communion`: distant/transactional to warm/affiliative interaction;
3. `information_structure`: fragmented/ambiguous to sequenced and actionable;
4. `learner_contingency`: generic policy to learner-evidence-dependent policy.

`help_directness` is retained from the original validated semantic/action panel.
Epistemic commitment is measured with objective confidence, answer revision,
and abstention data rather than another floor-prone semantic caution rating.

## Frozen response sample and split

The runner is `scripts/run_theory_grounded_judge.py`. It uses seed `20260819`
and the original inventory/counts, reproducing all 360 response slates from
`artifacts/semantic_judge/full_v1/sample_manifest.json` exactly. Each slate
contains the six fixed model responses in judge-specific blinded order.

The development split selects six `pair_id` values per `pair_group` by SHA-256
rank. Both generic and pedagogy arms of a MathDial item are assigned together.
This gives 36 pilot slates and 324 untouched formal slates. Because external
review of LongTutor histories has not been newly authorized, the current
executable pilot is restricted to 30 public MathTutorBench slates: six matched
standard pairs (12 slates), six matched hard pairs (12), and six Socratic
slates. No LongTutor context is transmitted in this run.

Two earlier output directories, `theory_grounded_judge_v1` and `v2`, are design
development debris only. V1 split paired arms independently; V2 corrected the
pairing but used a different sampling seed. Neither is eligible for analysis or
claim support. V3 is the sole analysis panel.

## Judges and payload boundary

The pilot judges are MiniMax-M3 and MiniMax-M2.7 through the MiniMax official
API plus GLM-5.2 and DeepSeek-V4-Pro through the local API Gateway. Concurrency
is capped at four for MiniMax and eight for the Gateway. Candidate identities,
prompt-arm labels, gold answers, provider credentials, and model reasoning
traces are excluded. Raw source text is not copied into derived outputs. The
four judges span three model families, although two judges are from MiniMax;
formal conclusions therefore require leave-one-family sensitivity.

## Pilot decision rule

The rubric may proceed unchanged to the formal split only if each dimension has:

1. consensus score SD at least 0.50;
2. floor and ceiling fractions each below 0.80;
3. two-judge ICC(3,k) at least 0.60; and
4. cross-judge six-model profile Spearman at least 0.70.

Failure of response-level ICC with strong model-profile agreement permits
profile-level exploratory use but not response-level measurement. Failure of
model-profile agreement removes the dimension from the formal trait/signature
claim. Pilot thresholds were not weakened after inspection.

## Pilot outcome and one permitted scale revision

The complete synthetic pilot contains 120/120 valid judge calls (30 slates by
four judges). `instructional_agency` and `relational_communion` passed all four
measurement gates. `learner_contingency` failed the fixed minimum cross-judge
model-profile threshold (minimum rho 0.638), so it is excluded from the
confirmatory trait claim. The original double-barrelled `information_structure`
also failed model-profile agreement (minimum rho 0.123).

As the sole permitted wording revision, `information_structure` was split into
`information_sequencing` and `next_step_actionability` and rerun on the same
pilot. The split panel again achieved 120/120 coverage. Sequencing still failed
model-profile agreement (minimum rho -0.029) and is rejected. Actionability
passed: ICC(3,k)=0.940, consensus SD=1.314, minimum judge-pair model-profile
rho=0.714, and pilot cross-task ICC(3,1)=0.518. No further scale revision is
permitted.

The compact confirmatory rubric therefore contains only agency, communion, and
next-step actionability. Because placing unchanged dimensions into a new joint
rubric can itself change judge behavior, the same 30-slate pilot is used for a
bridge before opening the formal split. Each dimension must match all 180
response hashes and achieve raw-score Spearman at least 0.70, exact-item-
centered Spearman at least 0.60, and six-model profile Spearman at least 0.70
against its source pilot. These bridge thresholds are fixed before bridge
calls. Any failure cancels the compact formal panel rather than triggering more
wording iteration.

The first compact bridge attempt (`confirmatory_character_judge_v1`) is
ineligible transport debris: the MiniMax official Token Plan was exhausted
after the first few requests, so the run was interrupted and is never analyzed.
Four API Gateway models were then smoke-tested. GLM-5.2, DeepSeek-V4-Pro,
Doubao-Seed-2.0-Lite, and Gateway-routed MiniMax-M2.7 returned valid JSON; Kimi
K2.6 returned an empty response and was rejected. A v2 attempt incorrectly
retained the Kimi-motivated 4,096-token cap for all judges; repeated empty GLM
outputs showed that the cap could starve hidden reasoning, so v2 was interrupted
and is also ineligible. The replacement v3 bridge freezes the four successful
Gateway judges, uncapped as in the successful original pilots. They represent
four model families on one provider route. Bridge thresholds remain unchanged.

The complete v3 bridge achieved 120/120 valid calls. All dimensions passed the
bridge: raw response rho was 0.901 for agency, 0.940 for communion, and 0.867
for actionability; exact-item-centered rho was 0.855, 0.856, and 0.866; all
three six-model profile correlations were 0.943. Under the new four-family
panel, communion and actionability also passed every pilot measurement gate.
Agency did not: the minimum pairwise judge model-profile rho was 0.657, below
the frozen 0.70 threshold, despite ICC(3,k)=0.903. Formal calls therefore test
communion and actionability confirmatorily. Agency is retained in the same
compact response at zero marginal call cost but is permanently exploratory;
formal-set recovery cannot override its pilot failure.

## Formal-set decision rule

A dimension becomes a finite-panel cross-task signature only if it first passes
the pilot measurement gates and then, on the untouched formal set:

1. retains ICC(3,k) at least 0.60, score SD at least 0.50, and both endpoints
   below 0.80;
2. has cross-task ICC(3,1) at least 0.50 or median pairwise task Spearman at
   least 0.50;
3. shows nonzero exact-item-controlled model variance with bootstrap 95% lower
   bound above zero in every eligible analyzed benchmark; and
4. is not reducible to an original scale under the convergence/discriminant
   checks below.

The operational reducibility threshold is fixed before formal inspection: the
maximum absolute exact-response Spearman with any original semantic scale must
be below 0.80. The bridge pilot already shows communion at rho=0.833 with
`affective_warmth`; unless the untouched formal set falls below 0.80, communion
is a reliable relabelling/refinement of warmth rather than an additional axis.

To reach the stronger validated-character tier rather than merely a semantic
signature, at least one registered transparent behavior anchor must also have
the expected sign and absolute Spearman magnitude at least 0.30 on identical
response hashes: agency (`imperative_rate` positive or `question_rate`
negative) and communion (`praise_rate` or `encouragement_rate` positive).
Actionability has no uncontaminated pre-existing transparent detector and can
therefore reach at most the finite-panel signature tier in the current study.

The formal synthetic analysis uses the 290 non-pilot MathTutorBench slates. The
34 formal LongTutor slates remain unscored unless separately authorized.

## Construct checks

All correlations use identical response hashes where possible and are
descriptive rather than population estimates.

- Agency should correlate negatively with original `elicitation` and
  `autonomy_support`, and positively with `help_directness`, without becoming a
  duplicate of directness.
- Communion should correlate positively with `affective_warmth` but must improve
  prompt-wording reliability before it is promoted.
- Information sequencing is rejected. Next-step actionability is retained as a
  distinct candidate strategy dimension; a short or long response can be
  actionable, and actionability is not equated with tutor control.
- Learner contingency should correlate positively with `personalization` and
  must still face the already-failed factorial learner-need and LongTutor
  objective tests. Semantic relabelling cannot erase those negative results.
- Agency and communion are approximately discriminant at the response level if
  their exact-item-centered absolute Spearman correlation is at most 0.30.

## Prompt estimands

Prompt effects are computed only within matched `pair_id`, as pedagogy minus
generic. The expected agency direction is lower tutor control under the
pedagogy/scaffolding prompt. No favorable direction is registered for communion
or actionability. The actionability pilot showed positive average
pedagogy-minus-generic effects in all 12 model-by-task cells (0.50 to 2.08
points), but this was observed during scale development and is not a registered
formal direction. Model-specific prompt elasticity is a meta-property and does
not upgrade a dimension that fails measurement or cross-task gates.

## Judge-family sensitivity

Before formal results are inspected, the leave-one-family robustness gates are
fixed. For each dimension, every one-family-excluded panel must preserve: (1)
the full-panel six-model profile at rho at least 0.90; (2) the 12 model-by-task
prompt-delta profile at rho at least 0.70; (3) the sign of the overall prompt
delta when its full-panel magnitude is at least 0.10; and (4) the formal
cross-task ICC-or-rank gate. A full-panel signature that fails any leaveout gate
is reported as judge-family-sensitive rather than robust. Because all four
families share the API Gateway route, this is not provider-route replication.

## Formal execution and outcome

The synthetic formal run completed 1,160/1,160 unique calls (290 slates by four
judge families), with 290 calls per judge, zero failed or invalid rows, and exit
code zero. LongTutor remained excluded. A post-completion dry run regenerated
the payload audit with the exact formal execution scope.

No new dimension passes the full frozen chain:

- agency has strong formal agreement and cross-task stability but remains
  exploratory because its replacement-panel pilot gate failed;
- communion is reliable and cross-task rank-stable, but has no model variance
  in the Socratic task and exceeds the fixed 0.80 redundancy threshold with
  `affective_warmth`; and
- actionability has high response-level ICC and a large shared prompt effect,
  but fails formal judge model-profile agreement and reverses model ordering
  across tasks.

All judge-family leaveouts retain the overall prompt directions. Actionability
also retains its cross-task failure in every leaveout, so no single judge family
explains the negative signature decision.

## Claim boundary and stopping rule

The unit is a fixed deployed model configuration, not a human-like psyche or a
population of models. Accuracy, diagnosis, action optimality, safety, and
learning gains remain competencies or outcomes.

The formal panel does not supply evidence that a failed gate is merely a
same-context scoring artifact. Further model calls are justified only by a new
identification layer—prospective learner outcomes, independently sampled model
families/provider routes, learner-evidence interventions, or matched epistemic
policy prompts. Generic scale expansion, Big Five questionnaires, wording
iteration, and repeated judge panels do not satisfy the stopping rule.
