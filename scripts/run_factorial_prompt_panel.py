#!/usr/bin/env python3
"""Run the frozen synthetic factorial policy panel against external models."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import fcntl
import hashlib
import json
from pathlib import Path
import sys
import threading
import time
from typing import Any


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def completed_keys(path: Path) -> set[tuple[str, str]]:
    if not path.is_file():
        return set()
    latest: dict[tuple[str, str], dict[str, Any]] = {}
    for row in load_jsonl(path):
        key = (str(row.get("sample_id", "")), str(row.get("model", "")))
        if all(key):
            latest[key] = row
    return {
        key for key, row in latest.items()
        if isinstance(row.get("response"), str) and row["response"].strip() and not row.get("error")
    }


def call_one(client: Any, model: str, sample: dict[str, Any], retries: int) -> dict[str, Any]:
    response = ""
    error = ""
    usage: dict[str, Any] = {}
    transport = "stream"
    nonstream = False
    for attempt in range(1, retries + 1):
        try:
            client.reset_usage_window()
            transport = "nonstream" if nonstream else "stream"
            response = client.chat(sample["messages"], model=model, max_tokens=None, stream=not nonstream)
            usage = client.read_usage_window()
            if response.strip():
                return result_row(sample, model, response, usage, attempt, "", transport)
            error = "empty response"
            nonstream = True
        except Exception as exc:  # noqa: BLE001
            error = str(exc)[:500]
        time.sleep(min(8, attempt * 2))
    return result_row(sample, model, response, usage, retries, error, transport)


def result_row(
    sample: dict[str, Any], model: str, response: str, usage: dict[str, Any],
    attempts: int, error: str, transport: str,
) -> dict[str, Any]:
    return {
        "request_id": f"{sample['sample_id']}|{model}",
        "sample_id": sample["sample_id"],
        "base_id": sample["base_id"],
        "problem_family": sample["problem_family"],
        "learner_need": sample["learner_need"],
        "question_policy": sample["question_policy"],
        "answer_policy": sample["answer_policy"],
        "tone_policy": sample["tone_policy"],
        "model": model,
        "prompt_sha256": sample["prompt_sha256"],
        "response": response,
        "response_sha256": hashlib.sha256(response.encode()).hexdigest() if response else "",
        "usage": usage,
        "attempts": attempts,
        "transport": transport,
        "error": error,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, default=Path("data/factorial_prompt_spec_v1.json"))
    parser.add_argument("--manifest", type=Path, default=Path("artifacts/factorial_prompt_v1/sample_manifest.jsonl"))
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/factorial_prompt_v1/run"))
    parser.add_argument("--edubenchmark-root", type=Path, default=Path("../edubenchmark"))
    parser.add_argument("--models", default="")
    parser.add_argument("--minimax-concurrency", type=int, default=4)
    parser.add_argument("--gateway-concurrency", type=int, default=8)
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    samples = load_jsonl(args.manifest)
    models = [x.strip() for x in args.models.split(",") if x.strip()] or list(spec["models"])
    unknown = sorted(set(models) - set(spec["models"]))
    if unknown:
        raise RuntimeError(f"models outside frozen spec: {unknown}")
    if args.limit:
        samples = samples[: args.limit]
    expected = len(samples) * len(models)
    print(json.dumps({
        "samples": len(samples), "models": models, "expected_calls": expected,
        "payload": "synthetic problem, synthetic learner work/request, frozen factor clauses",
        "routes": {
            "MiniMax-M3": "MiniMax official", "MiniMax-M2.7": "MiniMax official",
            "glm-5.2": "gateway", "deepseek-v4-pro": "gateway",
            "doubao-seed-2.0-lite": "gateway",
        },
    }, sort_keys=True), flush=True)
    if args.dry_run:
        return

    sys.path.insert(0, str(args.edubenchmark_root.resolve()))
    from scripts.eval.providers import build_client

    args.output_dir.mkdir(parents=True, exist_ok=True)
    output_path = args.output_dir / "responses.jsonl"
    lock_path = args.output_dir / "writer.lock"
    lock_handle = lock_path.open("a+")
    try:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as exc:
        raise RuntimeError(f"another writer holds {lock_path}") from exc

    done = completed_keys(output_path)
    with output_path.open("a", encoding="utf-8") as handle:
        for model in models:
            concurrency = args.minimax_concurrency if model.lower().startswith("minimax") else args.gateway_concurrency
            if concurrency > (4 if model.lower().startswith("minimax") else 8):
                raise RuntimeError(f"concurrency exceeds frozen provider cap for {model}")
            pending = [row for row in samples if (row["sample_id"], model) not in done]
            thread_state = threading.local()

            def run_sample(sample: dict[str, Any]) -> dict[str, Any]:
                if not hasattr(thread_state, "client"):
                    thread_state.client = build_client(model, timeout=args.timeout, temperature=0)
                return call_one(thread_state.client, model, sample, args.retries)

            with ThreadPoolExecutor(max_workers=concurrency) as pool:
                futures = {pool.submit(run_sample, sample): sample for sample in pending}
                for future in as_completed(futures):
                    row = future.result()
                    handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
                    handle.flush()
                    print(json.dumps({
                        "request_id": row["request_id"], "ok": not bool(row["error"]),
                        "error": row["error"],
                    }, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
