#!/usr/bin/env python3
"""Run the frozen blind semantic coding protocol against local Ollama models.

Unlike the API runner, this process sends prompts only to 127.0.0.1. It is
resumable and stores ratings/hashes, not copies of upstream contexts or candidate
responses.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any

from run_semantic_judge import (
    DIMENSIONS,
    build_batches,
    build_prompt,
    candidate_order,
    completed_ids,
    load_json,
    parse_json_object,
    result_row,
    validate_annotation,
)


def json_schema(labels: list[str]) -> dict[str, Any]:
    score_object = {
        "type": "object",
        "properties": {name: {"type": "integer", "minimum": 1, "maximum": 5} for name in DIMENSIONS},
        "required": list(DIMENSIONS),
        "additionalProperties": False,
    }
    return {
        "type": "object",
        "properties": {
            "candidates": {
                "type": "object",
                "properties": {label: score_object for label in labels},
                "required": labels,
                "additionalProperties": False,
            },
            "confidence": {"type": "integer", "minimum": 1, "maximum": 5},
        },
        "required": ["candidates", "confidence"],
        "additionalProperties": False,
    }


def call_ollama(model: str, prompt: str, labels: list[str], timeout: int, num_ctx: int) -> tuple[str, dict[str, Any]]:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "think": False,
        "format": json_schema(labels),
        "options": {"temperature": 0, "num_ctx": num_ctx},
    }
    request = urllib.request.Request(
        "http://127.0.0.1:11434/api/chat",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = time.monotonic()
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = json.loads(response.read().decode("utf-8"))
    elapsed = time.monotonic() - started
    raw = str(body.get("message", {}).get("content", ""))
    usage = {
        "prompt_eval_count": body.get("prompt_eval_count"),
        "eval_count": body.get("eval_count"),
        "total_duration_ns": body.get("total_duration"),
        "load_duration_ns": body.get("load_duration"),
        "elapsed_seconds": elapsed,
    }
    return raw, usage


def annotate_local(
    model: str, seed: int, batch: dict[str, Any], retries: int, timeout: int, num_ctx: int,
) -> dict[str, Any]:
    judge = f"ollama/{model}"
    order = candidate_order(seed, judge, batch)
    prompt, mapping = build_prompt(batch, order)
    raw = ""
    parsed: dict[str, Any] = {}
    usage: dict[str, Any] = {}
    error = ""
    for attempt in range(1, retries + 1):
        try:
            raw, usage = call_ollama(model, prompt, list(mapping), timeout, num_ctx)
            parsed = parse_json_object(raw)
            if validate_annotation(parsed, list(mapping)):
                return result_row(batch, judge, mapping, prompt, raw, parsed, usage, attempt, "")
            error = "invalid annotation JSON"
        except Exception as exc:  # noqa: BLE001
            error = str(exc)[:500]
        time.sleep(min(8, 2 * attempt))
    return result_row(batch, judge, mapping, prompt, raw, parsed, usage, retries, error)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--edubenchmark-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--models", default="qwen3:8b,llama3.1:8b,mistral-nemo:12b")
    parser.add_argument("--benchmarks", default="", help="Optional comma-separated benchmark filter")
    parser.add_argument("--seed", type=int, default=20260819)
    parser.add_argument("--longtutor", type=int, default=40)
    parser.add_argument("--mathdial", type=int, default=80)
    parser.add_argument("--mathdial-hard", type=int, default=40)
    parser.add_argument("--socratic", type=int, default=80)
    parser.add_argument("--num-ctx", type=int, default=32768)
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--limit-batches", type=int, default=0, help="Smoke-test prefix; zero means the full frozen sample")
    args = parser.parse_args()

    sys.path.insert(0, str(args.edubenchmark_root.resolve()))
    inventory = load_json(args.inventory)
    counts = {
        "longtutor": args.longtutor,
        "mathdial": args.mathdial,
        "mathdial_hard": args.mathdial_hard,
        "socratic": args.socratic,
    }
    batches = build_batches(inventory, args.seed, counts)
    benchmark_filter = {value.strip() for value in args.benchmarks.split(",") if value.strip()}
    if benchmark_filter:
        batches = [batch for batch in batches if batch["benchmark"] in benchmark_filter]
    if args.limit_batches:
        batches = batches[: args.limit_batches]
    models = [value.strip() for value in args.models.split(",") if value.strip()]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output_path = args.output_dir / "annotations.jsonl"
    done = completed_ids(output_path)
    run_manifest = {
        "schema_version": 1,
        "route": "local Ollama at 127.0.0.1; no external API",
        "seed": args.seed,
        "counts": counts,
        "limit_batches": args.limit_batches,
        "selected_batch_count": len(batches),
        "judge_models": models,
        "benchmark_filter": sorted(benchmark_filter),
        "num_ctx": args.num_ctx,
        "items": [{k: b[k] for k in ("benchmark", "item_id", "pair_group", "pair_id")} for b in batches],
    }
    (args.output_dir / "run_manifest.json").write_text(
        json.dumps(run_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    with output_path.open("a", encoding="utf-8") as handle:
        for model in models:
            judge = f"ollama/{model}"
            for batch in batches:
                annotation_id = f"{batch['benchmark']}|{batch['item_id']}|{judge}"
                if annotation_id in done:
                    continue
                row = annotate_local(model, args.seed, batch, args.retries, args.timeout, args.num_ctx)
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
                handle.flush()
                print(json.dumps({
                    "annotation_id": annotation_id,
                    "ok": not bool(row["error"]),
                    "prompt_chars": row["prompt_chars"],
                    "elapsed_seconds": row.get("usage", {}).get("elapsed_seconds"),
                    "error": row["error"],
                }, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
