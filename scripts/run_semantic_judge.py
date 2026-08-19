#!/usr/bin/env python3
"""Blind, resumable multi-agent semantic coding of paired tutor responses."""

from __future__ import annotations

import argparse
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

from inventory_paths import resolve_inventory_path


DIMENSIONS = (
    "help_directness",
    "elicitation",
    "autonomy_support",
    "affective_warmth",
    "diagnostic_specificity",
    "personalization",
    "cognitive_load",
    "epistemic_caution",
)

MODEL_LABELS = {
    "minimax-m3": "MiniMax-M3",
    "minimax-m2.7": "MiniMax-M2.7",
    "glm-5.2": "glm-5.2",
    "deepseek-v4-pro": "deepseek-v4-pro",
    "doubao-seed-2.0-pro": "doubao-seed-2.0-pro",
    "qwen3.5-4b": "Qwen/Qwen3.5-4B",
}

ADAPTER_CLASSES = {
    "longtutor_teaching": ("scripts.eval.benchmarks.longtutor", "LongTutorTeachingAdapter"),
    "mathtutorbench_scaffolding": ("scripts.eval.benchmarks.mathtutorbench", "MTBScaffolding"),
    "mathtutorbench_pedagogy": ("scripts.eval.benchmarks.mathtutorbench", "MTBPedagogy"),
    "mathtutorbench_scaffolding_hard": ("scripts.eval.benchmarks.mathtutorbench", "MTBScaffoldingHard"),
    "mathtutorbench_pedagogy_hard": ("scripts.eval.benchmarks.mathtutorbench", "MTBPedagogyHard"),
    "mathtutorbench_socratic": ("scripts.eval.benchmarks.mathtutorbench", "MTBSocratic"),
}

RUBRIC = """You are a behavioral coder studying AI tutors. Code what each candidate DOES, not whether it is good, correct, likable, or similar to a reference. Candidate identities are hidden. Do not infer vendor or model identity. Use the full 1-5 range and apply the same anchors to every candidate.

Dimensions (all are descriptive; higher is not automatically better):
- help_directness: 1 = only a hint/question and no result; 3 = partial procedure or substantial hint; 5 = full solution or final answer is supplied.
- elicitation: 1 = tutor mainly explains/tells with no learner reasoning request; 3 = mixed explanation and elicitation; 5 = response mainly elicits the learner's next reasoning step.
- autonomy_support: 1 = fixed/directive path; 3 = neutral guidance; 5 = meaningful choice, self-explanation, or self-monitoring.
- affective_warmth: 1 = neutral/transactional; 3 = mildly supportive; 5 = strongly warm, encouraging, and relational.
- diagnostic_specificity: 1 = generic/no diagnosis; 3 = identifies a broad issue; 5 = commits to a specific learner misconception, error, or state.
- personalization: 1 = generic and reusable; 3 = uses current dialogue details; 5 = specifically and relevantly uses learner history or prior performance.
- cognitive_load: 1 = one manageable next step; 3 = several linked ideas; 5 = many simultaneous steps or dense information likely to overload a turn.
- epistemic_caution: 1 = unqualified certainty; 3 = neutral; 5 = explicitly calibrated uncertainty, ambiguity, or need for missing information.

Return JSON only, exactly this shape:
{"candidates":{"A":{"help_directness":1,"elicitation":1,"autonomy_support":1,"affective_warmth":1,"diagnostic_specificity":1,"personalization":1,"cognitive_load":1,"epistemic_caution":1},"B":{}},"confidence":1}

Include every supplied candidate label. Every dimension and confidence must be an integer from 1 to 5. Do not add prose or correctness scores."""


def import_object(module_name: str, class_name: str) -> type:
    module = __import__(module_name, fromlist=[class_name])
    return getattr(module, class_name)


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def read_latest_success(path: Path) -> dict[str, str]:
    latest: dict[str, str] = {}
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            item_id = str(row.get("item_id") or "")
            response = row.get("response")
            if item_id and isinstance(response, str) and response.strip() and not row.get("error"):
                latest[item_id] = response
    return latest


def adapter_items(benchmark: str) -> dict[str, dict[str, Any]]:
    module_name, class_name = ADAPTER_CLASSES[benchmark]
    adapter = import_object(module_name, class_name)()
    return {str(item["item_id"]): item for item in adapter.load_items()}


