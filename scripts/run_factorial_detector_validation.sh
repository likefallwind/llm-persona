#!/usr/bin/env bash
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$ROOT/.venv/bin/python"
OUT="$ROOT/artifacts/factorial_detector_validation_v1/run"
STATE="$OUT/run_state"
EDUBENCH="${EDUBENCH_ROOT:-$ROOT/../edubenchmark}"

if [[ -z "${MINIMAX_API_KEY:-}" || -z "${API_GATEWAY:-}" ]]; then
  : "${PERSONA_ENV_FILE:?Set API variables or provide PERSONA_ENV_FILE}"
  eval "$(grep -E '^export (MINIMAX_API_KEY|API_GATEWAY)=' "$PERSONA_ENV_FILE")"
fi
: "${MINIMAX_API_KEY:?MINIMAX_API_KEY is required}"
: "${API_GATEWAY:?API_GATEWAY is required}"

mkdir -p "$STATE"
date -Is > "$STATE/started"
rm -f "$STATE/finished" "$STATE/exit"

"$PY" "$ROOT/scripts/generate_factorial_detector_validation.py"
code=$?
if [[ "$code" -eq 0 ]]; then
  "$PY" "$ROOT/scripts/run_factorial_detector_validation.py" \
    --edubenchmark-root "$EDUBENCH" \
    --output-dir "$OUT"
  code=$?
fi
if [[ "$code" -eq 0 ]]; then
  "$PY" "$ROOT/scripts/factorial_detector_validation_status.py" \
    --annotations "$OUT/annotations.jsonl" \
    --require-complete
  code=$?
fi

printf '%s\n' "$code" > "$STATE/exit"
date -Is > "$STATE/finished"
exit "$code"
