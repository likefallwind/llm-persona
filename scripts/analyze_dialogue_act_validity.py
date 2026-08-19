#!/usr/bin/env python3
"""Independent dialogue-act validity from MathDial's human annotations.

Train a conventional text classifier on human teacher turns, validate it with
problem-grouped cross-validation, then apply it to model responses. No LLM judge
or new human annotation is used, and generated response text is not copied into
the output artifacts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import binomtest
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, balanced_accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import StratifiedGroupKFold, cross_val_predict
from sklearn.pipeline import FeatureUnion, make_pipeline
from sklearn.svm import LinearSVC

from run_behavioral_pilot import read_latest_success
from inventory_paths import resolve_inventory_path


ACTS = ("probing", "focus", "telling", "generic")
TASKS = {
    "mathtutorbench_scaffolding": ("standard", "generic", "mathdial_bridge.json"),
    "mathtutorbench_pedagogy": ("standard", "pedagogy", "mathdial_bridge.json"),
    "mathtutorbench_scaffolding_hard": ("hard", "generic", "mathdial_bridge_hard.json"),
    "mathtutorbench_pedagogy_hard": ("hard", "pedagogy", "mathdial_bridge_hard.json"),
}


def normalize(text: str) -> str:
    value = unicodedata.normalize("NFKC", str(text or "")).lower().strip()
    value = re.sub(r"\s+", " ", value)
    return re.sub(r"[^a-z0-9? ]", "", value)


def human_turns(mathdial_dir: Path) -> tuple[pd.DataFrame, dict[str, Counter[str]]]:
    rows: list[dict[str, str]] = []
    lookup: dict[str, Counter[str]] = defaultdict(Counter)
    for split in ("train", "test"):
        with (mathdial_dir / f"{split}.jsonl").open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle):
                example = json.loads(line)
                qid = str(example.get("qid") or f"{split}-{line_number}")
                conversation_id = f"{split}-{line_number}"
                for turn_number, segment in enumerate(str(example.get("conversation") or "").split("|EOM|")):
                    match = re.match(r"Teacher:\s*\(([^)]+)\)(.*)", segment, flags=re.DOTALL)
                    if not match:
                        continue
                    act = match.group(1).strip().lower()
                    text = match.group(2).strip()
                    if act not in ACTS or not text:
                        continue
                    rows.append({
                        "split": split,
                        "qid": qid,
                        "conversation_id": conversation_id,
                        "turn_number": str(turn_number),
                        "text": text,
                        "act": act,
                    })
                    lookup[normalize(text)][act] += 1
    return pd.DataFrame(rows), lookup


def classifiers() -> dict[str, Any]:
    char = TfidfVectorizer(
        analyzer="char_wb", ngram_range=(3, 5), min_df=2, max_features=80000, sublinear_tf=True
    )
    word = TfidfVectorizer(
        analyzer="word", ngram_range=(1, 2), min_df=2, max_features=60000,
        sublinear_tf=True, strip_accents="unicode",
    )
    return {
        "char_svm": make_pipeline(char, LinearSVC(C=2.0, class_weight="balanced")),
        "word_svm": make_pipeline(word, LinearSVC(C=2.0, class_weight="balanced")),
        "hybrid_svm": make_pipeline(
            FeatureUnion([
                ("char", TfidfVectorizer(
                    analyzer="char_wb", ngram_range=(3, 5), min_df=2,
                    max_features=60000, sublinear_tf=True,
                )),
                ("word", TfidfVectorizer(
                    analyzer="word", ngram_range=(1, 2), min_df=2,
                    max_features=40000, sublinear_tf=True, strip_accents="unicode",
                )),
            ]),
            LinearSVC(C=1.5, class_weight="balanced"),
        ),
    }


def resolve_target_act(turn: dict[str, Any], lookup: dict[str, Counter[str]]) -> tuple[str | None, str]:
    direct = str(turn.get("dialog_act") or "").strip().lower()
    if direct in ACTS:
        return direct, "bridge_direct"
    counts = lookup.get(normalize(str(turn.get("text") or "")), Counter())
    if not counts:
        return None, "unmatched"
    best = max(counts.values())
    winners = [label for label, count in counts.items() if count == best]
    if len(winners) != 1:
        return None, "ambiguous"
    return winners[0], "exact_human_lookup"


def load_targets(bridge_dir: Path, lookup: dict[str, Counter[str]]) -> tuple[dict[tuple[str, str], dict[str, str]], pd.DataFrame]:
    targets: dict[tuple[str, str], dict[str, str]] = {}
    audit_rows = []
    for benchmark, (family, _arm, filename) in TASKS.items():
        examples = json.loads((bridge_dir / filename).read_text(encoding="utf-8"))
        prefix = benchmark.split("_")[-1]
        for idx, example in enumerate(examples):
            final_turn = example["dialog_history"][-1]
            target, source = resolve_target_act(final_turn, lookup)
            item_id = f"{prefix}-{idx}"
            targets[(benchmark, item_id)] = {
                "target_act": target or "",
                "target_source": source,
                "family": family,
                "pair_id": str(idx),
            }
            audit_rows.append({
                "benchmark": benchmark,
                "family": family,
                "item_id": item_id,
                "target_act": target,
                "target_source": source,
            })
    return targets, pd.DataFrame(audit_rows)


def bootstrap_delta(values: np.ndarray, seed: int, reps: int = 4000) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    draws = rng.choice(values, size=(reps, len(values)), replace=True).mean(axis=1)
    return float(np.quantile(draws, 0.025)), float(np.quantile(draws, 0.975))


def paired_effects(predictions: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (variant, family, model), group in predictions.groupby(["classifier_variant", "family", "model"]):
        wide = group.pivot_table(index="pair_id", columns="arm", values="act_match", aggfunc="last").dropna()
        if not {"generic", "pedagogy"}.issubset(wide.columns):
            continue
        delta = (wide["pedagogy"] - wide["generic"]).to_numpy()
        improved = int(((wide["generic"] == 0) & (wide["pedagogy"] == 1)).sum())
        worsened = int(((wide["generic"] == 1) & (wide["pedagogy"] == 0)).sum())
        discordant = improved + worsened
        p_value = float(binomtest(improved, discordant, 0.5, alternative="two-sided").pvalue) if discordant else 1.0
        lo, hi = bootstrap_delta(delta, 20260819 + len(rows))
        rows.append({
            "classifier_variant": variant,
            "family": family,
            "model": model,
            "n_pairs": len(wide),
            "generic_match": float(wide["generic"].mean()),
            "pedagogy_match": float(wide["pedagogy"].mean()),
            "mean_delta": float(delta.mean()),
            "bootstrap_ci_low": lo,
            "bootstrap_ci_high": hi,
            "improved_pairs": improved,
            "worsened_pairs": worsened,
            "mcnemar_exact_p": p_value,
        })
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--mathdial-dir", type=Path, required=True)
    parser.add_argument("--bridge-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    turns, lookup = human_turns(args.mathdial_dir)
    cv = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=20260819)
    fitted_models: dict[str, Any] = {}
    cv_rows = []
    per_class_frames = []
    confusion_frames = []
    for variant, estimator in classifiers().items():
        oof = cross_val_predict(estimator, turns["text"], turns["act"], groups=turns["qid"], cv=cv, n_jobs=1)
        cv_rows.append({
            "classifier_variant": variant,
            "human_teacher_turns": len(turns),
            "unique_problems": turns["qid"].nunique(),
            "accuracy": accuracy_score(turns["act"], oof),
            "balanced_accuracy": balanced_accuracy_score(turns["act"], oof),
            "macro_f1": f1_score(turns["act"], oof, average="macro"),
        })
        report = pd.DataFrame(
            classification_report(turns["act"], oof, labels=list(ACTS), output_dict=True, zero_division=0)
        ).T.reset_index(names="label")
        report.insert(0, "classifier_variant", variant)
        per_class_frames.append(report)
        matrix = pd.DataFrame(confusion_matrix(turns["act"], oof, labels=list(ACTS)), index=ACTS, columns=ACTS)
        matrix.insert(0, "true_act", matrix.index)
        matrix.insert(0, "classifier_variant", variant)
        confusion_frames.append(matrix.reset_index(drop=True))
        fitted_models[variant] = estimator.fit(turns["text"], turns["act"])
    cv_summary = pd.DataFrame(cv_rows)
    per_class = pd.concat(per_class_frames, ignore_index=True)
    cv_confusion = pd.concat(confusion_frames, ignore_index=True)
    targets, target_audit = load_targets(args.bridge_dir, lookup)
    inventory = json.loads(args.inventory.read_text(encoding="utf-8"))
    selected = {(run["benchmark"], run["model"]): run for run in inventory["selected_runs"]}
    available_models = sorted({m for (b, m) in selected if b in TASKS and all((task, m) in selected for task in TASKS)})
    prediction_rows = []
    for benchmark, (family, arm, _filename) in TASKS.items():
        for candidate_model in available_models:
            responses = read_latest_success(
                resolve_inventory_path(selected[(benchmark, candidate_model)]["predictions_path"])
            )
            for item_id, row in responses.items():
                target = targets.get((benchmark, item_id))
                if not target or not target["target_act"]:
                    continue
                response = row["response"]
                for variant, fitted in fitted_models.items():
                    predicted_act = str(fitted.predict([response])[0])
                    prediction_rows.append({
                        "classifier_variant": variant,
                        "benchmark": benchmark,
                        "family": family,
                        "arm": arm,
                        "pair_id": target["pair_id"],
                        "item_id": item_id,
                        "model": candidate_model,
                        "target_act": target["target_act"],
                        "target_source": target["target_source"],
                        "predicted_act": predicted_act,
                        "act_match": int(predicted_act == target["target_act"]),
                        "response_sha256": hashlib.sha256(response.encode("utf-8")).hexdigest(),
                    })
    predictions = pd.DataFrame(prediction_rows)
    effects = paired_effects(predictions)
    match_summary = predictions.groupby(["classifier_variant", "family", "arm", "model"])["act_match"].agg(["count", "mean"]).reset_index()
    by_target = predictions.groupby(["classifier_variant", "family", "arm", "target_act"])["act_match"].agg(["count", "mean"]).reset_index()
    act_distribution = predictions.groupby(["classifier_variant", "family", "arm", "model", "predicted_act"]).size().rename("count").reset_index()
    act_distribution["share"] = act_distribution["count"] / act_distribution.groupby(["classifier_variant", "family", "arm", "model"])["count"].transform("sum")
    effect_robustness = effects.groupby(["classifier_variant", "family"])["mean_delta"].agg(
        model_count="count", positive_models=lambda values: int((values > 0).sum()),
        minimum_delta="min", mean_delta="mean", maximum_delta="max",
    ).reset_index()
    pooled_distribution = act_distribution.groupby(
        ["classifier_variant", "family", "arm", "predicted_act"]
    )["count"].sum().reset_index()
    pooled_distribution["share"] = pooled_distribution["count"] / pooled_distribution.groupby(
        ["classifier_variant", "family", "arm"]
    )["count"].transform("sum")
    distribution_shift = pooled_distribution.pivot_table(
        index=["classifier_variant", "family", "predicted_act"], columns="arm", values="share"
    ).reset_index()
    distribution_shift["pedagogy_minus_generic"] = distribution_shift["pedagogy"] - distribution_shift["generic"]

    cv_summary.to_csv(args.output_dir / "classifier_cv_summary.csv", index=False)
    per_class.to_csv(args.output_dir / "classifier_cv_per_class.csv", index=False)
    cv_confusion.to_csv(args.output_dir / "classifier_cv_confusion.csv", index=False)
    target_audit.to_csv(args.output_dir / "target_mapping_audit.csv", index=False)
    predictions.to_csv(args.output_dir / "generated_dialogue_acts.csv", index=False)
    effects.to_csv(args.output_dir / "paired_prompt_effects.csv", index=False)
    match_summary.to_csv(args.output_dir / "match_summary.csv", index=False)
    by_target.to_csv(args.output_dir / "match_by_target_act.csv", index=False)
    act_distribution.to_csv(args.output_dir / "predicted_act_distribution.csv", index=False)
    effect_robustness.to_csv(args.output_dir / "effect_robustness.csv", index=False)
    distribution_shift.to_csv(args.output_dir / "pooled_act_distribution_shift.csv", index=False)

    target_coverage = target_audit.groupby(["benchmark", "target_source"]).size().unstack(fill_value=0).reset_index()
    effect_overall = effects.groupby(["classifier_variant", "family"])[["generic_match", "pedagogy_match", "mean_delta"]].mean().reset_index()
    report = "\n".join([
        "# Human-labelled dialogue-act validity",
        "",
        "This analysis uses MathDial's existing human teacher-move labels and a conventional character TF-IDF linear classifier. No LLM judge and no new human annotation is used. Generated response text is represented only by hashes and predicted labels in the saved artifacts.",
        "",
        "## Problem-grouped classifier validation",
        "",
        cv_summary.to_markdown(index=False, floatfmt=".3f"),
        "",
        per_class[per_class["label"].isin(ACTS)].to_markdown(index=False, floatfmt=".3f"),
        "",
        "All turns sharing a MathDial problem ID remain in the same fold, so the score does not rely on seeing another conversation about the same math problem.",
        "",
        "## Bridge target coverage",
        "",
        target_coverage.to_markdown(index=False),
        "",
        "`exact_human_lookup` means the held-out teacher response text maps to one unambiguous human label in the original MathDial release. `bridge_direct` uses the label retained in the bridge file. Ambiguous and unmatched targets are excluded before model outcomes are examined.",
        "",
        "## Objective action match by model and prompt",
        "",
        match_summary.to_markdown(index=False, floatfmt=".3f"),
        "",
        "## Cross-classifier directional robustness",
        "",
        effect_robustness.to_markdown(index=False, floatfmt=".3f"),
        "",
        "All 54 classifier × difficulty × model prompt contrasts are positive if `positive_models` equals 9 in every row.",
        "",
        "## Paired prompt effect on matching the human next action",
        "",
        effects.to_markdown(index=False, floatfmt=".3f"),
        "",
        effect_overall.to_markdown(index=False, floatfmt=".3f"),
        "",
        "## Match by human target action",
        "",
        by_target.to_markdown(index=False, floatfmt=".3f"),
        "",
        "## How the prompt changes the inferred action distribution",
        "",
        distribution_shift.to_markdown(index=False, floatfmt=".3f"),
        "",
        "## Interpretation boundary",
        "",
        "This is independent of LLM-as-judge preferences, but it measures action-type agreement with the observed human teacher, not student learning or full response quality. The classifier's grouped cross-validation score bounds how literally generated-label matches should be interpreted.",
        "",
    ])
    (args.output_dir / "dialogue_act_validity_report.md").write_text(report, encoding="utf-8")
    print(args.output_dir / "dialogue_act_validity_report.md")


if __name__ == "__main__":
    main()
