#!/usr/bin/env python3
"""Fail closed on anonymity, page-boundary, and font defects in the ACL PDF."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any


TOOLS = ("pdfinfo", "pdffonts", "pdftotext")


def run(*command: str) -> str:
    return subprocess.run(command, check=True, capture_output=True, text=True).stdout


def pdfinfo_fields(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in text.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip()
    return fields


def font_rows(text: str) -> list[list[str]]:
    rows = []
    for line in text.splitlines():
        stripped = line.strip()
        if (
            not stripped
            or stripped.startswith("name ")
            or set(stripped).issubset({"-", " "})
        ):
            continue
        rows.append(stripped.split())
    return rows


def normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def audit(root: Path, tex_path: Path, pdf_path: Path) -> dict[str, Any]:
    missing_tools = [tool for tool in TOOLS if shutil.which(tool) is None]
    if missing_tools:
        raise RuntimeError(f"missing PDF audit tools: {missing_tools}")

    tex = tex_path.read_text(encoding="utf-8")
    compact_tex = normalized(tex)
    info = pdfinfo_fields(run("pdfinfo", str(pdf_path)))
    fonts = font_rows(run("pdffonts", str(pdf_path)))
    full_text = run("pdftotext", str(pdf_path), "-")
    page_eight = run("pdftotext", "-f", "8", "-l", "8", str(pdf_path), "-")
    page_nine = run("pdftotext", "-f", "9", "-l", "9", str(pdf_path), "-")
    compact = normalized(full_text)
    compact_page_eight = normalized(page_eight)
    compact_page_nine = normalized(page_nine)
    pages = int(info.get("Pages", "0"))

    identity_patterns = {
        "local_home_path": r"/home/",
        "workspace_user": r"likefallwind",
        "repository_owner_url": r"github\.com/likefallwind",
        "acknowledgements": r"(?i)acknowledg(?:e)?ments?",
    }
    identity_hits = {
        name: bool(re.search(pattern, full_text))
        for name, pattern in identity_patterns.items()
    }
    checks = {
        "review_mode": r"\usepackage[review]{acl}" in tex,
        "anonymous_author_field": r"\author{Anonymous ACL submission}" in tex,
        "page_count_within_review_package": 8 <= pages <= 9,
        "main_content_ends_on_page_eight": (
            "Ethics Statement" in compact_page_eight
            and "References" in compact_page_eight
            and compact_page_eight.index("Ethics Statement") < compact_page_eight.index("References")
        ),
        "page_nine_is_references_only": not any(
            heading in compact_page_nine
            for heading in ("Conclusion", "Limitations", "Ethics Statement")
        ),
        "blank_pdf_title_metadata": info.get("Title", "") == "",
        "blank_pdf_author_metadata": info.get("Author", "") == "",
        "fonts_present": bool(fonts),
        "all_fonts_embedded": bool(fonts) and all(len(row) >= 5 and row[-5] == "yes" for row in fonts),
        "no_type_three_fonts": all("Type 3" not in " ".join(row) for row in fonts),
        "no_identity_or_local_path_hits": not any(identity_hits.values()),
        "bounded_personality_claim": "not human-like personality or learning benefit" in compact_tex,
        "detector_downgrade_present": "not semantic warmth or support" in compact_tex,
        "learner_request_null_present": "learner requests alone do not reliably personalize" in compact_tex,
        "no_warm_tone_outcome_label": "Warm tone" not in tex,
    }
    return {
        "schema_version": 1,
        "pdf": str(pdf_path.relative_to(root)),
        "tex": str(tex_path.relative_to(root)),
        "pages": pages,
        "font_count": len(fonts),
        "identity_hits": identity_hits,
        "checks": checks,
        "passed": all(checks.values()),
    }


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# ACL submission audit",
        "",
        f"Overall: **{'PASS' if report['passed'] else 'FAIL'}**",
        "",
        f"- PDF pages: {report['pages']}",
        f"- Embedded font rows inspected: {report['font_count']}",
        "",
        "| Check | Pass |",
        "|---|:---:|",
    ]
    for name, passed in report["checks"].items():
        lines.append(f"| {name} | {'yes' if passed else 'NO'} |")
    lines.extend([
        "",
        "This is a structural audit, not a substitute for final visual inspection or the live venue rules.",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--tex", type=Path, default=Path("paper/submission/main.tex"))
    parser.add_argument("--pdf", type=Path, default=Path("paper/submission/submission.pdf"))
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/submission_audit"))
    parser.add_argument("--require-pass", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    tex = args.tex if args.tex.is_absolute() else root / args.tex
    pdf = args.pdf if args.pdf.is_absolute() else root / args.pdf
    output = args.output_dir if args.output_dir.is_absolute() else root / args.output_dir
    report = audit(root, tex, pdf)
    output.mkdir(parents=True, exist_ok=True)
    (output / "submission_audit.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output / "submission_audit.md").write_text(markdown(report), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    if args.require_pass and not report["passed"]:
        failed = [name for name, passed in report["checks"].items() if not passed]
        raise SystemExit(f"ACL submission audit failed: {failed}")


if __name__ == "__main__":
    main()
