"""Load and validate technical exclusions for the frozen semantic panel."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ItemKey = tuple[str, str]


def load_excluded_items(path: Path | None, manifest: dict[str, Any]) -> set[ItemKey]:
    if path is None:
        return set()
    specification = json.loads(path.read_text(encoding="utf-8"))
    if specification.get("schema_version") != 1:
        raise ValueError("semantic exclusion schema_version must equal 1")
    manifest_items = {
        (str(item["benchmark"]), str(item["item_id"]))
        for item in manifest["items"]
    }
    rows = specification.get("excluded_items")
    if not isinstance(rows, list) or not rows:
        raise ValueError("semantic exclusion file must contain excluded_items")
    excluded = {
        (str(item["benchmark"]), str(item["item_id"]))
        for item in rows
    }
    if len(excluded) != len(rows):
        raise ValueError("semantic exclusion file contains duplicate items")
    unknown = excluded - manifest_items
    if unknown:
        raise ValueError(f"semantic exclusions are absent from frozen manifest: {sorted(unknown)}")
    expected_manifest = specification.get("expected_manifest_batches")
    expected_analyzed = specification.get("expected_analyzed_batches")
    expected_annotations = specification.get("expected_analyzed_annotations")
    if expected_manifest != len(manifest_items):
        raise ValueError(
            f"frozen manifest drift: {len(manifest_items)} batches, expected {expected_manifest}"
        )
    analyzed = len(manifest_items) - len(excluded)
    if expected_analyzed != analyzed:
        raise ValueError(
            f"exclusion count drift: {analyzed} analyzed batches, expected {expected_analyzed}"
        )
    if expected_annotations != analyzed * 3:
        raise ValueError(
            f"annotation count drift: {analyzed * 3}, expected {expected_annotations}"
        )
    return excluded
