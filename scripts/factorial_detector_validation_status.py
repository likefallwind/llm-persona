#!/usr/bin/env python3
"""Report exact completion of the frozen factorial detector-validation panel."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from run_factorial_detector_validation import load_jsonl, valid_annotation


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--spec", type=Path, default=Path("data/factorial_detector_validation_spec_v1.json"))
    parser.add_argument("--batch-plan", type=Path, default=Path("artifacts/factorial_detector_validation_v1/batch_plan.jsonl"))
    parser.add_argument("--annotations", type=Path, default=Path("artifacts/factorial_detector_validation_v1/run/annotations.jsonl"))
    parser.add_argument("--require-complete", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    spec = json.loads((root / args.spec).read_text(encoding="utf-8"))
    batches = load_jsonl(root / args.batch_plan)
    expected = {
        f"{batch['batch_id']}|{judge}" for batch in batches for judge in spec["judges"]
    }
    latest = {}
    path = root / args.annotations
    if path.exists():
        for row in load_jsonl(path):
            annotation_id = str(row.get("annotation_id", ""))
            if annotation_id:
                latest[annotation_id] = row
    success = set()
    errors = set()
    per_judge = Counter()
    for annotation_id, row in latest.items():
        mapping = row.get("candidate_mapping") or {}
        if (
            annotation_id in expected
            and not row.get("error")
            and valid_annotation(row.get("annotation") or {}, list(mapping))
        ):
            success.add(annotation_id)
            per_judge[str(row.get("judge"))] += 1
        elif annotation_id in expected:
            errors.add(annotation_id)
    result = {
        "expected": len(expected),
        "successful": len(success),
        "current_errors": len(errors - success),
        "missing": len(expected - success),
        "unexpected_ids": len(set(latest) - expected),
        "per_judge": {
            judge: {
                "expected": len(batches),
                "successful": per_judge[judge],
                "missing": len(batches) - per_judge[judge],
            }
            for judge in spec["judges"]
        },
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    if args.require_complete and not (
        result["successful"] == len(expected)
        and result["current_errors"] == 0
        and result["missing"] == 0
        and result["unexpected_ids"] == 0
    ):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
