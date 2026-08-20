#!/usr/bin/env python3
"""Blind, resumable three-judge validation of factorial outcome detectors."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import random
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LABELS = ("question_first", "answer_reveal_correct", "warmth_marker")
VALUES = {"yes", "no", "uncertain"}
RUBRIC = """You are validating transparent behavioral measurements on synthetic AI-tutor responses. Candidate identities, policy conditions, and existing detector values are hidden. Apply the same rules literally to every candidate; do not judge overall quality.

For every candidate return three labels:

1. question_first: Starting at the first non-whitespace character, take the first sentence-like segment through the first period, exclamation mark, question mark, or newline. If none occurs, use at most the first 250 characters. Label yes only if that segment contains a question mark.
2. answer_reveal_correct: Label yes only if the response contains an explicit field labelled "Final answer:" or "Final answer=" and the value in that field is mathematically equivalent to the supplied correct answer. A correct equivalent fraction or decimal counts. A solution stated elsewhere without that explicit field is no.
3. warmth_marker: Label yes when the response contains explicit learner-directed encouragement or emotional support (for example praise, reassurance, "you can do it", "keep going", "let's work through it", or a clearly equivalent phrase). Polite but purely transactional wording is no.

Use uncertain only when the literal evidence genuinely cannot determine the label. Return JSON only, exactly:
{"candidates":{"A":{"question_first":"yes","answer_reveal_correct":"no","warmth_marker":"yes"}},"confidence":4}

