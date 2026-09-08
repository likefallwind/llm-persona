# Educational Personality in Language Models

> **Research goal active (2026-09-07).** The first experimental/manuscript checkpoint is complete; the top-conference quality goal remains open. See [quality reassessment and continuation](research/70_quality_goal_reopened.md).

**Update, 2026-09-08:** the [completed cue-transfer study](research/74_cue_transfer_results_v4.md)
changes the interpretation: answer-revelation and reasoning-elicitation defaults
retain predictive gains under new expressions, but the acknowledgement
student-state profile does not, despite a positive contemporary original-wording
control. The [integrated v4 bilingual draft](paper/educational_personality_v4/README.md)
now incorporates this finding in the abstract, design, results, discussion, and conclusion.
The v3 PDFs below preserve the earlier checkpoint.
[Archive inputs have been reconstructed](research/72_archive_input_reconstruction_v4.md);
natural-dialogue behavioral validation is frozen but unexecuted, pending specific
authorization for external coding of archived dialogue, references, and replies.
No archive-validation API job is running at this checkpoint. The research quality
goal remains incomplete; see the [v4 assessment](research/76_integrated_draft_quality_v4.md).
An additional [post-result diagnosis](research/78_cue_transfer_competing_explanations_results_v4.md)
separates loss of relative advantage from worsening absolute error: explicit
rewording slightly improves conditional loss while improving its baseline more;
implicit cues increase conditional loss. The bilingual draft now includes this
distinction and its descriptive decomposition, without changing the primary tests.

This study asks whether deployed language models have recurring educational
behavior that predicts their actions on new tutoring problems. It separates
model defaults, model-specific responses to student cues, and changes under
teaching instructions, without new human annotation or human-equivalent trait
claims.

As of 2026-09-07, all 5,320 formal tutor generations and all 12,120 confirmation
codes are complete. The six primary comparisons, eight coder-panel checks,
five generator deletions, 200 training-source resamples and confirmation-budget
sensitivity have finished. Default profiles predict all three primary actions;
student-state profiles add a resolved increment for affect acknowledgement.
Effect strength varies with model composition, and instruction-driven convergence
does not eliminate differences in permissible accompanying actions.

All 2,584 content reviews and all five content-sensitivity subsets are complete.
The [English/Chinese manuscript](paper/educational_personality_v3/README.md)
now includes the final empirical abstract, results, discussion, conclusion and
appendices. Content-screened matched subsets preserve the predictive pattern;
the low 18.5% natural-error positive agreement is explicitly retained as a
measurement limitation. The [evidence ledger](paper/educational_personality_v3/evidence_ledger.md)
and [final review](paper/educational_personality_v3/final_review.json) map claims
to source counts, estimates, uncertainty and verified PDF hashes.

Read the completed [English paper](paper/educational_personality_v3/build/working_draft_en.pdf),
[Chinese paper](paper/educational_personality_v3/build/working_draft_zh.pdf), or
[anonymous ACL layout](paper/educational_personality_v3/build/acl/anonymous_acl_draft.pdf).
The first-stage research and manuscript checkpoint is complete; these are local artifacts,
with no external submission or publication performed. The [scientific assessment](research/69_completed_content_and_final_scientific_assessment.md)
retains the contribution boundaries and remaining peer-review risks.

The [research charter](research/44_educational_personality_charter_v2.md),
[archive reanalysis](research/45_personality_evidence_gap_and_source_safe_results.md),
[measurement pilot](research/49_measurement_pilot_complete_and_prediction_development.md),
[prospective protocol](research/50_prospective_educational_personality_protocol_v3.md),
[related work](research/51_related_work_boundary_and_paper_spine_v3.md),
[archive role audit](research/54_archive_role_and_tutor_provenance_audit.md),
[content sensitivity policy](research/56_content_error_sensitivity_completion.md),
and [neutral precision analysis](research/57_design_precision_and_neutral_coverage.md)
remain the source records. Protocol deviations and failed runs are retained in
[training recovery](research/59_training_single_code_budget_amendment.md),
[Gateway recovery](research/63_gateway_outage_and_recovery.md),
[confirmation budget amendment](research/64_confirmation_six_code_budget_amendment.md),
and [single transport amendment](research/65_confirmation_single_transport_timeout_amendment.md).
The complete-main checkpoint agrees with all nine corresponding official tables;
its separate [record](research/66_complete_main_panel_checkpoint.md) does not
replace the full-study completion artifacts.

