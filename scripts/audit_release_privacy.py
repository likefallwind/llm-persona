#!/usr/bin/env python3
"""Fail if Git-eligible research artifacts contain source-text fields or local paths."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
from pathlib import Path
from typing import Any


FORBIDDEN_FIELDS = {
    "response", "response_text", "raw_response", "raw_judge_response",
    "candidate_response", "prompt", "prompt_text", "context", "context_text",
    "source_text", "question_text", "conversation", "student_response",
    "teacher_response", "history_text",
}
TEXT_SUFFIXES = {".csv", ".json", ".jsonl", ".md", ".txt", ".log"}


def ignored_by_git(root: Path, path: Path) -> bool:
    result = subprocess.run(
        ["git", "-C", str(root), "check-ignore", "-q", str(path.relative_to(root))],
        check=False,
    )
    return result.returncode == 0


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


def json_keys(path: Path) -> set[str]:
    if path.suffix == ".jsonl":
        keys: set[str] = set()
        with path.open(encoding="utf-8", errors="replace") as handle:
            for line in handle:
                if line.strip():
                    keys |= recursive_keys(json.loads(line))
        return keys
    return recursive_keys(json.loads(path.read_text(encoding="utf-8")))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--artifact-dir", type=Path, default=Path("artifacts"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/release_privacy_audit.md"))
    args = parser.parse_args()
    root = args.root.resolve()
    artifact_dir = args.artifact_dir if args.artifact_dir.is_absolute() else root / args.artifact_dir
    output = args.output if args.output.is_absolute() else root / args.output

    failures: list[str] = []
    scanned: list[Path] = []
    for path in sorted(artifact_dir.rglob("*")):
        if not path.is_file() or path == output or ignored_by_git(root, path):
            continue
        scanned.append(path)
        relative = path.relative_to(root)
        if path.suffix in TEXT_SUFFIXES:
            text = path.read_text(encoding="utf-8", errors="replace")
            if "/home/" in text or "C:\\Users\\" in text:
                failures.append(f"{relative}: contains an absolute user-home path")
        if path.suffix == ".csv":
            with path.open(encoding="utf-8", errors="replace", newline="") as handle:
                header = next(csv.reader(handle), [])
            forbidden = sorted(set(header) & FORBIDDEN_FIELDS)
            if forbidden:
                failures.append(f"{relative}: forbidden CSV fields {forbidden}")
        elif path.suffix in {".json", ".jsonl"}:
            try:
                forbidden = sorted(json_keys(path) & FORBIDDEN_FIELDS)
            except (json.JSONDecodeError, OSError) as error:
                failures.append(f"{relative}: cannot audit JSON: {error}")
            else:
                if forbidden:
                    failures.append(f"{relative}: forbidden JSON fields {forbidden}")

    output.parent.mkdir(parents=True, exist_ok=True)
    status = "PASS" if not failures else "FAIL"
    report = [
        "# Public artifact privacy audit", "",
        f"Status: **{status}**", "",
        f"Scanned {len(scanned)} Git-eligible artifact files; files ignored by `.gitignore` were excluded.", "",
        "The gate rejects explicit source-text fields and absolute user-home paths. It is a release-structure check, not proof that indirect identifiers or all sensitive information are absent.", "",
    ]
    if failures:
        report.extend(["## Failures", "", *[f"- {failure}" for failure in failures], ""])
    output.write_text("\n".join(report), encoding="utf-8")
    if failures:
        raise SystemExit("release privacy audit failed:\n" + "\n".join(failures))
    print(f"PASS: {len(scanned)} Git-eligible artifact files passed release privacy structure checks")


if __name__ == "__main__":
    main()
