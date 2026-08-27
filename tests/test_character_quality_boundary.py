from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from analyze_character_quality_boundary import analyze


def test_quality_analysis_uses_matched_hashes_and_leaves_models_out() -> None:
    consensus_rows = []
    feature_rows = []
    for model_index, model in enumerate(("a", "b", "c")):
        for item in range(12):
            digest = f"{model}-{item}"
            score = 1 + ((model_index + item) % 5)
            consensus_rows.append({
                "benchmark": "mathtutorbench_x", "item_id": str(item), "model": model,
                "response_sha256": digest, "dimension": "actionability", "score": score,
            })
            row = {
                "benchmark": "mathtutorbench_x", "item_id": str(item), "model": model,
                "response_sha256": digest, "outcome_primary": float((score + item) % 2),
            }
            for feature in __import__("analyze_character_quality_boundary").ALL_FEATURES:
                row[feature] = float((item + model_index) % 3)
            feature_rows.append(row)
    result = analyze(pd.DataFrame(consensus_rows), pd.DataFrame(feature_rows))
    assert set(result["held_out_model"]) == {"a", "b", "c"}
    assert "transparent_plus_actionability" in set(result["feature_set"])
    assert result["n_test"].eq(12).all()
