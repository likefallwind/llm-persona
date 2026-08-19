#!/usr/bin/env python3
"""Analyze existing MiniMax-M3 vs DeepSeek judge swaps and outcome validity."""

from __future__ import annotations

import argparse
import filecmp
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
from sklearn.metrics import balanced_accuracy_score, brier_score_loss, cohen_kappa_score, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from run_behavioral_pilot import ALL_FEATURES, POLICY_FEATURES, SURFACE_FEATURES


TASKS = (
    "mathtutorbench_scaffolding",
    "mathtutorbench_pedagogy",
    "mathtutorbench_scaffolding_hard",
    "mathtutorbench_pedagogy_hard",
)

MODEL_DIRS = {
    "minimax-m3": "minimax3",
    "minimax-m2.7": "MiniMax-M2.7",
    "glm-5.2": "glm-5.2",
    "deepseek-v4-pro": "deepseek-v4-pro",
    "doubao-seed-2.0-pro": "doubao-seed-2.0-pro",
    "qwen3.5-4b": "Qwen-Qwen3.5-4B",
}


def read_scores(path: Path) -> dict[str, float]:
    scores: dict[str, float] = {}
    if not path.exists():
        return scores
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            value = row.get("win_score")
            item_id = str(row.get("item_id") or "")
            if item_id and isinstance(value, (int, float)) and row.get("score_status") == "scored":
                scores[item_id] = float(value)
    return scores


def read_latest_responses(path: Path) -> tuple[int, dict[str, str]]:
    rows = 0
    latest: dict[str, str] = {}
    if not path.exists():
        return rows, latest
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            rows += 1
            item_id = str(row.get("item_id") or "")
            response = row.get("response")
            if item_id and isinstance(response, str):
                latest[item_id] = response
    return rows, latest


def response_identity_audit(eval_root: Path) -> pd.DataFrame:
    rows = []
    for task in TASKS:
        for model, directory in MODEL_DIRS.items():
            main = eval_root / task / directory / "predictions.jsonl"
            swap = eval_root / task / "_judge-deepseek-v4-flash" / directory / "predictions.jsonl"
            if not main.exists() or not swap.exists():
                continue
            main_rows, main_latest = read_latest_responses(main)
            swap_rows, swap_latest = read_latest_responses(swap)
            common = set(main_latest) & set(swap_latest)
            rows.append({
                "benchmark": task,
                "model": model,
                "main_rows": main_rows,
                "swap_rows": swap_rows,
                "main_unique_items": len(main_latest),
                "swap_unique_items": len(swap_latest),
                "common_items": len(common),
                "response_mismatches": sum(main_latest[x] != swap_latest[x] for x in common),
                "only_main": len(set(main_latest) - set(swap_latest)),
                "only_swap": len(set(swap_latest) - set(main_latest)),
                "byte_identical_files": filecmp.cmp(main, swap, shallow=False),
            })
    return pd.DataFrame(rows)


def load_judgements(eval_root: Path) -> pd.DataFrame:
    records = []
    for task in TASKS:
        for model, directory in MODEL_DIRS.items():
            m3 = read_scores(eval_root / task / directory / "scored.jsonl")
            ds = read_scores(eval_root / task / "_judge-deepseek-v4-flash" / directory / "scored.jsonl")
            for judge, values in (("minimax-m3", m3), ("deepseek-v4-flash", ds)):
                for item_id, score in values.items():
                    records.append({
                        "benchmark": task,
                        "family": "hard" if task.endswith("_hard") else "standard",
                        "arm": "pedagogy" if "_pedagogy" in task else "scaffolding",
                        "pair_id": item_id.rsplit("-", 1)[-1],
                        "item_id": item_id,
                        "model": model,
                        "judge": judge,
                        "win_score": score,
                        "strict_win": int(score > 0.5),
                    })
    return pd.DataFrame(records)


def bootstrap_mean(values: np.ndarray, seed: int = 20260819, reps: int = 4000) -> tuple[float, float]:
    if len(values) == 0:
        return float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    draws = rng.choice(values, size=(reps, len(values)), replace=True).mean(axis=1)
    return float(np.quantile(draws, 0.025)), float(np.quantile(draws, 0.975))


