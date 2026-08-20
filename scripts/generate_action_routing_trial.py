#!/usr/bin/env python3
"""Freeze a balanced probing/telling action-routing trial and request order."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any

from generate_factorial_prompt_panel import canonical_hash


SYSTEM_PROMPTS = {
    "generic": (
        "You are an experienced math teacher and you are going to respond to a "
        "student in a useful and caring way. The student is trying to solve the "
        "following problem. Use no more than two sentences."
    ),
    "uniform_scaffold": (
        "Be a friendly, supportive tutor. Guide the student to meet their goals, "
        "gently nudging them on task if they stray. Ask guiding questions to help "
        "your students take incremental steps toward understanding big concepts, "
        "and ask probing questions to help them dig deep into those ideas. Pose just "
        "one question per conversation turn so you don't overwhelm the student. Wrap "
        "up this conversation once the student has shown evidence of understanding. "
        "Use no more than two sentences."
    ),
    "adaptive_router": (
        "You are an experienced math teacher. Select the most appropriate next "
        "teaching move from the conversation evidence: ask one targeted diagnostic "
        "question, give a focused hint, directly explain the missing idea when the "
        "student needs explicit instruction, or briefly acknowledge and redirect. "
        "Do not reflexively default to a question. Perform the selected move naturally, "
        "without naming or discussing this selection, in no more than two sentences."
    ),
}

ORACLE_PROMPTS = {
    "probing": (
        "You are an experienced math teacher. The next teaching move must be exactly "
        "one targeted diagnostic question about the student's reasoning. Put the "
        "question in the first sentence and use no more than two sentences."
    ),
    "telling": (
        "You are an experienced math teacher. The next teaching move must directly "
        "explain the missing idea or correction. Use only declarative sentences, ask "
        "no questions, and use no more than two sentences."
    ),
}


def load_targets(path: Path, benchmark: str, source: str) -> dict[str, str]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    selected: dict[str, str] = {}
    for row in rows:
        if (
            row.get("benchmark") != benchmark
            or row.get("target_source") != source
            or not row.get("target_act")
        ):
            continue
        item_id, target = str(row["item_id"]), str(row["target_act"])
        if item_id in selected and selected[item_id] != target:
            raise RuntimeError(f"conflicting target labels for {item_id}")
        selected[item_id] = target
    return selected


def format_context(example: dict[str, Any]) -> tuple[str, str]:
    conversation = list(example.get("dialog_history") or [])
    if len(conversation) < 2 or conversation[-1].get("user") != "Teacher":
        raise RuntimeError("bridge item lacks a held-out final teacher turn")
    history = "\n".join(
        f"{'Student' if turn.get('user') == 'Student' else 'Teacher'}: {turn['text']}"
        for turn in conversation[:-1]
    )
    user = (
        f"Problem: {example['problem']}\n"
        "Conversation so far:\n"
        f"{history}\n"
        "Write the teacher's next response."
    )
    return user, str(conversation[-1].get("text") or "")


def select_contexts(
    spec: dict[str, Any], bridge: list[dict[str, Any]], targets: dict[str, str],
) -> list[dict[str, Any]]:
    prefix = str(spec["source_benchmark"]).split("_")[-1]
    candidates: dict[str, list[dict[str, Any]]] = {
        target: [] for target in spec["target_acts"]
    }
    for index, example in enumerate(bridge):
        item_id = f"{prefix}-{index}"
        target = targets.get(item_id)
        if target not in candidates:
            continue
        user, heldout = format_context(example)
        candidates[target].append({
            "context_id": item_id,
            "bridge_index": index,
            "target_act": target,
            "problem": example["problem"],
            "conversation_prompt": user,
            "heldout_teacher_sha256": hashlib.sha256(heldout.encode()).hexdigest(),
        })
    selected: list[dict[str, Any]] = []
    count = int(spec["contexts_per_target_act"])
    seed = int(spec["seed"])
    for target in spec["target_acts"]:
        ranked = sorted(
            candidates[target],
            key=lambda row: hashlib.sha256(
                f"{seed}|context|{target}|{row['context_id']}".encode()
            ).hexdigest(),
        )
        if len(ranked) < count:
            raise RuntimeError(f"only {len(ranked)} eligible {target} contexts")
        selected.extend(ranked[:count])
    if len(selected) != int(spec["expected_contexts"]):
        raise RuntimeError("selected context count differs from frozen spec")
    return sorted(selected, key=lambda row: row["context_id"])


def build_samples(spec: dict[str, Any], contexts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    samples: list[dict[str, Any]] = []
    for context in contexts:
        for arm in spec["arms"]:
            system = (
                ORACLE_PROMPTS[context["target_act"]]
                if arm == "oracle_action" else SYSTEM_PROMPTS[arm]
            )
            messages = [
                {"role": "system", "content": system},
                {"role": "user", "content": context["conversation_prompt"]},
            ]
            samples.append({
                "sample_id": f"routing-v1|{context['context_id']}|{arm}",
                "context_id": context["context_id"],
                "bridge_index": context["bridge_index"],
                "target_act": context["target_act"],
                "arm": arm,
                "heldout_teacher_sha256": context["heldout_teacher_sha256"],
                "messages": messages,
                "prompt_sha256": canonical_hash(messages),
                "prompt_chars": sum(len(message["content"]) for message in messages),
            })
    expected = int(spec["expected_samples_per_model"])
    if len(samples) != expected or len({row["sample_id"] for row in samples}) != expected:
        raise RuntimeError(f"routing sample count mismatch: {len(samples)} != {expected}")
    return sorted(samples, key=lambda row: row["sample_id"])


def stratum_key(row: dict[str, Any]) -> str:
    return f"{row['target_act']}|{row['arm']}"


def order_hash(seed: int, model: str, value: str) -> str:
    return hashlib.sha256(f"{seed}|{model}|{value}".encode()).hexdigest()


def build_order_plan(spec: dict[str, Any], samples: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seed = int(spec["order_seed"])
    plan: list[dict[str, Any]] = []
    for model in spec["models"]:
        strata: dict[str, list[dict[str, Any]]] = {}
        for sample in samples:
            strata.setdefault(stratum_key(sample), []).append(sample)
        if len(strata) != 8 or {len(rows) for rows in strata.values()} != {48}:
            raise RuntimeError("expected eight target-by-arm strata with 48 contexts each")
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
    parser.add_argument(
        "--spec", type=Path, default=Path("data/action_routing_trial_spec_v1.json"),
    )
    parser.add_argument("--bridge", type=Path)
    parser.add_argument("--target-audit", type=Path)
    parser.add_argument(
        "--output-dir", type=Path, default=Path("artifacts/action_routing_trial_v1"),
    )
    args = parser.parse_args()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    bridge_path = args.bridge or Path(spec["source_bridge"])
    target_path = args.target_audit or Path(spec["source_target_audit"])
    bridge_sha = hashlib.sha256(bridge_path.read_bytes()).hexdigest()
    target_sha = hashlib.sha256(target_path.read_bytes()).hexdigest()
    if bridge_sha != spec["source_hashes"]["bridge_sha256"]:
        raise RuntimeError("source bridge hash differs from frozen spec")
    if target_sha != spec["source_hashes"]["target_audit_sha256"]:
        raise RuntimeError("target audit hash differs from frozen spec")
    bridge = json.loads(bridge_path.read_text(encoding="utf-8"))
    targets = load_targets(
        target_path, str(spec["source_benchmark"]), str(spec["target_source"]),
    )
    contexts = select_contexts(spec, bridge, targets)
    samples = build_samples(spec, contexts)
    plan = build_order_plan(spec, samples)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = args.output_dir / "sample_manifest.jsonl"
    private_manifest_path = args.output_dir / "run" / "request_manifest.jsonl"
    order_path = args.output_dir / "request_order_plan.jsonl"
    public_samples = [
        {key: value for key, value in row.items() if key != "messages"}
        for row in samples
    ]
    manifest_path.write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
            for row in public_samples
        ),
        encoding="utf-8",
    )
    private_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    private_manifest_path.write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in samples
        ),
        encoding="utf-8",
    )
    order_path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in plan),
        encoding="utf-8",
    )
    nonoracle = [row for row in samples if row["arm"] != "oracle_action"]
    nonoracle_prompt_counts = {
        arm: len({
            row["messages"][0]["content"] for row in nonoracle if row["arm"] == arm
        })
        for arm in spec["arms"] if arm != "oracle_action"
    }
    summary = {
        "schema_version": 1,
        "context_count": len(contexts),
        "contexts_by_target": {
            target: sum(row["target_act"] == target for row in contexts)
            for target in spec["target_acts"]
        },
        "sample_count": len(samples),
        "samples_per_model": len(samples),
        "model_count": len(spec["models"]),
        "expected_calls": len(plan),
        "manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        "source_bridge_sha256": bridge_sha,
        "source_target_audit_sha256": target_sha,
        "order_plan_sha256": hashlib.sha256(order_path.read_bytes()).hexdigest(),
        "exact_eight_stratum_block_balance": all(
            len({row["stratum_key"] for row in plan
                 if row["model"] == model and row["block_index"] == block}) == 8
            for model in spec["models"] for block in range(48)
        ),
        "prompt_hashes_unique": len({row["prompt_sha256"] for row in samples}) == len(samples),
        "nonoracle_system_prompt_counts_by_arm": nonoracle_prompt_counts,
        "nonoracle_system_prompts_are_target_invariant": all(
            count == 1 for count in nonoracle_prompt_counts.values()
        ),
        "payload_scope": (
            "public MathDial-derived benchmark problem and conversation contexts; "
            "no private user logs, archived model responses, or held-out teacher text"
        ),
        "release_scope": (
            "public manifest contains IDs, labels, hashes, and design metadata only; "
            "the generated request manifest with benchmark text is gitignored"
        ),
    }
    (args.output_dir / "design_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
