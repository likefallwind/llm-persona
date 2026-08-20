# Prospective two-stage action-selection trial results

Date completed: 2026-08-20. Status: **complete prospective trial; registered
joint claim failed**.

## Provenance and completion

The 96 contexts, five-model panel, five calls per context, target-invariant
prompts, two order-counterbalanced selector wordings, counterfactual executors,
same-snapshot single-pass baseline, strict parser, model-specific ten-stratum
order, metrics, and thresholds were published in draft PR #12 before collection.
No response was inspected until the full panel completed.

The run started at `2026-08-20T11:36:03+08:00`, finished at
`2026-08-20T13:00:46+08:00`, and exited with code 0. All 2,400 planned cells
(96 contexts x five calls x five models) completed with zero failed, empty,
missing, or unexpected cells. Every model has exactly 480 responses, and all 48
model-specific blocks retain all ten target-by-call strata.

## Registered decision: explicit decomposition made selection worse

Both selector wordings failed every selector-specific gate. The executor and
wording-gap gates passed, so failure cannot be attributed to inability to realize
an explicitly chosen binary action or to one favorable wording.

| Registered endpoint | ASK-first selector | EXPLAIN-first selector | Gate |
|---|---:|---:|---|
| Valid output rate | 0.975 [0.960, 0.988] | 0.910 [0.890, 0.929] | Both >=0.98: fail |
| Human binary-action accuracy | 0.519 [0.456, 0.583] | 0.500 [0.433, 0.563] | Both >=0.60, lower bound >0.50: fail |
| Minimum model accuracy | 0.458 | 0.302 | Every model >0.50: fail |
| Composed - single-pass match | -0.058 [-0.110, -0.004] | -0.077 [-0.131, -0.023] | Both >=+0.08, lower bound >0: fail |
| Models with positive composed contrast | 1/5 | 1/5 | Every model positive: fail |

The absolute selector-accuracy difference was 0.019, below the registered 0.10
maximum. ASK execution produced a question in 0.998 of responses (minimum model
rate 0.990); EXPLAIN execution avoided questions in 1.000 (minimum 1.000). The
execution-realization gate therefore passed.

Per-model composed-minus-single-pass effects range from -0.156 to +0.052 for
ASK-first and -0.240 to +0.042 for EXPLAIN-first. Only MiniMax-M3 is positive
under both wordings, and both of its intervals cross zero. DeepSeek-V4-Pro is
significantly worse under both wordings; MiniMax-M2.7 is significantly worse
under EXPLAIN-first. This is a rejection of the tested two-stage remedy, not an
ambiguous near-pass.

The three frozen four-way human-action classifiers yield small positive
composed-minus-single-pass point estimates (+0.008 to +0.035), but all six
context-cluster intervals cross zero. That measurement-sensitive secondary
result cannot rescue the failed classifier-free binary gate.

## Post-hoc text-free mechanism audit

After the registered result was known, a deterministic audit used only parsed
actions, validity flags, target labels, and response hashes. It does not release
or rejudge provider text and does not alter the prospective decision.

Both selectors strongly prefer ASK: 0.733 of all ASK-first outputs and 0.723 of
all EXPLAIN-first outputs select ASK; among valid outputs the rates are 0.752 and
0.794. This is not a presentation-order artifact. The ASK-rate difference is
+0.010 [95% context-cluster CI -0.029, +0.050], both outputs are valid in 0.900
of context-model pairs, and agreement conditional on both being valid is 0.789.

ASK-first separates human-probing from human-telling contexts by only +0.058
[95% stratified-context CI -0.025, +0.142]. EXPLAIN-first separates them by
+0.104 [+0.029, +0.171], but its higher invalid rate and strong ASK base rate
leave total target accuracy at chance. The model breakdown exposes two different
failure modes:

| Model | ASK-first ASK rate on telling | EXPLAIN-first ASK rate on telling | Main failure |
|---|---:|---:|---|
| MiniMax-M2.7 | 0.458 | 0.208 | Format invalidity (0.104 / 0.521 on telling) |
| MiniMax-M3 | 0.375 | 0.562 | Weak and wording-sensitive conditioning |
| DeepSeek-V4-Pro | 0.958 | 0.938 | Near-universal ASK policy |
| Doubao-Seed-2.0-Lite | 0.938 | 0.875 | Near-universal ASK policy |
| GLM-5.2 | 0.792 | 0.771 | Strong ASK policy |

The resulting mechanism is a **selection--execution gap with policy anchoring**.
All five systems can nearly perfectly realize an externally fixed ASK or EXPLAIN
action, but an explicit binary selector does not reliably infer which action the
conversation calls for. For three systems, exposing a selector largely
re-expresses the same question-policy default that caused the original telling
harm. One system instead shows substantial format noncompliance. Stage separation
alone therefore does not constitute an adaptive controller.

## Closest-work and novelty boundary

Strategy-before-generation is not new. Wang et al. (2023) jointly predict tutor
strategy and response; Ikram et al. (2025) directly evaluate future tutor-move
prediction; Tutor CoPilot deliberately retains human strategy selection; and
SLOW (2026 preprint) separates learner-state inference from action selection.
This trial cannot claim to invent a two-stage tutor.

The defensible addition is the controlled falsification: the same contexts,
models, serving period, and observed human next-action reference are crossed
with two independently worded selectors, both counterfactual executors, and a
concurrent single-pass baseline. This design shows causally that excellent
action realization does not imply competent action selection, and that naive
modularization can significantly degrade the action match it was meant to fix.

## Scientific boundary

The human next action is one observed reference, not a uniquely optimal teaching
decision. Question marks operationalize a binary action boundary, not response
quality. The five provider snapshots are a fixed panel, not a model population.
No endpoint measures student learning. The post-hoc action-bias audit localizes
the registered failure but is not confirmatory evidence for a new gate.

## Reproducible artifacts

- Primary report: `artifacts/two_stage_routing_trial_analysis_v1/two_stage_routing_report.json`
  (SHA-256 `3f229c353ebf74bfff27d822dd0db17bb0871083bfbece7255ef4f7c618260da`).
- Selector summary: `artifacts/two_stage_routing_trial_analysis_v1/selector_summary.csv`
  (SHA-256 `74302ea3055a70a5f4abc6dace892d66785195873782fe539ca79ff4c7f8e904`).
- Registered binary contrasts:
  `artifacts/two_stage_routing_trial_analysis_v1/binary_policy_contrasts.csv`
  (SHA-256 `86d46fd7e027c5d5774974615acc0925d33f8b92c316a1a9fb51160eb8c60f5a`).
- Post-hoc diagnostic report:
  `artifacts/two_stage_selection_bias_audit_v1/selection_bias_report.json`
  (SHA-256 `2a52d95307986430fbdad971a105898616e745f7edf16d85d8be208280cb86d7`).
- Post-hoc target separation:
  `artifacts/two_stage_selection_bias_audit_v1/selector_target_separation.csv`
  (SHA-256 `f26e44ce94bbc67743c862b5ab348570a7f3477242c1c676fac66aa53677436e`).

Raw provider responses and the private request manifest remain excluded from
version control.
