#!/usr/bin/env python3
"""Audit default tutor-policy signatures and their deformation by prompts.

This is a secondary, outcome-aware analysis of the frozen semantic panel.  It
does not upgrade the preregistered disposition decisions.  Its purpose is to
separate three observable objects on the exact same contexts: default model
differences, the shared prompt effect, and model-specific prompt elasticity.
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


PAIRED_TASKS = ("mathdial_standard", "mathdial_hard")
ARMS = ("generic", "pedagogy")
REQUIRED_COLUMNS = {
    "task", "arm", "pair_id", "model", "dimension", "score", "centered_score",
}


def bh_adjust(pvalues: pd.Series) -> pd.Series:
    values = pvalues.fillna(1.0).to_numpy(float)
    order = np.argsort(values)
    ranked = values[order]
    adjusted = np.minimum.accumulate(
        (ranked * len(values) / np.arange(1, len(values) + 1))[::-1]
    )[::-1]
    output = np.empty(len(values), dtype=float)
    output[order] = np.minimum(adjusted, 1.0)
    return pd.Series(output, index=pvalues.index)


def validate_paired_semantic(frame: pd.DataFrame) -> pd.DataFrame:
    missing_columns = REQUIRED_COLUMNS - set(frame.columns)
    if missing_columns:
        raise ValueError(f"semantic input is missing columns: {sorted(missing_columns)}")
    data = frame[
        frame["task"].isin(PAIRED_TASKS) & frame["arm"].isin(ARMS)
    ].copy()
    if data.empty:
        raise ValueError("semantic input has no paired MathDial prompt arms")
    keys = ["task", "pair_id", "model", "arm", "dimension"]
    if data.duplicated(keys).any():
        raise ValueError("semantic input contains duplicate model-by-arm cells")
    models = sorted(data["model"].unique())
    expected = len(models) * len(ARMS)
    counts = data.groupby(["task", "pair_id", "dimension"]).size()
    if not (counts == expected).all():
        raise ValueError("every task, pair, and dimension must have a complete model-by-arm grid")
    arm_counts = data.groupby(["task", "pair_id", "dimension", "model"])["arm"].nunique()
    if not (arm_counts == len(ARMS)).all():
        raise ValueError("every model must have both prompt arms")
    model_sets = data.groupby(["task", "dimension"])["model"].agg(
        lambda values: tuple(sorted(set(values)))
    )
    if any(value != tuple(models) for value in model_sets):
        raise ValueError("all task-dimension panels must use the same models")
    return data


def default_profiles(frame: pd.DataFrame) -> pd.DataFrame:
    data = validate_paired_semantic(frame)
    generic = data[data["arm"] == "generic"]
    profiles = generic.groupby(["task", "model", "dimension"], as_index=False).agg(
        contexts=("pair_id", "nunique"),
        raw_mean=("score", "mean"),
        mean_item_centered_score=("centered_score", "mean"),
    )
    profiles["centered_across_models"] = profiles["raw_mean"] - profiles.groupby(
        ["task", "dimension"]
    )["raw_mean"].transform("mean")
    return profiles


def _balanced_array(group: pd.DataFrame) -> tuple[np.ndarray, list[str], list[str], list[str]]:
    pairs = sorted(group["pair_id"].unique())
    models = sorted(group["model"].unique())
    arms = list(ARMS)
    pivot = group.pivot(index="pair_id", columns=["model", "arm"], values="score")
    columns = pd.MultiIndex.from_product([models, arms])
    pivot = pivot.reindex(index=pairs, columns=columns)
    if pivot.isna().any().any():
        raise ValueError("balanced array contains missing model-by-arm cells")
    values = pivot.to_numpy(float).reshape(len(pairs), len(models), len(arms))
    return values, pairs, models, arms


def variance_decomposition(frame: pd.DataFrame) -> pd.DataFrame:
    """Balanced sums-of-squares decomposition after exact-context control."""
    data = validate_paired_semantic(frame)
    rows = []
    for (task, dimension), group in data.groupby(["task", "dimension"]):
        values, pairs, models, arms = _balanced_array(group)
        n_pairs, n_models, n_arms = values.shape
        grand = float(values.mean())
        pair_mean = values.mean(axis=(1, 2))
        model_mean = values.mean(axis=(0, 2))
        arm_mean = values.mean(axis=(0, 1))
        cell_mean = values.mean(axis=0)
        interaction = (
            cell_mean - model_mean[:, None] - arm_mean[None, :] + grand
        )
        ss_total = float(np.sum((values - grand) ** 2))
        ss_pair = float(n_models * n_arms * np.sum((pair_mean - grand) ** 2))
        ss_model = float(n_pairs * n_arms * np.sum((model_mean - grand) ** 2))
        ss_prompt = float(n_pairs * n_models * np.sum((arm_mean - grand) ** 2))
        ss_interaction = float(n_pairs * np.sum(interaction**2))
        ss_residual = max(0.0, ss_total - ss_pair - ss_model - ss_prompt - ss_interaction)

        def eta(value: float) -> float:
            return value / ss_total if ss_total else math.nan

        def partial(value: float) -> float:
            denominator = value + ss_residual
            return value / denominator if denominator else math.nan

        rows.append({
            "task": task,
            "dimension": dimension,
            "contexts": n_pairs,
            "models": n_models,
            "ss_total": ss_total,
            "ss_context": ss_pair,
            "ss_model": ss_model,
            "ss_prompt": ss_prompt,
            "ss_model_by_prompt": ss_interaction,
            "ss_residual": ss_residual,
            "eta_squared_context": eta(ss_pair),
            "eta_squared_model": eta(ss_model),
            "eta_squared_prompt": eta(ss_prompt),
            "eta_squared_model_by_prompt": eta(ss_interaction),
            "partial_eta_squared_model": partial(ss_model),
            "partial_eta_squared_prompt": partial(ss_prompt),
            "partial_eta_squared_model_by_prompt": partial(ss_interaction),
            "prompt_to_model_ss_ratio": ss_prompt / ss_model if ss_model else math.inf,
            "interaction_to_model_ss_ratio": ss_interaction / ss_model if ss_model else math.inf,
        })
    return pd.DataFrame(rows)


def _arm_pivots(group: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    models = sorted(group["model"].unique())
    wide = group.pivot(index="pair_id", columns=["model", "arm"], values="score")
    generic = wide.loc[:, pd.IndexSlice[models, "generic"]].copy()
    pedagogy = wide.loc[:, pd.IndexSlice[models, "pedagogy"]].copy()
    generic.columns = models
    pedagogy.columns = models
    return generic, pedagogy, pedagogy - generic


def elasticity_heterogeneity(
    frame: pd.DataFrame,
    reps: int = 5000,
    seed: int = 20260826,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Test whether paired prompt effects differ across the fixed model panel."""
    data = validate_paired_semantic(frame)
    rng = np.random.default_rng(seed)
    summary_rows = []
    model_rows = []
    for analysis_index, ((task, dimension), group) in enumerate(
        data.groupby(["task", "dimension"])
    ):
        generic, pedagogy, delta = _arm_pivots(group)
        values = delta.to_numpy(float)
        observed_means = values.mean(axis=0)
        observed_sd = float(np.std(observed_means, ddof=0))
        observed_range = float(observed_means.max() - observed_means.min())

        boot_indices = rng.integers(0, len(values), size=(reps, len(values)))
        boot_means = values[boot_indices].mean(axis=1)
        boot_sd = np.std(boot_means, axis=1, ddof=0)
        boot_range = np.ptp(boot_means, axis=1)

        null_sd = np.empty(reps, dtype=float)
        for rep in range(reps):
            order = rng.random(values.shape).argsort(axis=1)
            permuted = np.take_along_axis(values, order, axis=1)
            null_sd[rep] = np.std(permuted.mean(axis=0), ddof=0)
        p = float((1 + np.sum(null_sd >= observed_sd)) / (reps + 1))
        summary_rows.append({
            "task": task,
            "dimension": dimension,
            "contexts": len(values),
            "models": len(delta.columns),
            "sd_model_mean_delta": observed_sd,
            "sd_bootstrap_ci_low": float(np.quantile(boot_sd, 0.025)),
            "sd_bootstrap_ci_high": float(np.quantile(boot_sd, 0.975)),
            "max_minus_min_model_delta": observed_range,
            "range_bootstrap_ci_low": float(np.quantile(boot_range, 0.025)),
            "range_bootstrap_ci_high": float(np.quantile(boot_range, 0.975)),
            "permutation_p": p,
            "permutations": reps,
            "analysis_index": analysis_index,
        })
        for model_index, model in enumerate(delta.columns):
            model_draws = boot_means[:, model_index]
            model_rows.append({
                "task": task,
                "dimension": dimension,
                "model": model,
                "contexts": len(values),
                "generic_mean": float(generic[model].mean()),
                "pedagogy_mean": float(pedagogy[model].mean()),
                "mean_delta": float(observed_means[model_index]),
                "bootstrap_ci_low": float(np.quantile(model_draws, 0.025)),
                "bootstrap_ci_high": float(np.quantile(model_draws, 0.975)),
            })
    summary = pd.DataFrame(summary_rows).drop(columns="analysis_index")
    summary["permutation_q_within_task"] = summary.groupby("task", group_keys=False)[
        "permutation_p"
    ].transform(bh_adjust)
    return summary, pd.DataFrame(model_rows)


