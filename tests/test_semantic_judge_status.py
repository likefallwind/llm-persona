from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import semantic_judge_status as status


JUDGES = ["MiniMax-M3", "glm-5.2", "deepseek-v4-pro"]


@pytest.fixture
def complete_panel(tmp_path: Path) -> Path:
    manifest = {
        "items": [{"benchmark": "task", "item_id": "item-1"}],
    }
    (tmp_path / "sample_manifest.json").write_text(json.dumps(manifest))
    rows = [
        {
            "annotation_id": f"task|item-1|{judge}",
            "annotation": {"confidence": 4},
            "error": "",
        }
        for judge in JUDGES
    ]
    (tmp_path / "annotations.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in rows)
    )
    return tmp_path


def run_status(
    monkeypatch: pytest.MonkeyPatch, panel: Path, exclusions: Path | None = None,
) -> None:
    argv = [
        "semantic_judge_status.py", "--output-dir", str(panel), "--require-complete",
    ]
    if exclusions is not None:
        argv.extend(["--exclusions", str(exclusions)])
    monkeypatch.setattr(sys, "argv", argv)
    status.main()


def test_require_complete_accepts_exact_three_judge_coverage(
    complete_panel: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_status(monkeypatch, complete_panel)
    assert (complete_panel / "status_report.md").is_file()


def test_require_complete_rejects_latest_error(
    complete_panel: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    with (complete_panel / "annotations.jsonl").open("a") as handle:
        handle.write(json.dumps({
            "annotation_id": "task|item-1|deepseek-v4-pro",
            "annotation": None,
            "error": "invalid annotation JSON",
        }) + "\n")
    with pytest.raises(SystemExit, match="coverage gate failed"):
        run_status(monkeypatch, complete_panel)


def test_require_complete_accepts_validated_technical_exclusion(
    complete_panel: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = json.loads((complete_panel / "sample_manifest.json").read_text())
    manifest["items"].append({"benchmark": "task", "item_id": "item-2"})
    (complete_panel / "sample_manifest.json").write_text(json.dumps(manifest))
    with (complete_panel / "annotations.jsonl").open("a") as handle:
        handle.write(json.dumps({
            "annotation_id": "task|item-2|deepseek-v4-pro",
            "annotation": None,
            "error": "HTTP 500 InternalServiceError",
        }) + "\n")
    exclusions = complete_panel / "exclusions.json"
    exclusions.write_text(json.dumps({
        "schema_version": 1,
        "expected_manifest_batches": 2,
        "expected_analyzed_batches": 1,
        "expected_analyzed_annotations": 3,
        "excluded_items": [{"benchmark": "task", "item_id": "item-2"}],
    }))

    run_status(monkeypatch, complete_panel, exclusions)
    report = (complete_panel / "status_report.md").read_text()
    assert "Technical exclusions: **1**" in report
