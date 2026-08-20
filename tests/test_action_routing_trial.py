import importlib.util
import json
from pathlib import Path
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


generator = load_module(
    "action_routing_generator", ROOT / "scripts/generate_action_routing_trial.py",
)
runner = load_module(
    "action_routing_runner", ROOT / "scripts/run_action_routing_trial.py",
)
analyzer = load_module(
    "action_routing_analyzer", ROOT / "scripts/analyze_action_routing_trial.py",
)
surface = load_module(
    "action_routing_surface", ROOT / "scripts/analyze_action_routing_surface.py",
)


def frozen_objects():
    spec = json.loads((ROOT / "data/action_routing_trial_spec_v1.json").read_text())
    samples = [
        json.loads(line) for line in
        (ROOT / "artifacts/action_routing_trial_v1/sample_manifest.jsonl")
        .read_text(encoding="utf-8").splitlines() if line
    ]
    contexts = sorted({
        (row["context_id"], row["bridge_index"], row["target_act"],
         row["heldout_teacher_sha256"])
        for row in samples
    })
    return spec, contexts, samples


def test_manifest_is_balanced_and_nonoracle_policy_is_target_invariant():
    spec, contexts, samples = frozen_objects()
    assert len(contexts) == 96
    assert len(samples) == 384
    assert sum(row[2] == "probing" for row in contexts) == 48
    assert sum(row[2] == "telling" for row in contexts) == 48
    assert len({row["prompt_sha256"] for row in samples}) == 384
    for arm in ("generic", "uniform_scaffold", "adaptive_router"):
        assert {
            row["target_act"] for row in samples if row["arm"] == arm
        } == {"probing", "telling"}
    assert all("messages" not in row for row in samples)
    assert all("conversation_prompt" not in row for row in samples)

    synthetic_spec = {**spec, "expected_samples_per_model": 8}
    synthetic_contexts = [
        {
            "context_id": f"synthetic-{target}", "bridge_index": index,
            "target_act": target, "conversation_prompt": "public context",
            "heldout_teacher_sha256": "heldout-sentinel",
        }
        for index, target in enumerate(("probing", "telling"))
    ]
    synthetic = generator.build_samples(synthetic_spec, synthetic_contexts)
    for arm in ("generic", "uniform_scaffold", "adaptive_router"):
        prompts = {
            row["messages"][0]["content"] for row in synthetic if row["arm"] == arm
        }
        assert prompts == {generator.SYSTEM_PROMPTS[arm]}
    assert all(
        "heldout-sentinel" not in "\n".join(
            message["content"] for message in row["messages"]
        )
        for row in synthetic
    )


def test_order_plan_is_deterministic_and_exactly_block_balanced():
    spec, _, samples = frozen_objects()
    first = generator.build_order_plan(spec, samples)
    second = generator.build_order_plan(spec, samples)
    assert first == second
    checked_in = [
        json.loads(line) for line in
        (ROOT / "artifacts/action_routing_trial_v1/request_order_plan.jsonl")
        .read_text(encoding="utf-8").splitlines() if line
    ]
    assert first == checked_in
    assert len(first) == 1920
    for model in spec["models"]:
        ordered = runner.planned_samples(samples, first, model, spec["order_seed"])
        assert len(ordered) == 384
        for start in range(0, 384, 8):
            assert len({generator.stratum_key(row) for row in ordered[start:start + 8]}) == 8


def test_runner_rejects_tampered_order_hash():
    spec, _, samples = frozen_objects()
    plan = generator.build_order_plan(spec, samples)
    plan[0] = {**plan[0], "order_sha256": "0" * 64}
    try:
        runner.planned_samples(samples, plan, spec["models"][0], spec["order_seed"])
    except RuntimeError as exc:
        assert "order hash mismatch" in str(exc)
    else:
        raise AssertionError("tampered routing order was accepted")


