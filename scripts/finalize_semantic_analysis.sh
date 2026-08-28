#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$ROOT/.venv/bin/python"
EDUBENCH_ROOT="${EDUBENCH_ROOT:-$ROOT/../edubenchmark}"
export EDUBENCH_ROOT
PANEL="$ROOT/artifacts/semantic_judge/full_v1"
OUT="$ROOT/artifacts/semantic_panel"
EXCLUSIONS="$ROOT/research/semantic_panel_exclusions_v1.json"

cd "$ROOT"

"$PY" scripts/semantic_judge_status.py \
  --output-dir "$PANEL" \
  --exclusions "$EXCLUSIONS" \
  --require-complete

# This command intentionally has no --allow-incomplete flag. It is the formal
# 1,074-annotation complete-case gate after the frozen two-batch technical
# attrition amendment.
"$PY" scripts/analyze_semantic_panel.py \
  --panel-dir "$PANEL" \
  --exclusions "$EXCLUSIONS" \
  --features artifacts/pilot/behavior_features.csv \
  --dialogue-acts artifacts/dialogue_act_validity/generated_dialogue_acts.csv \
  --output-dir "$OUT" \
  --bootstrap-reps 2000

"$PY" scripts/analyze_semantic_leaveout_sensitivity.py \
  --ratings "$OUT/unblinded_ratings.csv" \
  --output-dir artifacts/semantic_leaveout

"$PY" scripts/analyze_semantic_scale_diagnostics.py \
  --ratings "$OUT/unblinded_ratings.csv" \
  --consensus "$OUT/response_consensus.csv" \
  --output-dir artifacts/semantic_scale_diagnostics

"$PY" scripts/analyze_semantic_objective_validity.py \
  --semantic-consensus "$OUT/response_consensus.csv" \
  --objective-outcomes artifacts/longtutor_objective_validity/matched_objective_outcomes.csv \
  --output-dir artifacts/semantic_objective_validity \
  --permutations 5000

"$PY" scripts/evaluate_submission_decision.py \
  --semantic-dir "$OUT" \
  --leaveout-dir artifacts/semantic_leaveout \
  --scale-dir artifacts/semantic_scale_diagnostics \
  --objective-dir artifacts/semantic_objective_validity \
  --output-dir artifacts/submission_decision

"$PY" scripts/analyze_prompt_contingent_signatures.py \
  --bootstrap-reps 5000 \
  --attribution-bootstrap-reps 2000

# The theory-grounded confirmation uses only the frozen synthetic formal split.
# Raw judge rows remain ignored; the analyzer exports identifiers, hashes,
# ratings, and aggregates only. LongTutor histories are not transmitted.
"$PY" scripts/analyze_theory_grounded_panel.py \
  --panel-dir artifacts/confirmatory_character_judge_v3 \
  --output-dir artifacts/confirmatory_character_panel_v1/formal \
  --split formal \
  --judges glm-5.2,deepseek-v4-pro,doubao-seed-2.0-lite,minimax-m2.7 \
  --benchmarks mathtutorbench_scaffolding,mathtutorbench_pedagogy,mathtutorbench_scaffolding_hard,mathtutorbench_pedagogy_hard,mathtutorbench_socratic \
  --pilot-decision artifacts/confirmatory_character_panel_v1/pilot/decision.json \
  --bootstrap 2000 \
  --seed 20260826 \
  --require-complete

"$PY" scripts/analyze_judge_family_sensitivity.py \
  --ratings artifacts/confirmatory_character_panel_v1/formal/unblinded_ratings.csv \
  --output-dir artifacts/confirmatory_character_panel_v1/formal

"$PY" scripts/analyze_character_quality_boundary.py \
  --consensus artifacts/confirmatory_character_panel_v1/formal/response_consensus.csv \
  --features artifacts/pilot/behavior_features.csv \
  --output-dir artifacts/confirmatory_character_panel_v1/formal

"$PY" scripts/analyze_epistemic_character_axes.py
"$PY" scripts/analyze_normative_boundary_axes.py

"$PY" scripts/synthesize_educational_character_framework.py \
  --formal-decision artifacts/confirmatory_character_panel_v1/formal/decision.json \
  --family-sensitivity artifacts/confirmatory_character_panel_v1/formal/judge_family_sensitivity.json \
  --submission-decision artifacts/submission_decision/submission_decision.json \
  --epistemic-decision artifacts/epistemic_character_axes_v1/decision.json \
  --normative-decision artifacts/normative_boundary_axes_v1/decision.json \
  --prompt-decision artifacts/prompt_contingent_signatures_v1/decision.json \
  --formal-profiles artifacts/confirmatory_character_panel_v1/formal/model_profiles.csv \
  --semantic-profiles artifacts/prompt_contingent_signatures_v1/default_semantic_profiles.csv \
  --epistemic-profiles artifacts/epistemic_character_axes_v1/model_profiles.csv \
  --formal-prompt artifacts/confirmatory_character_panel_v1/formal/prompt_effects.csv \
  --semantic-prompt artifacts/prompt_contingent_signatures_v1/model_semantic_elasticity.csv \
  --output-dir artifacts/educational_character_framework_v1

"$PY" scripts/analyze_existing_general_personality_bridge.py

"$PY" scripts/audit_general_personality_content_archive.py \
  --edubench-root "$EDUBENCH_ROOT"

"$PY" scripts/analyze_affiliation_stability_pilot.py

