import json
from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import complete_personality_confirmation_v3 as continuation


def test_terminal_training_failure_cannot_start_confirmation(tmp_path,monkeypatch):
    folder=tmp_path/'training/run'
    folder.mkdir(parents=True)
    (folder/'training_pipeline.lock').touch()
    (folder/'pipeline_state.json').write_text(json.dumps({'status':'failed','stage':'stopped_for_review','error':'incomplete codes'}))
    monkeypatch.setattr(continuation,'BASE',tmp_path)
    called=[]
    monkeypatch.setattr(continuation,'validate_stage',lambda stage:called.append(stage))
    with pytest.raises(ValueError,match='before successful completion'):
        continuation.wait_training()
    assert called==[]


def test_terminal_training_success_still_requires_prediction_validation(tmp_path,monkeypatch):
    folder=tmp_path/'training/run'
    folder.mkdir(parents=True)
    (folder/'training_pipeline.lock').touch()
    (folder/'pipeline_state.json').write_text(json.dumps({'status':'complete','stage':'training_measurement_and_prediction_lock_complete'}))
    monkeypatch.setattr(continuation,'BASE',tmp_path)
    def reject(stage):
        assert stage=='confirmation'
        raise ValueError('invalid prediction lock')
    monkeypatch.setattr(continuation,'validate_stage',reject)
    with pytest.raises(ValueError,match='invalid prediction lock'):
        continuation.wait_training()