def prompt_vs_model_scale(
    frame: pd.DataFrame,
    reps: int = 5000,
    seed: int = 20260827,
) -> pd.DataFrame:
    """Compare shared prompt movement with the generic-arm model spread."""
    data = validate_paired_semantic(frame)
    rng = np.random.default_rng(seed)
    rows = []
    for task, dimension in itertools.product(PAIRED_TASKS, sorted(data["dimension"].unique())):
        group = data[(data["task"] == task) & (data["dimension"] == dimension)]
        generic, _, delta = _arm_pivots(group)
        baseline_means = generic.mean(axis=0).to_numpy(float)
        prompt_delta = float(delta.to_numpy(float).mean())
        baseline_range = float(np.ptp(baseline_means))
        ratio = abs(prompt_delta) / baseline_range if baseline_range else math.inf
        indices = rng.integers(0, len(generic), size=(reps, len(generic)))
        generic_values = generic.to_numpy(float)
        delta_values = delta.to_numpy(float)
        boot_generic = generic_values[indices].mean(axis=1)
        boot_delta = delta_values[indices].mean(axis=(1, 2))
        boot_range = np.ptp(boot_generic, axis=1)
        with np.errstate(divide="ignore", invalid="ignore"):
            boot_ratio = np.abs(boot_delta) / boot_range
        finite_ratio = boot_ratio[np.isfinite(boot_ratio)]
        rows.append({
            "task": task,
            "dimension": dimension,
            "contexts": len(generic),
            "baseline_model_min": float(baseline_means.min()),
            "baseline_model_max": float(baseline_means.max()),
            "baseline_model_range": baseline_range,
            "shared_prompt_mean_delta": prompt_delta,
            "prompt_delta_bootstrap_ci_low": float(np.quantile(boot_delta, 0.025)),
            "prompt_delta_bootstrap_ci_high": float(np.quantile(boot_delta, 0.975)),
            "absolute_prompt_over_baseline_range": ratio,
            "ratio_bootstrap_ci_low": float(np.quantile(finite_ratio, 0.025)),
            "ratio_bootstrap_ci_high": float(np.quantile(finite_ratio, 0.975)),
        })
    return pd.DataFrame(rows)


