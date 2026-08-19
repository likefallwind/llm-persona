# Semantic-panel analysis freeze

Frozen: 2026-08-19 18:41:19 Asia/Shanghai, before any second- or third-judge
annotation was available.  The live append-only file then contained 311/1,080
successful annotations, all from MiniMax-M3.  The analysis script SHA-256 was
`844f03f0924603e89f2fb5dcca8097cb381fe5acda51a36389c81e7c3690bc7f`.

This is a prospective freeze for multi-judge quantities, not a claim of full
preregistration.  Single-judge prompt directions and preliminary predictive
results had already been inspected and must be labelled exploratory.

Implementation amendment: at 2026-08-19 18:50:04, with 360/1,080 annotations
(320 MiniMax and 40 GLM), the already-prespecified response-order check from
`research/02_semantic_coding_protocol.md` was found missing from the analyzer and
implemented as an identical-response, other-judge-residual position test.  No
hypothesis or threshold was added.  The amended analyzer SHA-256 is
`eb226420193355865e4b2e25f976b752e08bada9acf27877931c0633eb6245f8`.

Second implementation amendment: at 2026-08-19 18:57:22, with 410/1,080
annotations, the analyzer's already-prespecified exact-context model-variance
analysis was found to lack its planned context bootstrap interval.  Item-level
bootstrap intervals were added without changing the estimand or hypotheses.  The
resulting analyzer SHA-256 is
`f9ed6d763fa11495eedfd7cda659b4a63f27c26226d47c8f781db622129a2bcd`.

Third implementation amendment: at 637/1,080 annotations (MiniMax-M3 320/320,
GLM-5.2 317/320, DeepSeek-V4-Pro 0/320; no LongTutor judge calls), the formal
coverage gate was found to verify annotation IDs but not independently recheck
the response-level invariants promised in `research/06_reproducibility_and_release_ledger.md`.
The analyzer now requires exactly six candidates per annotation, 2,160 unique
response units, 17,280 response × dimension consensus rows, and three distinct
judges per row.  Report prose was also corrected to call the eight scales
*candidate behavioral dimensions* until validity gates pass.  No estimand,
hypothesis, threshold, or result-selection rule changed.  The amended analyzer
SHA-256 is
`aefa19fc3a7f99c2acb73b73745381bfa3594247fe327351035bf7591e626459`.

## Units and reduction

- A judge call codes all six candidate responses for one sampled context.
- Reliability uses response × dimension targets and the three fixed judges.
- All substantive analyses first reduce ratings to the median of the three
  judges for each response and dimension.  Judge calls are never treated as
  independent educational observations.
- Prompt effects are paired by the underlying MathDial context within model.
  Intervals resample contexts, preserving the six responses sharing a context.
- Cross-task stability has six model systems as its unit.  It is finite-panel
  description, not population psychometrics.

## Prespecified analyses

1. **Coverage gate.** No confirmatory report unless all 1,080 planned judge ×
   context annotations succeed with valid eight-dimension JSON.  Retries remain
   in the append-only log; only the latest success determines coverage.
2. **Judge reliability.** For every dimension report pairwise exact agreement,
   within-one agreement, Spearman correlation, quadratic weighted kappa,
   ICC(3,1), and ICC(3,k).  Do not silently discard low-variance dimensions.
3. **Exact-context model variance.** In each benchmark and dimension, decompose
   the balanced response matrix into context, model, and residual components;
   report model partial eta-squared after context control.
4. **Cross-task stability.** Use only generic scaffolding, generic hard,
   Socratic, and longitudinal tasks.  Center across models within exact context,
   scale within benchmark, and report ICC(3,1) plus all task-pair rank
   correlations.  Six models preclude a general population claim.
5. **Prompt intervention.** Within model and underlying context, subtract generic
   from explicit-pedagogy score.  Report all six model effects separately for
   standard and hard sets, context-bootstrap intervals, Wilcoxon tests, and BH
   correction over the 48 model × dimension contrasts within each difficulty.
6. **Judge-family sensitivity.** For each judge score, subtract the mean score of
   the other two judges for the identical response and dimension.  Compare these
   residuals for same-family versus other candidates, aggregating and
   bootstrapping at the six-candidate context batch.
7. **Leave-one-judge-out sensitivity.** Recompute response medians and all
   within-context-centered model profiles after excluding each judge; report the
   correlation with the full profile vector.  Material sign reversals must be
   shown, not averaged away.
8. **Incremental criterion association.** On sampled MathTutorBench responses,
   evaluate exact-item, transparent-feature, semantic-feature, and combined
   logistic models by holding out each candidate model.  Report AUC, Brier score,
   accuracy, and every fold; a mean gain without fold consistency is insufficient.
9. **Independent action convergence.** Join response hashes to the frozen hybrid
   TF-IDF/SVM dialogue-act predictions trained on existing human MathDial labels.
   The primary directional checks are higher help directness for `telling` than
   `probing/focus`, and lower elicitation and autonomy support for `telling`.
10. **Multiplicity and reporting.** The eight dimensions are reported together.
    Intervention p-values use within-difficulty BH adjustment.  Reliability,
    stability, effect sizes, and criterion convergence—not a single p-value—
    determine interpretation.

## Failure rules

- Above-chance model attribution alone is a fingerprint, not a disposition.
- A dimension with poor multi-judge reliability cannot support a stable-disposition
  claim even if its prompt effect is large.
- A reliable but task-unstable dimension is context-specific.
- Prompt sensitivity establishes steerability, not educational benefit.
- Dialogue-act agreement establishes behavioral convergence, not learning gain.
- Majority LLM judgement is not human ground truth; the existing expert-pair
  calibration is reported separately.

## Deferred work

Local Qwen/Ollama validation is paused at the user's request until a stronger
server is available.  Any new external student-simulation experiment requires a
separate payload/destination disclosure because it would transmit a new class of
data beyond the currently authorized semantic-coding panel.
