# Prospective paraphrase replication results

Date completed: 2026-08-20. Status: **complete prospective post-result wording
replication**.

## Outcome-independent provenance

The complete method, prompts, order plan, metrics, thresholds, and analysis code
were committed as `00fb58e` and published in draft PR #9 before any response call.
The experiment then ran without a method change. It completed all 1,280 planned
cells (five models x 256 cells), with zero failed, empty, missing, duplicate, or
unexpected cells. The detached run started at `2026-08-20T09:07:48+08:00`,
finished at `2026-08-20T10:02:31+08:00`, and recorded exit code 0.

This is prospective with respect to the two new wording sets and the
control-asymmetry estimand, but it follows inspection of the original factorial
results. It is therefore a post-result wording replication, not an
outcome-blind replication of the original study.

## Frozen-gate decisions

Both clause paraphrases had to pass independently; pooled success could not
rescue a failed wording set.

| Endpoint | Paraphrase A effect (95% block-bootstrap CI) | Paraphrase B effect (95% block-bootstrap CI) | Frozen decision |
|---|---:|---:|---|
| Question-first policy -> question-first behavior | 0.834 [0.809, 0.863] | 0.991 [0.981, 0.997] | Cross-wording robust |
| Reveal policy -> correct-answer reveal | 0.984 [0.969, 1.000] | 0.991 [0.978, 1.000] | Cross-wording robust |
| Warm policy -> literal encouragement marker | 0.431 [0.388, 0.487] | 0.291 [0.250, 0.331] | **Not** cross-wording robust |

Question and answer effects exceeded their frozen 0.60 target thresholds, were
positive in all five models under both wording sets, and independently passed
the selectivity gate. Their model-specific target effects ranged from 0.656 to
1.000 for question policy and from 0.969 to 1.000 for answer policy.

The literal tone marker passed under paraphrase A but missed the frozen 0.30
threshold under paraphrase B. The cross-wording effect difference was -0.141
[95% CI -0.191, -0.087]. Consequently, the registered joint rule rejects a
paraphrase-robust tone claim. This endpoint remains a string-level marker and is
not evidence of semantic warmth even in paraphrase A.

## Prospectively confirmed control asymmetry

The two configured action policies dominated ordinary learner requests that
asked for the opposite behavior. All four wording-by-policy tests passed every
frozen aggregate and every-model gate.

| Wording | Policy | System conflict effect (95% CI) | Learner override effect (95% CI) | Control gap (95% CI) |
|---|---|---:|---:|---:|
| A | question | 0.881 [0.844, 0.919] | 0.000 [0.000, 0.000] | 0.881 [0.844, 0.919] |
| A | answer | 0.975 [0.950, 0.994] | 0.000 [0.000, 0.000] | 0.975 [0.950, 0.994] |
| B | question | 0.981 [0.963, 0.994] | 0.000 [0.000, 0.000] | 0.981 [0.963, 0.994] |
| B | answer | 0.981 [0.956, 1.000] | 0.000 [0.000, 0.000] | 0.981 [0.956, 1.000] |

Every model had a positive system-conflict effect and control gap for both
policies in both wording sets. The minimum model-specific system effect was
0.781; every model-specific learner-override point estimate was exactly zero.
This confirms the predeclared mechanism in this fixed panel: apparent behavioral
consistency can be imposed by the configured system policy while ordinary
learner requests have essentially no realized control over the same action.

## Adaptivity result and scientific interpretation

Neither learner-need contrast reached its frozen 0.10 threshold under either
wording set:

- direct-minus-explore correct-answer reveal was 0.009 in both A and B; and
- explore-minus-direct question-first behavior was -0.047 in A and 0.009 in B.

The result therefore supports **paraphrase-robust policy addressability**, not
learner adaptivity. Together with the independently observed policy
homogenization and target-specific `telling` harm, it sharpens the paper's
mechanistic claim: reliable control of a tutor's outward action is not evidence
that the tutor selected that action responsively. The tone failure further shows
that not all persona-like surface controls transport even when action controls
do.

This experiment does not establish learning benefit, prove that a human teacher
action is optimal, or generalize beyond the five fixed provider/model snapshots.
The separately frozen action-routing trial is the prospective test of whether a
context-conditioned controller can recover `telling` without sacrificing the
uniform prompt's `probing` gain.

## Reproducible artifacts

The primary machine-readable result is
`artifacts/factorial_paraphrase_replication_analysis_v1/paraphrase_replication_report.json`
(SHA-256 `30c8070f026731700252fee3d40cbc1932224bbfbb1ae511cf4a40590d135207`).
The analysis directory also contains all wording-specific effects, interactions,
cell means, learner contrasts, control contrasts, model breakdowns, and the
paired wording-difference analysis. The derived response-metric table has
SHA-256 `9ced9bf71bf261e0c51d3bd2e17f467b4b018a5a2dcf9149ac1dd5a7737971b5`.
Raw provider responses remain excluded from version control.

Reproduce the frozen analysis with:

```bash
.venv/bin/python scripts/analyze_factorial_paraphrase_replication.py \
  --bootstrap-reps 2000
```
