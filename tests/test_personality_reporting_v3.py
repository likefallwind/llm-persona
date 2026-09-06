import fcntl
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import finish_personality_reporting_v3 as reporting


def isolate(monkeypatch, tmp_path):
    monkeypatch.setattr(reporting, 'BASE', tmp_path)
    monkeypatch.setattr(reporting, 'OUT', tmp_path / 'confirmation_reporting')
    dependency = tmp_path / 'confirmation/run'
    dependency.mkdir(parents=True)
    calls = []
    monkeypatch.setattr(reporting.subprocess, 'run', lambda *a, **kw: calls.append(a))
    return dependency, calls


def test_no_reports_while_confirmation_lock_is_held(monkeypatch, tmp_path):
    dependency, calls = isolate(monkeypatch, tmp_path)
    with (dependency / 'confirmation_pipeline.lock').open('a+') as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

        def stop_wait(seconds):
            assert seconds == 30
            assert calls == []
            state = json.loads((reporting.OUT / 'run/pipeline_state.json').read_text())
            assert state['stage'] == 'waiting_for_existing_confirmation_pipeline'
            raise RuntimeError('synthetic stop after observing the wait')

        monkeypatch.setattr(reporting.time, 'sleep', stop_wait)
        with pytest.raises(RuntimeError, match='synthetic stop'):
            reporting.main()
    assert calls == []
    assert not (reporting.OUT / 'summary.json').exists()


@pytest.mark.parametrize('completion', [
    {'status': 'failed', 'stage': 'stopped_for_review'},
    {'status': 'complete', 'stage': 'all_forecasts_verified_before_confirmation'},
])
def test_released_lock_requires_final_success(monkeypatch, tmp_path, completion):
    dependency, calls = isolate(monkeypatch, tmp_path)
    (dependency / 'confirmation_pipeline.lock').touch()
    (dependency / 'pipeline_state.json').write_text(json.dumps(completion))
    with pytest.raises(ValueError, match='before successful completion'):
        reporting.main()
    assert calls == []
    assert not (reporting.OUT / 'summary.json').exists()
    state = json.loads((reporting.OUT / 'run/pipeline_state.json').read_text())
    assert state['status'] == 'failed'
