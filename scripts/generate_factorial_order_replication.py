#!/usr/bin/env python3
"""Select the frozen parent prompts for the order-randomized replication."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


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
    selected = []
    for family in sorted(families):
        bases = sorted(families[family])
        for index in indices:
            if index < 0 or index >= len(bases):
                raise RuntimeError(f"base index {index} outside {family}: {len(bases)} bases")
            selected.append(bases[index])
    return selected


def build_subset(spec: dict[str, Any], parent_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    base_ids = selected_base_ids(
        parent_rows, [int(value) for value in spec["selected_base_indices_per_family"]],
    )
    subset = [row for row in parent_rows if row["base_id"] in set(base_ids)]
    expected_bases = int(spec["expected_base_problems"])
    expected_samples = int(spec["expected_samples_per_model"])
    if len(set(base_ids)) != expected_bases or len(subset) != expected_samples:
        raise RuntimeError(
            f"replication selection mismatch: bases={len(set(base_ids))}/{expected_bases} "
            f"samples={len(subset)}/{expected_samples}"
        )
    if len({row["sample_id"] for row in subset}) != expected_samples:
        raise RuntimeError("duplicate replication sample IDs")
    return sorted(subset, key=lambda row: row["sample_id"])


def order_key(seed: int, model: str, sample_id: str) -> str:
    return hashlib.sha256(f"{seed}|{model}|{sample_id}".encode()).hexdigest()


def cell_key(row: dict[str, Any]) -> str:
    return "|".join(str(row[column]) for column in (
        "learner_need", "question_policy", "answer_policy", "tone_policy",
    ))


def build_order_plan(
    spec: dict[str, Any], subset: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    seed = int(spec["order_seed"])
    plan = []
    for model in spec["models"]:
        by_cell: dict[str, list[dict[str, Any]]] = {}
        for row in subset:
            by_cell.setdefault(cell_key(row), []).append(row)
        if len(by_cell) != 16 or {len(rows) for rows in by_cell.values()} != {8}:
            raise RuntimeError("replication must contain eight bases in every one of 16 cells")
        for key, rows in by_cell.items():
            by_cell[key] = sorted(
                rows,
                key=lambda row, cell=key: order_key(
                    seed, str(model), f"base|{cell}|{row['sample_id']}",
                ),
            )
        rank = 0
        for block_index in range(8):
            block = [by_cell[key][block_index] for key in sorted(by_cell)]
            block = sorted(
                block,
                key=lambda row, block_number=block_index: order_key(
                    seed, str(model), f"block|{block_number}|{row['sample_id']}",
                ),
            )
            for row in block:
                plan.append({
                    "model": model,
                    "queue_rank": rank,
                    "block_index": block_index,
                    "cell_key": cell_key(row),
                    "sample_id": row["sample_id"],
                    "order_sha256": order_key(
                        seed, str(model), f"block|{block_index}|{row['sample_id']}",
                    ),
                })
                rank += 1
    return plan


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--spec", type=Path, default=Path("data/factorial_order_replication_spec_v1.json"),
    )
    parser.add_argument(
        "--parent-manifest", type=Path,
        default=Path("artifacts/factorial_prompt_v1/sample_manifest.jsonl"),
    )
    parser.add_argument(
        "--output-dir", type=Path, default=Path("artifacts/factorial_order_replication_v1"),
    )
    args = parser.parse_args()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    subset = build_subset(spec, load_jsonl(args.parent_manifest))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output = args.output_dir / "sample_manifest.jsonl"
    output.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in subset),
        encoding="utf-8",
    )
    order_plan = build_order_plan(spec, subset)
    order_path = args.output_dir / "request_order_plan.jsonl"
    order_path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in order_plan),
        encoding="utf-8",
    )
    summary = {
        "schema_version": 1,
        "base_ids": sorted({row["base_id"] for row in subset}),
        "base_problem_count": len({row["base_id"] for row in subset}),
        "sample_count": len(subset),
        "model_count": len(spec["models"]),
        "expected_calls": len(subset) * len(spec["models"]),
        "manifest_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "order_plan_sha256": hashlib.sha256(order_path.read_bytes()).hexdigest(),
        "order_plan_rows": len(order_plan),
        "factorial_blocks_per_model": 8,
        "factorial_cells_per_block": 16,
        "exact_block_balance": all(
            len({row["cell_key"] for row in order_plan
                 if row["model"] == model and row["block_index"] == block}) == 16
            for model in spec["models"] for block in range(8)
        ),
        "parent_prompt_hashes_preserved": all(bool(row.get("prompt_sha256")) for row in subset),
        "payload_scope": "unchanged parent synthetic prompts only",
    }
    (args.output_dir / "design_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8",
    )
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
