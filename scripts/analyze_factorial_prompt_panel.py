#!/usr/bin/env python3
"""Analyze the frozen synthetic factorial policy-intervention panel."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Any

import numpy as np
import pandas as pd


WARMTH_RE = re.compile(
    r"\b(?:great|good job|nice work|well done|you(?:'|’)re close|you(?:'|’)ve got|"
    r"don(?:'|’)t worry|you can do|keep going|encourag\w*|glad|happy to help|"
    r"let(?:'|’)s work through|strong start|good start)\b",
    flags=re.IGNORECASE,
)
FINAL_RE = re.compile(r"\bfinal\s+answer\s*[:=]", flags=re.IGNORECASE)
PRIMARY_METRICS = ("question_first", "answer_reveal_correct", "warmth_marker")
FACTOR_LEVELS = {
    "question_policy": ("question_first", "explain_only"),
    "answer_policy": ("reveal", "withhold"),
    "tone_policy": ("warm", "neutral"),
}
TARGET_METRICS = {
    "question_policy": "question_first",
    "answer_policy": "answer_reveal_correct",
    "tone_policy": "warmth_marker",
}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def first_segment(text: str) -> str:
    stripped = text.lstrip()
    match = re.search(r"[.!?\n]", stripped)
    return stripped[: match.end()] if match else stripped[:250]


def response_metrics(text: str, answer_patterns: list[str]) -> dict[str, Any]:
    final_match = FINAL_RE.search(text)
    correct = False
    if final_match:
        suffix = text[final_match.end() : final_match.end() + 100]
        correct = any(re.search(pattern, suffix, flags=re.IGNORECASE) for pattern in answer_patterns)
    words = re.findall(r"\b\w+(?:['’]\w+)?\b", text, flags=re.UNICODE)
    sentences = [part for part in re.split(r"[.!?]+", text) if part.strip()]
    return {
        "question_first": int("?" in first_segment(text)),
        "question_any": int("?" in text),
        "answer_reveal_any": int(bool(final_match)),
        "answer_reveal_correct": int(correct),
        "warmth_marker": int(bool(WARMTH_RE.search(text))),
        "word_count": len(words),
        "char_count": len(text),
        "sentence_count": len(sentences),
    }


def latest_success(rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    latest: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        key = (str(row.get("sample_id", "")), str(row.get("model", "")))
        if all(key):
            latest[key] = row
    return {
        key: row for key, row in latest.items()
        if isinstance(row.get("response"), str) and row["response"].strip() and not row.get("error")
    }


def build_metric_frame(
    spec: dict[str, Any], manifest: list[dict[str, Any]], response_rows: list[dict[str, Any]],
) -> pd.DataFrame:
    sample_map = {row["sample_id"]: row for row in manifest}
    expected = {(sample_id, model) for sample_id in sample_map for model in spec["models"]}
    successes = latest_success(response_rows)
    if set(successes) != expected:
        missing = sorted(expected - set(successes))[:5]
        unexpected = sorted(set(successes) - expected)[:5]
        raise RuntimeError(
            f"panel incomplete: successes={len(successes)} expected={len(expected)} "
            f"missing={missing} unexpected={unexpected}"
        )
    derived = []
    for key in sorted(expected):
        sample_id, model = key
        sample, response = sample_map[sample_id], successes[key]
        if response.get("prompt_sha256") != sample["prompt_sha256"]:
            raise RuntimeError(f"prompt hash mismatch for {sample_id}|{model}")
        text = response["response"]
        derived.append({
            "sample_id": sample_id,
            "base_id": sample["base_id"],
            "problem_family": sample["problem_family"],
            "learner_need": sample["learner_need"],
            "question_policy": sample["question_policy"],
            "answer_policy": sample["answer_policy"],
            "tone_policy": sample["tone_policy"],
            "model": model,
            "prompt_sha256": sample["prompt_sha256"],
            "response_sha256": hashlib.sha256(text.encode()).hexdigest(),
            **response_metrics(text, sample["accepted_answer_patterns"]),
        })
    return pd.DataFrame(derived)


def difference(frame: pd.DataFrame, column: str, high: str, low: str, metric: str) -> float:
    return float(frame.loc[frame[column] == high, metric].mean() - frame.loc[frame[column] == low, metric].mean())


def bootstrap_ci(frame: pd.DataFrame, column: str, high: str, low: str, metric: str, reps: int, seed: int) -> tuple[float, float]:
    by_base = frame.groupby("base_id").apply(
        lambda group: difference(group, column, high, low, metric),
        include_groups=False,
    ).to_numpy(dtype=float)
    rng = np.random.default_rng(seed)
    draws = rng.choice(by_base, size=(reps, len(by_base)), replace=True).mean(axis=1)
    return float(np.quantile(draws, 0.025)), float(np.quantile(draws, 0.975))


def effect_tables(frame: pd.DataFrame, reps: int, seed: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    family_rows = []
    metrics = list(PRIMARY_METRICS) + ["question_any", "answer_reveal_any", "word_count", "char_count"]
    groups = [("ALL", frame)] + [(model, group) for model, group in frame.groupby("model", sort=True)]
    for group_name, group in groups:
        for factor, (high, low) in FACTOR_LEVELS.items():
            for metric in metrics:
                estimate = difference(group, factor, high, low, metric)
                ci_low, ci_high = bootstrap_ci(
                    group, factor, high, low, metric, reps, seed + len(rows),
                )
                rows.append({
                    "group": group_name, "factor": factor, "high": high, "low": low,
                    "metric": metric, "mean_difference": estimate,
                    "bootstrap_ci_low": ci_low, "bootstrap_ci_high": ci_high,
                    "target_metric": metric == TARGET_METRICS[factor],
                })
    for family, group in frame.groupby("problem_family", sort=True):
        for factor, (high, low) in FACTOR_LEVELS.items():
            metric = TARGET_METRICS[factor]
            family_rows.append({
                "problem_family": family, "factor": factor, "metric": metric,
                "mean_difference": difference(group, factor, high, low, metric),
            })
    return pd.DataFrame(rows), pd.DataFrame(family_rows)


def learner_need_effects(frame: pd.DataFrame, reps: int, seed: int) -> pd.DataFrame:
    rows = []
    groups = [("ALL", frame)] + [(model, group) for model, group in frame.groupby("model", sort=True)]
    for group_name, group in groups:
        contrasts = [
            ("direct_minus_explore_reveal", "direct", "explore", "answer_reveal_correct"),
            ("explore_minus_direct_question", "explore", "direct", "question_first"),
        ]
        for name, high, low, metric in contrasts:
            estimate = difference(group, "learner_need", high, low, metric)
            ci_low, ci_high = bootstrap_ci(
                group, "learner_need", high, low, metric, reps, seed + len(rows),
            )
            rows.append({
                "group": group_name, "contrast": name, "metric": metric,
                "mean_difference": estimate, "bootstrap_ci_low": ci_low,
                "bootstrap_ci_high": ci_high,
            })
    return pd.DataFrame(rows)


def conditional_need_effects(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for factor, levels in FACTOR_LEVELS.items():
        for level in levels:
            subset = frame[frame[factor] == level]
            rows.extend([
                {
                    "condition_factor": factor, "condition_level": level,
                    "contrast": "direct_minus_explore_reveal",
                    "mean_difference": difference(
                        subset, "learner_need", "direct", "explore", "answer_reveal_correct",
                    ),
                },
                {
                    "condition_factor": factor, "condition_level": level,
                    "contrast": "explore_minus_direct_question",
                    "mean_difference": difference(
                        subset, "learner_need", "explore", "direct", "question_first",
                    ),
                },
            ])
    return pd.DataFrame(rows)


def evaluate_gates(spec: dict[str, Any], effects: pd.DataFrame, need: pd.DataFrame) -> dict[str, Any]:
    gates = spec["claim_gates"]
    target_thresholds = {
        "question_policy": float(gates["question_target_mean_difference_min"]),
        "answer_policy": float(gates["answer_target_mean_difference_min"]),
        "tone_policy": float(gates["tone_target_mean_difference_min"]),
    }
    factor_results = {}
    for factor, target_metric in TARGET_METRICS.items():
        overall = effects[(effects.group == "ALL") & (effects.factor == factor)]
        target = float(overall.loc[overall.metric == target_metric, "mean_difference"].iloc[0])
        cross = overall[overall.metric.isin(set(PRIMARY_METRICS) - {target_metric})]
        largest_cross = float(cross.mean_difference.abs().max())
        ratio = float("inf") if largest_cross == 0 else abs(target) / largest_cross
        model_rows = effects[
            (effects.group != "ALL") & (effects.factor == factor) & (effects.metric == target_metric)
        ]
        positive_all = bool((model_rows.mean_difference > 0).all())
        factor_results[factor] = {
            "target_metric": target_metric,
            "target_mean_difference": target,
            "target_threshold": target_thresholds[factor],
            "target_threshold_pass": target >= target_thresholds[factor],
            "positive_in_every_model": positive_all,
            "largest_primary_cross_effect_abs": largest_cross,
            "selectivity_ratio": ratio,
            "selectivity_pass": ratio >= float(gates["selectivity_ratio_min"]),
            "controllable": target >= target_thresholds[factor] and positive_all,
            "selective": target >= target_thresholds[factor] and positive_all and ratio >= float(gates["selectivity_ratio_min"]),
        }
    need_all = need[need.group == "ALL"].set_index("contrast")
    reveal = float(need_all.loc["direct_minus_explore_reveal", "mean_difference"])
    question = float(need_all.loc["explore_minus_direct_question", "mean_difference"])
    return {
        "factor_results": factor_results,
        "learner_need": {
            "direct_minus_explore_reveal": reveal,
            "reveal_threshold": float(gates["learner_need_reveal_difference_min"]),
            "reveal_pass": reveal >= float(gates["learner_need_reveal_difference_min"]),
            "explore_minus_direct_question": question,
            "question_threshold": float(gates["learner_need_question_difference_min"]),
            "question_pass": question >= float(gates["learner_need_question_difference_min"]),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, default=Path("data/factorial_prompt_spec_v1.json"))
    parser.add_argument("--manifest", type=Path, default=Path("artifacts/factorial_prompt_v1/sample_manifest.jsonl"))
    parser.add_argument("--responses", type=Path, default=Path("artifacts/factorial_prompt_v1/run/responses.jsonl"))
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/factorial_analysis_v1"))
    parser.add_argument("--bootstrap-reps", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=20260820)
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    manifest = load_jsonl(args.manifest)
    frame = build_metric_frame(spec, manifest, load_jsonl(args.responses))
    effects, family = effect_tables(frame, args.bootstrap_reps, args.seed)
    need = learner_need_effects(frame, args.bootstrap_reps, args.seed + 10_000)
    conditional = conditional_need_effects(frame)
    decision = evaluate_gates(spec, effects, need)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.output_dir / "derived_response_metrics.csv", index=False)
    effects.to_csv(args.output_dir / "factor_effects.csv", index=False)
    family.to_csv(args.output_dir / "family_target_effects.csv", index=False)
    need.to_csv(args.output_dir / "learner_need_effects.csv", index=False)
    conditional.to_csv(args.output_dir / "conditional_learner_need_effects.csv", index=False)
    report = {
        "schema_version": 1,
        "response_rows": len(frame),
        "models": sorted(frame.model.unique().tolist()),
        "base_problems": int(frame.base_id.nunique()),
        "factor_cells_per_model": int(len(frame) / frame.model.nunique()),
        "decision": decision,
    }
    (args.output_dir / "factorial_analysis_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