## Archived policy-signature study and reproduction

The material below describes the completed earlier study and its frozen rules.
Its results and failures remain intact; the v2 charter defines the current scope.

This repository studies whether language models exhibit stable, task-general
behavioral dispositions when acting in educational settings.  The central
empirical asset is the set of model responses produced by the shared
EduBenchmark evaluation harness.

The project deliberately studies **pedagogical policy signatures** rather than
claiming that language models possess human personality. A validated disposition
is a narrower observable, repeatable policy tendency (for example, giving a
direct answer versus eliciting student reasoning) that:

1. survives controls for task, item difficulty, response length, and competence;
2. generalizes to held-out educational tasks;
3. is robust across independent measurement methods; and
4. changes predictably under a targeted intervention.

The initial six-model paired panel is:

- MiniMax-M3
- MiniMax-M2.7
- GLM-5.2
- DeepSeek-V4-Pro
- Doubao-Seed-2.0-Pro
- Qwen3.5-4B

Doubao-Seed-2.0-Lite is retained as an optional seventh model wherever a complete
paired run exists.

An extended nine-model MathDial panel additionally includes Doubao-Seed-2.0-Lite,
DeepSeek-V4-Flash, and Qwen3.8-27B.  It supports four approximate within-family
comparisons, but these are not treated as clean parameter-scale interventions
because version, training, and serving differences are not held constant.

## Reproduce the corpus inventory

```bash
export EDUBENCH_ROOT=/path/to/edubenchmark
python scripts/build_corpus_inventory.py \
  --eval-root "$EDUBENCH_ROOT/reports/eval" \
  --output-dir artifacts/inventory
```

The inventory only reads the upstream evaluation repository.  It does not copy
raw model responses or credentials into this repository.

## Reproduce the completed analyses

Create the environment from `requirements.txt`, then run:

```bash
python scripts/run_behavioral_pilot.py \
  --inventory artifacts/inventory/corpus_inventory.json \
  --roles data/benchmark_roles.json \
  --output-dir artifacts/pilot

python scripts/analyze_existing_judge_robustness.py \
  --eval-root "$EDUBENCH_ROOT/reports/eval" \
  --features artifacts/pilot/behavior_features.csv \
  --output-dir artifacts/judge_robustness

python scripts/analyze_discriminant_validity.py \
  --teaching artifacts/pilot/behavior_features.csv \
  --negative artifacts/negative_controls/behavior_features.csv \
  --output-dir artifacts/discriminant_validity

python scripts/analyze_extended_panel.py \
  --features artifacts/extended_panel/behavior_features.csv \
  --output-dir artifacts/extended_analysis

python scripts/semantic_power_audit.py --output-dir artifacts/power_audit

python scripts/analyze_dialogue_act_validity.py \
  --inventory artifacts/inventory/corpus_inventory.json \
  --mathdial-dir "$EDUBENCH_ROOT/sources/datasets/mathdial" \
  --bridge-dir "$EDUBENCH_ROOT/sources/datasets/mathtutorbench/datasets" \
  --output-dir artifacts/dialogue_act_validity

python scripts/analyze_judge_human_calibration.py \
  --eval-root "$EDUBENCH_ROOT/reports/eval" \
  --output-dir artifacts/judge_human_calibration

python scripts/analyze_longtutor_objective_validity.py \
  --inventory artifacts/inventory/corpus_inventory.json \
  --output-dir artifacts/longtutor_objective_validity
```

The same completed, non-semantic analyses can be regenerated with one command.
Set `EDUBENCH_ROOT` if the sibling repository is elsewhere:

```bash
EDUBENCH_ROOT=/path/to/edubenchmark scripts/reproduce_completed.sh
```

The command ends by running `scripts/verify_release_claims.py`, a machine-readable
gate that checks registered headline claims against the regenerated CSVs. A
drifted count or effect fails the command rather than silently leaving stale
prose.  Other descriptive values remain covered by the reproducibility manifest
and ordinary manuscript review, not by an inaccurately broad automated claim.

It also writes `artifacts/provenance_audit/run_provenance.csv`, which pins every
selected upstream prediction/summary file by SHA-256 and reports whether decoding
and prompt-version metadata are actually recoverable.  Frozen responses permit
exact analysis reproduction even when provider-side regeneration is not exact.

