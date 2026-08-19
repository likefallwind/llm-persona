#!/usr/bin/env python3
"""Run a deterministic, no-annotation pilot on paired tutor responses.

The pilot is intentionally conservative: it measures transparent surface and
pedagogical-action proxies, never treats them as validated latent traits, and
stores derived features rather than copying raw upstream responses.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/llm-persona-matplotlib")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.stats import spearmanr, wilcoxon
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from inventory_paths import resolve_inventory_path


PATTERNS = {
    "second_person": r"\b(?:you|your|yours|yourself)\b|你(?:们|的|自己)?|同学",
    "first_plural": r"\b(?:we|our|ours|let['’]?s)\b|我们|咱们|一起",
    "praise": r"\b(?:great|good job|well done|nice|excellent|correct|exactly)\b|很好|真棒|做得好|答对|正确|不错",
    "encouragement": r"\b(?:keep going|you can|try again|don['’]?t worry)\b|加油|别担心|再试|你可以|相信你",
    "hedge": r"\b(?:maybe|perhaps|might|could|seem|likely|possibly)\b|可能|也许|似乎|或许|大概",
    "imperative": r"\b(?:try|look|find|identify|calculate|consider|remember|notice|check|tell me|think about)\b|请|试着|看看|找出|想一想|计算|注意|回忆|告诉我|检查",
    "history_reference": r"\b(?:previous|earlier|last time|history|before)\b|之前|上次|刚才|历史|曾经|第\s*\d+\s*题|\[\d+\]",
    "answer_reveal": r"\b(?:the answer is|final answer|equals?|therefore)\b|答案是|最终答案|所以(?:结果)?是|等于",
    "explanation": r"\b(?:because|since|this means|the reason|explain)\b|因为|原因|这意味着|解释|关键(?:是|点)",
    "diagnosis": r"\b(?:mistake|error|confus|misunderstand|incorrect)\w*\b|错误|出错|混淆|误解|问题在|错在",
}

SURFACE_FEATURES = [
    "log_chars", "log_tokens", "line_count", "sentence_count",
    "mean_sentence_tokens", "markdown_heading_rate", "bullet_rate",
    "numbered_step_rate", "latex_rate", "emoji_rate", "table_present",
]
POLICY_FEATURES = [
    "question_rate", "ends_question", "exactly_one_question",
    "second_person_rate", "first_plural_rate", "praise_rate",
    "encouragement_rate", "hedge_rate", "imperative_rate",
    "history_reference_rate", "answer_reveal_rate", "explanation_rate",
    "diagnosis_rate",
]
ALL_FEATURES = SURFACE_FEATURES + POLICY_FEATURES


def occurrences(pattern: str, text: str) -> int:
    return len(re.findall(pattern, text, flags=re.IGNORECASE))


def extract_features(text: str) -> dict[str, float]:
    chars = len(text)
    tokens = re.findall(r"[A-Za-z]+(?:['’][A-Za-z]+)?|\d+(?:\.\d+)?|[\u4e00-\u9fff]", text)
    token_count = max(1, len(tokens))
    sentences = [part for part in re.split(r"[.!?。！？]+", text) if part.strip()]
    sentence_count = max(1, len(sentences))
    question_count = text.count("?") + text.count("？")
    lines = text.splitlines() or [text]
    nonempty_lines = [line for line in lines if line.strip()]
    rate = lambda n: 100.0 * n / token_count
    pattern_rates = {
        f"{name}_rate": rate(occurrences(pattern, text))
        for name, pattern in PATTERNS.items()
    }
    emoji_count = occurrences(r"[\U0001F300-\U0001FAFF]|[☺☹❤♥★☆✓✔✨]", text)
    features = {
        "log_chars": math.log1p(chars),
        "log_tokens": math.log1p(token_count),
        "line_count": float(len(nonempty_lines)),
        "sentence_count": float(sentence_count),
        "mean_sentence_tokens": token_count / sentence_count,
        "question_rate": rate(question_count),
        "ends_question": float(text.rstrip().endswith(("?", "？"))),
        "exactly_one_question": float(question_count == 1),
        "markdown_heading_rate": rate(sum(bool(re.match(r"^\s*#{1,6}\s", line)) for line in lines)),
        "bullet_rate": rate(sum(bool(re.match(r"^\s*[-*•]\s+", line)) for line in lines)),
        "numbered_step_rate": rate(sum(bool(re.match(r"^\s*\d+[.)、]\s*", line)) for line in lines)),
        "latex_rate": rate(text.count("$") + text.count("\\(" ) + text.count("\\[")),
        "emoji_rate": rate(emoji_count),
        "table_present": float(any("|" in line for line in nonempty_lines)),
        **pattern_rates,
    }
    return features


def read_latest_success(path: Path) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            item_id = str(row.get("item_id") or "")
            response = row.get("response")
            if item_id and isinstance(response, str) and response.strip() and not row.get("error"):
                latest[item_id] = row
    return latest


def read_scored(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    latest: dict[str, dict[str, Any]] = {}
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            item_id = str(row.get("item_id") or "")
            if item_id:
                latest[item_id] = row
    return latest


def outcome_fields(row: dict[str, Any]) -> dict[str, float | None]:
    normalized = row.get("normalized")
    result: dict[str, float | None] = {
        "outcome_primary": None,
        "history_utilization": None,
        "strategy_alignment": None,
        "coherence": None,
        "appropriateness": None,
    }
    if isinstance(row.get("win_score"), (int, float)):
        result["outcome_primary"] = float(row["win_score"])
    elif isinstance(normalized, (int, float)):
        result["outcome_primary"] = float(normalized)
    elif isinstance(normalized, dict):
        vals = []
        for key in ("history_utilization", "strategy_alignment", "coherence", "appropriateness"):
            if isinstance(normalized.get(key), (int, float)):
                result[key] = float(normalized[key])
                vals.append(float(normalized[key]))
        if vals:
            result["outcome_primary"] = float(np.mean(vals))
    return result


def load_manifest(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def build_feature_frame(
    inventory: dict[str, Any], roles: dict[str, Any], models: list[str] | None = None,
    role_section: str = "primary_behavior_generation",
) -> pd.DataFrame:
    primary = roles[role_section]
    core_models = models or inventory["core_models"]
    selected = {
        (run["benchmark"], run["model"]): run
        for run in inventory["selected_runs"]
    }
    records: list[dict[str, Any]] = []
    for benchmark, metadata in primary.items():
        if not all((benchmark, model) in selected for model in core_models):
            continue
        predictions = {
            model: read_latest_success(resolve_inventory_path(selected[(benchmark, model)]["predictions_path"]))
            for model in core_models
        }
        common_items = set.intersection(*(set(rows) for rows in predictions.values()))
        scored = {}
        for model in core_models:
            pred_path = resolve_inventory_path(selected[(benchmark, model)]["predictions_path"])
            scored[model] = read_scored(pred_path.with_name("scored.jsonl"))
        for item_id in sorted(common_items):
            for model in core_models:
                response = predictions[model][item_id]["response"]
                record: dict[str, Any] = {
                    "benchmark": benchmark,
                    "family": metadata.get("family", benchmark),
                    "prompt_arm": metadata.get("paired_prompt_arm", "none"),
                    "item_id": item_id,
                    "model": model,
                    "response_sha256": hashlib.sha256(response.encode("utf-8")).hexdigest(),
                    **extract_features(response),
                    **outcome_fields(scored[model].get(item_id, {})),
                }
                records.append(record)
    return pd.DataFrame.from_records(records)


def classification_results(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, np.ndarray]]:
    feature_sets = {
        "length_only": ["log_chars", "log_tokens"],
        "surface": SURFACE_FEATURES,
        "policy": POLICY_FEATURES,
        "surface_plus_policy": ALL_FEATURES,
    }
    rows = []
    cms: dict[str, np.ndarray] = {}
    labels = sorted(frame["model"].unique())
    for set_name, features in feature_sets.items():
        cm_total = np.zeros((len(labels), len(labels)), dtype=int)
        for family in sorted(frame["family"].unique()):
            train = frame[frame["family"] != family]
            test = frame[frame["family"] == family]
            clf = make_pipeline(
                StandardScaler(),
                LogisticRegression(max_iter=3000, class_weight="balanced", C=1.0),
            )
            clf.fit(train[features], train["model"])
            pred = clf.predict(test[features])
            rows.append({
                "feature_set": set_name,
                "held_out_family": family,
                "n_test": len(test),
                "accuracy": accuracy_score(test["model"], pred),
                "balanced_accuracy": balanced_accuracy_score(test["model"], pred),
            })
            cm_total += confusion_matrix(test["model"], pred, labels=labels)
        cms[set_name] = cm_total
    return pd.DataFrame(rows), cms


def icc3_1(matrix: np.ndarray) -> float:
    """Shrout-Fleiss ICC(3,1): consistency across fixed task occasions."""
    n, k = matrix.shape
    if n < 2 or k < 2:
        return float("nan")
    row_means = matrix.mean(axis=1, keepdims=True)
    col_means = matrix.mean(axis=0, keepdims=True)
    grand = matrix.mean()
    ms_rows = k * np.sum((row_means - grand) ** 2) / (n - 1)
    residual = matrix - row_means - col_means + grand
    ms_error = np.sum(residual**2) / ((n - 1) * (k - 1))
    denom = ms_rows + (k - 1) * ms_error
    return float((ms_rows - ms_error) / denom) if denom else float("nan")


def stability_results(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    centered = frame.copy()
    for feature in ALL_FEATURES:
        centered[feature] = centered[feature] - centered.groupby(["benchmark", "item_id"])[feature].transform("mean")
        scale = centered.groupby("benchmark")[feature].transform("std").replace(0, np.nan)
        centered[feature] = (centered[feature] / scale).fillna(0.0)
    profile = centered.groupby(["model", "benchmark"])[ALL_FEATURES].mean().reset_index()
    rows = []
    for feature in ALL_FEATURES:
        pivot = profile.pivot(index="model", columns="benchmark", values=feature).dropna(axis=1)
        cors = []
        for i in range(pivot.shape[1]):
            for j in range(i + 1, pivot.shape[1]):
                corr = spearmanr(pivot.iloc[:, i], pivot.iloc[:, j]).statistic
                if np.isfinite(corr):
                    cors.append(float(corr))
        rows.append({
            "feature": feature,
            "icc3_1": icc3_1(pivot.to_numpy()),
            "mean_pairwise_spearman": float(np.mean(cors)) if cors else float("nan"),
            "task_count": pivot.shape[1],
        })
    return pd.DataFrame(rows).sort_values("icc3_1", ascending=False), profile


def benjamini_hochberg(p_values: list[float]) -> list[float]:
    n = len(p_values)
    order = np.argsort(p_values)
    adjusted = np.empty(n, dtype=float)
    running = 1.0
    for rank_index in range(n - 1, -1, -1):
        original_index = order[rank_index]
        rank = rank_index + 1
        running = min(running, p_values[original_index] * n / rank)
        adjusted[original_index] = running
    return adjusted.tolist()


def intervention_results(frame: pd.DataFrame) -> pd.DataFrame:
    paired = frame[frame["prompt_arm"].isin(["generic_caring_teacher", "explicit_learnlm_pedagogy"])].copy()
    paired["pair_id"] = paired["item_id"].str.extract(r"(\d+)$", expand=False)
    rows = []
    for family in sorted(paired["family"].unique()):
        subset = paired[paired["family"] == family]
        for model in sorted(subset["model"].unique()):
            model_rows = subset[subset["model"] == model]
            for feature in ALL_FEATURES + ["outcome_primary"]:
                pivot = model_rows.pivot_table(index="pair_id", columns="prompt_arm", values=feature, aggfunc="last").dropna()
                if pivot.empty or not {"generic_caring_teacher", "explicit_learnlm_pedagogy"}.issubset(pivot.columns):
                    continue
                delta = pivot["explicit_learnlm_pedagogy"] - pivot["generic_caring_teacher"]
                sd = float(delta.std(ddof=1))
                try:
                    p_value = float(wilcoxon(delta).pvalue) if np.any(delta != 0) else 1.0
                except ValueError:
                    p_value = 1.0
                rows.append({
                    "family": family,
                    "model": model,
                    "feature": feature,
                    "n_pairs": len(delta),
                    "generic_mean": float(pivot["generic_caring_teacher"].mean()),
                    "pedagogy_mean": float(pivot["explicit_learnlm_pedagogy"].mean()),
                    "mean_delta": float(delta.mean()),
                    "paired_dz": float(delta.mean() / sd) if sd else 0.0,
                    "wilcoxon_p": p_value,
                })
    result = pd.DataFrame(rows, columns=[
        "family", "model", "feature", "n_pairs", "generic_mean", "pedagogy_mean",
        "mean_delta", "paired_dz", "wilcoxon_p",
    ])
    if not result.empty:
        result["bh_q"] = benjamini_hochberg(result["wilcoxon_p"].tolist())
    return result


def save_figures(output_dir: Path, frame: pd.DataFrame, cms: dict[str, np.ndarray], profile: pd.DataFrame) -> None:
    sns.set_theme(style="whitegrid")
    labels = sorted(frame["model"].unique())
    fig, ax = plt.subplots(figsize=(8, 7))
    sns.heatmap(cms["policy"], annot=True, fmt="d", cmap="Blues", xticklabels=labels, yticklabels=labels, ax=ax)
    ax.set_xlabel("Predicted model")
    ax.set_ylabel("True model")
    ax.set_title("Leave-one-task-family-out model attribution: policy proxies")
    fig.tight_layout()
    fig.savefig(output_dir / "policy_confusion_matrix.png", dpi=180)
    plt.close(fig)

    aggregated = frame.groupby("model")[POLICY_FEATURES].mean()
    z = (aggregated - aggregated.mean()) / aggregated.std(ddof=0).replace(0, np.nan)
    fig, ax = plt.subplots(figsize=(12, 5))
    sns.heatmap(z.fillna(0), center=0, cmap="vlag", ax=ax)
    ax.set_title("Descriptive policy-proxy profile (not validated traits)")
    fig.tight_layout()
    fig.savefig(output_dir / "policy_proxy_profile.png", dpi=180)
    plt.close(fig)


def render_report(frame: pd.DataFrame, classification: pd.DataFrame, stability: pd.DataFrame, intervention: pd.DataFrame) -> str:
    mean_cls = classification.groupby("feature_set")[["accuracy", "balanced_accuracy"]].mean().sort_values("balanced_accuracy", ascending=False)
    stable = stability.head(8)
    intervention_focus = intervention[
        intervention["feature"].isin(["question_rate", "answer_reveal_rate", "praise_rate", "imperative_rate", "log_tokens", "outcome_primary"])
    ].sort_values(["family", "feature", "model"])
    return "\n".join([
        "# Deterministic behavioral pilot",
        "",
        f"Paired responses analyzed: **{len(frame):,}** across **{frame['benchmark'].nunique()}** benchmark arms and **{frame['model'].nunique()}** models.",
        "",
        "All features are transparent lexical/action proxies. They are useful for falsification and pipeline validation but are not yet validated pedagogical dispositions.",
        "",
        "## Held-out task-family model attribution",
        "",
        f"Chance accuracy is {1 / frame['model'].nunique():.3f}. Each fold withholds an entire task family.",
        "",
        mean_cls.to_markdown(floatfmt=".3f"),
        "",
        "## Most cross-task-stable proxies",
        "",
        "Features are centered within each item across models before task aggregation, removing item-level content difficulty.",
        "",
        stable.to_markdown(index=False, floatfmt=".3f"),
        "",
        "## Paired prompt intervention (selected endpoints)",
        "",
        "Delta = explicit LearnLM-style pedagogy prompt minus generic caring-teacher prompt on the same conversation and model.",
        "",
        intervention_focus.to_markdown(index=False, floatfmt=".4f") if not intervention_focus.empty else "No paired prompt intervention is defined for this role section.",
        "",
        "## Interpretation boundary",
        "",
        "Above-chance attribution demonstrates a reproducible signature, not personality. The next stage must replace proxy-only interpretation with multi-judge behavioral coding, outcome prediction, judge-swap robustness, and preregistered confirmatory analyses.",
        "",
    ])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--roles", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model-panel", choices=("core", "extended"), default="core")
    parser.add_argument(
        "--role-section",
        choices=("primary_behavior_generation", "external_criteria", "negative_controls", "judge_only"),
        default="primary_behavior_generation",
    )
    args = parser.parse_args()

    inventory = load_manifest(args.inventory)
    roles = load_manifest(args.roles)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    models = inventory["core_models"] if args.model_panel == "core" else inventory["extended_models"]
    frame = build_feature_frame(
        inventory, roles, models=models, role_section=args.role_section,
    )
    frame.to_csv(args.output_dir / "behavior_features.csv", index=False)
    classification, cms = classification_results(frame)
    classification.to_csv(args.output_dir / "classification.csv", index=False)
    stability, profile = stability_results(frame)
    stability.to_csv(args.output_dir / "stability.csv", index=False)
    profile.to_csv(args.output_dir / "task_profiles.csv", index=False)
    intervention = intervention_results(frame)
    intervention.to_csv(args.output_dir / "prompt_intervention.csv", index=False)
    save_figures(args.output_dir, frame, cms, profile)
    report = render_report(frame, classification, stability, intervention)
    (args.output_dir / "pilot_report.md").write_text(report, encoding="utf-8")
    print(args.output_dir / "pilot_report.md")


if __name__ == "__main__":
    main()
