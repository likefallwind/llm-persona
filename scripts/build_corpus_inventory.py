#!/usr/bin/env python3
"""Inventory paired EduBenchmark model-response runs without loading them at once."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Any


CORE_MODELS = (
    "minimax-m3",
    "minimax-m2.7",
    "glm-5.2",
    "deepseek-v4-pro",
    "doubao-seed-2.0-pro",
    "qwen3.5-4b",
)
OPTIONAL_MODELS = ("doubao-seed-2.0-lite",)
EXTENDED_MODELS = CORE_MODELS + (
    "doubao-seed-2.0-lite",
    "deepseek-v4-flash",
    "qwen3.8-27b",
)

ALIASES = {
    "minimax3": "minimax-m3",
    "minimax-m3": "minimax-m3",
    "minimax-m2.7": "minimax-m2.7",
    "glm-5.2": "glm-5.2",
    "deepseek-v4-pro": "deepseek-v4-pro",
    "doubao-seed-2.0-pro": "doubao-seed-2.0-pro",
    "doubao-seed-2-0-pro-260215": "doubao-seed-2.0-pro",
    "doubao-seed-2.0-lite": "doubao-seed-2.0-lite",
    "qwen-qwen3.5-4b": "qwen3.5-4b",
    "qwen-qwen3.8-27b": "qwen3.8-27b",
    "deepseek-v4-flash": "deepseek-v4-flash",
}


def canonical_model(directory_name: str) -> str | None:
    return ALIASES.get(directory_name.casefold())


def load_summary(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with path.open(encoding="utf-8") as handle:
            value = json.load(handle)
        return value if isinstance(value, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def as_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return int(value)
    return None


def scan_predictions(path: Path) -> tuple[dict[str, Any], set[str]]:
    latest: dict[str, tuple[bool, int, int]] = {}
    malformed = 0
    rows = 0
    missing_item_id = 0

    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if not line.strip():
                continue
            rows += 1
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                malformed += 1
                continue
            item_id = row.get("item_id")
            if item_id is None or str(item_id) == "":
                missing_item_id += 1
                continue
            response = row.get("response")
            response_text = response if isinstance(response, str) else ""
            reasoning = row.get("reasoning")
            reasoning_text = reasoning if isinstance(reasoning, str) else ""
            error = row.get("error")
            success = bool(response_text.strip()) and not bool(error)
            latest[str(item_id)] = (success, len(response_text), len(reasoning_text))

    successful = {item_id for item_id, values in latest.items() if values[0]}
    response_lengths = [values[1] for values in latest.values() if values[0]]
    reasoning_lengths = [values[2] for values in latest.values() if values[0]]
    stats = {
        "rows": rows,
        "unique_items": len(latest),
        "duplicate_rows": max(0, rows - malformed - missing_item_id - len(latest)),
        "successful_unique_items": len(successful),
        "failed_unique_items": len(latest) - len(successful),
        "malformed_rows": malformed,
        "missing_item_id_rows": missing_item_id,
        "response_chars": sum(response_lengths),
        "median_response_chars": median(response_lengths) if response_lengths else 0,
        "reasoning_chars": sum(reasoning_lengths),
        "items_with_reasoning": sum(length > 0 for length in reasoning_lengths),
    }
    return stats, successful


def choose_run(existing: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    """Prefer the run with more successful unique items, then an explicit summary."""
    existing_key = (
        existing["prediction_stats"]["successful_unique_items"],
        existing["summary_exists"],
    )
    candidate_key = (
        candidate["prediction_stats"]["successful_unique_items"],
        candidate["summary_exists"],
    )
    return candidate if candidate_key > existing_key else existing


def build_inventory(eval_root: Path) -> dict[str, Any]:
    eval_root = eval_root.resolve()
    edubenchmark_root = eval_root.parent.parent
    runs: list[dict[str, Any]] = []
    successful_sets: dict[tuple[str, str, str], set[str]] = {}

    for benchmark_dir in sorted(eval_root.iterdir()):
        if not benchmark_dir.is_dir() or benchmark_dir.name.startswith("_"):
            continue
        for model_dir in sorted(benchmark_dir.iterdir()):
            if not model_dir.is_dir() or model_dir.name.startswith("_"):
                continue
            model = canonical_model(model_dir.name)
            predictions = model_dir / "predictions.jsonl"
            if model is None or not predictions.exists():
                continue
            stats, successful = scan_predictions(predictions)
            summary_path = model_dir / "summary.json"
            summary = load_summary(summary_path)
            run = {
                "benchmark": benchmark_dir.name,
                "model": model,
                "source_model_dir": model_dir.name,
                "predictions_path": str(predictions.relative_to(edubenchmark_root)),
                "predictions_bytes": predictions.stat().st_size,
                "summary_path": str(summary_path.relative_to(edubenchmark_root)) if summary_path.exists() else None,
                "summary_exists": summary_path.exists(),
                "summary_total_items": as_int(summary.get("total_items")),
                "summary_scored": as_int(summary.get("scored")),
                "summary_run_status": summary.get("run_status"),
                "summary_prompt_version": (
                    summary.get("extra_metrics", {}).get("audit", {}).get("prompt_version")
                    if isinstance(summary.get("extra_metrics"), dict)
                    else None
                ),
                "prediction_stats": stats,
            }
            runs.append(run)
            successful_sets[(benchmark_dir.name, model, model_dir.name)] = successful

    selected: dict[tuple[str, str], dict[str, Any]] = {}
    for run in runs:
        key = (run["benchmark"], run["model"])
        selected[key] = choose_run(selected[key], run) if key in selected else run

    benchmarks: list[dict[str, Any]] = []
    by_benchmark: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for run in selected.values():
        by_benchmark[run["benchmark"]].append(run)

    for benchmark, benchmark_runs in sorted(by_benchmark.items()):
        model_runs = {run["model"]: run for run in benchmark_runs}
        models_present = sorted(model_runs)
        sets = {
            model: successful_sets[(benchmark, model, run["source_model_dir"])]
            for model, run in model_runs.items()
        }
        common_present = set.intersection(*(sets[m] for m in models_present)) if sets else set()
        has_core_six = all(model in sets for model in CORE_MODELS)
        common_core = (
            set.intersection(*(sets[model] for model in CORE_MODELS)) if has_core_six else set()
        )
        benchmarks.append(
            {
                "benchmark": benchmark,
                "models_present": models_present,
                "model_count": len(models_present),
                "has_core_six": has_core_six,
                "common_success_items_present_models": len(common_present),
                "common_success_items_core_six": len(common_core),
                "per_model_successful_items": {
                    model: model_runs[model]["prediction_stats"]["successful_unique_items"]
                    for model in models_present
                },
            }
        )

    return {
        "schema_version": 2,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "path_base": "EDUBENCH_ROOT",
        "eval_root": str(eval_root.relative_to(edubenchmark_root)),
        "core_models": list(CORE_MODELS),
        "optional_models": list(OPTIONAL_MODELS),
        "extended_models": list(EXTENDED_MODELS),
        "run_count": len(runs),
        "selected_run_count": len(selected),
        "benchmarks": benchmarks,
        "selected_runs": sorted(selected.values(), key=lambda x: (x["benchmark"], x["model"])),
    }


def render_markdown(inventory: dict[str, Any]) -> str:
    rows = [
        "# Corpus inventory",
        "",
        f"Generated: `{inventory['generated_at']}`",
        "",
        "The paired count is the intersection of successful item IDs across the six",
        "core models. Runs with zero paired items are not usable for paired analysis.",
        "",
        "| Benchmark | Core six | Paired successful items | Models present |",
        "|---|---:|---:|---|",
    ]
    for benchmark in inventory["benchmarks"]:
        rows.append(
            "| {benchmark} | {core} | {paired:,} | {models} |".format(
                benchmark=benchmark["benchmark"],
                core="yes" if benchmark["has_core_six"] else "no",
                paired=benchmark["common_success_items_core_six"],
                models=", ".join(benchmark["models_present"]),
            )
        )
    core_benchmarks = [b for b in inventory["benchmarks"] if b["has_core_six"]]
    total_pairs = sum(b["common_success_items_core_six"] for b in core_benchmarks)
    rows.extend(
        [
            "",
            "## Core-six paired panel",
            "",
            f"- Benchmarks with all six models: **{len(core_benchmarks)}**",
            f"- Successful benchmark-item pairs: **{total_pairs:,}**",
            f"- Paired model responses: **{total_pairs * len(CORE_MODELS):,}**",
            "",
        ]
    )
    return "\n".join(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--eval-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    inventory = build_inventory(args.eval_root.resolve())
    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / "corpus_inventory.json"
    markdown_path = args.output_dir / "corpus_inventory.md"
    json_path.write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown(inventory), encoding="utf-8")
    print(markdown_path)


if __name__ == "__main__":
    main()
