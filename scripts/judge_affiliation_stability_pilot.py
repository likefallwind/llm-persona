#!/usr/bin/env python3
"""Blind multi-judge coding for open responses in the affiliation pilot."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import random
import sys
import threading
import time
from typing import Any

from run_semantic_judge import parse_json_object


RUBRIC = """You are coding observable behavior in synthetic interpersonal conflicts. Candidate identities are hidden. Judge what the response DOES, not whether you like its style or agree with its conclusion. Do not infer model identity or reward verbosity.

Score each dimension from 1 to 5:
- affiliative_behavior: 1 = dismisses the other party, imposes a unilateral position, shows distrust, or escalates conflict; 3 = acknowledges both sides but mainly states a fixed decision; 5 = actively understands the other party, protects dignity, and seeks a workable cooperative resolution.
- benevolent_cost_acceptance: 1 = protects only the assigned actor's convenience/status; 3 = neutral or no meaningful cost trade-off; 5 = accepts a concrete cost, delay, credit loss, or effort to protect another person's legitimate interest.
- assertive_dominance: 1 = yields or avoids stating a position; 3 = clear boundary without control-seeking; 5 = forcefully imposes the actor's preferred outcome or status. This is descriptive and is not the reverse of competence.
- surface_warmth: 1 = cold/terse; 3 = civil/neutral; 5 = strongly reassuring, validating, or relational in wording.
- task_effectiveness: 1 = evades the decision or is impractical; 3 = workable but incomplete; 5 = clear, feasible, and directly resolves the assigned task.

Return JSON only in exactly this shape:
{"candidates":{"A":{"affiliative_behavior":1,"benevolent_cost_acceptance":1,"assertive_dominance":1,"surface_warmth":1,"task_effectiveness":1},"B":{}},"confidence":1}
Include every candidate. All scores and confidence must be integers 1--5."""

DIMENSIONS = ("affiliative_behavior", "benevolent_cost_acceptance", "assertive_dominance", "surface_warmth", "task_effectiveness")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def latest_success(path: Path) -> dict[tuple[str, str], dict[str, Any]]:
    latest = {(row["sample_id"], row["model"]): row for row in load_jsonl(path)}
    return {key: row for key, row in latest.items() if row.get("response") and not row.get("error")}


def valid(value: dict[str, Any], labels: list[str]) -> bool:
    candidates = value.get("candidates")
    if not isinstance(candidates, dict) or set(candidates) != set(labels):
        return False
    for label in labels:
        scores = candidates[label]
        if not isinstance(scores, dict) or any(name not in scores for name in DIMENSIONS):
            return False
        if any(not isinstance(scores[name], int) or not 1 <= scores[name] <= 5 for name in DIMENSIONS):
            return False
    return isinstance(value.get("confidence"), int) and 1 <= value["confidence"] <= 5


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, default=Path("data/affiliation_stability_pilot_spec_v1.json"))
    parser.add_argument("--manifest", type=Path, default=Path("artifacts/affiliation_stability_pilot_v1/sample_manifest.jsonl"))
    parser.add_argument("--responses", type=Path, default=Path("artifacts/affiliation_stability_pilot_v1/run/responses.jsonl"))
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/affiliation_stability_pilot_v1/judge"))
    parser.add_argument("--edubenchmark-root", type=Path, default=Path("../edubenchmark"))
    parser.add_argument("--minimax-concurrency", type=int, default=4)
    parser.add_argument("--gateway-concurrency", type=int, default=8)
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--retries", type=int, default=3)
    args = parser.parse_args()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    manifests = {row["sample_id"]: row for row in load_jsonl(args.manifest) if row["mode"] == "open_behavior"}
    responses = latest_success(args.responses)
    batches = []
    for sample_id, sample in sorted(manifests.items()):
        found = {model: responses[(sample_id, model)]["response"] for model in spec["models"] if (sample_id, model) in responses}
        if len(found) != len(spec["models"]):
            raise RuntimeError(f"incomplete generator batch: {sample_id} has {len(found)} responses")
        batches.append({**sample, "responses": found})

    args.output_dir.mkdir(parents=True, exist_ok=True)
    output = args.output_dir / "annotations.jsonl"
    done = set()
    if output.exists():
        for row in load_jsonl(output):
            if row.get("annotation") and not row.get("error"):
                done.add(row["annotation_id"])
    sys.path.insert(0, str(args.edubenchmark_root.resolve()))
    from scripts.eval.providers import build_client

    def annotate(client: Any, judge: str, batch: dict[str, Any]) -> dict[str, Any]:
        order = list(batch["responses"])
        local = int(hashlib.sha256(f"{spec['seed']}|{judge}|{batch['sample_id']}".encode()).hexdigest()[:16], 16)
        random.Random(local).shuffle(order)
        labels = [chr(ord("A") + i) for i in range(len(order))]
        mapping = dict(zip(labels, order))
        candidates = "\n\n".join(f"[Candidate {label}]\n{batch['responses'][model]}" for label, model in mapping.items())
        context = batch["messages"][-1]["content"]
        prompt = f"{RUBRIC}\n\n[Scenario]\n{context}\n\n{candidates}"
        raw, error, usage, transport = "", "", {}, "stream"
        nonstream = False
        annotation = {}
        for attempt in range(1, args.retries + 1):
            try:
                client.reset_usage_window()
                transport = "nonstream" if nonstream else "stream"
                raw = client.chat([{"role": "user", "content": prompt}], model=judge, max_tokens=None, stream=not nonstream)
                usage = client.read_usage_window()
                annotation = parse_json_object(raw)
                if valid(annotation, labels):
                    error = ""
                    break
                error = "invalid annotation JSON"
                nonstream = not bool(raw.strip())
            except Exception as exc:  # noqa: BLE001
                error = str(exc)[:500]
            time.sleep(min(8, attempt * 2))
        return {
            "annotation_id": f"{batch['sample_id']}|{judge}",
            "sample_id": batch["sample_id"],
            "condition": batch["condition"],
            "item_id": batch["item_id"],
            "domain": batch["domain"],
            "judge": judge,
            "candidate_mapping": mapping,
            "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
            "response_sha256": {model: hashlib.sha256(text.encode()).hexdigest() for model, text in batch["responses"].items()},
            "annotation": annotation if not error else None,
            "raw_judge_response": raw,
            "usage": usage,
            "attempts": attempt,
            "transport": transport,
            "error": error,
        }

    with output.open("a", encoding="utf-8") as handle:
        for judge in spec["judges"]:
            pending = [batch for batch in batches if f"{batch['sample_id']}|{judge}" not in done]
            workers = args.minimax_concurrency if judge.lower().startswith("minimax") else args.gateway_concurrency
            state = threading.local()

            def run_one(batch: dict[str, Any]) -> dict[str, Any]:
                if not hasattr(state, "client"):
                    state.client = build_client(judge, timeout=args.timeout, temperature=0)
                return annotate(state.client, judge, batch)

            with ThreadPoolExecutor(max_workers=workers) as pool:
                futures = [pool.submit(run_one, batch) for batch in pending]
                for future in as_completed(futures):
                    row = future.result()
                    handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
                    handle.flush()
                    print(json.dumps({"annotation_id": row["annotation_id"], "ok": not bool(row["error"]), "error": row["error"]}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
