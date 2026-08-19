#!/usr/bin/env python3
"""Test whether transparent 'pedagogical' proxies are actually domain-general fingerprints."""

from __future__ import annotations

import argparse
import itertools
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from run_behavioral_pilot import ALL_FEATURES, POLICY_FEATURES, SURFACE_FEATURES


def residualize(frame: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    result = frame.copy()
    for feature in features:
        result[feature] -= result.groupby(["benchmark", "item_id"])[feature].transform("mean")
        sd = result.groupby("benchmark")[feature].transform("std").replace(0, np.nan)
        result[feature] = (result[feature] / sd).fillna(0.0)
    return result


def balanced_sample(frame: pd.DataFrame, seed: int = 20260819) -> pd.DataFrame:
    target = int(frame.groupby(["benchmark", "model"]).size().min())
    parts = [
        group.sample(n=target, random_state=seed)
        for _, group in frame.groupby(["benchmark", "model"], sort=True)
    ]
    return pd.concat(parts, ignore_index=True)


def cross_domain_attribution(teaching: pd.DataFrame, negative: pd.DataFrame) -> pd.DataFrame:
    feature_sets = {
        "length_only": ["log_chars", "log_tokens"],
        "surface": SURFACE_FEATURES,
        "policy": POLICY_FEATURES,
        "surface_plus_policy": ALL_FEATURES,
    }
    teaching_sample = balanced_sample(teaching)
    negative_sample = balanced_sample(negative)
    rows = []
    for train_name, train, test_name, test in (
        ("teaching", teaching_sample, "negative_control", negative_sample),
        ("negative_control", negative_sample, "teaching", teaching_sample),
    ):
        for set_name, features in feature_sets.items():
            clf = make_pipeline(
                StandardScaler(),
                LogisticRegression(max_iter=4000, class_weight="balanced", C=1.0),
            )
            clf.fit(train[features], train["model"])
            pred = clf.predict(test[features])
            rows.append({
                "train_domain": train_name,
                "test_domain": test_name,
                "feature_set": set_name,
                "n_train": len(train),
                "n_test": len(test),
                "accuracy": accuracy_score(test["model"], pred),
                "balanced_accuracy": balanced_accuracy_score(test["model"], pred),
            })
    return pd.DataFrame(rows)


def model_profiles(frame: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    task_profile = frame.groupby(["model", "benchmark"])[features].mean().reset_index()
    return task_profile.groupby("model")[features].mean()


def exact_spearman_p(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    observed = float(spearmanr(x, y).statistic)
    null = []
    for perm in itertools.permutations(range(len(y))):
        null.append(float(spearmanr(x, y[list(perm)]).statistic))
    null_array = np.asarray([z for z in null if np.isfinite(z)])
    p = (1 + np.sum(np.abs(null_array) >= abs(observed))) / (1 + len(null_array))
    return observed, float(p)


def feature_correlations(teaching_profile: pd.DataFrame, negative_profile: pd.DataFrame) -> pd.DataFrame:
    common = sorted(set(teaching_profile.index) & set(negative_profile.index))
    rows = []
    for feature in ALL_FEATURES:
        x = teaching_profile.loc[common, feature].to_numpy()
        y = negative_profile.loc[common, feature].to_numpy()
        if np.std(x) == 0 or np.std(y) == 0:
            rho, p = np.nan, np.nan
        else:
            rho, p = exact_spearman_p(x, y)
        rows.append({"feature": feature, "cross_domain_spearman": rho, "exact_two_sided_p": p})
    return pd.DataFrame(rows).sort_values("cross_domain_spearman", ascending=False)


def distance_matrix(profile: pd.DataFrame, features: list[str], models: list[str]) -> np.ndarray:
    values = profile.loc[models, features].to_numpy()
    matrix = np.zeros((len(models), len(models)))
    for i, j in itertools.combinations(range(len(models)), 2):
        matrix[i, j] = matrix[j, i] = np.linalg.norm(values[i] - values[j])
    return matrix


def mantel_exact(teaching_profile: pd.DataFrame, negative_profile: pd.DataFrame, features: list[str]) -> dict[str, float]:
    models = sorted(set(teaching_profile.index) & set(negative_profile.index))
    a = distance_matrix(teaching_profile, features, models)
    b = distance_matrix(negative_profile, features, models)
    upper = np.triu_indices(len(models), 1)
    observed = float(np.corrcoef(a[upper], b[upper])[0, 1])
    null = []
    for perm in itertools.permutations(range(len(models))):
        bp = b[np.ix_(perm, perm)]
        null.append(float(np.corrcoef(a[upper], bp[upper])[0, 1]))
    null_array = np.asarray(null)
    p = (1 + np.sum(np.abs(null_array) >= abs(observed))) / (1 + len(null_array))
    return {
        "feature_set": "policy",
        "model_count": len(models),
        "distance_matrix_correlation": observed,
        "exact_two_sided_p": float(p),
        "permutations": len(null),
    }


def render_report(
    teaching: pd.DataFrame, negative: pd.DataFrame, attribution: pd.DataFrame,
    correlations: pd.DataFrame, mantel: dict[str, float],
) -> str:
    return "\n".join([
        "# Discriminant-validity negative control",
        "",
        f"Teaching responses: **{len(teaching):,}**. Negative-control responses: **{len(negative):,}**. Models: **{teaching['model'].nunique()}**.",
        "",
        "All features were centered within item across models and standardized within benchmark before this analysis. This removes shared item content and benchmark scale.",
        "",
        "## Cross-domain model attribution",
        "",
        attribution.to_markdown(index=False, floatfmt=".3f"),
        "",
        "Chance accuracy is 0.167. Above-chance transfer means a feature set contains model-specific information that is not unique to tutoring.",
        "",
        "## Cross-domain feature ranks",
        "",
        correlations.head(12).to_markdown(index=False, floatfmt=".3f"),
        "",
        "## Policy-profile geometry",
        "",
        pd.DataFrame([mantel]).to_markdown(index=False, floatfmt=".3f"),
        "",
        "## Consequence",
        "",
        "Any proxy that transfers strongly to test-taking or generic instruction following must be labeled a domain-general model fingerprint, not a pedagogical disposition. Confirmatory semantic dimensions must demonstrate incremental validity after controlling these negative-domain profiles.",
        "",
    ])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--teaching", type=Path, required=True)
    parser.add_argument("--negative", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    teaching = residualize(pd.read_csv(args.teaching, dtype={"item_id": str}), ALL_FEATURES)
    negative = residualize(pd.read_csv(args.negative, dtype={"item_id": str}), ALL_FEATURES)
    attribution = cross_domain_attribution(teaching, negative)
    teaching_profile = model_profiles(teaching, ALL_FEATURES)
    negative_profile = model_profiles(negative, ALL_FEATURES)
    correlations = feature_correlations(teaching_profile, negative_profile)
    mantel = mantel_exact(teaching_profile, negative_profile, POLICY_FEATURES)

    attribution.to_csv(args.output_dir / "cross_domain_attribution.csv", index=False)
    correlations.to_csv(args.output_dir / "feature_cross_domain_correlations.csv", index=False)
    pd.DataFrame([mantel]).to_csv(args.output_dir / "policy_geometry_mantel.csv", index=False)
    teaching_profile.reset_index().to_csv(args.output_dir / "teaching_profiles.csv", index=False)
    negative_profile.reset_index().to_csv(args.output_dir / "negative_profiles.csv", index=False)
    report = render_report(teaching, negative, attribution, correlations, mantel)
    (args.output_dir / "discriminant_validity_report.md").write_text(report, encoding="utf-8")
    print(args.output_dir / "discriminant_validity_report.md")


if __name__ == "__main__":
    main()
