#!/usr/bin/env python3
"""Freeze a counterbalanced selection-then-execution tutoring trial."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from generate_action_routing_trial import format_context
from generate_factorial_prompt_panel import canonical_hash


PROMPTS = {
    "selector_ask_first": (
        "Choose the teacher's single best next action from the conversation. "
        "Choose ASK when a targeted diagnostic question about the student's reasoning "
        "is more appropriate. Choose EXPLAIN when the student needs a direct explanation "
        "of the missing idea or correction. Return exactly ASK or EXPLAIN and nothing else."
    ),
    "selector_explain_first": (
        "Decide on exactly one next teaching action using only the conversation evidence. "
        "Return EXPLAIN if direct instruction about the missing idea or correction is the "
        "better move. Return ASK if a diagnostic question about the student's reasoning is "
        "the better move. Output only the single token EXPLAIN or ASK."
    ),
    "ask_executor": (
        "You are an experienced math teacher. Ask exactly one targeted diagnostic question "
        "about the student's reasoning. Put the question in the first sentence and use no "
        "more than two sentences."
    ),
    "explain_executor": (
        "You are an experienced math teacher. Directly explain the missing idea or correction. "
        "Use only declarative sentences, ask no questions, and use no more than two sentences."
    ),
    "single_pass_adaptive": (
        "You are an experienced math teacher. Select the most appropriate next teaching move "
        "from the conversation evidence: ask one targeted diagnostic question, give a focused "
        "hint, directly explain the missing idea when the student needs explicit instruction, "
        "or briefly acknowledge and redirect. Do not reflexively default to a question. Perform "
        "the selected move naturally, without naming or discussing this selection, in no more "
        "than two sentences."
    ),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inherited_contexts(spec: dict[str, Any]) -> list[dict[str, Any]]:
    action_manifest = [
        json.loads(line) for line in Path(spec["parent_action_manifest"])
        .read_text(encoding="utf-8").splitlines() if line
    ]
    public_by_context: dict[str, dict[str, Any]] = {}
    for row in action_manifest:
        context_id = str(row["context_id"])
        public_by_context.setdefault(context_id, row)
        if public_by_context[context_id]["target_act"] != row["target_act"]:
            raise RuntimeError(f"parent target drift for {context_id}")
    if len(public_by_context) != int(spec["expected_contexts"]):
        raise RuntimeError("parent action contexts differ from frozen count")
    bridge = json.loads(Path(spec["source_bridge"]).read_text(encoding="utf-8"))
    contexts = []
    for context_id, row in sorted(public_by_context.items()):
        index = int(row["bridge_index"])
        user, heldout = format_context(bridge[index])
        if hashlib.sha256(heldout.encode()).hexdigest() != row["heldout_teacher_sha256"]:
            raise RuntimeError(f"held-out teacher hash drift for {context_id}")
        contexts.append({
            "context_id": context_id,
            "bridge_index": index,
            "target_act": row["target_act"],
            "conversation_prompt": user,
            "heldout_teacher_sha256": row["heldout_teacher_sha256"],
        })
    return contexts


def build_samples(spec: dict[str, Any], contexts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    samples = []
    for context in contexts:
        for call_type in spec["call_types"]:
            messages = [
                {"role": "system", "content": PROMPTS[call_type]},
                {"role": "user", "content": context["conversation_prompt"]},
            ]
            samples.append({
                "sample_id": f"two-stage-v1|{context['context_id']}|{call_type}",
                "context_id": context["context_id"],
                "bridge_index": context["bridge_index"],
                "target_act": context["target_act"],
                "arm": call_type,
                "call_type": call_type,
                "heldout_teacher_sha256": context["heldout_teacher_sha256"],
                "messages": messages,
                "prompt_sha256": canonical_hash(messages),
                "prompt_chars": sum(len(message["content"]) for message in messages),
            })
    expected = int(spec["expected_samples_per_model"])
    if len(samples) != expected or len({row["sample_id"] for row in samples}) != expected:
        raise RuntimeError(f"two-stage sample count mismatch: {len(samples)} != {expected}")
    return sorted(samples, key=lambda row: row["sample_id"])


def stratum_key(row: dict[str, Any]) -> str:
    return f"{row['target_act']}|{row['call_type']}"


def order_hash(seed: int, model: str, value: str) -> str:
    return hashlib.sha256(f"{seed}|{model}|{value}".encode()).hexdigest()


def build_order_plan(spec: dict[str, Any], samples: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seed = int(spec["order_seed"])
    plan = []
    for model in spec["models"]:
        strata: dict[str, list[dict[str, Any]]] = {}
        for sample in samples:
            strata.setdefault(stratum_key(sample), []).append(sample)
        if len(strata) != 10 or {len(rows) for rows in strata.values()} != {48}:
            raise RuntimeError("expected ten target-by-call strata with 48 contexts each")
        for key, rows in strata.items():
            strata[key] = sorted(
                rows,
                key=lambda row, key=key: order_hash(
                    seed, str(model), f"stratum|{key}|{row['sample_id']}",
                ),
            )
        rank = 0
        for block_index in range(48):
            block = [strata[key][block_index] for key in sorted(strata)]
            block = sorted(
                block,
                key=lambda row, block_index=block_index: order_hash(
                    seed, str(model), f"block|{block_index}|{row['sample_id']}",
                ),
            )
            for row in block:
                plan.append({
                    "model": model,
                    "queue_rank": rank,
                    "block_index": block_index,
                    "stratum_key": stratum_key(row),
                    "sample_id": row["sample_id"],
                    "order_sha256": order_hash(
                        seed, str(model), f"block|{block_index}|{row['sample_id']}",
                    ),
                })
                rank += 1
    return plan


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, default=Path("data/two_stage_routing_trial_spec_v1.json"))
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/two_stage_routing_trial_v1"))
    args = parser.parse_args()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    for key, field in (
        ("parent_action_spec_sha256", "parent_action_spec"),
        ("parent_action_manifest_sha256", "parent_action_manifest"),
        ("bridge_sha256", "source_bridge"),
        ("target_audit_sha256", "source_target_audit"),
    ):
        if sha256(Path(spec[field])) != spec["source_hashes"][key]:
            raise RuntimeError(f"frozen source hash drift: {field}")
    contexts = inherited_contexts(spec)
    samples = build_samples(spec, contexts)
    plan = build_order_plan(spec, samples)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    run_dir = args.output_dir / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    public = [{key: value for key, value in row.items() if key != "messages"} for row in samples]
    (args.output_dir / "sample_manifest.jsonl").write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in public), encoding="utf-8",
    )
    (run_dir / "request_manifest.jsonl").write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in samples), encoding="utf-8",
    )
    (args.output_dir / "request_order_plan.jsonl").write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in plan), encoding="utf-8",
    )
    report = {
        "schema_version": 1,
        "contexts": len(contexts),
        "samples_per_model": len(samples),
        "expected_calls": len(plan),
        "contexts_by_target": {
            target: sum(row["target_act"] == target for row in contexts)
            for target in spec["target_acts"]
        },
        "call_types": spec["call_types"],
        "unique_prompt_hashes": len({row["prompt_sha256"] for row in samples}),
        "exact_ten_stratum_block_balance": True,
        "payload_scope": "public MathDial-derived contexts; no held-out teacher text or private logs",
    }
    (args.output_dir / "design_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8",
    )
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
