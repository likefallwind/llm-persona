#!/usr/bin/env python3
"""Report exclusion-free completion status for the factorial prompt panel."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def latest_rows(path: Path) -> dict[tuple[str, str], dict[str, Any]]:
    latest: dict[tuple[str, str], dict[str, Any]] = {}
    if not path.is_file():
        return latest
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            key = (str(row.get("sample_id", "")), str(row.get("model", "")))
            if all(key):
                latest[key] = row
    return latest


def status(spec: dict[str, Any], manifest_rows: list[dict[str, Any]], latest: dict[tuple[str, str], dict[str, Any]]) -> dict[str, Any]:
    expected_keys = {(row["sample_id"], model) for row in manifest_rows for model in spec["models"]}
    successful = {
        key for key, row in latest.items()
        if key in expected_keys and isinstance(row.get("response"), str)
        and row["response"].strip() and not row.get("error")
    }
    errors = {key for key, row in latest.items() if key in expected_keys and row.get("error")}
    per_model = {}
    for model in spec["models"]:
        model_expected = {key for key in expected_keys if key[1] == model}
        per_model[model] = {
            "expected": len(model_expected),
            "successful": len(model_expected & successful),
            "errors": len(model_expected & errors),
            "missing": len(model_expected - successful - errors),
        }
    return {
        "expected": len(expected_keys),
        "successful": len(successful),
        "current_errors": len(errors - successful),
        "missing": len(expected_keys - successful - errors),
        "unexpected_keys": len(set(latest) - expected_keys),
        "per_model": per_model,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, default=Path("data/factorial_prompt_spec_v1.json"))
    parser.add_argument("--manifest", type=Path, default=Path("artifacts/factorial_prompt_v1/sample_manifest.jsonl"))
    parser.add_argument("--responses", type=Path, default=Path("artifacts/factorial_prompt_v1/run/responses.jsonl"))
    parser.add_argument("--require-complete", action="store_true")
    args = parser.parse_args()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    manifest_rows = [json.loads(line) for line in args.manifest.read_text(encoding="utf-8").splitlines() if line]
    report = status(spec, manifest_rows, latest_rows(args.responses))
    print(json.dumps(report, indent=2, sort_keys=True))
    if args.require_complete and (
        report["successful"] != report["expected"] or report["current_errors"]
        or report["missing"] or report["unexpected_keys"]
    ):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
