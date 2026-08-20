import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
module_spec = importlib.util.spec_from_file_location(
    "learner_power", ROOT / "scripts/power_learner_outcome_trial.py"
)
learner_power = importlib.util.module_from_spec(module_spec)
assert module_spec.loader is not None
module_spec.loader.exec_module(learner_power)


def test_conservative_power_target_is_frozen_and_balanced():
    spec = json.loads((ROOT / "data/learner_outcome_trial_spec_v1.json").read_text())
    report = learner_power.build_report(spec)
    assert report["required_completed_per_policy_arm"] == 698
    assert report["required_recruited_per_policy_arm"] == 822
    assert report["planned_recruited_per_policy_arm"] == 825
    assert report["planned_total"] == 3300
    assert report["planned_cells"] == 12
    assert report["planned_per_cell"] == 275
    assert report["passed"]


def test_invalid_power_inputs_fail_closed():
    for values in ((0, .05, .8), (.15, 0, .8), (.15, .05, 1)):
        try:
            learner_power.required_completed_per_arm(*values)
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid power inputs accepted: {values}")


def test_trial_is_explicitly_not_started_and_uses_no_human_annotation():
    spec = json.loads((ROOT / "data/learner_outcome_trial_spec_v1.json").read_text())
    assert spec["status"] == "planning_only_not_preregistered_not_started"
    assert spec["measurement"]["human_annotation"] is False
    assert spec["measurement"]["tutor_access_during_outcomes"] is False
    assert spec["measurement"]["warmth_marker_used_as_construct_or_treatment"] is False
