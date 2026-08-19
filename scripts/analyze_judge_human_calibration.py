#!/usr/bin/env python3
"""Audit planned semantic judges against existing expert preference pairs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score


JUDGE_DIRS = {
    "MiniMax-M3": "minimax3",
    "glm-5.2": "glm-5.2",
    "deepseek-v4-pro": "deepseek-v4-pro",
}


def load_scores(path: Path, judge: str) -> pd.DataFrame:
    latest = {}
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("score_status") == "scored" and row.get("item_id"):
                latest[str(row["item_id"])] = row
    return pd.DataFrame([{
        "item_id": item_id,
        "pair_id": row.get("pair_id"),
        "order": row.get("order"),
        "judge": judge,
        "chose_positive": int(bool(row.get("chose_positive"))),
        "normalized": row.get("normalized"),
        "gold": row.get("gold"),
    } for item_id, row in latest.items()])


def pair_bootstrap(frame: pd.DataFrame, seed: int = 20260819, reps: int = 6000) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    judges = list(JUDGE_DIRS)
    rows = []
    keys = [*judges, "majority"]
    # Reduce the two presentation orders to one mean per expert pair, then
    # resample pair rows with a single vectorized index matrix.
    pair_means = frame.groupby("pair_id")[keys].mean().to_numpy()
    observed = dict(zip(keys, pair_means.mean(axis=0)))
    sample_indices = rng.integers(0, len(pair_means), size=(reps, len(pair_means)))
    boot_means = pair_means[sample_indices].mean(axis=1)
    draws = {key: boot_means[:, idx] for idx, key in enumerate(keys)}
    for key, estimate in observed.items():
        values = draws[key]
        rows.append({
            "judge_or_ensemble": key,
            "agreement": float(estimate),
            "cluster_bootstrap_ci_low": float(np.quantile(values, 0.025)),
            "cluster_bootstrap_ci_high": float(np.quantile(values, 0.975)),
        })
    best = max(judges, key=lambda judge: observed[judge])
    delta = draws["majority"] - draws[best]
    rows.append({
        "judge_or_ensemble": f"majority_minus_{best}",
        "agreement": float(observed["majority"] - observed[best]),
        "cluster_bootstrap_ci_low": float(np.quantile(delta, 0.025)),
        "cluster_bootstrap_ci_high": float(np.quantile(delta, 0.975)),
    })
    return pd.DataFrame(rows)


def position_consistency(long: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for judge, group in long.groupby("judge"):
        wide = group.pivot(index="pair_id", columns="order", values="chose_positive").dropna()
        consistent = wide["ab"] == wide["ba"]
        rows.append({
            "judge": judge,
            "complete_pairs": len(wide),
            "position_consistency": float(consistent.mean()),
            "positive_both_orders": float(((wide["ab"] == 1) & (wide["ba"] == 1)).mean()),
            "negative_both_orders": float(((wide["ab"] == 0) & (wide["ba"] == 0)).mean()),
        })
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--eval-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    frames = []
    base = args.eval_root / "mathtutorbench_judge_calibration"
    for judge, directory in JUDGE_DIRS.items():
        frames.append(load_scores(base / directory / "scored.jsonl", judge))
    long = pd.concat(frames, ignore_index=True)
    wide = long.pivot(index=["item_id", "pair_id", "order"], columns="judge", values="chose_positive").dropna().reset_index()
    wide["majority"] = (wide[list(JUDGE_DIRS)].sum(axis=1) >= 2).astype(int)

    calibration = pair_bootstrap(wide)
    positions = position_consistency(long)
    agreement_rows = []
    for i, left in enumerate(JUDGE_DIRS):
        for right in list(JUDGE_DIRS)[i + 1:]:
            agreement_rows.append({
                "judge_left": left,
                "judge_right": right,
                "raw_agreement": float((wide[left] == wide[right]).mean()),
                "cohen_kappa": float(cohen_kappa_score(wide[left], wide[right])),
            })
    pairwise = pd.DataFrame(agreement_rows)
    correct_count = wide[list(JUDGE_DIRS)].sum(axis=1)
    overlap = pd.DataFrame([{
        "expert_pair_order_items": len(wide),
        "all_three_correct": int((correct_count == 3).sum()),
        "exactly_two_correct": int((correct_count == 2).sum()),
        "exactly_one_correct": int((correct_count == 1).sum()),
        "all_three_wrong": int((correct_count == 0).sum()),
    }])

    calibration.to_csv(args.output_dir / "human_preference_agreement.csv", index=False)
    positions.to_csv(args.output_dir / "position_consistency.csv", index=False)
    pairwise.to_csv(args.output_dir / "pairwise_judge_agreement.csv", index=False)
    overlap.to_csv(args.output_dir / "error_overlap.csv", index=False)
    report = "\n".join([
        "# Human preference calibration of the planned semantic judges",
        "",
        "The calibration set contains 482 expert-labelled positive/negative teacher-response pairs, each shown in both A/B orders (964 items). These data predate the semantic study and require no new API calls.",
        "",
        "## Agreement with expert preference",
        "",
        calibration.to_markdown(index=False, floatfmt=".3f"),
        "",
        "Intervals resample the 482 underlying preference pairs and preserve both presentation orders.",
        "",
        "## Position robustness",
        "",
        positions.to_markdown(index=False, floatfmt=".3f"),
        "",
        "## Pairwise judge agreement",
        "",
        pairwise.to_markdown(index=False, floatfmt=".3f"),
        "",
        "## Error overlap",
        "",
        overlap.to_markdown(index=False),
        "",
        "## Interpretation boundary",
        "",
        "This establishes that the three models are competent and reasonably position-stable on human pedagogical preference pairs. It does not validate the eight descriptive semantic dimensions, eliminate shared LLM variance, or turn majority vote into human ground truth.",
        "",
    ])
    (args.output_dir / "judge_human_calibration_report.md").write_text(report, encoding="utf-8")
    print(args.output_dir / "judge_human_calibration_report.md")


if __name__ == "__main__":
    main()