The frozen external semantic-coding runner is `scripts/run_semantic_judge.py`.
It exports sampled educational contexts and candidate responses to configured
judge endpoints, so it must only be run after explicit authorization naming the
payload and destinations. That authorization was obtained for the frozen
three-judge panel. The formal complete-case analysis contains 1,074 annotations
after the audited exclusion of one technically failed paired context (six
ratings, 0.56%). Reproduce it with:

```bash
python scripts/analyze_semantic_panel.py \
  --panel-dir artifacts/semantic_judge/full_v1 \
  --exclusions research/semantic_panel_exclusions_v1.json \
  --features artifacts/pilot/behavior_features.csv \
  --dialogue-acts artifacts/dialogue_act_validity/generated_dialogue_acts.csv \
  --output-dir artifacts/semantic_panel

python scripts/analyze_semantic_leaveout_sensitivity.py \
  --ratings artifacts/semantic_panel/unblinded_ratings.csv \
  --output-dir artifacts/semantic_leaveout

python scripts/analyze_semantic_scale_diagnostics.py \
  --ratings artifacts/semantic_panel/unblinded_ratings.csv \
  --consensus artifacts/semantic_panel/response_consensus.csv \
  --output-dir artifacts/semantic_scale_diagnostics

python scripts/analyze_semantic_objective_validity.py \
  --semantic-consensus artifacts/semantic_panel/response_consensus.csv \
  --objective-outcomes artifacts/longtutor_objective_validity/matched_objective_outcomes.csv \
  --output-dir artifacts/semantic_objective_validity

python scripts/evaluate_submission_decision.py \
  --semantic-dir artifacts/semantic_panel \
  --leaveout-dir artifacts/semantic_leaveout \
  --scale-dir artifacts/semantic_scale_diagnostics \
  --objective-dir artifacts/semantic_objective_validity \
  --output-dir artifacts/submission_decision
```

The last command applies the thresholds frozen in
`research/11_submission_decision_rule.md` without dropping failed dimensions.
`scripts/finalize_semantic_analysis.sh` runs the same sequence only after the
strict exclusion-aware coverage and response-level completeness gates pass.

`scripts/run_local_semantic_judge.py` keeps all text on the machine through
Ollama; the current 8B/12B smoke tests are valid structurally but too slow and
low-confidence to serve as primary judges.  Local model work is paused until a
stronger server is available.

## Build the anonymous ACL submission

The review manuscript is in `paper/submission/main.tex`. It uses the official
ACL `[review]` mode and a pinned, hash-checked checkout of
<https://github.com/acl-org/acl-style-files>. The upstream style files are not
vendored or modified. Build the deterministic seven-page PDF with:

```bash
ACL_STYLE_DIR=/path/to/acl-style-files ./scripts/build_acl_submission.sh
```

The exact official commit and file hashes are recorded in
`paper/submission/README.md`. The build fails on a style hash mismatch or any
unresolved citation/reference. The fresh-checkout reproduction boundary and ARR
checklist evidence map are in `research/14_clean_room_reproduction.md` and
`research/15_arr_responsible_nlp_checklist.md`.

## Prospective factorial policy intervention

`research/17_factorial_prompt_intervention_protocol.md` freezes a synthetic
2×2×2 experiment separating question-first, answer-withholding, and warm-tone
instructions. It uses 32 newly generated math problems, two conflicting learner
requests, eight policy cells, and five currently reachable model routes (2,560
calls). No benchmark or learner text is transmitted.

Generate and audit the public synthetic payload without making API calls:

```bash
python scripts/generate_factorial_prompt_panel.py
python scripts/run_factorial_prompt_panel.py --dry-run
```

The live runner is append-only, resumable, provider-capped, and protected by a
single-writer lock. Raw provider responses remain ignored; only their hashes,
deterministic behavior metrics, and aggregate contrasts are eligible for release.

`research/19_factorial_order_replication_protocol.md` freezes a 640-call,
outcome-blind request-order replication. It copies 128 byte-identical parent
prompts, independently hash-randomizes their queue for every model, and applies
exact 16-cell local blocking plus downgrade-only joint gates. Generate and
dry-run that public design with:

```bash
python scripts/generate_factorial_order_replication.py
python scripts/run_factorial_order_replication.py --dry-run
```

The order replication runs only after the 2,560-call parent panel completes and
regardless of its outcomes. Its raw response directory is also ignored.

