#!/usr/bin/env python3
"""Verify the conservative planning sample for the future learner-outcome trial."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

from scipy.stats import norm


def required_completed_per_arm(effect: float, alpha: float, power: float) -> int:
    if not 0 < effect or not 0 < alpha < 1 or not 0 < power < 1:
        raise ValueError("effect must be positive and alpha/power must be in (0, 1)")
    z_alpha = norm.ppf(1 - alpha / 2)
    z_power = norm.ppf(power)
    return math.ceil(2 * ((z_alpha + z_power) / effect) ** 2)


def build_report(spec: dict[str, Any]) -> dict[str, Any]:
    estimand = spec["primary_estimand"]
    randomization = spec["randomization"]
    arms = len(spec["policy_arms"])
    models = len(spec["models"])
    completed = required_completed_per_arm(
        float(estimand["target_standardized_effect"]),
        float(estimand["two_sided_alpha"]),
        float(estimand["power"]),
    )
    recruited = math.ceil(completed / (1 - float(estimand["anticipated_attrition"])))
    planned_per_arm = int(randomization["learners_per_policy_arm"])
    planned_total = int(spec["population"]["target_recruited_learners"])
    cells = int(randomization["cells"])
    cell_size = int(randomization["learners_per_model_policy_cell"])
    checks = {
        "planning_only_status": spec["status"] == "planning_only_not_preregistered_not_started",
        "arm_count": arms == 4,
        "model_count": models == 3,
        "cell_count": cells == arms * models,
        "per_arm_balance": planned_total == planned_per_arm * arms,
        "per_cell_balance": planned_total == cell_size * cells,
        "power_target": planned_per_arm >= recruited,
        "no_human_annotation": spec["measurement"]["human_annotation"] is False,
        "unassisted_primary_outcome": spec["measurement"]["tutor_access_during_outcomes"] is False,
        "warmth_not_promoted": spec["measurement"]["warmth_marker_used_as_construct_or_treatment"] is False,
    }
    return {
        "schema_version": 1,
        "status": spec["status"],
        "required_completed_per_policy_arm": completed,
        "required_recruited_per_policy_arm": recruited,
        "planned_recruited_per_policy_arm": planned_per_arm,
        "planned_total": planned_total,
        "planned_cells": cells,
        "planned_per_cell": cell_size,
        "assumptions": {
            "standardized_effect": estimand["target_standardized_effect"],
            "two_sided_alpha": estimand["two_sided_alpha"],
            "power": estimand["power"],
            "attrition": estimand["anticipated_attrition"],
            "covariate_or_blocking_credit": 0,
        },
        "checks": checks,
        "passed": all(checks.values()),
        "claim_boundary": "A passing planning report is not evidence that the trial was registered, run, or effective.",
    }


def markdown(report: dict[str, Any]) -> str:
    rows = [
        "# Learner-outcome trial power plan",
        "",
        f"Status: **{report['status']}**",
        "",
        f"Overall planning checks: **{'PASS' if report['passed'] else 'FAIL'}**",
        "",
        f"- Required completed learners per policy arm: {report['required_completed_per_policy_arm']}",
        f"- Required recruited learners per arm after attrition inflation: {report['required_recruited_per_policy_arm']}",
        f"- Planned: {report['planned_recruited_per_policy_arm']} per arm, {report['planned_total']} total",
        f"- Balanced model-policy cells: {report['planned_cells']} × {report['planned_per_cell']}",
        "- No ANCOVA, classroom blocking, or repeated-measure efficiency is credited in this conservative calculation.",
        "",
        report["claim_boundary"],
        "",
    ]
    return "\n".join(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, default=Path("data/learner_outcome_trial_spec_v1.json"))
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/learner_outcome_trial_planning_v1"))
    parser.add_argument("--require-pass", action="store_true")
    args = parser.parse_args()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    report = build_report(spec)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "power_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (args.output_dir / "power_report.md").write_text(markdown(report), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    if args.require_pass and not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
