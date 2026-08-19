from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess


ROOT = Path(__file__).resolve().parents[1]


def test_wrapper_runs_main_longtutor_and_strict_status(tmp_path: Path) -> None:
    """Exercise the production Bash wrapper without making external requests."""
    sandbox = tmp_path / "repo"
    scripts = sandbox / "scripts"
    python_bin = sandbox / ".venv" / "bin" / "python"
    scripts.mkdir(parents=True)
    python_bin.parent.mkdir(parents=True)

    shutil.copy2(ROOT / "scripts" / "run_external_semantic_panel.sh", scripts)
    (scripts / "run_semantic_judge.py").touch()
    (scripts / "semantic_judge_status.py").touch()
    python_bin.write_text(
        "#!/usr/bin/env bash\n"
        "printf '%s\\n' \"$*\" >> \"$PERSONA_TEST_CALLS\"\n",
        encoding="utf-8",
    )
    python_bin.chmod(0o755)

    calls = tmp_path / "calls.log"
    env = os.environ.copy()
    env.update(
        {
            "MINIMAX_API_KEY": "test-only",
            "API_GATEWAY": "https://invalid.test",
            "PERSONA_TEST_CALLS": str(calls),
        }
    )
    completed = subprocess.run(
        ["bash", str(scripts / "run_external_semantic_panel.sh")],
        cwd=sandbox,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    invocations = calls.read_text(encoding="utf-8").splitlines()
    assert len(invocations) == 3
    assert "--run-benchmarks mathtutorbench_scaffolding," in invocations[0]
    assert "--run-benchmarks longtutor_teaching" in invocations[1]
    assert invocations[2].endswith("--require-complete")

    state = sandbox / "artifacts" / "semantic_judge" / "full_v1" / "run_state"
    assert (state / "main.exit").read_text(encoding="utf-8").strip() == "0"
    assert (state / "longtutor.exit").read_text(encoding="utf-8").strip() == "0"
    assert (state / "exit").read_text(encoding="utf-8").strip() == "0"
    assert (state / "finished").is_file()
