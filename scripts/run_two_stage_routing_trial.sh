#!/usr/bin/env bash
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$ROOT/.venv/bin/python"
OUT="$ROOT/artifacts/two_stage_routing_trial_v1/run"
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

"$PY" "$ROOT/scripts/generate_two_stage_routing_trial.py" \
  --spec "$ROOT/data/two_stage_routing_trial_spec_v1.json" \
  --output-dir "$ROOT/artifacts/two_stage_routing_trial_v1"
code=$?
if [[ "$code" -eq 0 ]]; then
  "$PY" "$ROOT/scripts/run_two_stage_routing_trial.py" \
    --spec "$ROOT/data/two_stage_routing_trial_spec_v1.json" \
    --request-manifest "$OUT/request_manifest.jsonl" \
    --order-plan "$ROOT/artifacts/two_stage_routing_trial_v1/request_order_plan.jsonl" \
    --output-dir "$OUT" \
    --edubenchmark-root "$EDUBENCH" \
    --minimax-concurrency 4 \
    --gateway-concurrency 8 \
    --timeout 600 \
    --retries 3
  code=$?
fi
if [[ "$code" -eq 0 ]]; then
  "$PY" "$ROOT/scripts/factorial_prompt_status.py" \
    --spec "$ROOT/data/two_stage_routing_trial_spec_v1.json" \
    --manifest "$ROOT/artifacts/two_stage_routing_trial_v1/sample_manifest.jsonl" \
    --responses "$OUT/responses.jsonl" \
    --require-complete
  code=$?
fi

printf '%s\n' "$code" > "$STATE/exit"
date -Is > "$STATE/finished"
exit "$code"
