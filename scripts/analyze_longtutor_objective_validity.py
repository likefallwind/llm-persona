#!/usr/bin/env python3
"""Link LongTutor teaching behavior to human-gold diagnosis and evidence outcomes."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import accuracy_score, mean_squared_error, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from inventory_paths import resolve_inventory_path


TEACHING_DIMENSIONS = ("history_utilization", "strategy_alignment", "coherence", "appropriateness")


def latest_scored(path: Path) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            item_id = str(row.get("item_id") or "")
            if item_id and row.get("score_status") == "scored":
                rows[item_id] = row
    return rows


def selected_runs(inventory_path: Path) -> tuple[list[str], dict[tuple[str, str], dict[str, Any]]]:
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    selected = {(row["benchmark"], row["model"]): row for row in inventory["selected_runs"]}
    return inventory["core_models"], selected


def scored_path(run: dict[str, Any]) -> Path:
    return resolve_inventory_path(run["predictions_path"]).with_name("scored.jsonl")


def build_outcomes(inventory_path: Path) -> pd.DataFrame:
    models, runs = selected_runs(inventory_path)
    records = []
    for model in models:
        teaching = latest_scored(scored_path(runs[("longtutor_teaching", model)]))
        diagnosis = latest_scored(scored_path(runs[("longtutor_diagnosis", model)]))
        evidence = latest_scored(scored_path(runs[("longtutor_evidence", model)]))
        evidence_records = []
        for item_id, row in evidence.items():
            base_id = item_id.rsplit("::Q", 1)[0]
            evidence_records.append({
                "item_id": base_id,
                "memory_type": row.get("buckets", {}).get("memory_type", "unknown"),
                "correct": float(bool(row.get("correct"))),
            })
        evidence_frame = pd.DataFrame(evidence_records)
        evidence_mean = evidence_frame.groupby("item_id")["correct"].mean()
        evidence_count = evidence_frame.groupby("item_id").size()
        for item_id in sorted(set(teaching) & set(diagnosis) & set(evidence_mean.index)):
            normalized = teaching[item_id].get("normalized")
            if not isinstance(normalized, dict) or not all(isinstance(normalized.get(k), (int, float)) for k in TEACHING_DIMENSIONS):
                continue
            record = {
                "item_id": item_id, "model": model,
                "diagnosis_correct": float(bool(diagnosis[item_id].get("correct"))),
                "diagnosis_predicted": diagnosis[item_id].get("normalized"),
                "diagnosis_gold": diagnosis[item_id].get("gold"),
                "evidence_accuracy": float(evidence_mean[item_id]),
                "evidence_questions": int(evidence_count[item_id]),
            }
            for dimension in TEACHING_DIMENSIONS:
                record[dimension] = float(normalized[dimension])
            record["teaching_quality"] = float(np.mean([record[k] for k in TEACHING_DIMENSIONS]))
            records.append(record)
    return pd.DataFrame(records)


def model_summary(data: pd.DataFrame) -> pd.DataFrame:
    return data.groupby("model", as_index=False).agg(
        items=("item_id", "nunique"), diagnosis_accuracy=("diagnosis_correct", "mean"),
        evidence_accuracy=("evidence_accuracy", "mean"), teaching_quality=("teaching_quality", "mean"),
        history_utilization=("history_utilization", "mean"), strategy_alignment=("strategy_alignment", "mean"),
        coherence=("coherence", "mean"), appropriateness=("appropriateness", "mean"),
    )


def paired_associations(data: pd.DataFrame, reps: int, seed: int) -> pd.DataFrame:
    rows = []
    rng = np.random.default_rng(seed)
    for model, group in data.groupby("model"):
        for outcome in ("diagnosis_correct", "evidence_accuracy"):
            for teaching in ("teaching_quality", *TEACHING_DIMENSIONS):
                rho = spearmanr(group[outcome], group[teaching]).statistic
                x = group[outcome].to_numpy()
                y = group[teaching].to_numpy()
                boot = np.empty(reps)
                for i in range(reps):
                    chosen = rng.integers(0, len(group), size=len(group))
                    value = spearmanr(x[chosen], y[chosen]).statistic
                    boot[i] = value if np.isfinite(value) else 0
                rows.append({
                    "model": model, "objective_outcome": outcome, "teaching_measure": teaching,
                    "items": len(group), "spearman": float(rho),
                    "ci_low": float(np.quantile(boot, .025)), "ci_high": float(np.quantile(boot, .975)),
                })
    return pd.DataFrame(rows)


def heldout_model_prediction(data: pd.DataFrame) -> pd.DataFrame:
    rows = []
    predictors = {
        "item_only": [],
        "teaching_mean": ["teaching_quality"],
        "teaching_dimensions": list(TEACHING_DIMENSIONS),
    }
    for heldout in sorted(data["model"].unique()):
        train, test = data[data["model"] != heldout], data[data["model"] == heldout]
        for name, numeric in predictors.items():
            transformers = [("item", OneHotEncoder(handle_unknown="ignore"), ["item_id"])]
            if numeric:
                transformers.append(("numeric", StandardScaler(), numeric))
            prep = ColumnTransformer(transformers)
            diagnosis_model = make_pipeline(
                prep, LogisticRegression(max_iter=4000, class_weight="balanced", C=1.0)
            )
            diagnosis_model.fit(train, train["diagnosis_correct"])
            prob = diagnosis_model.predict_proba(test)[:, 1]
            rows.append({
                "held_out_model": heldout, "outcome": "diagnosis_correct", "predictors": name,
                "n_test": len(test), "auc": roc_auc_score(test["diagnosis_correct"], prob),
                "accuracy": accuracy_score(test["diagnosis_correct"], prob >= .5), "rmse": math.nan,
            })
            evidence_model = make_pipeline(prep, Ridge(alpha=10.0))
            evidence_model.fit(train, train["evidence_accuracy"])
            pred = np.clip(evidence_model.predict(test), 0, 1)
            rows.append({
                "held_out_model": heldout, "outcome": "evidence_accuracy", "predictors": name,
                "n_test": len(test), "auc": math.nan, "accuracy": math.nan,
                "rmse": math.sqrt(mean_squared_error(test["evidence_accuracy"], pred)),
            })
    return pd.DataFrame(rows)


def render_report(data: pd.DataFrame, summary: pd.DataFrame, associations: pd.DataFrame, prediction: pd.DataFrame) -> str:
    pred_summary = prediction.groupby(["outcome", "predictors"])[["auc", "accuracy", "rmse"]].mean().reset_index()
    assoc_summary = associations.groupby(["objective_outcome", "teaching_measure"])["spearman"].agg(["mean", "min", "max"]).reset_index()
    return "\n".join([
        "# LongTutor diagnosis and evidence cross-task validity", "",
        f"Matched records: **{len(data):,}** model × history observations, **{data['item_id'].nunique():,}** histories, **{data['model'].nunique()}** models. "
        "Diagnosis is an exact four-class human-gold outcome. Evidence accuracy aggregates reference-conditioned historical-memory questions; non-exact answers were judged for semantic equivalence by the same fixed MiniMax-M3 extractor across candidate models. Teaching scores come from the separate teaching task.", "",
        "## Model summaries", "", summary.to_markdown(index=False, floatfmt=".3f"), "",
        "Model means are descriptive only because there are six systems.", "",
        "## Within-model associations", "", assoc_summary.to_markdown(index=False, floatfmt=".3f"), "",
        "## Held-out-model prediction with exact-history controls", "", pred_summary.to_markdown(index=False, floatfmt=".3f"), "",
        "Each fold trains on five models and tests the sixth. The item-only baseline absorbs history difficulty; teaching measures test incremental cross-task association.", "",
        "## Interpretation boundary", "",
        "Human-gold diagnosis is a stronger external criterion than a prompted simulated student. Evidence accuracy is a secondary, reference-grounded but LLM-judged criterion. Both measure prerequisite tutor competence rather than student learning gain. "
        "A positive association does not show that any teaching style causes learning.", "",
    ])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--bootstrap-reps", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=20260819)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    data = build_outcomes(args.inventory)
    summary = model_summary(data)
    associations = paired_associations(data, args.bootstrap_reps, args.seed)
    prediction = heldout_model_prediction(data)
    data.to_csv(args.output_dir / "matched_objective_outcomes.csv", index=False)
    summary.to_csv(args.output_dir / "model_summary.csv", index=False)
    associations.to_csv(args.output_dir / "within_model_associations.csv", index=False)
    prediction.to_csv(args.output_dir / "heldout_model_prediction.csv", index=False)
    report = render_report(data, summary, associations, prediction)
    (args.output_dir / "longtutor_objective_validity_report.md").write_text(report, encoding="utf-8")
    print(args.output_dir / "longtutor_objective_validity_report.md")


if __name__ == "__main__":
    main()
