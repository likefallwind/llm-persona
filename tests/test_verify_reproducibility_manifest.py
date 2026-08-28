import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
module_spec = importlib.util.spec_from_file_location(
    "manifest_verifier", ROOT / "scripts/verify_reproducibility_manifest.py"
)
manifest_verifier = importlib.util.module_from_spec(module_spec)
assert module_spec.loader is not None
module_spec.loader.exec_module(manifest_verifier)


def test_manifest_verifier_accepts_matching_file(tmp_path):
    payload = tmp_path / "result.txt"
    payload.write_text("frozen\n", encoding="utf-8")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps({
            "files": [{
                "path": "result.txt",
                "bytes": payload.stat().st_size,
                "sha256": manifest_verifier.sha256(payload),
            }]
        }),
        encoding="utf-8",
    )
    assert manifest_verifier.verify(tmp_path.resolve(), manifest) == []


def test_manifest_verifier_rejects_hash_drift(tmp_path):
    payload = tmp_path / "result.txt"
    payload.write_text("changed\n", encoding="utf-8")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps({
            "files": [{
                "path": "result.txt",
                "bytes": payload.stat().st_size,
                "sha256": "0" * 64,
            }]
        }),
        encoding="utf-8",
    )
    assert manifest_verifier.verify(tmp_path.resolve(), manifest) == [
        "sha256 mismatch: result.txt"
    ]