Both panels are complete (2,560/2,560 parent and 640/640 replication, with zero
failed calls). Reproduce the frozen analyses and paper-facing report with:

```bash
python scripts/analyze_factorial_prompt_panel.py --bootstrap-reps 2000
python scripts/analyze_factorial_order_replication.py --bootstrap-reps 2000
python scripts/render_factorial_results_report.py
```

The three system clauses pass their registered target, every-model sign,
selectivity, and randomized-order replication gates. Parent target effects are
0.773 (question-first), 0.895 (correct answer reveal), and 0.595 (frozen
encouragement-lexicon marker); replication effects are 0.809, 0.922, and 0.550.
Learner-request adaptation fails both registered 0.10 gates in both panels. The
fixed complete report is
`research/20_factorial_results.md`; released derived rows contain hashes and
deterministic metrics, not response text.

A post-result, downgrade-only blind validation samples 480 responses without
using outcomes or factor cells and obtains 144/144 batch annotations from three
judges. Question-first and correct-answer-reveal validate (balanced accuracy
1.000 and 0.996; kappa 1.000 and 0.992). The lexicon marker does not validate
semantic warmth or support (0.818; kappa 0.631), so the paper reports it only by
its literal operational definition. See
`research/22_factorial_detector_validation_results.md`.

## Prospective wording transport and routing falsifications

Three later, separately frozen experiments test whether the factorial result
transports and whether it can support action-adaptive control. They are complete:
the paraphrase panel has 1,280/1,280 successful calls, the action-routing panel
has 1,920/1,920, and the two-stage routing panel has 2,400/2,400, all with zero
failed or missing responses.

The two validated behavioral clauses transport across both paraphrase sets; the
literal encouragement marker does not. The action-routing panel independently
replicates the generic probing benefit and telling-target harm, but rejects its
registered single-pass adaptive router. The two-stage trial also fails its joint
gate: selectors remain near chance and underperform the same-snapshot single-pass
baseline even though the forced ASK and EXPLAIN executors realize their assigned
actions at 0.998--1.000. These are controller-requirements and falsification
results, not evidence that this repository invented or solved adaptive tutoring.
See `research/27_factorial_paraphrase_replication_results.md`,
`research/28_action_routing_trial_results.md`, and
`research/30_two_stage_routing_results.md`.

With the ignored private response JSONL files present, reproduce all three result
families with:

```bash
python scripts/analyze_factorial_paraphrase_replication.py --bootstrap-reps 2000
python scripts/analyze_action_routing_trial.py
python scripts/analyze_action_routing_surface.py
python scripts/analyze_two_stage_routing_trial.py
python scripts/analyze_two_stage_selection_bias.py
```

`scripts/finalize_semantic_analysis.sh` first requires complete frozen response
panels, then rebuilds every semantic, factorial, paraphrase, and routing analysis,
verifies registered claims and privacy structure, audits the anonymous PDF,
rebuilds figures, writes the reproducibility manifest, and runs the full tests.
Raw provider responses and request manifests remain deliberately excluded from
Git; a clean public checkout verifies all released derived artifacts and claims
but cannot regenerate response-derived tables without those governed inputs.

The data and model release boundaries are documented in
`research/09_dataset_card.md` and `research/10_model_panel_card.md`.  In
particular, a public release contains derived measurements and hashes rather
than copied benchmark prompts or model responses.  Run
`python scripts/audit_release_privacy.py --root .` before publication; it fails
on Git-eligible artifacts with explicit source-text fields or local user-home
paths, while documenting that this structural check is not a complete privacy
assessment.

## Existing-response general-personality bridge

Before authorizing a new general-personality experiment, the archive-only bridge
audit screens all 283,926 six-model paired responses. A frozen eligibility map
retains 123,468 free-form responses across 16 benchmarks and excludes constrained
labels from personality interpretation. It tests communal, dialogic, directive,
epistemic, and boundary-language manifestations against organizational-style and
verbosity controls, then links non-tutoring profiles to default tutoring and the
existing educational axes.

```bash
EDUBENCH_ROOT=/path/to/edubenchmark \
  .venv/bin/python scripts/analyze_existing_general_personality_bridge.py
```

