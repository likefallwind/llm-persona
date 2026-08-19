# Model and judge panel card

Snapshot: 2026-08-19.

## Core candidate panel

| Analysis label | Role | Inclusion rationale | Important limitation |
|---|---|---|---|
| MiniMax-M3 | Candidate and independent semantic judge | Complete paired coverage and official API access | Candidate/judge family overlap is audited; API alias is not a frozen weight snapshot |
| MiniMax-M2.7 | Candidate | Complete paired coverage; approximate within-provider comparison with M3 | Version change bundles training, scale, alignment, and serving changes |
| GLM-5.2 | Candidate and independent semantic judge | Complete paired coverage and distinct provider route | Gateway alias and serving stack are not independently controlled |
| DeepSeek-V4-Pro | Candidate and independent semantic judge | Complete paired coverage and distinct provider route | Gateway alias and serving stack are not independently controlled |
| Doubao-Seed-2.0-Pro | Candidate | Complete historical paired coverage | Endpoint is no longer available; exact regeneration may not be possible |
| Qwen3.5-4B | Candidate | Complete paired coverage and a substantially smaller open-weight family | Existing outputs are analyzed; new API generation is not currently configured |

The six systems are a convenience panel selected for shared coverage, not a
random sample from a model population.  Item-level uncertainty can be estimated
precisely, but population-level statements about model families, parameter scale,
or the LLM ecosystem cannot be supported by six model means.

## Extended and family panels

The MathDial-only extended panel adds Doubao-Seed-2.0-Lite,
DeepSeek-V4-Flash, and Qwen3.8-27B.  It permits nine-model descriptive
replication and four approximate within-family pairs.  These pairs are not clean
scale interventions: release date, training data, architecture, alignment,
decoding, and provider serving may all differ.  Family resemblance is therefore
appendix evidence rather than a headline causal claim.

## Generation comparability

All core responses were produced through the same EduBenchmark harness against
the same item IDs.  Exact-item controls remove shared prompt difficulty, and
paired intervention contrasts compare prompt arms within the same model/item.
However, provider-side system prompts, implementation details, quantization,
backend revisions, and nondisclosed model updates are not experimentally held
constant.  Model names should be interpreted as deployed API configurations at
the recorded evaluation time, not immutable scientific specimens.

A file-level audit covers 84 core benchmark/model runs used as tutoring data,
negative controls, or external criteria.  Every prediction and summary file is
pinned by SHA-256.  Temperature is stored for 22/84 runs, but seed and prompt
version are stored for 0/84; consequently 0/84 satisfy the strict minimum tuple
for exact provider-response regeneration.  This distinction is central:
analysis from the frozen responses is exactly reproducible, whereas regeneration
of the original API bytes is not.  See
`artifacts/provenance_audit/generation_provenance_report.md`.

## Semantic judge panel

MiniMax-M3, GLM-5.2, and DeepSeek-V4-Pro independently rate every retained
context. Candidate identities are replaced by independently shuffled blind
letters for each judge and context. The primary unit is the response-level
median across all three judges. One technically failed prompt pair is excluded
for every judge under the frozen attrition amendment; no confirmatory result is
emitted unless each of the remaining 2,148 responses has three distinct ratings.

Judge competence is calibrated on 482 existing expert preference pairs shown in
both candidate orders.  Individual agreement with expert preference is
0.817--0.844 and position consistency is 0.900--0.919.  The majority does not
significantly outperform the best individual judge, so consensus is used for
robustness rather than described as superior human alignment.

The analysis explicitly reports:

- pairwise exact/within-one agreement, rank correlation, weighted kappa, and ICC;
- leave-one-judge-out profile and prompt-effect sensitivity;
- judge-family residual bias when a judge evaluates a same-family candidate;
- candidate-position residuals after context and model controls;
- scale floor, ceiling, dispersion, and entropy diagnostics.

Shared LLM training data and evaluator conventions can still induce correlated
errors.  The panel is not human ground truth, and dimensions with weak reliability
or range restriction are not retained as validated dispositions.

## Nonclaims and update policy

Results describe model-conditioned behavior under the observed tasks and prompt
regime.  They do not establish consciousness, stable human personality, provider
intent, or educational effectiveness for real students.  Any future rerun with a
new alias, provider endpoint, server-hosted Qwen model, or prompt template is a new
panel version and must not silently overwrite this snapshot.
