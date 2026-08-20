# Planning-only protocol for a learner-outcome extension

Snapshot: 2026-08-20. Status: **planning only; not preregistered; not started**.
This document is not evidence of ethics approval, recruitment, collection, or a
learning effect. Its purpose is to make the remaining journal-level requirement
concrete without weakening the present paper's claim boundary.

## Why archive joins and simulated students are insufficient

EduBenchmark contains real model responses, while EdNet and PTADisc contain real
longitudinal student attempts. The same learners did not receive the evaluated
model responses, so joining these sources would manufacture a counterfactual and
cannot identify a tutoring effect. LongTutor also has no unbiased retained future
attempt after its selected 200-event window. Prompted student agents are useful
for software testing but are not objective learning outcomes.

Recent trials clarify the required standard. The PNAS high-school mathematics
trial preregistered an unassisted exam and found that unguarded GPT access could
harm learning even while improving assisted practice
([Bastani et al., 2025](https://doi.org/10.1073/pnas.2422633122)). A university
physics RCT used pre/post quizzes and an active-learning control
([Kestin et al., 2025](https://doi.org/10.1038/s41598-025-97652-6)). A five-school
UK trial measured transfer to novel problems under direct tutor supervision
([LearnLM Team and Eedi, 2025](https://arxiv.org/abs/2512.23633)). A six-session
school RCT held content and interface constant while changing only pedagogical
prompts
([Fütterer et al., 2026](https://doi.org/10.1007/s10648-026-10133-8)). These
designs motivate an unassisted delayed outcome, policy-level randomization,
content grounding, teacher oversight, and explicit attrition accounting.

## Causal question

Does an external controller that changes question-first and answer-reveal policy
from observable learner state improve delayed, unassisted mathematical transfer
relative to a model's default policy? The key contrast is controller versus
default, averaged across three hidden model routes. Static question-withhold and
static explain-reveal arms test whether one universal pedagogy helps or harms.
This directly follows the current evidence: system clauses control these actions,
ordinary learner requests do not, and a universal questioning prompt can suppress
appropriate telling.

## Design

- Recruit 3,300 grade 8--10 learners from at least 40 classrooms after ethics
  approval and required guardian/learner consent or assent.
- Randomize learners within classroom and pretest quartile across four policy
  arms and three hidden model routes: 12 cells of 275 learners.
- Use MiniMax-M3, GLM-5.2, and DeepSeek-V4-Pro as deployed route snapshots. Model
  interactions are exploratory; three routes do not define a model population.
- Run a pretest, six 35-minute learning sessions over three weeks, an immediate
  unassisted posttest, and a seven-day unassisted delayed posttest.
- Give every route identical curriculum grounding, worked solutions, UI, safety
  constraints, and time. No tutor is available during either outcome test.

The adaptive controller is deterministic and external to the model. It selects
question-withhold after a productive attempt, but switches to explanation-reveal
after two failed attempts, an explicit stall, or a safety trigger. The two static
arms always apply one of those policies. The default arm omits question/answer
policy clauses while retaining grounding and safety. Semantic warmth is not a
treatment because the frozen lexicon failed validation.

## Outcomes and estimand

The sole primary outcome is the seven-day unassisted transfer score, standardized
to the pooled control distribution. Items must be isomorphic or novel transfer
items absent from learning sessions. Scoring is exact numeric,
symbolic-equivalence, or fixed-choice and fully automatic; no human annotation is
introduced.

The primary intention-to-treat contrast is adaptive controller minus model
default. ANCOVA includes pretest, model route, and classroom fixed effects, with
small-sample-corrected classroom-clustered standard errors. Secondary outcomes
include immediate transfer, retention, time on task, independent attempts before
help, solution copying, completion, and differential attrition. Model-by-policy
interactions and process mediation are exploratory.

## Power and missingness

The planning script uses a deliberately conservative independent-arm
approximation: two-sided alpha 0.05, 80% power, standardized effect 0.15, and no
credit for pretest adjustment or within-class blocking. It requires 698 completed
learners per arm. Inflating for 15% attrition requires 822; the balanced design
uses 825 per arm, or 3,300 total. Reproduce with:

```bash
python scripts/power_learner_outcome_trial.py --require-pass
```

All randomized learners remain in the intention-to-treat analysis. Report
complete-case results only alongside multiple imputation, inverse-probability
weighting, and worst-case bounds. An arm difference above five percentage points
in delayed-test completion is a mandatory attrition warning, not a reason to
drop an arm.

## Safety and non-negotiable gates

- Teacher dashboard, escalation, and immediate kill switch during every session.
- No high-stakes grading, clinical advice, sensitive profiling, or unsupervised
  deployment to minors.
- Separate identity/contact data from research logs; retain exact assignment,
  prompt version, route, policy decision, timestamps, attempts, and errors.
- Validate realized question-first and correct-answer-reveal compliance before
  outcomes are unblinded; do not resurrect the failed warmth construct.
- Register the protocol, analysis code, primary outcome, and exclusions before
  enrollment. Any later amendment must be timestamped and cannot hide an arm.
- No learning-effectiveness statement is eligible until ethics approval,
  registration, complete collection, and the frozen analysis all exist.

The machine-readable planning contract is
`data/learner_outcome_trial_spec_v1.json`. A future collaborating institution may
change population-specific operational details before registration, but any
change creates a new version rather than silently rewriting this planning record.
