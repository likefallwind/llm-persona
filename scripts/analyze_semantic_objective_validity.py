#!/usr/bin/env python3
"""Exploratory link from semantic tutor behavior to LongTutor criterion tasks.

This analysis was added after the single-judge interim view and is intentionally
kept separate from the frozen confirmatory semantic-panel script.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import pearsonr
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import accuracy_score, mean_squared_error, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from run_semantic_judge import DIMENSIONS


def bh_adjust(values: pd.Series) -> pd.Series:
    p = values.to_numpy(float)
    order = np.argsort(p)
    ranked = p[order]
    adjusted = np.minimum.accumulate((ranked * len(p) / np.arange(1, len(p) + 1))[::-1])[::-1]
    output = np.empty(len(p)); output[order] = np.minimum(adjusted, 1)
    return pd.Series(output, index=values.index)


def matched_frame(consensus_path: Path, objective_path: Path) -> pd.DataFrame:
    semantic = pd.read_csv(consensus_path, dtype={"item_id": str})
    semantic = semantic[semantic["benchmark"] == "longtutor_teaching"]
    wide = semantic.pivot_table(
        index=["item_id", "model", "response_sha256"], columns="dimension", values="score"
    ).reset_index()
    objective = pd.read_csv(objective_path, dtype={"item_id": str})
    return wide.merge(objective, on=["item_id", "model"], how="inner", validate="one_to_one")


def heldout_prediction(data: pd.DataFrame) -> pd.DataFrame:
    sets = {
        "item_only": [],
        "diagnosis_personalization": ["diagnostic_specificity", "personalization"],
        "all_semantic": list(DIMENSIONS),
        "semantic_without_diagnosis_personalization": [
            dimension for dimension in DIMENSIONS
            if dimension not in {"diagnostic_specificity", "personalization"}
        ],
    }
    rows = []
    for heldout in sorted(data["model"].unique()):
        train, test = data[data["model"] != heldout], data[data["model"] == heldout]
        for name, numeric in sets.items():
            transformers = [("item", OneHotEncoder(handle_unknown="ignore"), ["item_id"])]
            if numeric:
                transformers.append(("semantic", StandardScaler(), numeric))
            prep = ColumnTransformer(transformers)
            classifier = make_pipeline(prep, LogisticRegression(max_iter=4000, class_weight="balanced"))
            classifier.fit(train, train["diagnosis_correct"])
            prob = classifier.predict_proba(test)[:, 1]
            rows.append({
                "held_out_model": heldout, "outcome": "diagnosis_correct", "feature_set": name,
                "n_test": len(test), "auc": roc_auc_score(test["diagnosis_correct"], prob),
                "accuracy": accuracy_score(test["diagnosis_correct"], prob >= .5), "rmse": math.nan,
            })
            regressor = make_pipeline(prep, Ridge(alpha=10.0))
            regressor.fit(train, train["evidence_accuracy"])
            pred = np.clip(regressor.predict(test), 0, 1)
            rows.append({
                "held_out_model": heldout, "outcome": "evidence_accuracy", "feature_set": name,
                "n_test": len(test), "auc": math.nan, "accuracy": math.nan,
                "rmse": math.sqrt(mean_squared_error(test["evidence_accuracy"], pred)),
            })
    result = pd.DataFrame(rows)
    baseline = result[result["feature_set"] == "item_only"].set_index(["held_out_model", "outcome"])
    result["gain_vs_item"] = result.apply(
        lambda row: (
            row["auc"] - baseline.loc[(row["held_out_model"], row["outcome"]), "auc"]
            if row["outcome"] == "diagnosis_correct"
            else baseline.loc[(row["held_out_model"], row["outcome"]), "rmse"] - row["rmse"]
        ), axis=1,
    )
    return result


def fixed_item_permutation(data: pd.DataFrame, reps: int, seed: int) -> pd.DataFrame:
    centered = data.copy()
    for column in [*DIMENSIONS, "diagnosis_correct", "evidence_accuracy"]:
        centered[column] -= centered.groupby("item_id")[column].transform("mean")
    rng = np.random.default_rng(seed)
    item_indices = [group.index.to_numpy() for _, group in centered.groupby("item_id")]
    rows = []
    for outcome in ("diagnosis_correct", "evidence_accuracy"):
        y = centered[outcome].to_numpy()
        for dimension in DIMENSIONS:
            x = centered[dimension].to_numpy()
            observed = float(pearsonr(x, y).statistic) if np.std(x) and np.std(y) else math.nan
            null = np.empty(reps)
            for i in range(reps):
                permuted = x.copy()
                for indices in item_indices:
                    permuted[indices] = rng.permutation(permuted[indices])
                null[i] = pearsonr(permuted, y).statistic if np.std(permuted) and np.std(y) else 0
            p = float((1 + np.sum(np.abs(null) >= abs(observed))) / (reps + 1)) if np.isfinite(observed) else 1.0
            rows.append({
                "outcome": outcome, "dimension": dimension, "matched_responses": len(centered),
                "exact_item_centered_pearson": observed, "permutation_p": p, "permutations": reps,
            })
    result = pd.DataFrame(rows)
    result["bh_q_within_outcome"] = result.groupby("outcome", group_keys=False)["permutation_p"].apply(bh_adjust)
    return result


def render_report(data: pd.DataFrame, prediction: pd.DataFrame, associations: pd.DataFrame) -> str:
    summary = prediction.groupby(["outcome", "feature_set"])[["auc", "accuracy", "rmse", "gain_vs_item"]].mean().reset_index()
    return "\n".join([
        "# Semantic-to-LongTutor criterion validity (exploratory)", "",
        f"Matched **{len(data):,}** response-level observations: **{data['item_id'].nunique()}** histories × **{data['model'].nunique()}** models. "
        "Semantic scores describe a teaching response. Diagnosis correctness is exact match to a human-gold class. Historical-evidence accuracy comes from separate model calls and reference answers, with non-exact equivalence scored by a fixed MiniMax-M3 judge.", "",
        "This analysis was designed after the MiniMax-only interim view and is not part of the prospective multi-judge analysis freeze.", "",
        "## Held-out-model prediction with exact-history controls", "", summary.to_markdown(index=False, floatfmt=".3f"), "",
        "For diagnosis, positive gain is AUC improvement over item-only. For evidence, positive gain is RMSE reduction. Every model fold is retained in the CSV.", "",
        "## Exact-history-centered associations", "", associations.to_markdown(index=False, floatfmt=".3f"), "",
        "Permutation tests shuffle model-linked semantic scores within each history and use BH correction across the eight dimensions for each objective outcome.", "",
        "## Interpretation boundary", "",
        "Diagnosis is an external prerequisite-competence test, not student learning gain; evidence accuracy remains LLM-judged. Failure is informative: a reliable behavioral disposition may still be disconnected from accurate learner-state inference.", "",
    ])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--semantic-consensus", type=Path, required=True)
    parser.add_argument("--objective-outcomes", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--permutations", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=20260819)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    data = matched_frame(args.semantic_consensus, args.objective_outcomes)
    if len(data) != 240:
        raise SystemExit(f"expected 240 matched responses (40 histories x 6 models), found {len(data)}")
    prediction = heldout_prediction(data)
    associations = fixed_item_permutation(data, args.permutations, args.seed)
    data.to_csv(args.output_dir / "matched_semantic_objective.csv", index=False)
    prediction.to_csv(args.output_dir / "heldout_model_objective_prediction.csv", index=False)
    associations.to_csv(args.output_dir / "fixed_item_associations.csv", index=False)
    report = render_report(data, prediction, associations)
    (args.output_dir / "semantic_objective_validity_report.md").write_text(report, encoding="utf-8")
    print(args.output_dir / "semantic_objective_validity_report.md")


if __name__ == "__main__":
    main()
