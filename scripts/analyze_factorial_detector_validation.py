#!/usr/bin/env python3
"""Analyze blind three-judge validation of factorial outcome detectors."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from run_factorial_detector_validation import LABELS, load_jsonl, valid_annotation


ROOT = Path(__file__).resolve().parents[1]
JUDGE_FAMILIES = {
    "MiniMax-M3": {"MiniMax-M3", "MiniMax-M2.7"},
    "glm-5.2": {"glm-5.2"},
    "deepseek-v4-pro": {"deepseek-v4-pro"},
}


def confusion_metrics(detector: np.ndarray, gold: np.ndarray) -> dict[str, float | int]:
    detector = detector.astype(int)
    gold = gold.astype(int)
    tp = int(((detector == 1) & (gold == 1)).sum())
    tn = int(((detector == 0) & (gold == 0)).sum())
    fp = int(((detector == 1) & (gold == 0)).sum())
    fn = int(((detector == 0) & (gold == 1)).sum())

    def ratio(numerator: int, denominator: int) -> float:
        return float(numerator / denominator) if denominator else float("nan")

    sensitivity = ratio(tp, tp + fn)
    specificity = ratio(tn, tn + fp)
    accuracy = ratio(tp + tn, tp + tn + fp + fn)
    balanced = float(np.nanmean([sensitivity, specificity]))
    ppv = ratio(tp, tp + fp)
    npv = ratio(tn, tn + fn)
    observed = accuracy
    n = tp + tn + fp + fn
    detector_positive = ratio(tp + fp, n)
    gold_positive = ratio(tp + fn, n)
    expected = detector_positive * gold_positive + (1 - detector_positive) * (1 - gold_positive)
    kappa = ratio(int(0), 0) if expected == 1 else float((observed - expected) / (1 - expected))
    return {
        "n": n,
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "accuracy": accuracy,
        "balanced_accuracy": balanced,
        "sensitivity": sensitivity,
        "specificity": specificity,
        "positive_predictive_value": ppv,
        "negative_predictive_value": npv,
        "cohen_kappa": kappa,
    }


def bootstrap_balanced_accuracy(
    detector: np.ndarray, gold: np.ndarray, reps: int, seed: int,
) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    values = []
    for _ in range(reps):
        indices = rng.integers(0, len(detector), size=len(detector))
        sampled_gold = gold[indices]
        if len(np.unique(sampled_gold)) < 2:
            continue
        values.append(confusion_metrics(detector[indices], sampled_gold)["balanced_accuracy"])
    if not values:
        return float("nan"), float("nan")
    return float(np.quantile(values, 0.025)), float(np.quantile(values, 0.975))


def majority_label(values: list[str]) -> str:
    yes = sum(value == "yes" for value in values)
    no = sum(value == "no" for value in values)
    if yes >= 2:
        return "yes"
    if no >= 2:
        return "no"
    return "uncertain"


def load_detector_rows(root: Path, spec: dict[str, Any], samples: pd.DataFrame) -> pd.DataFrame:
    frames = []
    for panel, panel_spec in spec["panels"].items():
        metrics = pd.read_csv(root / panel_spec["derived_metrics"], dtype={"sample_id": str})
        metrics["panel"] = panel
        frames.append(metrics[["panel", "sample_id", "model", *LABELS]])
    detectors = pd.concat(frames, ignore_index=True)
    merged = samples.merge(detectors, on=["panel", "sample_id", "model"], how="left", validate="one_to_one")
    if merged[list(LABELS)].isna().any().any():
        raise RuntimeError("selected validation units are missing detector values")
    return merged


def load_judge_labels(
    root: Path, spec: dict[str, Any], samples: pd.DataFrame,
) -> pd.DataFrame:
    batches = {
        row["batch_id"]: row for row in load_jsonl(
            root / "artifacts/factorial_detector_validation_v1/batch_plan.jsonl"
        )
    }
    expected = {f"{batch_id}|{judge}" for batch_id in batches for judge in spec["judges"]}
    latest = {}
    for row in load_jsonl(root / "artifacts/factorial_detector_validation_v1/run/annotations.jsonl"):
        annotation_id = str(row.get("annotation_id", ""))
        if annotation_id:
            latest[annotation_id] = row
    if set(latest) != expected:
        raise RuntimeError(
            f"annotation coverage mismatch: success candidates={len(latest)} expected={len(expected)} "
            f"missing={sorted(expected - set(latest))[:3]} unexpected={sorted(set(latest) - expected)[:3]}"
        )
    labels = []
    selected_ids = set(samples["validation_id"])
    for annotation_id in sorted(expected):
        row = latest[annotation_id]
        mapping = row.get("candidate_mapping") or {}
        annotation = row.get("annotation") or {}
        if row.get("error") or not valid_annotation(annotation, list(mapping)):
            raise RuntimeError(f"invalid final annotation: {annotation_id}")
        batch_id = row["batch_id"]
        if set(mapping.values()) != set(batches[batch_id]["validation_ids"]):
            raise RuntimeError(f"candidate mapping mismatch: {annotation_id}")
        if not set(mapping.values()) <= selected_ids:
            raise RuntimeError(f"unknown validation unit: {annotation_id}")
        for blind_label, validation_id in mapping.items():
            candidate = annotation["candidates"][blind_label]
            for metric in LABELS:
                labels.append({
                    "validation_id": validation_id,
                    "judge": row["judge"],
                    "metric": metric,
                    "label": str(candidate[metric]).lower(),
                    "confidence": annotation["confidence"],
                    "batch_id": batch_id,
                    "prompt_sha256": row["prompt_sha256"],
                })
    frame = pd.DataFrame(labels)
    expected_rows = len(samples) * len(spec["judges"]) * len(LABELS)
    if len(frame) != expected_rows or frame.duplicated(["validation_id", "judge", "metric"]).any():
        raise RuntimeError(f"judge label matrix is not rectangular: {len(frame)} vs {expected_rows}")
    return frame


def build_majority(samples: pd.DataFrame, labels: pd.DataFrame) -> pd.DataFrame:
    records = []
    detector_lookup = samples.set_index("validation_id")
    for (validation_id, metric), group in labels.groupby(["validation_id", "metric"], sort=True):
        values = list(group["label"])
        source = detector_lookup.loc[validation_id]
        records.append({
            "validation_id": validation_id,
            "panel": source["panel"],
            "base_id": source["base_id"],
            "sample_id": source["sample_id"],
            "model": source["model"],
            "metric": metric,
            "detector_label": int(source[metric]),
            "majority_label": majority_label(values),
            "yes_votes": sum(value == "yes" for value in values),
            "no_votes": sum(value == "no" for value in values),
            "uncertain_votes": sum(value == "uncertain" for value in values),
        })
    return pd.DataFrame(records)


def metric_report(majority: pd.DataFrame, spec: dict[str, Any]) -> pd.DataFrame:
    gate = spec["validation_gate"]
    rows = []
    for index, metric in enumerate(LABELS):
        all_rows = majority[majority["metric"] == metric]
        classified = all_rows[all_rows["majority_label"].isin(["yes", "no"])]
        detector = classified["detector_label"].to_numpy(dtype=int)
        gold = (classified["majority_label"] == "yes").to_numpy(dtype=int)
        values = confusion_metrics(detector, gold)
        low, high = bootstrap_balanced_accuracy(
            detector, gold, int(gate["bootstrap_reps"]), int(spec["seed"]) + index,
        )
        coverage = len(classified) / len(all_rows)
        values.update({
            "metric": metric,
            "majority_label_coverage": coverage,
            "balanced_accuracy_ci_low": low,
            "balanced_accuracy_ci_high": high,
        })
        values["coverage_pass"] = coverage >= gate["majority_label_coverage_min"]
        values["balanced_accuracy_pass"] = values["balanced_accuracy"] >= gate["balanced_accuracy_min"]
        values["bootstrap_ci_pass"] = low >= gate["balanced_accuracy_bootstrap_ci_low_min"]
        values["kappa_pass"] = values["cohen_kappa"] >= gate["cohen_kappa_min"]
        values["validated"] = all(
            values[name] for name in (
                "coverage_pass", "balanced_accuracy_pass", "bootstrap_ci_pass", "kappa_pass"
            )
        )
        rows.append(values)
    return pd.DataFrame(rows)


def subgroup_report(majority: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for metric in LABELS:
        frame = majority[
            (majority["metric"] == metric) & majority["majority_label"].isin(["yes", "no"])
        ]
        for dimension in ("panel", "model"):
            for group, subset in frame.groupby(dimension, sort=True):
                gold = (subset["majority_label"] == "yes").to_numpy(dtype=int)
                values = confusion_metrics(subset["detector_label"].to_numpy(dtype=int), gold)
                rows.append({"metric": metric, "dimension": dimension, "group": group, **values})
    return pd.DataFrame(rows)


def judge_leaveout_report(samples: pd.DataFrame, labels: pd.DataFrame, judges: list[str]) -> pd.DataFrame:
    sample_models = samples.set_index("validation_id")["model"].to_dict()
    rows = []
    for judge in judges:
        other = [name for name in judges if name != judge]
        for metric in LABELS:
            pivot = labels[labels["metric"] == metric].pivot(
                index="validation_id", columns="judge", values="label"
            )
            reference = pivot[other[0]].where(pivot[other[0]] == pivot[other[1]], "uncertain")
            eligible = reference.isin(["yes", "no"]) & pivot[judge].isin(["yes", "no"])
            for family_group, mask in {
                "ALL": eligible,
                "same_family": eligible & pd.Series(
                    {key: sample_models[key] in JUDGE_FAMILIES[judge] for key in pivot.index}
                ),
                "other_family": eligible & pd.Series(
                    {key: sample_models[key] not in JUDGE_FAMILIES[judge] for key in pivot.index}
                ),
            }.items():
                n = int(mask.sum())
                agreement = float((pivot.loc[mask, judge] == reference.loc[mask]).mean()) if n else float("nan")
                rows.append({
                    "judge": judge,
                    "metric": metric,
                    "candidate_family_group": family_group,
                    "comparable_units": n,
                    "agreement_with_other_two": agreement,
                })
    return pd.DataFrame(rows)


def write_report(output: Path, metrics: pd.DataFrame, decision: dict[str, Any]) -> None:
    lines = [
        "# Factorial detector validation",
        "",
        f"Overall downgrade-only decision: **{'PASS' if decision['all_detectors_validated'] else 'DOWNGRADE'}**",
        "",
        "| Metric | Coverage | Balanced accuracy (95% CI) | Kappa | Validated |",
        "|---|---:|---:|---:|:---:|",
    ]
    for row in metrics.to_dict("records"):
        lines.append(
            f"| {row['metric']} | {row['majority_label_coverage']:.3f} | "
            f"{row['balanced_accuracy']:.3f} [{row['balanced_accuracy_ci_low']:.3f}, "
            f"{row['balanced_accuracy_ci_high']:.3f}] | {row['cohen_kappa']:.3f} | "
            f"{'yes' if row['validated'] else 'NO'} |"
        )
    lines += [
        "",
        "Validation is post-result and downgrade-only. It does not establish tutoring quality, learner understanding, or learning gain.",
    ]
    (output / "detector_validation_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--spec", type=Path, default=Path("data/factorial_detector_validation_spec_v1.json"))
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/factorial_detector_validation_analysis_v1"))
    args = parser.parse_args()
    root = args.root.resolve()
    spec = json.loads((root / args.spec).read_text(encoding="utf-8"))
    samples = pd.DataFrame(load_jsonl(
        root / "artifacts/factorial_detector_validation_v1/sample_manifest.jsonl"
    ))
    if len(samples) != spec["success_gate"]["response_units"]:
        raise RuntimeError("validation sample size does not match frozen gate")
    samples = load_detector_rows(root, spec, samples)
    labels = load_judge_labels(root, spec, samples)
    majority = build_majority(samples, labels)
    metrics = metric_report(majority, spec)
    subgroups = subgroup_report(majority)
    judge_leaveout = judge_leaveout_report(samples, labels, list(spec["judges"]))
    decision = {
        "schema_version": 1,
        "response_units": len(samples),
        "batches": spec["success_gate"]["batches"],
        "annotations": spec["success_gate"]["annotations"],
        "detectors": {
            row["metric"]: {
                "validated": bool(row["validated"]),
                "majority_label_coverage": float(row["majority_label_coverage"]),
                "balanced_accuracy": float(row["balanced_accuracy"]),
                "balanced_accuracy_ci_low": float(row["balanced_accuracy_ci_low"]),
                "balanced_accuracy_ci_high": float(row["balanced_accuracy_ci_high"]),
                "cohen_kappa": float(row["cohen_kappa"]),
            }
            for row in metrics.to_dict("records")
        },
        "all_detectors_validated": bool(metrics["validated"].all()),
        "rule": spec["decision_rule"],
    }
    output = root / args.output_dir
    output.mkdir(parents=True, exist_ok=True)
    labels.to_csv(output / "judge_labels.csv", index=False)
    majority.to_csv(output / "majority_labels.csv", index=False)
    metrics.to_csv(output / "detector_validation_metrics.csv", index=False)
    subgroups.to_csv(output / "detector_validation_subgroups.csv", index=False)
    judge_leaveout.to_csv(output / "judge_leaveout_agreement.csv", index=False)
    (output / "detector_validation_report.json").write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    write_report(output, metrics, decision)
    print(json.dumps(decision, sort_keys=True))


if __name__ == "__main__":
    main()
