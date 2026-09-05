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


# Keep figure text searchable and avoid Type 3 fonts in the ACL PDF.
plt.rcParams["pdf.fonttype"] = 42
plt.rcParams["ps.fonttype"] = 42


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

    semantic = pd.read_csv(root / "artifacts/semantic_panel/semantic_profiles.csv")
    epistemic = pd.read_csv(root / "artifacts/epistemic_character_axes_v1/model_profiles.csv")
    actions = pd.read_csv(root / "artifacts/dialogue_act_validity/match_by_target_act.csv")
    routing_selectors = pd.read_csv(
        root / "artifacts/two_stage_routing_trial_analysis_v1/selector_summary.csv"
    )
    routing_executors = pd.read_csv(
        root / "artifacts/two_stage_routing_trial_analysis_v1/executor_realization.csv"
    )

    plt.rcParams.update({
        "font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9,
        "legend.fontsize": 8, "figure.dpi": 160,
    })
    fig, axes = plt.subplots(2, 2, figsize=(8.0, 5.8), constrained_layout=True)

    model_labels = {
        "glm-5.2": "GLM", "deepseek-v4-pro": "DeepSeek", "qwen3.5-4b": "Qwen",
        "doubao-seed-2.0-pro": "Doubao", "minimax-m3": "M3", "minimax-m2.7": "M2.7",
    }
    core_models = list(model_labels)

    # Panel A: a compact five-axis profile. Each column is standardized across
    # the six-model panel; these are behavioral axes, not an ability score.
    ax = axes[0, 0]
    generic = semantic[(semantic["arm"] == "generic") & semantic["model"].isin(core_models)]
    defaults = generic.groupby(["model", "dimension"])["centered_mean"].mean().unstack()
    prompt_delta = semantic[semantic["model"].isin(core_models)].pivot_table(
        index=["task", "model", "dimension"], columns="arm", values="raw_mean"
    )
    prompt_delta["delta"] = prompt_delta["pedagogy"] - prompt_delta["generic"]
    prompt_delta = prompt_delta.groupby(["model", "dimension"])["delta"].mean().unstack()
    confidence = epistemic.set_index("model")["expressed_confidence"]
    profile = pd.DataFrame({
        "Direct\nhelp": defaults["help_directness"],
        "Expressed\nconfidence": confidence,
        "Information\nload": defaults["cognitive_load"],
        "Shift to\nelicitation": prompt_delta["elicitation"],
        "Shift away from\ndirect help": -prompt_delta["help_directness"],
    }).loc[core_models]
    standardized = (profile - profile.mean()) / profile.std(ddof=0)
    im = ax.imshow(standardized.to_numpy(), aspect="auto", cmap="RdBu_r", vmin=-1.7, vmax=1.7)
    ax.set_xticks(range(profile.shape[1]), profile.columns, fontsize=7)
    ax.set_yticks(range(profile.shape[0]), [model_labels[m] for m in profile.index], fontsize=8)
    for i in range(standardized.shape[0]):
        for j in range(standardized.shape[1]):
            value = standardized.iloc[i, j]
            ax.text(j, i, f"{value:+.1f}", ha="center", va="center", fontsize=6.5,
                    color="white" if abs(value) > 1.05 else "black")
    ax.tick_params(length=0)
    ax.set_title("A  Model-conditioned behavioral profiles", loc="left", fontweight="bold")

    # Panel B: the same prompt shifts every model, but by different amounts.
    ax = axes[0, 1]
    directness = semantic[
        (semantic["dimension"] == "help_directness") & semantic["model"].isin(core_models)
    ].groupby(["model", "arm"])["raw_mean"].mean().unstack()
    directness = directness.sort_values("generic")
    for model, row in directness.iterrows():
        ax.plot([0, 1], [row["generic"], row["pedagogy"]], color="0.72", linewidth=1, zorder=1)
        ax.scatter(0, row["generic"], color=COLORS["blue"], s=34, zorder=2)
        ax.scatter(1, row["pedagogy"], color=COLORS["orange"], s=34, zorder=2)
        ax.text(-.05, row["generic"], model_labels[model], ha="right", va="center", fontsize=7)
    ax.set_xlim(-.46, 1.18)
    ax.set_xticks([0, 1], ["Generic prompt", "Pedagogy prompt"])
    ax.set_ylabel("Help directness (1–5)")
    ax.set_title("B  Shared steering, model-specific movement", loc="left", fontweight="bold")

    ax = axes[1, 0]
    fit = actions[(actions["family"] == "standard") & actions["target_act"].isin(["probing", "telling"])]
    summary = fit.groupby(["target_act", "arm"])["mean"].mean().unstack().loc[["probing", "telling"]]
    x = np.arange(2); width = .34
    ax.bar(x - width / 2, summary["generic"], width, color=COLORS["blue"], label="Generic")
    ax.bar(x + width / 2, summary["pedagogy"], width, color=COLORS["orange"], label="Pedagogy")
    ax.set_xticks(x, ["Human chose\nprobing", "Human chose\ntelling"])
    ax.set_ylabel("Agreement with human action")
    ax.set_ylim(0, .5)
    ax.set_title("C  A fixed shift helps one context, harms another", loc="left", fontweight="bold")
    ax.legend(frameon=False, ncol=2, loc="upper center")

    ax = axes[1, 1]
    selector_values = routing_selectors["target_accuracy"].to_numpy()
    executor_values = routing_executors["realization_rate"].to_numpy()
    labels = ["Select\nASK", "Select\nEXPLAIN", "Execute\nASK", "Execute\nEXPLAIN"]
    values = np.r_[selector_values, executor_values]
    ax.bar(range(4), values, color=[COLORS["red"], COLORS["red"], COLORS["green"], COLORS["green"]],
           width=.66)
    ax.axhline(.5, color="0.35", linestyle="--", linewidth=1, label="Selection chance")
    ax.set_xticks(range(4), labels)
    ax.set_ylim(0, 1.08)
    ax.set_ylabel("Accuracy / realization rate")
    ax.set_title("D  Realization is easy; action selection is not", loc="left", fontweight="bold")
    ax.legend(frameon=False, loc="upper left")

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
