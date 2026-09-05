#!/usr/bin/env python3
"""Build the localized overview figure for the Chinese reading edition."""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/llm-persona-matplotlib-zh")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "paper/figures"
COLORS = {
    "blue": "#0072B2",
    "orange": "#E69F00",
    "green": "#009E73",
    "red": "#D55E00",
}


def main() -> None:
    semantic = pd.read_csv(ROOT / "artifacts/semantic_panel/semantic_profiles.csv")
    epistemic = pd.read_csv(
        ROOT / "artifacts/epistemic_character_axes_v1/model_profiles.csv"
    )
    actions = pd.read_csv(
        ROOT / "artifacts/dialogue_act_validity/match_by_target_act.csv"
    )
    routing_selectors = pd.read_csv(
        ROOT / "artifacts/two_stage_routing_trial_analysis_v1/selector_summary.csv"
    )
    routing_executors = pd.read_csv(
        ROOT / "artifacts/two_stage_routing_trial_analysis_v1/executor_realization.csv"
    )

    plt.rcParams.update(
        {
            "font.family": "Noto Sans CJK SC",
            "font.size": 9,
            "axes.titlesize": 10,
            "axes.labelsize": 9,
            "legend.fontsize": 8,
            "figure.dpi": 160,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "axes.unicode_minus": False,
        }
    )
    fig, axes = plt.subplots(2, 2, figsize=(8.0, 5.8), constrained_layout=True)

    model_labels = {
        "glm-5.2": "GLM", "deepseek-v4-pro": "DeepSeek", "qwen3.5-4b": "Qwen",
        "doubao-seed-2.0-pro": "Doubao", "minimax-m3": "M3", "minimax-m2.7": "M2.7",
    }
    core_models = list(model_labels)

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
        "直接\n帮助": defaults["help_directness"],
        "表达\n置信度": confidence,
        "信息\n负荷": defaults["cognitive_load"],
        "转向\n引导提问": prompt_delta["elicitation"],
        "减少\n直接帮助": -prompt_delta["help_directness"],
    }).loc[core_models]
    standardized = (profile - profile.mean()) / profile.std(ddof=0)
    ax.imshow(standardized.to_numpy(), aspect="auto", cmap="RdBu_r", vmin=-1.7, vmax=1.7)
    ax.set_xticks(range(profile.shape[1]), profile.columns, fontsize=7)
    ax.set_yticks(range(profile.shape[0]), [model_labels[m] for m in profile.index], fontsize=8)
    for i in range(standardized.shape[0]):
        for j in range(standardized.shape[1]):
            value = standardized.iloc[i, j]
            ax.text(j, i, f"{value:+.1f}", ha="center", va="center", fontsize=6.5,
                    color="white" if abs(value) > 1.05 else "black")
    ax.tick_params(length=0)
    ax.set_title("A  模型条件化的教育行为画像", loc="left", fontweight="bold")

    ax = axes[0, 1]
    directness = semantic[
        (semantic["dimension"] == "help_directness") & semantic["model"].isin(core_models)
    ].groupby(["model", "arm"])["raw_mean"].mean().unstack()
    directness = directness.sort_values("generic")
    for model, row in directness.iterrows():
        ax.plot([0, 1], [row["generic"], row["pedagogy"]], color="0.72", linewidth=1, zorder=1)
        ax.scatter(0, row["generic"], color=COLORS["blue"], s=34, zorder=2)
        ax.scatter(1, row["pedagogy"], color=COLORS["orange"], s=34, zorder=2)
        ax.text(-0.05, row["generic"], model_labels[model], ha="right", va="center", fontsize=7)
    ax.set_xlim(-0.46, 1.18)
    ax.set_xticks([0, 1], ["通用提示", "教学提示"])
    ax.set_ylabel("帮助直接性（1--5）")
    ax.set_title("B  共同引导，模型特异的位移", loc="left", fontweight="bold")

    ax = axes[1, 0]
    fit = actions[(actions["family"] == "standard") & actions["target_act"].isin(["probing", "telling"])]
    summary = fit.groupby(["target_act", "arm"])["mean"].mean().unstack().loc[["probing", "telling"]]
    x = np.arange(2); width = 0.34
    ax.bar(x - width / 2, summary["generic"], width, color=COLORS["blue"], label="通用提示")
    ax.bar(x + width / 2, summary["pedagogy"], width, color=COLORS["orange"], label="教学提示")
    ax.set_xticks(x, ["教师选择\n追问", "教师选择\n讲解"])
    ax.set_ylabel("与人类教师行动的一致率")
    ax.set_ylim(0, 0.5)
    ax.set_title("C  固定偏移帮助一种情境、损害另一种", loc="left", fontweight="bold")
    ax.legend(frameon=False, ncol=2, loc="upper center")

    ax = axes[1, 1]
    selector_values = routing_selectors["target_accuracy"].to_numpy()
    executor_values = routing_executors["realization_rate"].to_numpy()
    values = np.r_[selector_values, executor_values]
    labels = ["选择\n提问", "选择\n讲解", "执行\n提问", "执行\n讲解"]
    ax.bar(range(4), values, color=[COLORS["red"], COLORS["red"], COLORS["green"], COLORS["green"]], width=0.66)
    ax.axhline(0.5, color="0.35", linestyle="--", linewidth=1, label="选择随机水平")
    ax.set_xticks(range(4), labels)
    ax.set_ylim(0, 1.08)
    ax.set_ylabel("准确率 / 执行率")
    ax.set_title("D  动作易执行，情境化选择仍困难", loc="left", fontweight="bold")
    ax.legend(frameon=False, loc="upper left")

    for axis in axes.flat:
        axis.spines[["top", "right"]].set_visible(False)
        axis.grid(axis="y", color="0.9", linewidth=0.6, zorder=0)
        axis.set_axisbelow(True)

    OUTPUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT / "main_findings_zh.png", dpi=300, bbox_inches="tight")
    fig.savefig(
        OUTPUT / "main_findings_zh.pdf",
        bbox_inches="tight",
        metadata={"CreationDate": None, "ModDate": None},
    )
    plt.close(fig)
    print(OUTPUT / "main_findings_zh.pdf")


if __name__ == "__main__":
    main()
