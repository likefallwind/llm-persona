#!/usr/bin/env python3
"""Post-hoc deterministic surface audit for the action-routing trial.

The frozen dialogue-act analysis remains primary. This audit distinguishes
failure to realize a question/no-question instruction from failure to select an
appropriate action. It never releases response text.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Any

import numpy as np
import pandas as pd

from analyze_action_routing_trial import validate_responses
from run_factorial_prompt_panel import load_jsonl


SURFACE_METRICS = (
    "has_question_mark",
    "first_sentence_has_question_mark",
    "question_mark_count",
    "word_count",
    "char_count",
)


def first_sentence(text: str) -> str:
    return re.split(r"(?<=[.!?])\s+", text.strip(), maxsplit=1)[0]


def response_metrics(
    successful: dict[tuple[str, str], dict[str, Any]],
    manifest: list[dict[str, Any]],
) -> pd.DataFrame:
    samples = {str(row["sample_id"]): row for row in manifest}
    rows = []
    for (sample_id, model), response_row in sorted(successful.items()):
        sample = samples[sample_id]
        text = str(response_row["response"]).strip()
        first = first_sentence(text)
        rows.append({
            "sample_id": sample_id,
            "context_id": sample["context_id"],
            "target_act": sample["target_act"],
            "arm": sample["arm"],
            "model": model,
            "response_sha256": hashlib.sha256(text.encode()).hexdigest(),
            "has_question_mark": int("?" in text),
            "first_sentence_has_question_mark": int("?" in first),
            "question_mark_count": text.count("?"),
            "word_count": len(re.findall(r"\b\w+\b", text)),
            "char_count": len(text),
        })
    return pd.DataFrame(rows)


def context_cluster_interval(values: pd.DataFrame, metric: str, reps: int, seed: int) -> tuple[float, float]:
    per_context = values.groupby("context_id", sort=True)[metric].mean().to_numpy()
    rng = np.random.default_rng(seed)
    draws = rng.choice(
        per_context, size=(reps, len(per_context)), replace=True,
    ).mean(axis=1)
    return float(np.quantile(draws, 0.025)), float(np.quantile(draws, 0.975))


def arm_summary(frame: pd.DataFrame, reps: int, seed: int) -> pd.DataFrame:
    rows = []
    for group_index, ((target, arm), group) in enumerate(
        frame.groupby(["target_act", "arm"], sort=True)
    ):
        for metric_index, metric in enumerate(SURFACE_METRICS):
            lo, hi = context_cluster_interval(
                group, metric, reps, seed + group_index * 100 + metric_index,
            )
            rows.append({
                "target_act": target,
                "arm": arm,
                "metric": metric,
                "contexts": int(group.context_id.nunique()),
                "models": int(group.model.nunique()),
                "mean": float(group[metric].mean()),
                "context_cluster_ci_low": lo,
                "context_cluster_ci_high": hi,
            })
    return pd.DataFrame(rows)


def target_separation(frame: pd.DataFrame, reps: int, seed: int) -> pd.DataFrame:
    """Unpaired, target-stratified probing-minus-telling surface contrasts."""
    rows = []
    groups = [("ALL", frame)] + [
        (str(model), group) for model, group in frame.groupby("model", sort=True)
    ]
    for group_index, (model, group) in enumerate(groups):
        for arm_index, (arm, arm_group) in enumerate(group.groupby("arm", sort=True)):
            for metric_index, metric in enumerate((
                "has_question_mark", "first_sentence_has_question_mark",
            )):
                target_values = {
                    str(target): target_group.groupby("context_id", sort=True)[metric]
                    .mean().to_numpy()
                    for target, target_group in arm_group.groupby("target_act", sort=True)
                }
                if set(target_values) != {"probing", "telling"}:
                    raise RuntimeError(f"missing routing target for {model}|{arm}|{metric}")
                probing = target_values["probing"]
                telling = target_values["telling"]
                rng = np.random.default_rng(
                    seed + group_index * 10_000 + arm_index * 100 + metric_index,
                )
                draws = (
                    rng.choice(probing, size=(reps, len(probing)), replace=True).mean(axis=1)
                    - rng.choice(telling, size=(reps, len(telling)), replace=True).mean(axis=1)
                )
                rows.append({
                    "model": model,
                    "arm": arm,
                    "metric": metric,
                    "probing_mean": float(probing.mean()),
                    "telling_mean": float(telling.mean()),
                    "probing_minus_telling": float(probing.mean() - telling.mean()),
                    "stratified_context_ci_low": float(np.quantile(draws, 0.025)),
                    "stratified_context_ci_high": float(np.quantile(draws, 0.975)),
                })
    return pd.DataFrame(rows)


def prediction_distribution(predictions: pd.DataFrame) -> pd.DataFrame:
    counts = predictions.groupby(
        ["classifier_variant", "target_act", "arm", "predicted_act"], sort=True,
    ).size().rename("count").reset_index()
    counts["share"] = counts["count"] / counts.groupby(
        ["classifier_variant", "target_act", "arm"], sort=True,
    )["count"].transform("sum")
    return counts


def build_report(
    frame: pd.DataFrame, summary: pd.DataFrame, separation: pd.DataFrame,
    predictions: pd.DataFrame,
) -> dict[str, Any]:
    q_summary = summary[summary.metric == "has_question_mark"].set_index(
        ["target_act", "arm"],
    )["mean"]
    first_summary = summary[
        summary.metric == "first_sentence_has_question_mark"
    ].set_index(["target_act", "arm"])["mean"]
    adaptive_models = separation[
        (separation.arm == "adaptive_router")
        & (separation.metric == "has_question_mark")
        & (separation.model != "ALL")
    ]
    distributions = prediction_distribution(predictions)
    oracle_probe = distributions[
        (distributions.arm == "oracle_action")
        & (distributions.target_act == "probing")
        & (distributions.predicted_act == "probing")
    ]
    oracle_tell = distributions[
        (distributions.arm == "oracle_action")
        & (distributions.target_act == "telling")
        & (distributions.predicted_act == "telling")
    ]
    return {
        "schema_version": 1,
        "status": "post_hoc_mechanism_audit_after_primary_action_routing_analysis",
        "response_rows": len(frame),
        "claim_boundary": (
            "Question marks are deterministic surface indicators, not complete dialogue-act "
            "labels or learning outcomes. This audit was specified after the primary trial "
            "outcomes were inspected."
        ),
        "oracle_surface_realization": {
            "probing_any_question_rate": float(q_summary.loc[("probing", "oracle_action")]),
            "probing_first_sentence_question_rate": float(
                first_summary.loc[("probing", "oracle_action")]
            ),
            "telling_no_question_rate": float(
                1 - q_summary.loc[("telling", "oracle_action")]
            ),
        },
        "single_pass_routing": {
            "adaptive_question_rate_on_probing": float(
                q_summary.loc[("probing", "adaptive_router")]
            ),
            "adaptive_question_rate_on_telling": float(
                q_summary.loc[("telling", "adaptive_router")]
            ),
            "adaptive_probing_minus_telling_question_rate": float(
                q_summary.loc[("probing", "adaptive_router")]
                - q_summary.loc[("telling", "adaptive_router")]
            ),
            "adaptive_model_separation_min": float(
                adaptive_models.probing_minus_telling.min()
            ),
            "adaptive_model_separation_max": float(
                adaptive_models.probing_minus_telling.max()
            ),
            "uniform_question_rate_on_telling": float(
                q_summary.loc[("telling", "uniform_scaffold")]
            ),
            "generic_question_rate_on_telling": float(
                q_summary.loc[("telling", "generic")]
            ),
        },
        "oracle_classifier_match_ranges": {
            "probing_min": float(oracle_probe.share.min()),
            "probing_max": float(oracle_probe.share.max()),
            "telling_min": float(oracle_tell.share.min()),
            "telling_max": float(oracle_tell.share.max()),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, default=Path("data/action_routing_trial_spec_v1.json"))
    parser.add_argument("--manifest", type=Path, default=Path("artifacts/action_routing_trial_v1/sample_manifest.jsonl"))
    parser.add_argument("--order-plan", type=Path, default=Path("artifacts/action_routing_trial_v1/request_order_plan.jsonl"))
    parser.add_argument("--responses", type=Path, default=Path("artifacts/action_routing_trial_v1/run/responses.jsonl"))
    parser.add_argument("--predictions", type=Path, default=Path("artifacts/action_routing_trial_analysis_v1/predicted_actions.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/action_routing_surface_audit_v1"))
    parser.add_argument("--bootstrap-reps", type=int, default=4000)
    parser.add_argument("--seed", type=int, default=20260830)
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    manifest = load_jsonl(args.manifest)
    successful = validate_responses(
        spec, manifest, load_jsonl(args.order_plan), load_jsonl(args.responses),
    )
    frame = response_metrics(successful, manifest)
    summary = arm_summary(frame, args.bootstrap_reps, args.seed)
    separation = target_separation(frame, args.bootstrap_reps, args.seed + 100_000)
    predictions = pd.read_csv(args.predictions)
    distribution = prediction_distribution(predictions)
    report = build_report(frame, summary, separation, predictions)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.output_dir / "surface_response_metrics.csv", index=False)
    summary.to_csv(args.output_dir / "surface_arm_summary.csv", index=False)
    separation.to_csv(args.output_dir / "surface_target_separation.csv", index=False)
    distribution.to_csv(args.output_dir / "predicted_action_distribution.csv", index=False)
    (args.output_dir / "surface_mechanism_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8",
    )
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
