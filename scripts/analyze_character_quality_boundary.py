#!/usr/bin/env python3
"""Descriptive quality association for confirmatory character dimensions."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, brier_score_loss, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from run_behavioral_pilot import ALL_FEATURES


def analyze(consensus: pd.DataFrame, features: pd.DataFrame) -> pd.DataFrame:
    dimensions = sorted(consensus["dimension"].unique())
    wide = consensus.pivot_table(
        index=["benchmark", "item_id", "model", "response_sha256"],
        columns="dimension", values="score",
    ).reset_index()
    data = features.merge(
        wide, on=["benchmark", "item_id", "model", "response_sha256"], how="inner"
    )
    data = data[data["benchmark"].str.startswith("mathtutorbench_")].dropna(
        subset=["outcome_primary"]
    )
    data["quality_binary"] = (data["outcome_primary"] > .5).astype(int)
    feature_sets = {
        "task_item_only": [],
        "transparent_only": list(ALL_FEATURES),
        "transparent_plus_all_confirmatory": list(ALL_FEATURES) + dimensions,
    }
    feature_sets.update({
        f"transparent_plus_{dimension}": list(ALL_FEATURES) + [dimension]
        for dimension in dimensions
    })
    rows = []
    for heldout in sorted(data["model"].unique()):
        train = data[data["model"] != heldout]
        test = data[data["model"] == heldout]
        if train["quality_binary"].nunique() < 2 or test["quality_binary"].nunique() < 2:
            continue
        for name, numeric in feature_sets.items():
            transformers = [
                ("item", OneHotEncoder(handle_unknown="ignore"), ["benchmark", "item_id"])
            ]
            if numeric:
                transformers.append(("numeric", StandardScaler(), numeric))
            model = make_pipeline(
                ColumnTransformer(transformers),
                LogisticRegression(max_iter=4000, class_weight="balanced", C=1.0),
            )
            model.fit(train, train["quality_binary"])
            probability = model.predict_proba(test)[:, 1]
            prediction = (probability >= .5).astype(int)
            rows.append({
                "held_out_model": heldout,
                "feature_set": name,
                "n_test": len(test),
                "auc": roc_auc_score(test["quality_binary"], probability),
                "brier": brier_score_loss(test["quality_binary"], probability),
                "accuracy": accuracy_score(test["quality_binary"], prediction),
            })
    result = pd.DataFrame(rows)
    if len(result):
        baseline = result[result["feature_set"] == "transparent_only"].set_index(
            "held_out_model"
        )["auc"]
        result["auc_gain_vs_transparent"] = result.apply(
            lambda row: row["auc"] - baseline.get(row["held_out_model"], math.nan), axis=1
        )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--consensus", type=Path, required=True)
    parser.add_argument(
        "--features", type=Path, default=Path("artifacts/pilot/behavior_features.csv")
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    result = analyze(
        pd.read_csv(args.consensus, dtype={"item_id": str}),
        pd.read_csv(args.features, dtype={"item_id": str}, low_memory=False),
    )
    summary = result.groupby("feature_set", as_index=False).agg(
        mean_auc=("auc", "mean"),
        mean_auc_gain_vs_transparent=("auc_gain_vs_transparent", "mean"),
        positive_model_folds=("auc_gain_vs_transparent", lambda values: int((values > 0).sum())),
        model_folds=("held_out_model", "nunique"),
    ) if len(result) else pd.DataFrame()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.output_dir / "quality_heldout_model.csv", index=False)
    summary.to_csv(args.output_dir / "quality_summary.csv", index=False)
    decision = {
        "status": "descriptive_external_quality_association",
        "rows": len(result),
        "boundary": (
            "Existing benchmark quality is a judged response outcome, not learner gain. "
            "Association cannot upgrade a dimension that fails measurement, cross-task, "
            "nonredundancy, or judge-family gates."
        ),
    }
    (args.output_dir / "quality_boundary.json").write_text(
        json.dumps(decision, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(decision, ensure_ascii=False))


if __name__ == "__main__":
    main()
