#!/usr/bin/env python3
"""Check whether the compact confirmatory rubric preserves pilot measurements."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import pandas as pd
from scipy.stats import spearmanr


SOURCES = {
    "instructional_agency": "theory",
    "relational_communion": "theory",
    "next_step_actionability": "structure",
}


def correlation(left: pd.Series, right: pd.Series) -> float:
    if len(left) < 3 or not left.std() or not right.std():
        return math.nan
    return float(spearmanr(left, right).statistic)


def bridge_dimension(new: pd.DataFrame, old: pd.DataFrame, dimension: str) -> dict[str, Any]:
    keys = ["benchmark", "item_id", "pair_id", "model", "response_sha256", "dimension"]
    merged = new[new["dimension"] == dimension][keys + ["score"]].merge(
        old[old["dimension"] == dimension][keys + ["score"]],
        on=keys,
        suffixes=("_new", "_old"),
        validate="one_to_one",
    )
    merged["centered_new"] = merged["score_new"] - merged.groupby(
        ["benchmark", "item_id"]
    )["score_new"].transform("mean")
    merged["centered_old"] = merged["score_old"] - merged.groupby(
        ["benchmark", "item_id"]
    )["score_old"].transform("mean")
    profiles = merged.groupby("model", as_index=False).agg(
        new=("centered_new", "mean"), old=("centered_old", "mean")
    )
    response_rho = correlation(merged["score_new"], merged["score_old"])
    centered_rho = correlation(merged["centered_new"], merged["centered_old"])
    profile_rho = correlation(profiles["new"], profiles["old"])
    gates = {
        "all_180_responses_matched": len(merged) == 180,
        "uncentered_score_spearman_at_least_0_70": bool(response_rho >= .70),
        "item_centered_response_spearman_at_least_0_60": bool(centered_rho >= .60),
        "six_model_profile_spearman_at_least_0_70": bool(profile_rho >= .70),
    }
    return {
        "dimension": dimension,
        "matched_responses": len(merged),
        "uncentered_score_spearman": response_rho,
        "item_centered_response_spearman": centered_rho,
        "model_profile_spearman": profile_rho,
        "mean_absolute_score_difference": float((merged["score_new"] - merged["score_old"]).abs().mean()),
        "gates": gates,
        "bridge_pass": all(gates.values()),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--new-consensus", type=Path, required=True)
    parser.add_argument("--theory-consensus", type=Path, required=True)
    parser.add_argument("--structure-consensus", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    new = pd.read_csv(args.new_consensus)
    old_sources = {
        "theory": pd.read_csv(args.theory_consensus),
        "structure": pd.read_csv(args.structure_consensus),
    }
    results = [
        bridge_dimension(new, old_sources[source], dimension)
        for dimension, source in SOURCES.items()
    ]
    decision = {
        "schema_version": 1,
        "threshold_status": "fixed_before_confirmatory_bridge_calls",
        "dimensions": results,
        "all_dimensions_bridge_pass": all(row["bridge_pass"] for row in results),
        "boundary": (
            "A bridge pass licenses use of the compact rubric on the untouched formal split; "
            "it does not itself establish a cross-task model-character signature."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(decision, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(decision, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