def hash_rank(seed: int, group: str, item_id: str) -> str:
    return hashlib.sha256(f"{seed}|{group}|{item_id}".encode()).hexdigest()


def item_suffix(item_id: str) -> str:
    return item_id.rsplit("-", 1)[-1]


def build_batches(
    inventory: dict[str, Any], seed: int, counts: dict[str, int],
    edubenchmark_root: Path,
) -> list[dict[str, Any]]:
    core_models = inventory["core_models"]
    selected = {(r["benchmark"], r["model"]): r for r in inventory["selected_runs"]}
    needed = set(ADAPTER_CLASSES)
    response_maps: dict[tuple[str, str], dict[str, str]] = {}
    for benchmark in needed:
        for model in core_models:
            run = selected.get((benchmark, model))
            if run:
                response_maps[(benchmark, model)] = read_latest_success(
                    resolve_inventory_path(run["predictions_path"], edubenchmark_root)
                )
    item_maps = {benchmark: adapter_items(benchmark) for benchmark in needed}
    batches: list[dict[str, Any]] = []

    singles = {
        "longtutor_teaching": counts["longtutor"],
        "mathtutorbench_socratic": counts["socratic"],
    }
    for benchmark, count in singles.items():
        common = set(item_maps[benchmark])
        for model in core_models:
            common &= set(response_maps[(benchmark, model)])
        chosen = sorted(common, key=lambda x: hash_rank(seed, benchmark, x))[:count]
        for item_id in chosen:
            batches.append(make_batch(benchmark, item_id, item_maps, response_maps, core_models))

    pair_groups = [
        ("mathdial_standard", counts["mathdial"], "mathtutorbench_scaffolding", "mathtutorbench_pedagogy"),
        ("mathdial_hard", counts["mathdial_hard"], "mathtutorbench_scaffolding_hard", "mathtutorbench_pedagogy_hard"),
    ]
    for group, count, generic, pedagogy in pair_groups:
        suffixes_by_benchmark: dict[str, dict[str, str]] = {}
        for benchmark in (generic, pedagogy):
            common = set(item_maps[benchmark])
            for model in core_models:
                common &= set(response_maps[(benchmark, model)])
            suffixes_by_benchmark[benchmark] = {item_suffix(x): x for x in common}
        common_suffixes = set(suffixes_by_benchmark[generic]) & set(suffixes_by_benchmark[pedagogy])
        chosen_suffixes = sorted(common_suffixes, key=lambda x: hash_rank(seed, group, x))[:count]
        for suffix in chosen_suffixes:
            for benchmark in (generic, pedagogy):
                item_id = suffixes_by_benchmark[benchmark][suffix]
                batch = make_batch(benchmark, item_id, item_maps, response_maps, core_models)
                batch["pair_group"] = group
                batch["pair_id"] = suffix
                batches.append(batch)
    return sorted(batches, key=lambda x: (x["benchmark"], x["item_id"]))


def make_batch(
    benchmark: str,
    item_id: str,
    item_maps: dict[str, dict[str, dict[str, Any]]],
    response_maps: dict[tuple[str, str], dict[str, str]],
    core_models: list[str],
) -> dict[str, Any]:
    item = item_maps[benchmark][item_id]
    return {
        "benchmark": benchmark,
        "item_id": item_id,
        "pair_group": benchmark,
        "pair_id": item_id,
        "context": item["text"],
        "responses": {model: response_maps[(benchmark, model)][item_id] for model in core_models},
    }


def candidate_order(seed: int, judge: str, batch: dict[str, Any]) -> list[str]:
    models = list(batch["responses"])
    local_seed = int(hash_rank(seed, judge, f"{batch['benchmark']}|{batch['item_id']}")[:16], 16)
    random.Random(local_seed).shuffle(models)
    return models


def build_prompt(batch: dict[str, Any], order: list[str]) -> tuple[str, dict[str, str]]:
    labels = [chr(ord("A") + i) for i in range(len(order))]
    mapping = dict(zip(labels, order))
    candidates = "\n\n".join(f"[Candidate {label}]\n{batch['responses'][model]}" for label, model in mapping.items())
    prompt = f"{RUBRIC}\n\n[Educational context and instruction]\n{batch['context']}\n\n{candidates}"
    return prompt, mapping


