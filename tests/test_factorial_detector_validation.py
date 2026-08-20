from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


generator = load_module(
    "detector_validation_generator", ROOT / "scripts/generate_factorial_detector_validation.py",
)
runner = load_module(
    "detector_validation_runner", ROOT / "scripts/run_factorial_detector_validation.py",
)
analyzer = load_module(
    "detector_validation_analyzer", ROOT / "scripts/analyze_factorial_detector_validation.py",
)


def test_validation_plan_is_deterministic_balanced_and_outcome_independent():
    spec = json.loads((ROOT / "data/factorial_detector_validation_spec_v1.json").read_text())
    first_samples, first_batches = generator.build_plan(ROOT, spec)
    second_samples, second_batches = generator.build_plan(ROOT, spec)
    assert first_samples == second_samples
    assert first_batches == second_batches
    assert len(first_samples) == 480
    assert len(first_batches) == 48
    frame = pd.DataFrame(first_samples)
    assert set(frame.groupby("panel").size()) == {160, 320}
    assert set(frame.groupby("model").size()) == {96}
    expected = {"parent": 2, "replication": 4}
    for panel, count in expected.items():
        assert set(frame[frame.panel == panel].groupby(["base_id", "model"]).size()) == {count}
    assert not ({"question_first", "answer_reveal_correct", "warmth_marker"} & set(frame))


def test_validation_json_parser_and_schema_are_strict():
    parsed = runner.parse_json_object(
        '```json\n{"candidates":{"A":{"question_first":"yes",'
        '"answer_reveal_correct":"no","warmth_marker":"uncertain"}},"confidence":4}\n```'
    )
    assert runner.valid_annotation(parsed, ["A"])
    parsed["candidates"]["A"]["warmth_marker"] = "maybe"
    assert not runner.valid_annotation(parsed, ["A"])


def test_candidate_order_is_judge_specific_and_deterministic():
    batch = {
        "batch_id": "parent|base|B01",
        "candidates": [
            {"validation_id": f"v{index}", "response": f"response {index}"}
            for index in range(10)
        ],
    }
    first = [row["validation_id"] for row in runner.candidate_order(20260822, "MiniMax-M3", batch)]
    again = [row["validation_id"] for row in runner.candidate_order(20260822, "MiniMax-M3", batch)]
    other = [row["validation_id"] for row in runner.candidate_order(20260822, "glm-5.2", batch)]
    assert first == again
    assert first != other
    assert set(first) == {f"v{index}" for index in range(10)}


def test_confusion_metrics_and_registered_gate():
    detector = analyzer.np.array([1] * 45 + [0] * 5 + [0] * 45 + [1] * 5)
    gold = analyzer.np.array([1] * 50 + [0] * 50)
    values = analyzer.confusion_metrics(detector, gold)
    assert values["sensitivity"] == 0.9
    assert values["specificity"] == 0.9
    assert values["balanced_accuracy"] == 0.9
    assert values["cohen_kappa"] == 0.8

    majority_rows = []
    for metric in runner.LABELS:
        for index, (detector_value, gold_value) in enumerate(zip(detector, gold)):
            majority_rows.append({
                "validation_id": f"{metric}-{index}",
                "metric": metric,
                "detector_label": int(detector_value),
                "majority_label": "yes" if gold_value else "no",
            })
    spec = json.loads((ROOT / "data/factorial_detector_validation_spec_v1.json").read_text())
    spec["validation_gate"] = {**spec["validation_gate"], "bootstrap_reps": 100}
    report = analyzer.metric_report(pd.DataFrame(majority_rows), spec)
    assert set(report["majority_label_coverage"]) == {1.0}
    assert set(report["balanced_accuracy_pass"]) == {True}
    assert set(report["kappa_pass"]) == {True}


def test_majority_requires_two_binary_votes():
    assert analyzer.majority_label(["yes", "yes", "uncertain"]) == "yes"
    assert analyzer.majority_label(["no", "no", "yes"]) == "no"
    assert analyzer.majority_label(["yes", "no", "uncertain"]) == "uncertain"
