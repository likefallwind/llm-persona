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


def run_status(monkeypatch: pytest.MonkeyPatch, panel: Path) -> None:
    monkeypatch.setattr(sys, "argv", [
        "semantic_judge_status.py", "--output-dir", str(panel), "--require-complete",
    ])
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
