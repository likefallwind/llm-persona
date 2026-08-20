# Frozen factorial detector-validation protocol

Frozen: 2026-08-19, after the parent and request-order outcomes were analyzed,
but before any raw factorial response text or validation-judge label was
inspected. This is a post-result measurement audit, not a preregistration. It is
strictly downgrade-only: validation cannot rescue, strengthen, or create a
factorial claim.

Frozen implementation and public-plan hashes:

| Artifact | SHA-256 |
|---|---|
| `data/factorial_detector_validation_spec_v1.json` | `28b48a9179ddb4a1f3900055c08fb035c21d49f668b00db3b23bd867cbe83efb` |
| `scripts/generate_factorial_detector_validation.py` | `ccc12c2322f5a78d9c8ee307f6ce1be970305343d166a6f4704f0bdb4f0f7045` |
| `scripts/run_factorial_detector_validation.py` | `2c7274295fd25e5752708c30c4b307c9abce39fe6de71fffcac46eaf886f360f` |
| `scripts/factorial_detector_validation_status.py` | `5975209d58c217222a39b65b6b214c234e3c7fa8e7179c8c04802883b81da839` |
| `scripts/analyze_factorial_detector_validation.py` | `411aad4feb698c8c2693d27be13cddc364aeb01f9cf9b769c5513f3b57dc6947` |
| `artifacts/factorial_detector_validation_v1/sample_manifest.jsonl` | `916977000eb765c22f2b0582a9a78f3c9c28ff68af9ca3253cf9a47a48141a0d` |
| `artifacts/factorial_detector_validation_v1/batch_plan.jsonl` | `ddb84da90aaf7962c36d87150490bab7585a2aa8c6115ffbb5de6145bf32636e` |
| `artifacts/factorial_detector_validation_v1/payload_audit.json` | `61868f482e012916a437b6d14ab1fc5c199b68bd0536f315452ab258932bb250` |

## Motivation and claim boundary

The prospective factorial uses transparent deterministic outcomes. That avoids
LLM-judge dependence in the primary analysis, but a reviewer can still ask
whether the operational detectors represent the named behaviors on actual model
outputs. We therefore independently validate:

1. `question_first`: the first sentence-like segment, ending at the first `.`,
   `!`, `?`, or newline (or 250 characters if none occurs), contains `?`;
2. `answer_reveal_correct`: an explicit `Final answer:` or `Final answer=` field
   contains an accepted exact representation of the known solution within the
   following 100 characters; and
3. `warmth_marker`: the frozen encouragement lexicon is compared with a broader
   blind judgment of explicit learner-directed encouragement or support.

The first two labels audit implementation fidelity to exact operational rules.
The third audits whether the narrow lexicon transports to the intended surface
construct. None measures tutoring quality, empathy, learner understanding, or
learning gain.

## Outcome-independent sample

The public sample is generated without using detector values, factor effects, or
response text. Within every panel × base problem × candidate-model group,
responses are ordered by SHA-256 of the frozen seed, panel, sample ID, and model.
The lowest two of 16 parent cells and lowest four of 16 replication cells are
selected. This yields:

- 320 parent response units: 32 bases × five models × two cells;
- 160 replication response units: eight bases × five models × four cells; and
- 480 total units in 48 batches of ten sharing a base problem.

The replication units are distinct generations even when their prompts are
byte-identical to parent prompts. Candidate order is independently hash-shuffled
for every judge and batch. Judges do not receive model identity, factor levels,
learner-request condition, panel name, queue rank, current detector value, or
factorial effect estimate.

## Judges, payload, and completion

MiniMax-M3 uses the official MiniMax route; GLM-5.2 and DeepSeek-V4-Pro use the
configured gateway. Temperature is zero, retries are three, and concurrency is
capped at four for MiniMax and eight for gateway routes. Each judge labels all
48 batches. A valid JSON object must contain all ten blind candidates, all three
labels (`yes`, `no`, or `uncertain`), and confidence 1--5.

The external payload contains only a synthetic English math problem, its known
accepted answer representations, and synthetic model responses. It contains no
EduBenchmark prompt or response, LongTutor history, real learner data,
identifier, or private source text. Raw validation calls remain ignored. The
release contains sample/batch plans, hashes, parsed labels, usage/error metadata,
and aggregate agreement tables without response text.

Completion is all-or-nothing: 480 response units, 48 batches, and 144 successful
judge annotations, with no replacement judge, response, model, or batch.

## Frozen analysis and gates

For each metric, a majority label exists when at least two judges give the same
binary label; `uncertain` does not vote. The report retains judge disagreement,
uncertain rates, candidate-family overlap checks, panel/model breakdowns, and
every sampled unit hash.

A detector validates only if all hold:

1. majority-label coverage is at least 0.95;
2. balanced accuracy is at least 0.90;
3. a response-unit bootstrap with 2,000 replicates has balanced-accuracy 95%
   lower bound at least 0.80; and
4. Cohen's kappa is at least 0.70.

Bootstrap resampling uses response units and retains the three linked judge
labels. Accuracy, sensitivity, specificity, positive predictive value, negative
predictive value, kappa, and the full 2×2 table are reported even on failure.
Subgroup estimates are descriptive and cannot repair a failed aggregate gate.

If `question_first` or `answer_reveal_correct` fails, the corresponding policy
claim is restricted to literal formatting compliance. If `warmth_marker` fails,
the paper must say only that the frozen lexicon is controllable and remove a
semantic warm-tone interpretation. Passing preserves the existing bounded
black-box component-addressability wording but does not upgrade it.

## Interpretation of related work

LongTutor evaluates long-history evidence, diagnosis, and adaptive action, while
knowledge tracing predicts future performance. The released LongTutor XES3G5M
slice cannot provide a future-outcome validation here: all 1,000 gold points are
at index 199 of 200, and the upstream preprocessing selects the last incorrect
response before truncation. Any unreleased suffix would therefore contain only
correct responses by construction. This audit must not be presented as a
learning-outcome study.
