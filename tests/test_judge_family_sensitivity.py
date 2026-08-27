from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from analyze_judge_family_sensitivity import analyze


def test_identical_judges_are_leaveout_robust() -> None:
    rows = []
    for judge in ("j1", "j2", "j3", "j4"):
        for task, benchmark, arm in (
            ("mathdial_standard", "generic", "generic"),
            ("mathdial_standard", "pedagogy", "pedagogy"),
            ("mathdial_hard", "hard-generic", "generic"),
            ("mathdial_hard", "hard-pedagogy", "pedagogy"),
            ("socratic", "socratic", "socratic"),
        ):
            for model_index, model in enumerate("abcdef"):
                prompt_shift = model_index % 3 if arm == "pedagogy" else 0
                rows.append({
                    "judge": judge, "benchmark": benchmark, "task": task, "arm": arm,
                    "item_id": f"{benchmark}-1", "pair_id": "1", "model": model,
                    "dimension": "d", "score": model_index + prompt_shift,
                })
    detail, decision = analyze(pd.DataFrame(rows))
    assert len(detail) == 4
    assert decision["classification"][0]["judge_family_robust"] is True
