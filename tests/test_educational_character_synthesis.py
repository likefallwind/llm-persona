from __future__ import annotations

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from synthesize_educational_character_framework import evidence_rows, formal_status


def test_formal_status_separates_redundancy_from_signature() -> None:
    row = {
        "measurement_gates": {"pilot_measurement_pass": True},
        "reliable_measurement": True,
        "signature_gates": {
            "cross_task_icc_or_rank_at_least_0_50": True,
            "all_observed_benchmark_variance_ci_above_zero": True,
            "maximum_abs_old_scale_rho_below_0_80": False,
        },
        "cross_task_signature": False,
        "validated_character_axis": False,
    }
    assert formal_status(row, True) == "reliable_cross_task_pattern_redundant_with_old_scale"
    row["signature_gates"]["maximum_abs_old_scale_rho_below_0_80"] = True
    row["cross_task_signature"] = True
    assert formal_status(row, True) == "finite_panel_cross_task_signature"


def test_synthesis_always_preserves_six_axis_boundary() -> None:
    formal_row = {
        "dimension": "instructional_agency",
        "measurement_gates": {"pilot_measurement_pass": False},
        "reliable_measurement": False,
        "signature_gates": {},
        "cross_task_signature": False,
    }
    rows = evidence_rows(
        {"classification": [formal_row]},
        {"classification": [{"dimension": "instructional_agency", "judge_family_robust": False}]},
        {"validated_disposition_dimensions": ["help_directness"]},
        {"robust_trait_like_axes": ["expressed_confidence"]},
        {"candidate_axis_supported": False},
        {"verdict": "prompt_contingent_policy_signatures_supported"},
    )
    assert len(rows) == 6
    assert rows[0]["classification"] == "exploratory_only_pilot_measurement_failure"
    assert rows[-1]["classification"] == "negative_boundary_learner_contingency_not_supported"
