# Top-tier completion audit

Snapshot: 2026-08-20. This audit distinguishes a defensible main-conference NLP
submission from the substantially stronger evidence needed for an education or
general-science journal claim.

## Main-conference NLP package

The current package has a coherent measurement-and-falsification contribution:
a large exact-item archive analysis; generic-task and verbosity controls;
human-labelled teacher-action convergence; a blinded three-judge semantic
panel; a complete prospective factorial; an independently ordered replication;
and a post-result, downgrade-only validation of its three surface detectors.
Question-first and correct-answer-reveal detectors validate, while the
encouragement lexicon does not validate semantic warmth and is explicitly
downgraded. Failed learner-request gates, diagnosis nulls, telling-action harm,
and component interactions remain central results rather than exclusions.

Two additional prospective action-control trials materially strengthen the
mechanism boundary. A 1,920-call balanced trial prospectively replicates the
uniform prompt's probing benefit and telling harm while rejecting a one-pass
adaptive router. A separately published 2,400-call selection--execution trial
then rejects the proposed two-stage remedy: both selectors are near chance and
significantly worse than a same-snapshot single-pass baseline, even though ASK
and EXPLAIN executors realize their actions at 0.998--1.000. This is useful
negative evidence because the failed remedies were frozen before collection and
are not silently removed. It supports a controller-requirements result, not a
claim that this paper invents or solves adaptive routing.

The locally accessible package has completed its final release checks, anonymous
PDF audit, and stacked Draft PR CI pass. It is ready for a serious
main-conference NLP review under the bounded claim above. Acceptance is never
“without dispute”: reviewers can still challenge construct choice, model
sampling, API snapshot transport, LLM-judge dependence, and the absence of human
learning outcomes.

## Final release evidence

The integration snapshot was rebuilt from the governed raw-response inputs with
`bash scripts/finalize_semantic_analysis.sh` on 2026-08-20. The command exited
zero after confirming 1,074/1,074 semantic annotations, 2,560/2,560 parent
factorial responses, 640/640 independently ordered responses, 144/144 detector
annotations, 1,280/1,280 paraphrase responses, 1,920/1,920 action-routing
responses, and 2,400/2,400 two-stage responses, all with zero eligible errors or
missing cells. It then verified 72 registered release claims, passed all 55
tests, rebuilt the paper figure, and wrote a 349-file reproducibility manifest.

The code/artifact integration snapshot `cb933b0` is published on Draft PR #14,
which is open, mergeable, and based on the two-stage result PR. GitHub Actions
run `32355321110` completed every clean-checkout step successfully: syntax, 55
tests, 72 claims, 225 Git-eligible artifact privacy checks, anonymous-PDF audit,
figure rebuild, and checkout non-mutation. The PDF audit reports nine pages,
references only on page nine, 14 embedded fonts, blank author/title metadata,
review mode, and no identity or local-path hits. Preceding stacked result PR runs
are also green: `32353317168`, `32353350276`, `32353919584`, `32353996329`, and
`32354181133`.

## Broad-journal boundary

The work is not ready for a claim that agent personality or policy improves
learning. No prospective learner experiment provides objective pre/post
outcomes, and existing LongTutor analyses test diagnosis rather than subsequent
learning. A read-only, outcome-blind schema audit found that every selected
LongTutor sequence ends at index 199 with zero retained future interactions;
upstream construction chooses the 200-event window ending at the learner's last
incorrect response. Any discarded suffix is therefore selected to contain no
later errors and cannot serve as an unbiased future outcome.

A journal-level extension needs a prospectively specified learner study or a
separately validated simulator, objective pre/post tasks, assignment and
attrition handling, power analysis at the learner/classroom unit, and an
independently sampled model panel. A future server-hosted Qwen panel can improve
model transport, but it cannot substitute for learner-outcome evidence.

The remaining empirical requirement is now specified rather than left vague.
`research/24_learner_outcome_trial_protocol.md` and
`data/learner_outcome_trial_spec_v1.json` define a planning-only, 3,300-learner
trial of an external adaptive controller versus static and default policies,
with a seven-day unassisted transfer test, automatic scoring, intention-to-treat
analysis, and explicit attrition/safety gates. This is not a completed or
registered study and cannot change the present claim boundary.

## Checkpoints that require publication or study coordination

The remaining items cannot be truthfully completed inside this repository:

1. At upload time, record the chosen venue's live call, deadline, format, and
   responsible-NLP form version; no target venue has been selected here.
2. Record the final public or anonymous artifact URL and immutable submission
   commit after deciding the venue's anonymity policy, and repeat the upstream
   license review against that exact release payload.
3. Do not promote the work to an educational-efficacy or broad-journal claim
   until the planned learner study has ethics approval, registration, objective
   outcomes, and completed data. A future server-hosted Qwen panel is a transport
   extension, not a substitute for that study.
