#!/usr/bin/env python3
"""Blind model-judge coding for theory-grounded educational character axes.

This runner reuses the frozen response sampling machinery without modifying the
original eight-dimension semantic panel.  A deterministic pilot/formal split
allows rubric development on the pilot while keeping the formal rows untouched.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from run_semantic_judge import (
    build_batches,
    candidate_order,
    completed_ids,
    load_json,
    parse_json_object,
    payload_audit,
    result_row,
)


DIMENSIONS = (
    "instructional_agency",
    "relational_communion",
    "information_structure",
    "learner_contingency",
)

RUBRIC_VERSION = "theory_grounded_character_v1"

RUBRIC = """You are a behavioral coder studying AI tutors. Code only what each candidate DOES in this response given the supplied educational context. Candidate identities and prompt-arm labels are hidden. Do not infer vendor identity. Do not judge correctness, overall quality, verbosity, or whether the teaching choice is desirable. Use the full 1-5 range and apply the anchors literally.

Dimensions (higher is descriptive, not automatically better):

- instructional_agency — who controls the learner's next cognitive move, independent of how much answer content is revealed.
  1 = learner-led: invites the learner to choose a path, formulate an explanation, or decide the next move.
  2 = mostly learner-led, with a bounded tutor suggestion.
  3 = shared control: the tutor proposes a specific move but leaves meaningful reasoning to the learner.
  4 = mostly tutor-led: prescribes the next operation, sequence, or reasoning path with little learner choice.
  5 = tutor-controlled: dictates the path and performs or commands the cognitive moves; learner input is not meaningfully solicited.

- relational_communion — interpersonal affiliation, independent of politeness, correctness, and amount of explanation.
  1 = distant or impersonal; purely transactional and may be curt.
  2 = neutral-professional with no meaningful affiliation.
  3 = mildly affiliative: brief acknowledgement, encouragement, or respectful validation.
  4 = clearly warm and supportive, acknowledging effort, emotion, or perspective.
  5 = strongly relational: sustained empathy, encouragement, rapport, or partnership language grounded in the learner's situation.
  Mere greetings, "please", or generic politeness do not by themselves score above 2.

- information_structure — organization and next-step actionability, independent of response length and answer reveal.
  1 = fragmented, ambiguous, internally disordered, or gives no usable next step.
  2 = partly understandable but poorly sequenced or underspecified.
  3 = coherent and usable, with an identifiable next move but limited explicit organization.
  4 = clearly sequenced or chunked, with an explicit actionable next step.
  5 = exceptionally well organized: dependencies, sequence, and immediate action are explicit without contradictory branches.
  A short response can score 5 and a long response can score 1.

- learner_contingency — how specifically the teaching move responds to evidence about this learner, not merely to the subject matter.
  1 = generic response reusable for almost any learner facing the topic.
  2 = reacts only to the current question or answer, without using evidence about the learner's reasoning or state.
  3 = uses a specific detail of the learner's current reasoning, error, request, or expressed need.
  4 = adapts the teaching move to multiple or strong pieces of learner-state evidence.
  5 = explicitly integrates learner history, prior performance, recurring misconception, affect, or preference into the selected teaching strategy.
  Mentioning topic details or restating the learner's words without changing the teaching move is not contingency.

Return JSON only, exactly this shape:
{"candidates":{"A":{"instructional_agency":1,"relational_communion":1,"information_structure":1,"learner_contingency":1},"B":{}} ,"confidence":1}

Include every supplied candidate label. Every dimension and confidence must be an integer from 1 to 5. Do not add prose or correctness scores."""

STRUCTURE_RUBRIC_VERSION = "information_structure_facets_v1"
STRUCTURE_DIMENSIONS = ("information_sequencing", "next_step_actionability")
STRUCTURE_RUBRIC = """You are a behavioral coder studying how AI tutors organize information. Code only what each candidate DOES in this response given the supplied educational context. Candidate identities and prompt-arm labels are hidden. Do not infer vendor identity. Do not judge correctness, warmth, verbosity, answer reveal, or whether the tutor or learner controls the move. Use the full 1-5 range and keep the two dimensions separate.

- information_sequencing — whether ideas and dependencies are presented in a comprehensible order.
  1 = fragmented, contradictory, or unordered; dependencies are unusable.
  2 = partly coherent but important order or dependency is unclear.
  3 = coherent local flow, although the order is mostly implicit.
  4 = clearly ordered or chunked; prerequisite-to-next-step progression is visible.
  5 = exceptionally explicit sequencing: dependencies, branch conditions, and order are unambiguous.
  Length, bullets, and number of facts do not determine the score.

