from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


analyzer = load_module(
    "prompt_contingent_signatures",
    ROOT / "scripts/analyze_prompt_contingent_signatures.py",
)


@pytest.fixture
def balanced_semantic_frame() -> pd.DataFrame:
    rows = []
    models = ["model-a", "model-b", "model-c"]
    dimensions = ["help_directness", "cognitive_load"]
    for task_index, task in enumerate(["mathdial_standard", "mathdial_hard"]):
        for pair_index in range(18):
            pair_id = f"{task}-{pair_index:02d}"
            pair_offset = (pair_index % 3) * 0.05 + task_index * 0.03
            for model_index, model in enumerate(models):
                for arm in ["generic", "pedagogy"]:
                    for dimension_index, dimension in enumerate(dimensions):
                        default = 1.0 + model_index * 4.0 + dimension_index * 0.2
                        prompt = 0.0
                        if arm == "pedagogy":
                            prompt = 0.5 + model_index * 0.7
                        score = default + prompt + pair_offset
                        rows.append({
                            "benchmark": f"benchmark-{task}-{arm}",
                            "task": task,
                            "arm": arm,
                            "item_id": pair_id,
                            "pair_id": pair_id,
                            "model": model,
                            "response_sha256": f"{task}-{pair_index}-{model}-{arm}",
                            "dimension": dimension,
                            "score": score,
                            "score_mean": score,
                            "judge_count": 3,
                            "centered_score": score,
                            "z_centered_score": score,
                        })
    return pd.DataFrame(rows)


def test_validate_paired_semantic_rejects_missing_model_arm_cell(
    balanced_semantic_frame: pd.DataFrame,
):
    incomplete = balanced_semantic_frame.drop(index=balanced_semantic_frame.index[0])

    with pytest.raises(ValueError, match="complete model-by-arm grid"):
        analyzer.validate_paired_semantic(incomplete)


def test_variance_decomposition_recovers_prompt_and_model_interaction(
    balanced_semantic_frame: pd.DataFrame,
):
    result = analyzer.variance_decomposition(balanced_semantic_frame)

    assert (result["ss_prompt"] > 0).all()
    assert (result["ss_model_by_prompt"] > 0).all()
    assert np.allclose(result["ss_residual"], 0.0, atol=1e-10)


def test_elasticity_heterogeneity_detects_constructed_model_difference(
    balanced_semantic_frame: pd.DataFrame,
):
    result, model_effects = analyzer.elasticity_heterogeneity(
        balanced_semantic_frame,
        reps=499,
        seed=7,
    )

    assert (result["permutation_p"] < 0.05).all()
    assert (result["max_minus_min_model_delta"] > 1.0).all()
    assert set(model_effects["model"]) == {"model-a", "model-b", "model-c"}


def test_cross_prompt_attribution_retains_stable_model_identity(
    balanced_semantic_frame: pd.DataFrame,
):
    result = analyzer.cross_prompt_attribution(
        balanced_semantic_frame,
        reps=100,
        seed=11,
    )

    pooled = result[
        (result["train_task"] == "ALL")
        & (result["test_task"] == "ALL")
    ]
    assert len(pooled) == 2
    assert (pooled["accuracy"] == 1.0).all()
    assert (pooled["bootstrap_ci_low"] > pooled["chance_accuracy"]).all()


def test_headroom_adjustment_preserves_real_model_elasticity():
    rows = []
    models = ["model-a", "model-b", "model-c"]
    for task in ["mathdial_standard", "mathdial_hard"]:
        for pair_index in range(20):
            pair_id = f"{task}-{pair_index}"
            for model_index, model in enumerate(models):
                generic = 2.0 + 0.2 * model_index
                delta = 0.3 + 0.25 * model_index
                for arm, score in [("generic", generic), ("pedagogy", generic + delta)]:
                    rows.append({
                        "task": task,
                        "arm": arm,
                        "pair_id": pair_id,
                        "model": model,
                        "dimension": "help_directness",
                        "score": score,
                        "centered_score": score,
                    })
    frame = pd.DataFrame(rows)

    result, _ = analyzer.headroom_adjusted_elasticity(frame, reps=499, seed=19)

    assert (result["permutation_p"] < 0.05).all()
    assert (result["retained_context_fraction"] == 1.0).all()


def test_render_report_distinguishes_defaults_prompt_control_and_elasticity(
    balanced_semantic_frame: pd.DataFrame,
):
    decomposition = analyzer.variance_decomposition(balanced_semantic_frame)
    heterogeneity, _ = analyzer.elasticity_heterogeneity(
        balanced_semantic_frame,
        reps=99,
        seed=13,
    )
    attribution = analyzer.cross_prompt_attribution(
        balanced_semantic_frame,
        reps=50,
        seed=17,
    )
    report = analyzer.render_report(
        balanced_semantic_frame,
        decomposition,
        heterogeneity,
        attribution,
        decision={"verdict": "prompt_contingent_policy_signatures_supported"},
    )

    assert "default model differences" in report
    assert "shared prompt deformation" in report
    assert "model-specific elasticity" in report
    assert "prompt_contingent_policy_signatures_supported" in report
