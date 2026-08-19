# Prospective factorial policy-intervention protocol

Frozen before any response from this experiment is requested or inspected.

Executable freeze hashes:

| Component | SHA-256 |
|---|---|
| `data/factorial_prompt_spec_v1.json` | `bbe4ae5debcba9057f026a9e3fef18aab3bfc6522915a5464148d48f20d3abf5` |
| `artifacts/factorial_prompt_v1/sample_manifest.jsonl` | `c247dc3af4e1f1a85f18f5fd9a0b3a4e3441a925496197f4b4e02bd389784cc6` |
| `scripts/generate_factorial_prompt_panel.py` | `dddb2550fa92da0eb5f7d350ad0ecc23d9606205f5bd10fdb45b9545d763f5f2` |
| `scripts/run_factorial_prompt_panel.py` | `d46af3c4ea7704ad1bb855da54eeb7aec799c0473bdc0fd1fde25910cde18195` |
| `scripts/analyze_factorial_prompt_panel.py` | `fc546bb6be9fe8d920c554d9444ae04394c2262ef10a13826df8d9b2459ec0cb` |
| `scripts/factorial_prompt_status.py` | `e970b37843d023b50f989a8dd4eb58e7fd3dde4c26196033d98c717a30efd469` |

## Motivation

The archived MathTutorBench intervention is paired and causally interpretable as
a **bundled prompt**, but it jointly changes questioning, answer withholding,
tone, length, and specificity. A reviewer can therefore argue that the observed
convergence and telling harm are generic compliance with a more detailed prompt.
The new experiment separates three policy instructions in a complete factorial
design and uses procedurally generated post-hoc contexts rather than benchmark
items.

This experiment does not add a learner-outcome claim. It tests whether policy
components are independently controllable, whether models differ in those
control responses, and whether explicit learner requests still matter when they
conflict with system-level policy instructions.

## External payload and routes

Only synthetic English problem statements, synthetic incorrect student work,
the synthetic learner request, and the three frozen policy clauses are sent.
No EduBenchmark prompt, model response, LongTutor history, person identifier, or
private source text is included.

- MiniMax-M3 and MiniMax-M2.7: official MiniMax endpoint, at most four concurrent
  requests.
- GLM-5.2, DeepSeek-V4-Pro, and Doubao-Seed-2.0-Lite: configured API gateway, at
  most eight concurrent requests per sequential model phase.
- Qwen is excluded from v1 because its new route requires the later server. Its
  absence is reported and it cannot be silently substituted after results.

## Design

Seed `20260820` deterministically generates eight problems in each of four
families: fraction addition, one-variable linear equations, percentage discounts,
and arithmetic means. Every problem has exact machine-computable truth and a
plausible synthetic wrong solution. The exact numbers are newly sampled; no
benchmark corpus is read.

Each of the 32 base problems appears with two contradictory learner-need texts:

- `explore`: the learner asks to find the mistake without being given the final
  answer;
- `direct`: the learner asks for a direct explanation and final answer now.

Every resulting context is crossed with all eight cells of three binary
system-level factors:

1. `question_first` versus `explain_only`;
2. `withhold` versus `reveal` the final numeric answer; and
3. `warm` versus `neutral` tone.

The three clauses are independently hash-shuffled within each request to prevent
a factor from occupying one fixed serial position. All models receive identical
messages. The complete panel is 32 problems × 2 learner needs × 8 cells × 5
models = **2,560 calls**. Temperature is explicitly zero and output is uncapped,
following the provider-client policy for reasoning models.

## Deterministic outcomes

No LLM judge is used for the primary factorial test.

- `question_first`: the first sentence-like segment contains a question mark.
- `question_any`: the response contains a question mark.
- `answer_reveal_correct`: a `Final answer:` field contains an accepted exact
  representation generated from the known solution.
- `answer_reveal_any`: any `Final answer:` field occurs.
- `warmth_marker`: a frozen English encouragement lexicon is present.
- word/character/sentence counts are secondary surface outcomes.

The reveal instruction requires a `Final answer: <value>` ending and the
withhold instruction prohibits that label, making correct reveal observable
without semantic judging. Response text remains ignored locally; the release
contains hashes and derived binary/count features.

## Confirmatory contrasts and gates

Main effects average the high minus low factor level over all matched cells. The
primary target mapping is question policy → `question_first`, answer policy →
`answer_reveal_correct`, and tone policy → `warmth_marker`. Effects are reported
overall and for every model. Context-bootstrap intervals resample the 32 base
problems and retain both learner requests, all factor cells, and all models.

A component is called controllable only when its overall targeted difference
meets the threshold in `data/factorial_prompt_spec_v1.json` and the sign is
positive in every model. It is called selective only if the absolute targeted
effect is at least twice the largest absolute cross-effect on the other two
primary outcomes.

Learner-need responsiveness is assessed after averaging over all system cells:
direct minus explore must increase correct answer reveal by at least 0.10, and
explore minus direct must increase question-first behavior by at least 0.10.
Failure is substantively important: it means the system policy overrides an
explicit local learner request under this hierarchy.

## Failure and interpretation rules

- Completion is all-or-nothing: 2,560 successful nonempty responses. A failed
  endpoint is retried but not replaced by another model or route.
- All target effects, cross-effects, model effects, learner-need effects, and
  family breakdowns are reported.
- A large target effect with large cross-effects is bundled controllability, not
  an independently addressable dimension.
- Correct answer formatting is instruction adherence, not tutoring quality.
- Learner-request responsiveness is not evidence that the chosen action improves
  learning.
- Procedural novelty reduces exact benchmark memorization but does not prove the
  underlying mathematical templates were absent from training.
- The method commit and executable spec must be pushed before live calls begin.
