#!/usr/bin/env python3
"""Quantify system-policy control versus learner-request override effects."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from analyze_factorial_prompt_panel import build_metric_frame, load_jsonl


CONTRASTS = {
    "question": {
        "metric": "question_first",
        "system_factor": "question_policy",
        "system_high": "question_first",
        "system_low": "explain_only",
        "conflicting_need": "direct",
        "learner_high": "explore",
        "learner_low": "direct",
        "opposing_system_level": "explain_only",
    },
    "answer": {
        "metric": "answer_reveal_correct",
        "system_factor": "answer_policy",
        "system_high": "reveal",
        "system_low": "withhold",
        "conflicting_need": "explore",
        "learner_high": "direct",
        "learner_low": "explore",
        "opposing_system_level": "withhold",
    },
}


def difference(frame: pd.DataFrame, column: str, high: str, low: str, metric: str) -> float:
    return float(
        frame.loc[frame[column] == high, metric].mean()
        - frame.loc[frame[column] == low, metric].mean()
    )


def contrast_values(frame: pd.DataFrame, contrast: dict[str, str]) -> tuple[float, float, float]:
    metric = contrast["metric"]
    factor = contrast["system_factor"]
    conflict = frame[frame.learner_need == contrast["conflicting_need"]]
    system_effect = difference(
        conflict, factor, contrast["system_high"], contrast["system_low"], metric,
    )
    opposing = frame[frame[factor] == contrast["opposing_system_level"]]
    learner_override = difference(
        opposing, "learner_need", contrast["learner_high"], contrast["learner_low"], metric,
    )
    return system_effect, learner_override, system_effect - learner_override


def clustered_ci(
    frame: pd.DataFrame, contrast: dict[str, str], reps: int, seed: int,
) -> dict[str, tuple[float, float]]:
    bases = sorted(frame.base_id.unique())
    by_base = {base: frame[frame.base_id == base] for base in bases}
    rng = np.random.default_rng(seed)
    draws = {"system_conflict_effect": [], "learner_override_effect": [], "control_gap": []}
    for _ in range(reps):
        selected = rng.choice(bases, size=len(bases), replace=True)
        sample = pd.concat(
            [by_base[base].assign(_bootstrap_copy=index) for index, base in enumerate(selected)],
            ignore_index=True,
        )
        system, learner, gap = contrast_values(sample, contrast)
        draws["system_conflict_effect"].append(system)
        draws["learner_override_effect"].append(learner)
        draws["control_gap"].append(gap)
    return {
        name: (
            float(np.quantile(values, 0.025)),
            float(np.quantile(values, 0.975)),
        )
        for name, values in draws.items()
    }


def asymmetry_table(frame: pd.DataFrame, reps: int, seed: int) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    groups = [("ALL", frame)] + [
        (str(model), group) for model, group in frame.groupby("model", sort=True)
    ]
    for group_index, (group_name, group) in enumerate(groups):
        for contrast_index, (policy, contrast) in enumerate(CONTRASTS.items()):
            system, learner, gap = contrast_values(group, contrast)
            ci = clustered_ci(
                group, contrast, reps, seed + group_index * 1000 + contrast_index,
            )
            rows.append({
                "group": group_name,
                "policy": policy,
                "metric": contrast["metric"],
                "system_conflict_effect": system,
                "system_conflict_ci_low": ci["system_conflict_effect"][0],
                "system_conflict_ci_high": ci["system_conflict_effect"][1],
                "learner_override_effect": learner,
                "learner_override_ci_low": ci["learner_override_effect"][0],
                "learner_override_ci_high": ci["learner_override_effect"][1],
                "control_gap": gap,
                "control_gap_ci_low": ci["control_gap"][0],
                "control_gap_ci_high": ci["control_gap"][1],
            })
    return pd.DataFrame(rows)


def evaluate_asymmetry_gates(table: pd.DataFrame, gates: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for policy in CONTRASTS:
        overall = table[(table.group == "ALL") & (table.policy == policy)].iloc[0]
        models = table[(table.group != "ALL") & (table.policy == policy)]
        equivalence = float(gates["learner_override_equivalence_bound"])
        result[policy] = {
            "system_conflict_effect": float(overall.system_conflict_effect),
            "system_conflict_ci_low": float(overall.system_conflict_ci_low),
            "system_conflict_min": float(gates["system_conflict_effect_min"]),
            "system_conflict_pass": bool(
                overall.system_conflict_effect >= float(gates["system_conflict_effect_min"])
                and overall.system_conflict_ci_low >= float(gates["system_conflict_ci_low_min"])
                and (models.system_conflict_effect > 0).all()
            ),
            "learner_override_effect": float(overall.learner_override_effect),
            "learner_override_ci": [
                float(overall.learner_override_ci_low),
                float(overall.learner_override_ci_high),
            ],
            "learner_override_equivalent_to_zero": bool(
                overall.learner_override_ci_low > -equivalence
                and overall.learner_override_ci_high < equivalence
            ),
            "control_gap": float(overall.control_gap),
            "control_gap_ci_low": float(overall.control_gap_ci_low),
            "control_gap_pass": bool(
                overall.control_gap >= float(gates["control_gap_min"])
                and overall.control_gap_ci_low >= float(gates["control_gap_ci_low_min"])
                and (models.control_gap > 0).all()
            ),
        }
        result[policy]["control_asymmetry_pass"] = bool(
            result[policy]["system_conflict_pass"]
            and result[policy]["learner_override_equivalent_to_zero"]
            and result[policy]["control_gap_pass"]
        )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, default=Path("data/factorial_prompt_spec_v1.json"))
    parser.add_argument(
        "--manifest", type=Path,
        default=Path("artifacts/factorial_prompt_v1/sample_manifest.jsonl"),
    )
    parser.add_argument(
        "--responses", type=Path,
        default=Path("artifacts/factorial_prompt_v1/run/responses.jsonl"),
    )
    parser.add_argument(
        "--output-dir", type=Path,
        default=Path("artifacts/factorial_control_asymmetry_exploratory_v1"),
    )
    parser.add_argument("--bootstrap-reps", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=20260824)
    args = parser.parse_args()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    frame = build_metric_frame(spec, load_jsonl(args.manifest), load_jsonl(args.responses))
    table = asymmetry_table(frame, args.bootstrap_reps, args.seed)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    table.to_csv(args.output_dir / "control_asymmetry.csv", index=False)
    report = {
        "schema_version": 1,
        "status": "post_hoc_exploratory_on_existing_responses",
        "rows": len(frame),
        "base_problems": int(frame.base_id.nunique()),
        "models": sorted(frame.model.unique().tolist()),
        "aggregate": table[table.group == "ALL"].to_dict(orient="records"),
        "claim_boundary": (
            "The existing-panel analysis is exploratory because the estimand was defined "
            "after both parent and order-replication outcomes were inspected."
        ),
    }
    (args.output_dir / "control_asymmetry_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8",
    )
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
