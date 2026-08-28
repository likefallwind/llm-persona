from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from analyze_affiliation_stability_pilot import icc3
from judge_affiliation_stability_pilot import valid


def test_icc3_is_one_for_identical_judges() -> None:
    matrix = np.array([[1, 1, 1], [2, 2, 2], [4, 4, 4]], dtype=float)
    single, average = icc3(matrix)
    assert single == 1.0
    assert average == 1.0


def test_affiliation_annotation_validation_requires_complete_scale() -> None:
    labels = ["A", "B"]
    scores = {
        "affiliative_behavior": 4,
        "benevolent_cost_acceptance": 3,
        "assertive_dominance": 2,
        "surface_warmth": 4,
        "task_effectiveness": 5,
    }
    assert valid({"candidates": {"A": scores, "B": scores}, "confidence": 4}, labels)
    assert not valid({"candidates": {"A": scores}, "confidence": 4}, labels)