def parse_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re_fence(stripped)
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
                pass
    return {}


def re_fence(text: str) -> str:
    lines = text.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines)


def validate_annotation(value: dict[str, Any], labels: list[str]) -> bool:
    candidates = value.get("candidates")
    if not isinstance(candidates, dict) or set(candidates) != set(labels):
        return False
    for label in labels:
        scores = candidates[label]
        if not isinstance(scores, dict) or any(d not in scores for d in DIMENSIONS):
            return False
        if any(not isinstance(scores[d], int) or not 1 <= scores[d] <= 5 for d in DIMENSIONS):
            return False
    confidence = value.get("confidence")
    return isinstance(confidence, int) and 1 <= confidence <= 5


def annotate_one(client: Any, judge: str, seed: int, batch: dict[str, Any], retries: int) -> dict[str, Any]:
    order = candidate_order(seed, judge, batch)
    prompt, mapping = build_prompt(batch, order)
    error = ""
    raw = ""
    usage: dict[str, Any] = {}
    parsed: dict[str, Any] = {}
    for attempt in range(1, retries + 1):
        try:
            client.reset_usage_window()
            raw = client.chat([{"role": "user", "content": prompt}], model=judge, max_tokens=None)
            usage = client.read_usage_window()
            parsed = parse_json_object(raw)
            if validate_annotation(parsed, list(mapping)):
                return result_row(batch, judge, mapping, prompt, raw, parsed, usage, attempt, "")
            error = "invalid annotation JSON"
        except Exception as exc:  # noqa: BLE001
            error = str(exc)[:500]
        time.sleep(min(8, attempt * 2))
    return result_row(batch, judge, mapping, prompt, raw, parsed, usage, retries, error)


def result_row(
    batch: dict[str, Any], judge: str, mapping: dict[str, str], prompt: str,
    raw: str, parsed: dict[str, Any], usage: dict[str, Any], attempts: int, error: str,
) -> dict[str, Any]:
    return {
        "annotation_id": f"{batch['benchmark']}|{batch['item_id']}|{judge}",
        "benchmark": batch["benchmark"],
        "item_id": batch["item_id"],
        "pair_group": batch["pair_group"],
        "pair_id": batch["pair_id"],
        "judge": judge,
        "candidate_mapping": mapping,
        "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
        "prompt_chars": len(prompt),
        "response_sha256": {m: hashlib.sha256(t.encode()).hexdigest() for m, t in batch["responses"].items()},
        "annotation": parsed if not error else None,
        "raw_judge_response": raw,
        "usage": usage,
        "attempts": attempts,
        "error": error,
    }


def completed_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    done = set()
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("annotation") and not row.get("error"):
                done.add(str(row.get("annotation_id")))
    return done


