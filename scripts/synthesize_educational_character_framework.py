#!/usr/bin/env python3
"""Synthesize the repository's educational-character evidence into one audit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd


AXES = (
    "instructional_agency",
    "relational_communion",
    "assistance_directness",
    "next_step_actionability",
    "epistemic_commitment",
    "learner_contingency",
)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def formal_status(row: dict[str, Any], family_robust: bool) -> str:
    if not row.get("measurement_gates", {}).get("pilot_measurement_pass", False):
        return "exploratory_only_pilot_measurement_failure"
    signature_gates = row.get("signature_gates", {})
    other_signature_gates = [
        value for key, value in signature_gates.items()
        if key != "maximum_abs_old_scale_rho_below_0_80"
    ]
    core_signature = bool(row.get("reliable_measurement") and all(other_signature_gates))
    nonredundant = bool(signature_gates.get("maximum_abs_old_scale_rho_below_0_80"))
    if core_signature and not nonredundant:
        return "reliable_cross_task_pattern_redundant_with_old_scale"
    if not row.get("cross_task_signature"):
        return "formal_cross_task_signature_not_supported"
    if not family_robust:
        return "finite_panel_signature_judge_family_sensitive"
    if row.get("validated_character_axis"):
        return "validated_behavioral_character_axis"
    return "finite_panel_cross_task_signature"


def evidence_rows(
    formal: dict[str, Any], family: dict[str, Any], submission: dict[str, Any],
    epistemic: dict[str, Any], normative: dict[str, Any], prompt: dict[str, Any],
) -> list[dict[str, Any]]:
    formal_rows = {row["dimension"]: row for row in formal["classification"]}
    family_rows = {
        row["dimension"]: bool(row["judge_family_robust"])
        for row in family["classification"]
    }
    directness_validated = "help_directness" in submission["validated_disposition_dimensions"]
    confidence_robust = "expressed_confidence" in epistemic["robust_trait_like_axes"]
    prompt_supported = prompt.get("verdict") == "prompt_contingent_policy_signatures_supported"
    normative_rejected = normative.get("candidate_axis_supported") is False
    rows = []
    for axis in AXES:
        if axis in formal_rows:
            status = formal_status(formal_rows[axis], family_rows.get(axis, False))
            source = "confirmatory_character_panel_v1/formal"
            prompt_status = "matched_prompt_effect_estimated"
        elif axis == "assistance_directness":
            status = (
                "validated_behavioral_character_axis" if directness_validated
                else "not_supported"
            )
            source = "submission_decision_and_prompt_contingent_signatures_v1"
            prompt_status = (
                "replicated_model_specific_prompt_elasticity"
                if prompt_supported else "not_supported"
            )
        elif axis == "epistemic_commitment":
            status = (
                "finite_panel_expressed_confidence_signature_with_mixed_facets"
                if confidence_robust else "not_supported"
            )
            source = "epistemic_character_axes_v1"
            prompt_status = "matched_epistemic_prompt_elasticity_not_tested"
        else:
            status = "negative_boundary_learner_contingency_not_supported"
            source = "factorial_and_longtutor_negative_results"
            prompt_status = "system_policy_dominates_observed_learner_evidence"
        rows.append({
            "axis": axis,
            "classification": status,
            "evidence_source": source,
            "prompt_status": prompt_status,
            "normative_permissiveness_rejected": normative_rejected,
            "claim_unit": "fixed_deployed_model_configuration",
        })
    return rows


def weighted_profiles(frame: pd.DataFrame, value: str) -> pd.DataFrame:
    data = frame.copy()
    data["weighted"] = data[value] * data["contexts"]
    grouped = data.groupby(["model", "dimension"], as_index=False).agg(
        weighted_sum=("weighted", "sum"), contexts=("contexts", "sum")
    )
    grouped["estimate"] = grouped["weighted_sum"] / grouped["contexts"]
    return grouped


def profile_rows(
    formal_profiles: pd.DataFrame, semantic_profiles: pd.DataFrame,
    epistemic_profiles: pd.DataFrame,
) -> pd.DataFrame:
    rows = []
    formal_default = formal_profiles[formal_profiles["arm"] == "generic"]
    for record in weighted_profiles(formal_default, "centered_mean").to_dict("records"):
        rows.append({
            "axis": record["dimension"], "model": record["model"],
            "estimate": record["estimate"], "metric": "exact_item_centered_default_score",
            "contexts": int(record["contexts"]), "source": "confirmatory_formal",
        })
    directness = semantic_profiles[semantic_profiles["dimension"] == "help_directness"].copy()
    directness["contexts"] = directness["contexts"].astype(int)
    directness["dimension"] = "assistance_directness"
    directness = directness.rename(columns={"mean_item_centered_score": "value"})
    for record in weighted_profiles(directness, "value").to_dict("records"):
        rows.append({
            "axis": record["dimension"], "model": record["model"],
            "estimate": record["estimate"], "metric": "exact_item_centered_default_score",
            "contexts": int(record["contexts"]), "source": "frozen_semantic_panel",
        })
    for record in epistemic_profiles.to_dict("records"):
        rows.append({
            "axis": "epistemic_commitment", "model": record["model"],
            "estimate": float(record["expressed_confidence"]),
            "metric": "expressed_confidence", "contexts": None,
            "source": "epistemic_character_axes_v1",
        })
    return pd.DataFrame(rows)


def elasticity_rows(
    formal_prompt: pd.DataFrame, semantic_prompt: pd.DataFrame,
) -> pd.DataFrame:
    formal = formal_prompt[["task", "model", "dimension", "paired_contexts", "mean_delta"]].copy()
    formal = formal.rename(columns={"dimension": "axis", "paired_contexts": "contexts"})
    formal["source"] = "confirmatory_formal"
    direct = semantic_prompt[semantic_prompt["dimension"] == "help_directness"][
        ["task", "model", "contexts", "mean_delta"]
    ].copy()
    direct["axis"] = "assistance_directness"
    direct["source"] = "frozen_semantic_panel"
    return pd.concat(
        [formal[["task", "model", "axis", "contexts", "mean_delta", "source"]],
         direct[["task", "model", "axis", "contexts", "mean_delta", "source"]]],
        ignore_index=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--formal-decision", type=Path, required=True)
    parser.add_argument("--family-sensitivity", type=Path, required=True)
    parser.add_argument("--submission-decision", type=Path, required=True)
    parser.add_argument("--epistemic-decision", type=Path, required=True)
    parser.add_argument("--normative-decision", type=Path, required=True)
    parser.add_argument("--prompt-decision", type=Path, required=True)
    parser.add_argument("--formal-profiles", type=Path, required=True)
    parser.add_argument("--semantic-profiles", type=Path, required=True)
    parser.add_argument("--epistemic-profiles", type=Path, required=True)
    parser.add_argument("--formal-prompt", type=Path, required=True)
    parser.add_argument("--semantic-prompt", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    evidence = evidence_rows(
        read_json(args.formal_decision), read_json(args.family_sensitivity),
        read_json(args.submission_decision), read_json(args.epistemic_decision),
        read_json(args.normative_decision), read_json(args.prompt_decision),
    )
    evidence_frame = pd.DataFrame(evidence)
    profiles = profile_rows(
        pd.read_csv(args.formal_profiles), pd.read_csv(args.semantic_profiles),
        pd.read_csv(args.epistemic_profiles),
    )
    elasticity = elasticity_rows(
        pd.read_csv(args.formal_prompt), pd.read_csv(args.semantic_prompt),
    )
    classifications = evidence_frame.set_index("axis")["classification"].to_dict()
    supported = [
        axis for axis, status in classifications.items()
        if "validated" in status or "finite_panel" in status
    ]
    redundant = [
        axis for axis, status in classifications.items() if "redundant" in status
    ]
    exploratory = [
        axis for axis, status in classifications.items() if "exploratory" in status
    ]
    rejected = [
        axis for axis, status in classifications.items()
        if "not_supported" in status or "negative_boundary" in status
    ]
    decision = {
        "schema_version": 1,
        "recommended_thesis": "prompt_contingent_pedagogical_policy_signatures",
        "supported_axes": supported,
        "bounded_redundant_axes": redundant,
        "exploratory_axes": exploratory,
        "rejected_or_unsupported_axes": rejected,
        "axis_classifications": classifications,
        "prompt_elasticity_is_meta_property": True,
        "normative_permissiveness_is_not_a_unified_axis": True,
        "claim_boundary": (
            "Classifications describe six fixed deployed configurations. They do not establish "
            "human-like personality, consciousness, learner understanding, or learning gains."
        ),
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    evidence_frame.to_csv(args.output_dir / "dimension_evidence.csv", index=False)
    profiles.to_csv(args.output_dir / "model_profiles.csv", index=False)
    elasticity.to_csv(args.output_dir / "prompt_elasticity.csv", index=False)
    (args.output_dir / "decision.json").write_text(
        json.dumps(decision, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    report = "\n".join([
        "# Educational-character framework synthesis", "",
        "## Dimension evidence", "", evidence_frame.to_markdown(index=False), "",
        "## Decision", "", "```json", json.dumps(decision, ensure_ascii=False, indent=2), "```", "",
    ])
    (args.output_dir / "report.md").write_text(report, encoding="utf-8")
    print(json.dumps(decision, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
