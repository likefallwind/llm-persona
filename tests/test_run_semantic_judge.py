from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import run_semantic_judge as semantic


class EmptyStreamClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def reset_usage_window(self) -> None:
        pass

    def read_usage_window(self) -> dict[str, int]:
        return {"calls": 1}

    def chat(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        self.calls.append(kwargs)
        if kwargs["stream"]:
            return ""
        scores = {dimension: 3 for dimension in semantic.DIMENSIONS}
        return json.dumps({
            "candidates": {label: scores for label in "ABCDEF"},
            "confidence": 4,
        })


def test_empty_stream_retries_same_prompt_with_nonstream_transport(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(semantic.time, "sleep", lambda _: None)
    client = EmptyStreamClient()
    batch = {
        "benchmark": "task",
        "item_id": "item-1",
        "pair_group": "task",
        "pair_id": "item-1",
        "context": "context",
        "responses": {f"model-{index}": f"response-{index}" for index in range(6)},
    }

    row = semantic.annotate_one(client, "judge", 7, batch, retries=2)

    assert row["error"] == ""
    assert row["annotation"] is not None
    assert row["attempts"] == 2
    assert row["transport"] == "nonstream"
    assert [call["stream"] for call in client.calls] == [True, False]
