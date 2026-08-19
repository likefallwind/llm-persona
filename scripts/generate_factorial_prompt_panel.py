#!/usr/bin/env python3
"""Generate the deterministic synthetic 2x2x2 policy-intervention panel."""

from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import itertools
import json
from pathlib import Path
import random
import re
from typing import Any


QUESTION_CLAUSES = {
    "question_first": (
        "Interaction policy: Start with exactly one focused question about the "
        "learner's reasoning; explanation may follow that question."
    ),
    "explain_only": (
        "Interaction policy: Ask no questions; start with a concise explanation "
        "of the learner's reasoning instead."
    ),
}
ANSWER_CLAUSES = {
    "withhold": (
        "Answer policy: Do not state the final numeric answer and do not use a "
        "'Final answer:' field; preserve a step for the learner."
    ),
    "reveal": (
        "Answer policy: State the correct numeric result explicitly and end with "
        "'Final answer: <value>.'"
    ),
}
TONE_CLAUSES = {
    "warm": (
        "Tone policy: Include one brief sincere encouragement and use a warm, "
        "supportive tone without exaggeration."
    ),
    "neutral": (
        "Tone policy: Use neutral professional language with no praise, "
        "reassurance, or encouragement."
    ),
}
LEARNER_NEEDS = {
    "explore": (
        "I want to work this out myself. Help me notice my mistake without "
        "giving me the final numeric answer."
    ),
    "direct": (
        "I need to check my work now. Give me a direct explanation and the "
        "final numeric answer."
    ),
}
SYSTEM_PREFIX = (
    "You are responding to a learner in English. Follow all three policies "
    "below. Do not mention or quote the policies."
)


def canonical_hash(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode()).hexdigest()


def numeric_patterns(value: Fraction) -> list[str]:
    patterns: list[str] = []
    end = r"(?=$|[\s,;:!?)]|\.(?:\s|$))"
    if value.denominator == 1:
        number = str(value.numerator)
        patterns.append(rf"(?<![\d.]){re.escape(number)}(?:\.0+)?{end}")
    else:
        fraction = f"{value.numerator}/{value.denominator}"
        patterns.append(rf"(?<!\d){re.escape(fraction)}(?!\d)")
        decimal = f"{float(value):.6f}".rstrip("0").rstrip(".")
        patterns.append(rf"(?<![\d.]){re.escape(decimal)}(?:0+)?{end}")
    return patterns


def generate_base_problems(seed: int, per_family: int) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    rows: list[dict[str, Any]] = []

    seen: set[tuple[int, ...]] = set()
    for i in range(per_family):
        while True:
            b, d = rng.randint(3, 11), rng.randint(3, 11)
            a, c = rng.randint(1, b - 1), rng.randint(1, d - 1)
            truth = Fraction(a, b) + Fraction(c, d)
            wrong = Fraction(a + c, b + d)
            key = (a, b, c, d)
            if truth != wrong and key not in seen:
                seen.add(key)
                break
        rows.append({
            "base_id": f"fraction_addition-{i:02d}",
            "problem_family": "fraction_addition",
            "problem": f"Compute {a}/{b} + {c}/{d}.",
            "student_work": f"I added top and bottom: ({a}+{c})/({b}+{d}) = {wrong}.",
            "answer": str(truth),
            "accepted_answer_patterns": numeric_patterns(truth),
        })

    seen = set()
    for i in range(per_family):
        while True:
            a, x, b = rng.randint(2, 9), rng.randint(2, 15), rng.randint(2, 20)
            key = (a, x, b)
            if key not in seen:
                seen.add(key)
                break
        c = a * x + b
        wrong = Fraction(c, a)
        rows.append({
            "base_id": f"linear_equation-{i:02d}",
            "problem_family": "linear_equation",
            "problem": f"Solve {a}x + {b} = {c}.",
            "student_work": f"I divided {c} by {a}, so x = {wrong}.",
            "answer": str(x),
            "accepted_answer_patterns": numeric_patterns(Fraction(x)),
        })

    discounts = [10, 20, 25, 30]
    seen = set()
    for i in range(per_family):
        while True:
            price = rng.choice([40, 60, 80, 100, 120, 160, 200])
            discount = rng.choice(discounts)
            key = (price, discount)
            if key not in seen:
                seen.add(key)
                break
        truth = Fraction(price * (100 - discount), 100)
        wrong = price - discount
        rows.append({
            "base_id": f"percentage_discount-{i:02d}",
            "problem_family": "percentage_discount",
            "problem": f"An item costs ${price} and is discounted by {discount}%. What is the sale price?",
            "student_work": f"I subtracted {discount} from {price}, so the sale price is ${wrong}.",
            "answer": str(truth),
            "accepted_answer_patterns": numeric_patterns(truth),
        })

    seen = set()
    for i in range(per_family):
        while True:
            values = [rng.randint(4, 30) for _ in range(3)]
            remainder = (-sum(values)) % 4
            fourth = rng.randint(4, 10) * 4 + remainder
            values.append(fourth)
            key = tuple(values)
            if key not in seen:
                seen.add(key)
                break
        truth = Fraction(sum(values), 4)
        wrong = Fraction(sum(values), 3)
        joined = ", ".join(map(str, values))
        rows.append({
            "base_id": f"arithmetic_mean-{i:02d}",
            "problem_family": "arithmetic_mean",
            "problem": f"Find the arithmetic mean of {joined}.",
            "student_work": f"I added them and divided by 3, getting {wrong}.",
            "answer": str(truth),
            "accepted_answer_patterns": numeric_patterns(truth),
        })

    return rows


