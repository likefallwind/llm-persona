#!/usr/bin/env python3
"""Apply the frozen semantic construct and manuscript decision rule.

This script deliberately converts every gate into a visible Boolean and keeps
failed dimensions in the output.  It does not choose favorable subsets of
tasks, models, judges, or prompt contrasts.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


CHANCE_ATTRIBUTION = 1 / 6
ACTION_ANCHORS = {
    # Expected sign for telling minus probing/focus.
    "help_directness": 1,
    "elicitation": -1,
}
PROMPT_ANCHORS = {
    # Expected sign for pedagogy-prompt minus generic-prompt.
    "help_directness": -1,
    "elicitation": 1,
}


def read_csv(directory: Path, name: str, **kwargs: object) -> pd.DataFrame:
    path = directory / name
    if not path.is_file():
        raise SystemExit(f"missing required decision input: {path}")
    return pd.read_csv(path, **kwargs)


def direction_holds(values: pd.Series, expected_sign: int) -> bool:
    numeric = pd.to_numeric(values, errors="coerce").dropna()
    return bool(len(numeric) and np.all(expected_sign * numeric.to_numpy(float) > 0))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--semantic-dir", type=Path, required=True)
    parser.add_argument("--leaveout-dir", type=Path, required=True)
    parser.add_argument("--scale-dir", type=Path, required=True)
    parser.add_argument("--objective-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    icc = read_csv(args.semantic_dir, "judge_icc.csv").set_index("dimension")
    scale = read_csv(args.scale_dir, "consensus_scale_diagnostics.csv").set_index("dimension")
    stability = read_csv(args.semantic_dir, "cross_task_stability.csv").set_index("dimension")
    variance = read_csv(args.semantic_dir, "model_variance_after_item_control.csv")
    attribution = read_csv(args.semantic_dir, "heldout_task_model_attribution.csv")
    quality = read_csv(args.semantic_dir, "quality_incremental_validity.csv")
    actions = read_csv(args.semantic_dir, "dialogue_act_semantic_contrasts.csv").set_index("dimension")
    family_bias = read_csv(args.semantic_dir, "judge_family_bias.csv")
    position = read_csv(args.semantic_dir, "candidate_position_slopes.csv")
    dimension_corr = read_csv(args.semantic_dir, "interdimension_spearman.csv", index_col=0)

    leaveout_summary = read_csv(args.leaveout_dir, "leaveout_summary.csv")
    leaveout_prompt = read_csv(args.leaveout_dir, "leaveout_prompt_effects.csv")
    prompt = read_csv(args.semantic_dir, "prompt_effects.csv")
    objective = read_csv(args.objective_dir, "fixed_item_associations.csv")

    dimensions = list(icc.index)
    if set(dimensions) != set(scale.index) or set(dimensions) != set(stability.index):
        raise SystemExit("dimension sets disagree across reliability, scale, and stability tables")

    profile_loo_min = float(leaveout_summary["profile_spearman_vs_full"].min())
    semantic_attribution = attribution[attribution["feature_set"] == "semantic"]
    if semantic_attribution.empty:
        raise SystemExit("semantic held-out-task attribution rows are missing")
    semantic_attribution_mean = float(semantic_attribution["accuracy"].mean())
    attribution_gate = semantic_attribution_mean > CHANCE_ATTRIBUTION

    quality_panel = quality[quality["feature_set"] == "transparent_plus_semantic"]
    if quality_panel.empty:
        raise SystemExit("transparent_plus_semantic quality rows are missing")
    quality_mean_gain = float(quality_panel["auc_gain_vs_transparent"].mean())
    quality_min_gain = float(quality_panel["auc_gain_vs_transparent"].min())
    quality_gate = quality_mean_gain > 0 and quality_min_gain >= 0

    rows = []
    for dimension in dimensions:
        dimension_variance = variance[variance["dimension"] == dimension]
        dimension_leaveout = leaveout_prompt[leaveout_prompt["dimension"] == dimension]
        dimension_prompt = prompt[prompt["dimension"] == dimension]
        dimension_objective = objective[
            (objective["dimension"] == dimension)
            & (objective["outcome"] == "diagnosis_correct")
        ]

        icc_gate = float(icc.loc[dimension, "icc_3_k"]) >= .60
        scale_gate = (
            float(scale.loc[dimension, "sd"]) >= .50
            and float(scale.loc[dimension, "floor_fraction"]) <= .80
            and float(scale.loc[dimension, "ceiling_fraction"]) <= .80
        )
        loo_profile_gate = profile_loo_min >= .70
        no_prompt_reversal = bool(
            len(dimension_leaveout) and not dimension_leaveout["sign_reversal"].astype(bool).any()
        )
        reliable = icc_gate and scale_gate and loo_profile_gate and no_prompt_reversal

        # Conservative transport rule: no benchmark is silently dropped.
        variance_gate = bool(
            len(dimension_variance)
            and (pd.to_numeric(dimension_variance["bootstrap_ci_low"], errors="coerce") > 0).all()
        )
        stability_gate = (
            float(stability.loc[dimension, "icc_3_1_across_tasks"]) >= .50
            or float(stability.loc[dimension, "median_pairwise_task_spearman"]) >= .50
        )
        signature = reliable and variance_gate and stability_gate and attribution_gate

        action_expected = ACTION_ANCHORS.get(dimension)
        action_gate = False
        if action_expected is not None and dimension in actions.index:
            action_gate = direction_holds(
                pd.Series([actions.loc[dimension, "telling_minus_probing_or_focus"]]),
                action_expected,
            )
        criterion_1 = quality_gate and action_gate

        prompt_expected = PROMPT_ANCHORS.get(dimension)
        prompt_direction_gate = False
        leaveout_direction_gate = False
        if prompt_expected is not None:
            prompt_direction_gate = direction_holds(dimension_prompt["mean_delta"], prompt_expected)
            leaveout_direction_gate = direction_holds(
                dimension_leaveout["leaveout_mean_delta"], prompt_expected
            )
        criterion_2 = prompt_direction_gate and leaveout_direction_gate

        criterion_3 = bool(
            len(dimension_objective)
            and (pd.to_numeric(dimension_objective["bh_q_within_outcome"], errors="coerce") < .05).any()
        )
        disposition = signature and (criterion_1 or criterion_2 or criterion_3)

        family_flag = bool(
            (family_bias.loc[family_bias["dimension"] == dimension, "own_minus_other_residual"].abs() > .25).any()
        )
        position_flag = bool(
            (position.loc[position["dimension"] == dimension, "max_minus_min_position_mean"].abs() > .25).any()
        )
        rows.append({
            "dimension": dimension,
            "icc_3_k": float(icc.loc[dimension, "icc_3_k"]),
            "icc_gate": icc_gate,
            "consensus_sd": float(scale.loc[dimension, "sd"]),
            "floor_fraction": float(scale.loc[dimension, "floor_fraction"]),
            "ceiling_fraction": float(scale.loc[dimension, "ceiling_fraction"]),
            "scale_gate": scale_gate,
            "panel_min_leaveout_profile_spearman": profile_loo_min,
            "leaveout_profile_gate": loo_profile_gate,
            "prompt_sign_reversals": int(dimension_leaveout["sign_reversal"].astype(bool).sum()),
            "no_prompt_reversal_gate": no_prompt_reversal,
            "reliable_semantic_measurement": reliable,
            "min_model_variance_bootstrap_ci_low": float(dimension_variance["bootstrap_ci_low"].min()),
            "all_benchmarks_variance_gate": variance_gate,
            "cross_task_icc_3_1": float(stability.loc[dimension, "icc_3_1_across_tasks"]),
            "median_pairwise_task_spearman": float(stability.loc[dimension, "median_pairwise_task_spearman"]),
            "stability_gate": stability_gate,
            "panel_semantic_attribution_accuracy": semantic_attribution_mean,
            "panel_attribution_gate": attribution_gate,
            "cross_task_semantic_signature": signature,
            "quality_panel_mean_auc_gain": quality_mean_gain,
            "quality_panel_min_fold_auc_gain": quality_min_gain,
            "quality_gate": quality_gate,
            "anchored_action_gate": action_gate,
            "criterion_1_quality_and_action": criterion_1,
            "anchored_prompt_full_gate": prompt_direction_gate,
            "anchored_prompt_leaveout_gate": leaveout_direction_gate,
            "criterion_2_prompt_action_convergence": criterion_2,
            "criterion_3_human_gold_diagnosis": criterion_3,
            "validated_pedagogical_disposition": disposition,
            "self_family_bias_flag": family_flag,
            "slate_position_flag": position_flag,
        })

    decisions = pd.DataFrame(rows)
    disposition_dimensions = decisions.loc[
        decisions["validated_pedagogical_disposition"], "dimension"
    ].tolist()
    thesis = "pedagogical_dispositions" if len(disposition_dimensions) >= 2 else "pedagogical_policy_signatures"
    anchored = decisions[decisions["dimension"].isin(PROMPT_ANCHORS)]
    contextual_oversteering = bool(
        (anchored["reliable_semantic_measurement"]
         & anchored["criterion_2_prompt_action_convergence"]).any()
    )
    summary = {
        "dimensions": len(decisions),
        "reliable_dimensions": decisions.loc[decisions["reliable_semantic_measurement"], "dimension"].tolist(),
        "signature_dimensions": decisions.loc[decisions["cross_task_semantic_signature"], "dimension"].tolist(),
        "validated_disposition_dimensions": disposition_dimensions,
        "recommended_thesis": thesis,
        "contextual_oversteering_semantic_claim_eligible": contextual_oversteering,
        "main_conference_finite_panel_claim_eligible": bool(decisions["reliable_semantic_measurement"].any()),
        "broad_learning_effectiveness_claim_eligible": False,
        "broad_learning_effectiveness_blocker": "No prospective learner study or independently validated simulator with objective pre/post outcomes.",
    }

    decisions.to_csv(args.output_dir / "dimension_decisions.csv", index=False)
    (args.output_dir / "submission_decision.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    report = "\n".join([
        "# Frozen semantic submission decision", "",
        f"**Recommended thesis:** `{thesis}`", "",
        f"Validated disposition dimensions: {', '.join(disposition_dimensions) if disposition_dimensions else 'none'}.", "",
        decisions.to_markdown(index=False, floatfmt=".3f"), "",
        "The broad learning-effectiveness claim is ineligible by construction: this panel contains no prospective objective learner outcome. Bias flags are reported but do not erase otherwise valid rows.", "",
    ])
    (args.output_dir / "submission_decision_report.md").write_text(report, encoding="utf-8")
    print(args.output_dir / "submission_decision_report.md")


if __name__ == "__main__":
    main()
