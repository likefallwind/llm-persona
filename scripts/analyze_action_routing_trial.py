#!/usr/bin/env python3
"""Analyze the prospective action-routing trial with frozen human-act classifiers."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from analyze_dialogue_act_validity import classifiers, human_turns
from analyze_policy_homogenization import bootstrap_mean, normalized_entropy
from run_factorial_prompt_panel import load_jsonl


CONTRASTS = {
    "uniform_minus_generic": ("uniform_scaffold", "generic"),
    "adaptive_minus_uniform": ("adaptive_router", "uniform_scaffold"),
    "adaptive_minus_generic": ("adaptive_router", "generic"),
    "oracle_minus_generic": ("oracle_action", "generic"),
}


def validate_responses(
    spec: dict[str, Any], manifest: list[dict[str, Any]],
    plan: list[dict[str, Any]], response_rows: list[dict[str, Any]],
) -> dict[tuple[str, str], dict[str, Any]]:
    sample_map = {str(row["sample_id"]): row for row in manifest}
    expected = {
        (sample_id, str(model)) for sample_id in sample_map for model in spec["models"]
    }
    latest: dict[tuple[str, str], dict[str, Any]] = {}
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
            f"routing response panel incomplete: successful={len(successful)} "
            f"expected={len(expected)} missing={len(expected - set(successful))} "
            f"unexpected={len(set(successful) - expected)}"
        )
    planned = {
        (str(row["sample_id"]), str(row["model"])): int(row["queue_rank"])
        for row in plan
    }
    if set(planned) != expected:
        raise RuntimeError("routing order plan differs from expected response keys")
    audit_rows = []
    for key, row in successful.items():
        sample = sample_map[key[0]]
        if row.get("prompt_sha256") != sample["prompt_sha256"]:
            raise RuntimeError(f"prompt hash mismatch for {key}")
        rank = int(row.get("routing_queue_rank", -1))
        if rank != planned[key]:
            raise RuntimeError(f"observed queue rank differs from plan for {key}")
        audit_rows.append({
            "model": key[1],
            "queue_rank": rank,
            "block_index": rank // 8,
            "stratum": f"{sample['target_act']}|{sample['arm']}",
        })
    audit = pd.DataFrame(audit_rows)
    counts = audit.groupby(["model", "block_index"]).stratum.nunique()
    if len(counts) != len(spec["models"]) * 48 or not (counts == 8).all():
        raise RuntimeError("observed routing requests fail exact eight-stratum blocks")
    return successful


def classify_responses(
    spec: dict[str, Any], manifest: list[dict[str, Any]],
    successful: dict[tuple[str, str], dict[str, Any]], mathdial_dir: Path,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    train_sha = hashlib.sha256((mathdial_dir / "train.jsonl").read_bytes()).hexdigest()
    test_sha = hashlib.sha256((mathdial_dir / "test.jsonl").read_bytes()).hexdigest()
    if train_sha != spec["source_hashes"]["mathdial_train_sha256"]:
        raise RuntimeError("MathDial train hash differs from frozen spec")
    if test_sha != spec["source_hashes"]["mathdial_test_sha256"]:
        raise RuntimeError("MathDial test hash differs from frozen spec")
    turns, _lookup = human_turns(mathdial_dir)
    expected_turns = 18_541
    if len(turns) != expected_turns:
        raise RuntimeError(f"human classifier training rows drifted: {len(turns)} != {expected_turns}")
    fitted = {name: estimator.fit(turns.text, turns.act) for name, estimator in classifiers().items()}
    if set(fitted) != set(spec["analysis"]["classifier_variants"]):
        raise RuntimeError("classifier variants differ from frozen spec")
    sample_map = {str(row["sample_id"]): row for row in manifest}
    records: list[dict[str, Any]] = []
    for (sample_id, model), response_row in sorted(successful.items()):
        sample = sample_map[sample_id]
        text = str(response_row["response"])
        for variant, fitted_model in fitted.items():
            predicted = str(fitted_model.predict([text])[0])
            records.append({
                "classifier_variant": variant,
                "sample_id": sample_id,
                "context_id": sample["context_id"],
                "target_act": sample["target_act"],
                "arm": sample["arm"],
                "model": model,
                "predicted_act": predicted,
                "act_match": int(predicted == sample["target_act"]),
                "response_sha256": hashlib.sha256(text.encode()).hexdigest(),
            })
    provenance = {
        "human_training_turns": len(turns),
        "unique_math_problems": int(turns.qid.nunique()),
        "training_label_counts": {
            key: int(value) for key, value in turns.act.value_counts().sort_index().items()
        },
        "classifier_variants": sorted(fitted),
        "mathdial_train_sha256": train_sha,
        "mathdial_test_sha256": test_sha,
    }
    return pd.DataFrame(records), provenance


def contrast_tables(
    predictions: pd.DataFrame, reps: int, seed: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, Any]] = []
    model_rows: list[dict[str, Any]] = []
    for variant_index, (variant, variant_frame) in enumerate(
        predictions.groupby("classifier_variant", sort=True)
    ):
        targets = [("ALL", variant_frame)] + [
            (str(target), group)
            for target, group in variant_frame.groupby("target_act", sort=True)
        ]
        for target_index, (target, group) in enumerate(targets):
            wide = group.pivot(
                index=["context_id", "model"], columns="arm", values="act_match",
            ).reset_index()
            required_arms = {arm for pair in CONTRASTS.values() for arm in pair}
            if not required_arms.issubset(wide.columns) or wide[list(required_arms)].isna().any().any():
                raise RuntimeError(f"unpaired routing arms for {variant}|{target}")
            for contrast_index, (name, (high, low)) in enumerate(CONTRASTS.items()):
                delta = wide[high] - wide[low]
                context_delta = pd.DataFrame({
                    "context_id": wide.context_id, "delta": delta,
                }).groupby("context_id", sort=True).delta.mean().to_numpy()
                lo, hi = bootstrap_mean(
                    context_delta, reps,
                    seed + variant_index * 100_000 + target_index * 10_000 + contrast_index,
                )
                model_effects = delta.groupby(wide.model).mean()
                rows.append({
                    "classifier_variant": variant,
                    "target_act": target,
                    "contrast": name,
                    "context_count": int(wide.context_id.nunique()),
                    "model_count": int(wide.model.nunique()),
                    "mean_delta": float(delta.mean()),
                    "context_cluster_ci_low": lo,
                    "context_cluster_ci_high": hi,
                    "positive_models": int((model_effects > 0).sum()),
                    "negative_models": int((model_effects < 0).sum()),
                    "minimum_model_delta": float(model_effects.min()),
                    "maximum_model_delta": float(model_effects.max()),
                })
                for model, model_group in wide.groupby("model", sort=True):
                    values = (model_group[high] - model_group[low]).to_numpy()
                    model_lo, model_hi = bootstrap_mean(
                        values, reps,
                        seed + 500_000 + len(model_rows),
                    )
                    model_rows.append({
                        "classifier_variant": variant,
                        "target_act": target,
                        "contrast": name,
                        "model": model,
                        "context_count": len(values),
                        "mean_delta": float(values.mean()),
                        "context_bootstrap_ci_low": model_lo,
                        "context_bootstrap_ci_high": model_hi,
                    })
    return pd.DataFrame(rows), pd.DataFrame(model_rows)


def arm_means(predictions: pd.DataFrame, reps: int, seed: int) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for index, (keys, group) in enumerate(
        predictions.groupby(["classifier_variant", "target_act", "arm"], sort=True)
    ):
        context_mean = group.groupby("context_id", sort=True).act_match.mean().to_numpy()
        lo, hi = bootstrap_mean(context_mean, reps, seed + index)
        rows.append({
            "classifier_variant": keys[0],
            "target_act": keys[1],
            "arm": keys[2],
            "context_count": int(group.context_id.nunique()),
            "model_count": int(group.model.nunique()),
            "mean_match": float(group.act_match.mean()),
            "context_cluster_ci_low": lo,
            "context_cluster_ci_high": hi,
        })
    return pd.DataFrame(rows)


def consensus_effects(predictions: pd.DataFrame, reps: int, seed: int) -> pd.DataFrame:
    context = predictions.groupby(
        ["classifier_variant", "target_act", "arm", "context_id"], sort=True,
    ).predicted_act.agg(normalized_entropy=normalized_entropy).reset_index()
    rows: list[dict[str, Any]] = []
    for index, (keys, group) in enumerate(
        context.groupby(["classifier_variant", "target_act"], sort=True)
    ):
        wide = group.pivot(index="context_id", columns="arm", values="normalized_entropy")
        for contrast, (high, low) in CONTRASTS.items():
            delta = (wide[high] - wide[low]).to_numpy()
            lo, hi = bootstrap_mean(delta, reps, seed + index * 10 + len(rows))
            rows.append({
                "classifier_variant": keys[0],
                "target_act": keys[1],
                "contrast": contrast,
                "context_count": len(delta),
                "entropy_delta": float(delta.mean()),
                "context_bootstrap_ci_low": lo,
                "context_bootstrap_ci_high": hi,
            })
    return pd.DataFrame(rows)


def evaluate_gates(
    spec: dict[str, Any], contrasts: pd.DataFrame, means: pd.DataFrame,
) -> dict[str, Any]:
    gates = spec["claim_gates"]
    per_variant: dict[str, Any] = {}
    for variant in spec["analysis"]["classifier_variants"]:
        table = contrasts[contrasts.classifier_variant == variant].set_index(
            ["target_act", "contrast"]
        )
        mean_table = means[means.classifier_variant == variant].set_index(
            ["target_act", "arm"]
        )

        def row(target: str, contrast: str) -> pd.Series:
            return table.loc[(target, contrast)]

        uniform_probe = row("probing", "uniform_minus_generic")
        uniform_tell = row("telling", "uniform_minus_generic")
        adaptive_tell_uniform = row("telling", "adaptive_minus_uniform")
        adaptive_tell_generic = row("telling", "adaptive_minus_generic")
        adaptive_probe_uniform = row("probing", "adaptive_minus_uniform")
        adaptive_overall = row("ALL", "adaptive_minus_generic")
        oracle_probe = mean_table.loc[("probing", "oracle_action")]
        oracle_tell = mean_table.loc[("telling", "oracle_action")]
        checks = {
            "uniform_probing_gain_replicates": bool(
                uniform_probe.mean_delta >= gates["uniform_replication_probing_delta_min"]
                and uniform_probe.context_cluster_ci_low > 0
            ),
            "uniform_telling_harm_replicates": bool(
                uniform_tell.mean_delta <= gates["uniform_replication_telling_delta_max"]
                and uniform_tell.context_cluster_ci_high < 0
            ),
            "adaptive_recovers_telling_vs_uniform": bool(
                adaptive_tell_uniform.mean_delta
                >= gates["adaptive_telling_vs_uniform_delta_min"]
                and adaptive_tell_uniform.context_cluster_ci_low > 0
                and adaptive_tell_uniform.positive_models == len(spec["models"])
            ),
            "adaptive_telling_noninferior_to_generic": bool(
                adaptive_tell_generic.context_cluster_ci_low
                > -gates["adaptive_telling_vs_generic_noninferiority_margin"]
            ),
            "adaptive_probing_noninferior_to_uniform": bool(
                adaptive_probe_uniform.context_cluster_ci_low
                > -gates["adaptive_probing_vs_uniform_noninferiority_margin"]
            ),
            "adaptive_improves_overall_vs_generic": bool(
                adaptive_overall.mean_delta >= gates["adaptive_overall_vs_generic_delta_min"]
                and adaptive_overall.context_cluster_ci_low > 0
            ),
            "oracle_realization_check": bool(
                oracle_probe.mean_match >= gates["oracle_target_match_min"]
                and oracle_tell.mean_match >= gates["oracle_target_match_min"]
            ),
        }
        per_variant[variant] = {
            "checks": checks,
            "all_primary_gates_pass": all(checks.values()),
        }
    return {
        "per_classifier_variant": per_variant,
        "joint_all_classifier_variants_pass": all(
            result["all_primary_gates_pass"] for result in per_variant.values()
        ),
        "rule": (
            "Every frozen classifier variant must independently pass every gate. "
            "The oracle arm is a realization diagnostic and not evidence of adaptivity."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--spec", type=Path, default=Path("data/action_routing_trial_spec_v1.json"),
    )
    parser.add_argument(
        "--manifest", type=Path,
        default=Path("artifacts/action_routing_trial_v1/sample_manifest.jsonl"),
    )
    parser.add_argument(
        "--order-plan", type=Path,
        default=Path("artifacts/action_routing_trial_v1/request_order_plan.jsonl"),
    )
    parser.add_argument(
        "--responses", type=Path,
        default=Path("artifacts/action_routing_trial_v1/run/responses.jsonl"),
    )
    parser.add_argument("--mathdial-dir", type=Path)
    parser.add_argument(
        "--output-dir", type=Path,
        default=Path("artifacts/action_routing_trial_analysis_v1"),
    )
    parser.add_argument("--bootstrap-reps", type=int)
    parser.add_argument("--seed", type=int, default=20260829)
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    manifest = load_jsonl(args.manifest)
    successful = validate_responses(
        spec, manifest, load_jsonl(args.order_plan), load_jsonl(args.responses),
    )
    mathdial_dir = args.mathdial_dir or Path(spec["source_mathdial"])
    predictions, classifier_provenance = classify_responses(
        spec, manifest, successful, mathdial_dir,
    )
    reps = args.bootstrap_reps or int(spec["analysis"]["context_cluster_bootstrap_reps"])
    contrasts, model_contrasts = contrast_tables(predictions, reps, args.seed)
    means = arm_means(predictions, reps, args.seed + 100_000)
    consensus = consensus_effects(predictions, reps, args.seed + 200_000)
    decision = evaluate_gates(spec, contrasts, means)
    report = {
        "schema_version": 1,
        "status": "prospective_action_routing_trial",
        "response_rows": len(successful),
        "derived_classifier_rows": len(predictions),
        "contexts": int(predictions.context_id.nunique()),
        "models": sorted(predictions.model.unique().tolist()),
        "classifier_provenance": classifier_provenance,
        "exact_eight_stratum_block_balance": True,
        "decision": decision,
        "claim_boundary": (
            "This tests agreement with a frozen observed human next-action label in a "
            "fixed model panel. It does not establish learning benefit, globally optimal "
            "pedagogy, or a model-population effect."
        ),
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    predictions.to_csv(args.output_dir / "predicted_actions.csv", index=False)
    contrasts.to_csv(args.output_dir / "action_match_contrasts.csv", index=False)
    model_contrasts.to_csv(args.output_dir / "action_match_model_contrasts.csv", index=False)
    means.to_csv(args.output_dir / "action_match_arm_means.csv", index=False)
    consensus.to_csv(args.output_dir / "cross_model_consensus_contrasts.csv", index=False)
    (args.output_dir / "action_routing_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8",
    )
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
