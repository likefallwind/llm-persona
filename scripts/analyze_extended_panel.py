#!/usr/bin/env python3
"""Analyze family resemblance and prompt-response heterogeneity in nine models."""

from __future__ import annotations

import argparse
import itertools
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/llm-persona-matplotlib")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from run_behavioral_pilot import POLICY_FEATURES


FAMILY_PAIRS = {
    "deepseek": ("deepseek-v4-flash", "deepseek-v4-pro"),
    "doubao": ("doubao-seed-2.0-lite", "doubao-seed-2.0-pro"),
    "minimax": ("minimax-m2.7", "minimax-m3"),
    "qwen": ("qwen3.5-4b", "qwen3.8-27b"),
}

FOCAL_FEATURES = [
    "question_rate",
    "answer_reveal_rate",
    "praise_rate",
    "imperative_rate",
    "first_plural_rate",
    "hedge_rate",
    "explanation_rate",
    "diagnosis_rate",
    "log_tokens",
]


def add_arm_and_pair(frame: pd.DataFrame) -> pd.DataFrame:
    data = frame.copy()
    data["arm"] = np.where(data["prompt_arm"] == "explicit_learnlm_pedagogy", "pedagogy", "generic")
    data["pair_id"] = data["item_id"].str.extract(r"(\d+)$", expand=False)
    return data