"$PY" scripts/factorial_prompt_status.py --require-complete

"$PY" scripts/analyze_factorial_prompt_panel.py \
  --bootstrap-reps 2000

"$PY" scripts/factorial_prompt_status.py \
  --spec data/factorial_order_replication_spec_v1.json \
  --manifest artifacts/factorial_order_replication_v1/sample_manifest.jsonl \
  --responses artifacts/factorial_order_replication_v1/run/responses.jsonl \
  --require-complete

"$PY" scripts/analyze_factorial_order_replication.py \
  --bootstrap-reps 2000

"$PY" scripts/factorial_detector_validation_status.py \
  --require-complete

"$PY" scripts/analyze_factorial_detector_validation.py

"$PY" scripts/factorial_prompt_status.py \
  --spec data/factorial_paraphrase_replication_spec_v1.json \
  --manifest artifacts/factorial_paraphrase_replication_v1/sample_manifest.jsonl \
  --responses artifacts/factorial_paraphrase_replication_v1/run/responses.jsonl \
  --require-complete

"$PY" scripts/analyze_factorial_paraphrase_replication.py \
  --bootstrap-reps 2000

"$PY" scripts/factorial_prompt_status.py \
  --spec data/action_routing_trial_spec_v1.json \
  --manifest artifacts/action_routing_trial_v1/sample_manifest.jsonl \
  --responses artifacts/action_routing_trial_v1/run/responses.jsonl \
  --require-complete

"$PY" scripts/analyze_action_routing_trial.py

"$PY" scripts/analyze_action_routing_surface.py

"$PY" scripts/factorial_prompt_status.py \
  --spec data/two_stage_routing_trial_spec_v1.json \
  --manifest artifacts/two_stage_routing_trial_v1/sample_manifest.jsonl \
  --responses artifacts/two_stage_routing_trial_v1/run/responses.jsonl \
  --require-complete

"$PY" scripts/analyze_two_stage_routing_trial.py

"$PY" scripts/analyze_two_stage_selection_bias.py

"$PY" scripts/render_factorial_results_report.py

"$PY" scripts/power_learner_outcome_trial.py \
  --require-pass

"$PY" scripts/audit_acl_submission.py \
  --root "$ROOT" \
  --require-pass

"$PY" scripts/verify_release_claims.py \
  --root "$ROOT" \
  --output-dir artifacts/claim_verification

"$PY" scripts/audit_release_privacy.py \
  --root "$ROOT"

"$PY" scripts/make_paper_figures.py \
  --root "$ROOT"

"$PY" scripts/build_reproducibility_manifest.py \
  --root "$ROOT" \
  --include \
    scripts tests data research paper \
    artifacts/inventory \
    artifacts/provenance_audit \
    artifacts/pilot \
    artifacts/negative_controls \
    artifacts/discriminant_validity \
    artifacts/extended_panel \
    artifacts/extended_analysis \
    artifacts/judge_robustness \
    artifacts/judge_human_calibration \
    artifacts/dialogue_act_validity \
    artifacts/longtutor_objective_validity \
    artifacts/power_audit \
    artifacts/claim_verification \
    artifacts/semantic_judge/full_v1 \
    artifacts/semantic_panel \
    artifacts/semantic_leaveout \
    artifacts/semantic_scale_diagnostics \
    artifacts/semantic_objective_validity \
    artifacts/submission_decision \
    artifacts/prompt_contingent_signatures_v1 \
    artifacts/theory_grounded_judge_v3 \
    artifacts/theory_grounded_panel_v1 \
    artifacts/structure_facet_judge_v1 \
    artifacts/structure_facet_panel_v1 \
    artifacts/confirmatory_character_judge_v3 \
    artifacts/confirmatory_character_panel_v1 \
    artifacts/epistemic_character_axes_v1 \
    artifacts/normative_boundary_axes_v1 \
    artifacts/educational_character_framework_v1 \
    artifacts/general_personality_bridge_v1 \
    artifacts/general_personality_content_archive_v1 \
    artifacts/affiliation_stability_pilot_v1 \
    artifacts/factorial_prompt_v1 \
    artifacts/factorial_analysis_v1 \
    artifacts/factorial_order_replication_v1 \
    artifacts/factorial_order_replication_analysis_v1 \
    artifacts/factorial_control_asymmetry_exploratory_v1 \
    artifacts/factorial_order_replication_control_asymmetry_exploratory_v1 \
    artifacts/factorial_paraphrase_replication_v1 \
    artifacts/factorial_paraphrase_replication_analysis_v1 \
    artifacts/factorial_detector_validation_v1 \
    artifacts/factorial_detector_validation_analysis_v1 \
    artifacts/policy_homogenization_v1 \
    artifacts/action_routing_trial_v1 \
    artifacts/action_routing_trial_analysis_v1 \
    artifacts/action_routing_surface_audit_v1 \
    artifacts/two_stage_routing_trial_v1 \
    artifacts/two_stage_routing_trial_analysis_v1 \
    artifacts/two_stage_selection_bias_audit_v1 \
    artifacts/learner_outcome_trial_planning_v1 \
    artifacts/submission_audit \
  --output artifacts/reproducibility_manifest.json

"$PY" scripts/verify_reproducibility_manifest.py \
  --root "$ROOT" \
  --manifest artifacts/reproducibility_manifest.json

"$PY" -m py_compile scripts/*.py
"$PY" -m pytest -q tests
git diff --check