Include every supplied candidate exactly once. Values must be yes, no, or uncertain. Confidence must be an integer 1--5. Do not add prose."""


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8", errors="replace") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def parse_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        stripped = "\n".join(lines)
    try:
        value = json.loads(stripped)
        return value if isinstance(value, dict) else {}
    except json.JSONDecodeError:
        start, end = stripped.find("{"), stripped.rfind("}")
        if start >= 0 and end > start:
            try:
                value = json.loads(stripped[start : end + 1])
                return value if isinstance(value, dict) else {}
            except json.JSONDecodeError:
                return {}
    return {}


def valid_annotation(value: dict[str, Any], candidate_labels: list[str]) -> bool:
    candidates = value.get("candidates")
    if not isinstance(candidates, dict) or set(candidates) != set(candidate_labels):
        return False
    for label in candidate_labels:
        result = candidates.get(label)
        if not isinstance(result, dict) or set(result) != set(LABELS):
            return False
        if any(str(result[name]).lower() not in VALUES for name in LABELS):
            return False
    confidence = value.get("confidence")
    return isinstance(confidence, int) and 1 <= confidence <= 5


def latest_successes(path: Path) -> dict[tuple[str, str], dict[str, Any]]:
    latest: dict[tuple[str, str], dict[str, Any]] = {}
    for row in load_jsonl(path):
        key = (str(row.get("sample_id", "")), str(row.get("model", "")))
        if all(key):
            latest[key] = row
    return {
        key: row for key, row in latest.items()
        if isinstance(row.get("response"), str) and row["response"].strip() and not row.get("error")
    }


def build_batches(root: Path, spec: dict[str, Any]) -> list[dict[str, Any]]:
    samples = {row["validation_id"]: row for row in load_jsonl(
        root / "artifacts/factorial_detector_validation_v1/sample_manifest.jsonl"
    )}
    batch_plan = load_jsonl(root / "artifacts/factorial_detector_validation_v1/batch_plan.jsonl")
    source_manifests: dict[str, dict[str, dict[str, Any]]] = {}
    responses: dict[str, dict[tuple[str, str], dict[str, Any]]] = {}
    for panel, panel_spec in spec["panels"].items():
        source_manifests[panel] = {
            row["sample_id"]: row for row in load_jsonl(root / panel_spec["manifest"])
        }
        responses[panel] = latest_successes(root / panel_spec["raw_responses"])

    batches = []
    for batch in batch_plan:
        candidates = []
        problem = None
        answer = None
        for validation_id in batch["validation_ids"]:
            selected = samples[validation_id]
            panel = selected["panel"]
            source = source_manifests[panel][selected["sample_id"]]
            response = responses[panel].get((selected["sample_id"], selected["model"]))
            if response is None:
                raise RuntimeError(f"missing raw response for {validation_id}")
            response_text = response["response"]
            if hashlib.sha256(response_text.encode()).hexdigest() != selected["response_sha256"]:
                raise RuntimeError(f"response hash mismatch for {validation_id}")
            if response.get("prompt_sha256") != selected["prompt_sha256"]:
                raise RuntimeError(f"prompt hash mismatch for {validation_id}")
            if problem is None:
                problem, answer = source["problem"], source["answer"]
            if source["problem"] != problem or source["answer"] != answer:
                raise RuntimeError(f"batch {batch['batch_id']} mixes base problems")
            candidates.append({"validation_id": validation_id, "response": response_text})
        batches.append({**batch, "problem": problem, "answer": answer, "candidates": candidates})
    return batches


def candidate_order(seed: int, judge: str, batch: dict[str, Any]) -> list[dict[str, Any]]:
    ordered = list(batch["candidates"])
    local_seed = int(hashlib.sha256(
        f"{seed}|{judge}|{batch['batch_id']}".encode()
    ).hexdigest()[:16], 16)
    random.Random(local_seed).shuffle(ordered)
    return ordered


def build_prompt(seed: int, judge: str, batch: dict[str, Any]) -> tuple[str, dict[str, str]]:
    ordered = candidate_order(seed, judge, batch)
    letters = [chr(ord("A") + index) for index in range(len(ordered))]
    mapping = {letter: row["validation_id"] for letter, row in zip(letters, ordered)}
    candidate_text = "\n\n".join(
        f"[Candidate {letter}]\n{row['response']}" for letter, row in zip(letters, ordered)
    )
    prompt = (
        f"{RUBRIC}\n\n[Synthetic problem]\n{batch['problem']}\n\n"
        f"[Known correct answer]\n{batch['answer']}\n\n{candidate_text}"
    )
    return prompt, mapping


def result_row(
    batch: dict[str, Any], judge: str, mapping: dict[str, str], prompt: str,
    parsed: dict[str, Any], raw: str, usage: dict[str, Any], attempts: int,
    transport: str, error: str,
) -> dict[str, Any]:
    return {
        "annotation_id": f"{batch['batch_id']}|{judge}",
        "batch_id": batch["batch_id"],
        "judge": judge,
        "candidate_mapping": mapping,
        "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
        "prompt_chars": len(prompt),
        "response_sha256": {
            row["validation_id"]: hashlib.sha256(row["response"].encode()).hexdigest()
            for row in batch["candidates"]
        },
        "annotation": parsed if not error else None,
        "raw_judge_response": raw,
        "usage": usage,
        "attempts": attempts,
        "transport": transport,
        "error": error,
    }


def annotate_one(client: Any, judge: str, seed: int, batch: dict[str, Any], retries: int) -> dict[str, Any]:
    prompt, mapping = build_prompt(seed, judge, batch)
    raw, error, transport = "", "", "stream"
    parsed: dict[str, Any] = {}
    usage: dict[str, Any] = {}
    prefer_nonstream = False
    for attempt in range(1, retries + 1):
        try:
            client.reset_usage_window()
            transport = "nonstream" if prefer_nonstream else "stream"
            raw = client.chat(
                [{"role": "user", "content": prompt}], model=judge, max_tokens=None,
                stream=not prefer_nonstream,
            )
            usage = client.read_usage_window()
            parsed = parse_json_object(raw)
            if valid_annotation(parsed, list(mapping)):
                return result_row(batch, judge, mapping, prompt, parsed, raw, usage, attempt, transport, "")
            error = "empty judge response" if not raw.strip() else "invalid annotation JSON"
            prefer_nonstream = not raw.strip()
        except Exception as exc:  # noqa: BLE001
            error = str(exc)[:500]
        time.sleep(min(8, attempt * 2))
    return result_row(batch, judge, mapping, prompt, parsed, raw, usage, retries, transport, error)


def completed_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    done = set()
    for row in load_jsonl(path):
        if row.get("annotation") and not row.get("error"):
            done.add(str(row.get("annotation_id", "")))
    return done


def payload_audit(batches: list[dict[str, Any]], judges: list[str], seed: int) -> dict[str, Any]:
    texts = [batch["problem"] for batch in batches]
    texts += [row["response"] for batch in batches for row in batch["candidates"]]
    patterns = {
        "email": r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
        "url": r"https?://[^\s]+",
        "ipv4": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
        "china_id_like": r"(?<!\d)\d{17}[0-9Xx](?!\d)",
        "china_mobile_like": r"(?<!\d)(?:\+?86[ -]?)?1[3-9]\d{9}(?!\d)",
    }
    return {
        "schema_version": 1,
        "judges": judges,
        "batch_count": len(batches),
        "response_units": sum(len(batch["candidates"]) for batch in batches),
        "total_payload_characters_per_judge": sum(
            len(build_prompt(seed, judges[0], batch)[0]) for batch in batches
        ) if judges else 0,
        "potential_identifier_pattern_flags": {
            name: sum(bool(re.search(pattern, text, flags=re.IGNORECASE)) for text in texts)
            for name, pattern in patterns.items()
        },
        "external_payload_scope": "synthetic problem, known answer, and synthetic model responses only",
        "excluded": "benchmark text, LongTutor histories, real learner data, identifiers, private source text, model identity, factor cells, detector values, and effect estimates",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--spec", type=Path, default=Path("data/factorial_detector_validation_spec_v1.json"))
    parser.add_argument("--edubenchmark-root", type=Path, default=Path("../edubenchmark"))
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/factorial_detector_validation_v1/run"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    spec = json.loads((root / args.spec).read_text(encoding="utf-8"))
    judges = list(spec["judges"])
    batches = build_batches(root, spec)
    output = root / args.output_dir
    output.mkdir(parents=True, exist_ok=True)
    audit = payload_audit(batches, judges, int(spec["seed"]))
    public_audit = root / "artifacts/factorial_detector_validation_v1/payload_audit.json"
    public_audit.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(audit, sort_keys=True), flush=True)
    if args.dry_run:
        return

    sys.path.insert(0, str((root / args.edubenchmark_root).resolve()))
    from scripts.eval.providers import build_client

    lock_path = output / ".writer.lock"
    with lock_path.open("w") as lock_handle:
        try:
            fcntl.flock(lock_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise SystemExit(f"active detector-validation writer: {lock_path}") from exc
        output_path = output / "annotations.jsonl"
        done = completed_ids(output_path)
        with output_path.open("a", encoding="utf-8") as handle:
            for judge in judges:
                concurrency = (
                    spec["generation"]["minimax_concurrency"]
                    if judge.lower().startswith("minimax")
                    else spec["generation"]["gateway_concurrency"]
                )
                pending = [
                    batch for batch in batches
                    if f"{batch['batch_id']}|{judge}" not in done
                ]
                thread_state = threading.local()

                def run_batch(batch: dict[str, Any]) -> dict[str, Any]:
                    if not hasattr(thread_state, "client"):
                        thread_state.client = build_client(judge, timeout=300)
                    return annotate_one(
                        thread_state.client, judge, spec["seed"], batch,
                        spec["generation"]["retries"],
                    )

                with ThreadPoolExecutor(max_workers=concurrency) as pool:
                    futures = {pool.submit(run_batch, batch): batch for batch in pending}
                    for future in as_completed(futures):
                        row = future.result()
                        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
                        handle.flush()
                        print(json.dumps({
                            "annotation_id": row["annotation_id"],
                            "ok": not bool(row["error"]),
                            "error": row["error"],
                        }), flush=True)


if __name__ == "__main__":
    main()