No content candidate passes the joint stability, transport, and surface-
nonreduction screen. Communal expression has strong pooled transport but weak
non-tutoring recurrence; dialogic engagement has moderate recurrence but misses
the transport gate. Organizational style is the strongest general signal. The
result therefore retains prompt-contingent pedagogical policy signatures and
rejects upgrading the current archive to a domain-general personality claim. See
`research/37_existing_response_general_personality_bridge_protocol.md` and
`research/38_existing_response_general_personality_bridge_results.md`.

The follow-on content audit explicitly covers all Big Five dimensions, HEXACO
honesty-humility, the Dark Triad, all ten Schwartz values, adjacent behavioral
dispositions, measurement modality, and stability perturbations:

```bash
.venv/bin/python scripts/audit_general_personality_content_archive.py \
  --edubench-root /path/to/edubenchmark
```

It audits 22 constructs or validity targets: nine have only partially observable
behavioral candidates and thirteen are not identifiable in the old tasks. No
general-personality construct is validated. The only purpose-built pilot
priority is a narrow affiliation/agreeableness/benevolence cluster: its pooled
cross-role and educational links are strong, while its individual-task ordering
is unstable. Conscientiousness-like organization is falsified by its negative
association with objective IFEval accuracy; epistemic and safety facets do not
converge into honesty-humility or Schwartz conservation. See
`research/39_general_personality_content_archive_protocol.md` and
`research/40_general_personality_content_archive_results.md`.

The archive-selected affiliation hypothesis was then tested prospectively on
five reachable configurations, with 280 generator calls and 144 blinded
three-judge calls:

```bash
.venv/bin/python scripts/analyze_affiliation_stability_pilot.py
```

All frozen stability gates pass (judge ICC(3,k)=0.931; default education versus
non-education rho=0.900; default versus irrelevant-context rho=0.718), and the
high-minus-low prompt effect is 1.689/5 with all models moving in the intended
direction. General-trait convergence nevertheless fails: self-report correlates
-0.200 with open behavior and default forced choice has a complete affiliative
ceiling. The supported extension is therefore a stable but prompt-contingent
affiliation behavior policy, not Big Five personality. See
`research/41_affiliation_stability_pilot_protocol.md` and
`research/42_affiliation_stability_pilot_results.md`.

## Planning-only learner-outcome extension

`research/24_learner_outcome_trial_protocol.md` turns the remaining journal-level
gap into a machine-checkable design without claiming that a trial has occurred.
It proposes learner-level randomization across four policy arms and three hidden
model routes, with a seven-day unassisted transfer test as the sole primary
outcome. A conservative effect-size-0.15 calculation requires 698 completed
learners per arm; after 15% attrition inflation, the balanced target is 3,300
learners across 12 cells. Scoring is automatic and semantic warmth is excluded.

```bash
python scripts/power_learner_outcome_trial.py --require-pass
```

Passing this command proves only that the planning contract is internally
consistent. The status remains `planning_only_not_preregistered_not_started`
until a collaborating institution supplies ethics approval, registration, and
actual learners.

## Evidential status

The completed evidence has four complementary pieces.  In leave-one-model-out
prediction with exact-item fixed effects, transparent policy features improve
tutoring-quality AUC by 0.023--0.031 under two judges, while length adds about
0.002.  A non-LLM action classifier trained on existing human MathDial labels
finds prompt effects for all nine models but reveals a sharp failure on human
`telling` targets.  On LongTutor, adaptive-teaching scores do not improve
human-gold diagnosis prediction beyond exact-history difficulty, separating an
adaptive presentation from accurate learner modeling. The completed semantic
panel adds a separate result: semantic features identify models on held-out
educational tasks at 0.322 accuracy (0.167 chance) and reach 0.391 when combined
with transparent features. Registered gates retain help directness and cognitive
load as cross-task signatures, but only help directness as a validated
disposition, forcing the policy-signature thesis. The completed prospective
factorial adds a separate control result: explicit
system clauses selectively address question-first and answer-reveal behavior;
the warm-tone clause changes an order-robust encouragement-lexicon marker that
fails broader semantic validation. Learner requests alone do not reliably
produce the corresponding adaptation. Finally, the archive-only general-
personality bridge retains 123,468 free-form responses but finds no content
candidate that jointly passes non-tutoring recurrence and default-tutoring
transport; organizational style is the most stable general profile. See
`research/03_claim_evidence_matrix.md` and `research/04_red_team_review.md` for
the claim boundary and remaining submission blockers.
