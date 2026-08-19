#!/usr/bin/env python3
"""Audit floor, ceiling, range compression, and judge severity in semantic scores."""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np
import pandas as pd


def normalized_entropy(values: pd.Series) -> float:
    probabilities = values.value_counts(normalize=True).to_numpy()
    entropy = -float(np.sum(probabilities * np.log(probabilities)))
    return entropy / math.log(5)


def summarize(frame: pd.DataFrame, groups: list[str], score: str) -> pd.DataFrame:
    rows = []
    for keys, group in frame.groupby(groups, dropna=False):
        keys = keys if isinstance(keys, tuple) else (keys,)
        values = group[score]
        row = dict(zip(groups, keys))
        row.update({
            "ratings": len(values), "mean": float(values.mean()), "sd": float(values.std(ddof=0)),
            "floor_fraction": float((values == 1).mean()), "ceiling_fraction": float((values == 5).mean()),
            "unique_values": int(values.nunique()), "normalized_entropy": normalized_entropy(values),
        })
        rows.append(row)
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ratings", type=Path, required=True)
    parser.add_argument("--consensus", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    ratings = pd.read_csv(args.ratings)
    consensus = pd.read_csv(args.consensus)
    judge_task = summarize(ratings, ["judge", "task", "dimension"], "score")
    judge_overall = summarize(ratings, ["judge", "dimension"], "score")
    consensus_task = summarize(consensus, ["task", "arm", "dimension"], "score")
    consensus_overall = summarize(consensus, ["dimension"], "score")
    for name, frame in {
        "judge_task_scale_diagnostics.csv": judge_task,
        "judge_scale_diagnostics.csv": judge_overall,
        "consensus_task_scale_diagnostics.csv": consensus_task,
        "consensus_scale_diagnostics.csv": consensus_overall,
    }.items():
        frame.to_csv(args.output_dir / name, index=False)
    flagged = consensus_task[
        (consensus_task["sd"] < .5)
        | (consensus_task["floor_fraction"] > .8)
        | (consensus_task["ceiling_fraction"] > .8)
    ]
    report = "\n".join([
        "# Semantic scale diagnostics", "",
        "## Consensus across all tasks", "", consensus_overall.to_markdown(index=False, floatfmt=".3f"), "",
        "## Low-information task × arm scales", "",
        flagged.to_markdown(index=False, floatfmt=".3f") if len(flagged) else "No scale met the diagnostic flags (SD < 0.5 or >80% at an endpoint).", "",
        "These are measurement diagnostics, not exclusion rules. Low-variance dimensions remain in the report and cannot support strong cross-model conclusions merely because another test is significant.", "",
    ])
    (args.output_dir / "semantic_scale_diagnostics_report.md").write_text(report, encoding="utf-8")
    print(args.output_dir / "semantic_scale_diagnostics_report.md")


if __name__ == "__main__":
    main()
