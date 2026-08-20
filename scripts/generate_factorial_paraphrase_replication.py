#!/usr/bin/env python3
"""Generate two frozen clause-paraphrase factorial panels and balanced queues."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from generate_factorial_prompt_panel import LEARNER_NEEDS, canonical_hash


SYSTEM_PREFIXES = {
    "paraphrase_a": (
        "Reply to the student in English. Obey each teaching constraint below, "
        "without referring to these constraints in your reply."
    ),
    "paraphrase_b": (
        "Write an English tutoring response that follows every rule listed here. "
        "Do not describe, repeat, or acknowledge the rules."
    ),
}

CLAUSE_SETS = {
    "paraphrase_a": {
        "question_policy": {
            "question_first": (
                "Teaching move: Open by posing one specific question about how the "
                "student reasoned. Any explanation must come after that question."
            ),
            "explain_only": (
                "Teaching move: Open by briefly explaining the reasoning error. Do "
                "not ask the student a question anywhere in the response."
            ),
        },
        "answer_policy": {
            "withhold": (
                "Solution disclosure: Leave the numerical result unstated, including "
                "in any summary, and leave one meaningful step for the student."
            ),
            "reveal": (
                "Solution disclosure: Give the correct numerical result plainly and "
                "close with the exact template 'Final answer: <value>.'"
            ),
        },
        "tone_policy": {
            "warm": (
                "Interpersonal style: Add one short, genuine encouraging remark and "
                "remain supportive without exaggerated praise."
            ),
            "neutral": (
                "Interpersonal style: Remain matter-of-fact and professional, with no "
                "praise, reassurance, or encouragement."
            ),
        },
    },
    "paraphrase_b": {
        "question_policy": {
            "question_first": (
                "Dialogue rule: Before offering an explanation, ask exactly one "
                "targeted question about the learner's approach in the opening sentence."
            ),
            "explain_only": (
                "Dialogue rule: Give a concise explanation immediately, using only "
                "declarative sentences and posing no questions."
            ),
        },
        "answer_policy": {
            "withhold": (
                "Result rule: Do not disclose the solved numeric value anywhere and "
                "omit any final-answer label so the learner must finish a step."
            ),
            "reveal": (
                "Result rule: Disclose the solved numeric value explicitly, ending the "
                "response with 'Final answer: <value>.'"
            ),
        },
        "tone_policy": {
            "warm": (
                "Style rule: Use a caring and supportive voice with one concise "
                "encouraging statement, while avoiding overpraise."
            ),
            "neutral": (
                "Style rule: Use an even, businesslike voice and avoid every form of "
                "praise, comfort, reassurance, or encouragement."
            ),
        },
    },
}

ORIGINAL_CLAUSE_FRAGMENTS = (
    "Interaction policy: Start with exactly one focused question",
    "Interaction policy: Ask no questions",
    "Answer policy: Do not state the final numeric answer",
    "Answer policy: State the correct numeric result explicitly",
    "Tone policy: Include one brief sincere encouragement",
    "Tone policy: Use neutral professional language",
)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def selected_base_ids(rows: list[dict[str, Any]], indices: list[int]) -> list[str]:
    families: dict[str, set[str]] = {}
    for row in rows:
        families.setdefault(str(row["problem_family"]), set()).add(str(row["base_id"]))
    selected: list[str] = []
    for family in sorted(families):
        bases = sorted(families[family])
        for index in indices:
            if index < 0 or index >= len(bases):
                raise RuntimeError(f"base index {index} outside {family}: {len(bases)} bases")
            selected.append(bases[index])
    return selected


def build_samples(spec: dict[str, Any], parent_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    indices = [int(value) for value in spec["selected_base_indices_per_family"]]
    selected = set(selected_base_ids(parent_rows, indices))
    parent_subset = [row for row in parent_rows if str(row["base_id"]) in selected]
    expected_parent = int(spec["expected_base_problems"]) * 16
    if len(parent_subset) != expected_parent:
        raise RuntimeError(f"parent subset mismatch: {len(parent_subset)} != {expected_parent}")

    samples: list[dict[str, Any]] = []
    seed = int(spec["seed"])
    permutations = [
        (0, 1, 2), (1, 2, 0), (2, 0, 1),
        (0, 2, 1), (2, 1, 0), (1, 0, 2),
    ]
    permutation_by_sample: dict[str, tuple[int, int, int]] = {}
    for wording_set in spec["wording_sets"]:
        sample_ids = [
            f"paraphrase-v1|{parent['sample_id']}|{wording_set}"
            for parent in parent_subset
        ]
        ranked = sorted(
            sample_ids,
            key=lambda sample_id: hashlib.sha256(
                f"{seed}|clauses|{wording_set}|{sample_id}".encode()
            ).hexdigest(),
        )
        permutation_by_sample.update({
            sample_id: permutations[index % len(permutations)]
            for index, sample_id in enumerate(ranked)
        })
    for parent in sorted(parent_subset, key=lambda row: str(row["sample_id"])):
        learner_need = str(parent["learner_need"])
        user = (
            f"Problem: {parent['problem']}\n"
            f"Learner work: {parent['student_work']}\n"
            f"Learner request: {LEARNER_NEEDS[learner_need]}"
        )
        for wording_set in spec["wording_sets"]:
            clauses = [
                CLAUSE_SETS[wording_set]["question_policy"][parent["question_policy"]],
                CLAUSE_SETS[wording_set]["answer_policy"][parent["answer_policy"]],
                CLAUSE_SETS[wording_set]["tone_policy"][parent["tone_policy"]],
            ]
            sample_id = f"paraphrase-v1|{parent['sample_id']}|{wording_set}"
            permutation = permutation_by_sample[sample_id]
            ordered = [clauses[index] for index in permutation]
            system = SYSTEM_PREFIXES[wording_set] + "\n- " + "\n- ".join(ordered)
            messages = [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ]
            samples.append({
                "sample_id": sample_id,
                "parent_sample_id": parent["sample_id"],
                "base_id": parent["base_id"],
                "problem_family": parent["problem_family"],
                "problem": parent["problem"],
                "student_work": parent["student_work"],
                "answer": parent["answer"],
                "accepted_answer_patterns": parent["accepted_answer_patterns"],
                "learner_need": learner_need,
                "question_policy": parent["question_policy"],
                "answer_policy": parent["answer_policy"],
                "tone_policy": parent["tone_policy"],
                "wording_set": wording_set,
                "clause_order": list(permutation),
                "messages": messages,
                "prompt_sha256": canonical_hash(messages),
                "prompt_chars": sum(len(message["content"]) for message in messages),
            })

    expected = int(spec["expected_samples_per_model"])
    if len(samples) != expected or len({row["sample_id"] for row in samples}) != expected:
        raise RuntimeError(f"paraphrase sample mismatch: {len(samples)} != {expected}")
    return sorted(samples, key=lambda row: str(row["sample_id"]))


def stratum_key(row: dict[str, Any]) -> str:
    columns = (
        "wording_set", "learner_need", "question_policy", "answer_policy", "tone_policy",
    )
    return "|".join(str(row[column]) for column in columns)


def order_hash(seed: int, model: str, value: str) -> str:
    return hashlib.sha256(f"{seed}|{model}|{value}".encode()).hexdigest()


def build_order_plan(spec: dict[str, Any], samples: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seed = int(spec["order_seed"])
    plan: list[dict[str, Any]] = []
    for model in spec["models"]:
        strata: dict[str, list[dict[str, Any]]] = {}
        for sample in samples:
            strata.setdefault(stratum_key(sample), []).append(sample)
        if len(strata) != 32 or {len(rows) for rows in strata.values()} != {8}:
            raise RuntimeError("expected 32 wording-by-factor strata with eight bases each")
        for key, rows in strata.items():
            strata[key] = sorted(
                rows,
                key=lambda row, key=key: order_hash(
                    seed, str(model), f"stratum|{key}|{row['sample_id']}",
                ),
            )
        rank = 0
        for block_index in range(8):
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
        "--spec", type=Path,
        default=Path("data/factorial_paraphrase_replication_spec_v1.json"),
    )
    parser.add_argument(
        "--parent-manifest", type=Path,
        default=Path("artifacts/factorial_prompt_v1/sample_manifest.jsonl"),
    )
    parser.add_argument(
        "--output-dir", type=Path,
        default=Path("artifacts/factorial_paraphrase_replication_v1"),
    )
    args = parser.parse_args()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    samples = build_samples(spec, load_jsonl(args.parent_manifest))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = args.output_dir / "sample_manifest.jsonl"
    manifest_path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in samples),
        encoding="utf-8",
    )
    plan = build_order_plan(spec, samples)
    plan_path = args.output_dir / "request_order_plan.jsonl"
    plan_path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in plan),
        encoding="utf-8",
    )
    all_text = "\n".join(
        message["content"] for row in samples for message in row["messages"]
    )
    positions = {
        f"policy_{policy_index}_position_{position}": sum(
            row["clause_order"][position] == policy_index for row in samples
        )
        for policy_index in range(3) for position in range(3)
    }
    summary = {
        "schema_version": 1,
        "base_ids": sorted({row["base_id"] for row in samples}),
        "base_problem_count": len({row["base_id"] for row in samples}),
        "wording_sets": sorted({row["wording_set"] for row in samples}),
        "sample_count": len(samples),
        "samples_per_wording_set": {
            wording: sum(row["wording_set"] == wording for row in samples)
            for wording in spec["wording_sets"]
        },
        "model_count": len(spec["models"]),
        "expected_calls": len(samples) * len(spec["models"]),
        "manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        "order_plan_sha256": hashlib.sha256(plan_path.read_bytes()).hexdigest(),
        "order_plan_rows": len(plan),
        "exact_32_stratum_block_balance": all(
            len({row["stratum_key"] for row in plan
                 if row["model"] == model and row["block_index"] == block}) == 32
            for model in spec["models"] for block in range(8)
        ),
        "clause_position_counts": positions,
        "original_clause_fragment_hits": {
            fragment: all_text.count(fragment) for fragment in ORIGINAL_CLAUSE_FRAGMENTS
        },
        "prompt_hashes_unique": len({row["prompt_sha256"] for row in samples}) == len(samples),
        "potential_pii_pattern_flags": {
            "email": len(re.findall(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", all_text, re.I)),
            "url": len(re.findall(r"https?://", all_text, re.I)),
            "phone_like": len(re.findall(r"(?<!\d)(?:\+?\d[ -]?){10,14}(?!\d)", all_text)),
        },
        "payload_scope": "synthetic problems, wrong work, learner requests, and frozen paraphrased policy clauses only",
    }
    (args.output_dir / "design_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
