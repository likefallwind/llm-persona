#!/usr/bin/env python3
"""Audit whether a shared pedagogy prompt improves averages by homogenizing actions."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ARMS = ("generic", "pedagogy")
ACTS = ("probing", "focus", "telling", "generic")


def bootstrap_mean(values: np.ndarray, reps: int, seed: int) -> tuple[float, float]:
    values = np.asarray(values, dtype=float)
    if not len(values):
        return float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    draws = rng.choice(values, size=(reps, len(values)), replace=True).mean(axis=1)
    return float(np.quantile(draws, 0.025)), float(np.quantile(draws, 0.975))


def validate_and_pair(predictions: pd.DataFrame) -> pd.DataFrame:
    required = {
        "classifier_variant", "family", "arm", "pair_id", "model", "target_act",
        "predicted_act", "act_match",
    }
    missing = required - set(predictions.columns)
    if missing:
        raise RuntimeError(f"missing generated-act columns: {sorted(missing)}")
    keys = ["classifier_variant", "family", "model", "pair_id", "target_act"]
    counts = predictions.groupby(keys + ["arm"]).size()
    if not (counts == 1).all():
        raise RuntimeError("generated-act rows are not unique per paired arm")
    wide = predictions.pivot(index=keys, columns="arm", values="act_match")
    if not set(ARMS).issubset(wide.columns) or wide[list(ARMS)].isna().any().any():
        raise RuntimeError("generated-act panel is not exactly paired across arms")
    wide = wide.reset_index()
    wide["delta"] = wide["pedagogy"] - wide["generic"]
    return wide


def action_effect_tables(
    paired: pd.DataFrame, reps: int, seed: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    model_rows: list[dict[str, Any]] = []
    aggregate_rows: list[dict[str, Any]] = []
    for group_index, (keys, group) in enumerate(
        paired.groupby(["classifier_variant", "family", "target_act"], sort=True)
    ):
        variant, family, target_act = keys
        context_delta = group.groupby("pair_id", sort=True).delta.mean().to_numpy()
        lo, hi = bootstrap_mean(context_delta, reps, seed + group_index)
        aggregate_rows.append({
            "classifier_variant": variant,
            "family": family,
            "target_act": target_act,
            "context_count": int(group.pair_id.nunique()),
            "model_count": int(group.model.nunique()),
            "generic_match": float(group.generic.mean()),
            "pedagogy_match": float(group.pedagogy.mean()),
            "mean_delta": float(group.delta.mean()),
            "context_cluster_ci_low": lo,
            "context_cluster_ci_high": hi,
        })
        for model_index, (model, model_group) in enumerate(group.groupby("model", sort=True)):
            model_lo, model_hi = bootstrap_mean(
                model_group.delta.to_numpy(), reps,
                seed + 100_000 + group_index * 100 + model_index,
            )
            model_rows.append({
                "classifier_variant": variant,
                "family": family,
                "target_act": target_act,
                "model": model,
                "context_count": len(model_group),
                "generic_match": float(model_group.generic.mean()),
                "pedagogy_match": float(model_group.pedagogy.mean()),
                "mean_delta": float(model_group.delta.mean()),
                "context_bootstrap_ci_low": model_lo,
                "context_bootstrap_ci_high": model_hi,
            })
    model_effects = pd.DataFrame(model_rows)
    aggregate = pd.DataFrame(aggregate_rows)
    signs = model_effects.groupby(
        ["classifier_variant", "family", "target_act"], sort=True,
    ).agg(
        model_count=("model", "nunique"),
        positive_models=("mean_delta", lambda values: int((values > 0).sum())),
        negative_models=("mean_delta", lambda values: int((values < 0).sum())),
        zero_models=("mean_delta", lambda values: int((values == 0).sum())),
        minimum_model_delta=("mean_delta", "min"),
        maximum_model_delta=("mean_delta", "max"),
    ).reset_index()
    return aggregate, model_effects, signs


def normalized_entropy(values: pd.Series) -> float:
    probabilities = values.value_counts(normalize=True).to_numpy(dtype=float)
    return float(-(probabilities * np.log(probabilities)).sum() / np.log(len(ACTS)))


def modal_disagreement(values: pd.Series) -> float:
    return float(1.0 - values.value_counts(normalize=True).max())


def consensus_tables(
    predictions: pd.DataFrame, reps: int, seed: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    context = predictions.groupby(
        ["classifier_variant", "family", "arm", "pair_id"], sort=True,
    ).predicted_act.agg(
        normalized_entropy=normalized_entropy,
        modal_disagreement=modal_disagreement,
        unique_actions="nunique",
    ).reset_index()
    rows: list[dict[str, Any]] = []
    metrics = ("normalized_entropy", "modal_disagreement", "unique_actions")
    for group_index, (keys, group) in enumerate(
        context.groupby(["classifier_variant", "family"], sort=True)
    ):
        wide = group.pivot(index="pair_id", columns="arm", values=list(metrics)).dropna()
        if len(wide) != group.pair_id.nunique():
            raise RuntimeError(f"consensus panel is not paired for {keys}")
        for metric_index, metric in enumerate(metrics):
            delta = (wide[(metric, "pedagogy")] - wide[(metric, "generic")]).to_numpy()
            lo, hi = bootstrap_mean(
                delta, reps, seed + group_index * 100 + metric_index,
            )
            rows.append({
                "classifier_variant": keys[0],
                "family": keys[1],
                "metric": metric,
                "context_count": len(delta),
                "generic_mean": float(wide[(metric, "generic")].mean()),
                "pedagogy_mean": float(wide[(metric, "pedagogy")].mean()),
                "pedagogy_minus_generic": float(delta.mean()),
                "context_bootstrap_ci_low": lo,
                "context_bootstrap_ci_high": hi,
            })
    return context, pd.DataFrame(rows)


def overall_effects(paired: pd.DataFrame, reps: int, seed: int) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for index, (keys, group) in enumerate(
        paired.groupby(["classifier_variant", "family"], sort=True)
    ):
        context_delta = group.groupby("pair_id", sort=True).delta.mean().to_numpy()
        lo, hi = bootstrap_mean(context_delta, reps, seed + index)
        rows.append({
            "classifier_variant": keys[0],
            "family": keys[1],
            "context_count": int(group.pair_id.nunique()),
            "model_count": int(group.model.nunique()),
            "generic_match": float(group.generic.mean()),
            "pedagogy_match": float(group.pedagogy.mean()),
            "mean_delta": float(group.delta.mean()),
            "context_cluster_ci_low": lo,
            "context_cluster_ci_high": hi,
        })
    return pd.DataFrame(rows)


def headline_report(
    overall: pd.DataFrame, action: pd.DataFrame, signs: pd.DataFrame,
    consensus: pd.DataFrame,
) -> dict[str, Any]:
    standard_overall = overall[overall.family == "standard"]
    telling = action[(action.family == "standard") & (action.target_act == "telling")]
    probing = action[(action.family == "standard") & (action.target_act == "probing")]
    telling_signs = signs[(signs.family == "standard") & (signs.target_act == "telling")]
    probing_signs = signs[(signs.family == "standard") & (signs.target_act == "probing")]
    entropy = consensus[consensus.metric == "normalized_entropy"]
    checks = {
        "overall_standard_positive_all_classifiers": bool(
            len(standard_overall) == 3 and (standard_overall.mean_delta > 0).all()
        ),
        "telling_negative_all_models_all_classifiers": bool(
            len(telling_signs) == 3
            and (telling_signs.negative_models == telling_signs.model_count).all()
        ),
        "telling_aggregate_ci_below_zero_all_classifiers": bool(
            len(telling) == 3 and (telling.context_cluster_ci_high < 0).all()
        ),
        "probing_positive_all_models_all_classifiers": bool(
            len(probing_signs) == 3
            and (probing_signs.positive_models == probing_signs.model_count).all()
        ),
        "probing_aggregate_ci_above_zero_all_classifiers": bool(
            len(probing) == 3 and (probing.context_cluster_ci_low > 0).all()
        ),
        "cross_model_entropy_decreases_all_classifier_families": bool(
            len(entropy) == 6 and (entropy.pedagogy_minus_generic < 0).all()
        ),
        "entropy_decrease_ci_below_zero_all_classifier_families": bool(
            len(entropy) == 6 and (entropy.context_bootstrap_ci_high < 0).all()
        ),
    }
    return {
        "schema_version": 1,
        "status": "post_hoc_action_heterogeneity_audit_on_existing_responses",
        "checks": checks,
        "standard_overall_delta_range": [
            float(standard_overall.mean_delta.min()),
            float(standard_overall.mean_delta.max()),
        ],
        "standard_telling_delta_range": [
            float(telling.mean_delta.min()), float(telling.mean_delta.max()),
        ],
        "standard_probing_delta_range": [
            float(probing.mean_delta.min()), float(probing.mean_delta.max()),
        ],
        "cross_model_entropy_delta_range": [
            float(entropy.pedagogy_minus_generic.min()),
            float(entropy.pedagogy_minus_generic.max()),
        ],
        "claim_boundary": (
            "The response panel and target labels predate this audit, but the joint "
            "average-gain/action-harm/homogenization estimand was specified after outcome "
            "inspection. Models are a fixed convenience panel; classifier variants are "
            "robustness checks, not independent samples; action match is not learning gain."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--predictions", type=Path,
        default=Path("artifacts/dialogue_act_validity/generated_dialogue_acts.csv"),
    )
    parser.add_argument(
        "--output-dir", type=Path,
        default=Path("artifacts/policy_homogenization_v1"),
    )
    parser.add_argument("--bootstrap-reps", type=int, default=4000)
    parser.add_argument("--seed", type=int, default=20260826)
    args = parser.parse_args()

    predictions = pd.read_csv(args.predictions)
    paired = validate_and_pair(predictions)
    action, model_action, signs = action_effect_tables(
        paired, args.bootstrap_reps, args.seed,
    )
    overall = overall_effects(paired, args.bootstrap_reps, args.seed + 100_000)
    context_consensus, consensus = consensus_tables(
        predictions, args.bootstrap_reps, args.seed + 200_000,
    )
    report = headline_report(overall, action, signs, consensus)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    paired.to_csv(args.output_dir / "paired_action_match.csv", index=False)
    overall.to_csv(args.output_dir / "overall_prompt_effects.csv", index=False)
    action.to_csv(args.output_dir / "target_action_effects.csv", index=False)
    model_action.to_csv(args.output_dir / "target_action_model_effects.csv", index=False)
    signs.to_csv(args.output_dir / "target_action_sign_robustness.csv", index=False)
    context_consensus.to_csv(args.output_dir / "context_model_consensus.csv", index=False)
    consensus.to_csv(args.output_dir / "consensus_prompt_effects.csv", index=False)
    (args.output_dir / "policy_homogenization_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8",
    )
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
