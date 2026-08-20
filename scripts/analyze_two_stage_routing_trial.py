#!/usr/bin/env python3
"""Analyze the frozen two-stage tutoring action-selection trial."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Any

import numpy as np
import pandas as pd

from analyze_dialogue_act_validity import classifiers, human_turns
from analyze_policy_homogenization import bootstrap_mean
from generate_two_stage_routing_trial import stratum_key
from run_factorial_prompt_panel import load_jsonl


SELECTORS = ("selector_ask_first", "selector_explain_first")


def validate_responses(
    spec: dict[str, Any], manifest: list[dict[str, Any]],
    plan: list[dict[str, Any]], response_rows: list[dict[str, Any]],
) -> dict[tuple[str, str], dict[str, Any]]:
    sample_map = {str(row["sample_id"]): row for row in manifest}
    expected = {
        (sample_id, str(model)) for sample_id in sample_map for model in spec["models"]
    }
    latest = {}
    for row in response_rows:
        key = (str(row.get("sample_id", "")), str(row.get("model", "")))
        if all(key):
            latest[key] = row
    successful = {
        key: row for key, row in latest.items()
        if isinstance(row.get("response"), str) and row["response"].strip()
        and not row.get("error")
    }
    if set(successful) != expected:
        raise RuntimeError(
            f"two-stage panel incomplete: successful={len(successful)} "
            f"expected={len(expected)} missing={len(expected - set(successful))} "
            f"unexpected={len(set(successful) - expected)}"
        )
    planned = {
        (str(row["sample_id"]), str(row["model"])): int(row["queue_rank"])
        for row in plan
    }
    if set(planned) != expected:
        raise RuntimeError("two-stage order plan differs from expected keys")
    audit_rows = []
    for key, row in successful.items():
        sample = sample_map[key[0]]
        if row.get("prompt_sha256") != sample["prompt_sha256"]:
            raise RuntimeError(f"two-stage prompt hash mismatch for {key}")
        rank = int(row.get("two_stage_queue_rank", -1))
        if rank != planned[key]:
            raise RuntimeError(f"two-stage observed rank differs for {key}")
        audit_rows.append({
            "model": key[1], "block_index": rank // 10,
            "stratum": stratum_key(sample),
        })
    audit = pd.DataFrame(audit_rows)
    counts = audit.groupby(["model", "block_index"]).stratum.nunique()
    if len(counts) != len(spec["models"]) * 48 or not (counts == 10).all():
        raise RuntimeError("observed two-stage requests fail exact ten-stratum blocks")
    return successful


def parse_selector(text: str, pattern: str) -> str:
    normalized = str(text).strip().upper()
    match = re.fullmatch(pattern, normalized)
    return str(match.group(1)) if match else "INVALID"


def binary_rows(
    spec: dict[str, Any], manifest: list[dict[str, Any]],
    successful: dict[tuple[str, str], dict[str, Any]],
) -> pd.DataFrame:
    samples = {str(row["sample_id"]): row for row in manifest}
    response_map = {
        (samples[sample_id]["context_id"], model, samples[sample_id]["call_type"]): row
        for (sample_id, model), row in successful.items()
    }
    contexts = {
        str(row["context_id"]): str(row["target_act"]) for row in manifest
    }
    pattern = str(spec["analysis"]["selector_parse_regex"])
    records = []
    for context_id, target_act in sorted(contexts.items()):
        target_action = str(spec["binary_actions"][target_act])
        for model in spec["models"]:
            texts = {
                call_type: str(response_map[(context_id, model, call_type)]["response"]).strip()
                for call_type in spec["call_types"]
            }
            ask_realized = int("?" in texts["ask_executor"])
            explain_realized = int("?" not in texts["explain_executor"])
            single_action = "ASK" if "?" in texts["single_pass_adaptive"] else "EXPLAIN"
            row = {
                "context_id": context_id,
                "target_act": target_act,
                "target_binary_action": target_action,
                "model": model,
                "ask_executor_question_realized": ask_realized,
                "explain_executor_no_question_realized": explain_realized,
                "single_pass_binary_action": single_action,
                "single_pass_target_match": int(single_action == target_action),
                "single_pass_response_sha256": hashlib.sha256(
                    texts["single_pass_adaptive"].encode()
                ).hexdigest(),
                "ask_executor_response_sha256": hashlib.sha256(
                    texts["ask_executor"].encode()
                ).hexdigest(),
                "explain_executor_response_sha256": hashlib.sha256(
                    texts["explain_executor"].encode()
                ).hexdigest(),
            }
            for selector in SELECTORS:
                selected = parse_selector(texts[selector], pattern)
                valid = int(selected in {"ASK", "EXPLAIN"})
                if selected == "ASK":
                    composed_action = "ASK" if ask_realized else "EXPLAIN"
                    composed_text = texts["ask_executor"]
                elif selected == "EXPLAIN":
                    composed_action = "EXPLAIN" if explain_realized else "ASK"
                    composed_text = texts["explain_executor"]
                else:
                    composed_action = "INVALID"
                    composed_text = ""
                row[f"{selector}_selected_action"] = selected
                row[f"{selector}_valid"] = valid
                row[f"{selector}_target_match"] = int(valid and selected == target_action)
                row[f"{selector}_composed_action"] = composed_action
                row[f"{selector}_composed_target_match"] = int(
                    valid and composed_action == target_action
                )
                row[f"{selector}_response_sha256"] = hashlib.sha256(
                    texts[selector].encode()
                ).hexdigest()
                row[f"{selector}_composed_response_sha256"] = (
                    hashlib.sha256(composed_text.encode()).hexdigest() if composed_text else ""
                )
            records.append(row)
    return pd.DataFrame(records)


def cluster_ci(frame: pd.DataFrame, column: str, reps: int, seed: int) -> tuple[float, float]:
    values = frame.groupby("context_id", sort=True)[column].mean().to_numpy()
    return bootstrap_mean(values, reps, seed)


def primary_tables(
    frame: pd.DataFrame, reps: int, seed: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    selector_rows = []
    contrast_rows = []
    model_rows = []
    for selector_index, selector in enumerate(SELECTORS):
        valid_col = f"{selector}_valid"
        match_col = f"{selector}_target_match"
        composed_col = f"{selector}_composed_target_match"
        valid_lo, valid_hi = cluster_ci(frame, valid_col, reps, seed + selector_index * 100)
        match_lo, match_hi = cluster_ci(frame, match_col, reps, seed + selector_index * 100 + 1)
        model_accuracy = frame.groupby("model", sort=True)[match_col].mean()
        selector_rows.append({
            "selector": selector,
            "contexts": int(frame.context_id.nunique()),
            "models": int(frame.model.nunique()),
            "valid_rate": float(frame[valid_col].mean()),
            "valid_rate_ci_low": valid_lo,
            "valid_rate_ci_high": valid_hi,
            "target_accuracy": float(frame[match_col].mean()),
            "target_accuracy_ci_low": match_lo,
            "target_accuracy_ci_high": match_hi,
            "minimum_model_accuracy": float(model_accuracy.min()),
            "maximum_model_accuracy": float(model_accuracy.max()),
            "models_above_chance": int((model_accuracy > 0.5).sum()),
        })
        delta_col = f"{selector}_delta"
        delta_frame = frame.assign(**{
            delta_col: frame[composed_col] - frame["single_pass_target_match"],
        })
        lo, hi = cluster_ci(delta_frame, delta_col, reps, seed + selector_index * 100 + 2)
        effects = delta_frame.groupby("model", sort=True)[delta_col].mean()
        contrast_rows.append({
            "selector": selector,
            "contrast": "two_stage_composed_minus_single_pass",
            "mean_delta": float(delta_frame[delta_col].mean()),
            "context_cluster_ci_low": lo,
            "context_cluster_ci_high": hi,
            "positive_models": int((effects > 0).sum()),
            "minimum_model_delta": float(effects.min()),
            "maximum_model_delta": float(effects.max()),
        })
        for model, group in delta_frame.groupby("model", sort=True):
            model_lo, model_hi = bootstrap_mean(
                group[delta_col].to_numpy(), reps,
                seed + 10_000 + selector_index * 1_000 + len(model_rows),
            )
            model_rows.append({
                "selector": selector, "model": model,
                "selector_accuracy": float(group[match_col].mean()),
                "single_pass_match": float(group.single_pass_target_match.mean()),
                "composed_match": float(group[composed_col].mean()),
                "composed_minus_single_pass": float(group[delta_col].mean()),
                "context_bootstrap_ci_low": model_lo,
                "context_bootstrap_ci_high": model_hi,
            })
    return pd.DataFrame(selector_rows), pd.DataFrame(contrast_rows), pd.DataFrame(model_rows)


def execution_table(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for name, column in (
        ("ask_executor_question", "ask_executor_question_realized"),
        ("explain_executor_no_question", "explain_executor_no_question_realized"),
    ):
        model_rates = frame.groupby("model", sort=True)[column].mean()
        rows.append({
            "executor": name,
            "realization_rate": float(frame[column].mean()),
            "minimum_model_rate": float(model_rates.min()),
            "maximum_model_rate": float(model_rates.max()),
        })
    return pd.DataFrame(rows)


def fine_grained_analysis(
    spec: dict[str, Any], binary: pd.DataFrame,
    manifest: list[dict[str, Any]], successful: dict[tuple[str, str], dict[str, Any]],
    mathdial_dir: Path, reps: int, seed: int,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    turns, _ = human_turns(mathdial_dir)
    fitted = {name: estimator.fit(turns.text, turns.act) for name, estimator in classifiers().items()}
    if set(fitted) != set(spec["analysis"]["classifier_variants"]):
        raise RuntimeError("two-stage classifier variants differ from frozen spec")
    samples = {str(row["sample_id"]): row for row in manifest}
    response_map = {
        (samples[sample_id]["context_id"], model, samples[sample_id]["call_type"]): str(row["response"])
        for (sample_id, model), row in successful.items()
    }
    records = []
    for row in binary.itertuples(index=False):
        policies = {"single_pass": response_map[(row.context_id, row.model, "single_pass_adaptive")]}
        for selector in SELECTORS:
            selected = getattr(row, f"{selector}_selected_action")
            policies[selector] = (
                response_map[(row.context_id, row.model, "ask_executor")]
                if selected == "ASK" else
                response_map[(row.context_id, row.model, "explain_executor")]
                if selected == "EXPLAIN" else ""
            )
        for variant, estimator in fitted.items():
            for policy, text in policies.items():
                predicted = str(estimator.predict([text])[0]) if text else "INVALID"
                records.append({
                    "classifier_variant": variant,
                    "context_id": row.context_id,
                    "target_act": row.target_act,
                    "model": row.model,
                    "policy": policy,
                    "predicted_act": predicted,
                    "act_match": int(predicted == row.target_act),
                    "response_sha256": hashlib.sha256(text.encode()).hexdigest() if text else "",
                })
    predictions = pd.DataFrame(records)
    contrasts = []
    for index, ((variant, selector), group) in enumerate(
        predictions[predictions.policy != "single_pass"].groupby(
            ["classifier_variant", "policy"], sort=True,
        )
    ):
        base = predictions[
            (predictions.classifier_variant == variant)
            & (predictions.policy == "single_pass")
        ][["context_id", "model", "act_match"]].rename(columns={"act_match": "base"})
        paired = group.merge(base, on=["context_id", "model"], validate="one_to_one")
        paired["delta"] = paired.act_match - paired.base
        values = paired.groupby("context_id", sort=True).delta.mean().to_numpy()
        lo, hi = bootstrap_mean(values, reps, seed + index)
        effects = paired.groupby("model", sort=True).delta.mean()
        contrasts.append({
            "classifier_variant": variant,
            "selector": selector,
            "composed_minus_single_pass": float(paired.delta.mean()),
            "context_cluster_ci_low": lo,
            "context_cluster_ci_high": hi,
            "positive_models": int((effects > 0).sum()),
            "minimum_model_delta": float(effects.min()),
            "maximum_model_delta": float(effects.max()),
        })
    provenance = {
        "human_training_turns": len(turns),
        "unique_math_problems": int(turns.qid.nunique()),
        "classifier_variants": sorted(fitted),
    }
    return predictions, pd.DataFrame(contrasts), provenance


def evaluate_gates(
    spec: dict[str, Any], selectors: pd.DataFrame,
    contrasts: pd.DataFrame, execution: pd.DataFrame,
) -> dict[str, Any]:
    gates = spec["claim_gates"]
    per_selector = {}
    for row in selectors.itertuples(index=False):
        contrast = contrasts[contrasts.selector == row.selector].iloc[0]
        checks = {
            "valid_rate": bool(row.valid_rate >= gates["selector_valid_rate_min"]),
            "selector_accuracy": bool(
                row.target_accuracy >= gates["selector_accuracy_min"]
                and row.target_accuracy_ci_low > gates["selector_accuracy_ci_low_min"]
                and row.models_above_chance == len(spec["models"])
            ),
            "composed_improves_over_single_pass": bool(
                contrast.mean_delta >= gates["composed_vs_single_pass_delta_min"]
                and contrast.context_cluster_ci_low > 0
                and contrast.positive_models == len(spec["models"])
            ),
        }
        per_selector[row.selector] = {
            "checks": checks, "all_selector_gates_pass": all(checks.values()),
        }
    ask = execution[execution.executor == "ask_executor_question"].iloc[0]
    explain = execution[execution.executor == "explain_executor_no_question"].iloc[0]
    execution_pass = bool(
        ask.realization_rate >= gates["ask_executor_question_rate_min"]
        and explain.realization_rate >= gates["explain_executor_no_question_rate_min"]
        and min(ask.minimum_model_rate, explain.minimum_model_rate)
        >= gates["executor_minimum_model_rate_min"]
    )
    accuracy = selectors.set_index("selector").target_accuracy
    wording_gap = float(abs(accuracy[SELECTORS[0]] - accuracy[SELECTORS[1]]))
    wording_pass = wording_gap <= gates["selector_wording_accuracy_difference_abs_max"]
    return {
        "per_selector": per_selector,
        "execution_realization_pass": execution_pass,
        "selector_wording_accuracy_abs_difference": wording_gap,
        "selector_wording_robustness_pass": bool(wording_pass),
        "joint_two_stage_claim_pass": bool(
            execution_pass and wording_pass
            and all(value["all_selector_gates_pass"] for value in per_selector.values())
        ),
        "rule": "Both selector wordings, both executors, and the wording-gap gate must pass independently.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, default=Path("data/two_stage_routing_trial_spec_v1.json"))
    parser.add_argument("--manifest", type=Path, default=Path("artifacts/two_stage_routing_trial_v1/sample_manifest.jsonl"))
    parser.add_argument("--order-plan", type=Path, default=Path("artifacts/two_stage_routing_trial_v1/request_order_plan.jsonl"))
    parser.add_argument("--responses", type=Path, default=Path("artifacts/two_stage_routing_trial_v1/run/responses.jsonl"))
    parser.add_argument("--mathdial-dir", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/two_stage_routing_trial_analysis_v1"))
    parser.add_argument("--bootstrap-reps", type=int)
    parser.add_argument("--seed", type=int, default=20260902)
    args = parser.parse_args()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    manifest = load_jsonl(args.manifest)
    successful = validate_responses(
        spec, manifest, load_jsonl(args.order_plan), load_jsonl(args.responses),
    )
    binary = binary_rows(spec, manifest, successful)
    reps = args.bootstrap_reps or int(spec["analysis"]["context_cluster_bootstrap_reps"])
    selectors, contrasts, model_contrasts = primary_tables(binary, reps, args.seed)
    execution = execution_table(binary)
    mathdial_dir = args.mathdial_dir or Path(spec["source_mathdial"])
    predictions, fine_contrasts, classifier_provenance = fine_grained_analysis(
        spec, binary, manifest, successful, mathdial_dir, reps, args.seed + 100_000,
    )
    decision = evaluate_gates(spec, selectors, contrasts, execution)
    report = {
        "schema_version": 1,
        "status": "prospective_two_stage_selection_then_execution_trial",
        "response_rows": len(successful),
        "contexts": int(binary.context_id.nunique()),
        "models": sorted(binary.model.unique().tolist()),
        "exact_ten_stratum_block_balance": True,
        "classifier_provenance": classifier_provenance,
        "decision": decision,
        "claim_boundary": (
            "The binary target is agreement with one observed human ASK-versus-EXPLAIN "
            "next action. It does not establish action optimality, response quality, or learning."
        ),
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    binary.to_csv(args.output_dir / "binary_response_metrics.csv", index=False)
    selectors.to_csv(args.output_dir / "selector_summary.csv", index=False)
    execution.to_csv(args.output_dir / "executor_realization.csv", index=False)
    contrasts.to_csv(args.output_dir / "binary_policy_contrasts.csv", index=False)
    model_contrasts.to_csv(args.output_dir / "binary_policy_model_contrasts.csv", index=False)
    predictions.to_csv(args.output_dir / "fine_grained_action_predictions.csv", index=False)
    fine_contrasts.to_csv(args.output_dir / "fine_grained_action_contrasts.csv", index=False)
    (args.output_dir / "two_stage_routing_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8",
    )
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
