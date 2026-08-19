#!/usr/bin/env bash
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$ROOT/.venv/bin/python"
RUNNER="$ROOT/scripts/run_semantic_judge.py"
INVENTORY="$ROOT/artifacts/inventory/corpus_inventory.json"
EDUBENCH="${EDUBENCH_ROOT:-$ROOT/../edubenchmark}"
OUT="$ROOT/artifacts/semantic_judge/full_v1"
STATE="$OUT/run_state"

# A long-lived tmux server may predate the current login environment. Mirror the
# upstream EduBenchmark launchers by loading only the two required exports; never
# print their values into the durable log.
if [[ -z "${MINIMAX_API_KEY:-}" || -z "${API_GATEWAY:-}" ]]; then
  : "${PERSONA_ENV_FILE:?Set API variables in the environment or set PERSONA_ENV_FILE}"
  # The file is user-selected.  Only the two required exports are evaluated,
  # and their values are never printed into the durable log.
  eval "$(grep -E '^export (MINIMAX_API_KEY|API_GATEWAY)=' "$PERSONA_ENV_FILE")"
fi
: "${MINIMAX_API_KEY:?MINIMAX_API_KEY is required}"
: "${API_GATEWAY:?API_GATEWAY is required}"

mkdir -p "$STATE"
date -Is > "$STATE/started"
rm -f \
  "$STATE/finished" "$STATE/exit" \
  "$STATE/main.finished" "$STATE/main.exit" \
  "$STATE/longtutor.finished" "$STATE/longtutor.exit"

run_phase() {
  local name="$1"
  local filter="$2"
  date -Is > "$STATE/${name}.started"
  "$PY" "$RUNNER" \
    --inventory "$INVENTORY" \
    --edubenchmark-root "$EDUBENCH" \
    --output-dir "$OUT" \
    --judges MiniMax-M3,glm-5.2,deepseek-v4-pro \
    --longtutor 40 \
    --mathdial 80 \
    --mathdial-hard 40 \
    --socratic 80 \
    --minimax-concurrency 4 \
    --gateway-concurrency 8 \
    --timeout 600 \
    --retries 3 \
    --run-benchmarks "$filter"
  local code=$?
  printf '%s\n' "$code" > "$STATE/${name}.exit"
  date -Is > "$STATE/${name}.finished"
  return "$code"
}

main_filter="mathtutorbench_scaffolding,mathtutorbench_pedagogy,mathtutorbench_scaffolding_hard,mathtutorbench_pedagogy_hard,mathtutorbench_socratic"
run_phase main "$main_filter"
code=$?
if [[ "$code" -eq 0 ]]; then
  run_phase longtutor "longtutor_teaching"
  code=$?
fi

printf '%s\n' "$code" > "$STATE/exit"
date -Is > "$STATE/finished"
exit "$code"
