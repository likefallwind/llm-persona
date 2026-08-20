#!/usr/bin/env python3
"""Analyze wording transport and prospective control asymmetry."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from analyze_factorial_control_asymmetry import asymmetry_table, evaluate_asymmetry_gates
from analyze_factorial_prompt_panel import (
    FACTOR_LEVELS,
    TARGET_METRICS,
    build_metric_frame,
    conditional_need_effects,
    difference,
    effect_tables,
    evaluate_gates,
    interaction_tables,
    learner_need_effects,
    load_jsonl,
)


def validate_queue(
    response_rows: list[dict[str, Any]], plan: list[dict[str, Any]],
    models: list[str], samples_per_model: int,
) -> pd.DataFrame:
    latest: dict[tuple[str, str], dict[str, Any]] = {}
    for row in response_rows:
        key = (str(row.get("sample_id", "")), str(row.get("model", "")))
        if all(key):
            latest[key] = row
    successful = {
        key: row for key, row in latest.items()
        if isinstance(row.get("response"), str) and row["response"].strip()
        and not row.get("error")
    }
    planned = {
        (str(row["sample_id"]), str(row["model"])): int(row["queue_rank"])
        for row in plan
    }
    expected = samples_per_model * len(models)
    if len(successful) != expected or set(successful) != set(planned):
        raise RuntimeError(
            f"paraphrase response/plan mismatch: successful={len(successful)} "
            f"planned={len(planned)} expected={expected}"
        )
    records = []
    for key, row in successful.items():
        rank = int(row.get("paraphrase_queue_rank", -1))
        if planned[key] != rank:
            raise RuntimeError(f"observed queue rank differs from plan for {key}")
        records.append({
            "sample_id": key[0], "model": key[1], "paraphrase_queue_rank": rank,
        })
    queue = pd.DataFrame(records)
    for model in models:
        ranks = set(queue.loc[queue.model == model, "paraphrase_queue_rank"])
        if ranks != set(range(samples_per_model)):
            raise RuntimeError(f"incomplete queue ranks for {model}")
    return queue


def exact_block_balance(frame: pd.DataFrame) -> bool:
    audited = frame.copy()
    audited["block_index"] = audited.paraphrase_queue_rank // 32
    columns = [
        "wording_set", "learner_need", "question_policy", "answer_policy", "tone_policy",
    ]
    counts = audited.groupby(["model", "block_index"])[columns].apply(
        lambda group: len(group.drop_duplicates()), include_groups=False,
    )
    return bool((counts == 32).all() and len(counts) == audited.model.nunique() * 8)


def target_effect_difference(
    frame: pd.DataFrame, wording_a: str, wording_b: str, reps: int, seed: int,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    groups = [("ALL", frame)] + [
        (str(model), group) for model, group in frame.groupby("model", sort=True)
    ]
    for group_index, (group_name, group) in enumerate(groups):
        bases = sorted(group.base_id.unique())
        rng = np.random.default_rng(seed + group_index * 1000)
        for factor_index, (factor, metric) in enumerate(TARGET_METRICS.items()):
            high, low = FACTOR_LEVELS[factor]

            def effect(data: pd.DataFrame, wording: str) -> float:
                return difference(data[data.wording_set == wording], factor, high, low, metric)

            estimate = effect(group, wording_b) - effect(group, wording_a)
            draws = []
            by_base = {base: group[group.base_id == base] for base in bases}
            for _ in range(reps):
                selected = rng.choice(bases, size=len(bases), replace=True)
                sample = pd.concat(
                    [by_base[base].assign(_copy=index) for index, base in enumerate(selected)],
                    ignore_index=True,
                )
                draws.append(effect(sample, wording_b) - effect(sample, wording_a))
            rows.append({
                "group": group_name,
                "factor": factor,
                "metric": metric,
                "wording_b_minus_a": estimate,
                "bootstrap_ci_low": float(np.quantile(draws, 0.025)),
                "bootstrap_ci_high": float(np.quantile(draws, 0.975)),
            })
    return pd.DataFrame(rows)


def wording_decision(
    spec: dict[str, Any], per_wording: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    wording_sets = list(spec["wording_sets"])
    factors: dict[str, Any] = {}
    for factor in TARGET_METRICS:
        passes = {
            wording: bool(per_wording[wording]["factor_gates"]["factor_results"][factor]["selective"])
            for wording in wording_sets
        }
        factors[factor] = {
            "selective_by_wording_set": passes,
            "paraphrase_robust_operational_effect": all(passes.values()),
            "semantic_claim": (
                "literal frozen encouragement marker only"
                if factor == "tone_policy" else TARGET_METRICS[factor]
            ),
        }
    asymmetry: dict[str, Any] = {}
    for policy in ("question", "answer"):
        passes = {
            wording: bool(per_wording[wording]["control_asymmetry"][policy]["control_asymmetry_pass"])
            for wording in wording_sets
        }
        asymmetry[policy] = {
            "pass_by_wording_set": passes,
            "prospectively_confirmed_across_wordings": all(passes.values()),
        }
    return {
        "factor_wording_transport": factors,
        "control_asymmetry": asymmetry,
        "rule": (
            "Both frozen wording sets must independently pass. The tone result remains "
            "a literal marker and cannot regain semantic warmth status."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--spec", type=Path,
        default=Path("data/factorial_paraphrase_replication_spec_v1.json"),
    )
    parser.add_argument(
        "--manifest", type=Path,
        default=Path("artifacts/factorial_paraphrase_replication_v1/sample_manifest.jsonl"),
    )
    parser.add_argument(
        "--order-plan", type=Path,
        default=Path("artifacts/factorial_paraphrase_replication_v1/request_order_plan.jsonl"),
    )
    parser.add_argument(
        "--responses", type=Path,
        default=Path("artifacts/factorial_paraphrase_replication_v1/run/responses.jsonl"),
    )
    parser.add_argument(
        "--output-dir", type=Path,
        default=Path("artifacts/factorial_paraphrase_replication_analysis_v1"),
    )
    parser.add_argument("--bootstrap-reps", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=20260825)
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    manifest = load_jsonl(args.manifest)
    responses = load_jsonl(args.responses)
    queue = validate_queue(
        responses, load_jsonl(args.order_plan), list(spec["models"]),
        int(spec["expected_samples_per_model"]),
    )
    frame = build_metric_frame(spec, manifest, responses)
    wording_map = {str(row["sample_id"]): str(row["wording_set"]) for row in manifest}
    frame["wording_set"] = frame.sample_id.map(wording_map)
    frame = frame.merge(queue, on=["sample_id", "model"], how="left", validate="one_to_one")
    if not exact_block_balance(frame):
        raise RuntimeError("observed requests fail exact 32-stratum block balance")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.output_dir / "derived_response_metrics.csv", index=False)
    per_wording: dict[str, dict[str, Any]] = {}
    for wording_index, wording in enumerate(spec["wording_sets"]):
        subset = frame[frame.wording_set == wording].copy()
        effects, family = effect_tables(
            subset, args.bootstrap_reps, args.seed + wording_index * 100_000,
        )
        cells, interactions = interaction_tables(
            subset, args.bootstrap_reps, args.seed + 20_000 + wording_index * 100_000,
        )
        need = learner_need_effects(
            subset, args.bootstrap_reps, args.seed + 40_000 + wording_index * 100_000,
        )
        conditional = conditional_need_effects(subset)
        asymmetry = asymmetry_table(
            subset, args.bootstrap_reps, args.seed + 60_000 + wording_index * 100_000,
        )
        effects.to_csv(args.output_dir / f"{wording}_factor_effects.csv", index=False)
        family.to_csv(args.output_dir / f"{wording}_family_target_effects.csv", index=False)
        cells.to_csv(args.output_dir / f"{wording}_factorial_cell_means.csv", index=False)
        interactions.to_csv(args.output_dir / f"{wording}_factor_interactions.csv", index=False)
        need.to_csv(args.output_dir / f"{wording}_learner_need_effects.csv", index=False)
        conditional.to_csv(
            args.output_dir / f"{wording}_conditional_learner_need_effects.csv", index=False,
        )
        asymmetry.to_csv(args.output_dir / f"{wording}_control_asymmetry.csv", index=False)
        per_wording[wording] = {
            "rows": len(subset),
            "factor_gates": evaluate_gates(spec, effects, need),
            "control_asymmetry": evaluate_asymmetry_gates(
                asymmetry, spec["control_asymmetry_gates"],
            ),
        }

    wording_a, wording_b = list(spec["wording_sets"])
    differences = target_effect_difference(
        frame, wording_a, wording_b, args.bootstrap_reps, args.seed + 500_000,
    )
    differences.to_csv(args.output_dir / "wording_target_effect_differences.csv", index=False)
    decision = wording_decision(spec, per_wording)
    report = {
        "schema_version": 1,
        "status": "prospective_post_result_wording_replication",
        "response_rows": len(frame),
        "base_problems": int(frame.base_id.nunique()),
        "models": sorted(frame.model.unique().tolist()),
        "wording_sets": list(spec["wording_sets"]),
        "exact_32_stratum_block_balance": True,
        "per_wording": per_wording,
        "joint_decision": decision,
        "claim_boundary": (
            "This tests transport across two frozen clause paraphrases and confirms the "
            "predeclared control-asymmetry estimand. It is not outcome-blind replication "
            "of the original panel and does not measure learner benefit."
        ),
    }
    (args.output_dir / "paraphrase_replication_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8",
    )
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