class RoutingSuccessClient:
    def reset_usage_window(self):
        pass

    def read_usage_window(self):
        return {"calls": 1}

    def chat(self, messages, model, max_tokens, stream):
        assert messages == [{"role": "user", "content": "public context"}]
        assert model == "test-model"
        assert max_tokens is None
        assert stream
        return "Try the inverse operation first."


def test_runner_serializes_action_schema_without_factorial_fields():
    sample = {
        "sample_id": "route-1",
        "context_id": "context-1",
        "arm": "adaptive_router",
        "target_act": "telling",
        "prompt_sha256": "a" * 64,
        "messages": [{"role": "user", "content": "public context"}],
    }
    row = runner.call_one(RoutingSuccessClient(), "test-model", sample, retries=1)
    assert not row["error"]
    assert row["context_id"] == "context-1"
    assert row["arm"] == "adaptive_router"
    assert row["target_act"] == "telling"
    assert row["response_sha256"]
    assert "base_id" not in row


def deterministic_predictions(spec):
    rows = []
    matches = {
        "probing": {
            "generic": 0, "uniform_scaffold": 1,
            "adaptive_router": 1, "oracle_action": 1,
        },
        "telling": {
            "generic": 1, "uniform_scaffold": 0,
            "adaptive_router": 1, "oracle_action": 1,
        },
    }
    for variant in spec["analysis"]["classifier_variants"]:
        for target in spec["target_acts"]:
            for context in range(6):
                for model in spec["models"]:
                    for arm in spec["arms"]:
                        match = matches[target][arm]
                        rows.append({
                            "classifier_variant": variant,
                            "context_id": f"{target}-{context}",
                            "target_act": target,
                            "arm": arm,
                            "model": model,
                            "predicted_act": target if match else "generic",
                            "act_match": match,
                        })
    return pd.DataFrame(rows)


def test_joint_gates_pass_only_when_adaptive_arm_recovers_telling():
    spec = json.loads((ROOT / "data/action_routing_trial_spec_v1.json").read_text())
    predictions = deterministic_predictions(spec)
    contrasts, _ = analyzer.contrast_tables(predictions, reps=20, seed=5)
    means = analyzer.arm_means(predictions, reps=20, seed=6)
    decision = analyzer.evaluate_gates(spec, contrasts, means)
    assert decision["joint_all_classifier_variants_pass"]

    broken = contrasts.copy()
    mask = (
        (broken.classifier_variant == spec["analysis"]["classifier_variants"][0])
        & (broken.target_act == "telling")
        & (broken.contrast == "adaptive_minus_uniform")
    )
    broken.loc[mask, "mean_delta"] = 0.0
    broken.loc[mask, "context_cluster_ci_low"] = -0.1
    decision = analyzer.evaluate_gates(spec, broken, means)
    assert not decision["joint_all_classifier_variants_pass"]


def test_surface_audit_distinguishes_selection_from_realization():
    manifest = []
    successful = {}
    for target in ("probing", "telling"):
        for arm in ("generic", "uniform_scaffold", "adaptive_router", "oracle_action"):
            sample_id = f"{target}|{arm}"
            manifest.append({
                "sample_id": sample_id, "context_id": target,
                "target_act": target, "arm": arm,
            })
            if arm == "oracle_action":
                response = "What step led you there?" if target == "probing" else "Subtract three from both sides."
            elif arm == "adaptive_router":
                response = "What should you try next?"
            else:
                response = "Try the inverse operation."
            successful[(sample_id, "model")] = {"response": response}
    frame = surface.response_metrics(successful, manifest)
    summary = surface.arm_summary(frame, reps=20, seed=1)
    oracle = summary[
        (summary.arm == "oracle_action")
        & (summary.metric == "has_question_mark")
    ].set_index("target_act")["mean"]
    assert oracle["probing"] == 1
    assert oracle["telling"] == 0
    separation = surface.target_separation(frame, reps=20, seed=2)
    adaptive = separation[
        (separation.model == "ALL")
        & (separation.arm == "adaptive_router")
        & (separation.metric == "has_question_mark")
    ].iloc[0]
    assert adaptive.probing_minus_telling == 0
