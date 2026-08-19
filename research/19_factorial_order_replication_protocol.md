# Outcome-blind request-order replication protocol

Frozen on 2026-08-19 while the parent factorial panel had 714/2,560 successful
responses and zero current errors. MiniMax-M3 was complete, MiniMax-M2.7 had
199/512 responses, and the three gateway models had one formal smoke response
each. No parent response text, derived outcome, effect estimate, or gate result
had been inspected.

## Why this replication exists

The parent manifest is lexicographically ordered by `sample_id`. Each local
base-problem block contains all 16 learner-need × policy cells, but their mean
within-block queue positions are not identical: direct versus explore differs by
8 positions, question policy by 4, answer policy by 2, and tone policy by 1.
This makes a condition-correlated short-timescale service, load, or cache effect
an identifiable design threat even though the full panel is balanced.

The replication changes only request order. It uses byte-identical parent
messages and prompt hashes on a fixed subset, independently randomizes a locally
factorial-balanced queue for each model, and reruns every factor cell. The
replication must run after the parent panel completes and regardless of the
parent outcomes, provided the frozen endpoints remain available.

Instruction conflict is interpreted using the system-over-user priority studied
by [IHEval](https://aclanthology.org/2025.naacl-long.425/), not as model
personality, empathy, learner understanding, or pedagogical benefit. IHEval
contains 3,538 examples across nine tasks and reports substantial degradation
under conflicting instruction priorities; our narrower replication asks whether
the educational policy contrasts survive request-sequence randomization.

## Frozen executable objects

| Component | SHA-256 |
|---|---|
| `data/factorial_order_replication_spec_v1.json` | `8b4fba2e751b41f59aac29c46730231da8041f5f816f86dc62116a8597bf8755` |
| `artifacts/factorial_order_replication_v1/sample_manifest.jsonl` | `e66a02ed36824229cc9b5afe0116e4a0dbc437bdf6f22fe5bc06797f66293c48` |
| `artifacts/factorial_order_replication_v1/request_order_plan.jsonl` | `0e863f87dfd2d55ed0e54cc61b8accd08e7cd017bede260279c8e34f175176bc` |
| `scripts/generate_factorial_order_replication.py` | `1841ae12c6d2466362369558882bc5f7cbe41c273e381f56de6e2ce7c9fb711a` |
| `scripts/run_factorial_order_replication.py` | `e79250ee96edf52a4ab707d301bbccab515d5c00d75b077f1aedd72dafbbabe6` |
| `scripts/analyze_factorial_order_replication.py` | `0bbc1020e808f54c22494dec06c55be036121dc83a8cc837ff7803392377bf5f` |
| `scripts/run_factorial_order_replication.sh` | `58d61e4fd3b7f284d46ba5b40efb99a69a2135c53310b4cb24282740ec789430` |

## Fixed sample and external payload

The subset contains indices `00` and `04` from each of the four parent problem
families:

- `arithmetic_mean-00`, `arithmetic_mean-04`;
- `fraction_addition-00`, `fraction_addition-04`;
- `linear_equation-00`, `linear_equation-04`; and
- `percentage_discount-00`, `percentage_discount-04`.

These eight base problems produce 8 × 2 learner needs × 8 policy cells = 128
prompts per model and **640 calls** across the same five models. Every message and
`prompt_sha256` is copied from the parent manifest. The external payload remains
only synthetic English problems, synthetic wrong work and learner requests, and
the frozen policy clauses. No benchmark prompt/response, LongTutor history, real
student record, identifier, or private source text is transmitted.

MiniMax-M3 and MiniMax-M2.7 use the official MiniMax route at concurrency 4.
GLM-5.2, DeepSeek-V4-Pro, and Doubao-Seed-2.0-Lite use the frozen gateway at
concurrency 8, one model phase at a time. Temperature remains zero, output is
uncapped, and failed or empty calls receive at most three attempts. No endpoint,
model, context, or factor cell may be replaced after outcome inspection.

## Request-order intervention

Within each model and each of the 16 learner-need × policy cells, the eight base
problems are first independently ranked by a SHA-256 key containing seed
`20260821`, model, cell, and sample ID. One item from every cell is then placed in
each of eight consecutive blocks. The 16 samples inside every block are ranked by
a second model- and block-specific SHA-256 key. Thus every 16-call block contains
all 16 cells exactly once, while base assignment and within-block order differ by
model. The complete 640-row plan is frozen in
`request_order_plan.jsonl` before any replication call.

The raw run records the planned queue rank for every request; analysis requires
exactly ranks 0--127 once per model and verifies each observed rank against the
public plan. Both the direct runner and shell wrapper refuse live calls unless
the parent status is exactly 2,560/2,560 with no missing, error, or unexpected
key. Model phases remain sequential to respect endpoint caps and prevent the
replication from competing with its parent collection.

## Analysis and downgrade-only gates

The replication uses the parent deterministic metrics, base-problem bootstrap,
all target and cross-effects, learner-need effects, family breakdowns, 16 cell
means per group, and all two- and three-way interactions. It also compares each
target effect with the same eight-context subset in the parent run.

A factor is called **order-robust** only if all conditions hold:

1. the complete parent panel passes its original controllability and selectivity
   gates;
2. the randomized replication independently passes the same target threshold,
   positive-in-every-model rule, and selectivity ratio of at least 2; and
3. the target effect is positive in both the parent subset and replication for
   the aggregate panel and every model.

Learner-need responsiveness is order-robust only when its registered threshold
passes in both complete panels. Absolute parent-subset versus replication
differences are reported without a post-hoc equivalence margin. All failed gates,
cell means, cross-effects, and interactions remain visible.

The replication is strictly downgrade-only. It cannot rescue a failed parent
gate, replace the 32-context primary estimate, or establish learning benefit.
If an endpoint is unavailable, the replication is incomplete and no
order-robust claim is made.
