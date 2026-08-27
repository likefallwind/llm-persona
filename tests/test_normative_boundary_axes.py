from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from analyze_normative_boundary_axes import stability


def test_stability_classifies_matching_context_profiles() -> None:
    frame = pd.DataFrame([
        {"model": model, "context": context, "value": value}
        for context in ("a", "b", "c")
        for model, value in (("m1", .1), ("m2", .3), ("m3", .8))
    ])
    result = stability(frame, "axis", "value")
    assert result["rank_gate"]
    assert result["icc_gate"]
    assert result["stability_strength"] == "robust_both_metrics"
