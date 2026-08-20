#!/usr/bin/env python3
"""Render the prespecified paper-facing factorial result summary."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

from analyze_factorial_prompt_panel import PRIMARY_METRICS, TARGET_METRICS


FACTOR_LABELS = {
    "question_policy": "Question policy",
    "answer_policy": "Answer policy",
    "tone_policy": "Tone policy",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def value(frame: pd.DataFrame, **filters: str) -> pd.Series:
    selected = frame
    for column, expected in filters.items():
        selected = selected[selected[column] == expected]
    if len(selected) != 1:
        raise RuntimeError(f"expected one row for {filters}, found {len(selected)}")
    return selected.iloc[0]


def num(number: Any) -> str:
    return f"{float(number):.3f}"


def effect_ci(row: pd.Series, column: str = "mean_difference") -> str:
    return (
        f"{num(row[column])} "
        f"[{num(row['bootstrap_ci_low'])}, {num(row['bootstrap_ci_high'])}]"
    )


def factor_verdict(
    factor: str, parent: dict[str, Any], joint: dict[str, Any],
) -> str:
    main = parent["factor_results"][factor]
    combined = joint["factor_results"][factor]
    if combined["order_robust"]:
        return "order-robust black-box component addressability"
    if main["selective"]:
        return "selective in parent, but not order-robust"
    if main["controllable"]:
        return "bundled controllability; component selectivity failed"
    return "registered controllability gate failed"


def render(parent_dir: Path, replication_dir: Path, detector_validation_path: Path) -> str:
    parent_report = read_json(parent_dir / "factorial_analysis_report.json")
    replication_report = read_json(replication_dir / "order_replication_report.json")
    if parent_report["response_rows"] != 2560:
        raise RuntimeError("parent report is not the complete 2,560-row panel")
    if replication_report["replication_rows"] != 640:
        raise RuntimeError("replication report is not the complete 640-row panel")
    if not replication_report.get("request_order_block_balance_pass"):
        raise RuntimeError("replication request-order block balance did not pass")

    parent_effects = pd.read_csv(parent_dir / "factor_effects.csv")
    replication_effects = pd.read_csv(
        replication_dir / "replication_factor_effects.csv"
    )
    comparison = pd.read_csv(
        replication_dir / "order_replication_target_comparison.csv"
    )
    parent_need = pd.read_csv(parent_dir / "learner_need_effects.csv")
    replication_need = pd.read_csv(
        replication_dir / "replication_learner_need_effects.csv"
    )
    parent_family = pd.read_csv(parent_dir / "family_target_effects.csv")
    replication_family = pd.read_csv(
        replication_dir / "replication_family_target_effects.csv"
    )
    parent_interactions = pd.read_csv(parent_dir / "factor_interactions.csv")
    replication_interactions = pd.read_csv(
        replication_dir / "replication_factor_interactions.csv"
    )
    parent_decision = parent_report["decision"]
    replication_decision = replication_report["replication_decision"]
    joint = replication_report["joint_order_robustness_decision"]
    detector_validation = read_json(detector_validation_path)
    expected_detector_decisions = {
        "question_first": True,
        "answer_reveal_correct": True,
        "warmth_marker": False,
    }
    observed_detector_decisions = {
        metric: bool(detector_validation["detectors"][metric]["validated"])
        for metric in expected_detector_decisions
    }
    if observed_detector_decisions != expected_detector_decisions:
        raise RuntimeError(
            "detector-validation decision drift: "
            f"{observed_detector_decisions} != {expected_detector_decisions}"
        )

    lines = [
        "# Prospective factorial and request-order replication results",
        "",
        "This report is generated from the complete frozen outputs. It lists every",
        "registered headline gate and the prespecified paper-facing secondary tables.",
        "A replication result can only preserve or downgrade a parent-panel claim.",
        "",
        "## Completion",
        "",
        "- Parent factorial: 2,560/2,560 responses, five models, 32 base problems.",
        "- Order replication: 640/640 responses, five models, eight fixed base problems.",
        "- Replication order plan: exact 16-cell block balance passed.",
        "",
        "## Registered factor gates",
        "",
        "| Factor | Parent target effect (95% CI) | Parent selective | Replication target effect (95% CI) | Replication selective | Joint order-robust | Verdict |",
        "|---|---:|:---:|---:|:---:|:---:|---|",
    ]
    for factor, metric in TARGET_METRICS.items():
        parent_row = value(
            parent_effects, group="ALL", factor=factor, metric=metric,
        )
        replication_row = value(
            replication_effects, group="ALL", factor=factor, metric=metric,
        )
        parent_gate = parent_decision["factor_results"][factor]
        replication_gate = replication_decision["factor_results"][factor]
        joint_gate = joint["factor_results"][factor]
        lines.append(
            f"| {FACTOR_LABELS[factor]} | {effect_ci(parent_row)} | "
            f"{'PASS' if parent_gate['selective'] else 'FAIL'} | "
            f"{effect_ci(replication_row)} | "
            f"{'PASS' if replication_gate['selective'] else 'FAIL'} | "
            f"{'PASS' if joint_gate['order_robust'] else 'FAIL'} | "
            f"{('order-robust frozen encouragement-marker effect; not semantic warmth' if factor == 'tone_policy' else factor_verdict(factor, parent_decision, joint))} |"
        )

    lines.extend([
        "",
        "## Blind detector validation",
        "",
        "This post-result audit is downgrade-only and cannot strengthen the original claim.",
        "",
        "| Detector | Coverage | Balanced accuracy (95% CI) | Kappa | Validated |",
        "|---|---:|---:|---:|:---:|",
    ])
    for metric in ("question_first", "answer_reveal_correct", "warmth_marker"):
        result = detector_validation["detectors"][metric]
        lines.append(
            f"| {metric} | {num(result['majority_label_coverage'])} | "
            f"{num(result['balanced_accuracy'])} "
            f"[{num(result['balanced_accuracy_ci_low'])}, {num(result['balanced_accuracy_ci_high'])}] | "
            f"{num(result['cohen_kappa'])} | "
            f"{'YES' if result['validated'] else 'NO'} |"
        )

    lines.extend([
        "",
        "## Target effects for every model",
        "",
        "| Factor | Model | Full parent | Matching parent subset | Randomized replication | Positive in subset and replication |",
        "|---|---|---:|---:|---:|:---:|",
    ])
    groups = sorted(group for group in parent_effects.group.unique() if group != "ALL")
    for factor, metric in TARGET_METRICS.items():
        for group in groups:
            parent_row = value(
                parent_effects, group=group, factor=factor, metric=metric,
            )
            compare_row = value(comparison, group=group, factor=factor, metric=metric)
            lines.append(
                f"| {FACTOR_LABELS[factor]} | {group} | "
                f"{num(parent_row['mean_difference'])} | "
                f"{num(compare_row['primary_subset_mean_difference'])} | "
                f"{num(compare_row['replication_mean_difference'])} | "
                f"{'YES' if bool(compare_row['positive_in_both']) else 'NO'} |"
            )

    lines.extend([
        "",
        "## Aggregate target and cross-effects",
        "",
        "| Panel | Factor | Outcome | Mean difference (95% CI) | Target outcome |",
        "|---|---|---|---:|:---:|",
    ])
    for panel_name, frame in (
        ("Parent", parent_effects), ("Replication", replication_effects),
    ):
        for factor in TARGET_METRICS:
            for metric in PRIMARY_METRICS:
                row = value(frame, group="ALL", factor=factor, metric=metric)
                lines.append(
                    f"| {panel_name} | {FACTOR_LABELS[factor]} | {metric} | "
                    f"{effect_ci(row)} | "
                    f"{'YES' if metric == TARGET_METRICS[factor] else 'NO'} |"
                )

    lines.extend([
        "",
        "## Learner-request effects for every model",
        "",
        "| Panel | Group | Contrast | Mean difference (95% CI) |",
        "|---|---|---|---:|",
    ])
    for panel_name, frame in (
        ("Parent", parent_need), ("Replication", replication_need),
    ):
        for row in frame.sort_values(["contrast", "group"]).itertuples(index=False):
            lines.append(
                f"| {panel_name} | {row.group} | {row.contrast} | "
                f"{num(row.mean_difference)} "
                f"[{num(row.bootstrap_ci_low)}, {num(row.bootstrap_ci_high)}] |"
            )

    lines.extend([
        "",
        "## Family target effects",
        "",
        "| Panel | Family | Factor | Mean difference |",
        "|---|---|---|---:|",
    ])
    for panel_name, frame in (
        ("Parent", parent_family), ("Replication", replication_family),
    ):
        for row in frame.sort_values(["problem_family", "factor"]).itertuples(index=False):
            lines.append(
                f"| {panel_name} | {row.problem_family} | "
                f"{FACTOR_LABELS[row.factor]} | {num(row.mean_difference)} |"
            )

    lines.extend([
        "",
        "## ALL-group interactions on primary outcomes",
        "",
        "| Panel | Order | Factors | Outcome | Interaction (95% CI) |",
        "|---|---:|---|---|---:|",
    ])
    for panel_name, frame in (
        ("Parent", parent_interactions),
        ("Replication", replication_interactions),
    ):
        selected = frame[(frame.group == "ALL") & frame.metric.isin(PRIMARY_METRICS)]
        for row in selected.sort_values(["order", "factors", "metric"]).itertuples(index=False):
            lines.append(
                f"| {panel_name} | {row.order} | {row.factors} | {row.metric} | "
                f"{num(row.interaction)} "
                f"[{num(row.bootstrap_ci_low)}, {num(row.bootstrap_ci_high)}] |"
            )

    lines.extend([
        "",
        "## Interpretation boundary",
        "",
        "- Effects measure black-box instruction following on five frozen deployed systems.",
        "- A failed selectivity or replication gate remains a central negative result.",
        "- System-over-user behavior is instruction-hierarchy behavior, not empathy or learner understanding.",
        "- Correct answer formatting is not tutoring quality or learning gain.",
        "- The encouragement lexicon fails semantic warmth validation; its effects are literal marker effects only.",
        "- Full released CSV files retain all surface outcomes, model groups, cells, and interactions.",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--parent-dir", type=Path, default=Path("artifacts/factorial_analysis_v1"),
    )
    parser.add_argument(
        "--replication-dir", type=Path,
        default=Path("artifacts/factorial_order_replication_analysis_v1"),
    )
    parser.add_argument(
        "--output", type=Path, default=Path("research/20_factorial_results.md"),
    )
    parser.add_argument(
        "--detector-validation", type=Path,
        default=Path("artifacts/factorial_detector_validation_analysis_v1/detector_validation_report.json"),
    )
    args = parser.parse_args()
    report = render(args.parent_dir, args.replication_dir, args.detector_validation)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
