#!/usr/bin/env python3
"""Stress-test semantic conclusions by excluding each judge in turn."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from analyze_semantic_panel import centered_profiles, response_consensus, task_stability


def prompt_means(consensus: pd.DataFrame) -> pd.DataFrame:
    paired = consensus[consensus["task"].isin(["mathdial_standard", "mathdial_hard"])]
    rows = []
    for keys, group in paired.groupby(["task", "model", "dimension"]):
        wide = group.pivot_table(index="pair_id", columns="arm", values="score", aggfunc="last").dropna()
        if {"generic", "pedagogy"}.issubset(wide):
            rows.append({"task": keys[0], "model": keys[1], "dimension": keys[2], "mean_delta": float((wide["pedagogy"] - wide["generic"]).mean())})
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ratings", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    ratings = pd.read_csv(args.ratings, dtype={"item_id": str, "pair_id": str})
    judges = sorted(ratings["judge"].unique())
    if len(judges) != 3:
        raise SystemExit(f"requires three complete judges, found {judges}")

    full_consensus = response_consensus(ratings)
    _, full_profiles = centered_profiles(full_consensus)
    full_profile = full_profiles.set_index(["benchmark", "model", "dimension"])["z_centered_mean"]
    full_prompt = prompt_means(full_consensus).rename(columns={"mean_delta": "full_mean_delta"})
    full_stability = task_stability(full_profiles).set_index("dimension")
    summary_rows, prompt_rows, stability_rows = [], [], []

    for excluded in judges:
        consensus = response_consensus(ratings[ratings["judge"] != excluded])
        _, profiles = centered_profiles(consensus)
        profile = profiles.set_index(["benchmark", "model", "dimension"])["z_centered_mean"]
        common = full_profile.index.intersection(profile.index)
        profile_rho = float(spearmanr(full_profile.loc[common], profile.loc[common]).statistic)

        prompt = prompt_means(consensus).rename(columns={"mean_delta": "leaveout_mean_delta"})
        merged = full_prompt.merge(prompt, on=["task", "model", "dimension"], validate="one_to_one")
        merged["excluded_judge"] = excluded
        merged["sign_reversal"] = (
            np.sign(merged["full_mean_delta"]) != np.sign(merged["leaveout_mean_delta"])
        ) & (merged["full_mean_delta"] != 0) & (merged["leaveout_mean_delta"] != 0)
        merged["absolute_change"] = (merged["leaveout_mean_delta"] - merged["full_mean_delta"]).abs()
        prompt_rows.append(merged)

        stability = task_stability(profiles).set_index("dimension")
        for dimension in full_stability.index:
            stability_rows.append({
                "excluded_judge": excluded, "dimension": dimension,
                "full_icc": full_stability.loc[dimension, "icc_3_1_across_tasks"],
                "leaveout_icc": stability.loc[dimension, "icc_3_1_across_tasks"],
                "icc_change": stability.loc[dimension, "icc_3_1_across_tasks"] - full_stability.loc[dimension, "icc_3_1_across_tasks"],
            })
        summary_rows.append({
            "excluded_judge": excluded, "profile_spearman_vs_full": profile_rho,
            "prompt_cells": len(merged), "prompt_sign_reversals": int(merged["sign_reversal"].sum()),
            "max_absolute_prompt_delta_change": float(merged["absolute_change"].max()),
            "mean_absolute_prompt_delta_change": float(merged["absolute_change"].mean()),
        })

    summary = pd.DataFrame(summary_rows)
    prompt_detail = pd.concat(prompt_rows, ignore_index=True)
    stability_detail = pd.DataFrame(stability_rows)
    summary.to_csv(args.output_dir / "leaveout_summary.csv", index=False)
    prompt_detail.to_csv(args.output_dir / "leaveout_prompt_effects.csv", index=False)
    stability_detail.to_csv(args.output_dir / "leaveout_task_stability.csv", index=False)
    report = "\n".join([
        "# Leave-one-judge-out semantic sensitivity", "",
        summary.to_markdown(index=False, floatfmt=".3f"), "",
        "Prompt sign reversals are counted over model × task × dimension cells and are never hidden by averaging. "
        "Detailed prompt and cross-task ICC changes are saved alongside this report.", "",
    ])
    (args.output_dir / "semantic_leaveout_report.md").write_text(report, encoding="utf-8")
    print(args.output_dir / "semantic_leaveout_report.md")


if __name__ == "__main__":
    main()
