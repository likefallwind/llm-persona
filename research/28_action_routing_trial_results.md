# Prospective action-routing trial results

Date completed: 2026-08-20. Status: **complete prospective trial; registered
joint claim failed**.

## Provenance and completion

The prompts, 96 public benchmark contexts, four arms, five-model panel,
model-specific eight-stratum order, three human-trained classifiers, estimands,
and thresholds were published in draft PR #9 before collection. The first launch
exposed a result-serialization incompatibility and was terminated with 0 response
rows and no result inspection. The implementation-only correction and its
regression test were then published as `d302b8f` before restarting from zero.
Neither amendment nor restart changed a request, prompt hash, sample, order,
model, route, metric, threshold, or decision rule.

The corrected run started at `2026-08-20T10:19:52+08:00`, finished at
`2026-08-20T11:23:05+08:00`, and exited with code 0. All 1,920 planned cells
(96 contexts x four arms x five models) completed with zero failed, empty,
missing, duplicate, or unexpected cells. Every model has exactly 384 responses,
and all 48 model-specific blocks retain all eight target-by-arm strata.

## Registered decision: the single-pass adaptive router failed

All three TF--IDF/linear-SVM variants were trained on the frozen 18,541 human
MathDial teacher turns and applied to the identical responses. The uniform
prompt's target-specific reversal replicated prospectively, but the adaptive
router did not meet any of the recovery, noninferiority, or aggregate-improvement
gates. All intervals below are 95% context-cluster bootstrap intervals over the
fixed five-model panel.

| Registered contrast | Character SVM | Hybrid SVM | Word SVM | Decision |
|---|---:|---:|---:|---|
| Uniform - generic, human `probing` | +0.158 [0.079, 0.242] | +0.154 [0.063, 0.246] | +0.150 [0.058, 0.238] | Replicated |
| Uniform - generic, human `telling` | -0.204 [-0.279, -0.129] | -0.263 [-0.346, -0.183] | -0.233 [-0.321, -0.150] | Replicated harm |
| Adaptive - uniform, human `telling` | +0.092 [0.042, 0.142] | +0.146 [0.092, 0.204] | +0.138 [0.079, 0.204] | Failed +0.15/every-model gate |
| Adaptive - generic, human `telling` | -0.113 [-0.196, -0.038] | -0.117 [-0.204, -0.033] | -0.096 [-0.183, -0.012] | Failed noninferiority |
| Adaptive - uniform, human `probing` | -0.083 [-0.162, -0.008] | -0.079 [-0.158, 0.000] | -0.050 [-0.129, 0.033] | Failed noninferiority |
| Adaptive - generic, balanced overall | -0.019 [-0.069, 0.031] | -0.021 [-0.077, 0.033] | +0.002 [-0.054, 0.058] | No aggregate improvement |

The router partially recovered `telling` relative to the uniform prompt, but it
remained significantly worse than generic under every classifier. Its probing
gain over generic was positive (+0.075 to +0.100), yet it did not retain the
uniform prompt's probing performance. This is a failure of the frozen proposed
solution, not an ambiguous near-pass.

## Oracle diagnostic and measurement boundary

The oracle arm explicitly prescribed the human target action. Its classifier
match was 0.700--0.775 for `telling` but only 0.429--0.454 for `probing`, so the
registered requirement that both exceed 0.65 failed. The asymmetry must be read
against the classifiers' pre-existing problem-grouped human validation: probing
recall is only 0.400--0.405, with most errors assigned to the neighboring
`focus` class. The oracle failure therefore cannot be interpreted solely as
model noncompliance.

## Post-hoc deterministic mechanism audit

After the primary result was inspected, a deterministic audit separated binary
question realization from the finer four-way dialogue-act labels. It uses only
question marks, first-sentence boundaries, counts, lengths, and response hashes;
it does not release response text or use an LLM judge.

| Target | Arm | Any-question rate | First-sentence question rate |
|---|---|---:|---:|
| `probing` | generic | 0.288 | 0.025 |
| `probing` | uniform | 0.963 | 0.271 |
| `probing` | adaptive | 0.700 | 0.217 |
| `probing` | oracle | 1.000 | 0.967 |
| `telling` | generic | 0.308 | 0.050 |
| `telling` | uniform | 0.854 | 0.288 |
| `telling` | adaptive | 0.633 | 0.238 |
| `telling` | oracle | 0.000 | 0.000 |

The oracle achieved perfect binary realization: every probing response contained
a question and every telling response contained none. This localizes the oracle
probing shortfall largely to the `probing`/`focus` measurement boundary.

The single-pass adaptive router, in contrast, asked questions on 70.0% of
human-probing contexts and 63.3% of human-telling contexts. Its probing-minus-
telling separation was only +0.067 [95% stratified-context CI -0.033, +0.171]
and ranged from -0.104 to +0.229 across models. The uniform prompt was also
poorly contextual: it asked questions in 85.4% of telling contexts. Adaptive
routing reduced that rate but remained far above the generic arm's 30.8%.

The post-hoc mechanism interpretation is therefore **selection bottleneck plus
question-policy anchoring**: this fixed panel can realize an explicitly selected
binary action, but a one-pass instruction to select among pedagogical moves does
not reliably condition that selection on the conversation. This interpretation
requires a prospective two-stage selection-then-execution trial before it can be
promoted to a confirmatory claim.

## Scientific boundary

The prospective result confirms the average-gain/contextual-harm reversal on a
fresh, balanced, same-snapshot panel. It rejects the tested single-pass adaptive
router as a solution. It does not prove that the observed human move is uniquely
optimal, that action agreement causes learning, or that five provider snapshots
form a model population. Question marks are binary surface indicators, not full
dialogue-act labels. The surface mechanism audit is explicitly post hoc.

## Reproducible artifacts

- Primary report: `artifacts/action_routing_trial_analysis_v1/action_routing_report.json`
  (SHA-256 `3c62585a5ba3b0a402c7f39d236244e13d2336c99d9eadef06976f59705ca22c`).
- Primary contrasts: `artifacts/action_routing_trial_analysis_v1/action_match_contrasts.csv`
  (SHA-256 `4d78e747c71c66eb41f2da4df154efcf9948b16fdfddf87f573a937b5e346f6b`).
- Post-hoc mechanism report:
  `artifacts/action_routing_surface_audit_v1/surface_mechanism_report.json`
  (SHA-256 `4ed3034df977e698a4a3e3353773ae2c36cc762a435d7d7a159dc3c514879e97`).
- Derived surface rows:
  `artifacts/action_routing_surface_audit_v1/surface_response_metrics.csv`
  (SHA-256 `7bd67bb7dd2a2d9c4291541e89940c44ed3384a9b8a739e9ae208f1d166f13ff`).

Raw provider responses and the private request manifest remain excluded from
version control.
