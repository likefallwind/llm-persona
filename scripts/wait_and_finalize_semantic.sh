#!/usr/bin/env bash
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PANEL="$ROOT/artifacts/semantic_judge/full_v1"

while [[ ! -f "$PANEL/run_state/finished" ]]; do
  sleep 30
done

date -Is > "$PANEL/run_state/finalize.started"
bash "$ROOT/scripts/finalize_semantic_analysis.sh" > "$PANEL/finalize.log" 2>&1
code=$?
printf '%s\n' "$code" > "$PANEL/run_state/finalize.exit"
date -Is > "$PANEL/run_state/finalize.finished"
exit "$code"
