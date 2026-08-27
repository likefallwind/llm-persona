#!/usr/bin/env python3
"""Explore objective epistemic-character axes in frozen EduBenchmark outputs.

The analysis never exports prompts, responses, reasoning, gold answers, or item
text.  It distinguishes behavior tendencies (revision, expressed confidence,
and abstention) from their competence consequences (fixing/breaking answers,
calibration, and answerability discrimination).
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from analyze_semantic_panel import icc3


MODEL_DIRS = {
    "minimax-m3": "minimax3",
    "minimax-m2.7": "MiniMax-M2.7",
    "glm-5.2": "glm-5.2",
    "deepseek-v4-pro": "deepseek-v4-pro",
    "doubao-seed-2.0-pro": "doubao-seed-2.0-pro",
    "qwen3.5-4b": "Qwen-Qwen3.5-4B",
}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            # Retain only derived fields needed below. Raw text must never enter
            # an output dataframe or a serialized artifact.
            rows.append({
                key: row.get(key)
                for key in (
                    "item_id", "source_benchmark", "score_status", "correct",
                    "confidence", "r1_correct", "changed", "r2_missing",
                    "answerable", "abstained", "answered", "category",
                )
            })
    return rows


def safe_spearman(left: pd.Series, right: pd.Series) -> float:
    if len(left) < 3 or left.nunique() < 2 or right.nunique() < 2:
        return math.nan
    return float(spearmanr(left, right).statistic)


def profile_stability(
    cells: pd.DataFrame, context_col: str, value_col: str, axis: str,
) -> dict[str, Any]:
    wide = cells.pivot(index="model", columns=context_col, values=value_col).dropna()
    correlations: list[float] = []
    for left, right in itertools.combinations(wide.columns, 2):
        rho = safe_spearman(wide[left], wide[right])
        if math.isfinite(rho):
            correlations.append(rho)
    icc = icc3(wide.to_numpy(float), average=False) if wide.shape[1] >= 2 else math.nan
    median_rho = float(np.median(correlations)) if correlations else math.nan
    minimum_rho = float(np.min(correlations)) if correlations else math.nan
    icc_pass = bool(math.isfinite(icc) and icc >= 0.50)
    rank_pass = bool(math.isfinite(median_rho) and median_rho >= 0.50)
    return {
        "axis": axis,
        "models": int(wide.shape[0]),
        "contexts": int(wide.shape[1]),
        "icc_3_1": float(icc),
        "median_pairwise_spearman": median_rho,
        "minimum_pairwise_spearman": minimum_rho,
        "icc_gate": icc_pass,
        "rank_gate": rank_pass,
        "stability_strength": (
            "robust_both_metrics" if icc_pass and rank_pass
            else "mixed_one_metric" if icc_pass or rank_pass
            else "unsupported"
        ),
    }


def selfcheck_cells(root: Path) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    for model, directory in MODEL_DIRS.items():
        path = root / "p07_selfcheck" / directory / "scored.jsonl"
        for row in load_jsonl(path):
            if row["score_status"] != "scored" or row["r2_missing"]:
                continue
            records.append({
                "model": model,
                "source": str(row["source_benchmark"]),
                "r1_correct": bool(row["r1_correct"]),
                "r2_correct": bool(row["correct"]),
                "changed": bool(row["changed"]),
            })
    data = pd.DataFrame(records)
    grouped: list[dict[str, Any]] = []
    for (model, source), group in data.groupby(["model", "source"], sort=True):
        wrong = ~group["r1_correct"]
        right = group["r1_correct"]
        fixed = wrong & group["r2_correct"]
        broken = right & ~group["r2_correct"]
        grouped.append({
            "model": model,
            "source": source,
            "n": len(group),
            "revision_propensity": float(group["changed"].mean()),
            "round1_accuracy": float(group["r1_correct"].mean()),
            "round2_accuracy": float(group["r2_correct"].mean()),
            "net_revision_gain": float((fixed.sum() - broken.sum()) / len(group)),
            "fix_rate_given_wrong": float(fixed.sum() / wrong.sum()) if wrong.sum() else math.nan,
            "break_rate_given_right": float(broken.sum() / right.sum()) if right.sum() else math.nan,
        })
    return pd.DataFrame(grouped)


def calibration_cells(root: Path) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    for model, directory in MODEL_DIRS.items():
        path = root / "p08_calibration" / directory / "scored.jsonl"
        for row in load_jsonl(path):
            confidence = row["confidence"]
            if row["score_status"] != "scored" or confidence is None:
                continue
            records.append({
                "model": model,
                "source": str(row["source_benchmark"]),
                "correct": bool(row["correct"]),
                "confidence": float(confidence) / 100.0,
            })
    data = pd.DataFrame(records)
    grouped: list[dict[str, Any]] = []
    for (model, source), group in data.groupby(["model", "source"], sort=True):
        confidence = group["confidence"].clip(0, 1)
        correctness = group["correct"].astype(float)
        grouped.append({
            "model": model,
            "source": source,
            "n": len(group),
            "expressed_confidence": float(confidence.mean()),
            "accuracy": float(correctness.mean()),
            "overconfidence_gap": float(confidence.mean() - correctness.mean()),
            "brier": float(np.mean((confidence - correctness) ** 2)),
            "high_confidence_wrong_rate": float(
                ((confidence >= 0.90) & ~group["correct"]).mean()
            ),
        })
    return pd.DataFrame(grouped)


def abstention_cells(root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    records: list[dict[str, Any]] = []
    for model, directory in MODEL_DIRS.items():
        path = root / "p08_abstention" / directory / "scored.jsonl"
        for row in load_jsonl(path):
            if row["score_status"] != "scored":
                continue
            records.append({
                "model": model,
                "answerable": bool(row["answerable"]),
                "category": "answerable" if row["answerable"] else str(row["category"]),
                "abstained": bool(row["abstained"]),
                "correct": bool(row["correct"]),
            })
    data = pd.DataFrame(records)
    category = data.groupby(["model", "category"], as_index=False).agg(
        n=("correct", "size"),
        abstention_propensity=("abstained", "mean"),
        accuracy=("correct", "mean"),
    )
    profiles: list[dict[str, Any]] = []
    for model, group in data.groupby("model", sort=True):
        answerable = group[group["answerable"]]
        unanswerable = group[~group["answerable"]]
        answerable_abstention = float(answerable["abstained"].mean())
        unanswerable_abstention = float(unanswerable["abstained"].mean())
        profiles.append({
            "model": model,
            "answerable_abstention_rate": answerable_abstention,
            "unanswerable_abstention_rate": unanswerable_abstention,
            "abstention_selectivity": unanswerable_abstention - answerable_abstention,
            "overall_accuracy": float(group["correct"].mean()),
        })
    return category, pd.DataFrame(profiles)


def model_profiles(
    revision: pd.DataFrame,
    confidence: pd.DataFrame,
    abstention: pd.DataFrame,
    semantic_path: Path,
) -> pd.DataFrame:
    left = revision.groupby("model", as_index=False).agg(
        revision_propensity=("revision_propensity", "mean"),
        net_revision_gain=("net_revision_gain", "mean"),
        fix_rate_given_wrong=("fix_rate_given_wrong", "mean"),
        break_rate_given_right=("break_rate_given_right", "mean"),
    )
    middle = confidence.groupby("model", as_index=False).agg(
        expressed_confidence=("expressed_confidence", "mean"),
        accuracy_under_confidence_prompt=("accuracy", "mean"),
        overconfidence_gap=("overconfidence_gap", "mean"),
        brier=("brier", "mean"),
    )
    profiles = left.merge(middle, on="model").merge(abstention, on="model")
    semantic = pd.read_csv(semantic_path)
    caution = (
        semantic[semantic["dimension"] == "epistemic_caution"]
        .groupby("model", as_index=False)["raw_mean"].mean()
        .rename(columns={"raw_mean": "semantic_epistemic_caution"})
    )
    return profiles.merge(caution, on="model", how="left").sort_values("model")


def correlation_table(profiles: pd.DataFrame) -> pd.DataFrame:
    pairs = [
        ("semantic_epistemic_caution", "expressed_confidence"),
        ("semantic_epistemic_caution", "unanswerable_abstention_rate"),
        ("semantic_epistemic_caution", "revision_propensity"),
        ("expressed_confidence", "unanswerable_abstention_rate"),
        ("revision_propensity", "net_revision_gain"),
        ("overconfidence_gap", "abstention_selectivity"),
    ]
    return pd.DataFrame([
        {
            "left": left,
            "right": right,
            "models": int(profiles[[left, right]].dropna().shape[0]),
            "spearman": safe_spearman(
                profiles[[left, right]].dropna()[left],
                profiles[[left, right]].dropna()[right],
            ),
            "status": "descriptive_only_six_models",
        }
        for left, right in pairs
    ])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--edubenchmark-eval-root", type=Path,
        default=Path("../edubenchmark/reports/eval"),
    )
    parser.add_argument(
        "--semantic-profiles", type=Path,
        default=Path("artifacts/prompt_contingent_signatures_v1/default_semantic_profiles.csv"),
    )
    parser.add_argument(
        "--output-dir", type=Path,
        default=Path("artifacts/epistemic_character_axes_v1"),
    )
    args = parser.parse_args()

    revision = selfcheck_cells(args.edubenchmark_eval_root)
    confidence = calibration_cells(args.edubenchmark_eval_root)
    abstention_category, abstention = abstention_cells(args.edubenchmark_eval_root)

    stability = pd.DataFrame([
        profile_stability(revision, "source", "revision_propensity", "revision_propensity"),
        profile_stability(confidence, "source", "expressed_confidence", "expressed_confidence"),
        profile_stability(
            abstention_category[abstention_category["category"] != "answerable"],
            "category", "abstention_propensity", "unanswerable_abstention_propensity",
        ),
    ])
    profiles = model_profiles(revision, confidence, abstention, args.semantic_profiles)
    correlations = correlation_table(profiles)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    revision.to_csv(args.output_dir / "selfcheck_source_cells.csv", index=False)
    confidence.to_csv(args.output_dir / "calibration_source_cells.csv", index=False)
    abstention_category.to_csv(args.output_dir / "abstention_category_cells.csv", index=False)
    profiles.to_csv(args.output_dir / "model_profiles.csv", index=False)
    stability.to_csv(args.output_dir / "cross_context_stability.csv", index=False)
    correlations.to_csv(args.output_dir / "cross_axis_correlations.csv", index=False)

    decision = {
        "status": "outcome_aware_exploratory_existing_data",
        "models": list(MODEL_DIRS),
        "axes": stability.to_dict(orient="records"),
        "robust_trait_like_axes": stability.loc[
            stability["stability_strength"] == "robust_both_metrics", "axis"
        ].tolist(),
        "mixed_stability_axes": stability.loc[
            stability["stability_strength"] == "mixed_one_metric", "axis"
        ].tolist(),
        "interpretation": (
            "Stability supports finite-panel behavioral tendencies only. Accuracy, "
            "calibration, correction quality, and abstention selectivity remain "
            "capabilities or consequences rather than personality dimensions."
        ),
    }
    (args.output_dir / "decision.json").write_text(
        json.dumps(decision, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    report = [
        "# Objective epistemic-character axes",
        "",
        "Status: **outcome-aware exploratory analysis of frozen data**.",
        "No provider response, prompt, reasoning trace, gold answer, or item text is exported.",
        "",
        "## Cross-context stability",
        "",
        stability.to_markdown(index=False, floatfmt=".3f"),
        "",
        "## Fixed-panel profiles",
        "",
        profiles.to_markdown(index=False, floatfmt=".3f"),
        "",
        "## Cross-axis convergence checks",
        "",
        correlations.to_markdown(index=False, floatfmt=".3f"),
        "",
        "## Boundary",
        "",
        "Revision propensity, expressed confidence, and abstention propensity are",
        "observable response tendencies. Their correctness consequences are not",
        "personality. With six fixed systems, correlations are descriptive and cannot",
        "support model-population or latent-trait claims. The semantic caution score",
        "previously failed reliability and cross-task gates, so convergence with it is",
        "a falsifier rather than a requirement that can promote a new disposition.",
        "",
    ]
    (args.output_dir / "report.md").write_text("\n".join(report), encoding="utf-8")


if __name__ == "__main__":
    main()