def headroom_adjusted_elasticity(
    frame: pd.DataFrame,
    reps: int = 5000,
    seed: int = 20260829,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Sensitivity test for bounded-score floor and ceiling opportunities.

    Positive pooled effects are divided by ``5 - generic`` and negative effects
    by ``generic - 1``. Contexts where any model has zero directional headroom
    are omitted so that the within-context permutation keeps a complete panel.
    """
    data = validate_paired_semantic(frame)
    rng = np.random.default_rng(seed)
    summary_rows = []
    model_rows = []
    for (task, dimension), group in data.groupby(["task", "dimension"]):
        generic, _, delta = _arm_pivots(group)
        direction = float(np.sign(delta.to_numpy(float).mean()))
        if not direction:
            direction = 1.0
        headroom = (5.0 - generic) if direction > 0 else (generic - 1.0)
        normalized = direction * delta / headroom.replace(0.0, np.nan)
        complete = normalized.dropna(axis=0, how="any")
        values = complete.to_numpy(float)
        if len(values) < 2:
            raise ValueError(
                f"insufficient complete headroom-adjusted contexts for {task}/{dimension}"
            )
        observed_means = values.mean(axis=0)
        observed_sd = float(np.std(observed_means, ddof=0))
        observed_range = float(np.ptp(observed_means))
        boot_indices = rng.integers(0, len(values), size=(reps, len(values)))
        boot_means = values[boot_indices].mean(axis=1)
        boot_sd = np.std(boot_means, axis=1, ddof=0)
        boot_range = np.ptp(boot_means, axis=1)
        null_sd = np.empty(reps, dtype=float)
        for rep in range(reps):
            order = rng.random(values.shape).argsort(axis=1)
            permuted = np.take_along_axis(values, order, axis=1)
            null_sd[rep] = np.std(permuted.mean(axis=0), ddof=0)
        p = float((1 + np.sum(null_sd >= observed_sd)) / (reps + 1))
        summary_rows.append({
            "task": task,
            "dimension": dimension,
            "direction": "increase" if direction > 0 else "decrease",
            "available_contexts": len(generic),
            "complete_nonboundary_contexts": len(values),
            "retained_context_fraction": len(values) / len(generic),
            "sd_model_mean_adjusted_elasticity": observed_sd,
            "sd_bootstrap_ci_low": float(np.quantile(boot_sd, 0.025)),
            "sd_bootstrap_ci_high": float(np.quantile(boot_sd, 0.975)),
            "max_minus_min_adjusted_elasticity": observed_range,
            "range_bootstrap_ci_low": float(np.quantile(boot_range, 0.025)),
            "range_bootstrap_ci_high": float(np.quantile(boot_range, 0.975)),
            "permutation_p": p,
            "permutations": reps,
        })
        for model_index, model in enumerate(complete.columns):
            draws = boot_means[:, model_index]
            model_rows.append({
                "task": task,
                "dimension": dimension,
                "model": model,
                "direction": "increase" if direction > 0 else "decrease",
                "complete_nonboundary_contexts": len(values),
                "mean_fraction_of_available_headroom": float(observed_means[model_index]),
                "bootstrap_ci_low": float(np.quantile(draws, 0.025)),
                "bootstrap_ci_high": float(np.quantile(draws, 0.975)),
            })
    summary = pd.DataFrame(summary_rows)
    summary["permutation_q_within_task"] = summary.groupby("task", group_keys=False)[
        "permutation_p"
    ].transform(bh_adjust)
    return summary, pd.DataFrame(model_rows)


def rank_stability(frame: pd.DataFrame) -> pd.DataFrame:
    data = validate_paired_semantic(frame)
    rows = []
    for (task, dimension), group in data.groupby(["task", "dimension"]):
        means = group.groupby(["arm", "model"])["score"].mean().unstack("arm")
        generic = means["generic"].to_numpy(float)
        pedagogy = means["pedagogy"].to_numpy(float)
        rho = float(spearmanr(generic, pedagogy).statistic)
        exact_null = np.asarray([
            spearmanr(generic, pedagogy[list(order)]).statistic
            for order in itertools.permutations(range(len(pedagogy)))
        ], dtype=float)
        p = float(np.mean(np.abs(exact_null) >= abs(rho)))
        discordant = 0
        pairs = 0
        for left, right in itertools.combinations(range(len(generic)), 2):
            generic_sign = np.sign(generic[left] - generic[right])
            pedagogy_sign = np.sign(pedagogy[left] - pedagogy[right])
            if generic_sign and pedagogy_sign:
                pairs += 1
                discordant += int(generic_sign != pedagogy_sign)
        rows.append({
            "task": task,
            "dimension": dimension,
            "models": len(means),
            "generic_to_pedagogy_spearman": rho,
            "exact_two_sided_p": p,
            "pairwise_rank_reversals": discordant,
            "comparable_model_pairs": pairs,
            "rank_reversal_fraction": discordant / pairs if pairs else math.nan,
            "generic_low_model": str(means["generic"].idxmin()),
            "generic_high_model": str(means["generic"].idxmax()),
            "pedagogy_low_model": str(means["pedagogy"].idxmin()),
            "pedagogy_high_model": str(means["pedagogy"].idxmax()),
        })
    return pd.DataFrame(rows)


def _response_vectors(frame: pd.DataFrame) -> pd.DataFrame:
    data = validate_paired_semantic(frame)
    vectors = data.pivot(
        index=["task", "arm", "pair_id", "model"],
        columns="dimension",
        values="centered_score",
    ).reset_index()
    if vectors.isna().any().any():
        raise ValueError("semantic response vectors contain missing dimensions")
    return vectors


def _bootstrap_accuracy(
    predictions: pd.DataFrame,
    reps: int,
    rng: np.random.Generator,
) -> tuple[float, float]:
    scored = predictions.assign(correct=predictions["model"] == predictions["prediction"])
    pair_accuracy = scored.groupby("pair_id")["correct"].mean().to_numpy(float)
    indices = rng.integers(0, len(pair_accuracy), size=(reps, len(pair_accuracy)))
    values = pair_accuracy[indices].mean(axis=1)
    return float(np.quantile(values, 0.025)), float(np.quantile(values, 0.975))


def cross_prompt_attribution(
    frame: pd.DataFrame,
    reps: int = 2000,
    seed: int = 20260828,
) -> pd.DataFrame:
    """Train model attribution under one prompt and test under another."""
    vectors = _response_vectors(frame)
    features = [column for column in vectors.columns if column not in {
        "task", "arm", "pair_id", "model",
    }]
    task_pairs: list[tuple[str, str]] = [("ALL", "ALL")]
    task_pairs.extend((task, task) for task in PAIRED_TASKS)
    task_pairs.extend([
        ("mathdial_standard", "mathdial_hard"),
        ("mathdial_hard", "mathdial_standard"),
    ])
    rng = np.random.default_rng(seed)
    rows = []
    for train_arm, test_arm in [("generic", "pedagogy"), ("pedagogy", "generic")]:
        for train_task, test_task in task_pairs:
            train = vectors[vectors["arm"] == train_arm]
            test = vectors[vectors["arm"] == test_arm]
            if train_task != "ALL":
                train = train[train["task"] == train_task]
            if test_task != "ALL":
                test = test[test["task"] == test_task]
            classifier = make_pipeline(
                StandardScaler(),
                LogisticRegression(max_iter=5000, random_state=seed),
            )
            classifier.fit(train[features], train["model"])
            prediction = classifier.predict(test[features])
            scored = test[["pair_id", "model"]].copy()
            scored["prediction"] = prediction
            ci_low, ci_high = _bootstrap_accuracy(scored, reps, rng)
            model_count = train["model"].nunique()
            rows.append({
                "train_arm": train_arm,
                "test_arm": test_arm,
                "train_task": train_task,
                "test_task": test_task,
                "train_responses": len(train),
                "test_responses": len(test),
                "feature_count": len(features),
                "model_count": model_count,
                "chance_accuracy": 1 / model_count,
                "accuracy": float(accuracy_score(test["model"], prediction)),
                "balanced_accuracy": float(balanced_accuracy_score(test["model"], prediction)),
                "bootstrap_ci_low": ci_low,
                "bootstrap_ci_high": ci_high,
            })
    return pd.DataFrame(rows)


def evaluate_decision(
    submission: pd.DataFrame,
    convergence: pd.DataFrame,
    scale: pd.DataFrame,
    heterogeneity: pd.DataFrame,
    adjusted_heterogeneity: pd.DataFrame,
    attribution: pd.DataFrame,
) -> dict[str, object]:
    signatures = sorted(submission.loc[
        submission["cross_task_semantic_signature"].astype(bool), "dimension"
    ].tolist())
    reliable = set(submission.loc[
        submission["reliable_semantic_measurement"].astype(bool), "dimension"
    ])
    reliable_scale = scale[scale["dimension"].isin(reliable)]
    stable_prompt = []
    comparable_prompt = []
    for dimension, group in reliable_scale.groupby("dimension"):
        if len(group) == len(PAIRED_TASKS):
            intervals_exclude_zero = (
                ((group["prompt_delta_bootstrap_ci_low"] > 0) & (group["prompt_delta_bootstrap_ci_high"] > 0))
                | ((group["prompt_delta_bootstrap_ci_low"] < 0) & (group["prompt_delta_bootstrap_ci_high"] < 0))
            )
            same_direction = np.sign(group["shared_prompt_mean_delta"]).nunique() == 1
            if intervals_exclude_zero.all() and same_direction:
                stable_prompt.append(dimension)
            if (group["absolute_prompt_over_baseline_range"] >= 0.75).all():
                comparable_prompt.append(dimension)
    replicated_heterogeneity = sorted([
        dimension for dimension, group in adjusted_heterogeneity[
            adjusted_heterogeneity["dimension"].isin(reliable)
        ].groupby("dimension")
        if len(group) == len(PAIRED_TASKS)
        and (group["permutation_q_within_task"] < 0.05).all()
    ])
    pooled = attribution[
        (attribution["train_task"] == "ALL") & (attribution["test_task"] == "ALL")
    ]
    cross_task = attribution[
        (attribution["train_task"] != "ALL")
        & (attribution["test_task"] != "ALL")
        & (attribution["train_task"] != attribution["test_task"])
    ]
    residual_identity = len(pooled) == 2 and len(cross_task) == 4 and (
        pooled["bootstrap_ci_low"] > pooled["chance_accuracy"]
    ).all() and (cross_task["bootstrap_ci_low"] > cross_task["chance_accuracy"]).all()
    convergence_row = convergence.iloc[0]
    convergence_supported = float(convergence_row["bootstrap_ci_high"]) < 1.0
    checks = {
        "at_least_two_frozen_cross_task_signatures": len(signatures) >= 2,
        "shared_prompt_compresses_nine_model_profiles": convergence_supported,
        "at_least_two_reliable_dimensions_shift_in_both_tasks": len(stable_prompt) >= 2,
        "at_least_two_reliable_dimensions_move_at_least_0_75_baseline_range": len(comparable_prompt) >= 2,
        "model_identity_transfers_across_prompt_arms_and_tasks": bool(residual_identity),
        "replicated_model_specific_semantic_elasticity_after_headroom_adjustment": len(replicated_heterogeneity) >= 1,
    }
    core_without_heterogeneity = all(
        value for key, value in checks.items()
        if key != "replicated_model_specific_semantic_elasticity_after_headroom_adjustment"
    )
    if all(checks.values()):
        verdict = "prompt_contingent_policy_signatures_supported"
    elif core_without_heterogeneity:
        verdict = "stable_defaults_and_prompt_deformation_supported_but_semantic_elasticity_not_replicated"
    else:
        verdict = "prompt_contingent_policy_signature_thesis_not_fully_supported"
    return {
        "schema_version": 1,
        "analysis_status": "post_hoc_secondary_audit_on_frozen_outputs",
        "verdict": verdict,
        "checks": checks,
        "frozen_cross_task_signature_dimensions": signatures,
        "reliable_same_direction_prompt_dimensions": sorted(stable_prompt),
        "prompt_comparable_to_baseline_range_dimensions": sorted(comparable_prompt),
        "replicated_semantic_elasticity_dimensions": replicated_heterogeneity,
        "claim_boundary": (
            "The audit characterizes observable prompt-contingent tutor policies in a fixed deployed-model panel. "
            "It does not upgrade the frozen disposition decision, establish human-like personality, infer learner "
            "understanding, or demonstrate learning gains."
        ),
    }


def render_report(
    frame: pd.DataFrame,
    decomposition: pd.DataFrame,
    heterogeneity: pd.DataFrame,
    attribution: pd.DataFrame,
    decision: dict[str, object],
    scale: pd.DataFrame | None = None,
    ranks: pd.DataFrame | None = None,
    adjusted_heterogeneity: pd.DataFrame | None = None,
) -> str:
    data = validate_paired_semantic(frame)
    key_decomposition = decomposition[[
        "task", "dimension", "eta_squared_model", "eta_squared_prompt",
        "eta_squared_model_by_prompt", "prompt_to_model_ss_ratio",
    ]]
    key_heterogeneity = heterogeneity[[
        "task", "dimension", "max_minus_min_model_delta", "permutation_p",
        "permutation_q_within_task",
    ]]
    pooled_attribution = attribution[
        (attribution["train_task"] == "ALL") & (attribution["test_task"] == "ALL")
    ]
    sections = [
        "# Prompt-contingent pedagogical policy signatures",
        "",
        f"Paired semantic response units: **{len(data):,}**; models: **{data['model'].nunique()}**; "
        f"tasks: **{data['task'].nunique()}**; dimensions: **{data['dimension'].nunique()}**.",
        "",
        f"**Decision:** `{decision['verdict']}`",
        "",
        "This secondary audit separates **default model differences**, **shared prompt deformation**, "
        "and **model-specific elasticity**. It is outcome-aware and cannot upgrade the frozen disposition decision.",
        "",
        "## Exact-context variance decomposition",
        "",
        key_decomposition.to_markdown(index=False, floatfmt=".4f"),
        "",
        "The prompt and model-by-prompt columns are descriptive balanced sums of squares after exact-context control. "
        "They quantify observed behavioral deformation; they are not population-level model variance estimates.",
        "",
        "## Model-specific elasticity",
        "",
        key_heterogeneity.to_markdown(index=False, floatfmt=".4f"),
        "",
        "The permutation test shuffles model labels within each paired context. A low adjusted value indicates that "
        "the fixed models do not merely share one common prompt effect.",
        "",
        "## Residual identity across prompts",
        "",
        pooled_attribution.to_markdown(index=False, floatfmt=".4f"),
        "",
        "Above-chance transfer means prompt steering did not erase model-conditioned response geometry. It remains a "
        "behavioral signature, not proof of an inner or human-like personality.",
    ]
    if scale is not None:
        sections.extend([
            "",
            "## Prompt movement relative to default model spread",
            "",
            scale[[
                "task", "dimension", "baseline_model_range", "shared_prompt_mean_delta",
                "absolute_prompt_over_baseline_range", "ratio_bootstrap_ci_low", "ratio_bootstrap_ci_high",
            ]].to_markdown(index=False, floatfmt=".4f"),
        ])
    if ranks is not None:
        sections.extend([
            "",
            "## Rank stability and reversals",
            "",
            ranks[[
                "task", "dimension", "generic_to_pedagogy_spearman",
                "pairwise_rank_reversals", "rank_reversal_fraction",
            ]].to_markdown(index=False, floatfmt=".4f"),
        ])
    if adjusted_heterogeneity is not None:
        sections.extend([
            "",
            "## Floor/ceiling-adjusted elasticity sensitivity",
            "",
            adjusted_heterogeneity[[
                "task", "dimension", "complete_nonboundary_contexts",
                "retained_context_fraction", "max_minus_min_adjusted_elasticity",
                "permutation_p", "permutation_q_within_task",
            ]].to_markdown(index=False, floatfmt=".4f"),
            "",
            "This sensitivity divides movement by the directional headroom available on the 1--5 scale. "
            "It tests whether elasticity heterogeneity survives the most direct floor/ceiling explanation.",
        ])
    sections.extend([
        "",
        "## Decision audit",
        "",
        pd.DataFrame([
            {"check": key, "passed": value}
            for key, value in decision.get("checks", {}).items()
        ]).to_markdown(index=False),
        "",
        "## Interpretation",
        "",
        "The supported object is a prompt-contingent policy response surface: a model-conditioned default plus a "
        "shared intervention effect and, where replicated, a model-specific response. Strong instruction following "
        "does not establish context-appropriate action selection, learner-state understanding, or learning benefit.",
        "",
        f"Boundary: {decision.get('claim_boundary', '')}",
        "",
    ])
    return "\n".join(sections)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--semantic-scores",
        type=Path,
        default=Path("artifacts/semantic_panel/centered_response_scores.csv"),
    )
    parser.add_argument(
        "--submission-decisions",
        type=Path,
        default=Path("artifacts/submission_decision/dimension_decisions.csv"),
    )
    parser.add_argument(
        "--prompt-convergence",
        type=Path,
        default=Path("artifacts/extended_analysis/prompt_convergence.csv"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/prompt_contingent_signatures_v1"),
    )
    parser.add_argument("--bootstrap-reps", type=int, default=5000)
    parser.add_argument("--attribution-bootstrap-reps", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=20260826)
    args = parser.parse_args()

    semantic = pd.read_csv(args.semantic_scores)
    submission = pd.read_csv(args.submission_decisions)
    convergence = pd.read_csv(args.prompt_convergence)
    validate_paired_semantic(semantic)

    profiles = default_profiles(semantic)
    decomposition = variance_decomposition(semantic)
    heterogeneity, elasticity = elasticity_heterogeneity(
        semantic, args.bootstrap_reps, args.seed,
    )
    scale = prompt_vs_model_scale(
        semantic, args.bootstrap_reps, args.seed + 100_000,
    )
    adjusted_heterogeneity, adjusted_model_elasticity = headroom_adjusted_elasticity(
        semantic, args.bootstrap_reps, args.seed + 150_000,
    )
    ranks = rank_stability(semantic)
    attribution = cross_prompt_attribution(
        semantic, args.attribution_bootstrap_reps, args.seed + 200_000,
    )
    decision = evaluate_decision(
        submission, convergence, scale, heterogeneity, adjusted_heterogeneity, attribution,
    )
    report = render_report(
        semantic, decomposition, heterogeneity, attribution, decision, scale, ranks,
        adjusted_heterogeneity,
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        "default_semantic_profiles.csv": profiles,
        "variance_decomposition.csv": decomposition,
        "semantic_elasticity_heterogeneity.csv": heterogeneity,
        "model_semantic_elasticity.csv": elasticity,
        "prompt_vs_model_scale.csv": scale,
        "headroom_adjusted_elasticity_heterogeneity.csv": adjusted_heterogeneity,
        "headroom_adjusted_model_elasticity.csv": adjusted_model_elasticity,
        "rank_stability.csv": ranks,
        "cross_prompt_model_attribution.csv": attribution,
    }
    for filename, output in outputs.items():
        output.to_csv(args.output_dir / filename, index=False)
    (args.output_dir / "decision.json").write_text(
        json.dumps(decision, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (args.output_dir / "report.md").write_text(report, encoding="utf-8")
    print(args.output_dir / "report.md")


if __name__ == "__main__":
    main()