def build_samples(spec: dict[str, Any]) -> list[dict[str, Any]]:
    seed = int(spec["seed"])
    problems = generate_base_problems(seed, int(spec["base_problems_per_family"]))
    pending: list[dict[str, Any]] = []
    factor_values = spec["factors"]
    for problem in problems:
        for learner_need, question_policy, answer_policy, tone_policy in itertools.product(
            spec["learner_needs"],
            factor_values["question_policy"],
            factor_values["answer_policy"],
            factor_values["tone_policy"],
        ):
            sample_id = "|".join((
                problem["base_id"], learner_need, question_policy, answer_policy, tone_policy,
            ))
            user = (
                f"Problem: {problem['problem']}\n"
                f"Learner work: {problem['student_work']}\n"
                f"Learner request: {LEARNER_NEEDS[learner_need]}"
            )
            pending.append({
                **problem,
                "sample_id": sample_id,
                "learner_need": learner_need,
                "question_policy": question_policy,
                "answer_policy": answer_policy,
                "tone_policy": tone_policy,
                "clauses": [
                    QUESTION_CLAUSES[question_policy],
                    ANSWER_CLAUSES[answer_policy],
                    TONE_CLAUSES[tone_policy],
                ],
                "user": user,
            })

    # Rank by a seeded hash, then cycle over all six clause permutations. This
    # retains deterministic pseudo-random assignment while guaranteeing that
    # each policy type occupies each serial position equally up to one request.
    ranked = sorted(
        pending,
        key=lambda row: hashlib.sha256(f"{seed}|{row['sample_id']}".encode()).hexdigest(),
    )
    permutations = [
        (0, 1, 2), (1, 2, 0), (2, 0, 1),
        (0, 2, 1), (2, 1, 0), (1, 0, 2),
    ]
    samples: list[dict[str, Any]] = []
    for index, row in enumerate(ranked):
        clauses = [row["clauses"][i] for i in permutations[index % len(permutations)]]
        system = SYSTEM_PREFIX + "\n- " + "\n- ".join(clauses)
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": row["user"]},
        ]
        samples.append({
            **{key: value for key, value in row.items() if key not in {"clauses", "user"}},
            "messages": messages,
            "prompt_sha256": canonical_hash(messages),
            "prompt_chars": sum(len(m["content"]) for m in messages),
        })
    return sorted(samples, key=lambda row: row["sample_id"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, default=Path("data/factorial_prompt_spec_v1.json"))
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/factorial_prompt_v1"))
    args = parser.parse_args()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    samples = build_samples(spec)
    expected = (
        len(spec["problem_families"]) * int(spec["base_problems_per_family"])
        * len(spec["learner_needs"])
        * len(spec["factors"]["question_policy"])
        * len(spec["factors"]["answer_policy"])
        * len(spec["factors"]["tone_policy"])
    )
    if len(samples) != expected or len({r["sample_id"] for r in samples}) != expected:
        raise RuntimeError(f"factorial panel invariant failed: {len(samples)} != {expected}")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = args.output_dir / "sample_manifest.jsonl"
    with manifest_path.open("w", encoding="utf-8") as handle:
        for row in samples:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    summary = {
        "schema_version": 1,
        "seed": spec["seed"],
        "base_problem_count": len({r["base_id"] for r in samples}),
        "sample_count": len(samples),
        "model_count": len(spec["models"]),
        "expected_calls": len(samples) * len(spec["models"]),
        "manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        "spec_sha256": hashlib.sha256(args.spec.read_bytes()).hexdigest(),
        "prompt_chars": {
            "min": min(r["prompt_chars"] for r in samples),
            "max": max(r["prompt_chars"] for r in samples),
            "mean": sum(r["prompt_chars"] for r in samples) / len(samples),
        },
        "payload_scope": "synthetic problem, synthetic learner work/request, frozen policy clauses",
        "potential_pii_pattern_flags": {
            "email": sum(
                bool(re.search(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", message["content"], re.I))
                for row in samples for message in row["messages"]
            ),
            "url": sum(
                bool(re.search(r"https?://", message["content"], re.I))
                for row in samples for message in row["messages"]
            ),
            "phone_like": sum(
                bool(re.search(r"(?<!\d)(?:\+?\d[ -]?){10,14}(?!\d)", message["content"]))
                for row in samples for message in row["messages"]
            ),
        },
    }
    (args.output_dir / "design_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
