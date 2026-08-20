import importlib.util
import itertools
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
    "paraphrase_generator", ROOT / "scripts/generate_factorial_paraphrase_replication.py",
)
runner = load_module(
    "paraphrase_runner", ROOT / "scripts/run_factorial_paraphrase_replication.py",
)
analyzer = load_module(
    "paraphrase_analyzer", ROOT / "scripts/analyze_factorial_paraphrase_replication.py",
)
asymmetry = load_module(
    "control_asymmetry", ROOT / "scripts/analyze_factorial_control_asymmetry.py",
)


def frozen_objects():
    spec = json.loads(
        (ROOT / "data/factorial_paraphrase_replication_spec_v1.json").read_text()
    )
    parent = generator.load_jsonl(ROOT / "artifacts/factorial_prompt_v1/sample_manifest.jsonl")
    samples = generator.build_samples(spec, parent)
    return spec, samples


def test_paraphrase_manifest_is_complete_paired_and_uses_no_original_clause():
    spec, samples = frozen_objects()
    assert len(samples) == 256
    assert len({row["base_id"] for row in samples}) == 8
    assert {row["wording_set"] for row in samples} == {"paraphrase_a", "paraphrase_b"}
    assert all(
        sum(row["wording_set"] == wording for row in samples) == 128
        for wording in spec["wording_sets"]
    )
    assert all(
        sum(row["base_id"] == base for row in samples) == 32
        for base in {row["base_id"] for row in samples}
    )
    assert len({row["prompt_sha256"] for row in samples}) == 256
    position_counts = [
        sum(row["clause_order"][position] == policy for row in samples)
        for policy in range(3) for position in range(3)
    ]
    assert max(position_counts) - min(position_counts) <= 2
    transmitted = "\n".join(
        message["content"] for row in samples for message in row["messages"]
    )
    assert all(fragment not in transmitted for fragment in generator.ORIGINAL_CLAUSE_FRAGMENTS)


def test_model_order_is_deterministic_and_every_block_has_32_strata():
    spec, samples = frozen_objects()
    first = generator.build_order_plan(spec, samples)
    second = generator.build_order_plan(spec, samples)
    assert first == second
    assert len(first) == 1280
    for model in spec["models"]:
        ordered = runner.planned_samples(samples, first, model, spec["order_seed"])
        assert len(ordered) == 256
        for start in range(0, 256, 32):
            assert len({generator.stratum_key(row) for row in ordered[start:start + 32]}) == 32


def test_runner_rejects_tampered_order_hash():
    spec, samples = frozen_objects()
    plan = generator.build_order_plan(spec, samples)
    plan[0] = {**plan[0], "order_sha256": "0" * 64}
    try:
        runner.planned_samples(samples, plan, spec["models"][0], spec["order_seed"])
    except RuntimeError as exc:
        assert "order hash mismatch" in str(exc)
    else:
        raise AssertionError("tampered request order was accepted")


def deterministic_policy_frame(models=("m1", "m2"), bases=("b1", "b2", "b3", "b4")):
    rows = []
    for model, base, need, question, answer, tone in itertools.product(
        models,
        bases,
        ("explore", "direct"),
        ("question_first", "explain_only"),
        ("reveal", "withhold"),
        ("warm", "neutral"),
    ):
        rows.append({
            "model": model,
            "base_id": base,
            "learner_need": need,
            "question_policy": question,
            "answer_policy": answer,
            "tone_policy": tone,
            "question_first": int(question == "question_first"),
            "answer_reveal_correct": int(answer == "reveal"),
        })
    return pd.DataFrame(rows)


def test_control_asymmetry_recovers_system_effect_and_zero_override():
    frame = deterministic_policy_frame()
    table = asymmetry.asymmetry_table(frame, reps=20, seed=7)
    aggregate = table[table.group == "ALL"].set_index("policy")
    assert aggregate.loc["question", "system_conflict_effect"] == 1.0
    assert aggregate.loc["question", "learner_override_effect"] == 0.0
    assert aggregate.loc["question", "control_gap"] == 1.0
    assert aggregate.loc["answer", "system_conflict_effect"] == 1.0
    assert aggregate.loc["answer", "learner_override_effect"] == 0.0
    assert aggregate.loc["answer", "control_gap"] == 1.0