- next_step_actionability — whether the learner can identify and execute the immediate next action.
  1 = no usable next action, or only vague advice.
  2 = a broad direction is present but the learner must guess what to do now.
  3 = an identifiable next move is stated, but inputs, operation, or expected output remain partly implicit.
  4 = one concrete and executable next action is clear.
  5 = the immediate action, relevant input, and expected intermediate output/check are all explicit.
  A question can be actionable and an explanation can be non-actionable. Do not score tutor control or answer reveal.

Return JSON only, exactly this shape:
{"candidates":{"A":{"information_sequencing":1,"next_step_actionability":1},"B":{}} ,"confidence":1}

Include every supplied candidate label. Every dimension and confidence must be an integer from 1 to 5. Do not add prose or correctness scores."""

CONFIRMATORY_RUBRIC_VERSION = "educational_character_confirmatory_v1"
CONFIRMATORY_DIMENSIONS = (
    "instructional_agency",
    "relational_communion",
    "next_step_actionability",
)
CONFIRMATORY_RUBRIC = """You are a behavioral coder studying AI tutors. Code only what each candidate DOES in this response given the supplied educational context. Candidate identities and prompt-arm labels are hidden. Do not infer vendor identity. Do not judge correctness, overall quality, verbosity, or whether the teaching choice is desirable. Use the full 1-5 range and keep the dimensions separate.

- instructional_agency — who controls the learner's next cognitive move, independent of how much answer content is revealed.
  1 = learner-led: invites the learner to choose a path, formulate an explanation, or decide the next move.
  2 = mostly learner-led, with a bounded tutor suggestion.
  3 = shared control: the tutor proposes a specific move but leaves meaningful reasoning to the learner.
  4 = mostly tutor-led: prescribes the next operation, sequence, or reasoning path with little learner choice.
  5 = tutor-controlled: dictates the path and performs or commands the cognitive moves; learner input is not meaningfully solicited.

- relational_communion — interpersonal affiliation, independent of politeness, correctness, and amount of explanation.
  1 = distant or impersonal; purely transactional and may be curt.
  2 = neutral-professional with no meaningful affiliation.
  3 = mildly affiliative: brief acknowledgement, encouragement, or respectful validation.
  4 = clearly warm and supportive, acknowledging effort, emotion, or perspective.
  5 = strongly relational: sustained empathy, encouragement, rapport, or partnership language grounded in the learner's situation.
  Mere greetings, "please", or generic politeness do not by themselves score above 2.

- next_step_actionability — whether the learner can identify and execute the immediate next action, independent of tutor control and answer reveal.
  1 = no usable next action, or only vague advice.
  2 = a broad direction is present but the learner must guess what to do now.
  3 = an identifiable next move is stated, but inputs, operation, or expected output remain partly implicit.
  4 = one concrete and executable next action is clear.
  5 = the immediate action, relevant input, and expected intermediate output/check are all explicit.
  A question can be actionable and an explanation can be non-actionable.

Return JSON only, exactly this shape:
{"candidates":{"A":{"instructional_agency":1,"relational_communion":1,"next_step_actionability":1},"B":{}} ,"confidence":1}

