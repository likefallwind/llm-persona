from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
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
    "factorial_order_generator", ROOT / "scripts/generate_factorial_order_replication.py",
)
runner = load_module(
    "factorial_order_runner", ROOT / "scripts/run_factorial_order_replication.py",
)
analyzer = load_module(
    "factorial_order_analyzer", ROOT / "scripts/analyze_factorial_order_replication.py",
)


def test_replication_subset_preserves_exact_parent_prompts():
    spec = json.loads(
        (ROOT / "data/factorial_order_replication_spec_v1.json").read_text()
    )
    parent = generator.load_jsonl(
        ROOT / "artifacts/factorial_prompt_v1/sample_manifest.jsonl"
    )
    subset = generator.build_subset(spec, parent)
    assert len(subset) == 128
    assert len({row["base_id"] for row in subset}) == 8
    assert sorted({row["base_id"] for row in subset}) == [
        "arithmetic_mean-00", "arithmetic_mean-04",
        "fraction_addition-00", "fraction_addition-04",
        "linear_equation-00", "linear_equation-04",
        "percentage_discount-00", "percentage_discount-04",
    ]
    parent_hashes = {row["sample_id"]: row["prompt_sha256"] for row in parent}
    assert all(parent_hashes[row["sample_id"]] == row["prompt_sha256"] for row in subset)


def test_model_specific_hash_order_is_deterministic_and_complete():
    spec = json.loads(
        (ROOT / "data/factorial_order_replication_spec_v1.json").read_text()
    )
    subset = generator.build_subset(
        spec,
        generator.load_jsonl(ROOT / "artifacts/factorial_prompt_v1/sample_manifest.jsonl"),
    )
    first_plan = generator.build_order_plan(spec, subset)
    second_plan = generator.build_order_plan(spec, subset)
    assert first_plan == second_plan
    first = runner.planned_samples(subset, first_plan, "MiniMax-M3", spec["order_seed"])
    other = runner.planned_samples(subset, first_plan, "MiniMax-M2.7", spec["order_seed"])
    assert {row["sample_id"] for row in first} == {row["sample_id"] for row in subset}
    assert [row["sample_id"] for row in first] != [row["sample_id"] for row in subset]
    assert [row["sample_id"] for row in first] != [row["sample_id"] for row in other]
    for block_start in range(0, 128, 16):
        assert len({generator.cell_key(row) for row in first[block_start:block_start + 16]}) == 16


def test_joint_order_decision_is_strictly_downgrade_only():
    passing_factor = {"selective": True}
    failing_factor = {"selective": False}
    primary = {
        "factor_results": {
            "question_policy": passing_factor,
            "answer_policy": failing_factor,
            "tone_policy": passing_factor,
        },
        "learner_need": {"reveal_pass": True, "question_pass": False},
    }
    replication = {
        "factor_results": {
            "question_policy": passing_factor,
            "answer_policy": passing_factor,
            "tone_policy": failing_factor,
        },
        "learner_need": {"reveal_pass": False, "question_pass": True},
    }
    rows = []
    for factor in ["question_policy", "answer_policy", "tone_policy"]:
        for group in ["ALL", "m1", "m2"]:
            rows.append({"factor": factor, "group": group, "positive_in_both": True})
    comparison = pd.DataFrame(rows)
    decision = analyzer.joint_decision(primary, replication, comparison)
    assert decision["factor_results"]["question_policy"]["order_robust"]
    assert not decision["factor_results"]["answer_policy"]["order_robust"]
    assert not decision["factor_results"]["tone_policy"]["order_robust"]
    assert not decision["learner_need"]["reveal_order_robust"]
    assert not decision["learner_need"]["question_order_robust"]


def test_replication_runner_requires_exact_parent_completion():
    complete = {
        "expected": 2560, "successful": 2560, "current_errors": 0,
        "missing": 0, "unexpected_keys": 0,
    }
    runner.require_parent_complete(complete)
    incomplete = {**complete, "successful": 2559, "missing": 1}
    try:
        runner.require_parent_complete(incomplete)
    except RuntimeError as exc:
        assert "must be exactly complete" in str(exc)
    else:
        raise AssertionError("incomplete parent panel was accepted")