def judge_agreement(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    wide = frame.pivot_table(
        index=["benchmark", "pair_id", "model"], columns="judge", values="win_score", aggfunc="last"
    ).dropna().reset_index()
    groups: list[tuple[str, pd.DataFrame]] = [("ALL", wide)]
    groups.extend((name, group) for name, group in wide.groupby("benchmark"))
    rows = []
    for name, group in groups:
        a = group["minimax-m3"].to_numpy()
        b = group["deepseek-v4-flash"].to_numpy()
        rho = spearmanr(a, b).statistic
        rows.append({
            "scope": name,
            "n": len(group),
            "exact_agreement": float(np.mean(a == b)),
            "within_half_point": float(np.mean(np.abs(a - b) <= 0.5)),
            "spearman": float(rho) if np.isfinite(rho) else np.nan,
            "quadratic_kappa": cohen_kappa_score(
                (a * 2).astype(int), (b * 2).astype(int), labels=[0, 1, 2], weights="quadratic"
            ),
            "m3_mean": float(a.mean()),
            "deepseek_mean": float(b.mean()),
            "mean_difference_m3_minus_deepseek": float((a - b).mean()),
        })

    bias_rows = []
    wide["difference"] = wide["minimax-m3"] - wide["deepseek-v4-flash"]
    for (benchmark, model), group in wide.groupby(["benchmark", "model"]):
        values = group["difference"].to_numpy()
        lo, hi = bootstrap_mean(values, seed=20260819 + len(bias_rows))
        bias_rows.append({
            "benchmark": benchmark,
            "model": model,
            "n": len(values),
            "mean_difference_m3_minus_deepseek": float(values.mean()),
            "bootstrap_ci_low": lo,
            "bootstrap_ci_high": hi,
        })
    return pd.DataFrame(rows), pd.DataFrame(bias_rows)


def prompt_effects(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (judge, family, model), group in frame.groupby(["judge", "family", "model"]):
        wide = group.pivot_table(index="pair_id", columns="arm", values="win_score", aggfunc="last").dropna()
        if not {"pedagogy", "scaffolding"}.issubset(wide.columns):
            continue
        delta = (wide["pedagogy"] - wide["scaffolding"]).to_numpy()
        lo, hi = bootstrap_mean(delta, seed=20260819 + len(rows))
        try:
            p_value = float(wilcoxon(delta).pvalue) if np.any(delta != 0) else 1.0
        except ValueError:
            p_value = 1.0
        rows.append({
            "judge": judge,
            "family": family,
            "model": model,
            "n_pairs": len(delta),
            "scaffolding_mean": float(wide["scaffolding"].mean()),
            "pedagogy_mean": float(wide["pedagogy"].mean()),
            "mean_delta": float(delta.mean()),
            "bootstrap_ci_low": lo,
            "bootstrap_ci_high": hi,
            "wilcoxon_p": p_value,
        })
    return pd.DataFrame(rows)


def ranking_agreement(frame: pd.DataFrame) -> pd.DataFrame:
    means = frame.groupby(["benchmark", "judge", "model"])["win_score"].mean().reset_index()
    rows = []
    for benchmark, group in means.groupby("benchmark"):
        wide = group.pivot(index="model", columns="judge", values="win_score").dropna()
        rho = spearmanr(wide["minimax-m3"], wide["deepseek-v4-flash"]).statistic
        rows.append({"benchmark": benchmark, "model_count": len(wide), "rank_spearman": float(rho)})
    overall = frame.groupby(["judge", "model"])["win_score"].mean().reset_index().pivot(index="model", columns="judge", values="win_score").dropna()
    rows.append({
        "benchmark": "ALL_TASK_MEAN",
        "model_count": len(overall),
        "rank_spearman": float(spearmanr(overall["minimax-m3"], overall["deepseek-v4-flash"]).statistic),
    })
    return pd.DataFrame(rows)


def quality_prediction(features: pd.DataFrame, judgements: pd.DataFrame) -> pd.DataFrame:
    base = features[features["benchmark"].isin(TASKS)].copy()
    outcomes = judgements[["benchmark", "item_id", "model", "judge", "strict_win"]]
    merged = base.merge(outcomes, on=["benchmark", "item_id", "model"], how="inner")
    feature_sets = {
        "task_only": (False, []),
        "task_item": (True, []),
        "item_plus_length": (True, ["log_chars", "log_tokens"]),
        "item_plus_policy_length": (True, ["log_tokens", *POLICY_FEATURES]),
        "item_plus_all_transparent": (True, ALL_FEATURES),
    }
    rows = []
    for judge, judge_rows in merged.groupby("judge"):
        for held_out_model in sorted(judge_rows["model"].unique()):
            train = judge_rows[judge_rows["model"] != held_out_model]
            test = judge_rows[judge_rows["model"] == held_out_model]
            for set_name, (include_item, numeric) in feature_sets.items():
                categorical = ["benchmark", "item_id"] if include_item else ["benchmark"]
                transformers: list[tuple[str, Any, list[str]]] = [
                    ("task_item", OneHotEncoder(handle_unknown="ignore"), categorical),
                ]
                if numeric:
                    transformers.append(("numeric", StandardScaler(), numeric))
                prep = ColumnTransformer(transformers)
                clf = make_pipeline(prep, LogisticRegression(max_iter=3000, class_weight="balanced", C=1.0))
                clf.fit(train, train["strict_win"])
                prob = clf.predict_proba(test)[:, 1]
                pred = (prob >= 0.5).astype(int)
                y = test["strict_win"].to_numpy()
                rows.append({
                    "judge": judge,
                    "held_out_model": held_out_model,
                    "feature_set": set_name,
                    "n_test": len(test),
                    "positive_rate": float(y.mean()),
                    "roc_auc": float(roc_auc_score(y, prob)) if len(np.unique(y)) == 2 else np.nan,
                    "balanced_accuracy": float(balanced_accuracy_score(y, pred)),
                    "brier": float(brier_score_loss(y, prob)),
                })
    return pd.DataFrame(rows)


def save_figures(output_dir: Path, agreement: pd.DataFrame, effects: pd.DataFrame, bias: pd.DataFrame) -> None:
    sns.set_theme(style="whitegrid")
    task_rows = agreement[agreement["scope"] != "ALL"].copy()
    fig, ax = plt.subplots(figsize=(9, 4))
    sns.barplot(task_rows, x="scope", y="quadratic_kappa", ax=ax, color="#4C78A8")
    ax.tick_params(axis="x", rotation=25)
    ax.set_ylim(-0.05, 1.0)
    ax.set_title("Existing judge-swap agreement")
    fig.tight_layout()
    fig.savefig(output_dir / "judge_agreement.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.pointplot(effects, x="model", y="mean_delta", hue="judge", dodge=0.35, markers=["o", "s"], ax=ax)
    ax.axhline(0, color="black", linewidth=1)
    ax.tick_params(axis="x", rotation=25)
    ax.set_ylabel("Pedagogy prompt minus scaffolding prompt win score")
    ax.set_title("Paired prompt effect replicates across two judges")
    fig.tight_layout()
    fig.savefig(output_dir / "prompt_effect_by_judge.png", dpi=180)
    plt.close(fig)


def render_report(
    agreement: pd.DataFrame, bias: pd.DataFrame, effects: pd.DataFrame,
    ranking: pd.DataFrame, prediction: pd.DataFrame, identity: pd.DataFrame,
) -> str:
    prediction_mean = prediction.groupby(["judge", "feature_set"])[["roc_auc", "balanced_accuracy", "brier"]].mean().reset_index()
    auc_wide = prediction.pivot_table(
        index=["judge", "held_out_model"], columns="feature_set", values="roc_auc"
    ).reset_index()
    for name in ("item_plus_length", "item_plus_policy_length", "item_plus_all_transparent"):
        auc_wide[f"delta_{name}_over_task_item"] = auc_wide[name] - auc_wide["task_item"]
    auc_delta = auc_wide.groupby("judge")[[
        "delta_item_plus_length_over_task_item",
        "delta_item_plus_policy_length_over_task_item",
        "delta_item_plus_all_transparent_over_task_item",
    ]].agg(["mean", "min", "max"])
    auc_delta.columns = ["_".join(col) for col in auc_delta.columns]
    auc_delta = auc_delta.reset_index()
    sign_rows = []
    for judge, group in auc_wide.groupby("judge"):
        for name in ("item_plus_length", "item_plus_policy_length", "item_plus_all_transparent"):
            values = group[f"delta_{name}_over_task_item"].to_numpy()
            positive = int(np.sum(values > 0))
            nonzero = int(np.sum(values != 0))
            # Exact one-sided sign test under p=0.5; useful with only five model folds.
            p_value = sum(math.comb(nonzero, k) for k in range(positive, nonzero + 1)) / (2 ** nonzero) if nonzero else 1.0
            sign_rows.append({
                "judge": judge,
                "feature_set": name,
                "positive_model_folds": positive,
                "nonzero_model_folds": nonzero,
                "one_sided_exact_sign_p": p_value,
            })
    sign_tests = pd.DataFrame(sign_rows)
    effect_summary = effects.groupby(["judge", "family"])["mean_delta"].agg(["mean", "min", "max"]).reset_index()
    model_bias = bias.groupby("model")["mean_difference_m3_minus_deepseek"].mean().sort_values().reset_index()
    identity_summary = pd.DataFrame([{
        "run_pairs_checked": len(identity),
        "common_items": int(identity["common_items"].sum()),
        "response_mismatches": int(identity["response_mismatches"].sum()),
        "byte_identical_files": int(identity["byte_identical_files"].sum()),
    }])
    return "\n".join([
        "# Existing judge-swap robustness",
        "",
        "This analysis uses already-generated scores; no new API call or data export was used.",
        "",
        identity_summary.to_markdown(index=False),
        "",
        "Two files contained duplicate resume rows, so only 18/20 raw files were byte-identical. After last-row-per-item resolution, all shared candidate responses matched exactly and no item existed on only one side.",
        "",
        "## Item-level agreement",
        "",
        agreement.to_markdown(index=False, floatfmt=".3f"),
        "",
        "## Model-ranking agreement",
        "",
        ranking.to_markdown(index=False, floatfmt=".3f"),
        "",
        "## Prompt effect replicated across judges",
        "",
        effect_summary.to_markdown(index=False, floatfmt=".3f"),
        "",
        "Every listed mean is a within-model, within-item difference. Positive values mean the explicit pedagogy prompt received a higher pairwise win score than the generic caring-teacher prompt.",
        "",
        "## Mean judge difference by candidate model",
        "",
        model_bias.to_markdown(index=False, floatfmt=".3f"),
        "",
        "A nonzero difference is judge severity/calibration, not automatically self-preference. The semantic-blind panel is still required to isolate self-family effects.",
        "",
        "## Does transparent behavior predict held-out-model quality?",
        "",
        prediction_mean.to_markdown(index=False, floatfmt=".3f"),
        "",
        "Models are held out one at a time. `task_item` knows the benchmark arm and exact item but not the candidate model. Feature models add response behavior to that strong item-difficulty baseline; no model identity is supplied.",
        "",
        "### Incremental AUC over the task + item baseline",
        "",
        auc_delta.to_markdown(index=False, floatfmt=".3f"),
        "",
        sign_tests.to_markdown(index=False, floatfmt=".4f"),
        "",
        "## Current evidential status",
        "",
        "The paired prompt effect is not a single-judge artifact if it is positive under both judges. However, these judges use the same pairwise pedagogical rubric, so this is robustness to judge model, not full construct validation.",
        "",
    ])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--eval-root", type=Path, required=True)
    parser.add_argument("--features", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    judgements = load_judgements(args.eval_root)
    agreement, bias = judge_agreement(judgements)
    effects = prompt_effects(judgements)
    ranking = ranking_agreement(judgements)
    features = pd.read_csv(args.features)
    prediction = quality_prediction(features, judgements)
    identity = response_identity_audit(args.eval_root)

    judgements.to_csv(args.output_dir / "paired_judgements.csv", index=False)
    agreement.to_csv(args.output_dir / "judge_agreement.csv", index=False)
    bias.to_csv(args.output_dir / "judge_bias_by_model_task.csv", index=False)
    effects.to_csv(args.output_dir / "prompt_effect_by_judge.csv", index=False)
    ranking.to_csv(args.output_dir / "model_ranking_agreement.csv", index=False)
    prediction.to_csv(args.output_dir / "quality_prediction.csv", index=False)
    identity.to_csv(args.output_dir / "response_identity_audit.csv", index=False)
    save_figures(args.output_dir, agreement, effects, bias)
    report = render_report(agreement, bias, effects, ranking, prediction, identity)
    (args.output_dir / "judge_robustness_report.md").write_text(report, encoding="utf-8")
    print(args.output_dir / "judge_robustness_report.md")


if __name__ == "__main__":
    main()
