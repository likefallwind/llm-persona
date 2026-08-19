from __future__ import annotations

from pathlib import Path
import subprocess
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build_reproducibility_manifest import git_eligible_files


def test_manifest_file_selection_excludes_gitignored_state(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / ".gitignore").write_text("ignored.log\n__pycache__/\n", encoding="utf-8")
    (tmp_path / "tracked.txt").write_text("tracked\n", encoding="utf-8")
    (tmp_path / "untracked.txt").write_text("eligible\n", encoding="utf-8")
    (tmp_path / "ignored.log").write_text("private state\n", encoding="utf-8")
    cache = tmp_path / "__pycache__"
    cache.mkdir()
    (cache / "module.pyc").write_bytes(b"cache")
    subprocess.run(
        ["git", "-C", str(tmp_path), "add", ".gitignore", "tracked.txt"],
        check=True,
    )

    selected = {
        path.relative_to(tmp_path).as_posix()
        for path in git_eligible_files(tmp_path, ["."])
    }

    assert selected == {".gitignore", "tracked.txt", "untracked.txt"}
