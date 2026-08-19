from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


generator = load_module("factorial_generator", ROOT / "scripts/generate_factorial_prompt_panel.py")
analyzer = load_module("factorial_analyzer", ROOT / "scripts/analyze_factorial_prompt_panel.py")
runner = load_module("factorial_runner", ROOT / "scripts/run_factorial_prompt_panel.py")


def test_generator_is_balanced_and_deterministic():
    spec = json.loads((ROOT / "data/factorial_prompt_spec_v1.json").read_text())
    first = generator.build_samples(spec)
    second = generator.build_samples(spec)
    assert first == second
    assert len(first) == 512
    assert len({row["sample_id"] for row in first}) == 512
    frame = pd.DataFrame(first)
    counts = frame.groupby([
        "problem_family", "learner_need", "question_policy", "answer_policy", "tone_policy",
    ]).size()
    assert counts.nunique() == 1
    assert counts.iloc[0] == 8
    assert all(len(row["messages"]) == 2 for row in first)
    assert len({row["prompt_sha256"] for row in first}) == 512


def test_response_metrics_are_deterministic():
    metrics = analyzer.response_metrics(
        "What did you do to the denominators? Great start! Final answer: 3/4.",
        [r"(?<!\d)3/4(?!\d)"],
    )
    assert metrics["question_first"] == 1
    assert metrics["question_any"] == 1
    assert metrics["answer_reveal_any"] == 1
    assert metrics["answer_reveal_correct"] == 1
    assert metrics["warmth_marker"] == 1
    integer_pattern = generator.numeric_patterns(generator.Fraction(17))
    assert analyzer.response_metrics("Final answer: 17.", integer_pattern)["answer_reveal_correct"] == 1
    assert analyzer.response_metrics("Final answer: 17.5.", integer_pattern)["answer_reveal_correct"] == 0


def test_gate_evaluation_accepts_selective_perfect_effects():
    spec = json.loads((ROOT / "data/factorial_prompt_spec_v1.json").read_text())
    rows = []
    for group in ["ALL", *spec["models"]]:
        for factor, target in analyzer.TARGET_METRICS.items():
            for metric in analyzer.PRIMARY_METRICS:
                rows.append({
                    "group": group,
                    "factor": factor,
                    "metric": metric,
                    "mean_difference": 1.0 if metric == target else 0.05,
                })
    effects = pd.DataFrame(rows)
    need = pd.DataFrame([
        {"group": "ALL", "contrast": "direct_minus_explore_reveal", "mean_difference": 0.2},
        {"group": "ALL", "contrast": "explore_minus_direct_question", "mean_difference": 0.2},
    ])
    decision = analyzer.evaluate_gates(spec, effects, need)
    assert all(row["controllable"] and row["selective"] for row in decision["factor_results"].values())
    assert decision["learner_need"]["reveal_pass"]
    assert decision["learner_need"]["question_pass"]


def test_end_to_end_analyzer_recovers_perfect_factor_effects():
    full_spec = json.loads((ROOT / "data/factorial_prompt_spec_v1.json").read_text())
    manifest = [
        row for row in generator.build_samples(full_spec)
        if row["base_id"] == "arithmetic_mean-00"
    ]
    spec = {**full_spec, "models": ["test-model"]}
    responses = []
    for sample in manifest:
        parts = []
        if sample["question_policy"] == "question_first":
            parts.append("What operation should determine the denominator?")
        else:
            parts.append("The denominator should be the number of observations.")
        if sample["tone_policy"] == "warm":
            parts.append("Great start!")
        if sample["answer_policy"] == "reveal":
            parts.append(f"Final answer: {sample['answer']}.")
        response = " ".join(parts)
        responses.append({
            "sample_id": sample["sample_id"],
            "model": "test-model",
            "prompt_sha256": sample["prompt_sha256"],
            "response": response,
            "error": "",
        })
    frame = analyzer.build_metric_frame(spec, manifest, responses)
    effects, _ = analyzer.effect_tables(frame, reps=20, seed=1)
    target = effects[(effects.group == "ALL") & effects.target_metric]
    assert dict(zip(target.factor, target.mean_difference)) == {
        "question_policy": 1.0,
        "answer_policy": 1.0,
        "tone_policy": 1.0,
    }


class EmptyThenSuccessClient:
    def __init__(self):
        self.calls = 0

    def reset_usage_window(self):
        pass

    def read_usage_window(self):
        return {"calls": self.calls}

    def chat(self, messages, model, max_tokens, stream):
        self.calls += 1
        return "" if self.calls == 1 else "A useful response"


def test_runner_retries_empty_stream_nonstream():
    sample = {
        "sample_id": "s", "base_id": "b", "problem_family": "f",
        "learner_need": "explore", "question_policy": "question_first",
        "answer_policy": "withhold", "tone_policy": "warm",
        "prompt_sha256": "p", "messages": [{"role": "user", "content": "x"}],
    }
    row = runner.call_one(EmptyThenSuccessClient(), "m", sample, retries=2)
    assert not row["error"]
    assert row["attempts"] == 2
    assert row["transport"] == "nonstream"
