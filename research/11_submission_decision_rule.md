# Semantic result and submission decision rule

Frozen: 2026-08-19 after 637/1,080 successful annotations.  At freeze time the
main-task counts were MiniMax-M3 320/320, GLM-5.2 317/320, and DeepSeek-V4-Pro
0/320; no judge had begun the 40 LongTutor batches.  Partial MiniMax/GLM tables
had already been inspected, so these thresholds are **not** represented as a
preregistration.  They are a prospective third-judge reveal and manuscript
decision rule intended to prevent selective emphasis after the independent
DeepSeek panel arrives.

Frozen analyzer hashes:

| Script | SHA-256 |
|---|---|
| `analyze_semantic_panel.py` | `aefa19fc3a7f99c2acb73b73745381bfa3594247fe327351035bf7591e626459` |
| `analyze_semantic_leaveout_sensitivity.py` | `794aa8e23626ffd505aaffa703daeadb2d2a7027988df2af5668e0469596d1c9` |
| `analyze_semantic_scale_diagnostics.py` | `c62871277dede714f3890899d1956951eb4361c17b2422c690446d54c26ce1cd` |
| `analyze_semantic_objective_validity.py` | `9810c8f9425c029d05254a94add97d2595efa01f91b80d7dcb4cc2661a4e7e08` |
| `evaluate_submission_decision.py` | `deb14346686160ce6a01ed8844c050fb595ff73ca28c82aaea76e05c4c2b0a89` |

The historical analyzer hash above identifies the prospective decision freeze.
After the provider failure documented in
`research/13_semantic_attrition_amendment.md`, only exclusion-aware coverage and
row-count plumbing changed; no threshold, estimand, or decision branch changed.
The implementation used for the formal result is pinned below:

| Attrition-aware component | SHA-256 |
|---|---|
| `analyze_semantic_panel.py` | `dc14ebdfb5d4b03ed3aa6ae4aba8e2ad5639193da481b401c7d5aecaeb5983b8` |
| `semantic_judge_status.py` | `a115af013f9054a373d3c9814432054717a90d4622d0baf8eae568b44aa6c2aa` |
| `semantic_panel_exclusions.py` | `e12a820f0d230ba45621529a6d6e92d6b925974821f5e24b60ce77a2e8ea502f` |
| `semantic_panel_exclusions_v1.json` | `90c2eaefa8127d4199300f00b58d13f00585abf97baec27ac2b67d1fc66241fa` |
| `evaluate_submission_decision.py` | `deb14346686160ce6a01ed8844c050fb595ff73ca28c82aaea76e05c4c2b0a89` |

Implementation note frozen at 640/1,080 successful annotations, before any
DeepSeek-V4-Pro or LongTutor annotation was available: the executable decision
gate applies the model-variance interval requirement to **every** sampled
benchmark for a dimension, and treats any prompt sign reversal in the full set
of model × MathDial-task headline candidates as a failure.  Automatic action-
direction criteria are limited to the two dimensions with unambiguous scale
anchors: `help_directness` (telling higher; pedagogy prompt lower) and
`elicitation` (telling lower; pedagogy prompt higher).  Other dimensions can
reach the disposition tier through the human-gold LongTutor diagnosis criterion,
but are not assigned a convenient action direction after results are seen.

Multiplicity amendment frozen at 725/1,080 successful annotations, while all
three judges still had 0/40 LongTutor batches: criterion 3 uses the prespecified
within-outcome Benjamini--Hochberg adjusted `q < 0.05`, not an unadjusted
permutation `p < 0.05`.  This is strictly more conservative and was fixed before
any semantic-to-human-gold LongTutor result was available.

## Dimension-level classification

Every one of the eight named dimensions is reported.  A dimension is classified
using the following hierarchy; a failure is not hidden by averaging it with a
stronger dimension.

### Reliable semantic measurement

All must hold:

1. three-judge ICC(3,k) is at least 0.60;
2. score standard deviation is at least 0.50 and neither endpoint contains more
   than 80% of response-level consensus scores;
3. the panel-level minimum leave-one-judge-out model-profile correlation is at
   least 0.70;
4. no leave-one-judge-out prompt-effect sign reversal occurs for a dimension ×
   model × task contrast used
   in the headline.

A dimension failing this tier is described as unreliable or range-restricted,
not as evidence for a model disposition.

### Cross-task semantic signature

In addition to reliable measurement, all must hold:

1. model identity explains nonzero exact-context variance with a bootstrap 95%
   interval whose lower endpoint is above zero;
2. cross-task stability has ICC(3,1) at least 0.50 or median pairwise task
   Spearman at least 0.50.

At the panel level, held-out-task attribution using all semantic features must
also exceed 1/6 chance.  This aggregate check supports transport of the semantic
measurement system; it is not misreported as a univariate test of each dimension.

This tier supports a finite-panel semantic *signature*.  Attribution alone never
upgrades a dimension to a disposition.

### Validated pedagogical disposition

In addition to both tiers above, at least one independent criterion must hold:

1. adding the full semantic panel improves exact-item, leave-one-model-out quality
   prediction over the transparent baseline with a positive mean AUC change and
   no negative model fold, **and** the dimension separates independently inferred
   human actions in its anchored direction (for example, elicitation is higher
   for probing/focus than telling); or
2. its paired prompt movement is consistent with the independently trained
   human-action result and remains directionally consistent under each
   single-judge exclusion; or
3. on the 40 LongTutor histories, it predicts human-gold diagnosis beyond exact
   history with the registered permutation test at within-outcome BH-adjusted
   q < 0.05.

Criterion 3 is primary only for human-gold diagnosis.  LLM-judged historical-
evidence equivalence remains secondary regardless of p-value.

## Bias and transportability flags

- A mean own-family judge residual difference above 0.25 scale points is a
  material self-family-bias flag.  A flagged dimension cannot use the affected
  judge as sole support; full and leave-one-judge estimates are shown together.
- A candidate-position range above 0.25 scale points after context/model control
  is a material slate-position flag.
- Absolute means are never compared across benchmarks.  The six-answer slate
  permits within-context comparison but does not establish isolated-response
  calibration.

These are practical interpretation thresholds, not additional null-hypothesis
tests, and are labelled as such in the paper.

## Manuscript go/no-go rule

The stronger title and thesis about *pedagogical dispositions* remain eligible
only if at least two semantically distinct dimensions reach the validated-
disposition tier and the result is not solely driven by one judge family.  If
fewer than two do so, the paper is reframed around *pedagogical policy signatures*
and the failed construct-validity audit becomes a central result.

The contextual-oversteering claim remains eligible only if the already observed
human `telling` result is accompanied by a reliable semantic prompt movement
that distinguishes direct help/elicitation rather than merely response length.
Otherwise it remains a robust action-classifier result but not a semantic
mechanism claim.

A main-conference NLP submission can proceed if the finite-panel measurement and
falsification contribution survives these rules.  A broad education or general-
science journal claim about learning effectiveness does **not** proceed without a
prospective learner study or independently validated simulator and objective
pre/post outcomes.  More LLM judges cannot substitute for that missing criterion.
