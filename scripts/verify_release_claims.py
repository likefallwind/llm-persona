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

    semantic_objective = pd.read_csv(root / "artifacts/semantic_objective_validity/heldout_model_objective_prediction.csv")
    semantic_objective = semantic_objective[semantic_objective["outcome"] == "diagnosis_correct"].groupby("feature_set")["auc"].mean()
    check("semantic diagnosis AUC item-only", rounded(semantic_objective["item_only"]), 0.775)
    check("semantic diagnosis AUC all dimensions", rounded(semantic_objective["all_semantic"]), 0.744)

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
