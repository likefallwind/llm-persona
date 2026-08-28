#!/usr/bin/env python3
"""Fail when headline manuscript claims drift from regenerated artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd


def macro_metric(frame: pd.DataFrame, feature_set: str, metric: str = "accuracy") -> float:
    rows = frame[frame["feature_set"] == feature_set]
    return float(rows[metric].mean())


def rounded(value: float, digits: int = 3) -> float:
    return round(float(value), digits)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/claim_verification"))
    args = parser.parse_args()
    root = args.root.resolve()
    output_dir = (root / args.output_dir).resolve() if not args.output_dir.is_absolute() else args.output_dir
    checks: list[dict[str, Any]] = []

    def check(name: str, observed: Any, expected: Any, predicate: Callable[[Any, Any], bool] = lambda a, b: a == b) -> None:
        passed = bool(predicate(observed, expected))
        checks.append({"claim": name, "observed": observed, "expected": expected, "passed": passed})

    with (root / "artifacts/inventory/corpus_inventory.json").open(encoding="utf-8") as handle:
        inventory = json.load(handle)
    common_items = sum(row["common_success_items_core_six"] for row in inventory["benchmarks"])
    check("core common benchmark-item IDs", common_items, 47321)
    check("core response count implied by paired panel", common_items * len(inventory["core_models"]), 283926)

    bridge_dir = root / "artifacts/general_personality_bridge_v1"
    bridge_decision = json.loads((bridge_dir / "decision.json").read_text())
    check("general-personality bridge included responses", bridge_decision["corpus"]["included_paired_responses"], 123468)
    check("general-personality bridge promising candidates", bridge_decision["promising_candidates"], [])
    check(
        "general-personality bridge verdict",
        bridge_decision["verdict"],
        "existing_archive_does_not_yet_support_general_personality_bridge",
    )
    bridge_stability = pd.read_csv(bridge_dir / "cross_task_stability.csv")
    non_tutoring_bridge = bridge_stability[bridge_stability["pool"] == "non_tutoring"].set_index("axis")
    check("general bridge organizational-style ICC", rounded(non_tutoring_bridge.loc["organizational_style", "icc3_1"]), 0.601)
    check(
        "general bridge organizational-style median task rho",
        rounded(non_tutoring_bridge.loc["organizational_style", "median_pairwise_spearman"]),
        0.771,
    )
    bridge_transport = pd.read_csv(bridge_dir / "cross_domain_transport.csv")
    bridge_transport = bridge_transport[
        (bridge_transport["left_pool"] == "non_tutoring")
        & (bridge_transport["right_pool"] == "default_tutoring")
    ].set_index("axis")
    check("general bridge communal transport", rounded(bridge_transport.loc["communal_expression", "spearman"]), 0.829)
    check("general bridge dialogic transport", rounded(bridge_transport.loc["dialogic_engagement", "spearman"]), 0.657)

    content_dir = root / "artifacts/general_personality_content_archive_v1"
    content_decision = json.loads((content_dir / "decision.json").read_text())
    check("general-personality constructs audited", content_decision["constructs_audited"], 22)
    check("general-personality partial candidates", content_decision["partial_behavioral_candidates"], 9)
    check("general-personality unidentifiable constructs", content_decision["not_identifiable"], 13)
    check("validated general-personality constructs", content_decision["validated_general_personality_constructs"], [])
    check(
        "general-personality targeted pilot priority",
        content_decision["purpose_built_pilot_priorities"],
        ["agreeableness_affiliation_and_benevolence"],
    )
    content_tests = pd.read_csv(content_dir / "construct_bridge_tests.csv")
    diligence = content_tests[
        (content_tests["construct_cluster"] == "conscientiousness_diligence")
        & (content_tests["right_indicator"] == "ifeval_accuracy")
    ].iloc[0]
    check("organization versus IFEval rho", rounded(diligence["spearman"]), -0.886)
    check("organization versus IFEval exact p", rounded(diligence["exact_two_sided_p"]), 0.035)

    affiliation_dir = root / "artifacts/affiliation_stability_pilot_v1/analysis"
    affiliation = json.loads((affiliation_dir / "decision.json").read_text())
    check("affiliation generator calls", affiliation["coverage"]["generator_calls"], 280)
    check("affiliation judge calls", affiliation["coverage"]["judge_calls"], 144)
    check("affiliation primary ICC3k", rounded(affiliation["estimates"]["primary_icc3_k"]), 0.931)
    check("affiliation cross-domain rho", rounded(affiliation["estimates"]["default_cross_domain_spearman"]), 0.900)
    check("affiliation irrelevant-context rho", rounded(affiliation["estimates"]["default_to_irrelevant_spearman"]), 0.718)
    check("affiliation high-low effect", rounded(affiliation["estimates"]["high_minus_low_mean"]), 1.689)
    check("affiliation directional models", affiliation["estimates"]["positive_high_low_models"], 5)
    check("affiliation self-report behavior rho", rounded(affiliation["estimates"]["self_report_to_open_spearman"]), -0.200)
    check("affiliation forced-choice ceiling", affiliation["estimates"]["scenario_choice_to_open_spearman"], None)
    check("stable default affiliation supported", affiliation["stable_default_affiliation_supported"], True)
    check("general personality convergence rejected", affiliation["general_personality_convergence_supported"], False)

    pilot = pd.read_csv(root / "artifacts/pilot/behavior_features.csv", dtype={"item_id": str}, low_memory=False)
    negative = pd.read_csv(root / "artifacts/negative_controls/behavior_features.csv", dtype={"item_id": str}, low_memory=False)
    extended = pd.read_csv(root / "artifacts/extended_panel/behavior_features.csv", dtype={"item_id": str}, low_memory=False)
    check("primary teaching response rows", len(pilot), 31638)
    check("negative-control response rows", len(negative), 57516)
    check("extended MathDial response rows", len(extended), 26586)

    pilot_cls = pd.read_csv(root / "artifacts/pilot/classification.csv")
    negative_cls = pd.read_csv(root / "artifacts/negative_controls/classification.csv")
    check("primary held-out-family macro policy attribution", rounded(macro_metric(pilot_cls, "policy")), 0.242)
    check("primary held-out-family macro all-feature attribution", rounded(macro_metric(pilot_cls, "surface_plus_policy")), 0.251)
    check("negative-control macro all-feature attribution", rounded(macro_metric(negative_cls, "surface_plus_policy")), 0.372)

    mantel = pd.read_csv(root / "artifacts/discriminant_validity/policy_geometry_mantel.csv").iloc[0]
    check("cross-domain policy-geometry Mantel r", rounded(mantel["distance_matrix_correlation"]), 0.296)
    check("cross-domain policy-geometry exact p", rounded(mantel["exact_two_sided_p"]), 0.307)

    convergence = pd.read_csv(root / "artifacts/extended_analysis/prompt_convergence.csv").iloc[0]
    check("pedagogy/generic profile dispersion ratio", rounded(convergence["dispersion_ratio_pedagogy_over_generic"]), 0.763)
    check("dispersion bootstrap lower bound", rounded(convergence["bootstrap_ci_low"]), 0.738)
    check("dispersion bootstrap upper bound", rounded(convergence["bootstrap_ci_high"]), 0.794)

    identity = pd.read_csv(root / "artifacts/judge_robustness/response_identity_audit.csv")
    check("identical responses in judge swap", int(identity["common_items"].sum()), 14770)
    check("judge-swap response mismatches", int(identity["response_mismatches"].sum()), 0)
    quality = pd.read_csv(root / "artifacts/judge_robustness/quality_prediction.csv")
    pivot = quality.pivot(index=["judge", "held_out_model"], columns="feature_set", values="roc_auc")
    deltas = pivot["item_plus_policy_length"] - pivot["task_item"]
    for judge, expected in (("deepseek-v4-flash", 0.031), ("minimax-m3", 0.023)):
        values = deltas.xs(judge, level="judge")
        check(f"{judge} mean policy AUC increment", rounded(values.mean()), expected)
        check(f"{judge} positive held-out-model policy folds", int((values > 0).sum()), len(values))

    calibration = pd.read_csv(root / "artifacts/judge_human_calibration/human_preference_agreement.csv")
    calibration = calibration.set_index("judge_or_ensemble")
    check("best judge expert-pair agreement", rounded(calibration.loc["MiniMax-M3", "agreement"]), 0.844)
    check("majority minus best CI contains zero", True, True, lambda _a, _b: (
        calibration.loc["majority_minus_MiniMax-M3", "cluster_bootstrap_ci_low"] < 0
        < calibration.loc["majority_minus_MiniMax-M3", "cluster_bootstrap_ci_high"]
    ))

    effects = pd.read_csv(root / "artifacts/dialogue_act_validity/effect_robustness.csv")
    check("action-classifier contrasts with all nine models positive", int((effects["positive_models"] == 9).sum()), len(effects))
    act_match = pd.read_csv(root / "artifacts/dialogue_act_validity/match_by_target_act.csv")
    telling = act_match[(act_match["family"] == "standard") & (act_match["target_act"] == "telling")]
    telling_pivot = telling.pivot(index="classifier_variant", columns="arm", values="mean")
    check("telling match drops for every classifier", int((telling_pivot["pedagogy"] < telling_pivot["generic"]).sum()), 3)
    check("telling generic match range", [rounded(telling_pivot["generic"].min()), rounded(telling_pivot["generic"].max())], [0.394, 0.442])
    check("telling pedagogy match range", [rounded(telling_pivot["pedagogy"].min()), rounded(telling_pivot["pedagogy"].max())], [0.111, 0.125])

    long_rows = pd.read_csv(root / "artifacts/longtutor_objective_validity/matched_objective_outcomes.csv")
    check("LongTutor matched model-history rows", len(long_rows), 6000)
    check("LongTutor unique histories", long_rows["item_id"].nunique(), 1000)
    associations = pd.read_csv(root / "artifacts/longtutor_objective_validity/within_model_associations.csv")
    teaching_quality = associations[(associations["objective_outcome"] == "diagnosis_correct") & (associations["teaching_measure"] == "teaching_quality")]
    strategy = associations[(associations["objective_outcome"] == "diagnosis_correct") & (associations["teaching_measure"] == "strategy_alignment")]
    evidence = associations[(associations["objective_outcome"] == "evidence_accuracy") & (associations["teaching_measure"] == "teaching_quality")]
    check("mean diagnosis-teaching-quality Spearman", rounded(teaching_quality["spearman"].mean()), 0.173)
    check("mean diagnosis-strategy-alignment Spearman", rounded(strategy["spearman"].mean()), 0.208)
    check("mean evidence-teaching-quality Spearman", rounded(evidence["spearman"].mean()), -0.010)
    heldout = pd.read_csv(root / "artifacts/longtutor_objective_validity/heldout_model_prediction.csv")
    diagnosis_auc = heldout[heldout["outcome"] == "diagnosis_correct"].groupby("predictors")["auc"].mean()
    evidence_rmse = heldout[heldout["outcome"] == "evidence_accuracy"].groupby("predictors")["rmse"].mean()
    check("LongTutor item-only diagnosis AUC", rounded(diagnosis_auc["item_only"]), 0.822)
    check("LongTutor teaching-dimensions diagnosis AUC", rounded(diagnosis_auc["teaching_dimensions"]), 0.816)
    check("LongTutor teaching-mean diagnosis AUC", rounded(diagnosis_auc["teaching_mean"]), 0.817)
    check("LongTutor evidence RMSE invariant at reported precision", sorted({rounded(value) for value in evidence_rmse}), [0.187])

    semantic_coverage = json.loads((root / "artifacts/semantic_panel/coverage.json").read_text())
    check("semantic analyzed batches", semantic_coverage["analyzed_batches"], 358)
    check("semantic eligible annotations", semantic_coverage["expected"], 1074)
    check("semantic successful annotations", semantic_coverage["success"], 1074)
    consensus = pd.read_csv(root / "artifacts/semantic_panel/response_consensus.csv")
    response_units = consensus[["benchmark", "item_id", "model", "response_sha256"]].drop_duplicates()
    check("semantic response units", len(response_units), 2148)
    check("semantic consensus rows have three judges", int((consensus["judge_count"] == 3).sum()), len(consensus))

    semantic_decision = json.loads((root / "artifacts/submission_decision/submission_decision.json").read_text())
    check("reliable semantic dimensions", semantic_decision["reliable_dimensions"], ["help_directness", "elicitation", "cognitive_load"])
    check("cross-task signature dimensions", semantic_decision["signature_dimensions"], ["help_directness", "cognitive_load"])
    check("validated disposition dimensions", semantic_decision["validated_disposition_dimensions"], ["help_directness"])
    check("frozen recommended thesis", semantic_decision["recommended_thesis"], "pedagogical_policy_signatures")

    semantic_attribution = pd.read_csv(root / "artifacts/semantic_panel/heldout_task_model_attribution.csv")
    semantic_attribution = semantic_attribution.groupby("feature_set")["accuracy"].mean()
    check("semantic held-out-task attribution", rounded(semantic_attribution["semantic"]), 0.322)
    check("combined held-out-task attribution", rounded(semantic_attribution["transparent_plus_semantic"]), 0.391)
    leaveout = pd.read_csv(root / "artifacts/semantic_leaveout/leaveout_summary.csv")
    check("minimum leave-one-judge profile Spearman", rounded(leaveout["profile_spearman_vs_full"].min()), 0.959)

    semantic_acts = pd.read_csv(root / "artifacts/semantic_panel/dialogue_act_semantic_contrasts.csv").set_index("dimension")
    check("telling help-directness contrast", rounded(semantic_acts.loc["help_directness", "telling_minus_probing_or_focus"]), 1.360)
    semantic_effects = pd.read_csv(root / "artifacts/semantic_panel/prompt_effects.csv")
    semantic_effects = semantic_effects.groupby(["task", "dimension"])["mean_delta"].mean()
    check(
        "semantic prompt deltas standard",
        [rounded(semantic_effects[("mathdial_standard", dimension)]) for dimension in ("help_directness", "elicitation", "cognitive_load")],
        [-1.709, 2.470, -0.759],
    )
    check(
        "semantic prompt deltas hard",
        [rounded(semantic_effects[("mathdial_hard", dimension)]) for dimension in ("help_directness", "elicitation", "cognitive_load")],
        [-1.542, 2.171, -0.721],
    )

    prompt_signature_dir = root / "artifacts/prompt_contingent_signatures_v1"
    prompt_signature_decision = json.loads((prompt_signature_dir / "decision.json").read_text())
    check(
        "prompt-contingent signature verdict",
        prompt_signature_decision["verdict"],
        "prompt_contingent_policy_signatures_supported",
    )
    check(
        "prompt-contingent signature decision gates",
        all(prompt_signature_decision["checks"].values()),
        True,
    )
    check(
        "headroom-adjusted replicated elasticity dimensions",
        prompt_signature_decision["replicated_semantic_elasticity_dimensions"],
        ["elicitation", "help_directness"],
    )

    prompt_variance = pd.read_csv(prompt_signature_dir / "variance_decomposition.csv")
    reliable_prompt_dimensions = ["cognitive_load", "elicitation", "help_directness"]
    prompt_variance = prompt_variance[prompt_variance["dimension"].isin(reliable_prompt_dimensions)]
    for task, expected in (
        ("mathdial_standard", [3.987, 7.532]),
        ("mathdial_hard", [4.837, 6.685]),
    ):
        ratios = prompt_variance[prompt_variance["task"] == task]["prompt_to_model_ss_ratio"]
        check(
            f"{task} reliable-dimension prompt/model SS ratio range",
            [rounded(ratios.min()), rounded(ratios.max())],
            expected,
        )

    prompt_scale = pd.read_csv(prompt_signature_dir / "prompt_vs_model_scale.csv")
    prompt_scale = prompt_scale[prompt_scale["dimension"].isin(reliable_prompt_dimensions)]
    for task, expected in (
        ("mathdial_standard", [1.000, 1.148]),
        ("mathdial_hard", [0.848, 1.011]),
    ):
        ratios = prompt_scale[prompt_scale["task"] == task]["absolute_prompt_over_baseline_range"]
        check(
            f"{task} reliable-dimension prompt/default-range ratio",
            [rounded(ratios.min()), rounded(ratios.max())],
            expected,
        )

    prompt_attribution = pd.read_csv(prompt_signature_dir / "cross_prompt_model_attribution.csv")
    pooled = prompt_attribution[
        (prompt_attribution["train_task"] == "ALL")
        & (prompt_attribution["test_task"] == "ALL")
    ]
    check(
        "pooled cross-prompt identity accuracy",
        [rounded(value) for value in pooled["accuracy"]],
        [0.301, 0.297],
    )
    check(
        "pooled cross-prompt identity lower bounds exceed chance",
        bool((pooled["bootstrap_ci_low"] > pooled["chance_accuracy"]).all()),
        True,
    )
    cross_task = prompt_attribution[
        (prompt_attribution["train_task"] != "ALL")
        & (prompt_attribution["test_task"] != "ALL")
        & (prompt_attribution["train_task"] != prompt_attribution["test_task"])
    ]
    check("cross-task cross-prompt transfer directions", len(cross_task), 4)
    check(
        "cross-task cross-prompt lower bounds exceed chance",
        bool((cross_task["bootstrap_ci_low"] > cross_task["chance_accuracy"]).all()),
        True,
    )

    character_dir = root / "artifacts/confirmatory_character_panel_v1/formal"
    character_decision = json.loads((character_dir / "decision.json").read_text())
    character_coverage = character_decision["coverage"]
    check("character formal judge calls", character_coverage["successful"], 1160)
    check("character formal missing or failed calls", character_coverage["missing_or_failed"], 0)
    character_rows = {row["dimension"]: row for row in character_decision["classification"]}
    check(
        "character formal classifications",
        {dimension: row["classification_status"] for dimension, row in character_rows.items()},
        {
            "instructional_agency": "formal_signature_not_supported",
            "relational_communion": "formal_signature_not_supported",
            "next_step_actionability": "formal_signature_not_supported",
        },
    )
    check(
        "agency pilot failure remains binding",
        character_rows["instructional_agency"]["measurement_gates"]["pilot_measurement_pass"],
        False,
    )
    character_icc = pd.read_csv(character_dir / "judge_icc.csv").set_index("dimension")
    check(
        "character formal ICC(3,k)",
        [rounded(character_icc.loc[dimension, "icc_3_k"]) for dimension in (
            "instructional_agency", "relational_communion", "next_step_actionability"
        )],
        [0.900, 0.945, 0.871],
    )
    character_profiles = pd.read_csv(character_dir / "judge_model_profile_agreement.csv")
    minimum_profile = character_profiles.groupby("dimension")["model_profile_spearman"].min()
    check("formal actionability minimum judge-profile rho", rounded(minimum_profile["next_step_actionability"]), 0.600)
    character_stability = pd.read_csv(character_dir / "cross_task_stability.csv").set_index("dimension")
    check(
        "formal actionability cross-task stability",
        [rounded(character_stability.loc["next_step_actionability", column]) for column in (
            "icc_3_1", "median_pairwise_spearman"
        )],
        [-0.111, -0.771],
    )
    character_old = pd.read_csv(character_dir / "old_scale_convergence.csv")
    communion_warmth = character_old[
        (character_old["new_dimension"] == "relational_communion")
        & (character_old["old_dimension"] == "affective_warmth")
    ].iloc[0]
    check("formal communion convergence with warmth", rounded(communion_warmth["spearman"]), 0.805)
    character_prompt = pd.read_csv(character_dir / "prompt_effect_summary.csv").set_index(["task", "dimension"])
    for task, expected in (
        ("mathdial_standard", [-0.995, 1.047, 0.679, 0.856]),
        ("mathdial_hard", [-1.039, 0.880, 0.942, 0.787]),
    ):
        check(
            f"{task} confirmatory character prompt effects and scale ratios",
            [
                rounded(character_prompt.loc[(task, "instructional_agency"), "mean_prompt_delta"]),
                rounded(character_prompt.loc[(task, "next_step_actionability"), "mean_prompt_delta"]),
                rounded(character_prompt.loc[(task, "instructional_agency"), "absolute_prompt_over_default_model_range"]),
                rounded(character_prompt.loc[(task, "next_step_actionability"), "absolute_prompt_over_default_model_range"]),
            ],
            expected,
        )
    family_decision = json.loads((character_dir / "judge_family_sensitivity.json").read_text())
    family_rows = {row["dimension"]: row for row in family_decision["classification"]}
    check("formal actionability judge-family robust", family_rows["next_step_actionability"]["judge_family_robust"], False)
    quality_boundary = pd.read_csv(character_dir / "quality_summary.csv").set_index("feature_set")
    check(
        "all confirmatory scores mean quality AUC gain",
        rounded(quality_boundary.loc["transparent_plus_all_confirmatory", "mean_auc_gain_vs_transparent"], 4),
        0.0035,
    )

    character_framework = json.loads(
        (root / "artifacts/educational_character_framework_v1/decision.json").read_text()
    )
    check(
        "educational character supported axes",
        character_framework["supported_axes"],
        ["assistance_directness", "epistemic_commitment"],
    )
    check("educational character exploratory axes", character_framework["exploratory_axes"], ["instructional_agency"])
    check(
        "educational character rejected axes",
        character_framework["rejected_or_unsupported_axes"],
        ["relational_communion", "next_step_actionability", "learner_contingency"],
    )

    semantic_objective = pd.read_csv(root / "artifacts/semantic_objective_validity/heldout_model_objective_prediction.csv")
    semantic_objective = semantic_objective[semantic_objective["outcome"] == "diagnosis_correct"].groupby("feature_set")["auc"].mean()
    check("semantic diagnosis AUC item-only", rounded(semantic_objective["item_only"]), 0.775)
    check("semantic diagnosis AUC all dimensions", rounded(semantic_objective["all_semantic"]), 0.744)

    factorial = json.loads(
        (root / "artifacts/factorial_analysis_v1/factorial_analysis_report.json").read_text()
    )
    factorial_decision = factorial["decision"]
    check("prospective factorial response rows", factorial["response_rows"], 2560)
    check(
        "parent factorial target effects",
        [
            rounded(factorial_decision["factor_results"][factor]["target_mean_difference"])
            for factor in ("question_policy", "answer_policy", "tone_policy")
        ],
        [0.773, 0.895, 0.595],
    )
    check(
        "parent factorial selective factors",
        [
            factorial_decision["factor_results"][factor]["selective"]
            for factor in ("question_policy", "answer_policy", "tone_policy")
        ],
        [True, True, True],
    )
    check(
        "parent learner-request gates",
        [
            factorial_decision["learner_need"]["question_pass"],
            factorial_decision["learner_need"]["reveal_pass"],
        ],
        [False, False],
    )

    replication = json.loads(
        (root / "artifacts/factorial_order_replication_analysis_v1/order_replication_report.json").read_text()
    )
    replication_decision = replication["replication_decision"]
    joint_decision = replication["joint_order_robustness_decision"]
    check("order-replication response rows", replication["replication_rows"], 640)
    check("order-replication exact block balance", replication["request_order_block_balance_pass"], True)
    check(
        "replication factorial target effects",
        [
            rounded(replication_decision["factor_results"][factor]["target_mean_difference"])
            for factor in ("question_policy", "answer_policy", "tone_policy")
        ],
        [0.809, 0.922, 0.550],
    )
    check(
        "joint order-robust factors",
        [
            joint_decision["factor_results"][factor]["order_robust"]
            for factor in ("question_policy", "answer_policy", "tone_policy")
        ],
        [True, True, True],
    )
    check(
        "order-robust learner-request gates",
        [
            joint_decision["learner_need"]["question_order_robust"],
            joint_decision["learner_need"]["reveal_order_robust"],
        ],
        [False, False],
    )

    detector_validation = json.loads(
        (root / "artifacts/factorial_detector_validation_analysis_v1/detector_validation_report.json").read_text()
    )
    check("factorial detector validation response units", detector_validation["response_units"], 480)
    check("factorial detector validation annotations", detector_validation["annotations"], 144)
    check("factorial detector validation batches", detector_validation["batches"], 48)
    detector_results = detector_validation["detectors"]
    check(
        "factorial detector validation decisions",
        [
            detector_results[metric]["validated"]
            for metric in ("question_first", "answer_reveal_correct", "warmth_marker")
        ],
        [True, True, False],
    )
    check(
        "factorial detector balanced accuracies",
        [
            rounded(detector_results[metric]["balanced_accuracy"])
            for metric in ("question_first", "answer_reveal_correct", "warmth_marker")
        ],
        [1.000, 0.996, 0.818],
    )
    check(
        "factorial detector kappa values",
        [
            rounded(detector_results[metric]["cohen_kappa"])
            for metric in ("question_first", "answer_reveal_correct", "warmth_marker")
        ],
        [1.000, 0.992, 0.631],
    )

    learner_trial = json.loads(
        (root / "artifacts/learner_outcome_trial_planning_v1/power_report.json").read_text()
    )
    check(
        "learner-outcome trial remains planning only",
        learner_trial["status"],
        "planning_only_not_preregistered_not_started",
    )
    check("learner-outcome conservative power plan passes", learner_trial["passed"], True)
    check(
        "learner-outcome planned sample and cells",
        [learner_trial["planned_total"], learner_trial["planned_cells"], learner_trial["planned_per_cell"]],
        [3300, 12, 275],
    )

    submission_audit = json.loads(
        (root / "artifacts/submission_audit/submission_audit.json").read_text()
    )
    check("anonymous ACL submission audit", submission_audit["passed"], True)
    check("ACL PDF page count", submission_audit["pages"], 10)
    check(
        "ACL PDF embedded fonts and identity boundary",
        [
            submission_audit["checks"]["all_fonts_embedded"],
            submission_audit["checks"]["no_type_three_fonts"],
            submission_audit["checks"]["no_identity_or_local_path_hits"],
        ],
        [True, True, True],
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    result = {
        "schema_version": 1,
        "passed": all(row["passed"] for row in checks),
        "checks": checks,
    }
    (output_dir / "claim_verification.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    lines = ["# Release claim verification", "", f"Overall: **{'PASS' if result['passed'] else 'FAIL'}**", "", "| Claim | Observed | Expected | Pass |", "|---|---:|---:|:---:|"]
    for row in checks:
        lines.append(f"| {row['claim']} | `{row['observed']}` | `{row['expected']}` | {'yes' if row['passed'] else 'NO'} |")
    (output_dir / "claim_verification.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    failed = [row for row in checks if not row["passed"]]
    if failed:
        for row in failed:
            print(f"FAIL {row['claim']}: observed={row['observed']!r} expected={row['expected']!r}")
        raise SystemExit(1)
    print(f"PASS: {len(checks)} release claims verified")


if __name__ == "__main__":
    main()