def payload_audit(batches: list[dict[str, Any]], judges: list[str]) -> dict[str, Any]:
    contexts = [b["context"] for b in batches]
    responses = [text for b in batches for text in b["responses"].values()]
    patterns = {
        "email": r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
        "url": r"https?://[^\s]+",
        "ipv4": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
        "china_id_like": r"(?<!\d)\d{17}[0-9Xx](?!\d)",
        "china_mobile_like": r"(?<!\d)(?:\+?86[ -]?)?1[3-9]\d{9}(?!\d)",
        "international_phone_like": r"(?<!\d)(?:\+?\d[ -]?){10,14}(?!\d)",
    }

    def flagged_count(texts: list[str], pattern: str) -> int:
        return sum(bool(re.search(pattern, text, flags=re.IGNORECASE)) for text in texts)

    def length_summary(texts: list[str]) -> dict[str, int]:
        lengths = sorted(map(len, texts))
        if not lengths:
            return {"min": 0, "median": 0, "p95": 0, "max": 0, "total": 0}
        return {
            "min": lengths[0],
            "median": lengths[len(lengths) // 2],
            "p95": lengths[min(len(lengths) - 1, int(len(lengths) * 0.95))],
            "max": lengths[-1],
            "total": sum(lengths),
        }

    return {
        "judges_and_routes": {
            "MiniMax-M3": "MiniMax official API",
            "glm-5.2": "configured API gateway",
            "deepseek-v4-pro": "configured API gateway",
        },
        "requested_judges": judges,
        "batch_count": len(batches),
        "context_count": len(contexts),
        "response_count": len(responses),
        "context_chars": length_summary(contexts),
        "response_chars": length_summary(responses),
        "potential_pii_pattern_flags": {
            name: {
                "contexts": flagged_count(contexts, pattern),
                "responses": flagged_count(responses, pattern),
            }
            for name, pattern in patterns.items()
        },
        "international_phone_like_contexts_by_benchmark": {
            benchmark: sum(
                bool(re.search(patterns["international_phone_like"], b["context"]))
                for b in batches if b["benchmark"] == benchmark
            )
            for benchmark in sorted({b["benchmark"] for b in batches})
        },
        "stored_locally": "sample ids, hashes, blind label mappings, judge ratings, and raw judge JSON; source contexts and candidate responses are not copied",
        "caveat": "Regex checks cannot prove absence of names or other indirect identifiers. LongTutor's upstream release has no LICENSE file according to the source repository instructions.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--edubenchmark-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--judges", default="MiniMax-M3,glm-5.2,deepseek-v4-pro")
    parser.add_argument("--seed", type=int, default=20260819)
    parser.add_argument("--longtutor", type=int, default=40)
    parser.add_argument("--mathdial", type=int, default=80)
    parser.add_argument("--mathdial-hard", type=int, default=40)
    parser.add_argument("--socratic", type=int, default=80)
    parser.add_argument("--minimax-concurrency", type=int, default=4)
    parser.add_argument("--gateway-concurrency", type=int, default=8)
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument(
        "--run-benchmarks",
        default="",
        help="Optional comma-separated execution filter; the frozen manifest still records the full sample",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    sys.path.insert(0, str(args.edubenchmark_root.resolve()))
    inventory = load_json(args.inventory)
    counts = {
        "longtutor": args.longtutor,
        "mathdial": args.mathdial,
        "mathdial_hard": args.mathdial_hard,
        "socratic": args.socratic,
    }
    batches = build_batches(inventory, args.seed, counts, args.edubenchmark_root)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": 1,
        "seed": args.seed,
        "counts": counts,
        "batch_count": len(batches),
        "response_count": len(batches) * len(inventory["core_models"]),
        "items": [{k: b[k] for k in ("benchmark", "item_id", "pair_group", "pair_id")} for b in batches],
    }
    manifest_path = args.output_dir / "sample_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    judges = [x.strip() for x in args.judges.split(",") if x.strip()]
    run_benchmarks = {x.strip() for x in args.run_benchmarks.split(",") if x.strip()}
    execution_batches = [b for b in batches if not run_benchmarks or b["benchmark"] in run_benchmarks]
    audit = payload_audit(batches, judges)
    (args.output_dir / "payload_audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    prompt_chars = sum(len(build_prompt(b, candidate_order(args.seed, judges[0], b))[0]) for b in batches) if judges else 0
    print(json.dumps({
        "manifest_batches": len(batches),
        "execution_batches": len(execution_batches),
        "responses": manifest["response_count"],
        "judges": judges,
        "run_benchmarks": sorted(run_benchmarks),
        "prompt_chars_per_judge": prompt_chars,
    }, ensure_ascii=False), flush=True)
    if args.dry_run:
        return

    from scripts.eval.providers import build_client

    output_path = args.output_dir / "annotations.jsonl"
    done = completed_ids(output_path)
    with output_path.open("a", encoding="utf-8") as handle:
        for judge in judges:
            concurrency = args.minimax_concurrency if judge.lower().startswith("minimax") else args.gateway_concurrency
            pending = [b for b in execution_batches if f"{b['benchmark']}|{b['item_id']}|{judge}" not in done]
            thread_state = threading.local()

            def annotate_with_thread_client(batch: dict[str, Any]) -> dict[str, Any]:
                if not hasattr(thread_state, "client"):
                    thread_state.client = build_client(judge, timeout=args.timeout)
                return annotate_one(thread_state.client, judge, args.seed, batch, args.retries)

            with ThreadPoolExecutor(max_workers=concurrency) as pool:
                futures = {pool.submit(annotate_with_thread_client, b): b for b in pending}
                for future in as_completed(futures):
                    row = future.result()
                    handle.write(json.dumps(row, ensure_ascii=False) + "\n")
                    handle.flush()
                    print(json.dumps({"annotation_id": row["annotation_id"], "ok": not bool(row["error"]), "error": row["error"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
