#!/usr/bin/env python3
"""Verify every path, byte count, and SHA-256 in a release manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify(root: Path, manifest_path: Path) -> list[str]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows = manifest.get("files")
    if not isinstance(rows, list):
        return ["manifest field 'files' is not a list"]

    failures: list[str] = []
    seen: set[str] = set()
    for row in rows:
        relative = row.get("path") if isinstance(row, dict) else None
        if not isinstance(relative, str):
            failures.append("manifest row has no string path")
            continue
        if relative in seen:
            failures.append(f"duplicate path: {relative}")
            continue
        seen.add(relative)
        path = (root / relative).resolve()
        try:
            path.relative_to(root)
        except ValueError:
            failures.append(f"path escapes root: {relative}")
            continue
        if not path.is_file():
            failures.append(f"missing file: {relative}")
            continue
        actual_bytes = path.stat().st_size
        if actual_bytes != row.get("bytes"):
            failures.append(
                f"byte mismatch: {relative} observed={actual_bytes} expected={row.get('bytes')}"
            )
        actual_hash = sha256(path)
        if actual_hash != row.get("sha256"):
            failures.append(f"sha256 mismatch: {relative}")
    return failures


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument(
        "--manifest", type=Path, default=Path("artifacts/reproducibility_manifest.json")
    )
    args = parser.parse_args()
    root = args.root.resolve()
    manifest = args.manifest if args.manifest.is_absolute() else root / args.manifest
    failures = verify(root, manifest)
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        raise SystemExit(f"reproducibility manifest verification failed: {len(failures)} issue(s)")
    count = len(json.loads(manifest.read_text(encoding="utf-8"))["files"])
    print(f"PASS: {count} manifest paths and hashes verified")


if __name__ == "__main__":
    main()
