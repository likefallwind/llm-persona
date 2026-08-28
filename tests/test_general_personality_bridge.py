from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from analyze_existing_general_personality_bridge import (
    axis_values,
    bridge_features,
    exact_spearman_p,
)


def test_bridge_features_are_bilingual_and_do_not_retain_text() -> None:
    values = bridge_features("抱歉，我不确定，信息不足，所以无法提供答案。")
    assert values["apology_rate"] > 0
    assert values["uncertainty_acknowledgment_rate"] > 0
    assert values["refusal_rate"] > 0
    assert all(not isinstance(value, str) for value in values.values())


def test_axis_signs_separate_directiveness_and_caution() -> None:
    profile = {
        "first_plural_rate": 0.0,
        "second_person_rate": 0.0,
        "praise_rate": 0.0,
        "encouragement_rate": 0.0,
        "question_rate": -1.0,
        "imperative_rate": 1.0,
        "explanation_rate": 1.0,
        "answer_reveal_rate": 1.0,
        "hedge_rate": -1.0,
        "uncertainty_acknowledgment_rate": -1.0,
        "limitation_rate": 0.0,
        "refusal_rate": 0.0,
        "apology_rate": 0.0,
        "markdown_heading_rate": 0.0,
        "bullet_rate": 0.0,
        "numbered_step_rate": 0.0,
        "log_tokens": 0.0,
    }
    axes = axis_values(profile)
    assert axes["directive_expression"] > 0
    assert axes["epistemic_caution_language"] < 0


def test_exact_spearman_detects_perfect_reversal() -> None:
    rho, p = exact_spearman_p(np.arange(6.0), np.arange(5.0, -1.0, -1.0))
    assert rho == -1.0
    assert p < 0.05
