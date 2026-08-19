# Pedagogical Policy Signatures in LLM Tutors

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

The data and model release boundaries are documented in
`research/09_dataset_card.md` and `research/10_model_panel_card.md`.  In
particular, a public release contains derived measurements and hashes rather
than copied benchmark prompts or model responses.  Run
`python scripts/audit_release_privacy.py --root .` before publication; it fails
on Git-eligible artifacts with explicit source-text fields or local user-home
paths, while documenting that this structural check is not a complete privacy
assessment.

## Evidential status

The completed evidence has three complementary pieces.  In leave-one-model-out
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
disposition, forcing the policy-signature thesis. See
`research/03_claim_evidence_matrix.md` and `research/04_red_team_review.md` for
the claim boundary and remaining submission blockers.
