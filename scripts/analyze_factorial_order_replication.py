#!/usr/bin/env python3
"""Compare the parent factorial panel with its order-randomized replication."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

from analyze_factorial_prompt_panel import (
    TARGET_METRICS,
    build_metric_frame,
    conditional_need_effects,
    effect_tables,
    evaluate_gates,
    interaction_tables,
    learner_need_effects,
    load_jsonl,
)


def only_expected_rows(
    rows: list[dict[str, Any]], sample_ids: set[str], models: set[str],
) -> list[dict[str, Any]]:
    return [
        row for row in rows
        if str(row.get("sample_id", "")) in sample_ids
        and str(row.get("model", "")) in models
    ]


def target_comparison(
    primary_subset_effects: pd.DataFrame, replication_effects: pd.DataFrame,
) -> pd.DataFrame:
    rows = []
    groups = sorted(set(primary_subset_effects.group) & set(replication_effects.group))
    for group in groups:
        for factor, metric in TARGET_METRICS.items():
            left = primary_subset_effects[
                (primary_subset_effects.group == group)
                & (primary_subset_effects.factor == factor)
                & (primary_subset_effects.metric == metric)
            ]
            right = replication_effects[
                (replication_effects.group == group)
                & (replication_effects.factor == factor)
                & (replication_effects.metric == metric)
            ]
            if len(left) != 1 or len(right) != 1:
                raise RuntimeError(f"missing target comparison row: {group}|{factor}|{metric}")
            primary = float(left.mean_difference.iloc[0])
            replication = float(right.mean_difference.iloc[0])
            rows.append({
                "group": group,
                "factor": factor,
                "metric": metric,
                "primary_subset_mean_difference": primary,
                "replication_mean_difference": replication,
                "absolute_difference": abs(replication - primary),
                "positive_in_both": primary > 0 and replication > 0,
            })
    return pd.DataFrame(rows)


def joint_decision(
    primary: dict[str, Any], replication: dict[str, Any], comparison: pd.DataFrame,
) -> dict[str, Any]:
    factors = {}
    for factor in TARGET_METRICS:
        factor_rows = comparison[comparison.factor == factor]
        positive_both = bool(factor_rows.positive_in_both.all()) and len(factor_rows) > 0
        main_result = primary["factor_results"][factor]
        replication_result = replication["factor_results"][factor]
        factors[factor] = {
            "primary_selective": bool(main_result["selective"]),
            "replication_selective": bool(replication_result["selective"]),
            "positive_in_parent_subset_and_replication_every_group": positive_both,
            "order_robust": bool(
                main_result["selective"] and replication_result["selective"] and positive_both
            ),
        }
    primary_need = primary["learner_need"]
    replication_need = replication["learner_need"]
    return {
        "factor_results": factors,
        "learner_need": {
            "reveal_order_robust": bool(
                primary_need["reveal_pass"] and replication_need["reveal_pass"]
            ),
            "question_order_robust": bool(
                primary_need["question_pass"] and replication_need["question_pass"]
            ),
        },
        "rule": "replication is downgrade-only and cannot rescue a failed parent gate",
    }


def validate_queue_ranks(
    rows: list[dict[str, Any]], models: list[str], samples_per_model: int,
    order_plan: list[dict[str, Any]],
) -> pd.DataFrame:
    successful = [
        row for row in rows
        if isinstance(row.get("response"), str) and row["response"].strip()
        and not row.get("error")
    ]
    latest: dict[tuple[str, str], dict[str, Any]] = {}
    for row in successful:
        latest[(str(row["sample_id"]), str(row["model"]))] = row
    planned = {
        (str(row["sample_id"]), str(row["model"])): int(row["queue_rank"])
        for row in order_plan
    }
    if len(planned) != samples_per_model * len(models):
        raise RuntimeError("frozen order plan has the wrong number of unique rows")
    records = []
    for model in models:
        model_rows = [row for (_, row_model), row in latest.items() if row_model == model]
        ranks = {int(row["replication_queue_rank"]) for row in model_rows}
        if ranks != set(range(samples_per_model)):
            raise RuntimeError(f"invalid or incomplete queue ranks for {model}")
        for row in model_rows:
            key = (str(row["sample_id"]), model)
            if planned.get(key) != int(row["replication_queue_rank"]):
                raise RuntimeError(f"observed queue rank differs from plan for {key}")
            records.append({
                "model": model,
                "sample_id": row["sample_id"],
                "replication_queue_rank": int(row["replication_queue_rank"]),
            })
    return pd.DataFrame(records)


def validate_factorial_blocks(frame: pd.DataFrame) -> bool:
    audited = frame.copy()
    audited["replication_block_index"] = audited.replication_queue_rank // 16
    cell_columns = [
        "learner_need", "question_policy", "answer_policy", "tone_policy",
    ]
    counts = audited.groupby(
        ["model", "replication_block_index", *cell_columns], sort=True,
    ).size()
    block_sizes = audited.groupby(["model", "replication_block_index"]).size()
    if set(counts) != {1} or set(block_sizes) != {16} or len(block_sizes) != 40:
        raise RuntimeError("replication request blocks are not exactly factorial-balanced")
    return True


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--parent-spec", type=Path, default=Path("data/factorial_prompt_spec_v1.json"),
    )
    parser.add_argument(
        "--replication-spec", type=Path,
        default=Path("data/factorial_order_replication_spec_v1.json"),
    )
    parser.add_argument(
        "--parent-manifest", type=Path,
        default=Path("artifacts/factorial_prompt_v1/sample_manifest.jsonl"),
    )
    parser.add_argument(
        "--replication-manifest", type=Path,
        default=Path("artifacts/factorial_order_replication_v1/sample_manifest.jsonl"),
    )
    parser.add_argument(
        "--order-plan", type=Path,
        default=Path("artifacts/factorial_order_replication_v1/request_order_plan.jsonl"),
    )
    parser.add_argument(
        "--parent-responses", type=Path,
        default=Path("artifacts/factorial_prompt_v1/run/responses.jsonl"),
    )
    parser.add_argument(
        "--replication-responses", type=Path,
        default=Path("artifacts/factorial_order_replication_v1/run/responses.jsonl"),
    )
    parser.add_argument(
        "--output-dir", type=Path,
        default=Path("artifacts/factorial_order_replication_analysis_v1"),
    )
    parser.add_argument("--bootstrap-reps", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=20260821)
    args = parser.parse_args()

    parent_spec = json.loads(args.parent_spec.read_text(encoding="utf-8"))
    replication_spec = json.loads(args.replication_spec.read_text(encoding="utf-8"))
    analysis_spec = {
        **parent_spec,
        "models": list(replication_spec["models"]),
        "claim_gates": dict(replication_spec["claim_gates"]),
    }
    parent_manifest = load_jsonl(args.parent_manifest)
    subset_manifest = load_jsonl(args.replication_manifest)
    order_plan = load_jsonl(args.order_plan)
    parent_rows = load_jsonl(args.parent_responses)
    replication_rows = load_jsonl(args.replication_responses)
    models = set(analysis_spec["models"])
    subset_ids = {str(row["sample_id"]) for row in subset_manifest}

    parent_frame = build_metric_frame(analysis_spec, parent_manifest, parent_rows)
    parent_subset_frame = build_metric_frame(
        analysis_spec,
        subset_manifest,
        only_expected_rows(parent_rows, subset_ids, models),
    )
    replication_frame = build_metric_frame(
        analysis_spec, subset_manifest,
        only_expected_rows(replication_rows, subset_ids, models),
    )
    queue = validate_queue_ranks(
        replication_rows, list(analysis_spec["models"]),
        int(replication_spec["expected_samples_per_model"]),
        order_plan,
    )
    replication_frame = replication_frame.merge(
        queue, on=["model", "sample_id"], validate="one_to_one",
    )
    block_balance_pass = validate_factorial_blocks(replication_frame)

    parent_effects, _ = effect_tables(parent_frame, args.bootstrap_reps, args.seed)
    parent_need = learner_need_effects(parent_frame, args.bootstrap_reps, args.seed + 10_000)
    subset_effects, _ = effect_tables(parent_subset_frame, args.bootstrap_reps, args.seed + 20_000)
    replication_effects, replication_family = effect_tables(
        replication_frame, args.bootstrap_reps, args.seed + 30_000,
    )
    replication_need = learner_need_effects(
        replication_frame, args.bootstrap_reps, args.seed + 40_000,
    )
    cell_means, interactions = interaction_tables(
        replication_frame, args.bootstrap_reps, args.seed + 50_000,
    )
    conditional_need = conditional_need_effects(replication_frame)
    comparison = target_comparison(subset_effects, replication_effects)
    parent_decision = evaluate_gates(analysis_spec, parent_effects, parent_need)
    replication_decision = evaluate_gates(
        analysis_spec, replication_effects, replication_need,
    )
    joint = joint_decision(parent_decision, replication_decision, comparison)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    replication_frame.to_csv(args.output_dir / "derived_replication_metrics.csv", index=False)
    replication_effects.to_csv(args.output_dir / "replication_factor_effects.csv", index=False)
    replication_family.to_csv(
        args.output_dir / "replication_family_target_effects.csv", index=False,
    )
    replication_need.to_csv(args.output_dir / "replication_learner_need_effects.csv", index=False)
    conditional_need.to_csv(
        args.output_dir / "replication_conditional_learner_need_effects.csv", index=False,
    )
    cell_means.to_csv(args.output_dir / "replication_factorial_cell_means.csv", index=False)
    interactions.to_csv(args.output_dir / "replication_factor_interactions.csv", index=False)
    comparison.to_csv(args.output_dir / "order_replication_target_comparison.csv", index=False)
    report = {
        "schema_version": 1,
        "parent_rows": len(parent_frame),
        "parent_subset_rows": len(parent_subset_frame),
        "replication_rows": len(replication_frame),
        "models": sorted(models),
        "base_problems": int(replication_frame.base_id.nunique()),
        "order_seed": int(replication_spec["order_seed"]),
        "request_order_block_balance_pass": block_balance_pass,
        "parent_decision": parent_decision,
        "replication_decision": replication_decision,
        "joint_order_robustness_decision": joint,
    }
    (args.output_dir / "order_replication_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8",
    )
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
