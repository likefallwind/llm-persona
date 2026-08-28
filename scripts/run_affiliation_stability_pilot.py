#!/usr/bin/env python3
"""Run the frozen affiliation pilot generator panel, resumably."""

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
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def completed(path: Path) -> set[tuple[str, str]]:
    if not path.exists():
        return set()
    latest = {(row.get("sample_id"), row.get("model")): row for row in load_jsonl(path)}
    return {key for key, row in latest.items() if row.get("response") and not row.get("error")}


def call(client: Any, model: str, sample: dict[str, Any], retries: int) -> dict[str, Any]:
    raw, error, usage, transport = "", "", {}, "stream"
    nonstream = False
    for attempt in range(1, retries + 1):
        try:
            client.reset_usage_window()
            transport = "nonstream" if nonstream else "stream"
            raw = client.chat(sample["messages"], model=model, max_tokens=None, stream=not nonstream)
            usage = client.read_usage_window()
            if raw.strip():
                error = ""
                break
            error = "empty response"
            nonstream = True
        except Exception as exc:  # noqa: BLE001
            error = str(exc)[:500]
        time.sleep(min(8, attempt * 2))
    return {
        "request_id": f"{sample['sample_id']}|{model}",
        "sample_id": sample["sample_id"],
        "condition": sample["condition"],
        "mode": sample["mode"],
        "item_id": sample["item_id"],
        "domain": sample["domain"],
        "model": model,
        "prompt_sha256": sample["prompt_sha256"],
        "response": raw,
        "response_sha256": hashlib.sha256(raw.encode()).hexdigest() if raw else "",
        "usage": usage,
        "attempts": attempt,
        "transport": transport,
        "error": error,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, default=Path("data/affiliation_stability_pilot_spec_v1.json"))
    parser.add_argument("--manifest", type=Path, default=Path("artifacts/affiliation_stability_pilot_v1/sample_manifest.jsonl"))
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/affiliation_stability_pilot_v1/run"))
    parser.add_argument("--edubenchmark-root", type=Path, default=Path("../edubenchmark"))
    parser.add_argument("--minimax-concurrency", type=int, default=4)
    parser.add_argument("--gateway-concurrency", type=int, default=8)
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--retries", type=int, default=3)
    args = parser.parse_args()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    samples = load_jsonl(args.manifest)
    print(json.dumps({"samples": len(samples), "models": spec["models"], "expected_calls": len(samples) * len(spec["models"])}, sort_keys=True), flush=True)

    sys.path.insert(0, str(args.edubenchmark_root.resolve()))
    from scripts.eval.providers import build_client

    args.output_dir.mkdir(parents=True, exist_ok=True)
    output = args.output_dir / "responses.jsonl"
    lock = (args.output_dir / "writer.lock").open("a+")
    try:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as exc:
        raise RuntimeError("another affiliation-pilot writer is active") from exc
    done = completed(output)
    with output.open("a", encoding="utf-8") as handle:
        for model in spec["models"]:
            workers = args.minimax_concurrency if model.lower().startswith("minimax") else args.gateway_concurrency
            if workers > (4 if model.lower().startswith("minimax") else 8):
                raise RuntimeError("provider concurrency cap exceeded")
            pending = [sample for sample in samples if (sample["sample_id"], model) not in done]
            state = threading.local()

            def run_one(sample: dict[str, Any]) -> dict[str, Any]:
                if not hasattr(state, "client"):
                    state.client = build_client(model, timeout=args.timeout, temperature=0)
                return call(state.client, model, sample, args.retries)

            with ThreadPoolExecutor(max_workers=workers) as pool:
                futures = [pool.submit(run_one, sample) for sample in pending]
                for future in as_completed(futures):
                    row = future.result()
                    handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
                    handle.flush()
                    print(json.dumps({"request_id": row["request_id"], "ok": not bool(row["error"]), "error": row["error"]}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
