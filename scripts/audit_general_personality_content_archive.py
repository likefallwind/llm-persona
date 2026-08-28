#!/usr/bin/env python3
"""Audit general-personality construct coverage in existing EduBenchmark data.

This is a secondary synthesis of released aggregate artifacts. It never reads or
exports response text and it does not convert behavioral indicators into human
personality scores.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from analyze_existing_general_personality_bridge import exact_spearman_p


MODELS = (
    "deepseek-v4-pro",
    "doubao-seed-2.0-pro",
    "glm-5.2",
    "minimax-m2.7",
    "minimax-m3",
    "qwen3.5-4b",
)

IFEVAL_DIRS = {
    "deepseek-v4-pro": "deepseek-v4-pro",
    "doubao-seed-2.0-pro": "doubao-seed-2.0-pro",
    "glm-5.2": "glm-5.2",
    "minimax-m2.7": "MiniMax-M2.7",
    "minimax-m3": "minimax3",
    "qwen3.5-4b": "Qwen-Qwen3.5-4B",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def bh_adjust(values: pd.Series) -> pd.Series:
    raw = values.fillna(1.0).to_numpy(float)
    order = np.argsort(raw)
    ranked = raw[order]
    adjusted = np.minimum.accumulate(
        (ranked * len(raw) / np.arange(1, len(raw) + 1))[::-1]
    )[::-1]
    output = np.empty(len(raw), dtype=float)
    output[order] = np.minimum(adjusted, 1.0)
    return pd.Series(output, index=values.index)


def construct_coverage(manifest: dict[str, Any]) -> pd.DataFrame:
    rows = []
    for row in manifest["constructs"]:
        rows.append({
            **row,
            "candidate_indicators": ";".join(row["candidate_indicators"]),
        })
    return pd.DataFrame(rows)


def measurement_coverage(manifest: dict[str, Any]) -> pd.DataFrame:
    layer_rows = [
        {"audit_type": "measurement_layer", "name": row["layer"], **row}
        for row in manifest["measurement_layers"]
    ]
    perturbation_rows = [
        {"audit_type": "stability_perturbation", "name": row["perturbation"], **row}
        for row in manifest["stability_tests"]
    ]
    frame = pd.DataFrame(layer_rows + perturbation_rows)
    return frame.drop(columns=[column for column in ("layer", "perturbation") if column in frame])


def load_ifeval_accuracy(edubench_root: Path) -> pd.Series:
    values = {}
    for model, directory in IFEVAL_DIRS.items():
        path = edubench_root / "reports" / "eval" / "ifeval" / directory / "summary.json"
        values[model] = float(load_json(path)["accuracy"])
    return pd.Series(values, name="ifeval_accuracy")


def build_indicator_profiles(root: Path, edubench_root: Path) -> pd.DataFrame:
    domain = pd.read_csv(root / "artifacts/general_personality_bridge_v1/domain_axis_profiles.csv")
    non_tutoring = domain[~domain["domain"].isin(["default_tutoring", "prompted_tutoring"])]
    general = non_tutoring.groupby("model", sort=True)[
        [
            "communal_expression",
            "dialogic_engagement",
            "directive_expression",
            "epistemic_caution_language",
            "boundary_refusal_expression",
            "organizational_style",
            "verbosity",
        ]
    ].mean()

    education = pd.read_csv(root / "artifacts/educational_character_framework_v1/model_profiles.csv")
    education = education.pivot(index="model", columns="axis", values="estimate")
    epistemic = pd.read_csv(root / "artifacts/epistemic_character_axes_v1/model_profiles.csv").set_index("model")
    boundary = pd.read_csv(root / "artifacts/normative_boundary_axes_v1/model_profiles.csv").set_index("model")

    profiles = general.join(education, how="inner").join(epistemic, how="inner").join(boundary, how="inner")
    profiles = profiles.join(load_ifeval_accuracy(edubench_root), how="inner")
    profiles = profiles.loc[list(MODELS)]
    profiles.index.name = "model"
    return profiles.reset_index()


RELATION_SPECS = (
    ("agreeableness_affiliation", "communal_expression", "relational_communion", 1,
     "open non-tutoring language versus independently judged educational communion"),
    ("conscientiousness_diligence", "organizational_style", "ifeval_accuracy", 1,
     "organization versus objective instruction following; capability/style confounded"),
    ("conscientiousness_diligence", "organizational_style", "net_revision_gain", 1,
     "organization versus objectively beneficial answer revision; capability confounded"),
    ("conscientiousness_diligence", "organizational_style", "overall_accuracy", 1,
     "organization versus self-monitoring accuracy; capability confounded"),
    ("honesty_humility_epistemic_honesty", "epistemic_caution_language", "overconfidence_gap", -1,
     "caution wording versus objective overconfidence"),
    ("honesty_humility_epistemic_honesty", "epistemic_caution_language", "abstention_selectivity", 1,
     "caution wording versus selective abstention"),
    ("honesty_humility_epistemic_honesty", "epistemic_caution_language", "net_revision_gain", 1,
     "caution wording versus objectively beneficial revision"),
    ("security_conformity_policy", "boundary_refusal_expression", "adversarial_boundary_enforcement", 1,
     "boundary wording versus adversarial boundary enforcement; provider-policy confounded"),
    ("security_conformity_policy", "boundary_refusal_expression", "educational_refusal_share", 1,
     "boundary wording versus refusal in educational safety cases; provider-policy confounded"),
    ("security_conformity_policy", "boundary_refusal_expression", "sata_incorrect_inclusion", -1,
     "boundary wording versus inappropriate option inclusion; competence/policy confounded"),
    ("security_conformity_policy", "adversarial_boundary_enforcement", "sata_incorrect_inclusion", -1,
     "two objective safety endpoints; incompatible task demands remain possible"),
)


def relation_table(profiles: pd.DataFrame) -> pd.DataFrame:
    rows = []
    indexed = profiles.set_index("model")
    for construct, left, right, expected_sign, interpretation in RELATION_SPECS:
        rho, p = exact_spearman_p(indexed[left].to_numpy(), indexed[right].to_numpy())
        rows.append({
            "construct_cluster": construct,
            "left_indicator": left,
            "right_indicator": right,
            "expected_sign": expected_sign,
            "spearman": rho,
            "direction_matches": bool(np.sign(rho) == expected_sign),
            "abs_rho_at_least_0_70": bool(abs(rho) >= 0.70),
            "exact_two_sided_p": p,
            "model_count": len(indexed),
            "interpretation_limit": interpretation,
        })
    result = pd.DataFrame(rows)
    result["bh_q_within_construct"] = result.groupby("construct_cluster", group_keys=False)[
        "exact_two_sided_p"
    ].apply(bh_adjust)
    return result


def build_construct_decisions(root: Path, relationships: pd.DataFrame) -> pd.DataFrame:
    stability = pd.read_csv(root / "artifacts/general_personality_bridge_v1/cross_task_stability.csv")
    stability = stability[stability["pool"] == "non_tutoring"].set_index("axis")
    transport = pd.read_csv(root / "artifacts/general_personality_bridge_v1/cross_domain_transport.csv")
    transport = transport[
        (transport["left_pool"] == "non_tutoring")
        & (transport["right_pool"] == "default_tutoring")
    ].set_index("axis")
    surface = pd.read_csv(root / "artifacts/general_personality_bridge_v1/surface_confound_audit.csv")
    surface = surface.groupby("axis")["candidate_max_abs_surface_rho"].max()

    agree_relation = relationships[
        relationships["construct_cluster"] == "agreeableness_affiliation"
    ].iloc[0]
    agree_localized = (
        transport.loc["communal_expression", "spearman"] >= 0.70
        and agree_relation["spearman"] >= 0.70
        and surface.loc["communal_expression"] < 0.80
    )
    rows = [
        {
            "construct_cluster": "agreeableness_affiliation_and_benevolence",
            "archive_identification": "localized_interpersonal_signal_not_trait_validation",
            "cross_task_stability": float(stability.loc["communal_expression", "median_pairwise_spearman"]),
            "cross_role_transport": float(transport.loc["communal_expression", "spearman"]),
            "strongest_behavior_bridge": float(agree_relation["spearman"]),
            "purpose_built_pilot_priority": bool(agree_localized),
            "reason": "Two cross-role/source links are strong, but individual-task recurrence fails; a targeted stability pilot can resolve the ambiguity.",
        },
        {
            "construct_cluster": "extraversion_dialogic_assertiveness",
            "archive_identification": "weak_and_faceted_candidate",
            "cross_task_stability": float(stability.loc["dialogic_engagement", "median_pairwise_spearman"]),
            "cross_role_transport": float(transport.loc["dialogic_engagement", "spearman"]),
            "strongest_behavior_bridge": float("nan"),
            "purpose_built_pilot_priority": False,
            "reason": "Dialogic recurrence is moderate, transport misses the gate, and sociability cannot be separated from teaching policy.",
        },
        {
            "construct_cluster": "conscientiousness_diligence",
            "archive_identification": "style_and_capability_confound",
            "cross_task_stability": float(stability.loc["organizational_style", "median_pairwise_spearman"]),
            "cross_role_transport": float(transport.loc["organizational_style", "spearman"]),
            "strongest_behavior_bridge": float(relationships.loc[
                relationships["construct_cluster"] == "conscientiousness_diligence", "spearman"
            ].abs().max()),
            "purpose_built_pilot_priority": False,
            "reason": "The stable signal is formatting; objective links cannot distinguish diligence from instruction-following skill or accuracy.",
        },
        {
            "construct_cluster": "honesty_humility_epistemic_honesty",
            "archive_identification": "objective_epistemic_facets_without_construct_convergence",
            "cross_task_stability": float(stability.loc["epistemic_caution_language", "median_pairwise_spearman"]),
            "cross_role_transport": float(transport.loc["epistemic_caution_language", "spearman"]),
            "strongest_behavior_bridge": float(relationships.loc[
                relationships["construct_cluster"] == "honesty_humility_epistemic_honesty", "spearman"
            ].abs().max()),
            "purpose_built_pilot_priority": False,
            "reason": "Calibration, revision, and abstention are measurable, but cautious wording neither recurs nor converges enough to identify honesty-humility.",
        },
        {
            "construct_cluster": "security_conformity_policy",
            "archive_identification": "provider_policy_and_task_demand_confound",
            "cross_task_stability": float(stability.loc["boundary_refusal_expression", "median_pairwise_spearman"]),
            "cross_role_transport": float(transport.loc["boundary_refusal_expression", "spearman"]),
            "strongest_behavior_bridge": float(relationships.loc[
                relationships["construct_cluster"] == "security_conformity_policy", "spearman"
            ].abs().max()),
            "purpose_built_pilot_priority": False,
            "reason": "Safety endpoints are real but cannot identify a personal value ordering apart from provider policy and competence.",
        },
        {
            "construct_cluster": "openness_emotional_stability_dark_triad_and_remaining_values",
            "archive_identification": "not_identifiable_in_existing_archive",
            "cross_task_stability": float("nan"),
            "cross_role_transport": float("nan"),
            "strongest_behavior_bridge": float("nan"),
            "purpose_built_pilot_priority": False,
            "reason": "Required novelty, stress, incentive, manipulation, status, risk, and explicit value-conflict opportunities are absent.",
        },
    ]
    return pd.DataFrame(rows)


def write_report(
    output_dir: Path,
    coverage: pd.DataFrame,
    measurement: pd.DataFrame,
    relationships: pd.DataFrame,
    decisions: pd.DataFrame,
) -> None:
    partial = coverage[coverage["archive_observability"] == "partial_behavioral_candidate"]
    unavailable = coverage[coverage["archive_observability"] == "not_identifiable"]
    strong = relationships[
        relationships["direction_matches"] & relationships["abs_rho_at_least_0_70"]
    ]
    report = f"""# General-personality content audit of the existing archive

