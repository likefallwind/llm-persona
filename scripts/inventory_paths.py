"""Resolve portable paths stored in the corpus inventory."""

from __future__ import annotations

import os
from pathlib import Path


def resolve_inventory_path(value: str, edubenchmark_root: Path | None = None) -> Path:
    path = Path(value)
    if path.is_absolute():
        # Backward compatibility for inventories created before schema v2.
        return path
    root = edubenchmark_root
    if root is None:
        configured = os.environ.get("EDUBENCH_ROOT")
        if not configured:
            raise RuntimeError(
                "portable inventory path requires EDUBENCH_ROOT or an explicit edubenchmark root"
            )
        root = Path(configured)
    return root / path
