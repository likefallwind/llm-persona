#!/usr/bin/env python3
"""Screen existing paired responses for domain-general behavioral manifestations.

The script never exports prompts or response text. It reads the already governed
EduBenchmark archive locally and writes only item-controlled aggregate profiles.
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from inventory_paths import resolve_inventory_path
from run_behavioral_pilot import extract_features, icc3_1, read_latest_success


CORE_CONTENT_AXES = (
    "communal_expression",
    "dialogic_engagement",
    "directive_expression",
    "epistemic_caution_language",
    "boundary_refusal_expression",
)
SURFACE_CONTROLS = ("organizational_style", "verbosity")
ALL_AXES = CORE_CONTENT_AXES + SURFACE_CONTROLS

NON_TUTORING_DOMAINS = {
    "general_reasoning",
    "instruction_following",
    "self_monitoring",
    "safety_assistance",
    "educational_assessment",
}

EXTRA_PATTERNS = {
    "uncertainty_acknowledgment_rate": (
        r"\b(?:not sure|uncertain|cannot determine|can't determine|insufficient "
        r"information|not enough information|unknown)\b|不确定|无法确定|难以判断|"
        r"信息不足|无法判断|不能确定"
    ),
    "limitation_rate": (
        r"\b(?:cannot|can't|unable to|do not have access|don't have access|"
        r"beyond my capabilities|as an ai)\b|无法|不能|做不到|没有权限|无权|"
        r"作为(?:一个)?(?:人工智能|AI)"
    ),
    "refusal_rate": (
        r"\b(?:i (?:must )?refuse|i can't help|i cannot help|won't provide|"
        r"cannot assist|can't assist)\b|拒绝|不能帮助|无法帮助|不能协助|无法协助|"
        r"不能提供|无法提供"
    ),
    "apology_rate": r"\b(?:sorry|apolog(?:y|ize|ise))\b|抱歉|对不起|歉意",
}

AXIS_SPEC = {
    "communal_expression": {
        "first_plural_rate": 1,
        "second_person_rate": 1,
        "praise_rate": 1,
        "encouragement_rate": 1,
    },
    "dialogic_engagement": {
        "first_plural_rate": 1,
        "second_person_rate": 1,
        "question_rate": 1,
    },
    "directive_expression": {
        "imperative_rate": 1,
        "explanation_rate": 1,
        "answer_reveal_rate": 1,
        "question_rate": -1,
        "hedge_rate": -1,
        "uncertainty_acknowledgment_rate": -1,
    },
    "epistemic_caution_language": {
        "hedge_rate": 1,
        "uncertainty_acknowledgment_rate": 1,
        "limitation_rate": 1,
        "answer_reveal_rate": -1,
    },
    "boundary_refusal_expression": {
        "refusal_rate": 1,
        "limitation_rate": 1,
        "apology_rate": 1,
    },
    "organizational_style": {
        "markdown_heading_rate": 1,
        "bullet_rate": 1,
        "numbered_step_rate": 1,
    },
    "verbosity": {"log_tokens": 1},
}

EDUCATIONAL_BRIDGES = (
    ("communal_expression", "relational_communion", 1),
    ("dialogic_engagement", "instructional_agency", -1),
    ("dialogic_engagement", "assistance_directness", -1),
    ("directive_expression", "instructional_agency", 1),
    ("directive_expression", "assistance_directness", 1),
    ("epistemic_caution_language", "epistemic_commitment", -1),
    ("organizational_style", "next_step_actionability", 1),
)


def token_count(text: str) -> int:
    return max(1, len(re.findall(
        r"[A-Za-z]+(?:['’][A-Za-z]+)?|\d+(?:\.\d+)?|[\u4e00-\u9fff]", text
    )))


def bridge_features(text: str) -> dict[str, float]:
    features = extract_features(text)
    denominator = token_count(text)
    for name, pattern in EXTRA_PATTERNS.items():
        features[name] = 100.0 * len(re.findall(pattern, text, flags=re.IGNORECASE)) / denominator
    return features


def exact_spearman_p(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    rho = float(spearmanr(x, y).statistic)
    if not np.isfinite(rho):
        return math.nan, math.nan
    null = []
    for permutation in itertools.permutations(range(len(y))):
        value = float(spearmanr(x, y[list(permutation)]).statistic)
        if np.isfinite(value):
            null.append(value)
    values = np.asarray(null)
    p = (1 + np.sum(np.abs(values) >= abs(rho) - 1e-12)) / (1 + len(values))
    return rho, float(p)


def bh_adjust(values: pd.Series) -> pd.Series:
    raw = values.fillna(1.0).to_numpy(float)
    order = np.argsort(raw)
    ranked = raw[order]
    adjusted = np.minimum.accumulate(
        (ranked * len(raw) / np.arange(1, len(raw) + 1))[::-1]
    )[::-1]
    output = np.empty(len(raw), dtype=float)
    output[order] = np.minimum(adjusted, 1.0)
    return pd.Series(output, index=values.index)


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def axis_values(profile: dict[str, float]) -> dict[str, float]:
    result = {}
    for axis, spec in AXIS_SPEC.items():
        result[axis] = float(np.mean([profile[feature] * sign for feature, sign in spec.items()]))
    return result


def profile_benchmark(
    benchmark: str,
    model_runs: dict[str, dict[str, Any]],
    models: list[str],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    predictions = {
        model: read_latest_success(resolve_inventory_path(model_runs[model]["predictions_path"]))
        for model in models
    }
    common = sorted(set.intersection(*(set(rows) for rows in predictions.values())))
    records = []
    for item_id in common:
        for model in models:
            values = bridge_features(predictions[model][item_id]["response"])
            records.append({"item_id": item_id, "model": model, **values})
    frame = pd.DataFrame.from_records(records)
    feature_names = sorted({feature for spec in AXIS_SPEC.values() for feature in spec})
    for feature in feature_names:
        centered = frame[feature] - frame.groupby("item_id")[feature].transform("mean")
        scale = float(centered.std(ddof=0))
        frame[feature] = centered / scale if scale > 0 else 0.0
    feature_profile = frame.groupby("model", sort=True)[feature_names].mean().reset_index()
    axis_rows = []
    for row in feature_profile.to_dict(orient="records"):
        axis_rows.append({"model": row["model"], **axis_values(row)})
    coverage = {
        "benchmark": benchmark,
        "paired_items": len(common),
        "paired_responses": len(common) * len(models),
        "median_response_chars_min": min(
            model_runs[model]["prediction_stats"]["median_response_chars"] for model in models
        ),
        "median_response_chars_max": max(
            model_runs[model]["prediction_stats"]["median_response_chars"] for model in models
        ),
    }
    return pd.DataFrame(axis_rows), coverage


def pairwise_rank_summary(pivot: pd.DataFrame) -> tuple[float, float, int]:
    correlations = []
    for left, right in itertools.combinations(pivot.columns, 2):
        rho = float(spearmanr(pivot[left], pivot[right]).statistic)
        if np.isfinite(rho):
            correlations.append(rho)
    if not correlations:
        return math.nan, math.nan, 0
    return float(np.median(correlations)), float(min(correlations)), len(correlations)


def stability_table(task_axes: pd.DataFrame) -> pd.DataFrame:
    pools = {
        "non_tutoring": task_axes[task_axes["domain"].isin(NON_TUTORING_DOMAINS)],
        "default_tutoring": task_axes[task_axes["domain"] == "default_tutoring"],
        "prompted_tutoring": task_axes[task_axes["domain"] == "prompted_tutoring"],
        "all_baseline": task_axes[task_axes["condition"].isin(["baseline", "default_tutoring"])],
    }
    rows = []
    for pool_name, pool in pools.items():
        for axis in ALL_AXES:
            pivot = pool.pivot(index="model", columns="benchmark", values=axis).dropna(axis=1)
            median_rho, minimum_rho, pairs = pairwise_rank_summary(pivot)
            rows.append({
                "pool": pool_name,
                "axis": axis,
                "task_count": pivot.shape[1],
                "icc3_1": icc3_1(pivot.to_numpy()) if pivot.shape[1] >= 2 else math.nan,
                "median_pairwise_spearman": median_rho,
                "minimum_pairwise_spearman": minimum_rho,
                "task_pairs": pairs,
            })
    return pd.DataFrame(rows)


def equal_domain_profile(domain_axes: pd.DataFrame, domains: set[str]) -> pd.DataFrame:
    selected = domain_axes[domain_axes["domain"].isin(domains)]
    return selected.groupby("model", sort=True)[list(ALL_AXES)].mean()


def cross_domain_table(
    domain_axes: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    general = equal_domain_profile(domain_axes, NON_TUTORING_DOMAINS)
    default = equal_domain_profile(domain_axes, {"default_tutoring"})
    prompted = equal_domain_profile(domain_axes, {"prompted_tutoring"})
    models = sorted(set(general.index) & set(default.index) & set(prompted.index))
    rows = []
    for axis in ALL_AXES:
        for left_name, left, right_name, right in (
            ("non_tutoring", general, "default_tutoring", default),
            ("non_tutoring", general, "prompted_tutoring", prompted),
            ("default_tutoring", default, "prompted_tutoring", prompted),
        ):
            rho, p = exact_spearman_p(
                left.loc[models, axis].to_numpy(), right.loc[models, axis].to_numpy()
            )
            rows.append({
                "axis": axis,
                "left_pool": left_name,
                "right_pool": right_name,
                "spearman": rho,
                "exact_two_sided_p": p,
                "model_count": len(models),
            })
    return pd.DataFrame(rows), general, default, prompted


def surface_confound_table(general: pd.DataFrame) -> pd.DataFrame:
    rows = []
    models = sorted(general.index)
    for axis in CORE_CONTENT_AXES:
        correlations = []
        for control in SURFACE_CONTROLS:
            rho, p = exact_spearman_p(
                general.loc[models, axis].to_numpy(), general.loc[models, control].to_numpy()
            )
            rows.append({
                "axis": axis,
                "surface_control": control,
                "spearman": rho,
                "exact_two_sided_p": p,
            })
            correlations.append(abs(rho))
        rows[-1]["candidate_max_abs_surface_rho"] = max(correlations)
        rows[-2]["candidate_max_abs_surface_rho"] = max(correlations)
    return pd.DataFrame(rows)


def leave_one_domain_out_transport(domain_axes: pd.DataFrame) -> pd.DataFrame:
    default = equal_domain_profile(domain_axes, {"default_tutoring"})
    rows = []
    for omitted in sorted(NON_TUTORING_DOMAINS):
        retained = NON_TUTORING_DOMAINS - {omitted}
        general = equal_domain_profile(domain_axes, retained)
        models = sorted(set(general.index) & set(default.index))
        for axis in ALL_AXES:
            rho, p = exact_spearman_p(
                general.loc[models, axis].to_numpy(), default.loc[models, axis].to_numpy()
            )
            rows.append({
                "axis": axis,
                "omitted_non_tutoring_domain": omitted,
                "spearman": rho,
                "exact_two_sided_p": p,
                "model_count": len(models),
            })
    return pd.DataFrame(rows)


def educational_bridge_table(general: pd.DataFrame, educational_path: Path) -> pd.DataFrame:
    educational = pd.read_csv(educational_path)
    wide = educational.pivot(index="model", columns="axis", values="estimate")
    models = sorted(set(general.index) & set(wide.index))
    rows = []
    for general_axis, educational_axis, expected_sign in EDUCATIONAL_BRIDGES:
        rho, p = exact_spearman_p(
            general.loc[models, general_axis].to_numpy(),
            wide.loc[models, educational_axis].to_numpy(),
        )
        rows.append({
            "general_manifestation": general_axis,
            "educational_axis": educational_axis,
            "expected_sign": expected_sign,
            "spearman": rho,
            "direction_matches": bool(np.sign(rho) == expected_sign),
            "exact_two_sided_p": p,
            "model_count": len(models),
        })
    result = pd.DataFrame(rows)
    result["bh_q"] = bh_adjust(result["exact_two_sided_p"])
    return result


def prompt_displacement_table(task_axes: pd.DataFrame) -> pd.DataFrame:
    pairs = {
        "standard": ("mathtutorbench_scaffolding", "mathtutorbench_pedagogy"),
        "hard": ("mathtutorbench_scaffolding_hard", "mathtutorbench_pedagogy_hard"),
    }
    indexed = task_axes.set_index(["benchmark", "model"])
    rows = []
    for pair_name, (generic, pedagogy) in pairs.items():
        models = sorted(set(task_axes.loc[task_axes["benchmark"] == generic, "model"]))
        for model in models:
            for axis in ALL_AXES:
                rows.append({
                    "pair": pair_name,
                    "model": model,
                    "axis": axis,
                    "relative_centered_displacement": float(
                        indexed.loc[(pedagogy, model), axis] - indexed.loc[(generic, model), axis]
                    ),
                })
    return pd.DataFrame(rows)


def decision_payload(
    inventory: dict[str, Any], coverage: pd.DataFrame, stability: pd.DataFrame,
    transport: pd.DataFrame, confounds: pd.DataFrame,
) -> dict[str, Any]:
    non_tutoring = stability[stability["pool"] == "non_tutoring"].set_index("axis")
    default_transport = transport[
        (transport["left_pool"] == "non_tutoring")
        & (transport["right_pool"] == "default_tutoring")
    ].set_index("axis")
    max_confound = confounds.groupby("axis")["candidate_max_abs_surface_rho"].max()
    interpretable = {
        "communal_expression": True,
        "dialogic_engagement": True,
        "directive_expression": True,
        "epistemic_caution_language": True,
        "boundary_refusal_expression": False,
    }
    candidates = []
    for axis in CORE_CONTENT_AXES:
        row = {
            "axis": axis,
            "non_tutoring_stability_gate": bool(
                non_tutoring.loc[axis, "task_count"] >= 3
                and (
                    non_tutoring.loc[axis, "icc3_1"] >= 0.50
                    or non_tutoring.loc[axis, "median_pairwise_spearman"] >= 0.50
                )
            ),
            "cross_domain_transport_gate": bool(
                abs(default_transport.loc[axis, "spearman"]) >= 0.70
            ),
            "surface_nonreduction_gate": bool(max_confound.loc[axis] < 0.80),
            "interpretability_gate": interpretable[axis],
            "non_tutoring_icc3_1": float(non_tutoring.loc[axis, "icc3_1"]),
            "non_tutoring_median_pairwise_spearman": float(
                non_tutoring.loc[axis, "median_pairwise_spearman"]
            ),
            "non_tutoring_to_default_tutoring_spearman": float(
                default_transport.loc[axis, "spearman"]
            ),
            "max_abs_surface_control_spearman": float(max_confound.loc[axis]),
        }
        row["promising_for_new_experiment"] = all(
            row[key] for key in (
                "non_tutoring_stability_gate",
                "cross_domain_transport_gate",
                "surface_nonreduction_gate",
                "interpretability_gate",
            )
        )
        candidates.append(row)
    promising = [row["axis"] for row in candidates if row["promising_for_new_experiment"]]
    paired_items = sum(
        benchmark["common_success_items_core_six"]
        for benchmark in inventory["benchmarks"] if benchmark["has_core_six"]
    )
    return {
        "schema_version": 1,
        "status": "complete_existing_response_screen",
        "corpus": {
            "complete_core_benchmarks": sum(b["has_core_six"] for b in inventory["benchmarks"]),
            "all_paired_items": paired_items,
            "all_paired_responses": paired_items * len(inventory["core_models"]),
            "included_freeform_benchmarks": int(coverage["include"].sum()),
            "included_paired_items": int(coverage.loc[coverage["include"], "paired_items"].sum()),
            "included_paired_responses": int(coverage.loc[coverage["include"], "paired_responses"].sum()),
        },
        "candidate_decisions": candidates,
        "promising_candidates": promising,
        "verdict": (
            "existing_archive_supports_targeted_general_personality_experiment"
            if promising else
            "existing_archive_does_not_yet_support_general_personality_bridge"
        ),
        "next_experiment_gate": (
            "targeted_scenario_and_context_stability_experiment_warranted"
            if promising else
            "do_not_treat_new_general_personality_experiment_as_archive_confirmatory"
        ),
        "claim_boundary": (
            "Screening of observable language and interaction policies in six fixed deployed configurations; "
            "not human personality, latent-trait validation, family-level inference, or provider-version stability."
        ),
    }


def render_report(
    coverage: pd.DataFrame, stability: pd.DataFrame, transport: pd.DataFrame,
    leaveout: pd.DataFrame, bridges: pd.DataFrame, confounds: pd.DataFrame, prompt: pd.DataFrame,
    decision: dict[str, Any],
) -> str:
    corpus = decision["corpus"]
    decisions = pd.DataFrame(decision["candidate_decisions"])
    prompt_summary = prompt.assign(
        absolute_displacement=prompt["relative_centered_displacement"].abs()
    ).groupby(["pair", "axis"]).agg(
        mean_absolute_relative_displacement=("absolute_displacement", "mean"),
        minimum_relative_displacement=("relative_centered_displacement", "min"),
        maximum_relative_displacement=("relative_centered_displacement", "max"),
    ).reset_index()
    return "\n".join([
        "# Existing-response general-personality bridge: results",
        "",
        "Status: **complete archive-only screening analysis**. No generator or judge calls were made.",
        "",
        "## Corpus",
        "",
        f"The inventory contains **{corpus['all_paired_responses']:,}** paired responses "
        f"({corpus['all_paired_items']:,} items, six models, {corpus['complete_core_benchmarks']} benchmarks). "
        f"The frozen free-form eligibility rule retains **{corpus['included_paired_responses']:,}** responses "
        f"from {corpus['included_freeform_benchmarks']} benchmarks. Short labels and constrained outputs remain "
        "in the coverage table but are not interpreted as personality.",
        "",
        coverage[["benchmark", "include", "domain", "condition", "paired_items", "paired_responses", "rationale"]]
        .to_markdown(index=False),
        "",
        "## Screening decision",
        "",
        f"Verdict: `{decision['verdict']}`.",
        "",
        decisions.to_markdown(index=False, floatfmt=".3f"),
        "",
        "A large item count controls response sampling error, but the decision remains a six-model construct screen. "
        "A candidate must recur across non-tutoring tasks, transport to default tutoring, and avoid reduction to "
        "organizational style or verbosity.",
        "",
        "## Cross-task stability",
        "",
        stability.to_markdown(index=False, floatfmt=".3f"),
        "",
        "## Cross-domain transport",
        "",
        transport.to_markdown(index=False, floatfmt=".3f"),
        "",
        "### Leave-one-non-tutoring-domain-out transport",
        "",
        leaveout.to_markdown(index=False, floatfmt=".3f"),
        "",
        "## Surface-style confounds",
        "",
        confounds.to_markdown(index=False, floatfmt=".3f"),
        "",
        "## Bridge to the existing educational axes",
        "",
        bridges.to_markdown(index=False, floatfmt=".3f"),
        "",
        "These six-model correlations are hypothesis-generating. They cannot estimate a latent general-personality "
        "structure or establish that an educational axis is caused by a human personality analogue.",
        "",
        "## Existing prompt-related model reordering on the same manifestations",
        "",
        prompt_summary.to_markdown(index=False, floatfmt=".3f"),
        "",
        "Exact-item centering is performed separately inside each prompt arm, so the common prompt main effect is "
        "removed by construction. This table reports only models' relative movement around that common effect. "
        "The existing semantic and factorial analyses remain authoritative for shared prompt displacement and "
        "model-specific elasticity; this is not a new general-personality intervention.",
        "",
        "## Boundary",
        "",
        decision["claim_boundary"],
        "",
    ])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", type=Path, default=Path("artifacts/inventory/corpus_inventory.json"))
    parser.add_argument("--manifest", type=Path, default=Path("data/general_personality_bridge_manifest_v1.json"))
    parser.add_argument(
        "--educational-profiles", type=Path,
        default=Path("artifacts/educational_character_framework_v1/model_profiles.csv"),
    )
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/general_personality_bridge_v1"))
    args = parser.parse_args()

    inventory = load_json(args.inventory)
    manifest = load_json(args.manifest)["benchmarks"]
    models = list(inventory["core_models"])
    selected = {(run["benchmark"], run["model"]): run for run in inventory["selected_runs"]}
    inventory_benchmarks = {
        row["benchmark"]: row for row in inventory["benchmarks"] if row["has_core_six"]
    }
    if set(inventory_benchmarks) != set(manifest):
        missing = sorted(set(inventory_benchmarks) - set(manifest))
        extra = sorted(set(manifest) - set(inventory_benchmarks))
        raise SystemExit(f"manifest/inventory benchmark mismatch: missing={missing}, extra={extra}")

    task_axis_frames = []
    coverage_rows = []
    for benchmark in sorted(manifest):
        spec = manifest[benchmark]
        base = inventory_benchmarks[benchmark]
        coverage = {
            "benchmark": benchmark,
            "include": bool(spec["include"]),
            "domain": spec["domain"],
            "condition": spec["condition"],
            "rationale": spec["rationale"],
            "paired_items": int(base["common_success_items_core_six"]),
            "paired_responses": int(base["common_success_items_core_six"] * len(models)),
        }
        if spec["include"]:
            model_runs = {model: selected[(benchmark, model)] for model in models}
            axes, observed = profile_benchmark(benchmark, model_runs, models)
            if observed["paired_items"] != coverage["paired_items"]:
                raise RuntimeError(f"paired item drift for {benchmark}")
            coverage.update({
                "median_response_chars_min": observed["median_response_chars_min"],
                "median_response_chars_max": observed["median_response_chars_max"],
            })
            axes.insert(0, "benchmark", benchmark)
            axes.insert(1, "domain", spec["domain"])
            axes.insert(2, "condition", spec["condition"])
            task_axis_frames.append(axes)
        else:
            coverage.update({"median_response_chars_min": math.nan, "median_response_chars_max": math.nan})
        coverage_rows.append(coverage)

    coverage_frame = pd.DataFrame(coverage_rows)
    task_axes = pd.concat(task_axis_frames, ignore_index=True)
    domain_axes = task_axes.groupby(["domain", "model"], sort=True)[list(ALL_AXES)].mean().reset_index()
    stability = stability_table(task_axes)
    transport, general, default, prompted = cross_domain_table(domain_axes)
    leaveout = leave_one_domain_out_transport(domain_axes)
    confounds = surface_confound_table(general)
    bridges = educational_bridge_table(general, args.educational_profiles)
    prompt = prompt_displacement_table(task_axes)
    decision = decision_payload(inventory, coverage_frame, stability, transport, confounds)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    coverage_frame.to_csv(args.output_dir / "corpus_coverage.csv", index=False)
    task_axes.to_csv(args.output_dir / "task_axis_profiles.csv", index=False)
    domain_axes.to_csv(args.output_dir / "domain_axis_profiles.csv", index=False)
    stability.to_csv(args.output_dir / "cross_task_stability.csv", index=False)
    transport.to_csv(args.output_dir / "cross_domain_transport.csv", index=False)
    leaveout.to_csv(args.output_dir / "leave_one_domain_out_transport.csv", index=False)
    confounds.to_csv(args.output_dir / "surface_confound_audit.csv", index=False)
    bridges.to_csv(args.output_dir / "educational_axis_bridge.csv", index=False)
    prompt.to_csv(args.output_dir / "prompt_displacement.csv", index=False)
    (args.output_dir / "decision.json").write_text(
        json.dumps(decision, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    report = render_report(
        coverage_frame, stability, transport, leaveout, bridges, confounds, prompt, decision
    )
    (args.output_dir / "report.md").write_text(report, encoding="utf-8")
    print(args.output_dir / "report.md")


if __name__ == "__main__":
    main()
