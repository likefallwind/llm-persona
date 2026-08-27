#!/usr/bin/env python3
"""Explore a possible normative-boundary axis using frozen EduGuard scores.

The script exports aggregate outcome fields only.  It never exports prompts,
responses, extracted text, gold option sets, or item content.
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from inventory_paths import resolve_inventory_path


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def icc3(matrix: np.ndarray) -> float:
    n, k = matrix.shape
    if n < 2 or k < 2:
        return math.nan
    row_mean = matrix.mean(axis=1, keepdims=True)
    col_mean = matrix.mean(axis=0, keepdims=True)
    grand = matrix.mean()
    ms_row = k * np.sum((row_mean - grand) ** 2) / (n - 1)
    residual = matrix - row_mean - col_mean + grand
    ms_error = np.sum(residual**2) / ((n - 1) * (k - 1))
    denominator = ms_row + (k - 1) * ms_error
    return float((ms_row - ms_error) / denominator) if denominator else math.nan


def stability(frame: pd.DataFrame, axis: str, value: str) -> dict[str, Any]:
    wide = frame.pivot_table(index="model", columns="context", values=value, aggfunc="last").dropna()
    correlations = []
    for left, right in itertools.combinations(wide.columns, 2):
        rho = spearmanr(wide[left], wide[right]).statistic if wide[left].std() and wide[right].std() else math.nan
        if np.isfinite(rho):
            correlations.append(float(rho))
    icc = icc3(wide.to_numpy())
    median_rho = float(np.median(correlations)) if correlations else math.nan
    return {
        "axis": axis,
        "models": len(wide),
        "contexts": len(wide.columns),
        "icc_3_1": icc,
        "median_pairwise_spearman": median_rho,
        "minimum_pairwise_spearman": float(np.min(correlations)) if correlations else math.nan,
        "icc_gate": bool(icc >= .50),
        "rank_gate": bool(median_rho >= .50),
        "stability_strength": (
            "robust_both_metrics" if icc >= .50 and median_rho >= .50
            else "mixed_one_metric" if icc >= .50 or median_rho >= .50
            else "unsupported"
        ),
    }


def adversarial_cells(
    selected: dict[tuple[str, str], dict[str, Any]], models: list[str], root: Path,
) -> pd.DataFrame:
    rows = []
    for model in models:
        run = selected[("eduguard_adversarial", model)]
        summary = load_json(resolve_inventory_path(run["summary_path"], root))
        extra = summary.get("extra_metrics") or {}
        for key, value in extra.items():
            if not key.startswith("category=") or not isinstance(value, dict):
                continue
            distribution = value.get("refusal_quality_distribution") or {}
            educational = distribution.get("educational_refusal") or {}
            rows.append({
                "model": model,
                "context": key.removeprefix("category="),
                "items": int(value.get("n_judged") or 0),
                "attack_success_rate": float(value.get("asr") or 0.0),
                "boundary_enforcement_rate": 1.0 - float(value.get("asr") or 0.0),
                "educational_refusal_share": float(educational.get("share_of_refusals") or 0.0),
            })
    return pd.DataFrame(rows)


def sata_cells(
    selected: dict[tuple[str, str], dict[str, Any]], models: list[str], root: Path,
) -> pd.DataFrame:
    rows = []
    for model in models:
        run = selected[("eduguard_sata", model)]
        summary_path = resolve_inventory_path(run["summary_path"], root)
        scored_path = summary_path.parent / "scored.jsonl"
        scored = [row for row in read_jsonl(scored_path) if row.get("score_status") == "scored"]
        cells: dict[tuple[str, str], list[dict[str, Any]]] = {}
        for row in scored:
            buckets = row.get("buckets") or {}
            key = (str(buckets.get("scenario") or "unknown"), str(buckets.get("language") or "unknown"))
            cells.setdefault(key, []).append(row)
        for (scenario, language), group in sorted(cells.items()):
            outcomes = [str(row.get("outcome") or "") for row in group]
            rows.append({
                "model": model,
                "context": f"{scenario}|{language}",
                "scenario": scenario,
                "language": language,
                "items": len(group),
                "incorrect_inclusion_rate": float(np.mean([outcome == "incorrect_inclusion" for outcome in outcomes])),
                "omission_rate": float(np.mean(["omission" in outcome for outcome in outcomes])),
                "perfect_match_rate": float(np.mean([outcome == "perfect_match" for outcome in outcomes])),
                "rfs": float(np.mean([float(row.get("rfs") or 0.0) for row in group])),
            })
    return pd.DataFrame(rows)


def model_profiles(adversarial: pd.DataFrame, sata: pd.DataFrame) -> pd.DataFrame:
    adv = adversarial.groupby("model", as_index=False).agg(
        adversarial_attack_success=("attack_success_rate", "mean"),
        adversarial_boundary_enforcement=("boundary_enforcement_rate", "mean"),
        educational_refusal_share=("educational_refusal_share", "mean"),
    )
    sat = sata.groupby("model", as_index=False).agg(
        sata_incorrect_inclusion=("incorrect_inclusion_rate", "mean"),
        sata_omission=("omission_rate", "mean"),
        sata_perfect_match=("perfect_match_rate", "mean"),
        sata_rfs=("rfs", "mean"),
    )
    return adv.merge(sat, on="model", how="inner")


def correlations(profiles: pd.DataFrame) -> pd.DataFrame:
    columns = [column for column in profiles.columns if column != "model"]
    rows = []
    for left, right in itertools.combinations(columns, 2):
        rho = spearmanr(profiles[left], profiles[right]).statistic
        rows.append({
            "left": left,
            "right": right,
            "models": len(profiles),
            "spearman": float(rho),
            "status": "descriptive_only_six_models",
        })
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", type=Path, default=Path("artifacts/inventory/corpus_inventory.json"))
    parser.add_argument("--edubenchmark-root", type=Path, default=Path("../edubenchmark"))
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/normative_boundary_axes_v1"))
    args = parser.parse_args()

    inventory = load_json(args.inventory)
    models = list(inventory["core_models"])
    selected = {
        (run["benchmark"], run["model"]): run
        for run in inventory["selected_runs"]
        if run["benchmark"] in {"eduguard_adversarial", "eduguard_sata"}
    }
    missing = [
        (benchmark, model)
        for benchmark in ("eduguard_adversarial", "eduguard_sata")
        for model in models
        if (benchmark, model) not in selected
    ]
    if missing:
        raise SystemExit(f"missing selected EduGuard runs: {missing}")

    adversarial = adversarial_cells(selected, models, args.edubenchmark_root)
    sata = sata_cells(selected, models, args.edubenchmark_root)
    profiles = model_profiles(adversarial, sata)
    stability_rows = pd.DataFrame([
        stability(adversarial, "adversarial_attack_success_propensity", "attack_success_rate"),
        stability(adversarial, "educational_refusal_style", "educational_refusal_share"),
        stability(sata, "sata_incorrect_inclusion_propensity", "incorrect_inclusion_rate"),
        stability(sata, "sata_omission_propensity", "omission_rate"),
    ])
    correlation_rows = correlations(profiles)

    permissiveness = correlation_rows[
        (correlation_rows["left"] == "adversarial_attack_success")
        & (correlation_rows["right"] == "sata_incorrect_inclusion")
    ]
    cross_task_rho = float(permissiveness.iloc[0]["spearman"]) if len(permissiveness) else math.nan
    decision = {
        "status": "exploratory_existing_data",
        "candidate_axis": "normative_boundary_permissiveness",
        "within_task_stability": stability_rows.to_dict(orient="records"),
        "cross_task_permissiveness_spearman": cross_task_rho,
        "candidate_axis_supported": bool(
            (stability_rows[stability_rows["axis"] == "adversarial_attack_success_propensity"]["stability_strength"] == "robust_both_metrics").all()
            and (stability_rows[stability_rows["axis"] == "sata_incorrect_inclusion_propensity"]["stability_strength"] == "robust_both_metrics").all()
            and cross_task_rho >= .50
        ),
        "boundary": (
            "Attack success and incorrect option inclusion are safety outcomes as well as behavioral tendencies. "
            "The adversarial scorer uses MiniMax-M3, including for MiniMax-M3 candidates. Results cannot establish "
            "a judge-independent personality trait or replace selective-safety evaluation."
        ),
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    # ``context`` is an internal grouping key only.  The released cells contain
    # aggregate category/scenario labels, but use an explicit non-source-text
    # field name so the privacy gate cannot confuse them with prompt context.
    adversarial.rename(columns={"context": "context_group"}).to_csv(
        args.output_dir / "adversarial_category_cells.csv", index=False
    )
    sata.rename(columns={"context": "context_group"}).to_csv(
        args.output_dir / "sata_scenario_language_cells.csv", index=False
    )
    profiles.to_csv(args.output_dir / "model_profiles.csv", index=False)
    stability_rows.to_csv(args.output_dir / "cross_context_stability.csv", index=False)
    correlation_rows.to_csv(args.output_dir / "cross_axis_correlations.csv", index=False)
    (args.output_dir / "decision.json").write_text(
        json.dumps(decision, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    report = "\n".join([
        "# Normative-boundary candidate axis",
        "",
        "Status: **exploratory analysis of frozen EduGuard aggregate/scored data**.",
        "No prompt, response, extracted text, reasoning, gold option set, or item text is exported.",
        "",
        "## Cross-context stability",
        "",
        stability_rows.to_markdown(index=False, floatfmt=".3f"),
        "",
        "## Fixed-panel profiles",
        "",
        profiles.to_markdown(index=False, floatfmt=".3f"),
        "",
        "## Decision",
        "",
        "```json",
        json.dumps(decision, ensure_ascii=False, indent=2),
        "```",
        "",
    ])
    (args.output_dir / "report.md").write_text(report, encoding="utf-8")
    print(json.dumps({
        "models": len(profiles),
        "adversarial_cells": len(adversarial),
        "sata_cells": len(sata),
        "candidate_axis_supported": decision["candidate_axis_supported"],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
