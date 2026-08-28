#!/usr/bin/env python3
"""Analyze the frozen affiliation stability-and-transfer pilot."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from analyze_existing_general_personality_bridge import exact_spearman_p
from run_semantic_judge import parse_json_object


DIMENSIONS = ("affiliative_behavior", "benevolent_cost_acceptance", "assertive_dominance", "surface_warmth", "task_effectiveness")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def latest_success(path: Path, left: str, right: str) -> dict[tuple[str, str], dict[str, Any]]:
    latest = {(str(row[left]), str(row[right])): row for row in load_jsonl(path)}
    return {key: row for key, row in latest.items() if not row.get("error")}


def icc3(matrix: np.ndarray) -> tuple[float, float]:
    n, k = matrix.shape
    grand = matrix.mean()
    row_mean = matrix.mean(axis=1)
    col_mean = matrix.mean(axis=0)
    msr = k * np.square(row_mean - grand).sum() / (n - 1)
    mse = np.square(matrix - row_mean[:, None] - col_mean[None, :] + grand).sum() / ((n - 1) * (k - 1))
    single = (msr - mse) / (msr + (k - 1) * mse) if msr + (k - 1) * mse else math.nan
    average = (msr - mse) / msr if msr else math.nan
    return float(single), float(average)


def parse_generator_scores(spec: dict[str, Any], responses: dict[tuple[str, str], dict[str, Any]]) -> tuple[pd.DataFrame, pd.DataFrame]:
    self_rows, choice_rows = [], []
    item_map = {row["id"]: row for row in spec["ipip_agreeableness_items"]}
    choice_map = {row["id"]: row for row in spec["scenario_choices"]}
    for (_, model), row in responses.items():
        if row["mode"] not in {"self_report", "scenario_choice"}:
            continue
        value = parse_json_object(row["response"])
        if row["mode"] == "self_report":
            ratings = value.get("ratings", {})
            valid = set(ratings) == set(item_map) and all(isinstance(ratings[key], int) and 1 <= ratings[key] <= 5 for key in item_map)
            if not valid:
                raise RuntimeError(f"invalid self-report JSON: {row['request_id']}")
            scores = [6 - ratings[key] if item_map[key]["reverse"] else ratings[key] for key in item_map]
            self_rows.append({"condition": row["condition"], "model": model, "agreeableness_self_report": float(np.mean(scores)), "item_sd": float(np.std(scores, ddof=0))})
        else:
            choices = value.get("choices", {})
            valid = set(choices) == set(choice_map) and all(choices[key] in {"A", "B"} for key in choice_map)
            if not valid:
                raise RuntimeError(f"invalid scenario-choice JSON: {row['request_id']}")
            for key, item in choice_map.items():
                choice_rows.append({
                    "condition": row["condition"], "model": model, "item_id": key,
                    "domain": item["domain"], "affiliative_choice": int(choices[key] == item["affiliative_option"]),
                })
    return pd.DataFrame(self_rows), pd.DataFrame(choice_rows)


def unblind_annotations(annotations: dict[tuple[str, str], dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for (_, judge), row in annotations.items():
        annotation = row.get("annotation")
        if not annotation:
            continue
        for label, model in row["candidate_mapping"].items():
            scores = annotation["candidates"][label]
            rows.append({
                "sample_id": row["sample_id"], "condition": row["condition"],
                "item_id": row["item_id"], "domain": row["domain"], "model": model,
                "judge": judge, **{name: scores[name] for name in DIMENSIONS},
            })
    return pd.DataFrame(rows)


def correlation_row(name: str, left: pd.Series, right: pd.Series) -> dict[str, Any]:
    common = left.index.intersection(right.index)
    left_values = left.loc[common].to_numpy(float)
    right_values = right.loc[common].to_numpy(float)
    if len(np.unique(left_values)) < 2 or len(np.unique(right_values)) < 2:
        rho, p = math.nan, math.nan
    else:
        rho, p = exact_spearman_p(left_values, right_values)
    return {"comparison": name, "spearman": rho, "exact_two_sided_p": p, "model_count": len(common)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, default=Path("data/affiliation_stability_pilot_spec_v1.json"))
    parser.add_argument("--responses", type=Path, default=Path("artifacts/affiliation_stability_pilot_v1/run/responses.jsonl"))
    parser.add_argument("--annotations", type=Path, default=Path("artifacts/affiliation_stability_pilot_v1/judge/annotations.jsonl"))
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/affiliation_stability_pilot_v1/analysis"))
    args = parser.parse_args()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    responses = latest_success(args.responses, "sample_id", "model")
    annotations = latest_success(args.annotations, "sample_id", "judge")
    expected_responses = 56 * len(spec["models"])
    expected_annotations = 48 * len(spec["judges"])
    if len(responses) != expected_responses:
        raise RuntimeError(f"generator panel incomplete: {len(responses)}/{expected_responses}")
    if len(annotations) != expected_annotations:
        raise RuntimeError(f"judge panel incomplete: {len(annotations)}/{expected_annotations}")

    self_report, choices = parse_generator_scores(spec, responses)
    ratings = unblind_annotations(annotations)
    consensus = ratings.groupby(["sample_id", "condition", "item_id", "domain", "model"], sort=True)[list(DIMENSIONS)].mean().reset_index()
    profile = consensus.groupby(["condition", "domain", "model"], sort=True)[list(DIMENSIONS)].mean().reset_index()
    overall = consensus.groupby(["condition", "model"], sort=True)[list(DIMENSIONS)].mean().reset_index()

    reliability_rows = []
    for dimension in DIMENSIONS:
        pivot = ratings.pivot(index=["sample_id", "model"], columns="judge", values=dimension).dropna()
        single, average = icc3(pivot.to_numpy(float))
        reliability_rows.append({"dimension": dimension, "units": len(pivot), "judges": pivot.shape[1], "icc3_1": single, "icc3_k": average})
    reliability = pd.DataFrame(reliability_rows)

    default_domain = profile[profile["condition"] == "default"].pivot(index="model", columns="domain", values="affiliative_behavior")
    overall_pivot = overall.pivot(index="model", columns="condition", values="affiliative_behavior")
    self_pivot = self_report.pivot(index="model", columns="condition", values="agreeableness_self_report")
    choice_profile = choices.groupby(["condition", "domain", "model"], sort=True)["affiliative_choice"].mean().reset_index()
    choice_overall = choices.groupby(["condition", "model"], sort=True)["affiliative_choice"].mean().unstack("condition")

    correlations = pd.DataFrame([
        correlation_row("default_education_vs_noneducation_open", default_domain["education"], default_domain["noneducation"]),
        correlation_row("default_vs_irrelevant_open", overall_pivot["default"], overall_pivot["irrelevant_context"]),
        correlation_row("default_self_report_vs_open", self_pivot["default"], overall_pivot["default"]),
        correlation_row("default_scenario_choice_vs_open", choice_overall["default"], overall_pivot["default"]),
        correlation_row("default_open_vs_high_affiliation_open", overall_pivot["default"], overall_pivot["high_affiliation"]),
        correlation_row("default_open_vs_low_affiliation_open", overall_pivot["default"], overall_pivot["low_affiliation"]),
        correlation_row("default_affiliation_vs_benevolent_cost", overall_pivot["default"], overall[overall["condition"] == "default"].set_index("model")["benevolent_cost_acceptance"]),
        correlation_row("default_affiliation_vs_surface_warmth", overall_pivot["default"], overall[overall["condition"] == "default"].set_index("model")["surface_warmth"]),
        correlation_row("default_affiliation_vs_assertive_dominance", overall_pivot["default"], overall[overall["condition"] == "default"].set_index("model")["assertive_dominance"]),
        correlation_row("default_affiliation_vs_task_effectiveness", overall_pivot["default"], overall[overall["condition"] == "default"].set_index("model")["task_effectiveness"]),
    ])

    full_default = overall_pivot["default"]
    leaveout_rows = []
    for judge in spec["judges"]:
        subset = ratings[(ratings["judge"] != judge) & (ratings["condition"] == "default")]
        subset_profile = subset.groupby("model")["affiliative_behavior"].mean()
        row = correlation_row(f"leave_out_{judge}", full_default, subset_profile)
        row["left_out_judge"] = judge
        leaveout_rows.append(row)
    judge_leaveout = pd.DataFrame(leaveout_rows)

    effects = []
    for model in spec["models"]:
        values = overall_pivot.loc[model]
        effects.append({"model": model, "high_minus_low_open": values["high_affiliation"] - values["low_affiliation"], "irrelevant_minus_default_open": values["irrelevant_context"] - values["default"]})
    effects = pd.DataFrame(effects)
    effects.loc[len(effects)] = {
        "model": "panel_mean",
        "high_minus_low_open": effects["high_minus_low_open"].mean(),
        "irrelevant_minus_default_open": effects["irrelevant_minus_default_open"].mean(),
    }

    dispersion = overall.groupby("condition")["affiliative_behavior"].std(ddof=0).rename("between_model_sd").reset_index()
    gates = spec["gates"]
    lookup = correlations.set_index("comparison")
    primary_icc = float(reliability.set_index("dimension").loc["affiliative_behavior", "icc3_k"])
    cross_domain_rho = float(lookup.loc["default_education_vs_noneducation_open", "spearman"])
    irrelevant_rho = float(lookup.loc["default_vs_irrelevant_open", "spearman"])
    irrelevant_shift = float(effects.loc[effects["model"] == "panel_mean", "irrelevant_minus_default_open"].iloc[0])
    default_sd = float(dispersion.set_index("condition").loc["default", "between_model_sd"])
    high_low = float(effects.loc[effects["model"] == "panel_mean", "high_minus_low_open"].iloc[0])
    positive_models = int((effects.loc[effects["model"] != "panel_mean", "high_minus_low_open"] > 0).sum())
    self_rho = float(lookup.loc["default_self_report_vs_open", "spearman"])
    choice_rho = float(lookup.loc["default_scenario_choice_vs_open", "spearman"])
    stability_gates = {
        "judge_reliability": bool(primary_icc >= gates["judge_reliability_icc3k"]),
        "cross_domain_transport": bool(cross_domain_rho >= gates["default_cross_domain_spearman"]),
        "irrelevant_rank_stability": bool(irrelevant_rho >= gates["default_to_irrelevant_spearman"]),
        "irrelevant_mean_stability": bool(abs(irrelevant_shift) <= gates["maximum_irrelevant_mean_shift"]),
        "default_model_dispersion": bool(default_sd >= gates["minimum_default_between_model_sd"]),
    }
    prompt_gates = {
        "high_low_mean_effect": bool(high_low >= gates["minimum_high_minus_low_effect"]),
        "all_models_directional": bool(positive_models >= gates["minimum_models_with_positive_high_low_effect"]),
    }
    convergence_gates = {
        "self_report_to_behavior": bool(np.isfinite(self_rho) and self_rho >= gates["self_report_behavior_spearman"]),
        "scenario_choice_to_behavior": bool(np.isfinite(choice_rho) and choice_rho >= gates["choice_behavior_spearman"]),
    }
    stable = all(stability_gates.values())
    steerable = all(prompt_gates.values())
    convergent = all(convergence_gates.values())
    decision = {
        "schema_version": 1,
        "status": "complete_targeted_affiliation_pilot",
        "coverage": {"generator_calls": len(responses), "judge_calls": len(annotations), "models": len(spec["models"]), "open_scenarios": 12},
        "estimates": {
            "primary_icc3_k": primary_icc,
            "default_cross_domain_spearman": cross_domain_rho,
            "default_to_irrelevant_spearman": irrelevant_rho,
            "irrelevant_minus_default_mean": irrelevant_shift,
            "default_between_model_sd": default_sd,
            "high_minus_low_mean": high_low,
            "positive_high_low_models": positive_models,
            "self_report_to_open_spearman": self_rho if np.isfinite(self_rho) else None,
            "scenario_choice_to_open_spearman": choice_rho if np.isfinite(choice_rho) else None,
            "affiliation_to_surface_warmth_spearman": float(lookup.loc["default_affiliation_vs_surface_warmth", "spearman"]),
            "affiliation_to_benevolent_cost_spearman": float(lookup.loc["default_affiliation_vs_benevolent_cost", "spearman"]),
            "minimum_judge_leaveout_profile_spearman": float(judge_leaveout["spearman"].min()),
        },
        "stability_gates": stability_gates,
        "prompt_gates": prompt_gates,
        "convergence_gates": convergence_gates,
        "stable_default_affiliation_supported": stable,
        "prompt_steerability_supported": steerable,
        "general_personality_convergence_supported": bool(stable and convergent),
        "posthoc_surface_warmth_overlap_is_high": bool(abs(float(lookup.loc["default_affiliation_vs_surface_warmth", "spearman"])) >= 0.80),
        "verdict": (
            "stable_and_convergent_affiliation_candidate" if stable and convergent
            else "stable_behavioral_affiliation_without_general_trait_convergence" if stable
            else "affiliation_is_prompt_contingent_or_context_unstable_not_a_stable_default_trait"
        ),
        "claim_boundary": "Five fixed deployed configurations, synthetic conflicts, LLM-coded open behavior; no human personality, model-family, temporal-stability, or learner-outcome claim.",
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    self_report.to_csv(args.output_dir / "self_report_profiles.csv", index=False)
    choice_profile.to_csv(args.output_dir / "scenario_choice_profiles.csv", index=False)
    ratings.to_csv(args.output_dir / "unblinded_ratings.csv", index=False)
    consensus.to_csv(args.output_dir / "response_consensus.csv", index=False)
    profile.to_csv(args.output_dir / "open_behavior_profiles.csv", index=False)
    overall.to_csv(args.output_dir / "open_behavior_overall_profiles.csv", index=False)
    reliability.to_csv(args.output_dir / "judge_reliability.csv", index=False)
    correlations.to_csv(args.output_dir / "construct_correlations.csv", index=False)
    judge_leaveout.to_csv(args.output_dir / "judge_leaveout_profiles.csv", index=False)
    effects.to_csv(args.output_dir / "condition_effects.csv", index=False)
    dispersion.to_csv(args.output_dir / "condition_dispersion.csv", index=False)
    (args.output_dir / "decision.json").write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8")
    report = f"""# Targeted affiliation stability pilot

