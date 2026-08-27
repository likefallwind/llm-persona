from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from analyze_confirmatory_bridge import bridge_dimension


def test_bridge_requires_exact_hash_matches_and_preserves_profiles() -> None:
    rows = []
    for item in range(30):
        for model, score in (("a", 1), ("b", 3), ("c", 5), ("d", 2), ("e", 4), ("f", 3)):
            rows.append({
                "benchmark": "bench",
                "item_id": str(item),
                "pair_id": str(item),
                "model": model,
                "response_sha256": f"{item}-{model}",
                "dimension": "instructional_agency",
                "score": score,
            })
    frame = pd.DataFrame(rows)
    result = bridge_dimension(frame, frame.copy(), "instructional_agency")
    assert result["matched_responses"] == 180
    assert result["bridge_pass"] is True
    assert result["mean_absolute_score_difference"] == 0
