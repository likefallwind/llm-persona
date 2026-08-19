# Frozen requirements for the future local-server extension

This document records the work to run only after the user provides a stronger
server.  No local model job should be started on the present machine.

## Priority A: architecture-distinct local semantic judge

Purpose: test whether the three external frontier judges share alignment-shaped
measurement variance.

- Serve a version-pinned open-weight Qwen-class instruct model large enough to
  follow the full eight-dimension JSON rubric reliably.  The 4B/8B/12B local smoke
  runs are not acceptable primary judges because confidence was 1 and latency was
  excessive.
- Run the existing frozen 360-batch manifest without changing items, anchors, or
  candidate order seed.
- Calibrate the local judge first on the existing 482 human preference pairs in
  both A/B orders.  Required report: expert agreement, order consistency,
  pairwise agreement with each external judge, and error overlap.
- Treat the local judge as a sensitivity route.  Do not silently add it to the
  three-judge median; report external-three and external-plus-local conclusions
  side by side.
- Keep all contexts and responses on the server.  Transfer only hashes, ratings,
  version metadata, and aggregate usage back to this repository.

## Priority B: slate-effect audit

The main semantic protocol shows six candidate replies together.  On a
deterministic 10% context subsample, score each reply in isolation with the same
local judge and rubric.

- Cross design: identical response × batch presentation versus isolated
  presentation.
- Estimate per-dimension weighted agreement, mean shift, variance compression,
  and model-rank stability.
- Randomize isolated-response order and clear conversation state between calls.
- A material batch-versus-isolated reversal limits the main study to comparative
  within-context claims.

## Priority C: prospectively expanded model panel

Population-level psychometrics require more model systems, not more responses
from the same six systems.

- Target at least 14--20 version-pinned systems if making model-level correlation
  claims; the current power audit shows roughly 14 are needed even for |r|=0.7 at
  80% power.
- Sample open models across at least three independent lineages and multiple
  sizes, with identical decoding, system prompt, and serving stack wherever
  possible.
- Generate only on the already frozen educational context sample first; do not
  rerun the entire benchmark until the small panel passes format and quality
  checks.
- Separate lineage, parameter count, post-training recipe, quantization, and
  serving version in the manifest.  Never call a size comparison causal when
  these differ.

## Reproducibility metadata

Every server run must record:

- exact model repository and revision hash;
- tokenizer revision, quantization, dtype, and inference engine version;
- GPU type/count, tensor parallelism, seed, temperature, top-p, and context limit;
- prompt SHA-256, manifest SHA-256, start/end timestamps, retry/error ledger;
- response hashes and rating JSON, but no duplicated raw LongTutor histories.

## Go/no-go gates

1. JSON validity at least 99% before retries on a 20-batch smoke test.
2. Median confidence at least 3/5.
3. Human-preference agreement and position consistency reported before semantic
   results are inspected.
4. No concurrent writer to the same append-only file.
5. Full analysis is rerun from hashes after the local route completes.