def test_control_asymmetry_gate_fails_when_override_is_not_equivalent_to_zero():
    table = asymmetry.asymmetry_table(deterministic_policy_frame(), reps=20, seed=8)
    mask = (table.group == "ALL") & (table.policy == "answer")
    table.loc[mask, "learner_override_ci_high"] = 0.2
    gates = json.loads(
        (ROOT / "data/factorial_paraphrase_replication_spec_v1.json").read_text()
    )["control_asymmetry_gates"]
    decision = asymmetry.evaluate_asymmetry_gates(table, gates)
    assert decision["question"]["control_asymmetry_pass"]
    assert not decision["answer"]["control_asymmetry_pass"]


def test_joint_wording_rule_is_downgrade_only():
    spec, _ = frozen_objects()

    def payload(selective=True, asymmetry_pass=True):
        return {
            "factor_gates": {
                "factor_results": {
                    factor: {"selective": selective}
                    for factor in ("question_policy", "answer_policy", "tone_policy")
                }
            },
            "control_asymmetry": {
                policy: {"control_asymmetry_pass": asymmetry_pass}
                for policy in ("question", "answer")
            },
        }

    per_wording = {
        "paraphrase_a": payload(),
        "paraphrase_b": payload(),
    }
    per_wording["paraphrase_b"]["factor_gates"]["factor_results"][
        "question_policy"
    ]["selective"] = False
    per_wording["paraphrase_b"]["control_asymmetry"]["answer"][
        "control_asymmetry_pass"
    ] = False
    decision = analyzer.wording_decision(spec, per_wording)
    assert not decision["factor_wording_transport"]["question_policy"][
        "paraphrase_robust_operational_effect"
    ]
    assert decision["factor_wording_transport"]["answer_policy"][
        "paraphrase_robust_operational_effect"
    ]
    assert not decision["control_asymmetry"]["answer"][
        "prospectively_confirmed_across_wordings"
    ]


def test_analyzer_end_to_end_on_deterministic_synthetic_responses(tmp_path):
    spec, samples = frozen_objects()
    plan = generator.build_order_plan(spec, samples)
    sample_map = {row["sample_id"]: row for row in samples}
    manifest_path = tmp_path / "manifest.jsonl"
    order_path = tmp_path / "order.jsonl"
    response_path = tmp_path / "responses.jsonl"
    output_dir = tmp_path / "analysis"
    manifest_path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in samples),
        encoding="utf-8",
    )
    order_path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in plan),
        encoding="utf-8",
    )
    responses = []
    for row in plan:
        sample = sample_map[row["sample_id"]]
        if sample["question_policy"] == "question_first":
            opening = "What step did you use first?"
        else:
            opening = "The first step needs a concise correction."
        warmth = (
            " Keep going; you can do this."
            if sample["tone_policy"] == "warm" else ""
        )
        answer = (
            f" Final answer: {sample['answer']}."
            if sample["answer_policy"] == "reveal" else ""
        )
        responses.append({
            "sample_id": row["sample_id"],
            "model": row["model"],
            "prompt_sha256": sample["prompt_sha256"],
            "response": opening + warmth + answer,
            "error": "",
            "paraphrase_queue_rank": row["queue_rank"],
        })
    response_path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in responses),
        encoding="utf-8",
    )
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/analyze_factorial_paraphrase_replication.py"),
            "--spec", str(ROOT / "data/factorial_paraphrase_replication_spec_v1.json"),
            "--manifest", str(manifest_path),
            "--order-plan", str(order_path),
            "--responses", str(response_path),
            "--output-dir", str(output_dir),
            "--bootstrap-reps", "20",
            "--seed", "19",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0
    report = json.loads(
        (output_dir / "paraphrase_replication_report.json").read_text(encoding="utf-8")
    )
    assert report["response_rows"] == 1280
    assert report["exact_32_stratum_block_balance"]
    assert all(
        item["paraphrase_robust_operational_effect"]
        for item in report["joint_decision"]["factor_wording_transport"].values()
    )
    assert all(
        item["prospectively_confirmed_across_wordings"]
        for item in report["joint_decision"]["control_asymmetry"].values()
    )
    assert (
        report["joint_decision"]["factor_wording_transport"]["tone_policy"]
        ["semantic_claim"] == "literal frozen encouragement marker only"
    )
