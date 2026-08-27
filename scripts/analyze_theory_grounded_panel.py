#!/usr/bin/env python3
"""Analyze the blind theory-grounded educational-character judge panel.

Only hashes, identifiers, ratings, and aggregate statistics are exported.  Raw
educational contexts and candidate responses remain in the upstream corpus.
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from run_theory_grounded_judge import DIMENSIONS, RUBRIC_VERSION


ARM = {
    "mathtutorbench_scaffolding": "generic",
    "mathtutorbench_pedagogy": "pedagogy",
    "mathtutorbench_scaffolding_hard": "generic",
    "mathtutorbench_pedagogy_hard": "pedagogy",
    "mathtutorbench_socratic": "socratic",
    "longtutor_teaching": "longitudinal",
}
TASK = {
    "mathtutorbench_scaffolding": "mathdial_standard",
    "mathtutorbench_pedagogy": "mathdial_standard",
    "mathtutorbench_scaffolding_hard": "mathdial_hard",
    "mathtutorbench_pedagogy_hard": "mathdial_hard",
    "mathtutorbench_socratic": "socratic",
    "longtutor_teaching": "longtutor",
}

FEATURE_ANCHORS = {
    "instructional_agency": (("imperative_rate", 1), ("question_rate", -1)),
    "relational_communion": (("praise_rate", 1), ("encouragement_rate", 1)),
    "information_structure": (("bullet_rate", 1), ("numbered_step_rate", 1)),
    "learner_contingency": (("history_reference_rate", 1), ("diagnosis_rate", 1)),
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def latest_rows(path: Path) -> tuple[dict[str, dict[str, Any]], int]:
    latest: dict[str, dict[str, Any]] = {}
    invalid = 0
    if not path.exists():
        return latest, invalid
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                invalid += 1
                continue
            annotation_id = str(row.get("annotation_id") or "")
            if annotation_id:
                latest[annotation_id] = row
    return latest, invalid


def expected_ids(
    manifest: dict[str, Any], split: str, judges: list[str], benchmarks: set[str],
) -> set[str]:
    return {
        f"{item['benchmark']}|{item['item_id']}|{judge}"
        for item in manifest["items"]
        for judge in judges
        if (split == "all" or item["split"] == split)
        and (not benchmarks or item["benchmark"] in benchmarks)
    }


def unblind(rows: dict[str, dict[str, Any]]) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    for row in rows.values():
        annotation = row["annotation"]
        for label, model in row["candidate_mapping"].items():
            scores = annotation["candidates"][label]
            for dimension in DIMENSIONS:
                records.append({
                    "benchmark": row["benchmark"],
                    "task": TASK[row["benchmark"]],
                    "arm": ARM[row["benchmark"]],
                    "split": row.get("split", ""),
                    "item_id": str(row["item_id"]),
                    "pair_id": str(row["pair_id"]),
                    "model": model,
                    "response_sha256": row["response_sha256"][model],
                    "judge": row["judge"],
                    "candidate_label": label,
                    "candidate_position": ord(label) - ord("A") + 1,
                    "dimension": dimension,
                    "score": int(scores[dimension]),
                    "confidence": int(annotation["confidence"]),
                })
    return pd.DataFrame.from_records(records)


def icc3(matrix: np.ndarray, average: bool) -> float:
    n, k = matrix.shape
    if n < 2 or k < 2:
        return math.nan
    row_mean = matrix.mean(axis=1, keepdims=True)
    col_mean = matrix.mean(axis=0, keepdims=True)
    grand = matrix.mean()
    ms_row = k * np.sum((row_mean - grand) ** 2) / (n - 1)
    residual = matrix - row_mean - col_mean + grand
    ms_error = np.sum(residual**2) / ((n - 1) * (k - 1))
    if average:
        return float((ms_row - ms_error) / ms_row) if ms_row else math.nan
    denominator = ms_row + (k - 1) * ms_error
    return float((ms_row - ms_error) / denominator) if denominator else math.nan


def response_consensus(ratings: pd.DataFrame) -> pd.DataFrame:
    keys = [
        "benchmark", "task", "arm", "split", "item_id", "pair_id", "model",
        "response_sha256", "dimension",
    ]
    return ratings.groupby(keys, as_index=False).agg(
        score=("score", "median"),
        score_mean=("score", "mean"),
        judge_count=("judge", "nunique"),
    )


def agreement_tables(
    ratings: pd.DataFrame, judges: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    pairwise_rows: list[dict[str, Any]] = []
    icc_rows: list[dict[str, Any]] = []
    profile_rows: list[dict[str, Any]] = []
    target = ["benchmark", "item_id", "model", "dimension"]
    for dimension in DIMENSIONS:
        subset = ratings[ratings["dimension"] == dimension]
        wide = subset.pivot_table(index=target, columns="judge", values="score", aggfunc="last").dropna()
        available = [judge for judge in judges if judge in wide]
        values = wide[available].to_numpy()
        icc_rows.append({
            "dimension": dimension,
            "targets": len(wide),
            "judges": len(available),
            "icc_3_1": icc3(values, average=False),
            "icc_3_k": icc3(values, average=True),
            "score_sd_all_judges": float(np.std(values)),
        })
        for left, right in itertools.combinations(available, 2):
            x, y = wide[left].to_numpy(), wide[right].to_numpy()
            rho = spearmanr(x, y).statistic if np.std(x) and np.std(y) else math.nan
            pairwise_rows.append({
                "dimension": dimension,
                "judge_left": left,
                "judge_right": right,
                "targets": len(wide),
                "exact_agreement": float(np.mean(x == y)),
                "within_one": float(np.mean(np.abs(x - y) <= 1)),
                "spearman": float(rho),
                "mean_difference_left_minus_right": float(np.mean(x - y)),
            })

        profiles = subset.copy()
        profiles["centered"] = profiles["score"] - profiles.groupby(
            ["benchmark", "item_id", "judge"]
        )["score"].transform("mean")
        judge_profiles = profiles.groupby(["judge", "model"])["centered"].mean().unstack(0)
        for left, right in itertools.combinations(available, 2):
            complete = judge_profiles[[left, right]].dropna()
            rho = (
                spearmanr(complete[left], complete[right]).statistic
                if len(complete) >= 3 and complete[left].std() and complete[right].std()
                else math.nan
            )
            profile_rows.append({
                "dimension": dimension,
                "judge_left": left,
                "judge_right": right,
                "models": len(complete),
                "model_profile_spearman": float(rho),
            })
    return (
        pd.DataFrame(pairwise_rows, columns=[
            "dimension", "judge_left", "judge_right", "targets", "exact_agreement",
            "within_one", "spearman", "mean_difference_left_minus_right",
        ]),
        pd.DataFrame(icc_rows),
        pd.DataFrame(profile_rows, columns=[
            "dimension", "judge_left", "judge_right", "models", "model_profile_spearman",
        ]),
    )


def scale_diagnostics(consensus: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for dimension, group in consensus.groupby("dimension"):
        rows.append({
            "dimension": dimension,
            "responses": len(group),
            "score_mean": float(group["score"].mean()),
            "score_sd": float(group["score"].std(ddof=0)),
            "floor_fraction": float((group["score"] == 1).mean()),
            "ceiling_fraction": float((group["score"] == 5).mean()),
            "unique_scores": int(group["score"].nunique()),
        })
    return pd.DataFrame(rows)


def centered_profiles(consensus: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    data = consensus.copy()
    data["centered_score"] = data["score"] - data.groupby(
        ["benchmark", "item_id", "dimension"]
    )["score"].transform("mean")
    scale = data.groupby(["benchmark", "dimension"])["centered_score"].transform("std").replace(0, np.nan)
    data["z_centered_score"] = (data["centered_score"] / scale).fillna(0)
    profiles = data.groupby(
        ["benchmark", "task", "arm", "model", "dimension"], as_index=False
    ).agg(
        raw_mean=("score", "mean"),
        centered_mean=("centered_score", "mean"),
        z_centered_mean=("z_centered_score", "mean"),
        contexts=("item_id", "nunique"),
    )
    return data, profiles


def task_stability(profiles: pd.DataFrame) -> pd.DataFrame:
    base = profiles[profiles["arm"].isin(["generic", "socratic", "longitudinal"])]
    rows = []
    for dimension in DIMENSIONS:
        wide = base[base["dimension"] == dimension].pivot_table(
            index="model", columns="task", values="z_centered_mean", aggfunc="last"
        ).dropna(axis=1)
        correlations = []
        for left, right in itertools.combinations(wide.columns, 2):
            rho = spearmanr(wide[left], wide[right]).statistic if wide[left].std() and wide[right].std() else math.nan
            if np.isfinite(rho):
                correlations.append(float(rho))
        rows.append({
            "dimension": dimension,
            "models": len(wide),
            "tasks": len(wide.columns),
            "icc_3_1": icc3(wide.to_numpy(), average=False),
            "median_pairwise_spearman": float(np.median(correlations)) if correlations else math.nan,
            "minimum_pairwise_spearman": float(np.min(correlations)) if correlations else math.nan,
        })
    return pd.DataFrame(rows)


def prompt_effects(consensus: pd.DataFrame) -> pd.DataFrame:
    rows = []
    paired = consensus[consensus["task"].isin(["mathdial_standard", "mathdial_hard"])]
    for (task, model, dimension), group in paired.groupby(["task", "model", "dimension"]):
        wide = group.pivot_table(index="pair_id", columns="arm", values="score", aggfunc="last").dropna()
        if not {"generic", "pedagogy"}.issubset(wide):
            continue
        delta = wide["pedagogy"] - wide["generic"]
        rows.append({
            "task": task,
            "model": model,
            "dimension": dimension,
            "paired_contexts": len(delta),
            "generic_mean": float(wide["generic"].mean()),
            "pedagogy_mean": float(wide["pedagogy"].mean()),
            "mean_delta": float(delta.mean()),
            "median_delta": float(delta.median()),
            "positive_fraction": float((delta > 0).mean()),
            "negative_fraction": float((delta < 0).mean()),
        })
    return pd.DataFrame(rows)


def prompt_effect_summary(
    consensus: pd.DataFrame, bootstrap: int, seed: int,
) -> pd.DataFrame:
    """Context-clustered prompt effect and scale relative to default model spread."""
    rows = []
    rng = np.random.default_rng(seed)
    paired = consensus[consensus["task"].isin(["mathdial_standard", "mathdial_hard"])]
    for (task, dimension), group in paired.groupby(["task", "dimension"]):
        wide = group.pivot_table(
            index=["pair_id", "model"], columns="arm", values="score", aggfunc="last"
        ).dropna()
        if not {"generic", "pedagogy"}.issubset(wide):
            continue
        wide["delta"] = wide["pedagogy"] - wide["generic"]
        context_delta = wide["delta"].groupby("pair_id").mean()
        context_ids = context_delta.index.to_numpy()
        boot = []
        for _ in range(bootstrap):
            sampled = rng.choice(context_ids, size=len(context_ids), replace=True)
            boot.append(float(context_delta.loc[sampled].mean()))
        model_delta = wide["delta"].groupby("model").mean()
        generic_model_means = wide["generic"].groupby("model").mean()
        baseline_range = float(generic_model_means.max() - generic_model_means.min())
        mean_delta = float(context_delta.mean())
        rows.append({
            "task": task,
            "dimension": dimension,
            "paired_contexts": len(context_delta),
            "models": len(model_delta),
            "mean_prompt_delta": mean_delta,
            "bootstrap_ci_low": float(np.quantile(boot, .025)),
            "bootstrap_ci_high": float(np.quantile(boot, .975)),
            "generic_cross_model_range": baseline_range,
            "absolute_prompt_over_default_model_range": (
                abs(mean_delta) / baseline_range if baseline_range else math.nan
            ),
            "minimum_model_mean_delta": float(model_delta.min()),
            "maximum_model_mean_delta": float(model_delta.max()),
            "all_model_mean_deltas_positive": bool((model_delta > 0).all()),
            "all_model_mean_deltas_negative": bool((model_delta < 0).all()),
        })
    return pd.DataFrame(rows)


def partial_eta_after_item(frame: pd.DataFrame) -> float:
    if frame.empty or frame["model"].nunique() < 2:
        return math.nan
    centered = frame["score"] - frame.groupby("item_id")["score"].transform("mean")
    model_mean = centered.groupby(frame["model"]).transform("mean")
    ss_model = float(np.sum(model_mean**2))
    ss_error = float(np.sum((centered - model_mean) ** 2))
    denominator = ss_model + ss_error
    return ss_model / denominator if denominator else math.nan


def model_variance(consensus: pd.DataFrame, bootstrap: int, seed: int) -> pd.DataFrame:
    rows = []
    rng = np.random.default_rng(seed)
    for (benchmark, dimension), group in consensus.groupby(["benchmark", "dimension"]):
        estimate = partial_eta_after_item(group)
        item_ids = group["item_id"].unique()
        boot = []
        for _ in range(bootstrap):
            sampled = rng.choice(item_ids, size=len(item_ids), replace=True)
            pieces = []
            for draw, item_id in enumerate(sampled):
                piece = group[group["item_id"] == item_id].copy()
                piece["item_id"] = f"draw-{draw}"
                pieces.append(piece)
            boot.append(partial_eta_after_item(pd.concat(pieces, ignore_index=True)))
        finite = np.asarray([value for value in boot if np.isfinite(value)], dtype=float)
        rows.append({
            "benchmark": benchmark,
            "dimension": dimension,
            "contexts": len(item_ids),
            "models": group["model"].nunique(),
            "partial_eta_squared_model_after_item": estimate,
            "bootstrap_ci_low": float(np.quantile(finite, .025)) if len(finite) else math.nan,
            "bootstrap_ci_high": float(np.quantile(finite, .975)) if len(finite) else math.nan,
        })
    return pd.DataFrame(rows)


def cross_dimension_correlations(centered: pd.DataFrame) -> pd.DataFrame:
    wide = centered.pivot_table(
        index=["benchmark", "item_id", "model"], columns="dimension", values="centered_score"
    ).dropna()
    rows = []
    for left, right in itertools.combinations(DIMENSIONS, 2):
        rho = spearmanr(wide[left], wide[right]).statistic if wide[left].std() and wide[right].std() else math.nan
        rows.append({"left": left, "right": right, "responses": len(wide), "spearman": float(rho)})
    return pd.DataFrame(rows)


def old_scale_convergence(centered: pd.DataFrame, old_path: Path) -> pd.DataFrame:
    if not old_path.exists():
        return pd.DataFrame(columns=["new_dimension", "old_dimension", "responses", "spearman"])
    old = pd.read_csv(old_path)
    old = old[["benchmark", "item_id", "model", "response_sha256", "dimension", "score"]].copy()
    old["old_score"] = old["score"] - old.groupby(
        ["benchmark", "item_id", "dimension"]
    )["score"].transform("mean")
    old = old.rename(columns={"dimension": "old_dimension"})
    new = centered[[
        "benchmark", "item_id", "model", "response_sha256", "dimension", "centered_score"
    ]].rename(
        columns={"dimension": "new_dimension", "centered_score": "new_score"}
    )
    merged = new.merge(
        old,
        on=["benchmark", "item_id", "model", "response_sha256"],
        how="inner",
    )
    rows = []
    for (new_dimension, old_dimension), group in merged.groupby(["new_dimension", "old_dimension"]):
        rho = spearmanr(group["new_score"], group["old_score"]).statistic if group["new_score"].std() and group["old_score"].std() else math.nan
        rows.append({
            "new_dimension": new_dimension,
            "old_dimension": old_dimension,
            "responses": len(group),
            "spearman": float(rho),
        })
    return pd.DataFrame(rows)


def feature_convergence(centered: pd.DataFrame, feature_path: Path) -> pd.DataFrame:
    columns = [
        "new_dimension", "feature", "expected_sign", "responses", "spearman",
        "direction_pass", "magnitude_pass_0_30",
    ]
    if not feature_path.exists():
        return pd.DataFrame(columns=columns)
    features = pd.read_csv(feature_path)
    required = {"benchmark", "item_id", "model", "response_sha256"}
    if not required.issubset(features.columns):
        return pd.DataFrame(columns=columns)
    new = centered[[
        "benchmark", "item_id", "model", "response_sha256", "dimension", "centered_score"
    ]]
    rows = []
    for dimension, anchors in FEATURE_ANCHORS.items():
        subset = new[new["dimension"] == dimension]
        for feature, expected_sign in anchors:
            if feature not in features:
                continue
            merged = subset.merge(
                features[[*required, feature]],
                on=["benchmark", "item_id", "model", "response_sha256"],
                how="inner",
            ).dropna(subset=["centered_score", feature])
            rho = (
                spearmanr(merged["centered_score"], merged[feature]).statistic
                if len(merged) >= 3 and merged["centered_score"].std() and merged[feature].std()
                else math.nan
            )
            rows.append({
                "new_dimension": dimension,
                "feature": feature,
                "expected_sign": expected_sign,
                "responses": len(merged),
                "spearman": float(rho),
                "direction_pass": bool(np.isfinite(rho) and rho * expected_sign > 0),
                "magnitude_pass_0_30": bool(np.isfinite(rho) and rho * expected_sign >= .30),
            })
    return pd.DataFrame(rows, columns=columns)


def decisions(
    icc: pd.DataFrame,
    diagnostics: pd.DataFrame,
    profile_agreement: pd.DataFrame,
    stability: pd.DataFrame,
    variance: pd.DataFrame,
    feature_validity: pd.DataFrame,
    convergence: pd.DataFrame,
    analysis_split: str,
    judges: list[str],
    pilot_pass_dimensions: set[str] | None = None,
) -> dict[str, Any]:
    rows = []
    for dimension in DIMENSIONS:
        reliability = icc[icc["dimension"] == dimension].iloc[0]
        scale = diagnostics[diagnostics["dimension"] == dimension].iloc[0]
        profiles = profile_agreement[profile_agreement["dimension"] == dimension]
        stable = stability[stability["dimension"] == dimension].iloc[0]
        variance_rows = variance[variance["dimension"] == dimension]
        feature_rows = feature_validity[feature_validity["new_dimension"] == dimension]
        convergence_rows = convergence[convergence["new_dimension"] == dimension]
        profile_min = float(profiles["model_profile_spearman"].min()) if len(profiles) else math.nan
        measurement_gates = {
            "icc_3_k_at_least_0_60": bool(reliability["icc_3_k"] >= .60),
            "score_sd_at_least_0_50": bool(scale["score_sd"] >= .50),
            "floor_below_0_80": bool(scale["floor_fraction"] < .80),
            "ceiling_below_0_80": bool(scale["ceiling_fraction"] < .80),
            "judge_model_profile_rho_at_least_0_70": bool(profile_min >= .70),
        }
        if analysis_split == "formal":
            measurement_gates["pilot_measurement_pass"] = bool(
                pilot_pass_dimensions is not None and dimension in pilot_pass_dimensions
            )
        signature_gates = {
            "cross_task_icc_or_rank_at_least_0_50": bool(
                stable["icc_3_1"] >= .50 or stable["median_pairwise_spearman"] >= .50
            ),
            "all_observed_benchmark_variance_ci_above_zero": bool(
                len(variance_rows) and (variance_rows["bootstrap_ci_low"] > 0).all()
            ),
            "maximum_abs_old_scale_rho_below_0_80": bool(
                len(convergence_rows)
                and convergence_rows["spearman"].abs().max() < .80
            ),
        }
        criterion_gates = {
            "at_least_one_registered_behavior_anchor": bool(
                len(feature_rows) and feature_rows["magnitude_pass_0_30"].any()
            ),
        }
        reliable = all(measurement_gates.values())
        signature = reliable and all(signature_gates.values())
        validated = signature and all(criterion_gates.values())
        rows.append({
            "dimension": dimension,
            "measurement_gates": measurement_gates,
            "signature_gates": signature_gates,
            "criterion_gates": criterion_gates,
            "reliable_measurement": reliable,
            "pilot_proceed_unchanged": reliable if analysis_split == "pilot" else None,
            "cross_task_signature": signature if analysis_split == "formal" else False,
            "validated_character_axis": validated if analysis_split == "formal" else False,
            "classification_status": (
                "pilot_measurement_pass" if analysis_split == "pilot" and reliable
                else "pilot_measurement_fail" if analysis_split == "pilot"
                else "formal_validated_character_axis" if validated
                else "formal_cross_task_signature" if signature
                else "formal_signature_not_supported"
            ),
        })
    minimax_count = sum(judge.lower().startswith("minimax") for judge in judges)
    family_count = len({
        "minimax" if judge.lower().startswith("minimax")
        else "glm" if judge.lower().startswith("glm")
        else "deepseek" if judge.lower().startswith("deepseek")
        else judge.lower()
        for judge in judges
    })
    return {
        "rubric_version": RUBRIC_VERSION,
        "analysis_split": analysis_split,
        "classification": rows,
        "boundary": (
            f"The panel uses {len(judges)} judges across {family_count} model families. "
            f"MiniMax contributes {minimax_count} judge(s); leave-one-family sensitivity is "
            "required before any formal cross-family validity claim."
        ),
    }


def markdown_report(
    coverage: dict[str, Any], decision: dict[str, Any], icc: pd.DataFrame,
    diagnostics: pd.DataFrame, stability: pd.DataFrame, prompt: pd.DataFrame,
    convergence: pd.DataFrame, cross_dims: pd.DataFrame,
    feature_validity: pd.DataFrame,
) -> str:
    merged = icc.merge(diagnostics, on="dimension").merge(stability, on="dimension", suffixes=("", "_stability"))
    prompt_summary = prompt.groupby("dimension", as_index=False).agg(
        mean_prompt_delta=("mean_delta", "mean"),
        min_model_task_delta=("mean_delta", "min"),
        max_model_task_delta=("mean_delta", "max"),
    ) if len(prompt) else pd.DataFrame()
    return "\n".join([
        "# Theory-grounded educational-character panel",
        "",
        f"Status: **{coverage['split']} analysis**; successful judge calls: **{coverage['successful']}/{coverage['expected']}**.",
        "No raw educational context, candidate response, or reasoning trace is exported.",
        "",
        "## Measurement and stability",
        "",
        merged.to_markdown(index=False, floatfmt=".3f"),
        "",
        "## Fixed-panel decision",
        "",
        "```json",
        json.dumps(decision, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Prompt effects",
        "",
        prompt_summary.to_markdown(index=False, floatfmt=".3f") if len(prompt_summary) else "No complete prompt pairs.",
        "",
        "## Convergence with the original semantic panel",
        "",
        convergence.to_markdown(index=False, floatfmt=".3f") if len(convergence) else "No matched old ratings.",
        "",
        "## Registered transparent-feature anchors",
        "",
        feature_validity.to_markdown(index=False, floatfmt=".3f") if len(feature_validity) else "No matched feature rows.",
        "",
        "## Interdimension correlations after exact-item centering",
        "",
        cross_dims.to_markdown(index=False, floatfmt=".3f"),
        "",
        "## Boundary",
        "",
        decision["boundary"],
        "A response tendency is not correctness, diagnostic accuracy, action optimality, or learning gain.",
        "",
    ])


def main() -> None:
    global DIMENSIONS, RUBRIC_VERSION

    parser = argparse.ArgumentParser()
    parser.add_argument("--panel-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--split", choices=("pilot", "formal", "all"), default="pilot")
    parser.add_argument("--judges", default="")
    parser.add_argument("--benchmarks", default="")
    parser.add_argument(
        "--old-consensus", type=Path,
        default=Path("artifacts/semantic_panel/response_consensus.csv"),
    )
    parser.add_argument(
        "--behavior-features", type=Path,
        default=Path("artifacts/pilot/behavior_features.csv"),
    )
    parser.add_argument("--bootstrap", type=int, default=500)
    parser.add_argument("--seed", type=int, default=20260826)
    parser.add_argument("--require-complete", action="store_true")
    parser.add_argument(
        "--pilot-decision", type=Path,
        help="Required for formal analysis; prevents a formal-set recovery from overriding pilot failure",
    )
    args = parser.parse_args()

    manifest = read_json(args.panel_dir / "sample_manifest.json")
    rubric_version = str(manifest.get("rubric_version") or RUBRIC_VERSION)
    if rubric_version == "information_structure_facets_v1":
        DIMENSIONS = ("information_sequencing", "next_step_actionability")
    elif rubric_version == "educational_character_confirmatory_v1":
        DIMENSIONS = (
            "instructional_agency", "relational_communion", "next_step_actionability",
        )
    elif rubric_version != RUBRIC_VERSION:
        raise SystemExit(f"unsupported rubric_version: {rubric_version}")
    RUBRIC_VERSION = rubric_version
    pilot_pass_dimensions: set[str] | None = None
    if args.split == "formal":
        if not args.pilot_decision:
            raise SystemExit("--pilot-decision is required for formal analysis")
        pilot = read_json(args.pilot_decision)
        pilot_pass_dimensions = {
            row["dimension"] for row in pilot.get("classification", [])
            if row.get("pilot_proceed_unchanged") is True
        }
    judges = [judge.strip() for judge in args.judges.split(",") if judge.strip()] or list(manifest["judges"])
    benchmarks = {benchmark.strip() for benchmark in args.benchmarks.split(",") if benchmark.strip()}
    expected = expected_ids(manifest, args.split, judges, benchmarks)
    latest, invalid_jsonl = latest_rows(args.panel_dir / "annotations.jsonl")
    selected = {
        key: row for key, row in latest.items()
        if key in expected and row.get("annotation") and not row.get("error")
    }
    coverage = {
        "split": args.split,
        "judges": judges,
        "benchmarks": sorted(benchmarks),
        "expected": len(expected),
        "successful": len(selected),
        "missing_or_failed": len(expected - set(selected)),
        "invalid_jsonl_rows": invalid_jsonl,
    }
    if args.require_complete and set(selected) != expected:
        raise SystemExit(json.dumps(coverage, ensure_ascii=False))
    if not selected:
        raise SystemExit(json.dumps(coverage, ensure_ascii=False))

    args.output_dir.mkdir(parents=True, exist_ok=True)
    ratings = unblind(selected)
    consensus = response_consensus(ratings)
    pairwise, icc, profile_agreement = agreement_tables(ratings, judges)
    diagnostics = scale_diagnostics(consensus)
    centered, profiles = centered_profiles(consensus)
    stability = task_stability(profiles)
    prompt = prompt_effects(consensus)
    prompt_summary = prompt_effect_summary(consensus, args.bootstrap, args.seed + 17)
    variance = model_variance(consensus, args.bootstrap, args.seed)
    cross_dims = cross_dimension_correlations(centered)
    convergence = old_scale_convergence(centered, args.old_consensus)
    feature_validity = feature_convergence(centered, args.behavior_features)
    decision = decisions(
        icc, diagnostics, profile_agreement, stability, variance, feature_validity,
        convergence,
        args.split, judges, pilot_pass_dimensions,
    )
    decision["coverage"] = coverage

    outputs = {
        "unblinded_ratings.csv": ratings,
        "response_consensus.csv": consensus,
        "judge_pairwise_agreement.csv": pairwise,
        "judge_icc.csv": icc,
        "judge_model_profile_agreement.csv": profile_agreement,
        "scale_diagnostics.csv": diagnostics,
        "model_profiles.csv": profiles,
        "cross_task_stability.csv": stability,
        "prompt_effects.csv": prompt,
        "prompt_effect_summary.csv": prompt_summary,
        "model_variance_after_item_control.csv": variance,
        "interdimension_spearman.csv": cross_dims,
        "old_scale_convergence.csv": convergence,
        "feature_convergence.csv": feature_validity,
    }
    for filename, frame in outputs.items():
        frame.to_csv(args.output_dir / filename, index=False)
    (args.output_dir / "decision.json").write_text(
        json.dumps(decision, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (args.output_dir / "report.md").write_text(
        markdown_report(
            coverage, decision, icc, diagnostics, stability, prompt, convergence,
            cross_dims, feature_validity,
        ),
        encoding="utf-8",
    )
    print(json.dumps(coverage, ensure_ascii=False))


if __name__ == "__main__":
    main()
