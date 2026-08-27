#!/usr/bin/env python3
"""Leave-one-judge-family sensitivity for the confirmatory character panel."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from analyze_theory_grounded_panel import icc3


def rho(left: pd.Series, right: pd.Series) -> float:
    if len(left) < 3 or not left.std() or not right.std():
        return math.nan
    return float(spearmanr(left, right).statistic)


def consensus(ratings: pd.DataFrame) -> pd.DataFrame:
    keys = [
        "benchmark", "task", "arm", "item_id", "pair_id", "model", "dimension",
    ]
    return ratings.groupby(keys, as_index=False)["score"].median()


def model_profile(frame: pd.DataFrame, dimension: str) -> pd.Series:
    data = frame[frame["dimension"] == dimension].copy()
    data["centered"] = data["score"] - data.groupby(
        ["benchmark", "item_id"]
    )["score"].transform("mean")
    return data.groupby("model")["centered"].mean().sort_index()


def prompt_cells(frame: pd.DataFrame, dimension: str) -> pd.Series:
    data = frame[
        (frame["dimension"] == dimension)
        & frame["task"].isin(["mathdial_standard", "mathdial_hard"])
    ]
    rows: dict[tuple[str, str], float] = {}
    for (task, model), group in data.groupby(["task", "model"]):
        wide = group.pivot_table(index="pair_id", columns="arm", values="score", aggfunc="last").dropna()
        if {"generic", "pedagogy"}.issubset(wide):
            rows[(task, model)] = float((wide["pedagogy"] - wide["generic"]).mean())
    return pd.Series(rows, dtype=float).sort_index()


def cross_task(frame: pd.DataFrame, dimension: str) -> dict[str, float | int | bool]:
    data = frame[
        (frame["dimension"] == dimension)
        & frame["arm"].isin(["generic", "socratic", "longitudinal"])
    ].copy()
    data["centered"] = data["score"] - data.groupby(
        ["benchmark", "item_id"]
    )["score"].transform("mean")
    scale = data.groupby("benchmark")["centered"].transform("std").replace(0, np.nan)
    data["z"] = (data["centered"] / scale).fillna(0)
    wide = data.groupby(["task", "model"])["z"].mean().unstack(0).dropna(axis=1)
    pair_rhos = [
        rho(wide[left], wide[right])
        for index, left in enumerate(wide.columns)
        for right in wide.columns[index + 1 :]
    ]
    pair_rhos = [value for value in pair_rhos if np.isfinite(value)]
    task_icc = icc3(wide.to_numpy(), average=False)
    median_rho = float(np.median(pair_rhos)) if pair_rhos else math.nan
    return {
        "tasks": len(wide.columns),
        "icc_3_1": task_icc,
        "median_pairwise_spearman": median_rho,
        "gate_pass": bool(task_icc >= .50 or median_rho >= .50),
    }


def analyze(ratings: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    judges = sorted(ratings["judge"].unique())
    dimensions = sorted(ratings["dimension"].unique())
    full = consensus(ratings)
    rows: list[dict[str, Any]] = []
    decisions = []
    for dimension in dimensions:
        full_profile = model_profile(full, dimension)
        full_prompt = prompt_cells(full, dimension)
        full_stability = cross_task(full, dimension)
        for judge in judges:
            leaveout = consensus(ratings[ratings["judge"] != judge])
            profile = model_profile(leaveout, dimension)
            prompts = prompt_cells(leaveout, dimension)
            profile_pair = pd.concat([full_profile, profile], axis=1).dropna()
            prompt_pair = pd.concat([full_prompt, prompts], axis=1).dropna()
            leaveout_stability = cross_task(leaveout, dimension)
            full_prompt_mean = float(full_prompt.mean()) if len(full_prompt) else math.nan
            leaveout_prompt_mean = float(prompts.mean()) if len(prompts) else math.nan
            rows.append({
                "dimension": dimension,
                "excluded_judge_family": judge,
                "models": len(profile_pair),
                "model_profile_spearman_full_vs_leaveout": rho(profile_pair.iloc[:, 0], profile_pair.iloc[:, 1]),
                "prompt_cells": len(prompt_pair),
                "prompt_cell_spearman_full_vs_leaveout": rho(prompt_pair.iloc[:, 0], prompt_pair.iloc[:, 1]),
                "full_mean_prompt_delta": full_prompt_mean,
                "leaveout_mean_prompt_delta": leaveout_prompt_mean,
                "prompt_direction_retained": bool(
                    abs(full_prompt_mean) < .10
                    or np.sign(full_prompt_mean) == np.sign(leaveout_prompt_mean)
                ),
                "full_cross_task_gate": full_stability["gate_pass"],
                "leaveout_cross_task_gate": leaveout_stability["gate_pass"],
                "leaveout_cross_task_icc_3_1": leaveout_stability["icc_3_1"],
                "leaveout_cross_task_median_rho": leaveout_stability["median_pairwise_spearman"],
            })
        dim_rows = [row for row in rows if row["dimension"] == dimension]
        gates = {
            "minimum_leaveout_model_profile_rho_at_least_0_90": bool(
                min(row["model_profile_spearman_full_vs_leaveout"] for row in dim_rows) >= .90
            ),
            "minimum_leaveout_prompt_cell_rho_at_least_0_70": bool(
                min(row["prompt_cell_spearman_full_vs_leaveout"] for row in dim_rows) >= .70
            ),
            "all_leaveouts_retain_prompt_direction": all(
                row["prompt_direction_retained"] for row in dim_rows
            ),
            "all_leaveouts_retain_cross_task_gate": all(
                row["leaveout_cross_task_gate"] for row in dim_rows
            ),
        }
        decisions.append({
            "dimension": dimension,
            "gates": gates,
            "judge_family_robust": all(gates.values()),
        })
    return pd.DataFrame(rows), {
        "schema_version": 1,
        "threshold_status": "fixed_before_formal_results",
        "judge_families": judges,
        "classification": decisions,
        "boundary": (
            "Each family is represented by one judge and all judges share one Gateway route; "
            "this tests family leaveout sensitivity, not provider-route replication."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ratings", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    rows, decision = analyze(pd.read_csv(args.ratings))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    rows.to_csv(args.output_dir / "judge_family_leaveout.csv", index=False)
    (args.output_dir / "judge_family_sensitivity.json").write_text(
        json.dumps(decision, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(decision, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
