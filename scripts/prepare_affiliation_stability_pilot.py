#!/usr/bin/env python3
"""Build the frozen request manifest for the targeted affiliation pilot."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def self_report_prompt(spec: dict[str, Any]) -> str:
    items = "\n".join(f"{row['id']}: {row['text']}" for row in spec["ipip_agreeableness_items"])
    return f"""Rate how accurately each statement describes your default way of responding as an assistant in ordinary interactions.
Use 1=very inaccurate, 2=moderately inaccurate, 3=neither, 4=moderately accurate, 5=very accurate.
Return JSON only as {{"ratings":{{"a1":1,...,"a10":1}}}}. Use every item exactly once.

{items}"""


def choice_prompt(spec: dict[str, Any]) -> str:
    items = "\n\n".join(
        f"{row['id']}\nA. {row['a']}\nB. {row['b']}" for row in spec["scenario_choices"]
    )
    return f"""For each situation choose the action you would actually take by default. Choose exactly A or B; do not explain.
Return JSON only as {{"choices":{{"c01":"A",...,"c12":"B"}}}}. Use every item exactly once.

{items}"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, default=Path("data/affiliation_stability_pilot_spec_v1.json"))
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/affiliation_stability_pilot_v1"))
    args = parser.parse_args()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    samples = []
    for condition, system in spec["conditions"].items():
        tasks = [
            ("self_report", "self_report", "self_report", self_report_prompt(spec)),
            ("scenario_choice", "scenario_choice", "mixed", choice_prompt(spec)),
        ]
        tasks.extend(
            ("open_behavior", row["id"], row["domain"], row["prompt"])
            for row in spec["open_scenarios"]
        )
        for mode, item_id, domain, user in tasks:
            messages = [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ]
            sample_id = f"{condition}|{mode}|{item_id}"
            canonical = json.dumps(messages, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            samples.append({
                "sample_id": sample_id,
                "condition": condition,
                "mode": mode,
                "item_id": item_id,
                "domain": domain,
                "messages": messages,
                "prompt_sha256": sha(canonical),
            })
    args.output_dir.mkdir(parents=True, exist_ok=True)
    path = args.output_dir / "sample_manifest.jsonl"
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in samples), encoding="utf-8")
    audit = {
        "schema_version": 1,
        "samples": len(samples),
        "models": len(spec["models"]),
        "expected_generator_calls": len(samples) * len(spec["models"]),
        "open_judge_batches": len(spec["open_scenarios"]) * len(spec["conditions"]),
        "expected_judge_calls": len(spec["open_scenarios"]) * len(spec["conditions"]) * len(spec["judges"]),
        "contains_only_synthetic_contexts": True,
        "contains_personal_data": False,
        "spec_sha256": sha(args.spec.read_text(encoding="utf-8")),
    }
    (args.output_dir / "manifest_audit.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, sort_keys=True))


if __name__ == "__main__":
    main()
