#!/usr/bin/env python3
"""Post-hoc, text-free diagnostics for the frozen two-stage selector trial."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from analyze_policy_homogenization import bootstrap_mean


SELECTORS = ("selector_ask_first", "selector_explain_first")


def validate_frame(frame: pd.DataFrame) -> None:
    required = {"context_id", "target_act", "model"}
    for selector in SELECTORS:
        required.update({
            f"{selector}_selected_action",
            f"{selector}_valid",
            f"{selector}_target_match",
        })
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"missing binary metric columns: {sorted(missing)}")
    if frame.duplicated(["context_id", "model"]).any():
        raise ValueError("expected one row per context and model")
    if set(frame.target_act) != {"probing", "telling"}:
        raise ValueError("expected probing and telling targets")


def long_selectors(frame: pd.DataFrame) -> pd.DataFrame:
    records = []
    for row in frame.itertuples(index=False):
        for selector in SELECTORS:
            action = str(getattr(row, f"{selector}_selected_action"))
            valid = int(getattr(row, f"{selector}_valid"))
            records.append({
                "context_id": row.context_id,
                "target_act": row.target_act,
                "model": row.model,
                "selector": selector,
                "selected_action": action,
                "valid": valid,
                "ask_selected": int(action == "ASK"),
                "target_match": int(getattr(row, f"{selector}_target_match")),
            })
    return pd.DataFrame(records)


def grouped_rates(long: pd.DataFrame, groups: list[str]) -> pd.DataFrame:
    rows = []
    for keys, group in long.groupby(groups, sort=True):
        keys = keys if isinstance(keys, tuple) else (keys,)
        valid = group[group.valid == 1]
        row = dict(zip(groups, keys))
        row.update({
            "rows": len(group),
            "valid_rate": float(group.valid.mean()),
            "invalid_rate": float(1 - group.valid.mean()),
            "ask_rate_all": float(group.ask_selected.mean()),
            "ask_rate_among_valid": (
                float(valid.ask_selected.mean()) if len(valid) else np.nan
            ),
            "target_accuracy": float(group.target_match.mean()),
        })
        rows.append(row)
    return pd.DataFrame(rows)


def target_separation(
    long: pd.DataFrame, reps: int, seed: int,
) -> pd.DataFrame:
    rows = []
    index = 0
    for selector, selector_group in long.groupby("selector", sort=True):
        panels = [("ALL", selector_group)] + list(
            selector_group.groupby("model", sort=True)
        )
        for model, group in panels:
            contexts = group.groupby(
                ["context_id", "target_act"], sort=True,
            ).ask_selected.mean().reset_index()
            probing = contexts[
                contexts.target_act == "probing"
            ].ask_selected.to_numpy()
            telling = contexts[
                contexts.target_act == "telling"
            ].ask_selected.to_numpy()
            rng = np.random.default_rng(seed + index)
            draws = (
                rng.choice(probing, size=(reps, len(probing)), replace=True).mean(axis=1)
                - rng.choice(telling, size=(reps, len(telling)), replace=True).mean(axis=1)
            )
            lo, hi = np.quantile(draws, [0.025, 0.975])
            rows.append({
                "selector": selector,
                "model": model,
                "probing_ask_rate": float(probing.mean()),
                "telling_ask_rate": float(telling.mean()),
                "probing_minus_telling_ask_rate": float(
                    probing.mean() - telling.mean()
                ),
                "stratified_context_bootstrap_ci_low": float(lo),
                "stratified_context_bootstrap_ci_high": float(hi),
            })
            index += 1
    return pd.DataFrame(rows)


def wording_audit(frame: pd.DataFrame, reps: int, seed: int) -> dict[str, float | int]:
    first = frame[f"{SELECTORS[0]}_selected_action"]
    second = frame[f"{SELECTORS[1]}_selected_action"]
    first_valid = frame[f"{SELECTORS[0]}_valid"].astype(bool)
    second_valid = frame[f"{SELECTORS[1]}_valid"].astype(bool)
    both_valid = first_valid & second_valid
    first_ask = first.eq("ASK").astype(int)
    second_ask = second.eq("ASK").astype(int)
    per_context = pd.DataFrame({
        "context_id": frame.context_id,
        "ask_first_minus_explain_first": first_ask - second_ask,
    }).groupby("context_id", sort=True).ask_first_minus_explain_first.mean()
    lo, hi = bootstrap_mean(per_context.to_numpy(), reps, seed)
    return {
        "rows": len(frame),
        "both_valid_rate": float(both_valid.mean()),
        "agreement_rate_given_both_valid": (
            float((first[both_valid] == second[both_valid]).mean())
            if both_valid.any() else float("nan")
        ),
        "ask_first_prompt_ask_rate": float(first_ask.mean()),
        "explain_first_prompt_ask_rate": float(second_ask.mean()),
        "ask_first_minus_explain_first_ask_rate": float(
            (first_ask - second_ask).mean()
        ),
        "position_effect_context_cluster_ci_low": lo,
        "position_effect_context_cluster_ci_high": hi,
        "ask_first_ask_to_explain_first_explain_rate": float(
            (first.eq("ASK") & second.eq("EXPLAIN")).mean()
        ),
        "ask_first_explain_to_explain_first_ask_rate": float(
            (first.eq("EXPLAIN") & second.eq("ASK")).mean()
        ),
    }


def analyze(frame: pd.DataFrame, reps: int, seed: int) -> tuple[
    pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, object]
]:
    validate_frame(frame)
    long = long_selectors(frame)
    overall = grouped_rates(long, ["selector"])
    by_target = grouped_rates(long, ["selector", "target_act"])
    by_target.insert(2, "model", "ALL")
    by_target_model = pd.concat([
        by_target,
        grouped_rates(long, ["selector", "target_act", "model"]),
    ], ignore_index=True).sort_values(
        ["selector", "target_act", "model"], ignore_index=True,
    )
    separation = target_separation(long, reps, seed)
    report = {
        "schema_version": 1,
        "status": "post_hoc_text_free_selector_diagnostic",
        "rows": len(frame),
        "contexts": int(frame.context_id.nunique()),
        "models": sorted(frame.model.unique().tolist()),
        "wording_audit": wording_audit(frame, reps, seed + 10_000),
        "interpretation_boundary": (
            "These diagnostics were specified after the registered trial result was known. "
            "They localize action and format biases but do not alter any prospective gate."
        ),
    }
    return overall, by_target_model, separation, report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input", type=Path,
        default=Path("artifacts/two_stage_routing_trial_analysis_v1/binary_response_metrics.csv"),
    )
    parser.add_argument(
        "--output-dir", type=Path,
        default=Path("artifacts/two_stage_selection_bias_audit_v1"),
    )
    parser.add_argument("--bootstrap-reps", type=int, default=4000)
    parser.add_argument("--seed", type=int, default=20260903)
    args = parser.parse_args()
    overall, by_target_model, separation, report = analyze(
        pd.read_csv(args.input), args.bootstrap_reps, args.seed,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    overall.to_csv(args.output_dir / "selector_action_rates.csv", index=False)
    by_target_model.to_csv(
        args.output_dir / "selector_action_rates_by_target_model.csv", index=False,
    )
    separation.to_csv(args.output_dir / "selector_target_separation.csv", index=False)
    (args.output_dir / "selection_bias_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8",
    )
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
