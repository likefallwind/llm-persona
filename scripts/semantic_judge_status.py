#!/usr/bin/env python3
"""Summarize resumable semantic-judge coverage without reading source text."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    manifest_path = args.output_dir / "sample_manifest.json"
    annotation_path = args.output_dir / "annotations.jsonl"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    judges = ["MiniMax-M3", "glm-5.2", "deepseek-v4-pro"]
    latest: dict[str, dict[str, Any]] = {}
    raw_rows = 0
    invalid_json_rows = 0
    if annotation_path.exists():
        with annotation_path.open(encoding="utf-8", errors="replace") as handle:
            for line in handle:
                raw_rows += 1
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    invalid_json_rows += 1
                    continue
                annotation_id = str(row.get("annotation_id") or "")
                if annotation_id:
                    latest[annotation_id] = row

    rows = []
    errors: Counter[str] = Counter()
    for item in manifest["items"]:
        for judge in judges:
            annotation_id = f"{item['benchmark']}|{item['item_id']}|{judge}"
            record = latest.get(annotation_id)
            if record is None:
                status = "missing"
            elif record.get("annotation") and not record.get("error"):
                status = "success"
            else:
                status = "error"
                errors[str(record.get("error") or "unknown")[:160]] += 1
            rows.append({
                "benchmark": item["benchmark"],
                "judge": judge,
                "status": status,
                "confidence": (
                    record.get("annotation", {}).get("confidence")
                    if record and isinstance(record.get("annotation"), dict)
                    else None
                ),
            })
    frame = pd.DataFrame(rows)
    coverage = frame.groupby(["judge", "benchmark", "status"]).size().unstack(fill_value=0).reset_index()
    for status in ("success", "error", "missing"):
        if status not in coverage:
            coverage[status] = 0
    coverage["expected"] = coverage[["success", "error", "missing"]].sum(axis=1)
    coverage["success_rate"] = coverage["success"] / coverage["expected"]
    confidence = (
        frame[frame["status"] == "success"]
        .groupby("judge")["confidence"]
        .agg(["count", "mean", "median", "min", "max"])
        .reset_index()
    )
    overall = pd.DataFrame([{
        "manifest_batches": len(manifest["items"]),
        "expected_annotations": len(rows),
        "successful_annotations": int((frame["status"] == "success").sum()),
        "current_errors": int((frame["status"] == "error").sum()),
        "missing_annotations": int((frame["status"] == "missing").sum()),
        "raw_jsonl_rows": raw_rows,
        "superseded_retry_rows": max(0, raw_rows - len(latest)),
        "invalid_jsonl_rows": invalid_json_rows,
    }])
    args.output_dir.mkdir(parents=True, exist_ok=True)
    coverage.to_csv(args.output_dir / "coverage.csv", index=False)
    report = "\n".join([
        "# Semantic judge run status",
        "",
        overall.to_markdown(index=False),
        "",
        "## Coverage",
        "",
        coverage.to_markdown(index=False, floatfmt=".3f"),
        "",
        "## Confidence among successful annotations",
        "",
        confidence.to_markdown(index=False, floatfmt=".3f") if not confidence.empty else "No successful annotations yet.",
        "",
        "## Current error signatures",
        "",
        pd.DataFrame([{"count": count, "error": error} for error, count in errors.most_common()]).to_markdown(index=False)
        if errors else "No current errors.",
        "",
        "Only the latest row for each annotation ID determines status; earlier failed retry rows remain in the append-only JSONL for auditability.",
        "",
    ])
    (args.output_dir / "status_report.md").write_text(report, encoding="utf-8")
    print(overall.to_json(orient="records"))


if __name__ == "__main__":
    main()
