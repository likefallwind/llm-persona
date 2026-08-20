#!/usr/bin/env python3
"""Generate the public outcome-independent factorial detector-validation plan."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def hash_rank(seed: int, panel: str, sample_id: str, model: str) -> str:
    return hashlib.sha256(f"{seed}|{panel}|{sample_id}|{model}".encode()).hexdigest()


def build_plan(root: Path, spec: dict) -> tuple[list[dict], list[dict]]:
    selected: list[dict] = []
    for panel, panel_spec in spec["panels"].items():
        manifest = {row["sample_id"]: row for row in load_jsonl(root / panel_spec["manifest"])}
        metrics = pd.read_csv(root / panel_spec["derived_metrics"], dtype={"sample_id": str})
        expected_columns = {"sample_id", "base_id", "model", "prompt_sha256", "response_sha256"}
        if not expected_columns <= set(metrics):
            raise RuntimeError(f"{panel} metrics missing {sorted(expected_columns - set(metrics))}")
        if metrics.duplicated(["sample_id", "model"]).any():
            raise RuntimeError(f"{panel} metrics contain duplicate sample/model rows")
        for (base_id, model), group in metrics.groupby(["base_id", "model"], sort=True):
            count = int(panel_spec["samples_per_base_model"])
            if len(group) != 16:
                raise RuntimeError(f"{panel}|{base_id}|{model} has {len(group)} rows, expected 16")
            ranked = sorted(
                group.to_dict("records"),
                key=lambda row: hash_rank(spec["seed"], panel, str(row["sample_id"]), str(model)),
            )[:count]
            for row in ranked:
                source = manifest[str(row["sample_id"])]
                selected.append({
                    "validation_id": f"{panel}|{row['sample_id']}|{model}",
                    "panel": panel,
                    "base_id": str(base_id),
                    "sample_id": str(row["sample_id"]),
                    "model": str(model),
                    "problem_family": source["problem_family"],
                    "prompt_sha256": str(row["prompt_sha256"]),
                    "response_sha256": str(row["response_sha256"]),
                })

    selected.sort(key=lambda row: (row["panel"], row["base_id"], row["validation_id"]))
    batches: list[dict] = []
    for (panel, base_id), group_frame in pd.DataFrame(selected).groupby(["panel", "base_id"], sort=True):
        group = group_frame.to_dict("records")
        ordered = sorted(
            group,
            key=lambda row: hashlib.sha256(
                f"{spec['seed']}|batch|{row['validation_id']}".encode()
            ).hexdigest(),
        )
        size = int(spec["batch_size"])
        if len(ordered) % size:
            raise RuntimeError(f"{panel}|{base_id} cannot be divided into batches of {size}")
        for part, start in enumerate(range(0, len(ordered), size), start=1):
            batch_rows = ordered[start : start + size]
            batches.append({
                "batch_id": f"{panel}|{base_id}|B{part:02d}",
                "panel": panel,
                "base_id": str(base_id),
                "validation_ids": [row["validation_id"] for row in batch_rows],
            })
    return selected, batches


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--spec", type=Path, default=Path("data/factorial_detector_validation_spec_v1.json"))
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/factorial_detector_validation_v1"))
    args = parser.parse_args()
    root = args.root.resolve()
    spec = json.loads((root / args.spec).read_text(encoding="utf-8"))
    selected, batches = build_plan(root, spec)
    output = root / args.output_dir
    write_jsonl(output / "sample_manifest.jsonl", selected)
    write_jsonl(output / "batch_plan.jsonl", batches)
    expected = spec["success_gate"]
    if len(selected) != expected["response_units"] or len(batches) != expected["batches"]:
        raise RuntimeError(
            f"plan mismatch: responses={len(selected)} batches={len(batches)} expected={expected}"
        )
    print(json.dumps({"response_units": len(selected), "batches": len(batches)}, sort_keys=True))


if __name__ == "__main__":
    main()
