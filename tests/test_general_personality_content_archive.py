from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from audit_general_personality_content_archive import construct_coverage, relation_table


def test_construct_map_covers_requested_taxonomies() -> None:
    manifest = json.loads((ROOT / "data/general_personality_construct_map_v1.json").read_text())
    coverage = construct_coverage(manifest)
    assert len(coverage) == 22
    assert set(coverage.loc[coverage["taxonomy"] == "Big Five", "construct"]) == {
        "agreeableness",
        "extraversion",
        "conscientiousness",
        "openness",
        "neuroticism_or_emotional_stability",
    }
    assert len(coverage[coverage["taxonomy"] == "Schwartz values"]) == 10
    assert len(coverage[coverage["taxonomy"] == "Dark Triad"]) == 3


def test_relation_table_respects_expected_direction() -> None:
    models = [f"m{i}" for i in range(6)]
    frame = pd.DataFrame({"model": models})
    required = {
        "communal_expression", "relational_communion", "organizational_style",
        "ifeval_accuracy", "net_revision_gain", "overall_accuracy",
        "epistemic_caution_language", "overconfidence_gap", "abstention_selectivity",
        "boundary_refusal_expression", "adversarial_boundary_enforcement",
        "educational_refusal_share", "sata_incorrect_inclusion",
    }
    for column in required:
        frame[column] = range(6)
    result = relation_table(frame)
    agree = result[result["construct_cluster"] == "agreeableness_affiliation"].iloc[0]
    honesty_overconfidence = result[
        (result["construct_cluster"] == "honesty_humility_epistemic_honesty")
        & (result["right_indicator"] == "overconfidence_gap")
    ].iloc[0]
    assert agree["direction_matches"]
    assert not honesty_overconfidence["direction_matches"]