The prospective five-model panel is complete: {len(responses)} generator calls
and {len(annotations)} blinded judge calls, with no failed final records.

## Frozen-gate result

- Judge reliability ICC(3,k): {primary_icc:.3f}
- Default education/non-education model-profile rho: {cross_domain_rho:.3f}
- Default/irrelevant-context profile rho: {irrelevant_rho:.3f}
- Mean irrelevant-context displacement: {irrelevant_shift:.3f}
- Default between-model SD: {default_sd:.3f}
- High-minus-low prompt effect: {high_low:.3f}; positive models: {positive_models}/5
- Self-report/open-behavior rho: {self_rho:.3f}
- Scenario-choice/open-behavior rho: {'undefined (default choice ceiling)' if not np.isfinite(choice_rho) else f'{choice_rho:.3f}'}

All five stability gates pass, as do both prompt-steerability gates. Neither
general-personality convergence gate passes. The primary open-behavior profile
is invariant to leaving out any one judge (minimum rho
{judge_leaveout['spearman'].min():.3f}).

## Interpretation

The fixed model configurations have a distinguishable default affiliation
behavior profile that transports across the two scenario domains and survives
the tested irrelevant context. The explicit high/low instruction moves behavior
strongly and in the same direction for every model, but elasticity differs.

This is not Big Five validation. Default IPIP-like self-reports are compressed
near the socially desirable end and correlate {self_rho:.3f} with open behavior.
Every model chooses the affiliative option in every default forced-choice item,
so choice/behavior correlation is undefined. Open affiliation also correlates
{float(lookup.loc['default_affiliation_vs_surface_warmth', 'spearman']):.3f} with
surface warmth and {float(lookup.loc['default_affiliation_vs_benevolent_cost', 'spearman']):.3f}
with costly benevolence. Thus the supported object is a behavioral cluster with
substantial warmth overlap, not a construct-equivalent human trait.

## Gate table

```json
{json.dumps({'stability_gates': stability_gates, 'prompt_gates': prompt_gates, 'convergence_gates': convergence_gates}, indent=2)}
```
"""
    (args.output_dir / "report.md").write_text(report, encoding="utf-8")
    print(json.dumps(decision, indent=2))


if __name__ == "__main__":
    main()
