#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EDUBENCH_ROOT="${EDUBENCH_ROOT:-$REPO_ROOT/../edubenchmark}"
export EDUBENCH_ROOT
PYTHON_BIN="${PYTHON_BIN:-$REPO_ROOT/.venv/bin/python}"
EVAL_ROOT="$EDUBENCH_ROOT/reports/eval"
MATHDIAL_DIR="$EDUBENCH_ROOT/sources/datasets/mathdial"
BRIDGE_DIR="$EDUBENCH_ROOT/sources/datasets/mathtutorbench/datasets"

require_path() {
  if [[ ! -e "$1" ]]; then
    echo "required input is missing: $1" >&2
    exit 2
  fi
}

require_path "$PYTHON_BIN"
require_path "$EVAL_ROOT"
require_path "$MATHDIAL_DIR/train.jsonl"
require_path "$MATHDIAL_DIR/test.jsonl"
require_path "$BRIDGE_DIR/mathdial_bridge.json"
require_path "$BRIDGE_DIR/mathdial_bridge_hard.json"

cd "$REPO_ROOT"

"$PYTHON_BIN" scripts/build_corpus_inventory.py \
  --eval-root "$EVAL_ROOT" \
  --output-dir artifacts/inventory

"$PYTHON_BIN" scripts/audit_generation_provenance.py \
  --inventory artifacts/inventory/corpus_inventory.json \
  --roles data/benchmark_roles.json \
  --edubenchmark-root "$EDUBENCH_ROOT" \
  --output-dir artifacts/provenance_audit

"$PYTHON_BIN" scripts/run_behavioral_pilot.py \
  --inventory artifacts/inventory/corpus_inventory.json \
  --roles data/benchmark_roles.json \
  --role-section primary_behavior_generation \
  --model-panel core \
  --output-dir artifacts/pilot

"$PYTHON_BIN" scripts/run_behavioral_pilot.py \
  --inventory artifacts/inventory/corpus_inventory.json \
  --roles data/benchmark_roles.json \
  --role-section negative_controls \
  --model-panel core \
  --output-dir artifacts/negative_controls

"$PYTHON_BIN" scripts/run_behavioral_pilot.py \
  --inventory artifacts/inventory/corpus_inventory.json \
  --roles data/benchmark_roles.json \
  --role-section primary_behavior_generation \
  --model-panel extended \
  --output-dir artifacts/extended_panel

"$PYTHON_BIN" scripts/analyze_discriminant_validity.py \
  --teaching artifacts/pilot/behavior_features.csv \
  --negative artifacts/negative_controls/behavior_features.csv \
  --output-dir artifacts/discriminant_validity

"$PYTHON_BIN" scripts/analyze_extended_panel.py \
  --features artifacts/extended_panel/behavior_features.csv \
  --output-dir artifacts/extended_analysis

"$PYTHON_BIN" scripts/analyze_existing_judge_robustness.py \
  --eval-root "$EVAL_ROOT" \
  --features artifacts/pilot/behavior_features.csv \
  --output-dir artifacts/judge_robustness

"$PYTHON_BIN" scripts/semantic_power_audit.py \
  --output-dir artifacts/power_audit

"$PYTHON_BIN" scripts/analyze_dialogue_act_validity.py \
  --inventory artifacts/inventory/corpus_inventory.json \
  --mathdial-dir "$MATHDIAL_DIR" \
  --bridge-dir "$BRIDGE_DIR" \
  --output-dir artifacts/dialogue_act_validity

"$PYTHON_BIN" scripts/analyze_judge_human_calibration.py \
  --eval-root "$EVAL_ROOT" \
  --output-dir artifacts/judge_human_calibration

"$PYTHON_BIN" scripts/analyze_longtutor_objective_validity.py \
  --inventory artifacts/inventory/corpus_inventory.json \
  --output-dir artifacts/longtutor_objective_validity

"$PYTHON_BIN" scripts/verify_release_claims.py \
  --root "$REPO_ROOT" \
  --output-dir artifacts/claim_verification

"$PYTHON_BIN" scripts/audit_release_privacy.py \
  --root "$REPO_ROOT"

"$PYTHON_BIN" scripts/make_paper_figures.py \
  --root "$REPO_ROOT"

"$PYTHON_BIN" -m py_compile scripts/*.py
"$PYTHON_BIN" -m pytest -q tests
bash -n scripts/*.sh

echo "completed non-semantic analyses reproduced successfully"