Include every supplied candidate label. Every dimension and confidence must be an integer from 1 to 5. Do not add prose or correctness scores."""

RUBRIC_SPECS = {
    RUBRIC_VERSION: (DIMENSIONS, RUBRIC),
    STRUCTURE_RUBRIC_VERSION: (STRUCTURE_DIMENSIONS, STRUCTURE_RUBRIC),
    CONFIRMATORY_RUBRIC_VERSION: (CONFIRMATORY_DIMENSIONS, CONFIRMATORY_RUBRIC),
}


def build_prompt(batch: dict[str, Any], order: list[str]) -> tuple[str, dict[str, str]]:
    labels = [chr(ord("A") + i) for i in range(len(order))]
    mapping = dict(zip(labels, order))
    candidates = "\n\n".join(
        f"[Candidate {label}]\n{batch['responses'][model]}" for label, model in mapping.items()
    )
    prompt = f"{RUBRIC}\n\n[Educational context and instruction]\n{batch['context']}\n\n{candidates}"
    return prompt, mapping


def validate_annotation(value: dict[str, Any], labels: list[str]) -> bool:
    candidates = value.get("candidates")
    if not isinstance(candidates, dict) or set(candidates) != set(labels):
        return False
    for label in labels:
        scores = candidates[label]
        if not isinstance(scores, dict) or set(scores) != set(DIMENSIONS):
            return False
        if any(not isinstance(scores[d], int) or not 1 <= scores[d] <= 5 for d in DIMENSIONS):
            return False
    confidence = value.get("confidence")
    return isinstance(confidence, int) and 1 <= confidence <= 5


def annotate_one(
    client: Any, judge: str, seed: int, batch: dict[str, Any], retries: int,
    max_tokens: int | None,
) -> dict[str, Any]:
    order = candidate_order(seed, judge, batch)
    prompt, mapping = build_prompt(batch, order)
    error = ""
    raw = ""
    usage: dict[str, Any] = {}
    parsed: dict[str, Any] = {}
    transport = "stream"
    prefer_nonstream = False
    for attempt in range(1, retries + 1):
        try:
            client.reset_usage_window()
            transport = "nonstream" if prefer_nonstream else "stream"
            raw = client.chat(
                [{"role": "user", "content": prompt}],
                model=judge,
                max_tokens=max_tokens,
                stream=not prefer_nonstream,
            )
            usage = client.read_usage_window()
            parsed = parse_json_object(raw)
            if validate_annotation(parsed, list(mapping)):
                row = result_row(
                    batch, judge, mapping, prompt, raw, parsed, usage, attempt, "", transport,
                )
                row["rubric_version"] = RUBRIC_VERSION
                row["split"] = batch["split"]
                return row
            if not raw.strip():
                error = "empty judge response"
                prefer_nonstream = True
            else:
                error = "invalid annotation JSON"
        except Exception as exc:  # noqa: BLE001
            error = str(exc)[:500]
        time.sleep(min(8, attempt * 2))
    row = result_row(
        batch, judge, mapping, prompt, raw, parsed, usage, retries, error, transport,
    )
    row["rubric_version"] = RUBRIC_VERSION
    row["split"] = batch["split"]
    return row


def assign_splits(
    batches: list[dict[str, Any]], seed: int, pilot_per_benchmark: int,
) -> list[dict[str, Any]]:
    """Assign whole prompt pairs to pilot or formal strata.

    ``pair_group`` is a benchmark name for unpaired tasks and a shared task name
    for generic/pedagogy arms.  Ranking ``pair_id`` within that group guarantees
    that both prompt arms of the same educational context stay in one split.
    """
    by_group: dict[str, list[dict[str, Any]]] = {}
    for batch in batches:
        by_group.setdefault(batch["pair_group"], []).append(batch)
    assigned: list[dict[str, Any]] = []
    for pair_group, rows in sorted(by_group.items()):
        pair_ids = sorted(
            {str(row["pair_id"]) for row in rows},
            key=lambda pair_id: hashlib.sha256(
                f"{seed}|theory-pilot|{pair_group}|{pair_id}".encode()
            ).hexdigest(),
        )
        pilot_ids = set(pair_ids[:pilot_per_benchmark])
        for row in rows:
            copy = dict(row)
            copy["split"] = "pilot" if str(row["pair_id"]) in pilot_ids else "formal"
            assigned.append(copy)
    return sorted(assigned, key=lambda row: (row["benchmark"], row["item_id"]))


def main() -> None:
    global DIMENSIONS, RUBRIC, RUBRIC_VERSION

    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--edubenchmark-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--judges", default="MiniMax-M3,glm-5.2,deepseek-v4-pro")
    parser.add_argument("--rubric-version", choices=tuple(RUBRIC_SPECS), default=RUBRIC_VERSION)
    parser.add_argument("--seed", type=int, default=20260826)
    parser.add_argument("--pilot-per-benchmark", type=int, default=6)
    parser.add_argument("--longtutor", type=int, default=40)
    parser.add_argument("--mathdial", type=int, default=80)
    parser.add_argument("--mathdial-hard", type=int, default=40)
    parser.add_argument("--socratic", type=int, default=80)
    parser.add_argument("--run-split", choices=("pilot", "formal", "all"), default="pilot")
    parser.add_argument(
        "--run-benchmarks", default="",
        help="Optional comma-separated benchmark allow-list for execution; the manifest remains complete",
    )
    parser.add_argument(
        "--max-batches", type=int, default=0,
        help="Deterministically cap execution batches for a transport/schema smoke test",
    )
    parser.add_argument("--minimax-concurrency", type=int, default=4)
    parser.add_argument("--gateway-concurrency", type=int, default=8)
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument(
        "--max-output-tokens", type=int, default=0,
        help="Visible-output budget; 0 leaves reasoning-capable judges uncapped",
    )
    parser.add_argument(
        "--force-gateway", action="store_true",
        help="Route every judge through the configured local API Gateway",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    DIMENSIONS, RUBRIC = RUBRIC_SPECS[args.rubric_version]
    RUBRIC_VERSION = args.rubric_version

    sys.path.insert(0, str(args.edubenchmark_root.resolve()))
    inventory = load_json(args.inventory)
    counts = {
        "longtutor": args.longtutor,
        "mathdial": args.mathdial,
        "mathdial_hard": args.mathdial_hard,
        "socratic": args.socratic,
    }
    batches = assign_splits(
        build_batches(inventory, args.seed, counts, args.edubenchmark_root),
        args.seed,
        args.pilot_per_benchmark,
    )
    execution_batches = [
        batch for batch in batches if args.run_split == "all" or batch["split"] == args.run_split
    ]
    allowed_benchmarks = {
        benchmark.strip() for benchmark in args.run_benchmarks.split(",") if benchmark.strip()
    }
    if allowed_benchmarks:
        execution_batches = [
            batch for batch in execution_batches if batch["benchmark"] in allowed_benchmarks
        ]
    if args.max_batches > 0:
        execution_batches = execution_batches[: args.max_batches]
    judges = [judge.strip() for judge in args.judges.split(",") if judge.strip()]
    args.output_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "schema_version": 1,
        "rubric_version": RUBRIC_VERSION,
        "seed": args.seed,
        "pilot_pairs_per_group": args.pilot_per_benchmark,
        "counts": counts,
        "judges": judges,
        "forced_provider": "gateway" if args.force_gateway else None,
        "batch_count": len(batches),
        "pilot_batch_count": sum(batch["split"] == "pilot" for batch in batches),
        "formal_batch_count": sum(batch["split"] == "formal" for batch in batches),
        "response_count": len(batches) * len(inventory["core_models"]),
        "items": [
            {key: batch[key] for key in ("benchmark", "item_id", "pair_group", "pair_id", "split")}
            for batch in batches
        ],
    }
    (args.output_dir / "sample_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    audit = payload_audit(batches, judges)
    audit["rubric_version"] = RUBRIC_VERSION
    audit["split_counts"] = {
        "pilot": manifest["pilot_batch_count"],
        "formal": manifest["formal_batch_count"],
    }
    audit["execution_scope"] = {
        "run_split": args.run_split,
        "run_benchmarks": sorted(allowed_benchmarks),
        "execution_batch_count": len(execution_batches),
        "judge_call_count": len(execution_batches) * len(judges),
        "excluded_benchmarks": sorted(
            {batch["benchmark"] for batch in batches}
            - {batch["benchmark"] for batch in execution_batches}
        ),
    }
    audit["judges_and_routes"] = {
        judge: (
            "configured API gateway"
            if args.force_gateway or not judge.lower().startswith("minimax")
            else "MiniMax official API"
        )
        for judge in judges
    }
    (args.output_dir / "payload_audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "manifest_batches": len(batches),
        "execution_batches": len(execution_batches),
        "judge_calls": len(execution_batches) * len(judges),
        "judges": judges,
        "run_split": args.run_split,
        "run_benchmarks": sorted(allowed_benchmarks),
    }, ensure_ascii=False), flush=True)
    if args.dry_run:
        return

    state_dir = args.output_dir / "run_state"
    state_dir.mkdir(parents=True, exist_ok=True)
    lock_handle = (state_dir / "writer.lock").open("w", encoding="utf-8")
    try:
        fcntl.flock(lock_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as exc:
        raise SystemExit(f"another theory-grounded judge writer holds {state_dir / 'writer.lock'}") from exc
    (state_dir / "started").write_text(
        datetime.now(timezone.utc).isoformat() + "\n", encoding="utf-8"
    )
    for marker in ("finished", "exit"):
        path = state_dir / marker
        if path.exists():
            path.unlink()

    from scripts.eval.providers import build_client

    output_path = args.output_dir / "annotations.jsonl"
    done = completed_ids(output_path)
    with output_path.open("a", encoding="utf-8") as handle:
        for judge in judges:
            concurrency = args.minimax_concurrency if judge.lower().startswith("minimax") else args.gateway_concurrency
            pending = [
                batch for batch in execution_batches
                if f"{batch['benchmark']}|{batch['item_id']}|{judge}" not in done
            ]
            thread_state = threading.local()

            def annotate_with_thread_client(batch: dict[str, Any]) -> dict[str, Any]:
                if not hasattr(thread_state, "client"):
                    thread_state.client = build_client(
                        judge,
                        timeout=args.timeout,
                        provider="gateway" if args.force_gateway else None,
                    )
                return annotate_one(
                    thread_state.client, judge, args.seed, batch, args.retries,
                    args.max_output_tokens or None,
                )

            with ThreadPoolExecutor(max_workers=concurrency) as pool:
                futures = {pool.submit(annotate_with_thread_client, batch): batch for batch in pending}
                for future in as_completed(futures):
                    row = future.result()
                    handle.write(json.dumps(row, ensure_ascii=False) + "\n")
                    handle.flush()
                    print(json.dumps({
                        "annotation_id": row["annotation_id"],
                        "split": row["split"],
                        "ok": not bool(row["error"]),
                        "error": row["error"],
                    }, ensure_ascii=False), flush=True)

    (state_dir / "exit").write_text("0\n", encoding="utf-8")
    (state_dir / "finished").write_text(
        datetime.now(timezone.utc).isoformat() + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
