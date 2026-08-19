# Submission route and internal gates

Snapshot: 2026-08-19.  Venue dates are time-sensitive and must be rechecked on
the official pages before submission.

## Recommended route

The current work is best scoped as a main-conference NLP measurement and
falsification paper.  The next viable official ARR cycle is **October 12, 2026**;
ARR currently lists that cycle as the final route for **NAACL 2027 and COLING
2027**, with a December 20 commitment deadline.  The August cycle has already
closed and EMNLP 2026 required the May 25 cycle, so neither is represented as an
available target.

- Official ARR dates: <https://aclrollingreview.org/dates>
- ACL 2027 official site: <https://2027.aclweb.org/> (conference August 17--22,
  2027; submission and commitment dates still TBA at this snapshot)
- EMNLP 2026 official call: <https://2026.emnlp.org/calls/main_conference_papers/>

Primary operational target: submit to the October 2026 ARR cycle, then use the
reviews to choose NAACL 2027 versus COLING 2027.  If the confirmatory semantic
panel or clean-room reproduction needs a substantive redesign, do not force the
October deadline; revise for the January 2027 ARR route listed for ACL 2027.

## Evidence gates before upload

1. The exclusion-aware semantic panel passes at 1,074/1,074 eligible annotations,
   2,148 responses, 17,184 consensus rows, and three judges per row; the 0.56%
   paired technical attrition is reported.
2. `evaluate_submission_decision.py` determines the title/thesis using the frozen
   hierarchy.  Fewer than two validated dimensions forces the policy-signature
   framing.
3. Reproduction evidence is reported by scope: the private-input semantic
   finalizer reruns locally; a fresh checkout verifies all frozen public files;
   and an independent GitHub Ubuntu runner installs the exact dependency
   versions and passes registered claims, unit tests, privacy structure, figure
   rebuild, and clean-worktree checks. No claim of provider-byte regeneration or
   private-corpus recomputation on CI is made.
4. The paper names GenPT, the ITS context-ablation study, and tutor-persona/runtime
   control work as closest comparisons; it does not claim behavior-first
   psychometrics as a generic invention.
5. Every learning-effectiveness sentence remains a nonclaim.  A broad education
   or general-science journal route is deferred until a prospective learner study
   or independently validated simulator supplies objective pre/post outcomes.

## Pull-request schedule

- **Method baseline Draft PR:** immediately after GitHub authentication and an
  empty-remote bootstrap; explicitly mark the semantic panel active.
- **Result freeze Draft PR:** after the finalizer and submission decision both
  pass, with no live annotation/log files.
- **Submission package Draft PR:** after clean-room reproduction, manuscript
  integration, bibliography audit, dataset/model cards, and final red-team review.

The calendar is subordinate to the gates.  Missing a cycle is preferable to
turning incomplete construct validity into a stronger claim.
