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
    "two_stage_generator", ROOT / "scripts/generate_two_stage_routing_trial.py",
)
runner = load_module(
    "two_stage_runner", ROOT / "scripts/run_two_stage_routing_trial.py",
)
analyzer = load_module(
    "two_stage_analyzer", ROOT / "scripts/analyze_two_stage_routing_trial.py",
)
selection_bias = load_module(
    "two_stage_selection_bias",
    ROOT / "scripts/analyze_two_stage_selection_bias.py",
)


def frozen_objects():
    spec = json.loads((ROOT / "data/two_stage_routing_trial_spec_v1.json").read_text())
    contexts = generator.inherited_contexts(spec)
    samples = generator.build_samples(spec, contexts)
    return spec, contexts, samples


def test_two_stage_manifest_and_order_are_exactly_balanced():
    spec, contexts, samples = frozen_objects()
    assert len(contexts) == 96
    assert len(samples) == 480
    assert len({row["prompt_sha256"] for row in samples}) == 480
    for call_type in spec["call_types"]:
        prompts = {
            row["messages"][0]["content"] for row in samples
            if row["call_type"] == call_type
        }
        assert len(prompts) == 1
        assert {row["target_act"] for row in samples if row["call_type"] == call_type} == {
            "probing", "telling",
        }
    plan = generator.build_order_plan(spec, samples)
    assert len(plan) == 2400
    for model in spec["models"]:
        ordered = runner.planned_samples(samples, plan, model, spec["order_seed"])
        for start in range(0, 480, 10):
            assert len({generator.stratum_key(row) for row in ordered[start:start + 10]}) == 10


def test_selector_parser_is_strict_but_allows_terminal_punctuation():
    pattern = "^(ASK|EXPLAIN)[.!]?$"
    assert analyzer.parse_selector("ASK", pattern) == "ASK"
    assert analyzer.parse_selector(" explain. ", pattern) == "EXPLAIN"
    assert analyzer.parse_selector("I choose ASK", pattern) == "INVALID"


class SuccessClient:
    def reset_usage_window(self):
        pass

    def read_usage_window(self):
        return {"calls": 1}

    def chat(self, messages, model, max_tokens, stream):
        return "ASK"


def test_runner_serializes_real_two_stage_sample_schema():
    _, _, samples = frozen_objects()
    row = runner.call_one(SuccessClient(), "test", samples[0], retries=1)
    assert not row["error"]
    assert row["context_id"]
    assert row["arm"] in {sample["call_type"] for sample in samples}
    assert row["target_act"] in {"probing", "telling"}


def test_complete_synthetic_panel_validates_and_composes_without_text_release():
    spec, _, samples = frozen_objects()
    plan = generator.build_order_plan(spec, samples)
    sample_map = {row["sample_id"]: row for row in samples}
    response_rows = []
    for planned in plan:
        sample = sample_map[planned["sample_id"]]
        target = spec["binary_actions"][sample["target_act"]]
        if sample["call_type"].startswith("selector_"):
            response = target
        elif sample["call_type"] == "ask_executor":
            response = "What step in your reasoning should we inspect?"
        elif sample["call_type"] == "explain_executor":
            response = "Subtract the same value from both sides."
        else:
            response = "What should you try next?" if target == "ASK" else "Use the inverse operation."
        response_rows.append({
            "sample_id": sample["sample_id"],
            "model": planned["model"],
            "prompt_sha256": sample["prompt_sha256"],
            "response": response,
            "error": "",
            "two_stage_queue_rank": planned["queue_rank"],
        })
    successful = analyzer.validate_responses(spec, samples, plan, response_rows)
    assert len(successful) == 2400
    binary = analyzer.binary_rows(spec, samples, successful)
    assert len(binary) == 480
    assert binary.single_pass_target_match.mean() == 1
    assert binary.selector_ask_first_composed_target_match.mean() == 1
    assert binary.selector_explain_first_composed_target_match.mean() == 1


def test_joint_gate_requires_both_selector_wordings():
    spec, _, _ = frozen_objects()
    selectors = pd.DataFrame([
        {
            "selector": selector, "valid_rate": 1.0, "target_accuracy": 0.7,
            "target_accuracy_ci_low": 0.6, "models_above_chance": 5,
        }
        for selector in analyzer.SELECTORS
    ])
    contrasts = pd.DataFrame([
        {
            "selector": selector, "mean_delta": 0.1,
            "context_cluster_ci_low": 0.02, "positive_models": 5,
        }
        for selector in analyzer.SELECTORS
    ])
    execution = pd.DataFrame([
        {"executor": "ask_executor_question", "realization_rate": 1.0, "minimum_model_rate": 1.0},
        {"executor": "explain_executor_no_question", "realization_rate": 1.0, "minimum_model_rate": 1.0},
    ])
    assert analyzer.evaluate_gates(spec, selectors, contrasts, execution)[
        "joint_two_stage_claim_pass"
    ]
    selectors.loc[selectors.selector == analyzer.SELECTORS[1], "target_accuracy"] = 0.5
    assert not analyzer.evaluate_gates(spec, selectors, contrasts, execution)[
        "joint_two_stage_claim_pass"
    ]


def test_post_hoc_selection_audit_exposes_position_bias_without_raw_text():
    rows = []
    for context_id, target in (("p", "probing"), ("t", "telling")):
        for model in ("m1", "m2"):
            rows.append({
                "context_id": context_id,
                "target_act": target,
                "model": model,
                "selector_ask_first_selected_action": "ASK",
                "selector_ask_first_valid": 1,
                "selector_ask_first_target_match": int(target == "probing"),
                "selector_explain_first_selected_action": "EXPLAIN",
                "selector_explain_first_valid": 1,
                "selector_explain_first_target_match": int(target == "telling"),
            })
    overall, by_target_model, separation, report = selection_bias.analyze(
        pd.DataFrame(rows), reps=20, seed=1,
    )
    assert len(overall) == 2
    assert len(by_target_model) == 12
    assert (separation.probing_minus_telling_ask_rate == 0).all()
    assert report["wording_audit"]["ask_first_minus_explain_first_ask_rate"] == 1
    assert report["status"] == "post_hoc_text_free_selector_diagnostic"
