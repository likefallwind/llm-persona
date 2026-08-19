#!/usr/bin/env python3
"""Audit whether archived generations retain enough metadata for exact reruns."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd

from inventory_paths import resolve_inventory_path


GENERATION_FIELDS = (
    "temperature", "top_p", "top_k", "seed", "max_tokens", "max_new_tokens",
    "prompt_version", "model_version", "endpoint", "base_url", "provider",
    "decoding", "system_prompt",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def recursive_keys(value: Any) -> set[str]:
    keys: set[str] = set()
    stack = [value]
    while stack:
        current = stack.pop()
        if isinstance(current, dict):
            keys.update(str(key) for key in current)
            stack.extend(current.values())
        elif isinstance(current, list):
            stack.extend(current)
    return keys


def git_value(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args], check=False, capture_output=True, text=True
    )
    return result.stdout.strip() if result.returncode == 0 else "unavailable"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--roles", type=Path, required=True)
    parser.add_argument("--edubenchmark-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    inventory = json.loads(args.inventory.read_text(encoding="utf-8"))
    roles = json.loads(args.roles.read_text(encoding="utf-8"))
    relevant = set(roles["primary_behavior_generation"]) | set(roles["negative_controls"]) | set(roles["external_criteria"])
    core = set(inventory["core_models"])
    selected = [
        row for row in inventory["selected_runs"]
        if row["benchmark"] in relevant and row["model"] in core
    ]

    rows: list[dict[str, Any]] = []
    for run in selected:
        prediction_path = resolve_inventory_path(run["predictions_path"], args.edubenchmark_root)
        summary_path = resolve_inventory_path(run["summary_path"], args.edubenchmark_root)
        keys: set[str] = set()
        model_labels: Counter[str] = Counter()
        parsed_rows = 0
        if summary_path.is_file():
            keys |= recursive_keys(json.loads(summary_path.read_text(encoding="utf-8")))
        with prediction_path.open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                parsed_rows += 1
                if parsed_rows <= 50:
                    keys |= recursive_keys(record)
                    if record.get("model"):
                        model_labels[str(record["model"])] += 1
                if parsed_rows >= 50:
                    break
        present = sorted(field for field in GENERATION_FIELDS if field in keys)
        missing = sorted(field for field in GENERATION_FIELDS if field not in keys)
        rows.append({
            "benchmark": run["benchmark"],
            "role_section": next(section for section in ("primary_behavior_generation", "negative_controls", "external_criteria") if run["benchmark"] in roles[section]),
            "model": run["model"],
            "prediction_file": str(prediction_path.relative_to(args.edubenchmark_root)),
            "prediction_sha256": sha256(prediction_path),
            "prediction_bytes": prediction_path.stat().st_size,
            "summary_file": str(summary_path.relative_to(args.edubenchmark_root)),
            "summary_sha256": sha256(summary_path),
            "successful_unique_items": run["prediction_stats"]["successful_unique_items"],
            "recorded_model_labels": "|".join(sorted(model_labels)),
            "generation_fields_present": "|".join(present),
            "generation_fields_missing": "|".join(missing),
            "exact_generation_settings_recoverable": all(field in keys for field in ("temperature", "seed", "prompt_version")),
        })

    frame = pd.DataFrame(rows).sort_values(["role_section", "benchmark", "model"])
    args.output_dir.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.output_dir / "run_provenance.csv", index=False)
    coverage = {
        field: int(frame["generation_fields_present"].str.split("|").apply(lambda values: field in values).sum())
        for field in GENERATION_FIELDS
    }
    report = [
        "# Archived generation provenance audit", "",
        f"Audited **{len(frame)}** core-panel benchmark/model runs across primary tutoring, negative controls, and external criteria.", "",
        f"EduBenchmark checkout commit: `{git_value(args.edubenchmark_root, 'rev-parse', 'HEAD')}`.",
        f"EduBenchmark working tree entries at audit time: **{len(git_value(args.edubenchmark_root, 'status', '--porcelain').splitlines())}**.", "",
        "Every prediction and summary file is pinned by SHA-256 in `run_provenance.csv`.  Item IDs, response bytes, model labels, and usage are available for analysis, but hashes do not reconstruct provider-side settings that were never stored.", "",
        "## Generation metadata coverage", "",
        "| Field | Runs recording field | Total runs |", "|---|---:|---:|",
    ]
    for field in GENERATION_FIELDS:
        report.append(f"| {field} | {coverage[field]} | {len(frame)} |")
    exact = int(frame["exact_generation_settings_recoverable"].sum())
    report.extend([
        "", "## Interpretation", "",
        f"Only **{exact}/{len(frame)}** runs record the minimum temperature + seed + prompt-version tuple used by this audit's strict exact-rerun definition.  Therefore the archive supports exact *analysis* reproduction from frozen response files, but not exact regeneration of every provider response.", "",
        "The shared EduBenchmark adapters and exact-item overlap strengthen comparability, while provider-side aliases, system prompts, backend revisions, and missing decoding metadata remain uncontrolled.  The paper must describe the panel as deployed configurations at the archived run, not immutable model weights or a clean architecture intervention.",
    ])
    (args.output_dir / "generation_provenance_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(args.output_dir / "generation_provenance_report.md")


if __name__ == "__main__":
    main()
