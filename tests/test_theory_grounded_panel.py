from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from analyze_theory_grounded_panel import (
    decisions, expected_ids, prompt_effect_summary, prompt_effects, response_consensus,
)


def test_expected_ids_respects_split_benchmark_and_judges() -> None:
    manifest = {
        "items": [
            {"benchmark": "a", "item_id": "1", "split": "pilot"},
            {"benchmark": "a", "item_id": "2", "split": "formal"},
            {"benchmark": "b", "item_id": "3", "split": "pilot"},
        ]
    }
    assert expected_ids(manifest, "pilot", ["j1", "j2"], {"a"}) == {
        "a|1|j1", "a|1|j2"
    }


def test_prompt_effects_uses_matched_pair_ids() -> None:
    rows = []
    for arm, score in (("generic", 4.0), ("pedagogy", 2.0)):
        rows.append({
            "benchmark": arm,
            "task": "mathdial_standard",
            "arm": arm,
            "split": "pilot",
            "item_id": f"{arm}-1",
            "pair_id": "1",
            "model": "m",
            "response_sha256": arm,
            "dimension": "instructional_agency",
            "score": score,
            "score_mean": score,
            "judge_count": 2,
        })
    result = prompt_effects(pd.DataFrame(rows))
    assert len(result) == 1
    assert result.iloc[0]["paired_contexts"] == 1
    assert result.iloc[0]["mean_delta"] == -2.0


def test_prompt_summary_clusters_six_models_by_context() -> None:
    rows = []
    for pair_id in ("p1", "p2", "p3"):
        for model_index, model in enumerate("abcdef"):
            for arm, score in (("generic", float(model_index)), ("pedagogy", float(model_index + 2))):
                rows.append({
                    "task": "mathdial_standard", "arm": arm, "pair_id": pair_id,
                    "model": model, "dimension": "d", "score": score,
                })
    result = prompt_effect_summary(pd.DataFrame(rows), bootstrap=100, seed=7)
    assert len(result) == 1
    assert result.iloc[0]["paired_contexts"] == 3
    assert result.iloc[0]["mean_prompt_delta"] == 2
    assert result.iloc[0]["all_model_mean_deltas_positive"]


def test_response_consensus_drops_no_raw_text_column() -> None:
    ratings = pd.DataFrame([
        {
            "benchmark": "b", "task": "t", "arm": "generic", "split": "pilot",
            "item_id": "i", "pair_id": "p", "model": "m", "response_sha256": "h",
            "dimension": "instructional_agency", "judge": "j1", "score": 2,
            "confidence": 4, "raw_response": "must not survive",
        },
        {
            "benchmark": "b", "task": "t", "arm": "generic", "split": "pilot",
            "item_id": "i", "pair_id": "p", "model": "m", "response_sha256": "h",
            "dimension": "instructional_agency", "judge": "j2", "score": 4,
            "confidence": 4, "raw_response": "must not survive",
        },
    ])
    consensus = response_consensus(ratings)
    assert "raw_response" not in consensus
    assert consensus.iloc[0]["score"] == 3


def test_formal_decision_cannot_override_pilot_failure() -> None:
    dimension = "instructional_agency"
    icc = pd.DataFrame([{"dimension": dimension, "icc_3_k": .9}])
    diagnostics = pd.DataFrame([{
        "dimension": dimension, "score_sd": 1.0, "floor_fraction": 0.0,
        "ceiling_fraction": 0.0,
    }])
    profile = pd.DataFrame([{"dimension": dimension, "model_profile_spearman": .9}])
    stability = pd.DataFrame([{
        "dimension": dimension, "icc_3_1": .8, "median_pairwise_spearman": .8,
    }])
    variance = pd.DataFrame([{"dimension": dimension, "bootstrap_ci_low": .1}])
    features = pd.DataFrame([{
        "new_dimension": dimension, "magnitude_pass_0_30": True,
    }])
    convergence = pd.DataFrame([{
        "new_dimension": dimension, "old_dimension": "old", "spearman": .2,
    }])
    import analyze_theory_grounded_panel as panel
    original = panel.DIMENSIONS
    panel.DIMENSIONS = (dimension,)
    try:
        result = decisions(
            icc, diagnostics, profile, stability, variance, features, convergence, "formal",
            ["glm-5.2", "deepseek-v4-pro"], set(),
        )
    finally:
        panel.DIMENSIONS = original
    row = result["classification"][0]
    assert row["measurement_gates"]["pilot_measurement_pass"] is False
    assert row["cross_task_signature"] is False
