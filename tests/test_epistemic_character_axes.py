from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from analyze_epistemic_character_axes import load_jsonl, profile_stability


def test_load_jsonl_drops_raw_text(tmp_path) -> None:
    path = tmp_path / "scored.jsonl"
    path.write_text(json.dumps({
        "item_id": "x",
        "response": "private response",
        "reasoning": "private reasoning",
        "score_status": "scored",
        "correct": True,
        "confidence": 90,
    }) + "\n", encoding="utf-8")

    row = load_jsonl(path)[0]

    assert "response" not in row
    assert "reasoning" not in row
    assert row["confidence"] == 90


def test_profile_stability_separates_robust_and_mixed() -> None:
    robust = pd.DataFrame([
        {"model": model, "context": context, "value": value + offset}
        for model, value in zip("abcdef", range(6), strict=True)
        for context, offset in (("x", 0.0), ("y", 0.1), ("z", -0.1))
    ])
    result = profile_stability(robust, "context", "value", "axis")

    assert result["icc_gate"]
    assert result["rank_gate"]
    assert result["stability_strength"] == "robust_both_metrics"
