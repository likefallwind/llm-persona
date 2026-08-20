import importlib.util
from pathlib import Path
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "policy_homogenization", ROOT / "scripts/analyze_policy_homogenization.py",
)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def synthetic_predictions():
    rows = []
    for target_act in ("probing", "telling"):
        for pair_id in range(4):
            for model_index, model in enumerate(("m1", "m2")):
                generic_prediction = target_act if model_index == 0 else "generic"
                pedagogy_prediction = "probing"
                for arm, predicted in (
                    ("generic", generic_prediction),
                    ("pedagogy", pedagogy_prediction),
                ):
                    rows.append({
                        "classifier_variant": "v1",
                        "family": "standard",
                        "arm": arm,
                        "pair_id": f"{target_act}-{pair_id}",
                        "model": model,
                        "target_act": target_act,
                        "predicted_act": predicted,
                        "act_match": int(predicted == target_act),
                    })
    return pd.DataFrame(rows)


def test_action_audit_detects_target_specific_polarity_reversal():
    paired = module.validate_and_pair(synthetic_predictions())
    aggregate, models, signs = module.action_effect_tables(paired, reps=20, seed=4)
    aggregate = aggregate.set_index("target_act")
    assert aggregate.loc["probing", "mean_delta"] == 0.5
    assert aggregate.loc["telling", "mean_delta"] == -0.5
    signs = signs.set_index("target_act")
    assert signs.loc["telling", "negative_models"] == 1
    assert signs.loc["probing", "positive_models"] == 1
    assert len(models) == 4


def test_consensus_audit_detects_cross_model_homogenization():
    context, effects = module.consensus_tables(
        synthetic_predictions(), reps=20, seed=9,
    )
    entropy = effects.loc[effects.metric == "normalized_entropy"].iloc[0]
    disagreement = effects.loc[effects.metric == "modal_disagreement"].iloc[0]
    assert entropy.pedagogy_minus_generic < 0
    assert disagreement.pedagogy_minus_generic < 0
    assert len(context) == 16


def test_pair_validation_rejects_missing_arm():
    frame = synthetic_predictions().iloc[1:].copy()
    try:
        module.validate_and_pair(frame)
    except RuntimeError as exc:
        assert "not exactly paired" in str(exc)
    else:
        raise AssertionError("missing arm was accepted")