def test_joint_order_decision_fails_on_one_nonpositive_group():
    passing = {
        "factor_results": {
            factor: {"selective": True}
            for factor in ["question_policy", "answer_policy", "tone_policy"]
        },
        "learner_need": {"reveal_pass": True, "question_pass": True},
    }
    comparison = pd.DataFrame([
        {"factor": factor, "group": group, "positive_in_both": not (
            factor == "question_policy" and group == "m2"
        )}
        for factor in ["question_policy", "answer_policy", "tone_policy"]
        for group in ["ALL", "m1", "m2"]
    ])
    decision = analyzer.joint_decision(passing, passing, comparison)
    assert not decision["factor_results"]["question_policy"]["order_robust"]
    assert decision["factor_results"]["answer_policy"]["order_robust"]


def test_order_replication_analyzer_end_to_end(tmp_path):
    parent_spec = json.loads((ROOT / "data/factorial_prompt_spec_v1.json").read_text())
    replication_spec = json.loads(
        (ROOT / "data/factorial_order_replication_spec_v1.json").read_text()
    )
    parent_manifest = generator.load_jsonl(
        ROOT / "artifacts/factorial_prompt_v1/sample_manifest.jsonl"
    )
    subset = generator.build_subset(replication_spec, parent_manifest)

    def response_for(sample):
        parts = [
            "What should we check first?"
            if sample["question_policy"] == "question_first"
            else "Here is a concise explanation."
        ]
        if sample["tone_policy"] == "warm":
            parts.append("Great start!")
        if sample["answer_policy"] == "reveal":
            parts.append(f"Final answer: {sample['answer']}.")
        return " ".join(parts)

    parent_rows = []
    for sample in parent_manifest:
        for model in parent_spec["models"]:
            parent_rows.append({
                "sample_id": sample["sample_id"], "model": model,
                "prompt_sha256": sample["prompt_sha256"],
                "response": response_for(sample), "error": "",
            })
    replication_rows = []
    order_plan = generator.build_order_plan(replication_spec, subset)
    for model in replication_spec["models"]:
        ordered = runner.planned_samples(
            subset, order_plan, model, replication_spec["order_seed"],
        )
        for rank, sample in enumerate(ordered):
            replication_rows.append({
                "sample_id": sample["sample_id"], "model": model,
                "prompt_sha256": sample["prompt_sha256"],
                "response": response_for(sample), "error": "",
                "replication_queue_rank": rank,
            })

    subset_path = tmp_path / "subset.jsonl"
    parent_path = tmp_path / "parent.jsonl"
    replication_path = tmp_path / "replication.jsonl"
    subset_path.write_text("".join(json.dumps(row) + "\n" for row in subset))
    parent_path.write_text("".join(json.dumps(row) + "\n" for row in parent_rows))
    replication_path.write_text(
        "".join(json.dumps(row) + "\n" for row in replication_rows)
    )
    output = tmp_path / "analysis"
    subprocess.run([
        sys.executable, str(ROOT / "scripts/analyze_factorial_order_replication.py"),
        "--parent-spec", str(ROOT / "data/factorial_prompt_spec_v1.json"),
        "--replication-spec", str(ROOT / "data/factorial_order_replication_spec_v1.json"),
        "--parent-manifest", str(ROOT / "artifacts/factorial_prompt_v1/sample_manifest.jsonl"),
        "--replication-manifest", str(subset_path),
        "--order-plan", str(
            ROOT / "artifacts/factorial_order_replication_v1/request_order_plan.jsonl"
        ),
        "--parent-responses", str(parent_path),
        "--replication-responses", str(replication_path),
        "--output-dir", str(output), "--bootstrap-reps", "10",
    ], check=True, capture_output=True, text=True)
    report = json.loads((output / "order_replication_report.json").read_text())
    assert report["parent_rows"] == 2560
    assert report["parent_subset_rows"] == 640
    assert report["replication_rows"] == 640
    assert all(
        row["order_robust"]
        for row in report["joint_order_robustness_decision"]["factor_results"].values()
    )
