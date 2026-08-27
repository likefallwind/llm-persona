from __future__ import annotations

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import run_theory_grounded_judge as judge_runner
from run_theory_grounded_judge import DIMENSIONS, assign_splits, validate_annotation


def test_validate_annotation_requires_exact_dimensions_and_labels() -> None:
    valid = {
        "candidates": {
            "A": {dimension: 3 for dimension in DIMENSIONS},
            "B": {dimension: 4 for dimension in DIMENSIONS},
        },
        "confidence": 4,
    }
    assert validate_annotation(valid, ["A", "B"])
    invalid = {**valid, "candidates": {"A": valid["candidates"]["A"]}}
    assert not validate_annotation(invalid, ["A", "B"])


def test_assign_splits_is_deterministic_and_stratified() -> None:
    batches = [
        {
            "benchmark": benchmark,
            "item_id": f"{benchmark}-{index}",
            "pair_group": benchmark,
            "pair_id": f"{benchmark}-{index}",
        }
        for benchmark in ("a", "b")
        for index in range(10)
    ]
    first = assign_splits(batches, seed=17, pilot_per_benchmark=3)
    second = assign_splits(list(reversed(batches)), seed=17, pilot_per_benchmark=3)
    assert [(row["benchmark"], row["item_id"], row["split"]) for row in first] == [
        (row["benchmark"], row["item_id"], row["split"]) for row in second
    ]
    for benchmark in ("a", "b"):
        assert sum(row["benchmark"] == benchmark and row["split"] == "pilot" for row in first) == 3


def test_assign_splits_keeps_prompt_pairs_together() -> None:
    batches = [
        {
            "benchmark": arm,
            "item_id": f"{arm}-{pair_id}",
            "pair_group": "shared",
            "pair_id": pair_id,
        }
        for pair_id in ("p1", "p2", "p3")
        for arm in ("generic", "pedagogy")
    ]
    assigned = assign_splits(batches, seed=9, pilot_per_benchmark=1)
    by_pair: dict[str, set[str]] = {}
    for row in assigned:
        by_pair.setdefault(row["pair_id"], set()).add(row["split"])
    assert all(len(splits) == 1 for splits in by_pair.values())
    assert sum(next(iter(splits)) == "pilot" for splits in by_pair.values()) == 1


def test_confirmatory_rubric_keeps_only_pilot_supported_dimensions() -> None:
    dimensions, rubric = judge_runner.RUBRIC_SPECS[
        judge_runner.CONFIRMATORY_RUBRIC_VERSION
    ]
    assert dimensions == (
        "instructional_agency", "relational_communion", "next_step_actionability",
    )
    assert "information_sequencing" not in rubric
    assert "learner_contingency" not in rubric
