#!/usr/bin/env python3
"""Build the manuscript overview figure from registered derived tables."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/llm-persona-matplotlib")

import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import numpy as np
import pandas as pd


COLORS = {"blue": "#0072B2", "orange": "#E69F00", "green": "#009E73", "red": "#D55E00"}


def make_semantic_figure(root: Path, output: Path) -> None:
    decision_path = root / "artifacts/submission_decision/dimension_decisions.csv"
    effects_path = root / "artifacts/semantic_panel/prompt_effects.csv"
    attribution_path = root / "artifacts/semantic_panel/heldout_task_model_attribution.csv"
    if not all(path.is_file() for path in (decision_path, effects_path, attribution_path)):
        return

    decisions = pd.read_csv(decision_path)
    effects = pd.read_csv(effects_path)
    attribution = pd.read_csv(attribution_path)
    short_names = {
        "help_directness": "Help directness",
        "elicitation": "Elicitation",
        "autonomy_support": "Autonomy support",
        "affective_warmth": "Warmth",
        "diagnostic_specificity": "Diagnosis",
        "personalization": "Personalization",
        "cognitive_load": "Cognitive load",
        "epistemic_caution": "Epistemic caution",
    }

    fig, axes = plt.subplots(1, 3, figsize=(11.0, 3.8), constrained_layout=True)
    ax = axes[0]
    gate_columns = [
        "reliable_semantic_measurement",
        "cross_task_semantic_signature",
        "validated_pedagogical_disposition",
    ]
    matrix = decisions[gate_columns].astype(int).to_numpy()
    ax.imshow(matrix, aspect="auto", vmin=0, vmax=1, cmap=ListedColormap(["#E5E5E5", COLORS["green"]]))
    for row in range(matrix.shape[0]):
        for column in range(matrix.shape[1]):
            ax.text(column, row, "pass" if matrix[row, column] else "—", ha="center", va="center", fontsize=8)
    ax.set_xticks(range(3), ["Reliable", "Signature", "Disposition"], rotation=18, ha="right")
    ax.set_yticks(range(len(decisions)), [short_names[name] for name in decisions["dimension"]])
    ax.set_title("A  Frozen decision ladder", loc="left", fontweight="bold")
    ax.tick_params(length=0)

    ax = axes[1]
    selected = ["help_directness", "elicitation", "cognitive_load"]
    summary = effects.groupby(["task", "dimension"])["mean_delta"].mean().unstack("task")
    summary = summary.reindex(selected)
    tasks = ["mathdial_standard", "mathdial_hard"]
    x = np.arange(len(selected)); width = .36
    ax.bar(x - width / 2, summary[tasks[0]], width, color=COLORS["blue"], label="Standard")
    ax.bar(x + width / 2, summary[tasks[1]], width, color=COLORS["orange"], label="Hard")
    ax.axhline(0, color="0.3", linewidth=.8)
    ax.set_xticks(x, [short_names[name] for name in selected], rotation=18, ha="right")
    ax.set_ylabel("Pedagogy minus generic score")
    ax.set_title("B  Prompt intervention", loc="left", fontweight="bold")
    ax.legend(frameon=False, ncol=2, loc="upper right")

    ax = axes[2]
    feature_order = ["length_only", "semantic", "transparent", "transparent_plus_semantic"]
    labels = ["Length", "Semantic", "Transparent", "Combined"]
    values = attribution.groupby("feature_set")["accuracy"].mean().reindex(feature_order)
    colors = ["#999999", COLORS["green"], COLORS["blue"], COLORS["orange"]]
    ax.bar(range(len(values)), values, color=colors, width=.68)
    ax.axhline(1 / 6, color="0.35", linestyle="--", linewidth=1, label="Chance")
    ax.set_xticks(range(len(values)), labels, rotation=18, ha="right")
    ax.set_ylabel("Held-out-task model accuracy")
    ax.set_ylim(0, max(values.max() * 1.18, .45))
    ax.set_title("C  Semantic signal transports", loc="left", fontweight="bold")
    ax.legend(frameon=False, loc="upper left")

    for axis in axes[1:]:
        axis.spines[["top", "right"]].set_visible(False)
        axis.grid(axis="y", color="0.9", linewidth=.6, zorder=0)
        axis.set_axisbelow(True)

    fig.savefig(output / "semantic_findings.png", dpi=300, bbox_inches="tight")
    fig.savefig(
        output / "semantic_findings.pdf", bbox_inches="tight",
        metadata={"CreationDate": None, "ModDate": None},
    )
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output-dir", type=Path, default=Path("paper/figures"))
    args = parser.parse_args()
    root = args.root.resolve()
    output = args.output_dir if args.output_dir.is_absolute() else root / args.output_dir
    output.mkdir(parents=True, exist_ok=True)

    teaching = pd.read_csv(root / "artifacts/pilot/classification.csv")
    negative = pd.read_csv(root / "artifacts/negative_controls/classification.csv")
    convergence = pd.read_csv(root / "artifacts/extended_analysis/prompt_convergence.csv").iloc[0]
    actions = pd.read_csv(root / "artifacts/dialogue_act_validity/match_by_target_act.csv")
    longtutor = pd.read_csv(root / "artifacts/longtutor_objective_validity/heldout_model_prediction.csv")

    plt.rcParams.update({
        "font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9,
        "legend.fontsize": 8, "figure.dpi": 160,
    })
    fig, axes = plt.subplots(2, 2, figsize=(8.0, 5.8), constrained_layout=True)

    ax = axes[0, 0]
    feature_order = ["length_only", "surface", "policy", "surface_plus_policy"]
    labels = ["Length", "Surface", "Policy", "All"]
    teach_mean = teaching.groupby("feature_set")["accuracy"].mean().reindex(feature_order)
    neg_mean = negative.groupby("feature_set")["accuracy"].mean().reindex(feature_order)
    x = np.arange(len(feature_order)); width = .36
    ax.bar(x - width / 2, teach_mean, width, label="Teaching", color=COLORS["blue"])
    ax.bar(x + width / 2, neg_mean, width, label="Generic control", color=COLORS["orange"])
    ax.axhline(1 / 6, color="0.35", linestyle="--", linewidth=1, label="Chance")
    ax.set_xticks(x, labels); ax.set_ylabel("Held-out-family accuracy")
    ax.set_ylim(0, max(neg_mean.max(), teach_mean.max()) * 1.25)
    ax.set_title("A  Attribution is not construct validity", loc="left", fontweight="bold")
    ax.legend(frameon=False, ncol=2, loc="upper left")

    ax = axes[0, 1]
    values = [convergence["generic_dispersion"], convergence["pedagogy_dispersion"]]
    ax.bar([0, 1], values, color=[COLORS["blue"], COLORS["green"]], width=.58)
    ax.set_xticks([0, 1], ["Generic", "Pedagogy"])
    ax.set_ylabel("Cross-model policy dispersion")
    ratio = convergence["dispersion_ratio_pedagogy_over_generic"]
    low, high = convergence["bootstrap_ci_low"], convergence["bootstrap_ci_high"]
    ax.text(.5, max(values) * .91, f"ratio = {ratio:.3f}\n95% CI [{low:.3f}, {high:.3f}]", ha="center", va="top")
    ax.set_ylim(0, max(values) * 1.18)
    ax.set_title("B  Shared prompting homogenizes policy", loc="left", fontweight="bold")

    ax = axes[1, 0]
    telling = actions[(actions["family"] == "standard") & (actions["target_act"] == "telling")]
    summary = telling.groupby("arm")["mean"].agg(["mean", "min", "max"]).reindex(["generic", "pedagogy"])
    means = summary["mean"].to_numpy()
    errors = np.vstack([means - summary["min"].to_numpy(), summary["max"].to_numpy() - means])
    ax.bar([0, 1], means, color=[COLORS["blue"], COLORS["red"]], width=.58)
    ax.errorbar([0, 1], means, yerr=errors, fmt="none", color="black", capsize=3, linewidth=1)
    ax.set_xticks([0, 1], ["Generic", "Pedagogy"])
    ax.set_ylabel("Match to human telling action")
    ax.set_ylim(0, max(.5, summary["max"].max() * 1.15))
    ax.set_title("C  Prompting suppresses appropriate telling", loc="left", fontweight="bold")
    ax.text(.5, .47, "bars: mean; whiskers: classifier range", ha="center", va="top", fontsize=8)

    ax = axes[1, 1]
    diagnosis = longtutor[longtutor["outcome"] == "diagnosis_correct"].copy()
    predictor_order = ["item_only", "teaching_mean", "teaching_dimensions"]
    predictor_labels = ["History only", "+ teaching mean", "+ four dimensions"]
    colors = [COLORS["blue"], COLORS["orange"], COLORS["green"]]
    rng = np.random.default_rng(20260819)
    for index, (predictor, label, color) in enumerate(zip(predictor_order, predictor_labels, colors)):
        values = diagnosis.loc[diagnosis["predictors"] == predictor, "auc"].to_numpy(float)
        ax.scatter(index + rng.uniform(-.10, .10, len(values)), values, s=11, color="black", alpha=.65, zorder=3)
        ax.scatter(index, values.mean(), marker="D", s=60, color=color, edgecolor="black", linewidth=.7, zorder=4)
    ax.set_xticks(range(3), predictor_labels, rotation=12, ha="right")
    ax.set_ylabel("Held-out-model diagnosis AUC")
    lower = max(0, diagnosis["auc"].min() - .04); upper = min(1, diagnosis["auc"].max() + .04)
    ax.set_ylim(lower, upper)
    ax.set_title("D  Teaching scores do not add diagnosis", loc="left", fontweight="bold")
    ax.text(1, upper - .01, "diamonds: mean; dots: held-out model folds", ha="center", va="top", fontsize=8)

    for axis in axes.flat:
        axis.spines[["top", "right"]].set_visible(False)
        axis.grid(axis="y", color="0.9", linewidth=.6, zorder=0)
        axis.set_axisbelow(True)

    fig.savefig(output / "main_findings.png", dpi=300, bbox_inches="tight")
    fig.savefig(
        output / "main_findings.pdf", bbox_inches="tight",
        metadata={"CreationDate": None, "ModDate": None},
    )
    plt.close(fig)
    make_semantic_figure(root, output)
    print(output / "main_findings.pdf")


if __name__ == "__main__":
    main()