def centered_profiles(data: pd.DataFrame, features: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    centered = data.copy()
    for feature in features:
        centered[feature] -= centered.groupby(["family", "pair_id", "arm"])[feature].transform("mean")
        sd = centered[feature].std(ddof=0)
        centered[feature] = centered[feature] / sd if sd else 0.0
    profiles = centered.groupby(["arm", "model"])[features].mean().reset_index()
    return centered, profiles


def pairwise_distances(profile: pd.DataFrame, features: list[str], label: str) -> pd.DataFrame:
    indexed = profile.set_index("model")[features]
    rows = []
    for left, right in itertools.combinations(sorted(indexed.index), 2):
        distance = float(np.linalg.norm(indexed.loc[left].to_numpy() - indexed.loc[right].to_numpy()))
        family = next((name for name, pair in FAMILY_PAIRS.items() if {left, right} == set(pair)), None)
        rows.append({
            "profile": label,
            "model_a": left,
            "model_b": right,
            "distance": distance,
            "within_named_family": family is not None,
            "family": family,
        })
    return pd.DataFrame(rows)


def matching_permutation_test(profile: pd.DataFrame, features: list[str], seed: int = 20260819, reps: int = 50000) -> dict[str, float]:
    indexed = profile.set_index("model")[features]
    models = sorted(indexed.index)
    observed = np.mean([
        np.linalg.norm(indexed.loc[a].to_numpy() - indexed.loc[b].to_numpy())
        for a, b in FAMILY_PAIRS.values()
    ])
    rng = np.random.default_rng(seed)
    null = np.empty(reps)
    for i in range(reps):
        chosen = list(rng.choice(models, size=8, replace=False))
        rng.shuffle(chosen)
        distances = []
        for j in range(0, 8, 2):
            distances.append(np.linalg.norm(indexed.loc[chosen[j]].to_numpy() - indexed.loc[chosen[j + 1]].to_numpy()))
        null[i] = np.mean(distances)
    return {
        "observed_family_pair_distance": float(observed),
        "null_mean_distance": float(null.mean()),
        "lower_tail_p": float((1 + np.sum(null <= observed)) / (reps + 1)),
        "permutations": reps,
    }


def treatment_profiles(data: pd.DataFrame, features: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    keys = ["family", "pair_id", "model"]
    deltas = []
    for feature in features:
        wide = data.pivot_table(index=keys, columns="arm", values=feature, aggfunc="last").dropna()
        delta = (wide["pedagogy"] - wide["generic"]).rename(feature)
        deltas.append(delta)
    delta_frame = pd.concat(deltas, axis=1).reset_index()
    for feature in features:
        sd = delta_frame[feature].std(ddof=0)
        if sd:
            delta_frame[feature] /= sd
    profile = delta_frame.groupby("model")[features].mean().reset_index()
    return delta_frame, profile


def mean_pairwise_distance(profile: pd.DataFrame, features: list[str]) -> float:
    values = profile.set_index("model")[features]
    distances = [
        np.linalg.norm(values.loc[a].to_numpy() - values.loc[b].to_numpy())
        for a, b in itertools.combinations(values.index, 2)
    ]
    return float(np.mean(distances))


def bootstrap_dispersion(centered: pd.DataFrame, features: list[str], reps: int = 3000) -> pd.DataFrame:
    rng = np.random.default_rng(20260819)
    families = sorted(centered["family"].unique())
    models = sorted(centered["model"].unique())
    results = []
    observed: dict[str, float] = {}
    for arm in ("generic", "pedagogy"):
        profile = centered[centered["arm"] == arm].groupby("model")[features].mean().reset_index()
        observed[arm] = mean_pairwise_distance(profile, features)
    arrays: dict[tuple[str, str], np.ndarray] = {}
    for family in families:
        family_rows = centered[centered["family"] == family]
        for arm in ("generic", "pedagogy"):
            arm_rows = family_rows[family_rows["arm"] == arm]
            blocks = []
            for feature in features:
                pivot = arm_rows.pivot_table(index="pair_id", columns="model", values=feature, aggfunc="last")
                blocks.append(pivot.reindex(columns=models).to_numpy())
            arrays[(family, arm)] = np.stack(blocks, axis=2)

    def array_dispersion(values: np.ndarray) -> float:
        pair_distances = [
            np.linalg.norm(values[i] - values[j])
            for i, j in itertools.combinations(range(len(models)), 2)
        ]
        return float(np.mean(pair_distances))

    ratios = []
    for _ in range(reps):
        totals = {"generic": np.zeros((len(models), len(features))), "pedagogy": np.zeros((len(models), len(features)))}
        total_n = 0
        for family in families:
            n_items = arrays[(family, "generic")].shape[0]
            indices = rng.integers(0, n_items, size=n_items)
            total_n += n_items
            for arm in ("generic", "pedagogy"):
                totals[arm] += arrays[(family, arm)][indices].sum(axis=0)
        arm_dist: dict[str, float] = {}
        for arm in ("generic", "pedagogy"):
            arm_dist[arm] = array_dispersion(totals[arm] / total_n)
        ratios.append(arm_dist["pedagogy"] / arm_dist["generic"])
    ratios_arr = np.asarray(ratios)
    results.append({
        "generic_dispersion": observed["generic"],
        "pedagogy_dispersion": observed["pedagogy"],
        "dispersion_ratio_pedagogy_over_generic": observed["pedagogy"] / observed["generic"],
        "bootstrap_ci_low": float(np.quantile(ratios_arr, 0.025)),
        "bootstrap_ci_high": float(np.quantile(ratios_arr, 0.975)),
        "probability_ratio_below_one": float(np.mean(ratios_arr < 1)),
    })
    return pd.DataFrame(results)


def directional_invariants(data: pd.DataFrame) -> pd.DataFrame:
    rows = []
    keys = ["family", "pair_id", "model"]
    for feature in FOCAL_FEATURES:
        wide = data.pivot_table(index=keys, columns="arm", values=feature, aggfunc="last").dropna()
        wide["delta"] = wide["pedagogy"] - wide["generic"]
        effects = wide.groupby(["family", "model"])["delta"].mean().reset_index()
        for family, family_rows in effects.groupby("family"):
            rows.append({
                "family": family,
                "feature": feature,
                "models_positive": int((family_rows["delta"] > 0).sum()),
                "models_negative": int((family_rows["delta"] < 0).sum()),
                "models_zero": int((family_rows["delta"] == 0).sum()),
                "model_count": len(family_rows),
                "min_model_mean_delta": float(family_rows["delta"].min()),
                "max_model_mean_delta": float(family_rows["delta"].max()),
            })
    return pd.DataFrame(rows)


def save_figures(output_dir: Path, profiles: pd.DataFrame, distances: pd.DataFrame, treatment: pd.DataFrame) -> None:
    sns.set_theme(style="whitegrid")
    generic = profiles[profiles["arm"] == "generic"].set_index("model")[FOCAL_FEATURES]
    fig, ax = plt.subplots(figsize=(11, 5))
    sns.heatmap(generic, center=0, cmap="vlag", ax=ax)
    ax.set_title("Generic-prompt model profiles after within-item centering")
    fig.tight_layout()
    fig.savefig(output_dir / "generic_profiles.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 4))
    sns.boxplot(distances, x="profile", y="distance", hue="within_named_family", ax=ax)
    ax.set_title("Named-family vs other pair distances")
    fig.tight_layout()
    fig.savefig(output_dir / "family_pair_distances.png", dpi=180)
    plt.close(fig)

    treatment_heat = treatment.set_index("model")[FOCAL_FEATURES]
    fig, ax = plt.subplots(figsize=(11, 5))
    sns.heatmap(treatment_heat, center=0, cmap="vlag", ax=ax)
    ax.set_title("Model-specific response to the explicit pedagogy prompt")
    fig.tight_layout()
    fig.savefig(output_dir / "treatment_profiles.png", dpi=180)
    plt.close(fig)


def render_report(
    data: pd.DataFrame, family_tests: pd.DataFrame, dispersion: pd.DataFrame,
    invariants: pd.DataFrame, distances: pd.DataFrame,
) -> str:
    focal_invariants = invariants[invariants["feature"].isin(["question_rate", "log_tokens", "praise_rate", "answer_reveal_rate"])]
    family_distance_summary = distances.groupby(["profile", "within_named_family"])["distance"].agg(["mean", "median", "count"]).reset_index()
    return "\n".join([
        "# Extended nine-model panel",
        "",
        f"Responses: **{len(data):,}**; models: **{data['model'].nunique()}**; paired prompt arms: **{data['benchmark'].nunique()}**.",
        "",
        "## Does behavior resemble model family?",
        "",
        family_tests.to_markdown(index=False, floatfmt=".4f"),
        "",
        family_distance_summary.to_markdown(index=False, floatfmt=".4f"),
        "",
        "The four named pairs are approximate family comparisons, not clean scaling experiments: model generation, training, and serving differ within every pair.",
        "",
        "## Does the explicit pedagogy prompt make models converge?",
        "",
        dispersion.to_markdown(index=False, floatfmt=".4f"),
        "",
        "Dispersion is the mean Euclidean distance between model profiles after within-item centering and feature standardization. A ratio below one means convergence.",
        "",
        "## Directional invariants and heterogeneity",
        "",
        focal_invariants.to_markdown(index=False, floatfmt=".4f"),
        "",
        "A universal sign across all nine models is stronger evidence of a prompt-level policy effect. Mixed signs reveal model-specific adaptation rather than simple compliance strength.",
        "",
        "## Interpretation",
        "",
        "The extended panel can separate three phenomena: persistent baseline signature, common response to an explicit pedagogical constraint, and model-specific treatment response. None alone licenses a human-personality claim.",
        "",
    ])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--features", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    data = add_arm_and_pair(pd.read_csv(args.features))
    centered, profiles = centered_profiles(data, FOCAL_FEATURES)
    distance_frames = []
    tests = []
    for arm in ("generic", "pedagogy"):
        profile = profiles[profiles["arm"] == arm].drop(columns="arm")
        distance_frames.append(pairwise_distances(profile, FOCAL_FEATURES, arm))
        tests.append({"profile": arm, **matching_permutation_test(profile, FOCAL_FEATURES)})
    delta_frame, treatment = treatment_profiles(data, FOCAL_FEATURES)
    distance_frames.append(pairwise_distances(treatment, FOCAL_FEATURES, "treatment_delta"))
    tests.append({"profile": "treatment_delta", **matching_permutation_test(treatment, FOCAL_FEATURES, seed=20260820)})
    distances = pd.concat(distance_frames, ignore_index=True)
    family_tests = pd.DataFrame(tests)
    dispersion = bootstrap_dispersion(centered, FOCAL_FEATURES)
    invariants = directional_invariants(data)

    profiles.to_csv(args.output_dir / "model_profiles.csv", index=False)
    treatment.to_csv(args.output_dir / "treatment_profiles.csv", index=False)
    delta_frame.to_csv(args.output_dir / "item_treatment_deltas.csv", index=False)
    distances.to_csv(args.output_dir / "model_pair_distances.csv", index=False)
    family_tests.to_csv(args.output_dir / "family_permutation_tests.csv", index=False)
    dispersion.to_csv(args.output_dir / "prompt_convergence.csv", index=False)
    invariants.to_csv(args.output_dir / "directional_invariants.csv", index=False)
    save_figures(args.output_dir, profiles, distances, treatment)
    report = render_report(data, family_tests, dispersion, invariants, distances)
    (args.output_dir / "extended_panel_report.md").write_text(report, encoding="utf-8")
    print(args.output_dir / "extended_panel_report.md")


if __name__ == "__main__":
    main()