This audit covers all requested Big Five dimensions, HEXACO honesty-humility,
the Dark Triad, all ten Schwartz values, adjacent cooperation/risk constructs,
measurement modalities, and stability perturbations. It uses existing aggregate
EduBenchmark results only; no generator or judge calls were made.

## Coverage

- Constructs audited: {len(coverage)}
- Partial behavioral candidates: {len(partial)}
- Not identifiable in this archive: {len(unavailable)}
- Strong expected-direction indicator links (absolute rho >= 0.70): {len(strong)}

{coverage.to_markdown(index=False)}

## Cross-indicator checks

{relationships.to_markdown(index=False, floatfmt=".3f")}

## Construct decisions

{decisions.to_markdown(index=False, floatfmt=".3f")}

## Measurement and stability gaps

{measurement.to_markdown(index=False)}

## Decision

No general human-personality construct is validated by the archive. The only
purpose-built pilot priority is the localized agreeableness/affiliation and
benevolence cluster: communal expression transports across pooled roles and
aligns with independently judged educational communion, but it is unstable
across individual non-tutoring tasks. The right follow-up is therefore a small
stability-and-transfer falsification pilot for that cluster, not a broad Big
Five, Dark Triad, or Schwartz battery.

Conscientiousness-like organization is the strongest recurring signal but is
treated as formatting/capability, not personality. Objective epistemic and
safety behaviors remain valuable axes in their own right, but their available
language manifestations do not identify honesty-humility or conservation
values. The remaining constructs are unmeasured rather than empirically absent.
"""
    (output_dir / "report.md").write_text(report, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--edubench-root", type=Path, default=Path("/home/likefallwind/code/edubenchmark"))
    parser.add_argument("--manifest", type=Path, default=Path("data/general_personality_construct_map_v1.json"))
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/general_personality_content_archive_v1"))
    args = parser.parse_args()
    root = args.root.resolve()
    manifest_path = args.manifest if args.manifest.is_absolute() else root / args.manifest
    output_dir = args.output_dir if args.output_dir.is_absolute() else root / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest = load_json(manifest_path)
    coverage = construct_coverage(manifest)
    measurement = measurement_coverage(manifest)
    profiles = build_indicator_profiles(root, args.edubench_root.resolve())
    relationships = relation_table(profiles)
    decisions = build_construct_decisions(root, relationships)

    coverage.to_csv(output_dir / "construct_coverage.csv", index=False)
    measurement.to_csv(output_dir / "measurement_and_stability_coverage.csv", index=False)
    profiles.to_csv(output_dir / "indicator_profiles.csv", index=False)
    relationships.to_csv(output_dir / "construct_bridge_tests.csv", index=False)
    decisions.to_csv(output_dir / "construct_decisions.csv", index=False)

    prioritized = decisions.loc[decisions["purpose_built_pilot_priority"], "construct_cluster"].tolist()
    decision = {
        "schema_version": 1,
        "status": "complete_existing_archive_content_audit",
        "constructs_audited": int(len(coverage)),
        "partial_behavioral_candidates": int((coverage["archive_observability"] == "partial_behavioral_candidate").sum()),
        "not_identifiable": int((coverage["archive_observability"] == "not_identifiable").sum()),
        "validated_general_personality_constructs": [],
        "purpose_built_pilot_priorities": prioritized,
        "broad_general_personality_experiment_authorized": False,
        "targeted_followup_verdict": "targeted_affiliation_stability_pilot_is_warranted" if prioritized else "no_new_pilot_trigger",
        "claim_boundary": manifest["claim_boundary"],
    }
    (output_dir / "decision.json").write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8")
    write_report(output_dir, coverage, measurement, relationships, decisions)


if __name__ == "__main__":
    main()
