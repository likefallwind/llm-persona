#!/usr/bin/env python3
"""Hash derived research artifacts and record the analysis environment."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
from pathlib import Path
import subprocess


PACKAGES = ("numpy", "pandas", "scipy", "scikit-learn", "statsmodels", "matplotlib", "seaborn")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_eligible_files(root: Path, includes: list[str]) -> list[Path]:
    """Return tracked or untracked-not-ignored files under the requested roots."""
    completed = subprocess.run(
        [
            "git", "-C", str(root), "ls-files", "--cached", "--others",
            "--exclude-standard", "-z", "--", *includes,
        ],
        check=True,
        capture_output=True,
    )
    relative_paths = [
        Path(raw.decode("utf-8", errors="surrogateescape"))
        for raw in completed.stdout.split(b"\0") if raw
    ]
    return sorted({(root / path).resolve() for path in relative_paths})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--include", nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    output = args.output.resolve()
    files = []
    for path in git_eligible_files(root, args.include):
        if path == output or not path.is_file():
            continue
        files.append({
            "path": str(path.relative_to(root)),
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
