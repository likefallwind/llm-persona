#!/usr/bin/env python3
"""Hash derived research artifacts and record the analysis environment."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
from pathlib import Path


PACKAGES = ("numpy", "pandas", "scipy", "scikit-learn", "statsmodels", "matplotlib", "seaborn")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--include", nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    files = []
    for relative in args.include:
        target = (args.root / relative).resolve()
        candidates = [target] if target.is_file() else sorted(path for path in target.rglob("*") if path.is_file())
        for path in candidates:
            if path == output or path.name == "finalize.log" or "run_state" in path.parts:
                continue
            files.append({
                "path": str(path.relative_to(args.root.resolve())),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            })
    manifest = {
        "schema_version": 1,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "packages": {package: importlib.metadata.version(package) for package in PACKAGES},
        "files": sorted(files, key=lambda row: row["path"]),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
