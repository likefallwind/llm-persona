#!/usr/bin/env python3
"""Confirmatory analysis for the blind multi-judge tutor-behavior panel.

The unit of inference is a sampled educational context (or a paired context for
prompt effects), never an individual judge score.  Semantic scores are reduced
to a response-level median before confirmatory analyses.
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
import os
from pathlib import Path
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/llm-persona-matplotlib")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.stats import spearmanr, wilcoxon
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score, brier_score_loss, cohen_kappa_score, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from run_behavioral_pilot import ALL_FEATURES
from run_semantic_judge import DIMENSIONS
from semantic_panel_exclusions import load_excluded_items


JUDGES = ("MiniMax-M3", "glm-5.2", "deepseek-v4-pro")
JUDGE_FAMILIES = {
    "MiniMax-M3": {"minimax-m3", "minimax-m2.7"},
    "glm-5.2": {"glm-5.2"},
    "deepseek-v4-pro": {"deepseek-v4-pro"},
}
ARM = {
    "mathtutorbench_scaffolding": "generic",
    "mathtutorbench_pedagogy": "pedagogy",
    "mathtutorbench_scaffolding_hard": "generic",
    "mathtutorbench_pedagogy_hard": "pedagogy",
    "mathtutorbench_socratic": "socratic",
    "longtutor_teaching": "longitudinal",
}
TASK = {
    "mathtutorbench_scaffolding": "mathdial_standard",
    "mathtutorbench_pedagogy": "mathdial_standard",
    "mathtutorbench_scaffolding_hard": "mathdial_hard",
    "mathtutorbench_pedagogy_hard": "mathdial_hard",
    "mathtutorbench_socratic": "socratic",
    "longtutor_teaching": "longtutor",
}


def latest_successes(path: Path) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]], int]:
    latest: dict[str, dict[str, Any]] = {}
    invalid = 0
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                invalid += 1
                continue
            annotation_id = str(row.get("annotation_id") or "")
            if annotation_id:
                latest[annotation_id] = row
    successes = {
        key: row for key, row in latest.items()
        if row.get("annotation") and not row.get("error")
    }
    return latest, successes, invalid


def expected_ids(manifest: dict[str, Any], excluded: set[tuple[str, str]]) -> set[str]:
    return {
        f"{item['benchmark']}|{item['item_id']}|{judge}"
        for item in manifest["items"] for judge in JUDGES
        if (str(item["benchmark"]), str(item["item_id"])) not in excluded
    }


def unblind(successes: dict[str, dict[str, Any]]) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    for row in successes.values():
        annotation = row["annotation"]
        for label, model in row["candidate_mapping"].items():
            scores = annotation["candidates"][label]
            for dimension in DIMENSIONS:
                records.append({
                    "benchmark": row["benchmark"],
                    "task": TASK[row["benchmark"]],
                    "arm": ARM[row["benchmark"]],
                    "item_id": str(row["item_id"]),
                    "pair_id": str(row["pair_id"]),
                    "model": model,
                    "response_sha256": row["response_sha256"][model],
                    "judge": row["judge"],
                    "candidate_label": label,
                    "candidate_position": ord(label) - ord("A") + 1,
                    "dimension": dimension,
                    "score": int(scores[dimension]),
                    "confidence": int(annotation["confidence"]),
                    "same_family": model in JUDGE_FAMILIES[row["judge"]],
                })
    return pd.DataFrame.from_records(records)


def response_consensus(ratings: pd.DataFrame) -> pd.DataFrame:
    keys = ["benchmark", "task", "arm", "item_id", "pair_id", "model", "response_sha256", "dimension"]
    return ratings.groupby(keys, as_index=False).agg(
        score=("score", "median"),
        score_mean=("score", "mean"),
        judge_count=("judge", "nunique"),
    )


def icc3(matrix: np.ndarray, average: bool) -> float:
    """Shrout-Fleiss ICC(3,1) or ICC(3,k), fixed raters, consistency."""
    n, k = matrix.shape
    if n < 2 or k < 2:
        return math.nan
    row_mean = matrix.mean(axis=1, keepdims=True)
    col_mean = matrix.mean(axis=0, keepdims=True)
    grand = matrix.mean()
    ms_row = k * np.sum((row_mean - grand) ** 2) / (n - 1)
    residual = matrix - row_mean - col_mean + grand
    ms_error = np.sum(residual**2) / ((n - 1) * (k - 1))
    if average:
        return float((ms_row - ms_error) / ms_row) if ms_row else math.nan
    denom = ms_row + (k - 1) * ms_error
    return float((ms_row - ms_error) / denom) if denom else math.nan


def agreement_tables(ratings: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    target = ["benchmark", "item_id", "model", "dimension"]
    rows = []
    for dimension in DIMENSIONS:
        subset = ratings[ratings["dimension"] == dimension]
        wide = subset.pivot_table(index=target, columns="judge", values="score", aggfunc="last").dropna()
        for left, right in itertools.combinations(JUDGES, 2):
            if left not in wide or right not in wide:
                continue
            x, y = wide[left].to_numpy(), wide[right].to_numpy()
            rho = spearmanr(x, y).statistic if np.std(x) and np.std(y) else math.nan
            rows.append({
                "dimension": dimension, "judge_left": left, "judge_right": right,
                "n": len(wide), "exact_agreement": float(np.mean(x == y)),
                "within_one": float(np.mean(np.abs(x - y) <= 1)),
                "spearman": float(rho),
                "quadratic_weighted_kappa": float(cohen_kappa_score(x, y, weights="quadratic")),
                "mean_difference_left_minus_right": float(np.mean(x - y)),
            })
    pairwise = pd.DataFrame(rows)
    icc_rows = []
    for dimension in DIMENSIONS:
        subset = ratings[ratings["dimension"] == dimension]
        wide = subset.pivot_table(index=["benchmark", "item_id", "model"], columns="judge", values="score").dropna()
        available = [judge for judge in JUDGES if judge in wide]
        values = wide[available].to_numpy()
        icc_rows.append({
            "dimension": dimension, "targets": len(wide),
            "judges": len(available), "icc_3_1": icc3(values, average=False), "icc_3_k": icc3(values, average=True),
            "score_sd": float(np.std(values)),
        })
    return pairwise, pd.DataFrame(icc_rows)


def bh_adjust(pvalues: pd.Series) -> pd.Series:
    p = pvalues.fillna(1.0).to_numpy(float)
    order = np.argsort(p)
    ranked = p[order]
    adjusted = np.minimum.accumulate((ranked * len(p) / np.arange(1, len(p) + 1))[::-1])[::-1]
    result = np.empty(len(p))
    result[order] = np.minimum(adjusted, 1.0)
    return pd.Series(result, index=pvalues.index)


def cluster_bootstrap_mean(values: pd.DataFrame, cluster: str, value: str, reps: int, seed: int) -> tuple[float, float]:
    grouped = values.groupby(cluster)[value].mean().to_numpy(float)
    if not len(grouped):
        return math.nan, math.nan
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, len(grouped), size=(reps, len(grouped)))
    means = grouped[indices].mean(axis=1)
    return float(np.quantile(means, .025)), float(np.quantile(means, .975))


def prompt_effects(consensus: pd.DataFrame, reps: int, seed: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    paired = consensus[consensus["task"].isin(["mathdial_standard", "mathdial_hard"])]
    rows = []
    item_rows = []
    for (task, model, dimension), group in paired.groupby(["task", "model", "dimension"]):
        wide = group.pivot_table(index="pair_id", columns="arm", values="score", aggfunc="last").dropna()
        if not {"generic", "pedagogy"}.issubset(wide):
            continue
        delta = (wide["pedagogy"] - wide["generic"]).rename("delta").reset_index()
        delta["task"], delta["model"], delta["dimension"] = task, model, dimension
        item_rows.append(delta)
        ci_low, ci_high = cluster_bootstrap_mean(delta, "pair_id", "delta", reps, seed)
        try:
            p = float(wilcoxon(delta["delta"], alternative="two-sided").pvalue) if np.any(delta["delta"] != 0) else 1.0
        except ValueError:
            p = 1.0
        rows.append({
            "task": task, "model": model, "dimension": dimension, "paired_contexts": len(delta),
            "generic_mean": float(wide["generic"].mean()), "pedagogy_mean": float(wide["pedagogy"].mean()),
            "mean_delta": float(delta["delta"].mean()), "median_delta": float(delta["delta"].median()),
            "ci_low": ci_low, "ci_high": ci_high, "wilcoxon_p": p,
            "positive_fraction": float((delta["delta"] > 0).mean()),
            "negative_fraction": float((delta["delta"] < 0).mean()),
        })
    effects = pd.DataFrame(rows)
    if len(effects):
        effects["bh_q_within_task"] = effects.groupby("task", group_keys=False)["wilcoxon_p"].apply(bh_adjust)
    return effects, pd.concat(item_rows, ignore_index=True) if item_rows else pd.DataFrame()


def centered_profiles(consensus: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    data = consensus.copy()
    data["centered_score"] = data["score"] - data.groupby(
        ["benchmark", "item_id", "dimension"]
    )["score"].transform("mean")
    scale = data.groupby(["benchmark", "dimension"])["centered_score"].transform("std").replace(0, np.nan)
    data["z_centered_score"] = (data["centered_score"] / scale).fillna(0)
    profiles = data.groupby(["benchmark", "task", "arm", "model", "dimension"], as_index=False).agg(
        raw_mean=("score", "mean"), centered_mean=("centered_score", "mean"),
        z_centered_mean=("z_centered_score", "mean"), contexts=("item_id", "nunique"),
    )
    return data, profiles


def task_stability(profiles: pd.DataFrame) -> pd.DataFrame:
    base = profiles[profiles["arm"].isin(["generic", "socratic", "longitudinal"])]
    rows = []
    for dimension in DIMENSIONS:
        wide = base[base["dimension"] == dimension].pivot_table(
            index="model", columns="task", values="z_centered_mean", aggfunc="last"
        ).dropna(axis=1)
        rank_corrs = []
        for a, b in itertools.combinations(wide.columns, 2):
            rho = spearmanr(wide[a], wide[b]).statistic if wide[a].std() and wide[b].std() else math.nan
            if np.isfinite(rho):
                rank_corrs.append(rho)
        rows.append({
            "dimension": dimension, "models": len(wide), "tasks": len(wide.columns),
            "icc_3_1_across_tasks": icc3(wide.to_numpy(), average=False),
            "median_pairwise_task_spearman": float(np.median(rank_corrs)) if rank_corrs else math.nan,
            "min_pairwise_task_spearman": float(np.min(rank_corrs)) if rank_corrs else math.nan,
        })
    return pd.DataFrame(rows)


def partial_eta_after_item(values: np.ndarray) -> float:
    grand = values.mean()
    item_mean = values.mean(axis=1, keepdims=True)
    model_mean = values.mean(axis=0, keepdims=True)
    residual = values - item_mean - model_mean + grand
    ss_model = values.shape[0] * float(np.sum((model_mean - grand) ** 2))
    ss_error = float(np.sum(residual**2))
    return ss_model / (ss_model + ss_error) if ss_model + ss_error else math.nan


def model_variance(consensus: pd.DataFrame, reps: int, seed: int) -> pd.DataFrame:
    rows = []
    rng = np.random.default_rng(seed)
    for (benchmark, dimension), group in consensus.groupby(["benchmark", "dimension"]):
        pivot = group.pivot_table(index="item_id", columns="model", values="score", aggfunc="last").dropna()
        values = pivot.to_numpy(float)
        model_mean = values.mean(axis=0, keepdims=True)
        eta = partial_eta_after_item(values)
        indices = rng.integers(0, len(values), size=(reps, len(values)))
        boot = np.asarray([partial_eta_after_item(values[index]) for index in indices])
        finite_boot = boot[np.isfinite(boot)]
        ci_low = float(np.quantile(finite_boot, .025)) if len(finite_boot) else math.nan
        ci_high = float(np.quantile(finite_boot, .975)) if len(finite_boot) else math.nan
        rows.append({
            "benchmark": benchmark, "dimension": dimension, "contexts": len(pivot),
            "models": len(pivot.columns), "partial_eta_squared_model_after_item": eta,
            "bootstrap_ci_low": ci_low,
            "bootstrap_ci_high": ci_high,
            "max_minus_min_model_mean": float(np.ptp(model_mean)),
        })
    return pd.DataFrame(rows)


def self_family_bias(ratings: pd.DataFrame, reps: int, seed: int) -> pd.DataFrame:
    keys = ["benchmark", "item_id", "model", "dimension"]
    data = ratings.copy()
    data["others_mean"] = data.groupby(keys)["score"].transform(lambda x: (x.sum() - x) / (len(x) - 1))
    data["deviation_from_other_judges"] = data["score"] - data["others_mean"]
    rows = []
    rng = np.random.default_rng(seed)
    for (judge, dimension), group in data.groupby(["judge", "dimension"]):
        batch_differences = []
        for _, batch in group.groupby(["benchmark", "item_id"]):
            own = batch.loc[batch["same_family"], "deviation_from_other_judges"]
            other = batch.loc[~batch["same_family"], "deviation_from_other_judges"]
            if len(own) and len(other):
                batch_differences.append(float(own.mean() - other.mean()))
        values = np.asarray(batch_differences)
        valid = values[np.isfinite(values)]
        if len(valid):
            observed = float(valid.mean())
            indices = rng.integers(0, len(valid), size=(reps, len(valid)))
            boot = valid[indices].mean(axis=1)
            ci_low, ci_high = float(np.quantile(boot, .025)), float(np.quantile(boot, .975))
        else:
            observed = math.nan
            ci_low = ci_high = math.nan
        rows.append({
            "judge": judge, "dimension": dimension, "context_batches": len(valid),
            "own_minus_other_residual": observed, "ci_low": ci_low, "ci_high": ci_high,
        })
    return pd.DataFrame(rows)


def position_bias(ratings: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    keys = ["benchmark", "item_id", "model", "dimension"]
    data = ratings.copy()
    data["other_judge_mean"] = data.groupby(keys)["score"].transform(
        lambda values: (values.sum() - values) / (len(values) - 1) if len(values) > 1 else math.nan
    )
    data["position_residual"] = data["score"] - data["other_judge_mean"]
    means = data.groupby(
        ["judge", "dimension", "candidate_position"], as_index=False
    ).agg(mean_residual=("position_residual", "mean"), ratings=("position_residual", "count"))
    rows = []
    for (judge, dimension), group in data.dropna(subset=["position_residual"]).groupby(["judge", "dimension"]):
        x = group["candidate_position"].to_numpy(float)
        y = group["position_residual"].to_numpy(float)
        slope = float(np.polyfit(x, y, 1)[0]) if len(np.unique(x)) > 1 else math.nan
        position_means = group.groupby("candidate_position")["position_residual"].mean()
        rows.append({
            "judge": judge, "dimension": dimension, "ratings": len(group),
            "residual_points_per_position_slope": slope,
            "max_minus_min_position_mean": float(position_means.max() - position_means.min()),
        })
    return means, pd.DataFrame(rows)


def leave_one_judge_out(ratings: pd.DataFrame) -> pd.DataFrame:
    full, full_profiles = centered_profiles(response_consensus(ratings))
    full_vector = full_profiles.set_index(["benchmark", "model", "dimension"])["z_centered_mean"]
    rows = []
    available = sorted(ratings["judge"].unique())
    if len(available) < 2:
        return pd.DataFrame(columns=["excluded_judge", "profile_cells", "spearman_vs_all_judges"])
    for excluded in available:
        _, profiles = centered_profiles(response_consensus(ratings[ratings["judge"] != excluded]))
        vector = profiles.set_index(["benchmark", "model", "dimension"])["z_centered_mean"]
        common = full_vector.index.intersection(vector.index)
        rho = spearmanr(full_vector.loc[common], vector.loc[common]).statistic
        rows.append({"excluded_judge": excluded, "profile_cells": len(common), "spearman_vs_all_judges": float(rho)})
    return pd.DataFrame(rows)


def quality_incremental(consensus: pd.DataFrame, features_path: Path) -> pd.DataFrame:
    features = pd.read_csv(features_path, dtype={"item_id": str})
    wide_semantic = consensus.pivot_table(
        index=["benchmark", "item_id", "model", "response_sha256"], columns="dimension", values="score"
    ).reset_index()
    data = features.merge(wide_semantic, on=["benchmark", "item_id", "model", "response_sha256"], how="inner")
    data = data[data["benchmark"].str.startswith("mathtutorbench_")].dropna(subset=["outcome_primary"])
    data["quality_binary"] = (data["outcome_primary"] > .5).astype(int)
    feature_sets = {
        "task_item_only": [], "transparent_only": ALL_FEATURES,
        "semantic_only": list(DIMENSIONS), "transparent_plus_semantic": ALL_FEATURES + list(DIMENSIONS),
    }
    rows = []
    for heldout in sorted(data["model"].unique()):
        train, test = data[data["model"] != heldout], data[data["model"] == heldout]
        if test["quality_binary"].nunique() < 2 or train["quality_binary"].nunique() < 2:
            continue
        for name, numeric in feature_sets.items():
            transformers = [("item", OneHotEncoder(handle_unknown="ignore"), ["benchmark", "item_id"])]
            if numeric:
                transformers.append(("numeric", StandardScaler(), numeric))
            pipeline = make_pipeline(
                ColumnTransformer(transformers),
                LogisticRegression(max_iter=4000, class_weight="balanced", C=1.0),
            )
            pipeline.fit(train, train["quality_binary"])
            prob = pipeline.predict_proba(test)[:, 1]
            pred = (prob >= .5).astype(int)
            rows.append({
                "held_out_model": heldout, "feature_set": name, "n_test": len(test),
                "auc": roc_auc_score(test["quality_binary"], prob),
                "brier": brier_score_loss(test["quality_binary"], prob),
                "accuracy": accuracy_score(test["quality_binary"], pred),
            })
    result = pd.DataFrame(rows)
    if len(result):
        baseline = result[result["feature_set"] == "transparent_only"].set_index("held_out_model")["auc"]
        result["auc_gain_vs_transparent"] = result.apply(
            lambda r: r["auc"] - baseline.get(r["held_out_model"], math.nan), axis=1
        )
    return result


def heldout_task_attribution(consensus: pd.DataFrame, features_path: Path) -> pd.DataFrame:
    features = pd.read_csv(features_path, dtype={"item_id": str})
    wide_semantic = consensus.pivot_table(
        index=["benchmark", "task", "item_id", "model", "response_sha256"],
        columns="dimension", values="score",
    ).reset_index()
    data = features.merge(
        wide_semantic, on=["benchmark", "item_id", "model", "response_sha256"], how="inner"
    )
    data["task"] = data["task"]
    feature_sets = {
        "length_only": ["log_chars", "log_tokens"],
        "transparent": ALL_FEATURES,
        "semantic": list(DIMENSIONS),
        "transparent_plus_semantic": ALL_FEATURES + list(DIMENSIONS),
    }
    all_numeric = sorted(set(itertools.chain.from_iterable(feature_sets.values())))
    for feature in all_numeric:
        data[feature] = data[feature] - data.groupby(["benchmark", "item_id"])[feature].transform("mean")
        scale = data.groupby("benchmark")[feature].transform("std").replace(0, np.nan)
        data[feature] = (data[feature] / scale).fillna(0)
    rows = []
    for heldout in sorted(data["task"].unique()):
        train, test = data[data["task"] != heldout], data[data["task"] == heldout]
        for name, columns in feature_sets.items():
            clf = make_pipeline(
                StandardScaler(),
                LogisticRegression(max_iter=4000, class_weight="balanced", C=1.0),
            )
            clf.fit(train[columns], train["model"])
            pred = clf.predict(test[columns])
            rows.append({
                "held_out_task": heldout, "feature_set": name, "n_train": len(train), "n_test": len(test),
                "accuracy": accuracy_score(test["model"], pred),
                "balanced_accuracy": balanced_accuracy_score(test["model"], pred),
            })
    return pd.DataFrame(rows)


def dialogue_act_convergence(consensus: pd.DataFrame, dialogue_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    acts = pd.read_csv(dialogue_path, dtype={"item_id": str, "pair_id": str})
    acts = acts[acts["classifier_variant"] == "hybrid_svm"]
    wide = consensus.pivot_table(
        index=["benchmark", "item_id", "pair_id", "model", "response_sha256"],
        columns="dimension", values="score"
    ).reset_index()
    data = acts.merge(wide, on=["benchmark", "item_id", "pair_id", "model", "response_sha256"], how="inner")
    summaries = data.groupby("predicted_act")[list(DIMENSIONS)].agg(["mean", "count"])
    summaries.columns = [f"{a}_{b}" for a, b in summaries.columns]
    summaries = summaries.reset_index()
    contrasts = []
    for dimension in DIMENSIONS:
        telling = data.loc[data["predicted_act"] == "telling", dimension]
        eliciting = data.loc[data["predicted_act"].isin(["probing", "focus"]), dimension]
        contrasts.append({
            "dimension": dimension, "telling_n": len(telling), "probing_or_focus_n": len(eliciting),
            "telling_minus_probing_or_focus": float(telling.mean() - eliciting.mean()),
        })
    return summaries, pd.DataFrame(contrasts)


def interdimension_correlations(consensus: pd.DataFrame) -> pd.DataFrame:
    wide = consensus.pivot_table(
        index=["benchmark", "item_id", "model"], columns="dimension", values="score"
    )
    return wide[list(DIMENSIONS)].corr(method="spearman")


def save_figures(output_dir: Path, profiles: pd.DataFrame, effects: pd.DataFrame, agreement: pd.DataFrame) -> None:
    sns.set_theme(style="whitegrid")
    generic = profiles[profiles["arm"].isin(["generic", "socratic", "longitudinal"])]
    heat = generic.groupby(["model", "dimension"])["z_centered_mean"].mean().unstack()
    fig, ax = plt.subplots(figsize=(11, 5))
    sns.heatmap(heat[list(DIMENSIONS)], center=0, cmap="vlag", ax=ax)
    ax.set_title("Cross-task tutor behavioral profiles (within-context centered)")
    fig.tight_layout(); fig.savefig(output_dir / "semantic_model_profiles.png", dpi=180); plt.close(fig)
    if len(effects):
        heat = effects.groupby(["model", "dimension"])["mean_delta"].mean().unstack()
        fig, ax = plt.subplots(figsize=(11, 5))
        sns.heatmap(heat[list(DIMENSIONS)], center=0, cmap="vlag", ax=ax)
        ax.set_title("Explicit-pedagogy prompt effects")
        fig.tight_layout(); fig.savefig(output_dir / "semantic_prompt_effects.png", dpi=180); plt.close(fig)
    if len(agreement):
        fig, ax = plt.subplots(figsize=(10, 4))
        sns.boxplot(agreement, x="dimension", y="quadratic_weighted_kappa", ax=ax)
        ax.tick_params(axis="x", rotation=35); ax.set_title("Pairwise judge agreement")
        fig.tight_layout(); fig.savefig(output_dir / "semantic_judge_agreement.png", dpi=180); plt.close(fig)


def render_report(
    coverage: dict[str, Any], ratings: pd.DataFrame, consensus: pd.DataFrame,
    pairwise: pd.DataFrame, iccs: pd.DataFrame, stability: pd.DataFrame,
    variance: pd.DataFrame, effects: pd.DataFrame, self_bias: pd.DataFrame,
    loo: pd.DataFrame, quality: pd.DataFrame, act_contrasts: pd.DataFrame,
    attribution: pd.DataFrame, position_slopes: pd.DataFrame,
) -> str:
    quality_summary = quality.groupby("feature_set")[["auc", "brier", "auc_gain_vs_transparent"]].mean().reset_index() if len(quality) else pd.DataFrame()
    return "\n".join([
        "# Confirmatory semantic panel", "",
        f"Coverage: **{coverage['success']:,}/{coverage['expected']:,}** annotations; "
        f"**{consensus[['benchmark','item_id','model']].drop_duplicates().shape[0]:,}** response-level units; "
        f"**{len(DIMENSIONS)}** prespecified descriptive dimensions.", "",
        "Candidate identity was blinded independently for each judge. The confirmatory unit is the response-level median across judges. "
        "The labels are prespecified candidate behavioral dimensions, not human personality traits; only dimensions passing the reported validity gates are interpreted as dispositions.", "",
        "## Judge reliability", "", iccs.to_markdown(index=False, floatfmt=".3f"), "",
        "Pairwise means:", "", pairwise.groupby("dimension")[["exact_agreement", "within_one", "spearman", "quadratic_weighted_kappa"]].mean().reset_index().to_markdown(index=False, floatfmt=".3f") if len(pairwise) else "Not yet estimable.", "",
        "## Cross-task stability", "", stability.to_markdown(index=False, floatfmt=".3f"), "",
        "With six models, these are finite-panel descriptive stability estimates; they are not population-level psychometrics.", "",
        "### Held-out-task model attribution", "",
        attribution.groupby("feature_set")[["accuracy", "balanced_accuracy"]].mean().reset_index().to_markdown(index=False, floatfmt=".3f") if len(attribution) else "Not estimable.", "",
        "Chance is 0.167. Attribution demonstrates a cross-task signature, not by itself a validated disposition.", "",
        "## Model variance after exact-context control", "", variance.groupby("dimension")[["partial_eta_squared_model_after_item", "max_minus_min_model_mean"]].mean().reset_index().to_markdown(index=False, floatfmt=".3f"), "",
        "## Same-context prompt intervention", "", effects.groupby(["task", "dimension"]).agg(mean_delta=("mean_delta", "mean"), models_positive=("mean_delta", lambda x: int((x > 0).sum())), models_negative=("mean_delta", lambda x: int((x < 0).sum())), models_bh_significant=("bh_q_within_task", lambda x: int((x < .05).sum()))).reset_index().to_markdown(index=False, floatfmt=".3f") if len(effects) else "Not yet estimable.", "",
        "## Judge-family bias audit", "", self_bias.groupby("judge")["own_minus_other_residual"].mean().reset_index().to_markdown(index=False, floatfmt=".3f"), "",
        "Positive values mean the judge scored same-family candidates higher than its residual relative to the other two judges; this is a bias diagnostic, not proof of favoritism.", "",
        "## Candidate-position audit", "",
        position_slopes.groupby("judge")[["residual_points_per_position_slope", "max_minus_min_position_mean"]].mean().reset_index().to_markdown(index=False, floatfmt=".3f") if len(position_slopes) else "Not yet estimable.", "",
        "Residuals compare each judge with the other judges on the identical response and dimension. Candidate order was independently randomized, so a nonzero position slope diagnoses presentation bias.", "",
        "## Leave-one-judge-out robustness", "", loo.to_markdown(index=False, floatfmt=".3f"), "",
        "## Incremental association with existing response quality", "", quality_summary.to_markdown(index=False, floatfmt=".3f") if len(quality_summary) else "Not estimable.", "",
        "AUC is evaluated by holding out each candidate model. Association is not evidence that a disposition causally improves learning.", "",
        "## Independent dialogue-act convergence", "", act_contrasts.to_markdown(index=False, floatfmt=".3f") if len(act_contrasts) else "Not estimable.", "",
        "The classifier was trained only on existing human MathDial dialogue-act labels. This validates alignment with observed tutor moves, not student learning gains.", "",
        "## Interpretation boundary", "",
        "A defensible paper claim requires convergence of reliability, cross-task stability, exact-context model variance, intervention sensitivity, and independent action validity. "
        "Any dimension failing those gates must be reported as context-specific or measurement-limited rather than as a stable disposition.", "",
    ])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--panel-dir", type=Path, required=True)
    parser.add_argument("--features", type=Path, required=True)
    parser.add_argument("--dialogue-acts", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--exclusions", type=Path)
    parser.add_argument("--bootstrap-reps", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=20260819)
    parser.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    manifest = json.loads((args.panel_dir / "sample_manifest.json").read_text(encoding="utf-8"))
    excluded = load_excluded_items(args.exclusions, manifest)
    latest, successes, invalid = latest_successes(args.panel_dir / "annotations.jsonl")
    expected = expected_ids(manifest, excluded)
    successes = {key: row for key, row in successes.items() if key in expected}
    missing = expected - set(successes)
    errors = {key for key in expected if key in latest and key not in successes}
    if (missing or errors or invalid) and not args.allow_incomplete:
        raise SystemExit(f"coverage gate failed: success={len(successes)}/{len(expected)}, errors={len(errors)}, invalid_lines={invalid}")
    coverage = {
        "manifest_batches": len(manifest["items"]),
        "excluded_batches": len(excluded),
        "analyzed_batches": len(manifest["items"]) - len(excluded),
        "expected": len(expected), "success": len(successes), "missing": len(missing),
        "errors": len(errors), "invalid_jsonl": invalid,
    }
    (args.output_dir / "coverage.json").write_text(json.dumps(coverage, indent=2) + "\n", encoding="utf-8")

    ratings = unblind(successes)
    consensus = response_consensus(ratings)
    if not args.allow_incomplete:
        expected_ratings = len(expected) * len(inventory_models := manifest.get("core_models", [])) * len(DIMENSIONS)
        if not inventory_models:
            inventory_models = sorted(ratings["model"].unique())
            expected_ratings = len(expected) * len(inventory_models) * len(DIMENSIONS)
        analyzed_batches = len(manifest["items"]) - len(excluded)
        expected_response_units = analyzed_batches * len(inventory_models)
        expected_consensus = expected_response_units * len(DIMENSIONS)
        failures = []
        if len(inventory_models) != 6:
            failures.append(f"candidate_models={len(inventory_models)} (expected 6)")
        if len(ratings) != expected_ratings:
            failures.append(f"ratings={len(ratings)} (expected {expected_ratings})")
        if len(consensus) != expected_consensus:
            failures.append(f"consensus_rows={len(consensus)} (expected {expected_consensus})")
        bad_judge_counts = int((consensus["judge_count"] != len(JUDGES)).sum())
        if bad_judge_counts:
            failures.append(f"consensus_rows_without_three_judges={bad_judge_counts}")
        response_units = consensus[["benchmark", "item_id", "model", "response_sha256"]].drop_duplicates().shape[0]
        if response_units != expected_response_units:
            failures.append(f"response_units={response_units} (expected {expected_response_units})")
        if failures:
            raise SystemExit("response-level completeness gate failed: " + "; ".join(failures))
    pairwise, iccs = agreement_tables(ratings)
    centered, profiles = centered_profiles(consensus)
    stability = task_stability(profiles)
    variance = model_variance(consensus, args.bootstrap_reps, args.seed)
    effects, item_effects = prompt_effects(consensus, args.bootstrap_reps, args.seed)
    bias = self_family_bias(ratings, args.bootstrap_reps, args.seed)
    position_means, position_slopes = position_bias(ratings)
    loo = leave_one_judge_out(ratings)
    quality = quality_incremental(consensus, args.features)
    attribution = heldout_task_attribution(consensus, args.features)
    act_summary, act_contrasts = dialogue_act_convergence(consensus, args.dialogue_acts)
    dimension_corr = interdimension_correlations(consensus)

    outputs = {
        "unblinded_ratings.csv": ratings, "response_consensus.csv": consensus,
        "judge_pairwise_agreement.csv": pairwise, "judge_icc.csv": iccs,
        "centered_response_scores.csv": centered, "semantic_profiles.csv": profiles,
        "cross_task_stability.csv": stability, "model_variance_after_item_control.csv": variance,
        "prompt_effects.csv": effects, "prompt_item_deltas.csv": item_effects,
        "judge_family_bias.csv": bias, "leave_one_judge_out.csv": loo,
        "candidate_position_means.csv": position_means, "candidate_position_slopes.csv": position_slopes,
        "quality_incremental_validity.csv": quality, "dialogue_act_semantic_means.csv": act_summary,
        "heldout_task_model_attribution.csv": attribution,
        "dialogue_act_semantic_contrasts.csv": act_contrasts,
    }
    for name, frame in outputs.items():
        frame.to_csv(args.output_dir / name, index=False)
    dimension_corr.to_csv(args.output_dir / "interdimension_spearman.csv")
    save_figures(args.output_dir, profiles, effects, pairwise)
    report = render_report(coverage, ratings, consensus, pairwise, iccs, stability, variance, effects, bias, loo, quality, act_contrasts, attribution, position_slopes)
    (args.output_dir / "semantic_panel_report.md").write_text(report, encoding="utf-8")
    print(args.output_dir / "semantic_panel_report.md")


if __name__ == "__main__":
    main()
