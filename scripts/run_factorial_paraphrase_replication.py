#!/usr/bin/env python3
"""Run the frozen two-wording factorial in model-specific balanced order."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import fcntl
import json
from pathlib import Path
import sys
import threading
from typing import Any

from factorial_prompt_status import latest_rows, status
from generate_factorial_paraphrase_replication import order_hash, stratum_key
from run_factorial_prompt_panel import call_one, completed_keys, load_jsonl


def planned_samples(
    samples: list[dict[str, Any]], plan: list[dict[str, Any]], model: str, seed: int,
) -> list[dict[str, Any]]:
    sample_map = {str(row["sample_id"]): row for row in samples}
    model_plan = sorted(
        (row for row in plan if row.get("model") == model),
        key=lambda row: int(row["queue_rank"]),
    )
    if [int(row["queue_rank"]) for row in model_plan] != list(range(len(samples))):
        raise RuntimeError(f"invalid frozen queue ranks for {model}")
    if {str(row["sample_id"]) for row in model_plan} != set(sample_map):
        raise RuntimeError(f"frozen order-plan samples differ for {model}")
    for row in model_plan:
        block_index = int(row["queue_rank"]) // 32
        if int(row.get("block_index", -1)) != block_index:
            raise RuntimeError(f"frozen block index mismatch for {model}|{row['sample_id']}")
        sample = sample_map[str(row["sample_id"])]
        if row.get("stratum_key") != stratum_key(sample):
            raise RuntimeError(f"frozen stratum mismatch for {model}|{row['sample_id']}")
        expected_hash = order_hash(
            seed, model, f"block|{block_index}|{row['sample_id']}",
        )
        if row.get("order_sha256") != expected_hash:
            raise RuntimeError(f"frozen order hash mismatch for {model}|{row['sample_id']}")
    return [sample_map[str(row["sample_id"])] for row in model_plan]


def require_source_complete(report: dict[str, Any], name: str) -> None:
    if (
        report["successful"] != report["expected"]
        or report["current_errors"]
        or report["missing"]
        or report["unexpected_keys"]
    ):
        raise RuntimeError(
            f"{name} must be exactly complete before paraphrase replication: "
            + json.dumps(report, sort_keys=True)
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--spec", type=Path,
        default=Path("data/factorial_paraphrase_replication_spec_v1.json"),
    )
    parser.add_argument(
        "--manifest", type=Path,
        default=Path("artifacts/factorial_paraphrase_replication_v1/sample_manifest.jsonl"),
    )
    parser.add_argument(
        "--order-plan", type=Path,
        default=Path("artifacts/factorial_paraphrase_replication_v1/request_order_plan.jsonl"),
    )
    parser.add_argument(
        "--output-dir", type=Path,
        default=Path("artifacts/factorial_paraphrase_replication_v1/run"),
    )
    parser.add_argument("--parent-spec", type=Path, default=Path("data/factorial_prompt_spec_v1.json"))
    parser.add_argument(
        "--parent-manifest", type=Path,
        default=Path("artifacts/factorial_prompt_v1/sample_manifest.jsonl"),
    )
    parser.add_argument(
        "--parent-responses", type=Path,
        default=Path("artifacts/factorial_prompt_v1/run/responses.jsonl"),
    )
    parser.add_argument(
        "--order-spec", type=Path,
        default=Path("data/factorial_order_replication_spec_v1.json"),
    )
    parser.add_argument(
        "--order-manifest", type=Path,
        default=Path("artifacts/factorial_order_replication_v1/sample_manifest.jsonl"),
    )
    parser.add_argument(
        "--order-responses", type=Path,
        default=Path("artifacts/factorial_order_replication_v1/run/responses.jsonl"),
    )
    parser.add_argument("--edubenchmark-root", type=Path, default=Path("../edubenchmark"))
    parser.add_argument("--minimax-concurrency", type=int, default=4)
    parser.add_argument("--gateway-concurrency", type=int, default=8)
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    samples = load_jsonl(args.manifest)
    plan = load_jsonl(args.order_plan)
    models = list(spec["models"])
    expected = int(spec["success_gate"]["required_complete_cells"])
    seed = int(spec["order_seed"])
    if len(samples) * len(models) != expected:
        raise RuntimeError(f"call count mismatch: {len(samples) * len(models)} != {expected}")
    for model in models:
        planned_samples(samples, plan, model, seed)
    print(json.dumps({
        "samples": len(samples),
        "models": models,
        "expected_calls": expected,
        "order": "model-specific SHA-256 order in exact 32-stratum blocks",
        "payload": "synthetic contexts and frozen paraphrased policy clauses only",
    }, sort_keys=True), flush=True)
    if args.dry_run:
        return

    parent_report = status(
        json.loads(args.parent_spec.read_text(encoding="utf-8")),
        load_jsonl(args.parent_manifest), latest_rows(args.parent_responses),
    )
    require_source_complete(parent_report, "parent factorial")
    order_report = status(
        json.loads(args.order_spec.read_text(encoding="utf-8")),
        load_jsonl(args.order_manifest), latest_rows(args.order_responses),
    )
    require_source_complete(order_report, "order replication")

    sys.path.insert(0, str(args.edubenchmark_root.resolve()))
    from scripts.eval.providers import build_client

    args.output_dir.mkdir(parents=True, exist_ok=True)
    output_path = args.output_dir / "responses.jsonl"
    lock_handle = (args.output_dir / "writer.lock").open("a+")
    try:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as exc:
        raise RuntimeError("another writer holds the paraphrase output lock") from exc

    done = completed_keys(output_path)
    with output_path.open("a", encoding="utf-8") as handle:
        for model in models:
            concurrency = (
                args.minimax_concurrency if model.lower().startswith("minimax")
                else args.gateway_concurrency
            )
            cap = 4 if model.lower().startswith("minimax") else 8
            if concurrency > cap:
                raise RuntimeError(f"concurrency exceeds frozen provider cap for {model}")
            ordered = planned_samples(samples, plan, model, seed)
            pending = [sample for sample in ordered if (sample["sample_id"], model) not in done]
            rank = {sample["sample_id"]: index for index, sample in enumerate(ordered)}
            thread_state = threading.local()

            def run_sample(sample: dict[str, Any]) -> dict[str, Any]:
                if not hasattr(thread_state, "client"):
                    thread_state.client = build_client(model, timeout=args.timeout, temperature=0)
                row = call_one(thread_state.client, model, sample, args.retries)
                row["wording_set"] = sample["wording_set"]
                row["paraphrase_order_seed"] = seed
                row["paraphrase_queue_rank"] = rank[sample["sample_id"]]
                return row

            with ThreadPoolExecutor(max_workers=concurrency) as pool:
                futures = [pool.submit(run_sample, sample) for sample in pending]
                for future in as_completed(futures):
                    row = future.result()
                    handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
                    handle.flush()
                    print(json.dumps({
                        "request_id": row["request_id"],
                        "queue_rank": row["paraphrase_queue_rank"],
                        "wording_set": row["wording_set"],
                        "ok": not bool(row["error"]),
                        "error": row["error"],
                    }, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
