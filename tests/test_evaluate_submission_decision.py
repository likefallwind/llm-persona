from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import evaluate_submission_decision as decision


DIMENSIONS = [
    "help_directness", "elicitation", "autonomy_support", "affective_warmth",
    "diagnostic_specificity", "personalization", "cognitive_load",
    "epistemic_caution",
]


@pytest.fixture
def decision_inputs(tmp_path: Path) -> dict[str, Path]:
    directories = {
        name: tmp_path / name
        for name in ("semantic", "leaveout", "scale", "objective", "output")
    }
    for path in directories.values():
        path.mkdir()

    pd.DataFrame({
        "dimension": DIMENSIONS, "icc_3_k": [.8] * 8,
    }).to_csv(directories["semantic"] / "judge_icc.csv", index=False)
    pd.DataFrame({
        "dimension": DIMENSIONS, "sd": [.8] * 8,
        "floor_fraction": [.1] * 8, "ceiling_fraction": [.1] * 8,
    }).to_csv(directories["scale"] / "consensus_scale_diagnostics.csv", index=False)
    pd.DataFrame({
        "dimension": DIMENSIONS, "icc_3_1_across_tasks": [.7] * 8,
        "median_pairwise_task_spearman": [.7] * 8,
    }).to_csv(directories["semantic"] / "cross_task_stability.csv", index=False)
    pd.DataFrame({
        "benchmark": ["task_a"] * 8, "dimension": DIMENSIONS,
        "bootstrap_ci_low": [.01] * 8,
    }).to_csv(directories["semantic"] / "model_variance_after_item_control.csv", index=False)
    pd.DataFrame({
        "held_out_task": ["task_a"], "feature_set": ["semantic"], "accuracy": [.3],
    }).to_csv(directories["semantic"] / "heldout_task_model_attribution.csv", index=False)
    pd.DataFrame({
        "held_out_model": ["m1", "m2"],
        "feature_set": ["transparent_plus_semantic"] * 2,
        "auc_gain_vs_transparent": [.05, .02],
    }).to_csv(directories["semantic"] / "quality_incremental_validity.csv", index=False)
    action_values = {dimension: 0.0 for dimension in DIMENSIONS}
    action_values.update({"help_directness": .4, "elicitation": -.4})
    pd.DataFrame({
        "dimension": DIMENSIONS,
        "telling_minus_probing_or_focus": [action_values[d] for d in DIMENSIONS],
    }).to_csv(directories["semantic"] / "dialogue_act_semantic_contrasts.csv", index=False)
    pd.DataFrame({
        "judge": ["j1"] * 8, "dimension": DIMENSIONS,
        "own_minus_other_residual": [0.0] * 8,
    }).to_csv(directories["semantic"] / "judge_family_bias.csv", index=False)
    pd.DataFrame({
        "judge": ["j1"] * 8, "dimension": DIMENSIONS,
        "max_minus_min_position_mean": [0.0] * 8,
    }).to_csv(directories["semantic"] / "candidate_position_slopes.csv", index=False)
    pd.DataFrame(np.eye(8), index=DIMENSIONS, columns=DIMENSIONS).to_csv(
        directories["semantic"] / "interdimension_spearman.csv"
    )

    pd.DataFrame({
        "excluded_judge": ["j1", "j2", "j3"],
        "profile_spearman_vs_full": [.9, .9, .9],
    }).to_csv(directories["leaveout"] / "leaveout_summary.csv", index=False)
    leaveout_rows = []
    prompt_rows = []
    for dimension in DIMENSIONS:
        delta = -.2 if dimension == "help_directness" else .2
        prompt_rows.append({"dimension": dimension, "mean_delta": delta})
        for judge in ("j1", "j2", "j3"):
            leaveout_rows.append({
                "dimension": dimension, "excluded_judge": judge,
                "leaveout_mean_delta": delta, "sign_reversal": False,
            })
    pd.DataFrame(prompt_rows).to_csv(
        directories["semantic"] / "prompt_effects.csv", index=False
    )
    pd.DataFrame(leaveout_rows).to_csv(
        directories["leaveout"] / "leaveout_prompt_effects.csv", index=False
    )
    pd.DataFrame({
        "outcome": ["diagnosis_correct"] * 8, "dimension": DIMENSIONS,
        "permutation_p": [.001] * 8, "bh_q_within_outcome": [.20] * 8,
    }).to_csv(directories["objective"] / "fixed_item_associations.csv", index=False)
    return directories


def run_decision(monkeypatch: pytest.MonkeyPatch, paths: dict[str, Path]) -> tuple[pd.DataFrame, dict]:
    monkeypatch.setattr(sys, "argv", [
        "evaluate_submission_decision.py",
        "--semantic-dir", str(paths["semantic"]),
        "--leaveout-dir", str(paths["leaveout"]),
        "--scale-dir", str(paths["scale"]),
        "--objective-dir", str(paths["objective"]),
        "--output-dir", str(paths["output"]),
    ])
    decision.main()
    rows = pd.read_csv(paths["output"] / "dimension_decisions.csv").set_index("dimension")
    summary = json.loads((paths["output"] / "submission_decision.json").read_text())
    return rows, summary


def test_two_anchored_dimensions_retain_disposition_thesis(
    decision_inputs: dict[str, Path], monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows, summary = run_decision(monkeypatch, decision_inputs)
    assert rows.loc[["help_directness", "elicitation"], "validated_pedagogical_disposition"].all()
    assert summary["recommended_thesis"] == "pedagogical_dispositions"


def test_unadjusted_p_does_not_pass_longtutor_criterion(
    decision_inputs: dict[str, Path], monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows, _ = run_decision(monkeypatch, decision_inputs)
    assert not bool(rows.loc["affective_warmth", "criterion_3_human_gold_diagnosis"])


def test_unreliable_dimension_cannot_be_upgraded_by_external_criterion(
    decision_inputs: dict[str, Path], monkeypatch: pytest.MonkeyPatch,
) -> None:
    icc_path = decision_inputs["semantic"] / "judge_icc.csv"
    icc = pd.read_csv(icc_path)
    icc.loc[icc["dimension"] == "affective_warmth", "icc_3_k"] = .4
    icc.to_csv(icc_path, index=False)
    objective_path = decision_inputs["objective"] / "fixed_item_associations.csv"
    objective = pd.read_csv(objective_path)
    objective.loc[objective["dimension"] == "affective_warmth", "bh_q_within_outcome"] = .01
    objective.to_csv(objective_path, index=False)
    rows, _ = run_decision(monkeypatch, decision_inputs)
    assert not bool(rows.loc["affective_warmth", "validated_pedagogical_disposition"])


def test_bias_flags_do_not_erase_an_otherwise_valid_result(
    decision_inputs: dict[str, Path], monkeypatch: pytest.MonkeyPatch,
) -> None:
    family_path = decision_inputs["semantic"] / "judge_family_bias.csv"
    family = pd.read_csv(family_path)
    family.loc[family["dimension"] == "help_directness", "own_minus_other_residual"] = .3
    family.to_csv(family_path, index=False)
    position_path = decision_inputs["semantic"] / "candidate_position_slopes.csv"
    position = pd.read_csv(position_path)
    position.loc[position["dimension"] == "help_directness", "max_minus_min_position_mean"] = .3
    position.to_csv(position_path, index=False)
    rows, _ = run_decision(monkeypatch, decision_inputs)
    assert bool(rows.loc["help_directness", "validated_pedagogical_disposition"])
    assert bool(rows.loc["help_directness", "self_family_bias_flag"])
    assert bool(rows.loc["help_directness", "slate_position_flag"])
